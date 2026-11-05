# Extração Quantitativa: stanford_crypto_pairs_trading.pdf

## Pagina 1

Crypto Trading 
Strategies
Apr 27, 2021
Amanda Brown
MS, MS&E ‘21
Jonathan Ling
MS, MS&E ‘21
Arjun Sawhney
MS, CS ‘21

---

## Pagina 2

Contents
Data Selection
Data Exploration
Methods
Evaluation
Data universe
Data availability
Handling missing data
Blockchain data
Asset correlation
Autocorrelation
Statistical arbitrage
Time series analysis
Deep learning
Toy model
Backtesting
Metrics

---

## Pagina 3

Dataset Selection

---

## Pagina 4

Data universe
7,800+ cryptocurrencies (as of Jan 2021)1
500+ cryptocurrency exchanges2
30+ public APIs available3; we looked into Kraken and Bitﬁnex as they had downloadable 
data without needing an API
BTCUSD is the most traded pair
Data availability: many new currencies have only been in existence for < 3 years
Data is mostly already clean, but missing when exchange is down or trade volume is zero
1 https://e-cryptonews.com/how-many-cryptocurrencies-are-there-in-2021/
2 https://www.cryptimi.com/guides/how-many-cryptocurrency-exchanges-are-there
3 https://github.com/public-apis/public-apis#cryptocurrency

---

## Pagina 5

Data source choice: Bitﬁnex is more liquid 
and has more complete data than Kraken
Bitfinex
Kraken
Difference
(Bitfinex - Kraken)
*Data was for BTCUSD from one sampled day (3/19/21)
Close price
Volume
Raw data
Difference
(Bitfinex - Kraken)

---

## Pagina 6

BTC/ETH/XRP-to-USD are the most data- 
complete currency pairs across 2019-21
We filtered for all currency pairs whose data 
availability percentage was above 60% for 
2019, 2020 and 2021 (only 5 pairs qualiﬁed), 
then plotted their availability.
From the data, BTC, ETH and XRP to USD are 
the most data-complete coins. This is 
conﬁrmed by the fact that they are also the 
top traded coins on coinmarketcap.com by 
volume and market capitalization.
Data availability (percentage non-missing) at 
the minute level for the most data-complete 
currency pairs in the Bitﬁnex data

---

## Pagina 7

Hourly-level data cleaning and availability 
was done by syncing ‘close’ timestamps
Exact filtering on on-the-hour timestamps
   +/- 2 minute timestamp leniency
Resolution technique for syncing “close” time stamps (+/- 2 minutes). This yielded much higher 
data availability percentage than minute-level data, as expected.
Data availability (percentage non-missing) at the hour level
calculated using two methods

---

## Pagina 8

Data Exploration

---

## Pagina 9

Time period of observations
Pairs Trading
●
Start: 2020-01-01
●
End: 2021-04
●
Frequency: by hour
Single-Asset Models
●
Start: 2018-01-01
●
End: 2021-04-01
●
Frequency: by minute & hour

---

## Pagina 10

Correlation matrix (hourly data), 
Sept. 2020 - Jan. 2021
Returns
Open Price

---

## Pagina 11

Time series correlations (BTC, ETH, XRP)
We observe extremely weak correlations at the minute level

---

## Pagina 12

Hourly returns (8 tokens)
34 hour lag
Top 4 Lagged Corrs:

---

## Pagina 13

Co-integrated pairs
Pairs where p-value is < 0.05:
(ETH, XLM) 
(DOT, ADA) 
(LTC, XLM)
Co-integration p-values (plotting p < 0.98)
XLM
ETH

---

## Pagina 14

Methods

---

## Pagina 15

Stat arb: pairs trading strategy
1.
Calculate price ratios of cointegrated pairs for all time points in training set (e.g. ‘eth’ 
divided by ‘xlm’)
2.
Get 6 hour moving average of ratios
3.
Get 72 hour moving average and standard deviation of ratios
4.
Calculate z-score
5.
If | z-score | > 2, sell the overperforming coin, buy the other
e.g. If ratio = eth price / xlm price, then 
if ratio is low (z < -2), buy ‘eth’ and sell ‘xlm’
If ratio is high (z > 2), sell ‘eth’ and buy ‘xlm’

---

## Pagina 16

Time series regression: autocorrelation and 
seasonality
●
We use lagged regression features up until some 
lookback time period to predict the target
●
Feature engineering can then be performed (as a 
function of the lookback) to account for non-linear 
signals and interactions
●
Seasonality settings will require further adjustments to 
make the model predictions more granular
Autocorrelation and seasonality
Model: neural network*
Autocorrelation
Model: regression
Actual log returns
Predicted log returns
Log returns
Log returns
Hours
*NeuralProphet library from Facebook

---

## Pagina 17

Deep learning approaches
Underway:
●
RNNs (recurrent neural networks)
○
LSTMs (long short-term memory)
Approaches to try next:
●
CNNs (convolutional neural networks)
●
Transformers

---

## Pagina 18

Evaluation

---

## Pagina 19

●
Rolling-window cross-validation approach
●
Accounting for seasonality or trends in model performance over time
Evaluating models: train, validate & test

---

## Pagina 20

●
Need to account for factors such as transaction costs and market impact
●
We aim to use Backtrader as our backtesting framework
●
It allows us to deﬁne data feeds to feed our models and also account for transaction 
costs, initial investments and the possibility of going long/short and trading on margin
Evaluating strategies: backtesting

---

## Pagina 21

Metrics for evaluation
We use different sets of metrics to evaluate our models and our strategies
●
For the model level, given that we focus on a regression task, we focus on the 
validation adjusted R2
●
For strategies, we consider the risk-adjusted return as our benchmark and so consider 
the Sharpe ratio as our strongest metric
●
To get a sense of our downside, we also consider our max-drawdown and win-ratio

---
