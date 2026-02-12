"""Streamlit UI for the smart household food management system."""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import requests
import streamlit as st
from PIL import Image

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
EXPIRY_ALERT_DAYS = int(os.getenv("EXPIRY_ALERT_DAYS", "5"))
CATEGORY_OPTIONS = [
    "Dairy",
    "Meat",
    "Seafood",
    "Vegetables",
    "Fruits",
    "Beverages",
    "Condiments",
    "Leftovers",
    "Frozen",
    "Other",
]
UNIT_OPTIONS = ["pieces", "mL", "L", "g", "kg"]
SESSION_DEFAULTS = {
    "is_authenticated": False,
    "user": None,
    "household_id": None,
    "tokens": None,
    "inventory": [],
    "inventory_dirty": True,
    "category_filter": "All",
    "sort_by_expiry": True,
    "detected_barcode": None,
    "detected_product_info": None,
    # Form keys
    "login_email": "",
    "login_password": "",
    "register_email": "",
    "register_password": "",
    "register_name": "",
    "register_household": "",
}
CUSTOM_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&display=swap');
.stApp {
    background: radial-gradient(circle at top, #1e1b4b 0%, #0f172a 55%, #020617 100%);
    color: #f8fafc;
}
section[data-testid="stSidebar"] > div {
    background: rgba(15, 23, 42, 0.85);
    border-right: 1px solid rgba(148, 163, 184, 0.2);
}
html, body, [class*="css"], .stMarkdown, label, input, button {
    font-family: 'Space Grotesk', sans-serif;
}
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}
.metric-card {
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(148, 163, 184, 0.3);
    border-radius: 1rem;
    padding: 1rem 1.25rem;
}
.metric-card h3 {
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.2rem;
    color: #94a3b8;
}
.metric-card p {
    font-size: 2rem;
    margin: 0;
    color: #f8fafc;
}
.pill-label {
    background: rgba(59, 130, 246, 0.15);
    border-radius: 999px;
    padding: 0.2rem 0.8rem;
    font-size: 0.85rem;
    color: #bfdbfe;
    display: inline-block;
}
.danger-pill {
    background: rgba(248, 113, 113, 0.15);
    color: #fecaca;
}
</style>
"""


class APIError(Exception):
    """Raised when the backend returns an error response."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def init_session_state() -> None:
    """Ensure Streamlit session state contains expected keys."""
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_session() -> None:
    """Reset authentication-related state."""
    for key, value in SESSION_DEFAULTS.items():
        st.session_state[key] = value


def get_api_client() -> requests.Session:
    """Return a per-user API client that stores cookies between calls."""
    if "api_client" not in st.session_state:
        st.session_state.api_client = requests.Session()
    return st.session_state.api_client


def api_request(method: str, path: str, **kwargs) -> Optional[Any]:
    """Wrap requests to the FastAPI backend with unified error handling."""
    session = get_api_client()
    url = f"{API_BASE_URL}{path}"
    timeout = kwargs.pop("timeout", 15)

    try:
        response = session.request(method, url, timeout=timeout, **kwargs)
    except requests.RequestException as exc:
        raise APIError("Network error while reaching the API") from exc

    if response.status_code >= 400:
        detail: Any = None
        try:
            payload = response.json()
            detail = payload.get("detail") if isinstance(payload, dict) else payload
        except ValueError:
            detail = response.text
        message = detail or "Request failed"
        raise APIError(str(message), response.status_code)

    if response.status_code == 204 or not response.content:
        return None

    try:
        return response.json()
    except ValueError:
        return response.text


def register_user(email: str, password: str, name: Optional[str], household_name: Optional[str]) -> Dict[str, Any]:
    payload = {
        "email": email,
        "password": password,
        "name": name or None,
        "household_name": household_name or None,
    }
    return api_request("post", "/auth/register", json=payload)  # type: ignore[return-value]


def login_user(email: str, password: str) -> None:
    data = {"username": email, "password": password}
    api_request("post", "/auth/login", data=data)
    profile = api_request("get", "/users/me")

    if not isinstance(profile, dict):
        raise APIError("Unexpected profile payload")

    st.session_state.is_authenticated = True
    st.session_state.user = profile
    st.session_state.household_id = profile.get("household_id")
    st.session_state.inventory_dirty = True


def logout_user() -> None:
    try:
        api_request("post", "/auth/logout")
    except APIError:
        pass

    client = get_api_client()
    client.cookies.clear()
    reset_session()


def fetch_inventory() -> List[Dict[str, Any]]:
    household_id = st.session_state.household_id
    if not household_id:
        return []
    params = {"household_id": household_id}
    result = api_request("get", "/items", params=params)
    return result if isinstance(result, list) else []


def create_inventory_item(item_data: Dict[str, Any]) -> Dict[str, Any]:
    params = {"household_id": st.session_state.household_id}
    return api_request("post", "/items", params=params, json=item_data)  # type: ignore[return-value]


def adjust_inventory_quantity(item_id: int, change: int) -> Dict[str, Any]:
    params = {"household_id": st.session_state.household_id}
    payload = {"change": change}
    return api_request("patch", f"/items/{item_id}/quantity", params=params, json=payload)  # type: ignore[return-value]


def delete_inventory_item(item_id: int) -> None:
    params = {"household_id": st.session_state.household_id}
    api_request("delete", f"/items/{item_id}", params=params)


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


def parse_expiry(raw_value: str) -> date:
    """Convert ISO strings from the API to date objects."""
    dt_value = datetime.fromisoformat(raw_value)
    return dt_value.date()


def summarize_inventory(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    today = date.today()
    soon_cutoff = today + timedelta(days=EXPIRY_ALERT_DAYS)

    expiring = []
    overdue = 0
    for item in items:
        expiry_raw = item.get("expiry_date")
        if not expiry_raw:
            continue
        expiry = parse_expiry(expiry_raw)
        if expiry < today:
            overdue += 1
        elif expiry <= soon_cutoff:
            expiring.append({
                "name": item.get("name"),
                "expiry": expiry,
                "quantity": item.get("quantity"),
                "unit": item.get("unit"),
            })

    return {
        "total": len(items),
        "expiring": len(expiring),
        "overdue": overdue,
        "expiring_items": expiring,
    }


def ensure_inventory_loaded() -> None:
    if not st.session_state.is_authenticated or not st.session_state.household_id:
        st.session_state.inventory = []
        st.session_state.inventory_dirty = False
        return

    if st.session_state.inventory_dirty:
        st.session_state.inventory = fetch_inventory()
        st.session_state.inventory_dirty = False


def filter_inventory(items: List[Dict[str, Any]], category: str) -> List[Dict[str, Any]]:
    if category == "All":
        return items
    return [item for item in items if item.get("category") == category]


def render_metric(label: str, value: Any, column: st.delta_generator.DeltaGenerator) -> None:
    with column:
        st.markdown(
            f"<div class='metric-card'><h3>{label}</h3><p>{value}</p></div>",
            unsafe_allow_html=True,
        )


def render_public_view() -> None:
    st.markdown(
        """
        <div class="pill-label">Experience-first frontend</div>
        <h1>Smart Pantry Control Center</h1>
        <p>Connect to the FastAPI backend, invite your household, and steer every item from a focused Streamlit workspace.</p>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["Sign in", "Create account"])

    with tabs[0]:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Sign in")
        if submitted:
            if not email or not password:
                st.error("Email and password are required")
            else:
                try:
                    login_user(email, password)
                    st.toast("Signed in")
                    st.rerun()
                except APIError as err:
                    st.error(err.message)

    with tabs[1]:
        with st.form("register_form"):
            reg_email = st.text_input("Email", key="register_email")
            reg_password = st.text_input("Password", type="password", key="register_password")
            reg_name = st.text_input("Display name", key="register_name")
            reg_household = st.text_input("Household name (optional)", key="register_household")
            submitted = st.form_submit_button("Create account")
        if submitted:
            if not reg_email or not reg_password:
                st.error("Email and password are required")
            else:
                try:
                    register_user(reg_email, reg_password, reg_name, reg_household)
                    st.success("Account created. Please sign in.")
                except APIError as err:
                    st.error(err.message)


def render_inventory_table(items: List[Dict[str, Any]], sort_by_expiry: bool) -> List[Dict[str, Any]]:
    working = items.copy()
    if sort_by_expiry:
        working.sort(key=lambda entry: parse_expiry(entry["expiry_date"]) if entry.get("expiry_date") else date.max)

    rows: List[Dict[str, Any]] = []
    soon_cutoff = date.today() + timedelta(days=EXPIRY_ALERT_DAYS)
    for item in working:
        expiry_raw = item.get("expiry_date")
        if not expiry_raw:
            continue
        expiry = parse_expiry(expiry_raw)
        status = "Fresh"
        if expiry < date.today():
            status = "Expired"
        elif expiry <= soon_cutoff:
            status = "Expiring soon"
        rows.append(
            {
                "Item": item.get("name"),
                "Quantity": f"{item.get('quantity')} {item.get('unit')}",
                "Category": item.get("category"),
                "Expiry": expiry.strftime("%b %d, %Y"),
                "Status": status,
            }
        )

    if not rows:
        st.info("No items to display yet.")
        return working

    st.markdown("### Inventory overview")
    st.dataframe(rows, use_container_width=True, hide_index=True)
    return working


def render_expiry_alerts(summary: Dict[str, Any]) -> None:
    expiring_items = summary.get("expiring_items", [])
    if not expiring_items:
        return

    st.warning("Watch these items before they go bad:")
    for item in expiring_items:
        expiry = item["expiry"].strftime("%b %d")
        st.write(f"• {item['name']} — {item['quantity']} {item['unit']} by {expiry}")


def handle_add_item() -> None:
    with st.form("add_item_form"):
        st.subheader("Add to pantry")
        name = st.text_input("Item name", key="create_name")
        quantity = st.number_input("Quantity", min_value=0, step=1, key="create_quantity")
        unit = st.selectbox("Unit", UNIT_OPTIONS, key="create_unit")
        expiry = st.date_input("Expiry date", min_value=date.today(), key="create_expiry")
        category = st.selectbox("Category", CATEGORY_OPTIONS, key="create_category")
        submitted = st.form_submit_button("Save item")

    if submitted:
        if not name:
            st.error("Item name is required")
            return
        payload = {
            "name": name,
            "quantity": int(quantity),
            "unit": unit,
            "expiry_date": expiry.isoformat(),
            "category": category,
        }
        try:
            create_inventory_item(payload)
            st.success("Item added")
            st.session_state.inventory_dirty = True
            st.rerun()
        except APIError as err:
            st.error(err.message)


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
        key="barcode_scan_mode"
    )

    new_barcode: Optional[str] = None

    # Mode 1: Manual Entry
    if scan_mode == "📝 Manual Entry":
        barcode_input = st.text_input(
            "Enter barcode",
            placeholder="Enter EAN/UPC barcode (e.g., 5901234123457)",
            key="barcode_input"
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
            key="barcode_image_upload"
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
            if product_info.get('image_url'):
                st.image(product_info['image_url'], width=150)

        with st.form("barcode_add_form"):
            st.subheader("Add to inventory")
            qty = st.number_input(
                "Quantity",
                min_value=1,
                value=1,
                key="barcode_qty"
            )

            suggested_expiry_str = product_info.get('suggested_expiry_days')
            suggested_expiry = date.fromisoformat(suggested_expiry_str) if suggested_expiry_str else date.today() + timedelta(days=30)

            expiry = st.date_input(
                "Expiry date",
                value=suggested_expiry,
                min_value=date.today(),
                key="barcode_expiry"
            )

            current_category = product_info.get('category', 'Other') or 'Other'
            category_choice = st.selectbox(
                "Category",
                CATEGORY_OPTIONS,
                index=CATEGORY_OPTIONS.index(current_category) if current_category in CATEGORY_OPTIONS else CATEGORY_OPTIONS.index("Other"),
                key="barcode_category_override"
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


def handle_add_item() -> None:
    with st.form("add_item_form"):
        st.subheader("Add to pantry")
        name = st.text_input("Item name", key="create_name")
        quantity = st.number_input("Quantity", min_value=0, step=1, key="create_quantity")
        unit = st.selectbox("Unit", UNIT_OPTIONS, key="create_unit")
        expiry = st.date_input("Expiry date", min_value=date.today(), key="create_expiry")
        category = st.selectbox("Category", CATEGORY_OPTIONS, key="create_category")
        submitted = st.form_submit_button("Save item")

    if submitted:
        if not name:
            st.error("Item name is required")
            return
        payload = {
            "name": name,
            "quantity": int(quantity),
            "unit": unit,
            "expiry_date": expiry.isoformat(),
            "category": category,
        }
        try:
            create_inventory_item(payload)
            st.success("Item added")
            st.session_state.inventory_dirty = True
            st.rerun()
        except APIError as err:
            st.error(err.message)


def handle_quick_actions(items: List[Dict[str, Any]]) -> None:
    st.subheader("Quick actions")
    if not items:
        st.info("Inventory is empty")
        return

    option_map = {
        f"#{item['id']} · {item['name']} ({item['quantity']} {item['unit']})": item["id"]
        for item in items
    }
    labels = list(option_map.keys())

    with st.form("quantity_form"):
        selected = st.selectbox("Select item", labels, key="adjust_target")
        change = st.number_input("Adjust quantity", min_value=-100, max_value=100, value=1, step=1, key="adjust_delta")
        submitted = st.form_submit_button("Apply change")
    if submitted:
        try:
            adjust_inventory_quantity(option_map[selected], int(change))
            st.success("Quantity updated")
            st.session_state.inventory_dirty = True
            st.rerun()
        except APIError as err:
            st.error(err.message)

    with st.form("delete_form"):
        target = st.selectbox("Remove item", labels, key="delete_target")
        confirm = st.checkbox("Yes, delete this item", key="delete_confirm")
        submitted = st.form_submit_button("Delete item")
    if submitted:
        if not confirm:
            st.warning("Please confirm deletion")
        else:
            try:
                delete_inventory_item(option_map[target])
                st.success("Item deleted")
                st.session_state.inventory_dirty = True
                st.rerun()
            except APIError as err:
                st.error(err.message)


def render_dashboard() -> None:
    user = st.session_state.user or {}
    st.markdown(
        f"""
        <div class="pill-label">Household · {user.get('household_id', 'Not set')}</div>
        <h1>Welcome back, {user.get('name') or user.get('email')}</h1>
        <p>Track inventory, keep expiry alarms close, and sync every household member.</p>
        """,
        unsafe_allow_html=True,
    )

    action_cols = st.columns([1, 1, 1, 1])
    render_metric("Items tracked", len(st.session_state.inventory), action_cols[0])
    summary = summarize_inventory(st.session_state.inventory)
    render_metric("Expiring soon", summary["expiring"], action_cols[1])
    render_metric("Expired", summary["overdue"], action_cols[2])
    with action_cols[3]:
        if st.button("Refresh inventory", type="primary"):
            st.session_state.inventory_dirty = True
            st.rerun()
        if st.button("Sign out", type="secondary"):
            logout_user()
            st.rerun()

    household_id = st.session_state.household_id
    if not household_id:
        st.info("You do not belong to a household yet. Ask an admin to assign you before managing items.")
        return

    ensure_inventory_loaded()
    filter_options = ["All"] + CATEGORY_OPTIONS
    default_index = filter_options.index(st.session_state.category_filter) if st.session_state.category_filter in filter_options else 0
    selected_category = st.selectbox("Filter by category", filter_options, index=default_index)
    st.session_state.category_filter = selected_category

    sort_toggle = st.toggle("Sort by expiry date", value=st.session_state.sort_by_expiry)
    st.session_state.sort_by_expiry = sort_toggle

    filtered = filter_inventory(st.session_state.inventory, st.session_state.category_filter)
    sorted_items = render_inventory_table(filtered, st.session_state.sort_by_expiry)
    render_expiry_alerts(summary)

    # Create tabs for different add methods
    tab1, tab2, tab3 = st.tabs(["📱 Barcode Scanner", "➕ Manual Entry", "⚙️ Quick Actions"])
    
    with tab1:
        handle_barcode_scan()
    with tab2:
        handle_add_item()
    with tab3:
        handle_quick_actions(sorted_items)


def main() -> None:
    st.set_page_config(page_title="Smart Pantry Dashboard", page_icon="🥕", layout="wide")
    st.markdown(CUSTOM_STYLE, unsafe_allow_html=True)
    init_session_state()

    if st.session_state.is_authenticated:
        ensure_inventory_loaded()
        render_dashboard()
    else:
        render_public_view()


if __name__ == "__main__":
    main()
