
import re

def parse_price_str(s):
    """
    Normalize a price-like string to numeric rupees.
    Supports formats like '1.2 Cr', '85 L', '12000000', '₹1,20,00,000'
    """
    if s is None:
        return None
    try:
        st = str(s)
        st = st.replace(',', '').replace('₹','').replace('Rs','').strip()
        m = re.search(r'([\d\.]+)\s*[Cc]r', st)
        if m:
            return float(m.group(1)) * 1e7
        m = re.search(r'([\d\.]+)\s*[Ll]', st)
        if m:
            return float(m.group(1)) * 1e5
        nums = re.findall(r'[\d\.]+', st)
        if nums:
            return float(nums[0])
    except Exception:
        return None
    return None
