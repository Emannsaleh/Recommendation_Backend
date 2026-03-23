"""
Download the four TensorFlow SavedModel folders from Google Drive into:
  <repo root>/models-saved/models/

Run from anywhere:
  python scripts/download_models.py

Requires: pip install gdown
"""
from __future__ import annotations

import sys,gdown,os,zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "models-saved" / "models"

# Outfit recommendation models (shared Drive folder)
DRIVE_FOLDER_URL = (
    "https://drive.google.com/drive/folders/1cIID51--8h882p04Nv0VkBPuHlB804xq"
)

EXPECTED = ("model_sub", "model_top", "model_bottom", "model_shoes")


def main() -> None:
    try:
        import gdown
    except ImportError:
        print("Missing package. Run: pip install gdown")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading into: {OUTPUT_DIR}")
    print("If Google asks for access, use a browser where you are signed into Drive.\n")

    gdown.download_folder(
        DRIVE_FOLDER_URL,
        output=str(OUTPUT_DIR),
        quiet=False,
        use_cookies=False,
    )

    present = {p.name for p in OUTPUT_DIR.iterdir() if p.is_dir()}
    missing = [name for name in EXPECTED if name not in present]
    if missing:
        print(f"\nWarning: expected folders not found: {missing}")
        print("Check the download output above (quota / permission errors are common).")
    else:
        print("\nOK: model_sub, model_top, model_bottom, model_shoes are present.")


if __name__ == "__main__":
    main()
