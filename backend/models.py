from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from py.recognition_module import bottom_list, foot_list, top_list


class ItemResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    item_type: str = Field(validation_alias="type", serialization_alias="type")
    season: str
    usage: str
    gender: str
    image_url: str


class EditItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    subtype: Optional[str] = Field(default=None, validation_alias="type", serialization_alias="type")
    gender: Optional[str] = None
    color: Optional[str] = None
    season: Optional[str] = None
    usage: Optional[str] = None


class AddToSession(BaseModel):
    user_id: str
    source: str  # "upload" or "closet"
    public_id: Optional[str] = None  # required when source == "closet" (Cloudinary public_id)


CATEGORY_LISTS = {
    "top": top_list,
    "bottom": bottom_list,
    "foot": foot_list,
}
