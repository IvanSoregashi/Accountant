import json
import re
import logging
from hashlib import sha256

from obscura import *
from datetime import datetime as dt
from decimal import Decimal

log = logging.getLogger("utils")

expand = lambda x: json.dumps(x, indent=2)
ts_now = lambda: dt.now().timestamp()
pntodt = lambda x: dt.strptime(x, "%Y%d%m_%H%M")
int_dt = lambda x: {k: (int(v) if isinstance(v, Decimal) else v) for k, v in x.items()}


def envron(data):
    if re.fullmatch(qa_user_regex, data, flags=re.I):
        return env_qa
    elif re.fullmatch(dev_user_regex, data, flags=re.I):
        return env_dev
    else:
        log.error("UserId doesn't match dev or qa pattern")


def ts_to_days(ts):
    # if pd.isna(ts): return None
    if ts > 2000000000:
        ts = ts // 1000
    date_time = dt.fromtimestamp(ts)
    now = dt.now()
    delta = (now - date_time)
    return delta.days


def ts_to_date(ts):
    # if pd.isna(ts): return None
    if ts > 2000000000:
        ts = ts // 1000
    date_time = dt.fromtimestamp(ts)
    return date_time.strftime("%Y-%m-%d")


def dec_to_int(item):
    if isinstance(item, dict): return int_dt(item)
    if isinstance(item, list): return [int_dt(x) for x in item]
    # log.error(f"dec_to_int - called with incorrect argument: {type(item)}")


def is_email(string: str) -> bool:
    regex_email = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.fullmatch(regex_email, string, flags=re.I))


def ensure_email(string: str) -> str:
    regex_usrnm = r"^[a-zA-Z0-9_.+-]+$"
    if is_email(string): return string
    if re.fullmatch(regex_usrnm, string, flags=re.I):
        return f"{string}@yopmail.com"
    return ""


def is_usrId(string: str) -> bool:
    regex_userid = user_regex
    return bool(re.fullmatch(regex_userid, string, flags=re.I))


def parse_pd(acc):
    m_pn = json.loads(acc['mobilePushData'])
    dates = []
    for dicts in m_pn['mobilePushOsMap'].values():
        dates.extend(pntodt(d["createdDate"]) for d in dicts)
    return max(dates).timestamp()


def confirm():
    while True:
        answer = input("Confirm this course of action: (yes/no) ")
        if answer in ("", "yes", "Yes", "YES"): return True
        if answer in ("no", "No", "NO"): return False


def confirm_env():
    while True:
        answer = input("Confirm the environment: (qa/dev) ")
        if answer == "qa": return env_qa
        if answer == "dev": return env_dev


def sha_256(data):
    data = data.encode()
    sha256_hash = sha256(data).hexdigest()
    return sha256_hash


def sort_args(args):
    args = list(map(str.upper, args))
    cc = [arg for arg in args if arg in COUNTRY_IP]
    rn = [arg for arg in args if arg in REGION]
    flt = [arg for arg in args if arg.lower() in FILTERS]
    cc += [cc for arg in rn for cc in REGION[arg]]
    cc = list(set(cc))
    return cc, flt

# Dicts

REGION = {
    "Z1": ["CA", "GB", "DE", "FR", "IT", "ES", "PT", "NL", "BE", "SE", "NO", "DK", "FI", "AT", "CH", "LV", "LT", "IE", "HR", "SK", "SI", "CZ", "PL", "EE", "RO", "HU", "LU", "GR", "CY", "MT", "BG", ],
    "Z2": ["US", ],
    "Z3": ["AU", "NZ", ],
    "Z4": ["SG", "JP", "HK", "TW", ],
    "Z5": ["CN", ],
    "EU": ["GB", "DE", "FR", "IT", "ES", "PT", "NL", "BE", "SE", "NO", "DK", "FI", "AT", "CH", "LV", "LT", "IE", "HR", "SK", "SI", "CZ", "PL", "EE", "RO", "HU", "LU", "GR", "CY", "MT", "BG", ],
    "IAP": ["CA", "NZ", "AU", "ZA", "SG", "JP", "HK", ],
    "APAC": ["SG", "JP", "HK", "TW", ],
    "LATAM": ["AR", "BR", "CL", "PE", ],
}

COUNTRY_IP = {
    "US": "65.203.177.0",       # USA
    "CA": "104.129.96.0",       # Canada
    "NZ": "203.97.33.12",       # New Zealand
    "AU": "1.120.0.0",          # Australia
    "GB": "185.245.80.156",     # United Kingdom, Great Britain
    "DE": "84.56.123.45",       # Germany
    "FR": "195.154.235.10",     # France 109.74.82.196, 83.145.67.210
    "IT": "151.12.34.56",       # Italy
    "ES": "81.47.159.23",       # Spain
    "PT": "109.48.0.0",         # Portugal
    "NL": "213.127.157.89",     # Netherlands 185.92.68.143
    "BE": "104.155.0.0",        # Belgium
    "SE": "129.16.0.0",         # Sweden
    "NO": "193.213.0.1",        # Norway
    "DK": "87.62.34.21",        # Denmark
    "FI": "109.204.128.0",      # Finland
    "AT": "77.119.154.32",      # Austria
    "CH": "194.230.109.34",     # Switzerland
    "LV": "94.140.117.200",     # Latvia
    "LT": "109.205.232.0",      # Lithuania
    "IE": "104.123.96.0",       # Ireland
    "HR": "78.0.0.0",           # Croatia
    "SK": "78.98.0.0",          # Slovakia
    "SI": "164.8.0.0",          # Slovenia
    "CZ": "89.102.0.0",         # Czechia
    "PL": "156.17.0.0",         # Poland
    "EE": "84.50.0.0",          # Estonia
    "RO": "109.96.0.0",         # Romania
    "HU": "147.7.0.0",          # Hungary
    "LU": "146.3.0.0",          # Luxembourg
    "GR": "188.4.0.0",          # Greece
    "CY": "69.6.0.0",           # Cyprus
    "MT": "46.11.0.0",          # Malta
    "BG": "78.128.0.0",         # Bulgaria
    "JP": "1.72.0.0",           # Japan
    "TW": "1.160.0.0",          # Taiwan 1.34.0.0  1.200.0.0
    "HK": "1.64.0.0",           # Hong Kong
    "SG": "101.127.0.0",        # Singapore
    "AR": "163.10.0.0",         # Argentina
    "BR": "131.0.4.0",          # Brazil
    "BS": "64.66.0.0",          # Bahamas
    "CL": "146.83.0.0",         # Chile
    "DO": "148.0.0.0",          # Dominican Republic
    "PE": "181.64.0.0",         # Peru
    "CN": "1.2.0.0",            # China
    "ZA": "152.106.0.0",        # South Africa
}

FILTERS = {
    "qa": lambda k, v: envron(k) == env_qa,
    "dev": lambda k, v: envron(k) == env_dev,
    company1: lambda k, v: "partnerId" not in v,
    "partner": lambda k, v: "partnerId" in v,
    company2: lambda k, v: v["partnerId"] == company2,
    company3: lambda k, v: v["partnerId"].startswith(company3),
}

LANGUAGE_CODES = [
    "en",       # English (United States)
    "da",       # Denmark
    "fi",       # Finland
    "it",       # Italy
    "fr",       # France
    "de",       # Germany
    "lv",       # Latvia
    "lt",       # Lithuania
    "es",       # Spain
    "no",       # Norway
    "nl-be",    # Belgium
    "nl",       # The Netherlands
    "ja",       # Japan
    "sv",       # Sweden
    "pl",       # Poland
    "pt-br",    # Brazil
    "pt",       # Portugal
    "zh-cn",    # China (PRC)
    "zh-tw",    # Taiwan
]