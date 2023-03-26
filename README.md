# trading-bot
Python-based trading bot using a naive pair trading strategy as an example (only for learning pupose)

# Usage
Create the following config files as per your use case and research

1. /config/account_example.json
```
{
    "host": "127.0.0.1",                                         
    "port": 7496,                                                 
    "clientid": 0,                                                  
    "accountid":  "",
    "currency": "USD",
    "exchange": "NASDAQ"
}       
```

2. /config/spread_example.json
```
{
    "name": "spread1",
    "exchange" : "NASDAQ",
    "sec_type" : "STK",
    "symbol_first" : "STOCK_A",
    "symbol_second" : "STOCK_B",
    "pair": ["STOCK_A","STOCK_B"],
    "hedge_ratio" : ,                                                                 
    "spread_mean" : ,                         
    "spread_std" : , 
    "entry_Zscore" : 1,
    "exit_Zscore" : 0
}     
```
Simply run
```
python run.py
```
