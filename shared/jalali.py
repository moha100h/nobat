import jdatetime
from datetime import date, datetime, timedelta
import pytz

TEHRAN_TZ = pytz.timezone("Asia/Tehran")

def to_jalali(d): return jdatetime.date.fromgregorian(date=d).strftime("%Y/%m/%d")
def jalali_to_gregorian(y, m, d): return jdatetime.date(y, m, d).togregorian()
def now_tehran(): return datetime.now(TEHRAN_TZ)
def today_tehran(): return now_tehran().date()
def next_n_days(n=14): return [today_tehran() + timedelta(days=i) for i in range(n)]
def weekday_fa(d):
    names = ["دوشنبه","سه\u200cشنبه","چهارشنبه","پنج\u200cشنبه","جمعه","شنبه","یکشنبه"]
    return names[d.weekday()]
