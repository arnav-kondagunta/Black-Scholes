#import packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import norm
import yfinance as yf
import os
from fredapi import Fred
from dotenv import load_dotenv, dotenv_values
import streamlit as st
import datetime

#assigning env variables
load_dotenv()
FED_API_KEY = os.getenv('FED_API_KEY')
FED_RATES = ['DGS1', 'DGS2', 'DGS3', 'DGS5', 'DGS7', 'DGS10', 'DGS20', 'DGS30', 'DGS3MO', 'DGS6MO', 'DGS1MO', 'DGS2MO', 'DGS3MO', 'DGS6MO', 'T10YIE', 'FEDFUNDS']

fred = Fred(api_key=FED_API_KEY)

#fetch yfinance stock data
def get_stock_data(ticker, period='1y'):
    stock = yf.Ticker(ticker)
    stock_price = stock.history(period='1d')['Close'][0]
    hist = stock.history(period=period)
    hist['returns'] = hist['Close'].pct_change()
    volatility = hist['returns'].std() * (252 ** 0.5)
    return stock_price, volatility, hist
    

#fetch risk free rate from fred data
def get_fred_data(rate_id):
    fred = Fred(api_key=FED_API_KEY)
    risk_free_rate = fred.get_series(rate_id).iloc[-1] / 100
    return risk_free_rate

#black-scholes model
def black_scholes_calc(S0, K, r, T, sd, option_type='call'):

    #First, determine d1 and d2
    d1 = 1/(sd*np.sqrt(T)) * (np.log(S0/K) + (r+sd**2/2)*T)
    d2 = d1 - sd*np.sqrt(T)

    #Next, find norm cdf of d1 and d2
    nd1 = norm.cdf(d1)
    nd2 = norm.cdf(d2)

    n_d1 = norm.cdf(-d1)
    n_d2 = norm.cdf(-d2)

    #Then, find call and put value
    call = round(nd1*S0 - nd2*K*np.exp(-r*T), 2)
    put = round(K*np.exp(-r*T)*n_d2 - S0*n_d1, 2)

    if option_type=="Call":
        return call
    elif option_type=="Put":
        return put
    else:
        print("Wrong option type specified")

def get_time_period(expire_date):
    today = datetime.date.today()
    time_period = int(abs((expire_date - today).days))
    return time_period / 365



#streamlit title
st.title("Black-Scholes Options Pricing Model")

#data input
ticker = st.text_input("Enter the ticker for your stock:", key='ticker', value='AAPL')
strike_price = float(st.text_input("Enter the strike price of the option:", key='strike_price', value=18))
expire_date = st.date_input("Enter the expiration date of your option:", key='expire_date', value=datetime.date(2028, 1 ,1))
risk_free_rates = st.selectbox("Risk-free rate options", FED_RATES, key="rates", index=5)
opt_type = st.selectbox("What is your option type?", ("Call", "Put"))


if ticker:
    stock_price, volatility, hist = get_stock_data(st.session_state.ticker)
else:
    st.write('Please enter a valid stock ticker symbol.')

if expire_date:
    time = get_time_period(st.session_state.expire_date)
else:
    st.write('Please enter a valid date.')

if risk_free_rates:
    rate = get_fred_data(st.session_state.rates)


st.write("### Inputs")
st.write(f"Ticker: {ticker}")
st.line_chart(hist['Close'])
st.write(f"Spot price: ${stock_price:.2f}")
st.write(f"Strike price: ${strike_price:.2f}")
st.write(f"Time: {time:.2} years")
st.write(f"Risk-free rate ({st.session_state.rates}): {rate:.2%}")
st.write(f"Volatility: {volatility:.2%}")

st.write("### Output")
if ticker and stock_price and rate and time and volatility:
    value = black_scholes_calc(stock_price, strike_price, rate, time, volatility, opt_type)
    st.write(f"The value of your option is ${value}")
else:
    st.write('Error. Please try again.')