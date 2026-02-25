from typing import Optional, Any, Dict, List
import streamlit as st
import numpy as np
import cv2
from datetime import date

from services.client import APIError, api_request


def lookup_barcode_product(barcode: str) -> Optional[Dict[str, Any]]:
    """Look up product information by barcode."""
    try:
        result = api_request("get", f"/barcode/lookup/{barcode}")
        return result if isinstance(result, dict) else None
    except APIError as err:
        st.error(f"Barcode lookup failed: {err.message}")
        return None


def add_item_from_barcode(
    barcode: str,
    quantity: int = 1,
    expiry_date: Optional[date] = None,
    category_override: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Add item to inventory from barcode scan."""
    params = {
        "household_id": st.session_state.household_id,
        "barcode": barcode,
        "quantity": quantity,
    }
    if expiry_date:
        params["expiry_date"] = expiry_date.isoformat()
    if category_override:
        params["category_override"] = category_override

    try:
        result = api_request("post", "/barcode/add-from-barcode", params=params)
        return result if isinstance(result, dict) else None
    except APIError as err:
        st.error(f"Failed to add item: {err.message}")
        return None


def detect_barcodes_in_image(image: np.ndarray) -> List[str]:
    """Detect and decode barcodes using OpenCV's built-in detector (no external DLLs)."""
    try:
        detector = cv2.barcode_BarcodeDetector()

        # detector.detectAndDecode returns (retval, decoded_info, decoded_type)
        ok, decoded_info, _decoded_type = detector.detectAndDecode(image)

        detected: List[str] = []
        if ok and decoded_info:
            for value in decoded_info:
                if value:
                    detected.append(value)

        # Fallback: retry with grayscale if nothing found
        if not detected:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            ok, decoded_info, _decoded_type = detector.detectAndDecode(gray)
            if ok and decoded_info:
                detected.extend([v for v in decoded_info if v])

        # Additional fallback: increase contrast
        if not detected:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            ok, decoded_info, _decoded_type = detector.detectAndDecode(enhanced)
            if ok and decoded_info:
                detected.extend([v for v in decoded_info if v])

        return detected
    except Exception as e:
        st.warning(f"Error detecting barcode: {e}")
        return []
