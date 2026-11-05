# Extração Quantitativa: ey_crypto_derivatives.pdf

## Pagina 1

Exploring crypto 
derivatives
An introduction of market 
landscape, emerging trends, 
valuation and risk management
February 2024

---

## Pagina 2

2 | Exploring crypto derivatives
In brief
•	 Despite the crypto recession, including high-profile crypto firm bankruptcies 
and the collapse in crypto asset prices since 2022, crypto derivatives markets 
are expected to continue to evolve with the introduction of new products and 
innovations in decentralized finance (DeFi) protocols.
•	 Crypto derivatives can be valued using the models with which we are familiar 
from traditional finance (e.g., the classical Black-Scholes model for option pricing 
under the condition of no arbitrage, which is widely used by options market 
participants), with key modeling considerations taking into account the unique 
characteristics of underlying crypto assets.1
•	 Effective risk management for crypto derivatives is crucial due to the high 
volatility, leverage and complexity of these instruments. It plays a pivitol role in 
ensuring protection against significant losses and promoting informed decision-
making in a rapidly evolving market.
1	
In this article, crypto assets refer to private digital assets that depend on cryptograph and 
distributed ledger technologies or similar technologies, and hence include all cryptocurrencies 
(e.g., Bitcoin (BTC) and Ethereum (ETH)).
The views reflected in this article are the views of the authors and do not necessarily 
reflect the views of Ernst & Young LLP or other members of the global EY organization.

---

## Pagina 3

3 | Exploring crypto derivatives
The trading volume of the crypto derivatives market has 
experienced substantial growth over the past few years, 
increasing from under US$100 billion in January 2019 to 
a peak of over US$4 trillion in May 2021. Despite a recent 
downward dip, as of September 2023, the monthly volume of 
crypto derivatives stands at US$1.33 trillion, which is nearly 
four times the size of the crypto spot market.[1] BTC and ETH 
are the most frequently referenced crypto assets in crypto 
derivatives.
The crypto derivative market can be categorized into two 
segments centralized and decentralized: 
•	 The centralized derivative market is primarily composed 
of exchange-traded options, futures and perpetual swaps, 
while over-the-counter (OTC) crypto derivatives are also 
growing rapidly. In the case of BTC- and ETH-referenced 
derivatives, as of September 2023, 96.2% of monthly 
trading volume is attributed to futures and perpetual 
swaps.[2] Taking a geographic lens: 
•	 The non-US market is the major contributor to the crypto 
derivative market and accounts for over 95% of the 
monthly derivative trading volume globally, with the top 
three exchanges holding a market share of 84.7%, as of 
September 2023. [1] 
•	 	The US market, on the other hand, accounts for the 
remaining less than 5% of the monthly derivative trading 
volume, with CME being the dominant exchange. As of 
September 2023, CME holds a market share of over 60% 
of the monthly derivative trading volume in the US.[1] 
•	 The decentralized2 derivative market offers a secure 
and more transparent alternative to the centralized 
counterpart, removing the need for intermediaries. While 
the decentralized derivative market is still much smaller 
compared with the centralized derivative market, it is 
growing rapidly. The current DeFi derivative market is 
largely dominated by dYdX protocol for perpetual swaps. As 
of September 2023, the monthly trading volume of dYdX 
was reported at $8.30 billion.[3] 
Despite the high-profile crypto firm bankruptcies in the 
2022 crypto recession, which have led to increased calls for 
greater regulation of the crypto asset industry, including 
the derivatives-trading sector, it is expected that the crypto 
derivatives market will continue to grow and evolve with the 
launch of new products that address market participants’ 
investment and hedging needs. Noteworthy examples of 
such products are UpDown options launched for US users by 
Crypto.com,[4] Luxor’s Hashprice NDF3 [5] and FalconX’s staking 
yield swap.[6] Moreover, the DeFi sector is expected to propel 
innovation in crypto derivatives (e.g., DeFi options vaults[7] and 
DeFi interest rate swaps (IRSs)[8]), as DeFi investors explore 
novel means to manage risk and generate yield. 
2	
While these markets are often referred to as decentralized, it’s 
important to note that their level of decentralization is debatable. 
Many of these markets rely on automated algorithms and smart 
contracts rather than being fully decentralized in contrast to traditional 
centralized markets.
3	
Luxor’s Hashprice NDF references mining computation power (a 
commodity-like underlying) rather than a direct crypto asset.
Crypto 
derivatives 
market overview

---

## Pagina 4

4 | Exploring crypto derivatives
In this section, we will introduce the pricing methodology 
for three types of crypto derivatives: options, futures and 
perpetual swaps. Valuation of crypto derivatives is a critical 
prerequisite of measuring and managing financial risk, 
including market risk, counterparty credit risk and liquidity 
risk, as discussed in subsection “Crypto derivative risk types.” 
Additionally, we will provide the overview on the most recent 
advancements in crypto derivative products.
Options
Crypto options offer a similar payout as traditional options, 
but with a crypto asset (usually a cryptocurrency or crypto 
index) serving as the underlying asset. Crypto option contracts 
can be settled either in cash or physically. The crypto options 
market inherits the Black-Scholes framework and quotes 
implied volatilities similar to traditional finance. A sample 
implied volatility surface on BTC as of November 10, 2023, is 
shown in Figure 1. This sample implied volatility surface covers 
a wide range of maturities (from one day to one year) and 
strikes (from $10,000 to $75,000). 
Figure 1: Sample implied volatility surface on BTC as 
of November 10, 2023
Crypto derivative 
products and 
valuation 
considerations
Source: Deribit.

---

## Pagina 5

5 | Exploring crypto derivatives
Sample plot
Sample plot
Volatility skew for BTC option withmaturity 0.14-year as of 
11/10/2023
Reverse skew – with price of underlying at $50
Volatility smile
Forward skew – with price of underlying at $50
Volatility skew type
Severe positive skew for crypto options
Volatility skew type 
U-shaped volatility smile for FX options 
and short-term equity options
Volatility skew type 
Reverse skew for long-term equity options
Volatility skew type 
Forward skew for commodity options
Table 1: Volatility skew comparison for crypto and traditional options [9]
Implied volatility percent
Volatility increases as options
become increasingly in-the-money
or out-of-the-money
At-the-money options
In-the-money calls
In-the-money puts
Out-of-the-money puts
Out-of-the-money calls
Strike price $
50
60
70
80
90
100
100
90
80
70
60
50
40
30
Implied volatility percent
Strike price (thousand $)
0
20
40
60
80
100
70
65
60
55
50
45
40
35
30
Implied volatility percent
Strike price $
0
20
40
60
80
100
70
65
60
55
50
45
40
35
30
Implied volatility percent
Strike price $
The crypto options market exhibits volatility skew. A sample of the volatility skew as of 
November 10, 2023, for European BTC options with a maturity of 0.14 years is shown in Table 1. This 
skew is characterized by a heavy right tail, which contrasts with the observed skews of traditional asset 
classes in Table 1. As shown in the first plot in Table 1, the largest strike with an implied volatility from 
the market is about 2.7 times as large as the ATM strike. This heavy right tail is believed to be due 
to extreme fluctuations in crypto asset prices, as well as a belief held by some investors that prices 
will move much higher in the next several weeks. Such a severe positive skew requires enhancements 
of standard volatility models to better fit the heavy tail of implied volatilities on high strikes.

---

## Pagina 6

6 | Exploring crypto derivatives
The options on more thinly traded crypto assets typically have 
fewer traded expiry dates. This presents a challenge when 
it comes to market making or valuing OTC-traded options 
without market quotes for specific moneyness and expiry 
levels. A common solution is to proxy the implied volatilities to 
the liquid implied volatilities of more established crypto assets, 
such as BTC or ETH. This is possible due to the high correlation 
among crypto assets. For example, if the volatility of a certain 
crypto asset C is not available, the implied volatility σ(C,T,K) 
with expiry T and strike K can be proxied using the ETH 
implied volatility surface and historical volatilities of ETH/C 
price returns. Particularly, the implied volatility of C can be 
calculated as follows:
Where
•	 	SC,t0: the price (in USD) of crypto asset C observed at 
valuation time t0
•	 	σhist (C,t0): the standard deviation of relative daily historical 
price return (i.e., 
 ) right before valuation time t0 for 
crypto asset C
Note that using the above implied volatility scaling 
methodology can under/overestimate option prices due to the 
potential of a poorly established proxy relationship.
Futures
Crypto futures offer a similar payout as traditional futures, 
but with the underlying asset being a crypto asset (usually a 
cryptocurrency or crypto index). Crypto futures contracts can 
be settled either in cash or physically.  Many crypto assets 
have liquid futures markets, providing valuable insight into 
market expectations for the underlying crypto asset’s future 
spot price. Here are two examples:
1. As shown in Figure 2, the BTC futures market is in 
backwardation as of March 12, 2023, while the BTC 
futures market is overall in contango as of November 10, 
2023. In fact, the shape of the futures curve, whether 
it be in a state of backwardation or contango, can 
provide valuable information about market sentiment 
and investment strategy. For instance, research[10] 
highlighted that crypto futures carry, the gap between 
futures and spot prices, can reach 60% per annum and 
vary greatly due to a volatile convenience yield. This 
is driven by smaller investors seeking leverage during 
booms and limited arbitrage capital in risky cash and 
carry positions. This dynamic, coupled with high leverage, 
can lead to frequent severe crypto market crashes.
32,000
34,000
36,000
38,000
40,000
42,000
1.0
0.8
0.6
0.4
0.2
0.0
BTC spot price as of 11/10/2023
BTC futures price as of 11/10/2023
Futures price ($)
Maturity (year)
BTC spot price as of 03/12/2023
BTC futures price as of 03/12/2023
20,000
20,500
21,000
21,500
22,000
Figure 2: Sample futures curves for BTC
Source: Deribit.

---

## Pagina 7

7 | Exploring crypto derivatives
2.	In a typical bearish crypto market, such as September 
2022, a large negative ETH futures implied yield4 was 
observed (as depicted in Figure 3), reflecting significant 
short positions and corresponding high borrowing costs.  It 
aligns with the market’s expectation for further decline in 
ETH prices.
In addition, despite the fact that crypto asset is generally a 
lightweight asset without any material storage cost, there 
are some unique costs associated with crypto assets, such as 
counterparty risk to the exchanges.
Perpetual swaps
A perpetual swap, also known as a “perpetual futures 
contract,” is an agreement to non-optionally buy or sell the 
underlying asset at an unspecified future point. Similar to a 
futures contract, it allows traders to speculate on the future 
crypto asset price movements. However, compared with 
regular futures, there is not any prespecified expiration date 
4	
Defined as 1
t log(Ft /S0), where Ft is the crypto future price with maturity 
t and S0 is the crypto asset spot price.
Source: Deribit.
-40
-30
-20
-10
0
27 Sep
24 Sep
21 Sep
18 Sep
15 Sep
12 Sep
9 Sep
6 Sep
Futures implied yield, percent
Date (2022)
Figure 3: Daily futures implied yields for ETH  
futures with maturity September 30, 2022,  
in September 2022 
for the perpetual swap, and this perpetual swap can be held 
indefinitely without any need to roll over contracts.
Although perpetual swaps were first introduced in 1992 to 
enable derivatives markets for illiquid assets,[11] perpetual 
swap markets have been developed for only crypto assets, 
and these markets have grown significantly since BitMex 
introduced crypto perpetual swaps in 2016. As of November 
2023, the crypto perpetual swap is the most liquid crypto 
derivative with the largest market notional value.
Crypto perpetual swaps are cash-settled contracts. Traders 
can take long (buy) or short (sell) positions based on their 
market predictions. To ensure that the contract’s price stays 
aligned with the spot market, a funding rate is introduced. This 
funding rate provides a mechanism for the perpetual swap to 
closely track its underlying crypto asset price, particularly, 
if the crypto perpetual swap price is higher (or lower) than 
the underlying crypto asset price, the funding rate is positive 
(or negative), and long (or short) traders would pay short (or 
long) traders, which incentivizes additional short (or long) 
position trading of perpetual swaps. In essence, this funding 
rate is a rebate or fee that helps to balance the short and long 
positions of perpetual swaps.

---

## Pagina 8

8 | Exploring crypto derivatives
The funding rate is generally calculated 
over a fixed time interval using the price 
difference between the crypto perpetual 
swap and the underlying crypto asset, 
and the funding fee (as the product of 
dollar position value and funding rate) is 
generally settled every eight hours. The 
recent funding rates for BTC perpetual 
swaps are presented in Figure 4 for the 
top five exchanges in terms of daily 
trading volume as of December 10, 
2023. Due to the different calculation 
methods on funding rate and long/
short trading positions by exchanges, 
this funding rate at a fixed time point 
can be positive for some exchanges but 
negative for other exchanges. 
New derivative product innovation
In addition to options, futures and perpetual swaps, several novel derivative products that have no counterpart in traditional 
assets have emerged in recent years. Although the valuation methodology for these products is still in the early stages of 
development, it is expected that the trend of meeting market participants’ hedging and investment needs through such 
innovation will continue to flourish. Below, we discuss three notable examples:
Date (2023)
4th Exchange
5th Exchange
2nd Exchange
3rd Exchange
1st Exchange
8 Dec
5 Dec
2 Dec
29 Nov
26 Nov
23 Nov
20 Nov
17 Nov
14 Nov
11 Nov
8 Nov
Funding rate, percent
-0.01
0.00
0.01
0.02
0.03
0.04
0.05
Figure 4: Sample funding rates for BTC perpetual swap
Source: Coinglass.
UpDown option [4] 
This is a Commodity Futures Trading 
Commission (CFTC)-regulated product 
listed on Crypto.com Derivatives 
North America, a US-regulated 
exchange. As a unique type of option, 
the UpDown option automatically 
expires when the underlying asset 
price reaches a predetermined target 
or stop price. These options offer 
several benefits, such as potentially 
limiting losses, providing full exposure 
to asset price fluctuations at a 
reduced cost and facilitating tailored 
hedging strategies. Nevertheless, 
UpDown options also possess certain 
drawbacks, which may include capped 
profit potential and a heightened 
risk of premature termination in 
turbulent market conditions.
Bitcoin Hashprice non-deliverable 
forward (NDF) [5]
Hashprice quantifies how much a 
bitcoin miner can expect to earn from 
a specific quantity of hashrate (i.e., 
compute power). Given the volatility 
of bitcoin price, the NDF provides 
bitcoin miners with a much-needed tool 
to hedge their mining operations by 
selling the contract to lock in bitcoin 
mining revenue. In the meantime, 
contract buyers can participate in the 
potential upside of bitcoin mining with 
nonphysical exposure. The valuation 
of the NDF contract depends on 
forward-looking market expectations 
of block subsidy, transaction fees, 
network difficulty and bitcoin price. 
Staking yield swap [6]
Interest rate swaps have long been 
a fundamental building block in 
traditional, fixed-income derivative 
markets. Such an instrument has been 
reinvented for the crypto world, where 
the staking yield swap is introduced to 
exchange fixed payments for floating 
payments (or vice versa) based on 
variable fees earned from staking ETH. 
In addition to providing synthetic access 
to staking yields, the staking yield 
swap allows for more intricate trading 
strategies for hedging and investing, as 
well as facilitating the introduction of 
structured product innovations. 
1
2
3

---

## Pagina 9

9 | Exploring crypto derivatives
Crypto derivatives have gained popularity in recent years, 
providing investors with an opportunity to gain exposure to 
crypto assets without actually holding the underlying assets. 
However, like other financial products, these derivatives also 
carry various types of risks that need to be understood and 
managed carefully. 
Crypto derivative risk types
The lifecycle of trading crypto derivatives primarily 
encompasses the following risk types: 
•	 Market risk stems from the potential financial loss due 
to unfavorable fluctuations in market prices. Accurate 
valuation of crypto derivatives is vital for calculating 
real-time or daily profit and loss (P&L) and estimating 
value at risk (VaR) or expected shortfall. Such measures 
help estimate losses associated with market movements 
corresponding to a high percentile (e.g., 99%). Emphasizing 
extreme crypto asset volatility, market participants must 
remain vigilant and incorporate strategies to manage the 
heightened market risk in the inherently volatile crypto 
landscape.
•	 Counterparty credit risk (CCR) is the risk of financial 
loss due to a counterparty’s unwillingness or inability to 
fulfill their obligations. Models measuring counterparty 
credit risk typically involve simulating market factors using 
Monte Carlo approaches and accurate valuation along 
time points in each simulated path to compute potential 
future exposures. In addition, properly capturing collateral 
requirements for variation margin (VM) and initial margin 
(IM) is crucial for CCR calculation.
•	 Liquidity risk can manifest in two forms: funding liquidity 
risk and market liquidity risk. Funding liquidity risk refers 
to potential financial losses stemming from an inability to 
meet liabilities. Market participants should address funding 
liquidity risk by factoring in the funding costs associated 
with posting collateral throughout the duration of the 
derivatives contract. This is commonly known as a “funding 
valuation adjustment” (FVA). Market liquidity risk arises 
when difficulties in selling assets at current market prices 
lead to losses. Participants should take this into account as 
a liquidity valuation adjustment (LVA).
•	 Operational risks in trading and managing crypto 
derivatives are diverse and complex: 
•	 	One critical consideration is the management of margin 
requirements imposed by trading venues, such as 
dealers or exchanges. This aspect can present various 
challenges, including potential margin calls, abrupt 
increases in margin requirements and other operational 
hurdles. Traders should have a thorough understanding 
of these margin requirements and maintain sufficient 
collateral buffers to handle potential market fluctuations. 
•	 	Technological vulnerabilities inherent in blockchain 
systems and smart contracts, coupled with cybersecurity 
threats, further complicate the risk landscape. Failures or 
malfunctions in trading platforms can lead to substantial 
losses, and the rapid pace of crypto markets introduces 
execution risks. The reliance on third-party services, 
such as wallet providers, adds another dimension of risk.
•	 Legal and compliance risk pertains to potential financial 
or other losses stemming from non-compliance with laws 
or regulations. This risk is amplified within cryptocurrency 
markets due to their decentralized and global structure 
coupled with inconsistent regulatory frameworks across 
jurisdictions. Certain crypto assets and activities face 
Crypto derivative 
risk management

---

## Pagina 10

10 | Exploring crypto derivatives
ongoing regulatory, legislative, and judicial uncertainties, 
including in major economies like the United States. 
Moreover, many active crypto derivative exchanges operate 
outside prominent jurisdictions, hence lacking the stringent 
regulatory oversight demanded by agencies like the U.S.’s 
CFTC, and posing additional risks to market participants.
All of these factors emphasize the crucial need for robust 
controls and a comprehensive risk management approach 
when trading and managing crypto derivatives.
Crypto derivative-specific risk modeling 
considerations 
In comparison with traditional asset risk modeling, crypto 
derivative-specific risk modeling considerations pose unique 
challenges. These challenges stem from the characteristics of 
the underlying crypto assets and the crypto markets in which 
they trade. Six key aspects to consider when developing risk 
models for crypto derivatives are:
1.	High volatility: Crypto assets tend to exhibit 
higher volatility than traditional assets, which can 
result in large price swings. This necessitates the 
incorporation of higher volatility estimates in market 
risk models to accurately capture the potential losses 
and risks associated with these instruments.
2.	Continuous trading: Crypto markets operate on a 
24/7 basis, unlike traditional financial markets, which 
have set trading hours. This continuous trading can 
lead to nonuniform price movements and liquidity 
changes over time. Risk models should account for 
this by adjusting the frequency of P&L calculations 
and considering intraday risk measures.
3.	Legal enforceability: The absence of a standardized 
legal framework for the netting and margining of 
crypto assets increases CCR for crypto derivatives. 
This uncertainty should be factored in when calculating 
margin requirements and exposure aggregation.
4.	Crypto collateral: Crypto assets are often used as 
collateral for derivative transactions; however, there 
is limited historical data on the liquidation costs of 
these collaterals during stress periods. This introduces 
additional uncertainty in the liquidity risk modeling 
process, which requires considering incorporating 
alternative stress scenarios or applying conservative 
assumptions to account for this limitation.
5.	Regulatory considerations: The regulatory 
environment for crypto derivatives is still evolving, 
and it is crucial to be cognizant of potential changes 
in regulations that could impact risk modeling 
assumptions or methodologies. Regular updates 
and reviews of the models should be conducted to 
ensure compliance with any regulatory changes.
6.	Market concentration: Crypto markets can 
be characterized by a high degree of market 
concentration, with a few dominant players or 
exchanges exerting significant influence. Risk models 
should account for potential risks arising from this 
concentration, such as increased vulnerability to 
market manipulation or abrupt liquidity shifts.
How we can help
Ernst & Young LLP offers extensive 
support for crypto derivatives valuation 
and risk modeling and management, 
adhering to industry practices 
and regulatory requirements. 
Our services encompass:
•	 Development, enhancement and implementation/integration of models
•	 Testing and documentation of models
•	 Validation and ongoing monitoring of models
•	 Dynamic lifecycle transformation of models, including optimizing 
strategies and adopting agile modeling approaches
•	 Regulation compliance support
•	 Risk identification, measurement, management and reporting

---

## Pagina 11

11 | Exploring crypto derivatives
[1]	 Exchange Review, Cryptocompare, September 2023. 
[2]	 Bitcoin futures charts: open interest and exchange volumes, 
The Block, theblock.co/data/crypto-markets/futures.
[3]	 dYdX Perpetual Trade Volume, CoinGecko, dYdX Perpetual 
Trade Volume, Trade Pairs & Trust Score | CoinGecko.
[4]	 What Are UpDown Options?, Crypto.com.
[5]	 OTC Trading Desk for Bitcoin Mining Derivatives: Live 
Hashprice Chart, Luxor, https://luxor.tech/derivatives.
[6]	 FalconX Executes First-Ever Staking Yield Swap with 
Figment, Unlocking New Opportunities By Pioneering a 
Brand New Crypto Derivatives Market, news release, May 9, 
2022, FalconX.
[7]	 An Explanation of DeFi Options Vaults (DOVs), QCP Capital, 
December 12, 2021.
[8]	 Jones, Simon and Begyan, Artur, An Automated Market 
Maker for Interest Rate Swaps, Voltz Protocol, December 
2021 (website-files.com).
[9]	 Volatility Smiles & Smirks, The Options & Futures Guide 
(theoptionsguide.com).
[10]	Schmeling, Maik, Schrimpf, Andreas and Todorov, Karamfil, 
BIS Working Papers No 1087: Crypto carry, BIS website, 
April 2023, bis.org/publ/work1087.pdf.
[11]	Shiller, Robert J. Measuring Asset Values for Cash 
Settlement in Derivative Markets: Hedonic Repeated 
Measures Indices and Perpetual Futures, Journal of Finance, 
July 1993.
References

---

## Pagina 12

EY  |  Building a better working world
EY exists to build a better working world, helping 
to create long-term value for clients, people and 
society and build trust in the capital markets. 
Enabled by data and technology, diverse EY teams in 
over 150 countries provide trust through assurance 
and help clients grow, transform and operate. 
Working across assurance, consulting, law, strategy, 
tax and transactions, EY teams ask better questions 
to find new answers for the complex issues facing 
our world today.
EY refers to the global organization, and may refer to one or more,  
of the member firms of Ernst & Young Global Limited, each of which is a 
separate legal entity. Ernst & Young Global Limited, a UK company limited 
by guarantee, does not provide services to clients. Information about 
how EY collects and uses personal data and a description of the rights 
individuals have under data protection legislation are available  
via ey.com/privacy. EY member firms do not practice law where prohibited 
by local laws. For more information about our organization, please visit 
ey.com.
© 2024 Ernst & Young LLP  
All Rights Reserved.
US SCORE no. 22441-241US_2 
2312-4391060
ED None
This material has been prepared for general informational purposes only and is not intended 
to be relied upon as accounting, tax, legal or other professional advice. Please refer to your 
advisors for specific advice.
ey.com
Ming Shi
Managing Director,  
Quantitative Advisory Services 
Ernst & Young LLP
ming.shi@ey.com
Donald Cheng
Senior Manager,  
Quantitative Advisory Services 
Ernst & Young LLP
donald.cheng@ey.com
Seha Islam
Senior Manager,  
Financial Risk Management 
Ernst & Young LLP
seha.islam@ey.com
Yang Yang
Senior Manager,  
Quantitative Advisory Services 
Ernst & Young LLP
yang.yang4@ey.com
Contact us
Authors

---
