# backend/nlp/summarizer.py
from typing import List
import math

def fmt_price(n):
    if n is None or (isinstance(n, float) and (math.isnan(n) or math.isinf(n))):
        return ""
    n = float(n)
    if n >= 1e7:
        return f"₹{round(n/1e7,2)} Cr"
    if n >= 1e5:
        return f"₹{round(n/1e5,2)} L"
    return f"₹{int(n)}"

def build_summary_from_df(df, parsed):
    """
    Produce a 2-4 sentence summary grounded entirely in df (filtered results).
    """
    total = len(df)
    if total == 0:
        # graceful fallback
        bhk_txt = parsed.get('bhk', 'matching properties')
        city_txt = parsed.get('city', 'the requested city')
        return f"No {bhk_txt} options found in {city_txt} with the given filters."

    # possession counts
    ready = int(df['possession_status'].astype(str).str.contains('Ready', case=False, na=False).sum())
    uc = total - ready

    # top localities
    locs = df['ProjectLocality'].fillna(df.get('Locality','')).value_counts().head(3)
    locs_list = locs.index.tolist()

    # price range
    prices = df['min_price'].dropna().astype(float) if 'min_price' in df.columns else []
    minp = prices.min() if not prices.empty else None
    maxp = prices.max() if not prices.empty else None

    parts = []
    bhk_txt = parsed.get('bhk', 'property')
    city_txt = parsed.get('city', '')

    parts.append(f"Found {total} {bhk_txt} listings in {city_txt} matching your filters.")
    parts.append(f"{ready} are marked Ready-to-move and {uc} are under construction.")
    if locs_list:
        parts.append("Top localities: " + ", ".join(locs_list) + ".")
    if minp is not None:
        parts.append(f"Price range among these listings: {fmt_price(minp)} to {fmt_price(maxp)}.")

    # join into up to 4 sentences
    summary = " ".join(parts[:4])
    return summary
