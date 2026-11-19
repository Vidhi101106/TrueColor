# True Colour: shade matching and Steel demo changes

This feature branch is a **reviewable prototype**, not a clinically or
commercially validated foundation matcher.

## Implemented
- Consistent OpenCV **float32 CIELAB**, with L* in 0..100 and signed a*/b*.
  The prior code mixed 8-bit LAB and threshold rules for true LAB.
- Smaller cheek sample patches to reduce background/hair contamination.
- The API now returns `colors` for the frontend results display.
- Added example shades for e.l.f. Soft Glam Satin and Maybelline Fit Me.
- Unified `products` recommendations with brand, shade, approximate color
  distance, currency-specific reference price and source link.
- UI filters by brand and maximum CAD price, sorts low/high or by match.
- A basic regression test suite for LAB conversion and recommendation output.

## IMPORTANT: limitations / source transparency
- Prices **are not live**. At the time of research, Walmart Canada listed
  e.l.f. Soft Glam Satin for CAD $9.98 and Well.ca listed Maybelline Fit Me
  Matte + Poreless for CAD $14.99. Availability and prices can change, and
  stores may have different listings for different shades.
- The original catalog now includes verified Sephora Canada **reference** prices:
  Fenty Pro Filt'r Soft Matte **CAD $54 regular** (Sephora currently shows
  some shades on sale at $16.20), NARS Natural Radiant Longwear **CAD $73**,
  and Too Faced Born This Way **CAD $66**. The link on each card opens the
  product listing, not necessarily a preselected shade. Prices and stock
  may vary by shade, retailer and date.
- New e.l.f./Maybelline hex swatches are visual **estimates**, not captured
  from manufacturer color calibration. Existing brand swatches are similarly
  approximate. Delta E ranking is a heuristic, not a guarantee of true
  foundation color, undertone, wear or oxidation.
- Lighting, white balance, makeup on the face, image compression and face
  region detection all affect results.
- Results are **not validated** without testing multiple calibrated samples.
- The prototype stores previous results in sessionStorage; be thoughtful
  before uploading real face photos or deploying publicly.

Sources:
- https://www.walmart.ca/en/ip/e-l-f-Cosmetics-Soft-Glam-Satin-Foundation/6000207918963
- https://well.ca/products/maybelline-fit-me-matte-poreless_261856.html
- https://www.maybelline.ca/en-ca/all-products/face-makeup/foundation/fit-me-matte-poreless-foundation
- https://www.sephora.com/ca/en/product/pro-filtr-soft-matte-longwear-foundation-P87985432
- https://www.sephora.com/ca/en/product/natural-radiant-longwear-foundation-P427301
- https://www.sephora.com/ca/en/product/too-faced-born-this-way-natural-finish-foundation-P517843

## Mac run-through

In the existing project clone:

```bash
cd ~/Documents/TrueColor
git status
# If backend/requirements.txt has local modifications from earlier setup:
git stash push -m "Save local Python package pins" -- backend/requirements.txt
git fetch origin
git switch feature/accurate-lab-budget-shade-matches
source .venv/bin/activate
python3 -m pip install --only-binary=:all: -r backend/requirements.txt
python3 -m unittest discover -s backend/tests -v
cd backend
python3 run.py
```

Open a **second Terminal tab**, leaving the API running:

```bash
cd ~/Documents/TrueColor/frontend
npm install
npm run dev
```

In browser: http://localhost:3000. Upload a clear photo. Check the
results and `/shades` filtering, and verify API response from
http://localhost:8000/docs.

## Before recording the Steel video

1. Run regression tests and perform an end-to-end browser upload.
2. Verify at least two different images to detect obviously incorrect colors.
3. Record a real, working flow without editing the results.
4. Explain your **personal contribution** to the original group project
   and make clear that the upgraded prototype is still under development.
5. Review the claims about the matching algorithm; don't call it AI/ML
   training or guarantee accuracy if it is rule-based color science plus K-Means.
