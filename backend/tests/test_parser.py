# backend/tests/test_parser.py
from nlp.parser import parse_query

def test_parse_basic():
    q = "3BHK flat in Pune under ₹1.2 Cr"
    p = parse_query(q)
    assert p.get('city') and 'pune' in p['city'].lower()
    assert p.get('bhk') == '3BHK'
    assert int(p.get('budget_max')) == 12000000
