import json
import re
import logging

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