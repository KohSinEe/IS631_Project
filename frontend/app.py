import streamlit as st
import requests
from inference_sdk import InferenceHTTPClient
import tempfile


# --- Roboflow Setup ---
ROBOFLOW_API_KEY = "Km2rdbKvwzJU0h2EOL7p"
WORKSPACE_NAME = "fridge-buddy"
WORKFLOW_ID = "rf-detr"
BACKEND_URL = "http://127.0.0.1:8000/add_item/"

client = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key=ROBOFLOW_API_KEY
)

st.title("Fridge Buddy: Object Detection & Inventory")

# Option: Image scan or manual input
option = st.radio("Choose input method:", ["Image Scan", "Manual Input"])

item_name = ""
quantity = 1.0
storage_type = "Fridge"
expiry_days = 7

if option == "Image Scan":
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Image", width=400)

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name

        with st.spinner("Detecting objects..."):
            try:
                result = client.run_workflow(
                    workspace_name=WORKSPACE_NAME,
                    workflow_id=WORKFLOW_ID,
                    images={"image": tmp_file_path},
                    use_cache=True
                )

                # Extract first detected object
                item_detected = None
                if isinstance(result, list):
                    for batch in result:
                        preds = batch.get("predictions", {}).get("predictions", [])
                        if preds:
                            item_detected = preds[0]
                            break

                if item_detected:
                    item_name = item_detected.get("class", "")
                    st.success(f"Detected item: {item_name}")
                else:
                    st.warning("No objects detected. Please use manual input below.")

            except Exception as e:
                st.error(f"Detection error: {e}")

if option == "Manual Input" or not item_name:
    item_name = st.text_input("Enter item name:")

quantity = st.number_input(f"Quantity for {item_name}", min_value=0.0, value=1.0)
storage_type = st.selectbox(f"Storage Type for {item_name}", ["Fridge", "Freezer", "Pantry"])
expiry_days = st.number_input(f"Expiry (days) for {item_name}", min_value=0, value=7)

if st.button("Add/Update Item"):
    if item_name.strip():
        payload = {
            "item_name": item_name.strip(),
            "quantity": quantity,
            "storage_type": storage_type,
            "expiry_days": expiry_days
        }
        try:
            response = requests.post(BACKEND_URL, json=payload)
            if response.status_code == 200:
                st.success(response.json().get("message", "Item added successfully."))
            else:
                st.error(response.json().get("error", "Error adding item."))
        except Exception as e:
            st.error(f"Request failed: {e}")
