import re
import hashlib
from difflib import SequenceMatcher


def parse_price(value):
    if value is None:
        return None
    s = str(value).replace(',', '').strip()
    m = re.search(r'(\d+(?:\.\d+)?)', s)
    if not m:
        return None
    val = float(m.group(1))
    if 'k' in s.lower():
        val *= 1000
    if '萬' in s:
        val *= 10000
    return round(val, 2)


def parse_sold(value):
    if value is None:
        return None
    s = str(value).replace(',', '').strip()
    m = re.search(r'(\d+(?:\.\d+)?)', s)
    if not m:
        return None
    val = float(m.group(1))
    if 'k' in s.lower():
        val *= 1000
    if '萬' in s:
        val *= 10000
    return int(round(val))


def text_similarity(a, b):
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()


def normalize_text(value):
    if value is None:
        return None
    return re.sub(r'\s+', ' ', str(value)).strip()


def make_product_hash(brand, title, model, price):
    base = f"{brand or ''}-{title or ''}-{model or ''}-{price or ''}"
    return hashlib.md5(base.encode('utf-8')).hexdigest()
