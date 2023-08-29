from datetime import datetime
from numpy import exp
import re
from werkzeug.datastructures import MultiDict


def time_decay(date: str = "1900-01-01", latest: int = 1):
    """Monotone decreasing function (inspired by IDF) to downweight older bulletins
    Args:
        date(str): published_date
        latest(int): controls how fast the weight decrease.
            0 - no decay, 1 - moderate decay,  2 - fast decay"""
    days_diff = (datetime.now() - datetime.strptime(date, "%d %B %Y")).days
    coef = (1.5 - 1 / (1 + exp(-days_diff / (400 / latest)))) ** latest
    return coef


def get_latest_flag(request_args, latest_max: int = 1):
    """parse the request arguments such as the latest priority flag"""
    if "latest-publication" in request_args:
        advanced = request_args
        latest = latest_max * (request_args.get("latest-publication") == "On")
    else:
        advanced = MultiDict()
        if re.search("(recent)|(latest)", request_args.get("q")):
            latest = latest_max
        else:
            latest = latest_max / 2

    return advanced, latest
