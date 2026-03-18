from datetime import date
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import streamlit as st
from services.client import APIError, api_request
from state.adapter import get_household_id


def _normalize_decoded_values(values: Any) -> List[str]:
    """Normalize OpenCV decoded barcode output into a clean list of strings."""
    if values is None:
        return []

    if isinstance(values, np.ndarray):
        values = values.tolist()

    if isinstance(values, (list, tuple)):
        normalized: List[str] = []
        for value in values:
            if isinstance(value, bytes):
                value = value.decode(errors="ignore")
            if isinstance(value, str):
                stripped = value.strip()
                if stripped:
                    normalized.append(stripped)
        return normalized

    if isinstance(values, bytes):
        values = values.decode(errors="ignore")

    if isinstance(values, str):
        stripped = values.strip()
        return [stripped] if stripped else []

    return []


def _decode_with_detector(detector: cv2.barcode_BarcodeDetector, image: np.ndarray) -> List[str]:
    """Decode barcodes from an image while handling OpenCV version output differences."""
    result = detector.detectAndDecode(image)

    if not isinstance(result, tuple):
        return _normalize_decoded_values(result)

    # Common signature: (ok, decoded_info, decoded_type)
    if len(result) >= 2:
        decoded = _normalize_decoded_values(result[1])
        if decoded:
            return decoded

    # Fallback for versions that may return decoded value first
    if len(result) >= 1:
        return _normalize_decoded_values(result[0])

    return []


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
        "household_id": get_household_id(),
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

        detected: List[str] = _decode_with_detector(detector, image)

        # Fallback: retry with grayscale if nothing found
        if not detected:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            detected.extend(_decode_with_detector(detector, gray))

        # Additional fallback: increase contrast
        if not detected:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            detected.extend(_decode_with_detector(detector, enhanced))

        # Deduplicate while preserving order
        return list(dict.fromkeys(detected))
    except Exception as e:
        st.warning(f"Error detecting barcode: {e}")
        return []
