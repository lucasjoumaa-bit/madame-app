"""
pipeline/inference.py — Madame de la Grande Bouche
Exact pipeline from your inference_pipeline.ipynb notebook:
  YOLO26s → crops → dominant colour (k-means, mask-aware)
           → EfficientNet-B0 attribute classifier
           → CLIP ViT-B/32 embedding
           → ChromaDB upsert
"""
from __future__ import annotations
import io, uuid, base64
import numpy as np
from PIL import Image, ImageDraw


# ─────────────────────────────────────────────────────────────────────────────
# 1. SEGMENTABILITY GATE  (Cell 9 in inference_pipeline.ipynb)
# ─────────────────────────────────────────────────────────────────────────────

def is_segmentable(
    result,
    min_detections : int   = 1,
    min_confidence : float = 0.30,
    min_area_ratio : float = 0.01,
) -> tuple[bool, str]:
    boxes = result.boxes
    if boxes is None or len(boxes) == 0:
        return False, "No clothing detected in this image"

    confs = boxes.conf.cpu().numpy()
    if confs.max() < min_confidence:
        return False, f"Low confidence ({confs.max():.0%}) — try better lighting or a clearer photo"

    xywhn = boxes.xywhn.cpu().numpy()
    areas = xywhn[:, 2] * xywhn[:, 3]
    if areas.max() < min_area_ratio:
        return False, "Detected items are too small — try a closer shot"

    good = int((confs >= min_confidence).sum())
    if good < min_detections:
        return False, f"Only {good} high-confidence detection(s) — try a photo with clearer garments"

    return True, "ok"


# ─────────────────────────────────────────────────────────────────────────────
# 2. DOMINANT COLOUR  (CLIP-based — exact copy from inference_pipeline.ipynb)
# ─────────────────────────────────────────────────────────────────────────────

BASIC_COLORS = [
    'a black clothing item',
    'a white clothing item',
    'a gray clothing item',
    'a red clothing item',
    'a orange clothing item',
    'a yellow clothing item',
    'a green clothing item',
    'a blue clothing item',
    'a navy blue clothing item',
    'a purple clothing item',
    'a pink clothing item',
    'a brown clothing item',
    'a beige clothing item',
]

COLOR_LABELS = [c.replace('a ', '').replace(' clothing item', '') for c in BASIC_COLORS]

_COLOR_RGB = {
    'black'    : (20,   20,  20),
    'white'    : (245, 245, 245),
    'gray'     : (128, 128, 128),
    'red'      : (220,  20,  60),
    'orange'   : (255, 140,   0),
    'yellow'   : (255, 215,   0),
    'green'    : (34,  139,  34),
    'blue'     : (30,  144, 255),
    'navy blue': (0,     0, 128),
    'purple'   : (138,  43, 226),
    'pink'     : (255, 105, 180),
    'brown'    : (139,  69,  19),
    'beige'    : (245, 245, 220),
}

# Globals — declared here so they always exist; populated by init_color_tokens()
_COLOR_TOKENS   = None
_CLIP_MODEL_REF = None
_CLIP_PREP_REF  = None
_DEVICE_REF     = "cpu"

def init_color_tokens(clip_model_ref, clip_preprocess_ref, device_ref: str) -> None:
    """
    Call this once after CLIP is loaded so the color tokens are ready.
    Mirrors the pre-tokenisation done at the top of Cell 9.
    """
    import clip as _clip
    global _COLOR_TOKENS, _CLIP_MODEL_REF, _CLIP_PREP_REF, _DEVICE_REF
    _COLOR_TOKENS    = _clip.tokenize(BASIC_COLORS).to(device_ref)
    _CLIP_MODEL_REF  = clip_model_ref
    _CLIP_PREP_REF   = clip_preprocess_ref
    _DEVICE_REF      = device_ref


def get_dominant_color_masked(crop: Image.Image, mask=None) -> dict:
    """
    Uses CLIP to classify the dominant colour from a fixed list of basic colours.
    Exact copy of get_dominant_color_masked() from inference_pipeline.ipynb.
    """
    import torch
    global _COLOR_TOKENS, _CLIP_MODEL_REF, _CLIP_PREP_REF, _DEVICE_REF

    if _CLIP_MODEL_REF is None or _COLOR_TOKENS is None:
        raise RuntimeError(
            "Color CLIP not initialised — call init_color_tokens() after loading CLIP."
        )

    image_tensor = _CLIP_PREP_REF(crop).unsqueeze(0).to(_DEVICE_REF)
    with torch.no_grad():
        image_feat = _CLIP_MODEL_REF.encode_image(image_tensor)
        image_feat = image_feat / image_feat.norm(dim=-1, keepdim=True)
        text_feat  = _CLIP_MODEL_REF.encode_text(_COLOR_TOKENS)
        text_feat  = text_feat / text_feat.norm(dim=-1, keepdim=True)

    logits   = (image_feat @ text_feat.T) * 100
    probs    = logits.softmax(dim=-1).cpu().numpy()[0]
    best_idx = int(probs.argmax())
    color    = COLOR_LABELS[best_idx]

    r, g, b = _COLOR_RGB.get(color, (128, 128, 128))
    return {
        'rgb' : (r, g, b),
        'hex' : f'#{r:02x}{g:02x}{b:02x}',
        'name': color,
    }


def get_dominant_color(crop: Image.Image, mask_array=None, n_colors: int = 6) -> dict:
    """Alias — mask not needed since CLIP reasons about the whole image."""
    return get_dominant_color_masked(crop, mask_array)


# ─────────────────────────────────────────────────────────────────────────────
# 3. ATTRIBUTE CLASSIFIER  (EfficientNet-B0 — trained on Fashionpedia attrs)
# ─────────────────────────────────────────────────────────────────────────────

def load_attribute_classifier(model_path: str, map_path: str, device: str):
    """
    Loads your trained EfficientNet-B0 attribute classifier.
    Returns (model, transform, selected_attrs) or (None, None, None) if not found.
    Mirrors Cell 9 / Cell 17 of inference_pipeline.ipynb.
    """
    import os, json
    import torch
    import torch.nn as nn
    import torchvision.transforms as T

    if not model_path or not os.path.exists(model_path):
        return None, None, []
    if not map_path or not os.path.exists(map_path):
        return None, None, []

    try:
        import timm

        with open(map_path) as f:
            attr_map = json.load(f)

        selected_attrs = attr_map["attributes"]
        num_attrs      = attr_map["num_attributes"]

        class AttributeClassifier(nn.Module):
            def __init__(self, num_attrs):
                super().__init__()
                self.backbone = timm.create_model(
                    "efficientnet_b0", pretrained=False, num_classes=0
                )
                self.head = nn.Sequential(
                    nn.Dropout(0.3),
                    nn.Linear(self.backbone.num_features, num_attrs),
                )
            def forward(self, x):
                return self.head(self.backbone(x))

        model = AttributeClassifier(num_attrs=num_attrs).to(device)
        model.load_state_dict(
            torch.load(model_path, map_location=device)
        )
        model.eval()

        transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        return model, transform, selected_attrs

    except Exception as e:
        print(f"[attribute_classifier] failed to load: {e}")
        return None, None, []


CATEGORY_ATTR_RULES = {
    'shirt'      : ['textile pattern', 'length', 'silhouette', 'neckline type', 'opening type', 'waistline'],
    'blouse'     : ['textile pattern', 'length', 'silhouette', 'neckline type', 'opening type', 'waistline'],
    'top'        : ['textile pattern', 'length', 'silhouette', 'neckline type', 'opening type', 'waistline'],
    'sweater'    : ['textile pattern', 'length', 'silhouette', 'neckline type', 'opening type'],
    'sweatshirt' : ['textile pattern', 'length', 'silhouette', 'neckline type', 'opening type'],
    't-shirt'    : ['textile pattern', 'length', 'silhouette', 'neckline type'],
    'jacket'     : ['textile pattern', 'length', 'silhouette', 'opening type'],
    'coat'       : ['textile pattern', 'length', 'silhouette', 'opening type'],
    'dress'      : ['textile pattern', 'length', 'silhouette', 'neckline type', 'opening type', 'waistline'],
    'jumpsuit'   : ['textile pattern', 'length', 'silhouette', 'neckline type', 'opening type', 'waistline'],
    'pants'      : ['textile pattern', 'length', 'silhouette', 'waistline', 'opening type'],
    'skirt'      : ['textile pattern', 'length', 'silhouette', 'waistline'],
    'shorts'     : ['textile pattern', 'length', 'silhouette', 'waistline'],
    'jeans'      : ['textile pattern', 'length', 'silhouette', 'waistline', 'opening type'],
    'leggings'   : ['textile pattern', 'length', 'silhouette'],
    'bag'        : ['textile pattern'],
    'wallet'     : ['textile pattern'],
    'belt'       : ['textile pattern'],
    'hat'        : ['textile pattern', 'silhouette'],
    'scarf'      : ['textile pattern'],
    'tie'        : ['textile pattern'],
    'shoe'       : [],
    'boot'       : [],
    'sandal'     : [],
    'sneaker'    : [],
    'heel'       : [],
}

def _get_allowed_attrs(class_name: str) -> list:
    class_lower = class_name.lower()
    for key, allowed in CATEGORY_ATTR_RULES.items():
        if key in class_lower:
            return allowed
    return ['textile pattern', 'length', 'silhouette', 'neckline type', 'opening type', 'waistline']


def get_attributes_efficientnet(
    crop_pil:       Image.Image,
    attr_model,
    attr_transform,
    selected_attrs: list,
    device:         str,
    class_name:     str = "clothing item",
    threshold:      float = 0.5,
) -> dict:
    """
    Runs the trained EfficientNet attribute classifier on a crop.
    Only returns attributes that make sense for the detected item type.
    Exact copy of get_attr_classifier_attributes() from inference_pipeline.ipynb.
    """
    import torch

    tensor = attr_transform(crop_pil).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = attr_model(tensor)
        probs  = torch.sigmoid(logits).cpu().numpy()[0]

    allowed_supercats = _get_allowed_attrs(class_name)

    group_best = {}
    for i, attr in enumerate(selected_attrs):
        sc   = attr['supercategory']
        if sc not in allowed_supercats:
            continue
        conf = float(probs[i])
        if sc not in group_best or conf > group_best[sc]['confidence']:
            group_best[sc] = {
                'label'      : attr['name'],
                'confidence' : round(conf, 4),
            }

    return group_best

# ─────────────────────────────────────────────────────────────────────────────
# 4. CLIP EMBEDDING  (for ChromaDB retrieval — Cell 9)
# ─────────────────────────────────────────────────────────────────────────────

def get_clip_embedding(
    crop_pil:       Image.Image,
    clip_model,
    clip_preprocess,
    device:         str,
) -> list[float]:
    """512-dim CLIP image embedding for ChromaDB similarity search."""
    import torch
    inp = clip_preprocess(crop_pil).unsqueeze(0).to(device)
    with torch.no_grad():
        emb = clip_model.encode_image(inp)
        emb = emb / emb.norm(dim=-1, keepdim=True)
    return emb.cpu().numpy()[0].tolist()


# ─────────────────────────────────────────────────────────────────────────────
# 5. CROP UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def _crop_padded(image_pil: Image.Image, x1, y1, x2, y2, padding=0.05) -> Image.Image:
    W, H = image_pil.size
    pw = (x2 - x1) * padding
    ph = (y2 - y1) * padding
    return image_pil.crop((
        max(0, x1 - pw), max(0, y1 - ph),
        min(W, x2 + pw), min(H, y2 + ph),
    )).convert("RGB")


def _pil_to_b64(img: Image.Image, max_size=(320, 320)) -> str:
    c = img.copy()
    c.thumbnail(max_size, Image.LANCZOS)
    buf = __import__("io").BytesIO()
    c.save(buf, format="JPEG", quality=88)
    return __import__("base64").b64encode(buf.getvalue()).decode()


def b64_to_pil(b64: str) -> Image.Image:
    return Image.open(io.BytesIO(base64.b64decode(b64)))


# ─────────────────────────────────────────────────────────────────────────────
# 6. ANNOTATION DRAWING
# ─────────────────────────────────────────────────────────────────────────────

def draw_annotations(image_pil: Image.Image, items: list[dict]) -> Image.Image:
    import hashlib
    annotated = image_pil.copy().convert("RGB")
    draw = ImageDraw.Draw(annotated)
    for item in items:
        x1, y1, x2, y2 = item["bbox"]
        h = hashlib.md5(item["class_name"].encode()).hexdigest()
        col = (max(60, int(h[0:2], 16)), max(60, int(h[2:4], 16)), max(60, int(h[4:6], 16)))
        draw.rectangle([x1, y1, x2, y2], outline=col, width=3)
        label = f"{item['class_name'].replace('_',' ')}  {item['confidence']:.0%}"
        lx, ly = int(x1), max(0, int(y1) - 22)
        try:
            tb = draw.textbbox((lx, ly), label)
            draw.rectangle(tb, fill=col)
            draw.text((lx, ly), label, fill="white")
        except Exception:
            draw.text((lx, ly), label, fill=col)
    return annotated


# ─────────────────────────────────────────────────────────────────────────────
# 7. MAIN PIPELINE  (run_pipeline() from Cell 10 / Cell 21)
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(
    image_pil:        Image.Image,
    yolo_model,
    clip_model,
    clip_preprocess,
    id_to_name:       dict[int, str],
    device:           str,
    chroma_collection = None,
    attr_model        = None,
    attr_transform    = None,
    selected_attrs:   list = None,
    conf_threshold:   float = 0.30,
    iou_threshold:    float = 0.45,
) -> dict:
    """
    Full inference pipeline for a single PIL image.

    Returns:
        segmentable:     bool
        reason:          str
        items:           list[dict]   — one dict per clothing item
        annotated_image: PIL.Image
    """
    W, H = image_pil.size

    # ── YOLO inference ────────────────────────────────────────────────────────
    results = yolo_model.predict(
        source  = image_pil,
        conf    = conf_threshold,
        iou     = iou_threshold,
        imgsz   = 640,
        device  = 0 if device == "cuda" else "cpu",
        verbose = False,
    )
    result = results[0]

    ok, reason = is_segmentable(result, min_confidence=conf_threshold)
    if not ok:
        return {"segmentable": False, "reason": reason, "items": [], "annotated_image": None}

    items: list[dict] = []

    for box in result.boxes:
        conf   = float(box.conf.cpu())
        if conf < conf_threshold:
            continue

        cls_id = int(box.cls.cpu())
        name   = id_to_name.get(cls_id, f"class_{cls_id}")

        x1, y1, x2, y2 = box.xyxy.cpu().numpy()[0]

        # ── padded crop ───────────────────────────────────────────────────────
        crop = _crop_padded(image_pil, x1, y1, x2, y2, padding=0.05)

        # ── try to get mask from YOLO segmentation head ───────────────────────
        mask_arr = None
        if result.masks is not None:
            try:
                idx       = list(result.boxes).index(box)
                mask_data = result.masks.data[idx].cpu().numpy()
                # resize mask to crop size for masked colour extraction
                from PIL import Image as _Image
                mask_pil  = _Image.fromarray((mask_data * 255).astype(np.uint8))
                mask_pil  = mask_pil.resize(crop.size, _Image.NEAREST)
                mask_arr  = np.array(mask_pil) > 127
            except Exception:
                mask_arr = None

        # ── dominant colour ───────────────────────────────────────────────────
        color = get_dominant_color(crop, mask_array=mask_arr)

        # ── attributes: prefer trained EfficientNet, fall back gracefully ─────
        if attr_model is not None and attr_transform is not None and selected_attrs:
            attributes = get_attributes_efficientnet(
                crop, attr_model, attr_transform, selected_attrs, device,
                class_name=name
            )
        else:
            # no attribute model available — store empty attrs
            attributes = {}

        # ── CLIP embedding ────────────────────────────────────────────────────
        embedding = get_clip_embedding(crop, clip_model, clip_preprocess, device)
        crop_b64  = _pil_to_b64(crop)
        item_id   = str(uuid.uuid4())

        # ── build human-readable document string (same as your notebook) ──────
        attr_labels = [v["label"] for v in attributes.values() if v.get("label")]
        doc = (
            f"{name}, {color['name']} color"
            + (f", {', '.join(attr_labels)}" if attr_labels else "")
        )

        item = {
            "item_id":    item_id,
            "class_name": name,
            "class_id":   cls_id,
            "confidence": round(conf, 3),
            "bbox":       [float(x1), float(y1), float(x2), float(y2)],
            "color":      color,
            "attributes": attributes,
            "embedding":  embedding,
            "crop_b64":   crop_b64,
        }
        items.append(item)

        # ── ChromaDB upsert ───────────────────────────────────────────────────
        if chroma_collection is not None:
            try:
                meta = {
                    "class_name":  name,
                    "class_id":    cls_id,
                    "confidence":  round(conf, 3),
                    "color_name":  color["name"],
                    "color_hex":   color["hex"],
                    "crop_b64":    crop_b64,
                }
                # flatten attribute labels into metadata (mirrors insert_into_wardrobe())
                for group, attr_data in attributes.items():
                    meta[f"attr_{group}"]       = attr_data.get("label", "")
                    meta[f"attr_{group}_conf"]   = attr_data.get("confidence", 0.0)

                chroma_collection.upsert(
                    ids        = [item_id],
                    embeddings = [embedding],
                    metadatas  = [meta],
                    documents  = [doc],
                )
            except Exception:
                pass   # never crash the UI on a DB error

    annotated = draw_annotations(image_pil, items)

    return {
        "segmentable":     True,
        "reason":          "ok",
        "items":           items,
        "annotated_image": annotated,
    }
