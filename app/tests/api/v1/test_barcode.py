"""Tests for camera features and barcode scanning"""

from fastapi.testclient import TestClient
from unittest.mock import patch

from app.config import settings
from app.models import User
from app.services.barcode import BarcodeProduct


def test_lookup_barcode_returns_product_details(auth_client: TestClient, create_test_user: User) -> None:
    # ARRANGE
    with patch('app.services.barcode.barcode_service.lookup_product') as mock_lookup:
        mock_lookup.return_value = BarcodeProduct(
            barcode="9780134685991",
            name="Organic Whole Milk",
            category="Dairy",
            brand="Happy Farm",
            image_url="https://example.com/milk.jpg",
        )

        # ACT
        response = auth_client.get(f"{settings.API_V1_STR}/barcode/lookup/9780134685991")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Organic Whole Milk"
        assert data["category"] == "Dairy"


def test_add_item_from_barcode_with_minimum_params(auth_client: TestClient, create_test_user: User) -> None:
    # ARRANGE
    household_id = create_test_user.household_id
    with patch('app.services.barcode.barcode_service.lookup_product') as mock_lookup:
        with patch('app.services.barcode.barcode_service.estimate_expiry_date') as mock_expiry:
            mock_lookup.return_value = BarcodeProduct(
                barcode="9780134685991",
                name="Organic Whole Milk",
                category="Dairy",
                brand="Happy Farm",
                image_url="https://example.com/milk.jpg",
            )
            mock_expiry.return_value = "2026-03-15"

            # ACT
            response = auth_client.post(
                f"{settings.API_V1_STR}/barcode/add-from-barcode",
                params={"barcode": "9780134685991", "household_id": household_id},
            )

            # ASSERT
            assert response.status_code == 201
            item = response.json()
            assert item["name"] == "Organic Whole Milk"
            assert item["household_id"] == household_id
