import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, StringVar, OptionMenu
from PIL import Image, ImageTk

from outfit_recommender import OutfitRecommender
from py.recognition_module import (
    COLOR_GROUP_INDEX,
    MULTI_COLOR,
    bottom_list,
    foot_list,
    map_color_to_group,
    top_list,
)

# -----------------------------
# Initialize recommender
# -----------------------------
recommender = OutfitRecommender()

# -----------------------------
# Helper: display image
# -----------------------------
def show_image(path, label):
    try:
        img = Image.open(path)
        img = img.resize((150, 150))
        img = ImageTk.PhotoImage(img)
        label.config(image=img)
        label.image = img
    except Exception as e:
        messagebox.showerror("Image Error", str(e))

# -----------------------------
# Add clothing item
# -----------------------------
def add_clothing():
    file_path = filedialog.askopenfilename(
        title="Select clothing image",
        filetypes=[("Image files", "*.jpg *.jpeg *.png")]
    )
    if not file_path:
        return

    try:
        subtype, item = recommender.add_image(file_path)

        # Use the actual keys in res_dict
        item_type = str(item.get("subtype", "Unknown"))
        item_season = str(item.get("season", "Unknown"))
        item_usage = str(item.get("usage", "Unknown"))
        item_gender = str(item.get("gender", "Unknown"))

        text = f"{item_type} | {item_season} | {item_usage} | {item_gender}"

        if subtype == "top":
            tops_listbox.insert(tk.END, text)
        elif subtype == "bottom":
            bottoms_listbox.insert(tk.END, text)
        elif subtype == "foot":
            shoes_listbox.insert(tk.END, text)

        messagebox.showinfo("Added", f"{subtype} added successfully!")

    except Exception as e:
        messagebox.showerror("Error", str(e))
# -----------------------------
# Delete item
# -----------------------------
def delete_item():
    try:
        if tops_listbox.curselection():
            idx = tops_listbox.curselection()[0]
            tops_listbox.delete(idx)
            del recommender.top[idx]
        elif bottoms_listbox.curselection():
            idx = bottoms_listbox.curselection()[0]
            bottoms_listbox.delete(idx)
            del recommender.bottom[idx]
        elif shoes_listbox.curselection():
            idx = shoes_listbox.curselection()[0]
            shoes_listbox.delete(idx)
            del recommender.shoes[idx]
        else:
            messagebox.showwarning("Delete", "Select an item first")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# -----------------------------
# Edit item
# -----------------------------
def edit_item(root):
    try:
        item = None
        listbox = None
        idx = None
        attr_list = None

        # Determine which listbox is selected
        if tops_listbox.curselection():
            idx = tops_listbox.curselection()[0]
            item = recommender.top[idx]
            listbox = tops_listbox
            attr_list = top_list
        elif bottoms_listbox.curselection():
            idx = bottoms_listbox.curselection()[0]
            item = recommender.bottom[idx]
            listbox = bottoms_listbox
            attr_list = bottom_list
        elif shoes_listbox.curselection():
            idx = shoes_listbox.curselection()[0]
            item = recommender.shoes[idx]
            listbox = shoes_listbox
            attr_list = foot_list
        else:
            messagebox.showwarning("Edit", "Select an item first")
            return

        # Create a popup window
        edit_window = tk.Toplevel(root)
        edit_window.title("Edit Item")

        # Create StringVars for dropdowns
        type_var = StringVar(value=item["subtype"])
        gender_var = StringVar(value=item["gender"])
        season_var = StringVar(value=item["season"])
        usage_var = StringVar(value=item["usage"])

        # Type
        tk.Label(edit_window, text="Type:").grid(row=0, column=0, padx=5, pady=5)
        OptionMenu(edit_window, type_var, *attr_list[0]).grid(row=0, column=1, padx=5, pady=5)

        # Gender
        tk.Label(edit_window, text="Gender:").grid(row=1, column=0, padx=5, pady=5)
        OptionMenu(edit_window, gender_var, *attr_list[1]).grid(row=1, column=1, padx=5, pady=5)

        _colors = attr_list[2]
        _default_color = item.get("color") or _colors[0]
        if _default_color not in _colors:
            _default_color = _colors[0]
        color_var = StringVar(value=_default_color)
        tk.Label(edit_window, text="Color:").grid(row=2, column=0, padx=5, pady=5)
        OptionMenu(edit_window, color_var, *_colors).grid(row=2, column=1, padx=5, pady=5)

        # Season
        tk.Label(edit_window, text="Season:").grid(row=3, column=0, padx=5, pady=5)
        OptionMenu(edit_window, season_var, *attr_list[3]).grid(row=3, column=1, padx=5, pady=5)

        # Usage
        tk.Label(edit_window, text="Usage:").grid(row=4, column=0, padx=5, pady=5)
        OptionMenu(edit_window, usage_var, *attr_list[4]).grid(row=4, column=1, padx=5, pady=5)

        def save_changes():
            item["subtype"] = type_var.get()
            item["gender"] = gender_var.get()
            item["season"] = season_var.get()
            item["usage"] = usage_var.get()
            item["color"] = color_var.get()
            gname = map_color_to_group(item["color"])
            item["color_group"] = COLOR_GROUP_INDEX.get(gname, COLOR_GROUP_INDEX[MULTI_COLOR])
            # Update listbox display
            text = f"{item['subtype']} | {item['season']} | {item['usage']} | {item['gender']}"
            listbox.delete(idx)
            listbox.insert(idx, text)
            messagebox.showinfo("Edit", "Item updated successfully!")
            edit_window.destroy()

        tk.Button(edit_window, text="Save", command=save_changes).grid(row=5, column=0, columnspan=2, pady=10)

    except Exception as e:
        messagebox.showerror("Error", str(e))

# -----------------------------
# Generate outfit
# -----------------------------
def generate_outfit():
    try:
        outfit = recommender.generate_outfit()
        show_image(outfit["top"]["path"], top_image)
        show_image(outfit["bottom"]["path"], bottom_image)
        show_image(outfit["shoes"]["path"], shoes_image)
    except Exception as e:
        messagebox.showerror("Error", str(e))

# -----------------------------
# Run UI
# -----------------------------
def run_ui():
    global tops_listbox, bottoms_listbox, shoes_listbox
    global top_image, bottom_image, shoes_image

    root = tk.Tk()
    root.title("AI Outfit Recommender")
    root.geometry("950x600")

    # Buttons
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    tk.Button(button_frame, text="Add Clothing", command=add_clothing, width=20).grid(row=0, column=0, padx=10)
    tk.Button(button_frame, text="Generate Outfit", command=generate_outfit, width=20).grid(row=0, column=1, padx=10)
    tk.Button(button_frame, text="Delete Selected", command=delete_item, width=20).grid(row=0, column=2, padx=10)
    tk.Button(button_frame, text="Edit Item", command=lambda: edit_item(root), width=20).grid(row=0, column=3, padx=10)
    # Wardrobe Lists
    wardrobe_frame = tk.Frame(root)
    wardrobe_frame.pack(pady=10)

    # Tops
    tops_frame = tk.Frame(wardrobe_frame)
    tops_frame.grid(row=0, column=0, padx=20)
    tk.Label(tops_frame, text="Tops").pack()
    tops_listbox = tk.Listbox(tops_frame, width=50, height=10)
    tops_listbox.pack()

    # Bottoms
    bottoms_frame = tk.Frame(wardrobe_frame)
    bottoms_frame.grid(row=0, column=1, padx=20)
    tk.Label(bottoms_frame, text="Bottoms").pack()
    bottoms_listbox = tk.Listbox(bottoms_frame, width=50, height=10)
    bottoms_listbox.pack()

    # Shoes
    shoes_frame = tk.Frame(wardrobe_frame)
    shoes_frame.grid(row=0, column=2, padx=20)
    tk.Label(shoes_frame, text="Shoes").pack()
    shoes_listbox = tk.Listbox(shoes_frame, width=50, height=10)
    shoes_listbox.pack()

    # Outfit Display
    outfit_frame = tk.Frame(root)
    outfit_frame.pack(pady=30)

    # Top image
    top_frame = tk.Frame(outfit_frame)
    top_frame.grid(row=0, column=0, padx=30)
    tk.Label(top_frame, text="Top").pack()
    top_image = tk.Label(top_frame)
    top_image.pack()

    # Bottom image
    bottom_frame = tk.Frame(outfit_frame)
    bottom_frame.grid(row=0, column=1, padx=30)
    tk.Label(bottom_frame, text="Bottom").pack()
    bottom_image = tk.Label(bottom_frame)
    bottom_image.pack()

    # Shoes image
    shoes_frame2 = tk.Frame(outfit_frame)
    shoes_frame2.grid(row=0, column=2, padx=30)
    tk.Label(shoes_frame2, text="Shoes").pack()
    shoes_image = tk.Label(shoes_frame2)
    shoes_image.pack()

    root.mainloop()
