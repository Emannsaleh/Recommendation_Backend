import os
from pathlib import Path
from threading import Lock
os.environ["TF_USE_LEGACY_KERAS"] = "1"

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

# for modeling
from datetime import date

from tensorflow.keras.preprocessing import image
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import random


#for read and show images
import cv2                                                          
import matplotlib.image as mpimg

#for save and load models
import tensorflow as tf
from tensorflow import keras                                        


import numpy as np

#for color classification
import colorsys                                                     
import PIL.Image as Image

from scipy.spatial import KDTree
from webcolors import hex_to_rgb

from webcolors import CSS3_NAMES_TO_HEX
CSS3_HEX_TO_NAMES = {v: k for k, v in CSS3_NAMES_TO_HEX.items()}

# ----------------------------
# 12 Color Groups + Neutrals
# ----------------------------
COLOR_GROUPS = {
    "red": ["red", "darkred", "firebrick", "indianred"],
    "orange": ["orange", "darkorange", "coral"],
    "yellow": ["yellow", "gold", "khaki"],
    "green": ["green", "lime", "forestgreen"],
    "cyan": ["cyan", "turquoise", "teal"],
    "blue": ["blue", "dodgerblue", "navy"],
    "purple": ["purple", "indigo", "violet"],
    "pink": ["pink", "hotpink", "deeppink"],
    "brown": ["brown", "saddlebrown", "chocolate"],
    "black": ["black"],
    "white": ["white"],
    "gray": ["gray", "grey", "silver"]
}
MULTI_COLOR = "multi"

COLOR_GROUP_INDEX = {
    "red": 0,
    "orange": 1,
    "yellow": 2,
    "green": 3,
    "cyan": 4,
    "blue": 5,
    "purple": 6,
    "pink": 7,
    "brown": 8,
    "black": 12,
    "white": 13,
    "gray": 14,
    "multi": 15
}

# load pre-trained models (repo: models-saved/models/...; override with MODELS_DIR)
_project_root = Path(__file__).resolve().parent.parent
_models_dir = Path(os.environ.get("MODELS_DIR", _project_root / "models-saved" / "models"))
sub_model = None
top_model = None
bottom_model = None
foot_model = None
_models_loaded = False
_models_lock = Lock()
_models_last_error = ""

def _ensure_models_loaded():
    """Load only the subtype model once per process on first use."""
    global sub_model
    global _models_loaded, _models_last_error

    if _models_loaded:
        return True

    with _models_lock:
        if _models_loaded:
            return True

        try:
            if (_models_dir / "model_sub").exists():
                sub_model = tf.keras.models.load_model(str(_models_dir / "model_sub"))
                _models_loaded = True
                _models_last_error = ""
                print("✅ Sub model loaded successfully")
                return True
            _models_last_error = f"Models not found in: {_models_dir}"
            print(f"⚠️ {_models_last_error}, running in fallback mode")
            return False
        except Exception as e:
            _models_last_error = str(e)
            print("❌ Error loading models:", e)
            return False


def _get_task_model(task: str):
    """
    Lazily load task-specific model and keep only one in memory at a time
    to reduce RAM usage on small instances.
    """
    global top_model, bottom_model, foot_model, _models_last_error

    with _models_lock:
        try:
            if task == "top":
                if top_model is None:
                    top_model = tf.keras.models.load_model(str(_models_dir / "model_top"))
                bottom_model = None
                foot_model = None
                return top_model
            if task == "bottom":
                if bottom_model is None:
                    bottom_model = tf.keras.models.load_model(str(_models_dir / "model_bottom"))
                top_model = None
                foot_model = None
                return bottom_model

            # foot
            if foot_model is None:
                foot_model = tf.keras.models.load_model(str(_models_dir / "model_shoes"))
            top_model = None
            bottom_model = None
            return foot_model
        except Exception as e:
            _models_last_error = str(e)
            print("❌ Error loading task model:", e)
            return None


def get_model_status():
    """
    Return current model loading state for diagnostics endpoints/logging.
    """
    status = {
        "loaded": bool(_models_loaded and sub_model is not None),
        "models_dir": str(_models_dir),
        "exists": {
            "model_sub": (_models_dir / "model_sub").exists(),
            "model_top": (_models_dir / "model_top").exists(),
            "model_bottom": (_models_dir / "model_bottom").exists(),
            "model_shoes": (_models_dir / "model_shoes").exists(),
        },
        "in_memory": {
            "sub_model": sub_model is not None,
            "top_model": top_model is not None,
            "bottom_model": bottom_model is not None,
            "foot_model": foot_model is not None,
        },
        "last_error": _models_last_error,
    }
    return status

# all output possibilities of the model for subsequent matching
sub_list = ["bottom","foot","top"]
top_list = [['Belts', 'Blazers', 'Dresses', 'Dupatta', 'Jackets', 'Kurtas',
       'Kurtis', 'Lehenga Choli', 'Nehru Jackets', 'Rain Jacket',
       'Rompers', 'Shirts', 'Shrug', 'Suspenders', 'Sweaters',
       'Sweatshirts', 'Tops', 'Tshirts', 'Tunics', 'Waistcoat'],
           ['Boys', 'Girls', 'Men', 'Unisex', 'Women'],
           ['Black', 'Blue', 'Dark Blue', 'Dark Green', 'Dark Yellow', 'Green',
       'Grey', 'Light Blue', 'Multi', 'Orange', 'Pink', 'Purple', 'Red',
       'White', 'Yellow'],
           ['Fall', 'Spring', 'Summer', 'Winter'],
           ['Casual', 'Ethnic', 'Formal', 'Party', 'Smart Casual', 'Sports',
       'Travel']]
bottom_list = [['Capris', 'Churidar', 'Jeans', 'Jeggings', 'Leggings', 'Patiala',
       'Salwar', 'Salwar and Dupatta', 'Shorts', 'Skirts', 'Stockings',
       'Swimwear', 'Tights', 'Track Pants', 'Tracksuits', 'Trousers'],
              ['Boys', 'Girls', 'Men', 'Unisex', 'Women'],
              ['Black', 'Blue', 'Dark Blue', 'Dark Green', 'Dark Yellow', 'Grey',
       'Light Blue', 'Multi', 'Orange', 'Pink', 'Purple', 'Red', 'White',
       'Yellow'],
              ['Fall', 'Spring', 'Summer', 'Winter'],
              ['Casual', 'Ethnic', 'Formal', 'Smart Casual', 'Sports']]
foot_list = [['Casual Shoes', 'Flats', 'Flip Flops', 'Formal Shoes', 'Heels',
       'Sandals', 'Sports Sandals', 'Sports Shoes'],
            ['Boys', 'Girls', 'Men', 'Unisex', 'Women'],
            ['Black', 'Blue', 'Dark Blue', 'Dark Green', 'Dark Orange',
       'Dark Yellow', 'Grey', 'Light Blue', 'Multi', 'Orange', 'Pink',
       'Purple', 'Red', 'White', 'Yellow'],
            ['Fall', 'Spring', 'Summer', 'Winter'],
            ['Casual', 'Ethnic', 'Formal', 'Party', 'Smart Casual', 'Sports']]

# ----------------------------
# Helper: Map CSS color → color group
# ----------------------------
def map_color_to_group(color_name):
    color_name = color_name.lower()
    for group, colors in COLOR_GROUPS.items():
        if color_name in colors:
            return group
    return MULTI_COLOR


def convert_rgb_to_names(rgb_tuple):
    names = []
    rgb_values = []
    for color_hex, color_name in CSS3_HEX_TO_NAMES.items():
        names.append(color_name)
        rgb_values.append(hex_to_rgb(color_hex))
    kdt_db = KDTree(rgb_values)
    distance, index = kdt_db.query(rgb_tuple)
    return names[index]



def get_cloth_color(image):
    max_score = 0.0001
    dominant_color = None
    for count, (r, g, b) in image.getcolors(image.size[0]*image.size[1]):
        # compute saturation
        saturation = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)[1]
        y = min(abs(r*2104 + g*4130 + b*802 + 4096 + 131072) >> 13, 235)
        y = (y - 16.0) / (235 - 16)
        if y > 0.9:
            continue
        score = (saturation + 0.1) * count
        if score > max_score:
            max_score = score
            dominant_color = (r, g, b)
    return convert_rgb_to_names(dominant_color)
    

def color_classification(single_path):
    """
    Input: path to clothing image
    Output: color group string (one of 12 + black/white/gray/multi)
    """
    image = Image.open(single_path)
    image = image.convert('RGB')
    css_color = get_cloth_color(image)
    color_group = map_color_to_group(css_color)
    return color_group
    
    
    
####################################
def single_helper(train_images, my_model, lelist):
    """
    This function is a helper function of the one below to use pre-trained model to predict.
    Input is an image, one of three sub-model, a encoder list
    Output is a list which is the result from the model
    """
    # Convert the predicted result encoded as a number back to the original string
    # and then make them a list contains all the informations
    my_predictions = my_model.predict(train_images)
    result = []
    type_predicted_label = np.argmax(my_predictions[0][0])
    result.append(lelist[0][type_predicted_label])
    type_predicted_label = np.argmax(my_predictions[1][0])
    result.append(lelist[1][type_predicted_label])
    type_predicted_label = np.argmax(my_predictions[2][0])
    result.append(lelist[2][type_predicted_label])
    type_predicted_label = np.argmax(my_predictions[3][0])
    result.append(lelist[3][type_predicted_label])
    type_predicted_label = np.argmax(my_predictions[4][0])
    result.append(lelist[4][type_predicted_label])
    return result




def single_classification(single_path):
    """
    Input: path to a clothing image
    Output: tuple (subtype, info_str, res_dict)
    res_dict contains:
        - subtype: top/bottom/foot
        - gender
        - color_group
        - season
        - usage
        - path
    """
    if not _ensure_models_loaded() or sub_model is None:
        return "top", "fallback", {
        "subtype": "Tshirts",
        "gender": "Women",
        "color": "Black",
        "color_group": 0,
        "season": "Summer",
        "usage": "Casual",
        "path": single_path,
    }
    
    # Load image for models
    train_images = np.zeros((1, 80, 60, 3))
    img = cv2.imread(single_path)
    if img is None or not hasattr(img, "shape"):
        img = image.load_img(single_path, target_size=(80, 60))
        img = np.array(img)
    elif img.shape != (80, 60, 3):
        img = image.load_img(single_path, target_size=(80, 60))
        img = np.array(img)

    train_images[0] = img

    # -----------------------
    # Predict subtype (top/bottom/foot)
    # -----------------------
    result2 = sub_list[np.argmax(sub_model.predict(train_images))]

    # -----------------------
    # Predict full attributes
    # -----------------------
    if result2 == "top":
        task_model = _get_task_model("top")
        if task_model is None:
            return "top", "fallback", {
                "subtype": "Tshirts",
                "gender": "Women",
                "color": "Black",
                "color_group": 0,
                "season": "Summer",
                "usage": "Casual",
                "path": single_path,
            }
        res = single_helper(train_images, task_model, top_list)
    elif result2 == "bottom":
        task_model = _get_task_model("bottom")
        if task_model is None:
            return "top", "fallback", {
                "subtype": "Tshirts",
                "gender": "Women",
                "color": "Black",
                "color_group": 0,
                "season": "Summer",
                "usage": "Casual",
                "path": single_path,
            }
        res = single_helper(train_images, task_model, bottom_list)
    elif result2 == "foot":
        task_model = _get_task_model("foot")
        if task_model is None:
            return "top", "fallback", {
                "subtype": "Tshirts",
                "gender": "Women",
                "color": "Black",
                "color_group": 0,
                "season": "Summer",
                "usage": "Casual",
                "path": single_path,
            }
        res = single_helper(train_images, task_model, foot_list)
    else:
        task_model = _get_task_model("foot")
        if task_model is None:
            return "top", "fallback", {
                "subtype": "Tshirts",
                "gender": "Women",
                "color": "Black",
                "color_group": 0,
                "season": "Summer",
                "usage": "Casual",
                "path": single_path,
            }
        res = single_helper(train_images, task_model, foot_list)

    # Add image path
    res.append(single_path)

    # -----------------------
    # Get color group
    # -----------------------
    color_group_name = color_classification(single_path)
    color_group_index = COLOR_GROUP_INDEX.get(color_group_name, COLOR_GROUP_INDEX[MULTI_COLOR])

    # -----------------------
    # Build res dict
    # -----------------------
    res_dict = {
        "subtype": res[0],
        "gender": res[1],
        "color": res[2],
        "color_group": color_group_index,
        "season": res[3],
        "usage": res[4],
        "path": single_path,
    }

    # Info string (optional)
    info_str = f"{res[0]}, {res[1]}, {color_group_name}, {res[3]}, {res[4]}, {single_path}"

    return result2, info_str, res_dict


def find_combo_by_top(top_color_group, combotype):
    """
    Recommend bottom and shoe color based on top color and angle (combotype)
    top_color_group: 0–11 for main colors, 12–14 for neutral, 15 for multi
    combotype: 0, 30, 60, 90 degrees
    Returns: (bottom_color_group, shoes_color_group)
    """
    co = combotype // 30

    # multi-color top
    if top_color_group == 15:
        bottom_color_group = random.choice([12,13,14])
        shoes_color_group = random.choice([c for c in [12,13,14] if c != bottom_color_group])
        return bottom_color_group, shoes_color_group

    # neutral top (black, white, gray)
    elif top_color_group in [12,13,14]:
        bottom_color_group = random.choice([12,13,14])
        shoes_color_group = random.choice([c for c in [12,13,14] if c != bottom_color_group])
        return bottom_color_group, shoes_color_group

    # colored top (0–11)
    else:
        bottom_color_group = (top_color_group + random.choice([-co, co])) % 12
        shoes_color_group = (top_color_group - random.choice([-co, co])) % 12
        return bottom_color_group, shoes_color_group


def current_season() -> str:
    """Calendar season in the same labels as the dataset (e.g. for default filtering)."""
    m = date.today().month
    if m in (3, 4, 5):
        return "Spring"
    if m in (6, 7, 8):
        return "Summer"
    if m in (9, 10, 11):
        return "Fall"
    return "Winter"