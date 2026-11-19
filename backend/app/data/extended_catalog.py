"""Curated demonstration products. Shade names are real, but display hex values
are APPROXIMATIONS, not measurements of dried foundation on skin.
Retail prices are Canadian examples, NOT live quotes. Update periodically.
"""
from app.utils.image_utils import hex_to_lab

ELF_URL = "https://www.walmart.ca/en/ip/e-l-f-Cosmetics-Soft-Glam-Satin-Foundation/6000207918963"
MAYBELLINE_URL = "https://www.maybelline.ca/en-ca/all-products/face-makeup/foundation/fit-me-matte-poreless-foundation"
WELL_URL = "https://well.ca/products/maybelline-fit-me-matte-poreless_261856.html"
ABH_URL = "https://www.sephora.com/ca/en/product/anastasia-beverly-hills-impeccable-blurring-second-skin-matte-foundation-P515098"

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
    + _make("Anastasia Beverly Hills", "Impeccable Blurring Second-Skin Matte Foundation",
            66.50, ABH_URL, ABH_URL, [
        # Shade labels from Anastasia/Sephora/Dermstore product shade guides.
        # These colours are HAND-ESTIMATED demo values, NOT measured ABH swatches.
        # They are only useful as a UI prototype until real reference swatches
        # can be independently acquired and calibrated.
        ("000N", "#F9E4D4", "neutral"),
        ("0CR", "#F6DCD4", "cool"),
        ("1N", "#F1D9C5", "neutral"),
        ("1CR", "#EECFC6", "cool"),
        ("1.5N", "#ECD3BC", "neutral"),
        ("2N", "#E7C6AE", "neutral"),
        ("2W", "#E9C69F", "warm"),
        ("2WP", "#E6BDA7", "warm"),
        ("2.5W", "#DDB795", "warm"),
        ("3N", "#D7AD8F", "neutral"),
        ("3W", "#D8A67B", "warm"),
        ("3WO", "#CBA07C", "warm"),
        ("3CR", "#D2A18D", "cool"),
        ("4N", "#C49375", "neutral"),
        ("4W", "#BF865E", "warm"),
        ("4WP", "#C58B75", "warm"),
        ("4WO", "#B8855B", "warm"),
        ("4.5W", "#B57D55", "warm"),
        ("5W", "#AD744C", "warm"),
        ("6N", "#996745", "neutral"),
        ("6W", "#95613D", "warm"),
        ("6.5N", "#865A42", "neutral"),
        ("7N", "#78503D", "neutral"),
        ("7.5N", "#714638", "neutral"),
        ("8N", "#603C2D", "neutral"),
        ("9N", "#4F2F25", "neutral"),
    ])
)
