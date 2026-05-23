import os
from dotenv import load_dotenv

load_dotenv()

IS_CLOUD = os.path.exists("/mount/src")

if IS_CLOUD:
    _MODELS_DIR = "/mount/src/madame-app/models"
    YOLO_MODEL_PATH      = os.path.join(_MODELS_DIR, "best.pt")
    ANNOTATION_JSON_PATH = os.path.join(_MODELS_DIR, "instances_train2020_clean.json")
    ATTR_MODEL_PATH      = os.path.join(_MODELS_DIR, "best_model.pt")
    ATTR_MAP_PATH        = os.path.join(_MODELS_DIR, "attribute_map.json")
else:
    YOLO_MODEL_PATH      = os.getenv("YOLO_MODEL_PATH",      "")
    ANNOTATION_JSON_PATH = os.getenv("ANNOTATION_JSON_PATH", "")
    ATTR_MODEL_PATH      = os.getenv("ATTR_MODEL_PATH",      "")
    ATTR_MAP_PATH        = os.getenv("ATTR_MAP_PATH",        "")

CHROMA_DB_PATH      = os.getenv("CHROMA_DB_PATH", "./wardrobe_db")
GROQ_API_KEY        = os.getenv("GROQ_API_KEY",        "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
CONF_THRESHOLD      = float(os.getenv("CONF_THRESHOLD", "0.30"))
IOU_THRESHOLD       = float(os.getenv("IOU_THRESHOLD",  "0.45"))

def validate() -> list[str]:
    issues = []
    if not IS_CLOUD:
        if not YOLO_MODEL_PATH:
            issues.append("YOLO_MODEL_PATH not set")
        elif not os.path.exists(YOLO_MODEL_PATH):
            issues.append(f"YOLO_MODEL_PATH not found: {YOLO_MODEL_PATH}")
    if not GROQ_API_KEY:
        issues.append("GROQ_API_KEY not set")
    return issues
