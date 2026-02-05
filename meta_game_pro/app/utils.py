from datetime import date, datetime, timedelta

def today_str():
    return date.today().isoformat()

def parse_date(s: str):
    return datetime.strptime(s, "%Y-%m-%d").date()

def week_bounds(d):
    # Monday..Sunday
    start = d - timedelta(days=d.weekday())
    end = start + timedelta(days=6)
    return start, end

def month_bounds(d):
    start = d.replace(day=1)
    if d.month == 12:
        nextm = d.replace(year=d.year+1, month=1, day=1)
    else:
        nextm = d.replace(month=d.month+1, day=1)
    end = nextm - timedelta(days=1)
    return start, end
