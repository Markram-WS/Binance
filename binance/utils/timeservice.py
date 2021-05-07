import time


def get_current_timestamp():
    return int(round(time.time() * 1000))


def convert_cst_in_second_to_utc(time_in_second):
    if time_in_second > 946656000:
        return (time_in_second - 8 * 60 * 60) * 1000
    else:
        return 0


def convert_cst_in_millisecond_to_utc(time_in_ms):
    if time_in_ms > 946656000000:
        return time_in_ms - 8 * 60 * 60 * 1000
    else:
        return 0

def timestampToDatetime(tm):
    time_tuple = time.gmtime(tm)
    return time.strftime("%Y-%m-%d %H:%M:%S", time_tuple)

def datetimeToTimestamp(tm):
    time_tuple = time.strptime(tm, "%Y-%m-%d %H:%M:%S")
    return int(time.mktime(time_tuple))
