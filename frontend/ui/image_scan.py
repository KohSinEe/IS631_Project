import streamlit as st
import requests
import base64
from PIL import Image
import io
from datetime import datetime, timedelta
import os

from services.inventory import create_inventory_item
from config.settings import CATEGORY_OPTIONS, UNIT_OPTIONS

# environment variables should already be loaded by frontend/app.py; just read
VISION_API_KEY = os.getenv("VISION_API_KEY")

# if running the module standalone or the key wasn't picked up above, try
# loading from parent directory explicitly
if not VISION_API_KEY:
    from dotenv import load_dotenv

    load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))
    VISION_API_KEY = os.getenv("VISION_API_KEY")


def handle_image_scan() -> None:
    """Simple food‑recognition UI using Google Vision labels."""
    st.subheader("📷 Photo scanner")

    if not VISION_API_KEY:
        st.error("VISION_API_KEY not configured in .env")
        return

    uploaded_file = st.file_uploader("Upload a food image", type=["jpg", "jpeg", "png"])
    if not uploaded_file:
        return

    file_bytes = uploaded_file.read()
    image = Image.open(io.BytesIO(file_bytes))
    st.image(image, caption="Uploaded image", use_container_width=True)

    # call the Vision API
    encoded_image = base64.b64encode(file_bytes).decode()
    url = f"https://vision.googleapis.com/v1/images:annotate?key={VISION_API_KEY}"
    body = {
        "requests": [
            {"image": {"content": encoded_image}, "features": [{"type": "LABEL_DETECTION"}]}
        ]
    }
    response = requests.post(url, json=body)
    if response.status_code != 200:
        st.error(f"Vision API request failed ({response.status_code})")
        st.write(response.text)
        return
    result = response.json()
    labels = result.get("responses", [{}])[0].get("labelAnnotations", [])
    detected_foods = [(l["description"], l["score"]) for l in labels if l.get("score", 0) > 0.9]
    detected_foods.sort(key=lambda x: x[1], reverse=True)
    food_names = [name for name, _ in detected_foods]

    # always offer manual entry in case detection is inaccurate
    selected_food = None
    if food_names:
        st.subheader("Detected foods")
        selected_food = st.selectbox("Select food to store in inventory", food_names)
    manual = st.text_input("Or enter food name manually", value="")
    if manual.strip():
        # if user typed something, give it priority over detection
        selected_food = manual.strip()

    if not selected_food:
        # nothing chosen yet, and manual is empty; keep a placeholder for adding
        selected_food = ""

    quantity = st.number_input("Quantity", min_value=0.0, step=0.1)
    unit = st.selectbox("Unit", UNIT_OPTIONS + ["Other"])
    if unit == "Other":
        unit = st.text_input("Enter unit manually", value="")

    purchase_date = st.date_input("Purchase date", datetime.today())

    # suggest an expiry based on the selected food name where possible
    from utils.inventory import suggest_expiry_for_name, FOOD_TO_CATEGORY

    default_expiry = suggest_expiry_for_name(selected_food, purchase_date)
    expiry = st.date_input("Expiry date", default_expiry)

    # default category based on food-to-category mapping; fall back to Other
    default_cat = "Other"
    if selected_food:
        default_cat = FOOD_TO_CATEGORY.get(selected_food.lower().strip(), "Other")
        # ensure matches one of the options (case-insensitive)
        if default_cat not in CATEGORY_OPTIONS:
            default_cat = "Other"
    category = st.selectbox(
        "Category",
        CATEGORY_OPTIONS,
        index=(
            CATEGORY_OPTIONS.index(default_cat)
            if default_cat in CATEGORY_OPTIONS
            else CATEGORY_OPTIONS.index("Other")
        ),
    )

    if st.button("Add to inventory"):
        if not selected_food:
            st.error("Food name is required")
        else:
            item = {
                "name": selected_food,
                "quantity": float(quantity),
                "unit": unit,
                "expiry_date": expiry.isoformat(),
                "category": category,
            }
            create_inventory_item(item)
            st.success(f"{selected_food} added to inventory")
            st.session_state.inventory_dirty = True
            st.rerun()
