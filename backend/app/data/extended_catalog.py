"""Curated demonstration products. Shade names are real, but display hex values
are APPROXIMATIONS, not measurements of dried foundation on skin.
Retail prices are Canadian examples, NOT live quotes. Update periodically.
"""
from app.utils.image_utils import hex_to_lab

ELF_URL = "https://www.walmart.ca/en/ip/e-l-f-Cosmetics-Soft-Glam-Satin-Foundation/6000207918963"
MAYBELLINE_URL = "https://www.maybelline.ca/en-ca/all-products/face-makeup/foundation/fit-me-matte-poreless-foundation"
WELL_URL = "https://well.ca/products/maybelline-fit-me-matte-poreless_261856.html"

# Example digital shades used only for approximate on-screen colour comparison.
# They have NOT been validated against manufacturer swatch measurements.
def _make(brand, line, price, reference, url, data):
    return [{
        "brand": brand,
        "product_line": line,
        "shade_name": name,
        "hex_color": hexc,
        "lab_l": float(hex_to_lab(hexc)[0]),
        "lab_a": float(hex_to_lab(hexc)[1]),
        "lab_b": float(hex_to_lab(hexc)[2]),
        "undertone": tone,
        "price_cad": price,
        "price_reference_url": reference,
        "product_url": url,
        "swatch_estimated": True,
    } for name, hexc, tone in data]

EXTRA_PRODUCTS = (
    _make("e.l.f.", "Soft Glam Satin Foundation", 9.98, ELF_URL, ELF_URL, [
        ("13 Fair Neutral", "#F0D4C3", "neutral"),
        ("21 Light Neutral", "#E8C4AE", "neutral"),
        ("22 Light Warm", "#E9C29D", "warm"),
        ("23 Light Cool", "#E2B5AA", "cool"),
        ("30 Medium Warm", "#D6A27A", "warm"),
        ("31 Medium Neutral", "#CD9B79", "neutral"),
        ("41 Tan Neutral", "#AC7859", "neutral"),
        ("42 Tan Neutral", "#AD7652", "neutral"),
        ("45 Tan Warm", "#9D6743", "warm"),
    ])
    + _make("Maybelline", "Fit Me Matte + Poreless", 14.99, WELL_URL, MAYBELLINE_URL, [
        ("112 Natural Ivory", "#EBD0B8", "neutral"),
        ("120 Classic Ivory", "#EAC9B3", "neutral"),
        ("125 Nude Beige", "#DDB79D", "neutral"),
        ("128 Warm Nude", "#D9AE89", "warm"),
        ("220 Natural Beige", "#D6A47F", "neutral"),
        ("228 Soft Tan", "#C48F69", "warm"),
        ("230 Natural Buff", "#CFA07A", "neutral"),
        ("310 Sun Beige", "#BB8058", "warm"),
        ("330 Toffee", "#9A6242", "warm"),
    ])
)
