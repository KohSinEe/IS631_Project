"""Barcode lookup and product recognition service."""

import httpx
from typing import Optional, Dict, Any
from pydantic import BaseModel

# Using Open Food Facts API (free, comprehensive food database)
# Alternative: EAN Database API, Barcode Lookup API


class BarcodeProduct(BaseModel):
    """Product information from barcode lookup."""

    barcode: str
    name: str
    category: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None


class BarcodeService:
    """Service for looking up product information by barcode."""

    # Open Food Facts API endpoints
    OFF_API_URL = "https://world.openfoodfacts.org/api/v0"

    @staticmethod
    async def lookup_product(barcode: str) -> Optional[BarcodeProduct]:
        """
        Look up product information by barcode using Open Food Facts API.

        Args:
            barcode: EAN/UPC barcode string

        Returns:
            BarcodeProduct if found, None otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # Try Open Food Facts API
                response = await client.get(f"{BarcodeService.OFF_API_URL}/product/{barcode}.json")

                if response.status_code == 200:
                    data = response.json()

                    if data.get("status") == 1:  # Product found
                        product = data.get("product", {})

                        return BarcodeProduct(
                            barcode=barcode,
                            name=product.get("product_name", "Unknown Product"),
                            category=product.get("categories", "Other"),
                            brand=product.get("brands"),
                            image_url=product.get("image_url"),
                        )
        except Exception as e:
            print(f"Error looking up barcode {barcode}: {e}")

        return None

    @staticmethod
    def estimate_expiry_date(product: BarcodeProduct) -> Optional[str]:
        """
        Try to estimate expiry date based on product category.
        This is a fallback if user doesn't provide explicit date.
        """
        from datetime import date, timedelta

        category = (product.category or "").lower()
        days_to_expiry = 30  # Default

        # Rough estimates based on category
        if "dairy" in category:
            days_to_expiry = 14
        elif "meat" in category or "fish" in category:
            days_to_expiry = 3
        elif "fresh" in category or "vegetable" in category or "fruit" in category:
            days_to_expiry = 7
        elif "beverage" in category:
            days_to_expiry = 365
        elif "frozen" in category:
            days_to_expiry = 180

        expiry_date = date.today() + timedelta(days=days_to_expiry)
        return expiry_date.isoformat()


# Singleton instance
barcode_service = BarcodeService()
