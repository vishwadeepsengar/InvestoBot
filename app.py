import os
import streamlit as st
import yfinance as yf
import pandas as pd

from dotenv import load_dotenv

from chatbot import ask_groq_deepseek
from rag import answer_with_rag
from calculators import (
    lumpsum_investment,
    sip_investment,
    loan_emi,
    retirement_corpus,
)

# -------------------------------
# Basic setup
# -------------------------------
load_dotenv()

st.set_page_config(
    page_title="InvestoBot Prototype",
    layout="wide",
    page_icon="💹",
)

# Custom CSS
st.markdown(
    """
<style>
body {
    background-color: #f5f7fa;
}
h1, h2, h3, h4 {
    color: #0d6efd;
}
.stButton>button {
    background-color: #0d6efd;
    color: white;
}
.stTextInput>div>input {
    border-radius: 10px;
    padding: 10px;
}
</style>
""",
    unsafe_allow_html=True,
)

st.sidebar.title("💹 InvestoBot")
mode = st.sidebar.radio(
    "Choose a feature:",
    ["Chatbot", "Stock Data Lookup", "PDF / News Q&A", "Smart PDF / News Q&A", "Finance Calculators"],
)

st.title("💹 InvestoBot – Personal Finance Assistant")


# -------------------------------
# 1️⃣ Chatbot Mode (Groq LLM)
# -------------------------------
if mode == "Chatbot":
    st.header("💬 Finance Chatbot ")

    user_input = st.text_input("Ask me anything about finance or investing:")

    if st.button("Ask"):
        if user_input.strip():
            with st.spinner("Thinking..."):
                # You already have ask_groq_deepseek() in chatbot.py
                reply = ask_groq_deepseek(
                    f"""
You are InvestoBot, a cautious financial education assistant.
Answer clearly and simply. Always avoid guaranteeing returns.
At the end, add: "This is general educational information, not investment advice."

User question: {user_input}
"""
                )
            st.success(reply)
        else:
            st.warning("Please type a question.")


# -------------------------------
# 2️⃣ Stock Data Lookup Mode
# -------------------------------
elif mode == "Stock Data Lookup":
    st.header("📊 Stock Data Lookup")

    ticker = st.text_input("Enter stock ticker (e.g., AAPL, TSLA, RELIANCE.BO):")
    option = st.selectbox(
        "Select data type:",
        ["Current Price", "Historical Prices", "Dividends", "Market Info"],
    )

    if st.button("Get Data"):
        if ticker.strip():
            try:
                stock = yf.Ticker(ticker)

                if option == "Current Price":
                    price = stock.info.get("currentPrice", None)
                    if price:
                        st.metric(
                            label=f"{ticker.upper()} Current Price",
                            value=f"{price:.2f}",
                        )
                    else:
                        st.warning("Price data not available.")

                elif option == "Historical Prices":
                    period = st.selectbox(
                        "Select period:", ["1mo", "3mo", "6mo", "1y", "5y"]
                    )
                    hist = stock.history(period=period)
                    if not hist.empty:
                        st.line_chart(hist["Close"])
                        st.success(f"Showing closing prices for {period}")
                    else:
                        st.warning("No historical data found.")

                elif option == "Dividends":
                    dividends = stock.dividends
                    if not dividends.empty:
                        st.line_chart(dividends)
                        st.success("Dividend history chart")
                    else:
                        st.warning("No dividend data found.")

                elif option == "Market Info":
                    info = stock.info
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("52 Week High", info.get("fiftyTwoWeekHigh", "N/A"))
                        st.metric("Volume", info.get("volume", "N/A"))
                    with col2:
                        st.metric("52 Week Low", info.get("fiftyTwoWeekLow", "N/A"))
                        st.metric("Market Cap", info.get("marketCap", "N/A"))
                    with col3:
                        st.metric("PE Ratio", info.get("trailingPE", "N/A"))

            except Exception as e:
                st.error(f"Error fetching stock: {e}")
        else:
            st.warning("Please enter a ticker symbol.")


# -------------------------------
# 3️⃣ PDF / News Q&A (RAG + Groq, simple)
# -------------------------------
elif mode == "PDF / News Q&A":
    st.header("📄 PDF / News Article Q&A with RAG ")

    source_type = st.radio(
        "Choose source type:",
        ["PDF document", "News article URL"],
        horizontal=True,
    )

    pdf_file = None
    article_url = ""

    if source_type == "PDF document":
        pdf_file = st.file_uploader("Upload a PDF document", type=["pdf"])
        if pdf_file is not None:
            st.success("✅ PDF uploaded! Now ask a question below.")
        else:
            st.info("Upload a PDF to start.")
    else:
        article_url = st.text_input("Paste news article URL (e.g., Yahoo Finance, Moneycontrol, etc.):")
        if article_url.strip():
            st.success("✅ URL received! Now ask a question about this article below.")
        else:
            st.info("Enter a valid article link to start.")

    query = st.text_input("Ask a question about this source:")

    if st.button("Get Answer"):
        if not query.strip():
            st.warning("Please enter a question.")
        elif source_type == "PDF document" and pdf_file is None:
            st.warning("Please upload a PDF first.")
        elif source_type == "News article URL" and not article_url.strip():
            st.warning("Please enter a news article URL first.")
        else:
            with st.spinner("Reading and thinking over your source..."):
                reply = answer_with_rag(
                    query,
                    pdf_file=pdf_file if source_type == "PDF document" else None,
                    article_url=article_url if source_type == "News article URL" else None,
                )
            st.success(reply)


# -------------------------------
# 4️⃣ Smart PDF / News Q&A (same RAG but for complex questions)
# -------------------------------
elif mode == "Smart PDF / News Q&A":
    st.header("🧠 Smart PDF / News Q&A (RAG + LLM)")

  

    source_type = st.radio(
        "Choose source type:",
        ["PDF document", "News article URL"],
        horizontal=True,
    )

    pdf_file = None
    article_url = ""

    if source_type == "PDF document":
        pdf_file = st.file_uploader("Upload a PDF document", type=["pdf"])
        if pdf_file is not None:
            st.success("✅ PDF uploaded! Now ask your detailed question.")
        else:
            st.info("Upload a PDF to start.")
    else:
        article_url = st.text_input("Paste news article URL:")
        if article_url.strip():
            st.success("✅ URL received! Now ask your detailed question.")
        else:
            st.info("Enter a valid article link to start.")

    query = st.text_input("Ask a complex question about this source:")

    if st.button("Get Smart Answer"):
        if not query.strip():
            st.warning("Please enter a question.")
        elif source_type == "PDF document" and pdf_file is None:
            st.warning("Please upload a PDF first.")
        elif source_type == "News article URL" and not article_url.strip():
            st.warning("Please enter a news article URL first.")
        else:
            with st.spinner("thinking"):
                smart_query = (
                    query
                    + "\n\nPlease reason step-by-step and keep it beginner-friendly."
                )
                reply = answer_with_rag(
                    smart_query,
                    pdf_file=pdf_file if source_type == "PDF document" else None,
                    article_url=article_url if source_type == "News article URL" else None,
                )
            st.success(reply)


# -------------------------------
# 5️⃣ Finance Calculators
# -------------------------------
elif mode == "Finance Calculators":
    st.header("🧮 Finance Calculators")

    calc_type = st.selectbox(
        "Choose a calculator:",
        ["Lumpsum Investment", "SIP Investment", "Loan EMI", "Retirement Corpus"],
    )

    if calc_type == "Lumpsum Investment":
        p = st.number_input("Initial Investment (₹)", min_value=1000.0, step=1000.0)
        r = st.number_input(
            "Annual Return Rate (%)", min_value=1.0, max_value=50.0, step=0.5
        )
        t = st.number_input("Time (years)", min_value=1, step=1)
        if st.button("Calculate"):
            fv = lumpsum_investment(p, r, t)
            st.success(f"Future Value: ₹{fv:,.2f}")

    elif calc_type == "SIP Investment":
        p = st.number_input("Monthly Investment (₹)", min_value=500.0, step=500.0)
        r = st.number_input(
            "Expected Annual Return (%)", min_value=1.0, max_value=50.0, step=0.5
        )
        t = st.number_input("Time (years)", min_value=1, step=1)
        if st.button("Calculate SIP"):
            fv = sip_investment(p, r, t)
            st.success(f"Future Value: ₹{fv:,.2f}")

    elif calc_type == "Loan EMI":
        p = st.number_input("Loan Amount (₹)", min_value=10000.0, step=10000.0)
        r = st.number_input(
            "Annual Interest Rate (%)", min_value=1.0, max_value=30.0, step=0.5
        )
        t = st.number_input("Tenure (years)", min_value=1, step=1)
        if st.button("Calculate EMI"):
            emi = loan_emi(p, r, t)
            st.success(f"Monthly EMI: ₹{emi:,.2f}")

    elif calc_type == "Retirement Corpus":
        exp = st.number_input(
            "Current Monthly Expense (₹)", min_value=1000.0, step=1000.0
        )
        infl = st.number_input(
            "Expected Inflation Rate (%)", min_value=1.0, max_value=15.0, step=0.5
        )
        yrs = st.number_input("Years until retirement", min_value=1, step=1)
        if st.button("Calculate Corpus"):
            corpus = retirement_corpus(exp, infl, yrs)
            st.success(f"Required Retirement Corpus: ₹{corpus:,.2f}")

