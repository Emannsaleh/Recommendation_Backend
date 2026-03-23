# database configuration
import os
from pathlib import Path
from urllib.parse import urlparse

import cloudinary
import cloudinary.api
import cloudinary.uploader

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def _load_env_file(path: Path) -> None:
    """Load KEY=VALUE lines into os.environ (no python-dotenv required).

    Fills missing keys, or replaces keys that are set but empty/whitespace (common on Windows).
    Uses utf-8-sig so Notepad UTF-8 BOM does not break the first variable name.
    """
    if not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError:
        return
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if not key:
            continue
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        existing = os.environ.get(key)
        if existing is None or str(existing).strip() == "":
            os.environ[key] = val


_load_env_file(_ENV_PATH)

try:
    from dotenv import load_dotenv

    load_dotenv(_ENV_PATH, override=False)
except ImportError:
    pass


def _parse_cloudinary_url(url: str) -> tuple[str, str, str]:
    u = urlparse(url.strip())
    if u.scheme != "cloudinary":
        raise ValueError("CLOUDINARY_URL must start with cloudinary://")
    netloc = u.netloc
    creds, _, cloud_name = netloc.rpartition("@")
    if not cloud_name or "@" in creds:
        raise ValueError("Invalid CLOUDINARY_URL format")
    api_key, sep, api_secret = creds.partition(":")
    if sep != ":" or not api_key or not api_secret:
        raise ValueError("Invalid CLOUDINARY_URL credentials segment")
    return cloud_name, api_key, api_secret


def _env_trim(name: str) -> str | None:
    v = os.getenv(name)
    if v is None:
        return None
    v = v.strip()
    return v if v else None


_url = _env_trim("CLOUDINARY_URL")
if _url:
    _cn, _key, _secret = _parse_cloudinary_url(_url)
    cloudinary.config(cloud_name=_cn, api_key=_key, api_secret=_secret)
else:
    _cloud_name = _env_trim("CLOUDINARY_CLOUD_NAME")
    _api_key = _env_trim("CLOUDINARY_API_KEY")
    _api_secret = _env_trim("CLOUDINARY_API_SECRET")
    if not (_cloud_name and _api_key and _api_secret):
        raise RuntimeError(
            "Set CLOUDINARY_URL, or CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and "
            "CLOUDINARY_API_SECRET (Railway variables or a local .env in the repo root). "
            f"Looked for .env at: {_ENV_PATH} (exists: {_ENV_PATH.is_file()}). "
            "If Windows has empty CLOUDINARY_* user variables, remove them or fill .env."
        )
    cloudinary.config(
        cloud_name=_cloud_name,
        api_key=_api_key,
        api_secret=_api_secret,
    )


def upload_to_cloudinary(file_path):
    result = cloudinary.uploader.upload(file_path)
    return result["secure_url"]
