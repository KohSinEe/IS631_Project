# app.py
import streamlit as st
import requests
import base64
from PIL import Image
import io
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import db as db  # <-- import the database module

# ------------------ Setup ------------------
load_dotenv()
VISION_API_KEY = os.getenv("VISION_API_KEY")
if not VISION_API_KEY:
    st.error("Check that your Google Vision API key is set in .env")
    st.stop()

# ------------------ Initialize DB ------------------
db.create_table()

# ------------------ Category Expiry Defaults ------------------
category_expiry_days = {
    "dairy": 7,
    "fruit": 14,
    "vegetable": 21,
    "spice": 180,
    "grain": 180,
    "meat": 7
}
food_to_category = {
    "milk": "dairy",
    "cheese": "dairy",
    "ginger": "vegetable",
    "potato": "vegetable",
    "banana": "fruit",
    "orange": "fruit",
    "onion": "vegetable",
    "noodles": "grain"
}

# ------------------ Streamlit UI ------------------
st.title("Fridge Buddy Inventory with Image Scanner")
uploaded_file = st.file_uploader("Upload a food image", type=["jpg","jpeg","png"])

if uploaded_file:
    file_bytes = uploaded_file.read()
    image = Image.open(io.BytesIO(file_bytes))
    st.image(image, caption="Uploaded Image", use_container_width=True)

    # Google Vision API
    encoded_image = base64.b64encode(file_bytes).decode()
    url = f"https://vision.googleapis.com/v1/images:annotate?key={VISION_API_KEY}"
    body = {"requests":[{"image":{"content":encoded_image},"features":[{"type":"LABEL_DETECTION"}]}]}
    response = requests.post(url, json=body)
    result = response.json()

    labels = result.get("responses", [{}])[0].get("labelAnnotations", [])
    detected_foods = [(label["description"], label["score"]) for label in labels if label["score"]>0.5]
    detected_foods.sort(key=lambda x: x[1], reverse=True)
    food_names = [name for name, score in detected_foods]

    if food_names:
        st.subheader("Detected Foods")
        selected_food = st.selectbox("Select food to store in inventory", food_names)
    else:
        selected_food = st.text_input("Enter food name manually")

    # Quantity
    quantity = st.number_input("Quantity", min_value=0.0, step=0.1)

    # Units
    unit_options = ["g","kg","ml","liter","pieces","Other"]
    unit = st.selectbox("Unit", unit_options)
    if unit == "Other":
        unit = st.text_input("Enter unit manually", value="")

    # Purchase date
    purchase_date = st.date_input("Purchase Date", datetime.today())

    # Auto-suggest expiry
    selected_food_lower = selected_food.lower().strip()
    category = food_to_category.get(selected_food_lower)
    suggested_days = category_expiry_days.get(category, 7)
    default_expiry = purchase_date + timedelta(days=suggested_days)
    expiry_date = st.date_input("Expiry Date", default_expiry)

    # Add to inventory
    if st.button("Add to Inventory"):
        db.add_item(selected_food, quantity, unit, purchase_date, expiry_date)
        st.success(f"{selected_food} added to inventory!")

# ------------------ View Inventory ------------------
st.subheader("Current Inventory")
rows = db.get_inventory()
for row in rows:
    st.write(f"{row[1]}: {row[2]} {row[3]}, Purchased: {row[4]}, Expires: {row[5]}")