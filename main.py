
from pathlib import Path
from outfit_recommender import OutfitRecommender

_root = Path(__file__).resolve().parent
rec = OutfitRecommender()

pics = _root / "pictures"
rec.add_image(str(pics / "Black_White Striped 2 In 1 Corset Fitted Shirt_Casual Top_Fall _ Winter Women Clothes.jpg"))
rec.add_image(str(pics / "9 Winter Outfit Ideas to Steal From Celebrities.jpg"))
rec.add_image(str(pics / "black boots.jpg"))

outfit = rec.generate_outfit(toseason="Summer")
print(outfit)
