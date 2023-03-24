# trading-bot
Python-based trading bot using a naive pair trading strategy as an example (only for learning pupose)

# usage
Create the following config files as per your 

/config/account_example.json
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

/config/spread_example.json
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


```
python run.py
```
