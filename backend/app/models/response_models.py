"""
Pydantic models for API responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class ProductRecommendation(BaseModel):
    brand: str
    product_line: str
    shade_name: str
    price_cad: Optional[float] = None
    price_reference_url: Optional[str] = None
    product_url: str
    delta_e: float
    swatch_hex: Optional[str] = None
    swatch_estimated: bool = True


class AnalysisResponse(BaseModel):
    """Response model for the /analyze endpoint"""
    
    skinLAB: List[float] = Field(
        ...,
        description="Dominant skin tone in LAB color space [L, A, B]",
        min_items=3,
        max_items=3
    )
    
    undertone: str = Field(
        ...,
        description="Skin undertone classification: warm, neutral, or cool"
    )
    
    pantone_family: str = Field(
        ...,
        description="Approximate Pantone SkinTone family code"
    )
    
    fenty: List[str] = Field(
        default_factory=list,
        description="Recommended Fenty Beauty foundation shades"
    )
    
    nars: List[str] = Field(
        default_factory=list,
        description="Recommended NARS foundation shades"
    )
    
    tooFaced: List[str] = Field(
        default_factory=list,
        description="Recommended Too Faced foundation shades"
    )

    elf: List[str] = Field(default_factory=list, description="Suggested e.l.f. Soft Glam shades")
    maybelline: List[str] = Field(default_factory=list, description="Suggested Maybelline Fit Me shades")
    products: List[ProductRecommendation] = Field(default_factory=list)
    colors: dict[str, List[int]] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "skinLAB": [65.2, 12.4, 18.6],
                "undertone": "warm",
                "pantone_family": "4Y05",
                "fenty": ["310", "330"],
                "nars": ["Barcelona", "Stromboli"],
                "tooFaced": ["Warm Sand", "Golden Beige"]
            }
        }
