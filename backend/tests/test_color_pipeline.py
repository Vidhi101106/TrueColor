"""Basic regression tests. Run: python -m unittest discover -s backend/tests -v"""
import asyncio
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.utils.image_utils import hex_to_lab, lab_to_hex
from app.services.skin_analysis import SkinAnalysisService
from app.services.shade_matcher import ShadeMatcherService


class ShadePipelineTests(unittest.TestCase):
    def test_srgb_cielab_roundtrip(self):
        for color in ("#E5BA9F", "#A16B4D", "#F0D4C3"):
            lab = hex_to_lab(color)
            self.assertTrue(0 <= lab[0] <= 100)
            self.assertLessEqual(abs(lab[1]), 128)
            self.assertLessEqual(abs(lab[2]), 128)
            actual = lab_to_hex(lab)
            original = np.array([int(color[i:i+2], 16) for i in (1,3,5)])
            restored = np.array([int(actual[i:i+2], 16) for i in (1,3,5)])
            self.assertLessEqual(int(np.max(np.abs(original - restored))), 3)

    def test_consistent_photo_and_swatch_lab(self):
        # BGR pixel for a mock sample. Both conversion paths must agree.
        rgb = (224, 171, 133)
        bgr = np.array([list(reversed(rgb))] * 80, dtype=np.uint8)
        actual = SkinAnalysisService(n_clusters=1).analyze_skin_tone(bgr)
        expected = hex_to_lab("#E0AB85")
        self.assertTrue(np.allclose(actual, expected, atol=1.2))

    def test_visualization_is_rgb_bytes(self):
        lab = hex_to_lab("#C99C78")
        colors = SkinAnalysisService().visualize_channels(lab)
        self.assertEqual(set(colors), {"combined", "l_channel", "a_channel", "b_channel"})
        for rgb in colors.values():
            self.assertEqual(len(rgb), 3)
            self.assertTrue(all(isinstance(ch, int) and 0 <= ch <= 255 for ch in rgb))

    def test_catalog_has_budget_recommendations(self):
        matches = asyncio.run(ShadeMatcherService().find_matches(hex_to_lab("#D6A47F"), "warm"))
        self.assertTrue(matches["elf"])
        self.assertTrue(matches["maybelline"])
        self.assertTrue(matches["products"])
        self.assertTrue(any(p["price_cad"] is not None for p in matches["products"]))

    def test_anastasia_discovered_from_catalog(self):
        from app.data.extended_catalog import EXTRA_PRODUCTS
        abh = [p for p in EXTRA_PRODUCTS if p["brand"] == "Anastasia Beverly Hills"]
        self.assertEqual(len(abh), 26)
        self.assertTrue(all(p["price_cad"] == 66.50 for p in abh))
        self.assertTrue(all(p["product_url"].startswith("https://www.sephora.com/ca/en/product/") for p in abh))

        matches = asyncio.run(ShadeMatcherService().find_matches(hex_to_lab("#D6A47F"), "warm"))
        brand_matches = [
            p for p in matches["products"] if p["brand"] == "Anastasia Beverly Hills"
        ]
        self.assertEqual(len(brand_matches), 3)
        self.assertTrue(all(p["swatch_estimated"] for p in brand_matches))
        self.assertEqual(len(matches["products"]), 18)  # 3 each across six brands

    def test_original_brands_include_prices_and_store_links(self):
        matches = asyncio.run(ShadeMatcherService().find_matches(hex_to_lab("#D6A47F"), "warm"))
        expected = {"Fenty": 54.00, "Nars": 73.00, "Too Faced": 66.00}
        for brand, regular_reference_price in expected.items():
            recommendations = [p for p in matches["products"] if p["brand"] == brand]
            self.assertTrue(recommendations, f"No recommendations for {brand}")
            for product in recommendations:
                self.assertEqual(product["price_cad"], regular_reference_price)
                self.assertTrue(product["product_url"].startswith("https://www.sephora.com/ca/en/product/"))
                self.assertEqual(product["price_reference_url"], product["product_url"])


if __name__ == "__main__":
    unittest.main()
