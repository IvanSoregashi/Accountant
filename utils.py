import json
import re

from datetime import datetime as dt
from decimal import Decimal

expand = lambda x: json.dumps(x, indent=2)
ts_now = lambda: dt.now().timestamp()
pntodt = lambda x: dt.strptime(x, "%Y%d%m_%H%M")
int_dt = lambda x: {k: (int(v) if isinstance(v, Decimal) else v) for k, v in x.items()}


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


def is_email(string):
    regex_email = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.fullmatch(regex_email, string, flags=re.I))


def parse_pd(acc):
    m_pn = json.loads(acc['mobilePushData'])
    dates = []
    for dicts in m_pn['mobilePushOsMap'].values():
        dates.extend(pntodt(d["createdDate"]) for d in dicts)
    return max(dates).timestamp()
