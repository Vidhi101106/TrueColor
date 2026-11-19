"""
Shade Matcher Service
Matches user's skin tone to makeup product shades
Now supports both Supabase and local fallback
"""

import numpy as np
from typing import Dict, List
from app.data.makeup_database import MAKEUP_DATABASE
from app.data.extended_catalog import EXTRA_PRODUCTS
from app.database.supabase_client import supabase_client
from app.services.skin_analysis import SkinAnalysisService
import logging

logger = logging.getLogger(__name__)


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
                self._products_cache = await supabase_client.get_all_products()
                self._products_cache.extend(EXTRA_PRODUCTS)
                logger.info(f"📦 Loaded {len(self._products_cache)} products from Supabase")
            else:
                # Fallback to local database
                self._products_cache = self._convert_local_to_products(MAKEUP_DATABASE) + EXTRA_PRODUCTS
                logger.info(f"📦 Using local database with {len(self._products_cache)} products")
        
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
        """Top three per brand plus a sortable list of product recommendations.

        Color distance compares approximate screen swatches. It cannot guarantee
        a match to the real physical product, especially under different lighting.
        """
        products = await self._load_products()
        brand_keys = {
            "fenty": "Fenty", "nars": "Nars", "tooFaced": "Too Faced",
            "elf": "e.l.f.", "maybelline": "Maybelline",
        }
        matches = {key: [] for key in brand_keys}
        unified = []
        for key, brand_name in brand_keys.items():
            subset = [p for p in products if p["brand"].lower() == brand_name.lower()]
            ranked = []
            for product in subset:
                shade_lab = np.array([product["lab_l"], product["lab_a"], product["lab_b"]], dtype=float)
                delta = float(self.skin_analyzer.calculate_color_distance(skin_lab, shade_lab))
                if not np.isfinite(delta):
                    continue
                bonus = -3.0 if product.get("undertone", "").lower() == undertone.lower() else 0
                ranked.append((delta + bonus, delta, product))
            ranked.sort(key=lambda entry: entry[0])
            for _, delta, product in ranked[:self.max_matches]:
                matches[key].append(product["shade_name"])
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
