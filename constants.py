import datetime

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

SEC_TYPE = {
    "STK",
    "CASH",
    "CMDTY"
}

ORDER_TYPE = {
    "LIMIT",
    "MARKET",
    "MID_PRICE"
}

ACTION = {
    "BUY",
    "SELL"
}