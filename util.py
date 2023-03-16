import datetime
import logging
import pytz

TRADING_HOURS = {
    "NASDAQ" : (datetime.time(9, 30, 0) ,datetime.time(16, 0, 0))       # 9:30am to 4:00pm
}

TRADING_DAYS = {
    "NASDAQ" : range(0,4)                                               # Monday to Friday
}


def log(message):
    print(datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S"),message)
    
def exchange_time():
    return datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S")

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

def check_trading_hours(exchange):
    return TRADING_HOURS[exchange][0] <=datetime.datetime.now(pytz.timezone('US/Eastern')).time() <= TRADING_HOURS[exchange][1]


def check_trading_days(exchange):
    return datetime.datetime.now(pytz.timezone('US/Eastern')).weekday() in TRADING_DAYS[exchange]


def check_exchange_active(exchange):
    return check_trading_hours(exchange) and check_trading_days(exchange)

def time_until_exchange_start(exchange):
    now = datetime.datetime.now(pytz.timezone('US/Eastern')).replace(tzinfo=None)
    next_start = datetime.datetime.combine(now,TRADING_HOURS[exchange][0]) 

    if now > next_start:
        next_start += datetime.timedelta(days=1)

    return next_start - now 

def time_until_exchange_end(exchange):
    now = datetime.datetime.now(pytz.timezone('US/Eastern')).replace(tzinfo=None)
    next_end = datetime.datetime.combine(now,TRADING_HOURS[exchange][1]) 

    if now > next_end:
        next_end += datetime.timedelta(days=1)

    return next_end - now
    
def main():

    print(check_trading_hours("NASDAQ"))
    print(check_trading_days("NASDAQ"))
    print(check_exchange_active("NASDAQ"))
    print(time_until_exchange_start("NASDAQ"))
    print(time_until_exchange_end("NASDAQ"))

if __name__ == "__main__":
  
  main()   