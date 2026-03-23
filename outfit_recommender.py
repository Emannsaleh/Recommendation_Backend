import random
from py.recognition_module import single_classification, find_combo_by_top


class OutfitRecommender:
    def __init__(self):
        self.top = []
        self.bottom = []
        self.shoes = []

    def add_image(self, image_path):
        """
        Classify the image and store it as a flat dictionary.
        Returns subtype and res_dict.
        """
        subtype, _info_str, res_dict = single_classification(image_path)

        if subtype == "top":
            self.top.append(res_dict)
        elif subtype == "bottom":
            self.bottom.append(res_dict)
        elif subtype == "foot":
            self.shoes.append(res_dict)
        else:
            self.top.append(res_dict)

        return subtype, res_dict

    # -------------------------------
    # Generate Outfit
    # -------------------------------
    def generate_outfit(self, toseason=None, gender=None, usage=None, combotype=60):
        """
        Generate an outfit with:
        - gender/season/usage filtering
        - color compatibility scoring
        Returns a flat dictionary ready for JSON (no duplicates)
        """
        if not self.top or not self.bottom or not self.shoes:
            raise ValueError("Add at least one top, bottom, and shoe")

        # Randomly select a top
        top_item = random.choice(self.top)

        gender = gender or top_item.get("gender")
        season = toseason or top_item.get("season")
        usage = usage or top_item.get("usage")
        top_color = top_item.get("color_group")

        # Filter bottoms and shoes
        valid_combos = []
        for b in self.bottom:
            for s in self.shoes:
                if ((b["gender"] == gender or b["gender"] == "Unisex") and
                    (s["gender"] == gender or s["gender"] == "Unisex") and
                    (b["season"] == season or b["season"] is None) and
                    (s["season"] == season or s["season"] is None) and
                    (b["usage"] == usage or b["usage"] is None) and
                    (s["usage"] == usage or s["usage"] is None)):
                    valid_combos.append((b, s))

        # If no valid combos, fallback to any combination
        if not valid_combos:
            valid_combos = [(b, s) for b in self.bottom for s in self.shoes]

        # Score combos based on color harmony
        best_score = -1
        best_combo = None
        for b, s in valid_combos:
            recommended_bottom, recommended_shoe = find_combo_by_top(top_color, combotype)
            score = 0
            # Bottom color scoring
            if b["color_group"] == recommended_bottom:
                score += 2
            elif b["color_group"] in [recommended_bottom-1, recommended_bottom+1]:
                score += 1
            # Shoe color scoring
            if s["color_group"] == recommended_shoe:
                score += 2
            elif s["color_group"] in [recommended_shoe-1, recommended_shoe+1]:
                score += 1

            if score > best_score:
                best_score = score
                best_combo = {"top": top_item, "bottom": b, "shoes": s}

        return best_combo