from datetime import date, timedelta
from typing import Optional

import cv2
import numpy as np
import streamlit as st
from config.settings import CATEGORY_OPTIONS
from PIL import Image
from services.barcode import add_item_from_barcode, detect_barcodes_in_image, lookup_barcode_product


def process_uploaded_image(uploaded_file) -> Optional[str]:
    """Process uploaded image and detect barcode."""
    try:
        image = Image.open(uploaded_file)
        image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        detected = detect_barcodes_in_image(image_cv)

        if detected:
            return detected[0]  # Return first barcode found
        return None
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return None


def handle_barcode_scan() -> None:
    """Handle barcode scanning and product recognition (manual, camera snapshot, or image upload)."""
    st.subheader("📱 Barcode Scanner")

    # Persist detected barcode/product across reruns so submit works
    detected_barcode = st.session_state.get("detected_barcode")
    product_info = st.session_state.get("detected_product_info")

    def clear_detected() -> None:
        st.session_state.detected_barcode = None
        st.session_state.detected_product_info = None

    scan_mode = st.radio(
        "Scanning method:",
        ["📝 Manual Entry", "📸 Camera Snapshot", "🖼️ Upload Image"],
        horizontal=True,
        key="barcode_scan_mode",
    )

    new_barcode: Optional[str] = None

    # Mode 1: Manual Entry
    if scan_mode == "📝 Manual Entry":
        barcode_input = st.text_input(
            "Enter barcode",
            placeholder="Enter EAN/UPC barcode (e.g., 5901234123457)",
            key="barcode_input",
        )

        if st.button("🔍 Look up product", use_container_width=True, key="barcode_lookup_manual"):
            if barcode_input:
                new_barcode = barcode_input
            else:
                st.warning("Please enter a barcode")

    # Mode 2: Camera snapshot (built-in Streamlit camera)
    elif scan_mode == "📸 Camera Snapshot":
        camera_image = st.camera_input("Capture barcode", key="barcode_camera_input")
        if camera_image is not None:
            st.image(camera_image, caption="Captured image", use_container_width=True)
            if st.button("🔍 Scan captured image", use_container_width=True, key="barcode_scan_camera"):
                with st.spinner("Scanning photo..."):
                    new_barcode = process_uploaded_image(camera_image)
                    if new_barcode:
                        st.success(f"✓ Barcode detected: `{new_barcode}`")
                    else:
                        st.warning("No barcode found. Try a closer, well-lit photo.")

    # Mode 3: Image Upload
    elif scan_mode == "🖼️ Upload Image":
        uploaded_file = st.file_uploader(
            "Upload image with barcode",
            type=["jpg", "jpeg", "png", "bmp"],
            key="barcode_image_upload",
        )

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded image", use_container_width=True)

            if st.button("🔍 Scan image for barcodes", use_container_width=True, key="barcode_scan_image"):
                with st.spinner("Scanning image..."):
                    new_barcode = process_uploaded_image(uploaded_file)
                    if new_barcode:
                        st.success(f"✓ Barcode detected: `{new_barcode}`")
                    else:
                        st.warning("No barcode found in image. Try a clearer photo.")

    # If a new barcode was found this run, look up and persist
    if new_barcode:
        with st.spinner("Looking up product..."):
            product = lookup_barcode_product(new_barcode)

        if product:
            st.session_state.detected_barcode = new_barcode
            st.session_state.detected_product_info = product
            detected_barcode = new_barcode
            product_info = product
        else:
            clear_detected()

    # Render product details and add form if we have one
    if detected_barcode and product_info:
        st.divider()
        st.success(f"✓ Product found: **{product_info.get('name')}**")

        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.caption(f"**Brand:** {product_info.get('brand', 'N/A')}")
            st.caption(f"**Category:** {product_info.get('category', 'Other')}")
        with col_info2:
            if product_info.get("image_url"):
                st.image(product_info["image_url"], width=150)

        with st.form("barcode_add_form"):
            st.subheader("Add to inventory")
            qty = st.number_input("Quantity", min_value=1, value=1, key="barcode_qty")

            suggested_expiry_str = product_info.get("suggested_expiry_days")
            suggested_expiry = date.fromisoformat(suggested_expiry_str) if suggested_expiry_str else date.today() + timedelta(days=30)

            expiry = st.date_input("Expiry date", value=suggested_expiry, min_value=date.today(), key="barcode_expiry")

            current_category = product_info.get("category", "Other") or "Other"
            category_choice = st.selectbox(
                "Category",
                CATEGORY_OPTIONS,
                index=(CATEGORY_OPTIONS.index(current_category) if current_category in CATEGORY_OPTIONS else CATEGORY_OPTIONS.index("Other")),
                key="barcode_category_override",
            )

            submitted = st.form_submit_button("✓ Add to inventory", type="primary", use_container_width=True)

        if submitted:
            with st.spinner("Adding item..."):
                result = add_item_from_barcode(detected_barcode, int(qty), expiry, category_choice)

            if result:
                st.success(result.get("message", "✓ Item added to inventory!"))
                clear_detected()
                st.session_state.inventory_dirty = True
                st.rerun()

        if st.button("Clear current scan", type="secondary"):
            clear_detected()
            st.rerun()
