import datetime
import logging
import pytz

TRADING_HOURS = {
    "NASDAQ" : (datetime.time(9, 30, 0) ,datetime.time(16, 0, 0)),      \
    "NYSE": (datetime.time(9, 30, 0) ,datetime.time(16, 0, 0)),
    "HKEX": (datetime.time(9, 30, 0) ,datetime.time(16, 0, 0))
}

TRADING_DAYS = {
    "NASDAQ" : range(5),
    "NYSE": range(5),
    "HKEX": range(5),                                                                                                                                                                                    # Monday to Friday
}

TIMEZONE = {
    "NASDAQ" : "US/Eastern",
    "NYSE": "US/Eastern",
    "HKEX": "Asia/Hong_Kong"
}


def exchange_time(exchange):
    return datetime.datetime.now(pytz.timezone(TIMEZONE[exchange])).strftime("%Y-%m-%d %H:%M:%S")

def setup_logger(logger_name, log_file, level=logging.INFO):
    l = logging.getLogger(logger_name)

    formatter = logging.Formatter('%(asctime)s %(name)-9s %(levelname)-8s %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

    fileHandler = logging.FileHandler(log_file, mode='a')
    fileHandler.setFormatter(formatter)
    fileHandler.setLevel(logging.ERROR)

    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    streamHandler.setLevel(logging.INFO)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)
    l.setLevel(logging.INFO)
    l.propagate = False    

def check_trading_hours(exchange,buffer=0):
    return (datetime.datetime.combine(datetime.datetime.now(),TRADING_HOURS["NASDAQ"][0])+datetime.timedelta(minutes=buffer)).time() <=datetime.datetime.now(pytz.timezone(TIMEZONE[exchange])).time() <= TRADING_HOURS[exchange][1]


def check_trading_days(exchange):
    return datetime.datetime.now(pytz.timezone(TIMEZONE[exchange])).weekday() in TRADING_DAYS[exchange]


def check_exchange_active(exchange, buffer=0):
    return check_trading_hours(exchange,buffer=buffer) and check_trading_days(exchange)

def time_until_exchange_start(exchange):
    now = datetime.datetime.now(pytz.timezone(TIMEZONE[exchange]))
    day = datetime.datetime.now(pytz.timezone(TIMEZONE[exchange])).weekday()

    if day in range(5) and now.replace(tzinfo=None) < datetime.datetime.combine(datetime.datetime.now(),TRADING_HOURS["NASDAQ"][0]):

        return datetime.datetime.combine(datetime.datetime.now(),TRADING_HOURS["NASDAQ"][0]) - now.replace(tzinfo=None)
        
    if day in range (4) or day == 6:
        day_diff = 1
    elif day == 4:
        day_diff = 3
    elif day == 5:
        day_diff = 2

    day = datetime.date.today() + datetime.timedelta(days=day_diff)
    next_start = datetime.datetime.combine(day,TRADING_HOURS[exchange][0]) 
  
    return next_start - now.replace(tzinfo=None)
  
def time_until_exchange_end(exchange):

    if check_exchange_active(exchange):
        now = datetime.datetime.now(pytz.timezone(TIMEZONE[exchange])).replace(tzinfo=None)
        next_end = datetime.datetime.combine(now,TRADING_HOURS[exchange][1]) 

        return next_end - now
    
    else:
        exchange_duration = datetime.datetime.combine(datetime.date.today(),TRADING_HOURS[exchange][1]) - datetime.datetime.combine(datetime.date.today(),TRADING_HOURS[exchange][0])
        return time_until_exchange_start(exchange) + exchange_duration
    
def main():
    # print(pytz.all_timezones)
    print(check_trading_hours("NASDAQ"))
    print(check_trading_days("NASDAQ"))
    print(check_exchange_active("NASDAQ"))
    print(time_until_exchange_start("NASDAQ"))
    print(time_until_exchange_end("NASDAQ"))
    print(type((datetime.datetime.combine(datetime.datetime.now(),TRADING_HOURS["NASDAQ"][0])+datetime.timedelta(hours=1)).time()))
    print(datetime.datetime.combine(datetime.datetime.now(),TRADING_HOURS["NASDAQ"][0]))
    print(datetime.datetime.now(pytz.timezone(TIMEZONE["NASDAQ"])).replace(tzinfo=None)<datetime.datetime.combine(datetime.datetime.now(),TRADING_HOURS["NASDAQ"][0]))
    # print(datetime.datetime.now(pytz.timezone(TIMEZONE["NASDAQ"])).weekday())

    # print(time_until_exchange_start("NASDAQ") + datetime.timedelta(minutes=10))
    # print(time_until_exchange_start("NASDAQ") >datetime.timedelta(hours = 5))
if __name__ == "__main__":
  
  main()   
