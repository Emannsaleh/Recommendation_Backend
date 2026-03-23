from typing import Optional, Dict, Any
import os
from outfit_recommender import OutfitRecommender

UPLOAD_ROOT = os.environ.get("UPLOAD_ROOT", "uploads_images")

os.makedirs(UPLOAD_ROOT, exist_ok=True)

uploads_by_user: Dict[str, list] = {}

rec_by_user: Dict[str, OutfitRecommender] = {}

id_by_user: Dict[str, int] = {}


def get_user_state(user_id: str):
    if user_id not in uploads_by_user:
        uploads_by_user[user_id] = []
        rec_by_user[user_id] = OutfitRecommender()
        id_by_user[user_id] = 1
    return uploads_by_user[user_id], rec_by_user[user_id]


def next_user_id(user_id: str) -> int:
    value = id_by_user.get(user_id, 1)
    id_by_user[user_id] = value + 1
    return value


def find_upload(user_id: str, item_id: int) -> Optional[Dict[str, Any]]:
    uploads, _ = get_user_state(user_id)
    for item in uploads:
        if item.get("id") == item_id:
            return item
    return None


def remove_from_rec(rec: OutfitRecommender, item_id: int):
    for lst in (rec.top, rec.bottom, rec.shoes):
        lst[:] = [x for x in lst if x.get("id") != item_id]
