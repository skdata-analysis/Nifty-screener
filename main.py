''''
import streamlit as st
st.title("hello chai app")
st.subheader("i am creating a screener")
st.text("welcome to tbx")
st.write("chooseyour fav.variety of stock")
chai = st.selectbox("your fav stock",['reliance','tcs','infy','tatasteel'])
st.write(f"your choose {chai}.Excellent choice")
st.success("your chai has been brew")'''


'''
if st.button('reliance'):
    st.success(" this is your stock")
add_stock= st.checkbox("add your fav stock",["reliance","tcs"])  

if add_stock:
    st.write("reliance your favorite stock")  

stock_type= st.radio("pick up your chai base:",["tata steel","adaniports"])
st.write(f"selected base {stock_type}")
flavour = st.selectbox("choose stock:",["nse","bse","mcx"])

sugar=st.slider("how much you want to invest in cr", 0,20,5)

investment_amount=st.number_input("how much you wan tot invest", min_value=1,max_value=10,step=1)
st.write(f"selected investment amount is {investment_amount}")

name=st.text_input("enter your name")
if name:
    st.write("welcome to tbx")
    
dob = st.date_input("select your date of birth")
'''
import streamlit as st
st.subheader("your fav stock")
'''
col1,col2=st.columns(2)
with col1:
    st.header(" stock")
    vote1= st.button("vote for trading")
with col2:
    st.header("politican")
    vote2 = st.button("vote for modi")
    st.image("https://www.pexels.com/photo/monochrome-chess-game-in-progress-39008092/", width=200)
if vote1:
    st.success("thanks for choosing your stock")
    
if vote2:
    st.success("thanks for choossing modi ji")
    
name=st.sidebar.text_input("enter your name")
tea =st.sidebar.selectbox("choose your fav stock",["reliance","tcs","infy","tatasteel"])
st.write(f"your name is {name} and you choose {tea} Excellent choice") 

with st.expander("show how you invest"):
    st.write("this is how you invest in stock market")
    st.image("https://www.pexels.com/photo/monochrome-chess-game-in-progress-39008092/", width=200  )
    
    
''' 
import pandas as pd 
file = st.file_uploader("upload your stock data", type=["csv","xlsx"])
if file:
    df=pd.read_csv(file)
    st.write(df)
    st.success("your file has been uploaded successfully")
if file:
    st.subheader("this is option chain")
    st.write(df.describe())
    