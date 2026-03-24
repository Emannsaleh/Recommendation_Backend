import gdown
import os
import zipfile
from pathlib import Path

# ===== CONFIG =====
FILE_ID = "1_q2_IrK9woPXg28mC41KFSeYrLDQcQI5"
URL = f"https://drive.google.com/uc?id={FILE_ID}"

ROOT = Path(__file__).resolve().parent.parent
ZIP_PATH = ROOT / "models.zip"
EXTRACT_PATH = ROOT / "models-saved"

def download_models():
    models_path = EXTRACT_PATH / "models"

    # ✅ If already downloaded → skip
    if models_path.exists():
        print("✅ Models already exist")
        return

    print("⬇️ Downloading models from Google Drive...")

    # Download file
    gdown.download(URL, str(ZIP_PATH), quiet=False)

    print("📦 Extracting models...")

    with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
        zip_ref.extractall(EXTRACT_PATH)

    print("✅ Models ready!")

if __name__ == "__main__":
    download_models()