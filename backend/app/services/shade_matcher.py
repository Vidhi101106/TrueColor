"""
Shade Matcher Service
Matches user's skin tone to makeup product shades
Now supports both Supabase and local fallback
"""

import numpy as np
from typing import Dict, List
from app.data.makeup_database import MAKEUP_DATABASE
from app.data.extended_catalog import EXTRA_PRODUCTS
from app.utils.image_utils import hex_to_lab
from app.database.supabase_client import supabase_client
from app.services.skin_analysis import SkinAnalysisService
import logging

logger = logging.getLogger(__name__)

# Canadian regular/reference prices, not live checkout prices. Sephora Canada
# may discount individual shades or change prices without notice.
PREMIUM_PRODUCT_REFERENCES = {
    "fenty": {
        "price_cad": 54.00,
        "product_line": "Pro Filt'r Soft Matte Longwear Liquid Foundation",
        "url": "https://www.sephora.com/ca/en/product/pro-filtr-soft-matte-longwear-foundation-P87985432",
    },
    "nars": {
        "price_cad": 73.00,
        "product_line": "Natural Radiant Longwear Full Coverage Foundation",
        "url": "https://www.sephora.com/ca/en/product/natural-radiant-longwear-foundation-P427301",
    },
    "too faced": {
        "price_cad": 66.00,
        "product_line": "Born This Way Undetectable Medium-To-Full Coverage Foundation",
        "url": "https://www.sephora.com/ca/en/product/too-faced-born-this-way-natural-finish-foundation-P517843",
    },
}


def _reference_for_brand(brand: str):
    """Return verified product-page links for the three original brands."""
    brand_name = brand.casefold().replace("beauty by rihanna", "").replace("beauty", "").strip()
    return PREMIUM_PRODUCT_REFERENCES.get(brand_name)



class ShadeMatcherService:
    """Service for matching skin tones to makeup shades"""
    
    def __init__(self, max_matches: int = 3):
        """
        Initialize shade matcher
        
        Args:
            max_matches: Maximum number of shade matches per brand
        """
        self.max_matches = max_matches
        self.skin_analyzer = SkinAnalysisService()
        self.makeup_db = MAKEUP_DATABASE
        
        # Cache for Supabase products (loaded once)
        self._products_cache = None
        self._using_supabase = supabase_client.is_connected()
        
        if self._using_supabase:
            logger.info("✅ Shade matcher using Supabase database")
        else:
            logger.info("📦 Shade matcher using local Python dictionary")
    
    async def _load_products(self):
        """Load products from Supabase (with caching) or local fallback"""
        if self._products_cache is None:
            if self._using_supabase:
                # Load from Supabase
                db_products = await supabase_client.get_all_products()
                if not db_products:
                    logger.warning("Database empty or unavailable; using local demonstration catalogue")
                    db_products = self._convert_local_to_products(MAKEUP_DATABASE)
                else:
                    # Existing stored LAB columns may use OpenCV's legacy uint8 encoding.
                    # Recompute from hex instead so values use the same CIELAB scale.
                    for p in db_products:
                        if p.get("hex_color"):
                            lab = hex_to_lab(p["hex_color"])
                            p["lab_l"], p["lab_a"], p["lab_b"] = [float(v) for v in lab]
                self._products_cache = db_products + EXTRA_PRODUCTS
                logger.info(f"📦 Loaded {len(self._products_cache)} products")
            else:
                # Fallback to local database
                self._products_cache = self._convert_local_to_products(MAKEUP_DATABASE) + EXTRA_PRODUCTS
                logger.info(f"📦 Using local database with {len(self._products_cache)} products")
        
        # Attach public storefront references even to products loaded from
        # Supabase, whose older rows may lack price/link metadata.
        for product in self._products_cache:
            reference = _reference_for_brand(product["brand"])
            if reference:
                product.setdefault("product_line", reference["product_line"])
                if product.get("price_cad") is None:
                    product["price_cad"] = reference["price_cad"]
                if not product.get("price_reference_url"):
                    product["price_reference_url"] = reference["url"]
                if not product.get("product_url"):
                    product["product_url"] = reference["url"]
        return self._products_cache
    
    def _convert_local_to_products(self, local_db):
        """Convert local database format to unified product format"""
        products = []
        for brand, shades in local_db.items():
            brand_name = "Too Faced" if brand == "tooFaced" else brand.title()
            for shade in shades:
                products.append({
                    "brand": brand_name,
                    "shade_name": shade["name"],
                    "hex_color": shade["hex"],
                    "lab_l": float(shade["lab"][0]),
                    "lab_a": float(shade["lab"][1]),
                    "lab_b": float(shade["lab"][2]),
                    "undertone": shade["undertone"],
                    "product_line": {"fenty": "Pro Filt'r Foundation", "nars": "Natural Radiant Longwear", "tooFaced": "Born This Way"}.get(brand, "Foundation"),
                    "price_cad": None,
                    "price_reference_url": None,
                    "product_url": "",
                    "swatch_estimated": True
                })
        return products
    
    async def find_matches(self, skin_lab: np.ndarray, undertone: str) -> Dict:
        """Rank matches from every brand in the catalog, with top 3 per brand.

        New brands require *only catalog entries*: the unified products array
        powers the frontend's auto-populated brand selector. Older named keys
        remain for backward compatibility with existing API consumers.

        Digital swatch colors are uncalibrated demo estimates, not real-world
        measurements of the foundation. Delta E is only an approximate ranking.
        """
        products = await self._load_products()
        legacy_keys = {
            "fenty": "fenty", "nars": "nars", "too faced": "tooFaced",
            "e.l.f.": "elf", "maybelline": "maybelline",
        }
        matches = {key: [] for key in legacy_keys.values()}
        unified = []

        grouped = {}
        for product in products:
            brand = product.get("brand", "").strip().casefold()
            if brand:
                grouped.setdefault(brand, []).append(product)

        for brand_key, brand_products in grouped.items():
            ranked = []
            for product in brand_products:
                shade_lab = np.array(
                    [product["lab_l"], product["lab_a"], product["lab_b"]],
                    dtype=float,
                )
                delta = float(
                    self.skin_analyzer.calculate_color_distance(skin_lab, shade_lab)
                )
                if not np.isfinite(delta):
                    continue
                bonus = -3.0 if product.get("undertone", "").lower() == undertone.lower() else 0
                ranked.append((delta + bonus, delta, product))

            ranked.sort(key=lambda entry: entry[0])
            for _, delta, product in ranked[:self.max_matches]:
                if brand_key in legacy_keys:
                    matches[legacy_keys[brand_key]].append(product["shade_name"])
                unified.append({
                    "brand": product["brand"],
                    "product_line": product.get("product_line", "Foundation"),
                    "shade_name": product["shade_name"],
                    "price_cad": product.get("price_cad"),
                    "price_reference_url": product.get("price_reference_url"),
                    "product_url": product.get("product_url", ""),
                    "delta_e": round(delta, 2),
                    "swatch_hex": product.get("hex_color"),
                    "swatch_estimated": product.get("swatch_estimated", True),
                })

        unified.sort(key=lambda p: p["delta_e"])
        matches["products"] = unified
        return matches

    def _find_brand_matches_from_list(self, skin_lab: np.ndarray, undertone: str, products: List[Dict]) -> List[str]:
        """
        Find best matches from a list of products
        
        Args:
            skin_lab: User's skin tone in LAB
            undertone: User's undertone
            products: List of product dictionaries
            
        Returns:
            List of shade names
        """
        if not products:
            return []
        
        distances = []
        
        for product in products:
            # Get LAB values from product
            shade_lab = np.array([
                product["lab_l"],
                product["lab_a"],
                product["lab_b"]
            ])
            
            # Calculate color distance (Delta E)
            delta_e = self.skin_analyzer.calculate_color_distance(skin_lab, shade_lab)
            
            # Bonus for matching undertone
            undertone_bonus = 0
            if product.get("undertone", "neutral").lower() == undertone.lower():
                undertone_bonus = -5  # Reduce distance for matching undertone
            
            adjusted_distance = delta_e + undertone_bonus
            
            distances.append({
                "name": product["shade_name"],
                "distance": adjusted_distance,
                "delta_e": delta_e
            })
        
        # Sort by distance
        distances.sort(key=lambda x: x["distance"])
        
        # Return top matches
        top_matches = distances[:self.max_matches]
        return [match["name"] for match in top_matches]
    
    # Legacy method for backwards compatibility (now uses local DB)
    def _find_brand_matches(self, skin_lab: np.ndarray, undertone: str, brand: str) -> List[str]:
        """
        Legacy method - Find best matches for a specific brand from local DB
        
        Args:
            skin_lab: User's skin tone in LAB
            undertone: User's undertone
            brand: Brand name (lowercase key)
            
        Returns:
            List of shade names
        """
        if brand not in self.makeup_db:
            return []
        
        brand_shades = self.makeup_db[brand]
        
        # Calculate distances for all shades
        distances = []
        for shade in brand_shades:
            shade_lab = np.array(shade["lab"])
            
            # Calculate color distance (Delta E)
            delta_e = self.skin_analyzer.calculate_color_distance(skin_lab, shade_lab)
            
            # Bonus for matching undertone
            undertone_bonus = 0
            if shade.get("undertone", "neutral").lower() == undertone.lower():
                undertone_bonus = -5  # Reduce distance for matching undertone
            
            adjusted_distance = delta_e + undertone_bonus
            
            distances.append({
                "name": shade["name"],
                "distance": adjusted_distance,
                "delta_e": delta_e
            })
        
        # Sort by distance
        distances.sort(key=lambda x: x["distance"])
        
        # Return top matches
        top_matches = distances[:self.max_matches]
        return [match["name"] for match in top_matches]
    
    def get_shade_info(self, brand: str, shade_name: str) -> Dict:
        """
        Get detailed information about a specific shade
        
        Args:
            brand: Brand name
            shade_name: Shade name
            
        Returns:
            Shade information dictionary
        """
        if brand not in self.makeup_db:
            return None
        
        for shade in self.makeup_db[brand]:
            if shade["name"] == shade_name:
                return shade
        
        return None
