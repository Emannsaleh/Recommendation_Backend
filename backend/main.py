import os

# Before TensorFlow loads (via py.recognition_module), reduce GPU-stub noise on CPU-only PCs.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

# Load .env and configure Cloudinary before other imports use the environment.
import backend.cloudinary_config  # noqa: F401

import shutil
import tempfile
import uuid
import cloudinary.api
import cloudinary.uploader
import requests
from fastapi import Body, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.EachUser import (
    UPLOAD_ROOT,
    find_upload,
    get_user_state,
    next_user_id,
    remove_from_rec,
)
from backend.models import EditItem
from py.recognition_module import (
    COLOR_GROUP_INDEX,
    MULTI_COLOR,
    map_color_to_group,
    single_classification,
)

app = FastAPI()

_allow = os.getenv("ALLOW_ORIGINS", "*").strip()
_origins = ["*"] if _allow == "*" else [o.strip() for o in _allow.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


def _parse_color_group(raw) -> int:
    if raw is None or str(raw).strip() == "":
        return COLOR_GROUP_INDEX[MULTI_COLOR]
    try:
        return int(float(raw))
    except (TypeError, ValueError):
        return COLOR_GROUP_INDEX[MULTI_COLOR]


# ==================== CLOSET (Cloudinary) ====================


@app.post("/closet/items")
async def add_closet_item(
    user_id: str = Query(...),
    file: UploadFile = File(...),
):
    try:
        suffix = "." + (file.filename or "img").split(".")[-1].lower()
    except Exception:
        suffix = ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        category, _info, meta = single_classification(tmp_path)
        cg = meta.get("color_group")
        result = cloudinary.uploader.upload(
            tmp_path,
            folder=f"closet/{user_id}",
            resource_type="image",
            context={
                "category": category,
                "subtype": meta.get("subtype") or "",
                "gender": meta.get("gender") or "",
                "season": meta.get("season") or "",
                "usage": meta.get("usage") or "",
                "color": meta.get("color") or "",
                "color_group": str(cg) if cg is not None else "",
            },
        )
        return {
            "public_id": result["public_id"],
            "url": result["secure_url"],
            "category": category,
            "subtype": meta.get("subtype"),
            "gender": meta.get("gender"),
            "season": meta.get("season"),
            "usage": meta.get("usage"),
            "color": meta.get("color"),
            "color_group": cg,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Closet upload failed: {e}") from e
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.get("/closet/items")
def list_closet_items(user_id: str = Query(...)):
    try:
        data = cloudinary.api.resources(
            type="upload",
            prefix=f"closet/{user_id}/",
            resource_type="image",
            max_results=100,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary list failed: {e}") from e
    items = []
    for r in data.get("resources", []):
        custom = (r.get("context") or {}).get("custom") or {}
        items.append(
            {
                "public_id": r.get("public_id"),
                "url": r.get("secure_url"),
                "category": custom.get("category"),
                "subtype": custom.get("subtype"),
                "gender": custom.get("gender"),
                "season": custom.get("season"),
                "usage": custom.get("usage"),
                "color": custom.get("color"),
                "color_group": _parse_color_group(custom.get("color_group")),
            }
        )
    return {"items": items}


@app.delete("/closet/items/{public_id:path}")
def delete_closet_item(public_id: str, user_id: str = Query(...)):
    if not public_id.startswith(f"closet/{user_id}/"):
        raise HTTPException(status_code=404, detail="Item not found")
    try:
        result = cloudinary.uploader.destroy(public_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary delete failed: {e}") from e
    if result.get("result") == "not found":
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "deleted", "public_id": public_id}


# ==================== UPLOADS (local + rec) ====================


@app.post("/uploads/items")
async def add_item(
    user_id: str = Query(...),
    source: str = Query(..., description="upload or closet"),
    file: UploadFile | None = File(None),
    public_id: str | None = Query(None),
):
    uploads, rec = get_user_state(user_id)
    if source == "upload":
        if not file:
            raise HTTPException(status_code=400, detail="file required when source=upload")
        ext = (file.filename or "img").split(".")[-1]
        user_folder = os.path.join(UPLOAD_ROOT, user_id)
        os.makedirs(user_folder, exist_ok=True)
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = os.path.join(user_folder, filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        try:
            category, _info, meta = single_classification(file_path)
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Classification failed: {e}") from e
        item = dict(meta)
        item["category"] = category
        item["file_path"] = file_path
        item["image_url"] = f"/images/{user_id}/{filename}"
        item["cloudinary_public_id"] = None
        item["cloudinary_url"] = None
        item["source"] = "upload"
    elif source == "closet":
        if not public_id:
            raise HTTPException(status_code=400, detail="public_id required when source=closet")
        if not public_id.startswith(f"closet/{user_id}/"):
            raise HTTPException(status_code=404, detail="Closet item not found")
        try:
            r = cloudinary.api.resource(public_id)
        except Exception:
            raise HTTPException(status_code=404, detail="Closet item not found")
        image_url = r.get("secure_url")
        custom = (r.get("context") or {}).get("custom") or {}
        if not image_url:
            raise HTTPException(status_code=404, detail="Closet image url not found")
        try:
            resp = requests.get(image_url, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch closet image: {e}") from e
        user_folder = os.path.join(UPLOAD_ROOT, user_id)
        os.makedirs(user_folder, exist_ok=True)
        filename = f"{uuid.uuid4()}.jpg"
        file_path = os.path.join(user_folder, filename)
        with open(file_path, "wb") as f:
            f.write(resp.content)
        item = {
            "subtype": custom.get("subtype"),
            "gender": custom.get("gender"),
            "season": custom.get("season"),
            "usage": custom.get("usage"),
            "color": custom.get("color"),
            "category": custom.get("category"),
            "color_group": _parse_color_group(custom.get("color_group")),
            "file_path": file_path,
            "image_url": f"/images/{user_id}/{filename}",
            "cloudinary_public_id": public_id,
            "cloudinary_url": image_url,
            "source": "closet",
        }
    else:
        raise HTTPException(status_code=400, detail="source must be upload or closet")
    item["id"] = next_user_id(user_id)
    cat = item.get("category")
    if cat == "top":
        rec.top.append(item)
    elif cat == "bottom":
        rec.bottom.append(item)
    elif cat == "foot":
        rec.shoes.append(item)
    else:
        rec.top.append(item)
    uploads.append(item)
    return item


@app.get("/uploads/items")
def list_items(user_id: str = Query(...)):
    uploads, _ = get_user_state(user_id)
    return {"items": uploads}


@app.put("/uploads/items/{item_id}")
def update_upload_item(
    item_id: int,
    user_id: str = Query(...),
    body: EditItem = Body(default_factory=EditItem),
):
    uploads, rec = get_user_state(user_id)
    item = find_upload(user_id, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if body.subtype is not None:
        item["subtype"] = body.subtype
    if body.gender is not None:
        item["gender"] = body.gender
    if body.color is not None:
        item["color"] = body.color
        gname = map_color_to_group(body.color)
        item["color_group"] = COLOR_GROUP_INDEX.get(gname, COLOR_GROUP_INDEX[MULTI_COLOR])
    if body.season is not None:
        item["season"] = body.season
    if body.usage is not None:
        item["usage"] = body.usage
    for lst in (rec.top, rec.bottom, rec.shoes):
        for i, v in enumerate(lst):
            if v.get("id") == item_id:
                lst[i] = item
                break
    return item


@app.delete("/uploads/items/{item_id}")
def delete_item(item_id: int, user_id: str = Query(...)):
    uploads, rec = get_user_state(user_id)
    for i, item in enumerate(uploads):
        if item.get("id") == item_id:
            fp = item.get("file_path")
            if fp and os.path.exists(fp):
                os.remove(fp)
            remove_from_rec(rec, item_id)
            uploads.pop(i)
            return {"message": "Item deleted successfully", "id": item_id}
    raise HTTPException(status_code=404, detail="Item not found")


@app.get("/uploads/outfit")
def generate_outfit(user_id: str = Query(...)):
    _uploads, rec = get_user_state(user_id)
    try:
        return rec.generate_outfit()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


app.mount("/images", StaticFiles(directory=UPLOAD_ROOT), name="images")
