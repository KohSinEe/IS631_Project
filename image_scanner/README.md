A lightweight inventory app that uses Google Vision API to detect food from images 📸, track quantities 🔢, categories 🗂, and automatically suggest expiry dates ⏳.

Features:

Upload food images and auto-detect items.

Auto-suggest expiry dates by category (editable).

Track quantity in Singapore metric units (g, kg, ml, L, pieces).

Manual input for name, quantity, unit, purchase date, and expiry 📝.

View full inventory details 💾.

Database:

SQLite file: inventory.db

Table: inventory with columns id, name, quantity, unit, expiry_date, category, image_path, created_at, updated_at.

Default Expiry by Category:

Category	Days
Dairy 🥛	7
Fruits 🍌	14
Vegetables 🥕	21
Meat 🥩	7
Other ❓	7

Usage:
Upload an image, select detected food or enter manually, set quantity/unit and purchase date, then add to inventory ✅.

----To run app.py----
cd image_scanner
pip install --user -r requirements.txt
python -m streamlit run app.py
Upload PNG/JPEG/JPG image file