trading_electricity_rhizome
==============================

MVP for trading in day ahead spot markets in europe. 
- Forecast 24 hour prices
- Actions strategy based on forecasted values


Please download require data before run.

### QuickStart
* At the root of the project run : 
```
python src/main.py --market_name=<market_name> --exp_name=<exp_name> 
```
* 3 markets avaliable : germany, france uk.
* Modify experience params in `1.yml`.