# backend/services/search.py
import os
import pandas as pd
from typing import Dict
from nlp.summarizer import build_summary_from_df
from .utils import parse_price_str
import re
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def load_dataframes() -> pd.DataFrame:
    """
    Load CSVs from DATA_DIR and produce a merged DataFrame with normalized fields.
    """
    p_path = os.path.join(DATA_DIR, "project.csv")
    addr_path = os.path.join(DATA_DIR, "ProjectAddress.csv")
    cfg_path = os.path.join(DATA_DIR, "ProjectConfiguration.csv")
    var_path = os.path.join(DATA_DIR, "ProjectConfigurationVariant.csv")

    project = pd.read_csv(p_path) if os.path.exists(p_path) else pd.DataFrame()
    addr = pd.read_csv(addr_path) if os.path.exists(addr_path) else pd.DataFrame()
    cfg = pd.read_csv(cfg_path) if os.path.exists(cfg_path) else pd.DataFrame()
    variant = pd.read_csv(var_path) if os.path.exists(var_path) else pd.DataFrame()

    df = project.copy()

    # Extract city from slug
    import re
    cities_pattern = r'(pune|mumbai|bengaluru|bangalore|delhi|hyderabad|noida|gurgaon|ahmedabad|chennai)'
    df['City'] = df['slug'].astype(str).str.extract(cities_pattern, flags=re.IGNORECASE, expand=False).str.title()
    df['City'] = df['City'].fillna('Mumbai')  # default

    # Use real project name
    df['ProjectName'] = df['projectName']

    # Format possession date and determine status
    df['possession'] = pd.to_datetime(df['possessionDate'], errors='coerce').dt.strftime('%Y-%m-%d')
    df['possession_status'] = df['status'].map({'READY_TO_MOVE': 'Ready-to-move', 'UNDER_CONSTRUCTION': 'Under construction'}).fillna('Under construction')

    # Set dummy bhk_types
    df['bhk_types'] = '1BHK,2BHK,3BHK'

    # Set dummy locality
    df['ProjectLocality'] = df['slug'].astype(str).str.split('-').str[-4].str.replace('-', ' ').str.title()

    # Merge address
    if not addr.empty and 'ProjectGUID' in df.columns and 'ProjectGUID' in addr.columns:
        df = df.merge(addr[['ProjectGUID','City','ProjectLocality','Locality','ProjectName']].drop_duplicates(),
                      on='ProjectGUID', how='left')
    elif not addr.empty and 'ProjectId' in df.columns and 'ProjectId' in addr.columns:
        df = df.merge(addr[['ProjectId','City','ProjectLocality','Locality','ProjectName']].drop_duplicates(),
                      on='ProjectId', how='left')
    elif not addr.empty and 'id' in df.columns and 'projectId' in addr.columns:
        df = df.merge(addr[['projectId','fullAddress']].drop_duplicates(),
                      left_on='id', right_on='projectId', how='left')
    else:
        # try to find city-like column
        for c in df.columns:
            if c.lower() == 'city':
                df['City'] = df[c]

    # Ensure columns exist
    for col in ['City','ProjectLocality','Locality','ProjectName']:
        if col not in df.columns:
            df[col] = None

    # Extract city from fullAddress if City is missing
    if 'fullAddress' in df.columns and df['City'].isna().all():
        cities = ['Pune', 'Mumbai', 'Bengaluru', 'Bangalore', 'Delhi', 'Hyderabad', 'Noida', 'Gurgaon', 'Ahmedabad', 'Chennai']
        for city in cities:
            mask = df['fullAddress'].astype(str).str.contains(city, case=False, na=False)
            df.loc[mask, 'City'] = city

    # Build bhk_types from cfg if present
    if not cfg.empty:
        name_col = 'Name' if 'Name' in cfg.columns else ('Configuration' if 'Configuration' in cfg.columns else None)
        if name_col:
            cfg['bhk'] = cfg[name_col].astype(str).str.extract(r'(\d+\s*BHK|\d+\s*bhk|Studio)', expand=False)
            if 'ProjectGUID' in cfg.columns and 'ProjectGUID' in df.columns:
                bhk_map = cfg.groupby('ProjectGUID')['bhk'].apply(lambda s: ','.join(sorted(set([x for x in s.dropna().astype(str) if x]))))
                df = df.merge(bhk_map.rename('bhk_types'), on='ProjectGUID', how='left')
            elif 'ProjectId' in cfg.columns and 'ProjectId' in df.columns:
                bhk_map = cfg.groupby('ProjectId')['bhk'].apply(lambda s: ','.join(sorted(set([x for x in s.dropna().astype(str) if x]))))
                df = df.merge(bhk_map.rename('bhk_types'), on='ProjectId', how='left')

    # Price: try to extract numeric price from variant table via configuration
    if not variant.empty and not cfg.empty:
        price_cols = [c for c in variant.columns if 'price' in c.lower() or 'amount' in c.lower() or 'rate' in c.lower()]
        if price_cols:
            variant['price_num'] = None
            for c in price_cols:
                variant['price_num'] = variant['price_num'].fillna(variant[c].apply(parse_price_str)).infer_objects(copy=False)
            # Merge variant with cfg on configurationId
            cfg_key = 'id' if 'id' in cfg.columns else ('configurationId' if 'configurationId' in cfg.columns else None)
            var_key = 'configurationId' if 'configurationId' in variant.columns else None
            if cfg_key and var_key:
                merged = variant.merge(cfg[[cfg_key, 'projectId']], left_on=var_key, right_on=cfg_key, how='left')
                # Group by projectId
                vp = merged.groupby('projectId')['price_num'].agg(['min','max']).reset_index().rename(columns={'min':'min_price','max':'max_price'})
                # Merge with df
                proj_key = 'id' if 'id' in df.columns else ('ProjectId' if 'ProjectId' in df.columns else None)
                if proj_key:
                    df = df.merge(vp, left_on=proj_key, right_on='projectId', how='left')
                    # Fill NaN with dummy prices if still missing
                    if 'min_price' in df.columns:
                        df['min_price'] = df['min_price'].fillna(500000)
                    else:
                        df['min_price'] = 500000
                    if 'max_price' in df.columns:
                        df['max_price'] = df['max_price'].fillna(1500000)
                    else:
                        df['max_price'] = 1500000

    # Fill missing columns
    for col in ['bhk_types','min_price','max_price']:
        if col not in df.columns:
            df[col] = None

    # possession and amenities heuristics
    poss_cols = [c for c in df.columns if 'possession' in c.lower() or 'possessiondate' in c.lower()]
    if poss_cols:
        df['possession'] = df[poss_cols[0]]
    else:
        df['possession'] = None

    # Fill NaN possession with empty string
    df['possession'] = df['possession'].fillna('')

    amen_cols = [c for c in df.columns if 'amenit' in c.lower() or 'feature' in c.lower() or 'facility' in c.lower()]
    if amen_cols:
        df['amenities'] = df[amen_cols[0]]
    else:
        df['amenities'] = None

    # unify locality column
    df['ProjectLocality'] = df['ProjectLocality'].fillna(df['Locality'])

    # ensure project name
    if 'ProjectName' not in df.columns:
        df['ProjectName'] = df.get('Name', None)

    return df

def fmt_price(num):
    import math
    if num is None or (isinstance(num, float) and math.isnan(num)):
        return ""
    n = float(num)
    if n >= 1e7:
        return f"₹{round(n/1e7,2)} Cr"
    if n >= 1e5:
        return f"₹{round(n/1e5,2)} L"
    return f"₹{int(n)}"

def search_and_summarize(df, parsed: Dict, max_results: int = 10):
    """
    Apply parsed filters to dataframe, build a grounded summary and return cards.
    """
    # Load cfg and variant for floor plan
    cfg_path = os.path.join(DATA_DIR, "ProjectConfiguration.csv")
    var_path = os.path.join(DATA_DIR, "ProjectConfigurationVariant.csv")
    cfg = pd.read_csv(cfg_path) if os.path.exists(cfg_path) else pd.DataFrame()
    variant = pd.read_csv(var_path) if os.path.exists(var_path) else pd.DataFrame()

    d = df.copy()

    # Apply filters
    if parsed.get('city'):
        d = d[d['City'].astype(str).str.contains(parsed['city'], case=False, na=False)]
    if parsed.get('bhk'):
        bhk_re = parsed['bhk']
        mask = d['bhk_types'].astype(str).str.contains(bhk_re, case=False, na=False) | d['ProjectName'].astype(str).str.contains(bhk_re, case=False, na=False)
        d = d[mask]
    if parsed.get('budget_max') is not None:
        budget = parsed['budget_max']
        mask = (d['min_price'].notna() & (d['min_price'] <= budget)) | (d['max_price'].notna() & (d['max_price'] <= budget))
        d = d[mask]
    if parsed.get('possession'):
        # Check both possession date and status
        possession_filter = parsed['possession'].lower()
        mask = (d['possession'].astype(str).str.contains(possession_filter, case=False, na=False)) | \
               (d['possession_status'].astype(str).str.contains(possession_filter, case=False, na=False))
        d = d[mask]
    if parsed.get('locality'):
        d = d[d['ProjectLocality'].astype(str).str.contains(parsed['locality'], case=False, na=False)]
    if parsed.get('project_name'):
        d = d[d['ProjectName'].astype(str).str.contains(parsed['project_name'], case=False, na=False)]

    # Build summary
    summary = build_summary_from_df(d, parsed)

    # Build cards (title, city+locality, bhk, price, project name, possession, top amenities, cta)
    cards = []
    for _, r in d.head(max_results).iterrows():
        title = r.get('ProjectName') or r.get('Name') or 'Project'
        city = r.get('City') or ''
        locality = r.get('ProjectLocality') or r.get('Locality') or ''
        bhk = r.get('bhk_types') or ''
        price_val = r.get('min_price') if pd.notna(r.get('min_price')) else r.get('max_price')
        price = fmt_price(price_val) if price_val is not None else ""
        possession = str(r.get('possession') or '')
        amenities = str(r.get('amenities') or '')
        # top 2-3 amenities - naive split by comma/semicolon
        amen_list = []
        for sep in [',', ';', '|']:
            if sep in amenities:
                amen_list = [x.strip() for x in amenities.split(sep) if x.strip()]
                break
        if not amen_list and amenities:
            amen_list = [amenities]
        top_amen = ", ".join(amen_list[:3])
        slug = re.sub(r'[^a-zA-Z0-9\-]', '-', str(title).lower()).replace('--','-').strip('-')[:80]
        # Get floor plan image from variant table
        floor_plan = None
        if not variant.empty:
            # Find variant for this project
            proj_id = r.get('id') or r.get('ProjectId')
            if proj_id:
                proj_variants = variant[variant['configurationId'].isin(cfg[cfg['projectId'] == proj_id]['id'])]
                if not proj_variants.empty:
                    floor_plan = proj_variants['floorPlanImage'].dropna().iloc[0] if 'floorPlanImage' in proj_variants.columns else None

        cards.append({
            "title": title,
            "city": city,
            "locality": locality,
            "bhk": bhk,
            "price": price,
            "project_name": title,
            "possession": possession,
            "amenities": top_amen,
            "floorPlanImage": floor_plan,
            "cta": f"/project/{slug}"
        })

    return {"summary": summary, "cards": cards}
