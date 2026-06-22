import os

ENV_TYPE = "rel"; # "dev"

API_ROOT_RELEASE = "https://public-api.nazk.gov.ua"
API_ROOT_DEV = "http://127.0.0.1:8000"

API_ROOT = os.environ.get("NAZK_API_ROOT", API_ROOT_DEV if ENV_TYPE == "dev" else API_ROOT_RELEASE)

STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage")
