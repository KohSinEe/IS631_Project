Image Scanner Setup

The image scanner detects food items from uploaded photos and feeds them into your inventory. It uses Roboflow AI for object detection.

Prerequisites:
Roboflow API Key – you need a valid key from your Roboflow project.
Python packages: inference_sdk, streamlit, requests (already in your requirements.txt).
Backend running (FastAPI) to save detected items.

Steps to Run
Make sure your backend is running:
cd backend
uvicorn main:app --reload


Run the frontend (Streamlit):
cd frontend
python streamlit run app.py
Open http://localhost:8501
 in a browser.

How to Use
Choose Image Scan in the Streamlit app.
Upload a photo of your food item(s).
The AI will detect items and display the detected class.
You can adjust the item name, quantity, storage type, and expiry before saving.
Click Add/Update Item to store it in the inventory.
