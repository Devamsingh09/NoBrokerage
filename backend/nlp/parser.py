# backend/nlp/parser.py
import re

def parse_query(q: str) -> dict:
    """
    Parse a free-text query and extract filters:
      - city
      - bhk (e.g., "3BHK")
      - budget_max (rupees numeric)
      - possession (Ready / Under Construction)
      - locality
      - project_name
    """
    q = (q or "").strip()
    out = {}

    # Budget patterns: 'under 1.2 Cr', 'below ₹80 L', 'up to 95L'
    m = re.search(r'(?:under|below|upto|up to|less than)\s*₹?\s*([\d,\.]+)\s*(Cr|cr|L|l|Lakhs|lakhs|K)?', q, re.IGNORECASE)
    if m:
        num = float(m.group(1).replace(',', ''))
        unit = (m.group(2) or '').lower()
        if 'cr' in unit:
            out['budget_max'] = num * 1e7
        elif unit.startswith('l') or 'lak' in unit:
            out['budget_max'] = num * 1e5
        elif unit == 'k':
            out['budget_max'] = num * 1e3
        else:
            out['budget_max'] = num
        # Remove the budget part from query to avoid interference
        q = q.replace(m.group(0), '').strip()

    # CITY: look for "in Pune", "at Pune"
    m = re.search(r'\b(?:in|at)\s+([A-Za-z][A-Za-z0-9\s\-\&]+)', q, re.IGNORECASE)
    if m:
        candidate = m.group(1).strip().split(',')[0]
        out['city'] = candidate

    # fallback: common city tokens
    if 'city' not in out:
        match = re.search(r'\b(Pune|Mumbai|Bengaluru|Bangalore|Delhi|Hyderabad|Noida|Gurgaon|Ahmedabad|Chennai)\b', q, re.IGNORECASE)
        if match:
            out['city'] = match.group(1)

    # BHK
    m = re.search(r'(\d+)\s*[-]?\s*BHK', q, re.IGNORECASE)
    if m:
        out['bhk'] = f"{m.group(1)}BHK"

    # Possession
    if re.search(r'ready to move|ready-to-move|ready', q, re.IGNORECASE):
        out['possession'] = 'Ready'
    if re.search(r'under construction|under-construction|uc', q, re.IGNORECASE):
        out['possession'] = 'Under Construction'

    # Locality: "near X" or "in Pune near Wakad"
    m = re.search(r'near\s+([A-Za-z0-9\s\-\&]+)', q, re.IGNORECASE)
    if m:
        out['locality'] = m.group(1).strip()

    # Project name: quoted or "project <name>"
    m = re.search(r'project\s+([A-Za-z0-9\s\-\&]+)', q, re.IGNORECASE)
    if m:
        out['project_name'] = m.group(1).strip()
    m2 = re.search(r'"([^"]+)"', q)
    if m2:
        out['project_name'] = m2.group(1).strip()

    return out
