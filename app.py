import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import re
from chatbot import ask_local_gpt4all
from rag import answer_query, extract_text_from_pdf, chunk_text

from calculators import lumpsum_investment, sip_investment, loan_emi, retirement_corpus

# -------------------------------
# Streamlit UI setup
# -------------------------------
st.set_page_config(
    page_title="Investobot Prototype",
    layout="wide",
    page_icon="💹"
)

# Custom CSS
st.markdown("""
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
""", unsafe_allow_html=True)

st.sidebar.title("💹 Investobot")
mode = st.sidebar.radio(
    "Choose a feature:",
    ["Chatbot", "Stock Data Lookup", "PDF Q&A", "Smart PDF Q&A", "Finance Calculators"]
)

# -------------------------------
# Chatbot Mode
# -------------------------------
if mode == "Chatbot":
    st.header("💬 Finance Chatbot")
    user_input = st.text_input("Ask me anything about finance or investing:")
    if st.button("Ask"):
        if user_input.strip():
            with st.spinner("Thinking..."):
                reply = ask_local_gpt4all(user_input)
            st.success(reply)
        else:
            st.warning("Please type a question.")

# -------------------------------
# Stock Data Lookup Mode
# -------------------------------
elif mode == "Stock Data Lookup":
    st.header("📊 Stock Data Lookup")

    ticker = st.text_input("Enter stock ticker (e.g., AAPL, TSLA, RELIANCE.BO):")
    option = st.selectbox("Select data type:", ["Current Price", "Historical Prices", "Dividends", "Market Info"])

    if st.button("Get Data"):
        if ticker.strip():
            try:
                stock = yf.Ticker(ticker)

                if option == "Current Price":
                    price = stock.info.get("currentPrice", None)
                    if price:
                        st.metric(label=f"{ticker.upper()} Current Price", value=f"${price:.2f}")
                    else:
                        st.warning("Price data not available.")

                elif option == "Historical Prices":
                    period = st.selectbox("Select period:", ["1mo", "3mo", "6mo", "1y", "5y"])
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
                    st.metric("52 Week High", info.get("fiftyTwoWeekHigh", "N/A"))
                    st.metric("52 Week Low", info.get("fiftyTwoWeekLow", "N/A"))
                    st.metric("Volume", info.get("volume", "N/A"))
                    st.metric("Market Cap", info.get("marketCap", "N/A"))
                    st.metric("PE Ratio", info.get("trailingPE", "N/A"))

            except Exception as e:
                st.error(f"Error fetching stock: {e}")
        else:
            st.warning("Please enter a ticker symbol.")

# -------------------------------
# PDF Q&A (Direct Retrieval)
# -------------------------------
elif mode == "PDF Q&A":
    st.header("📄 PDF Q&A with RAG")
    pdf_file = st.file_uploader("Upload a PDF document", type=["pdf"])

    if pdf_file:
        st.success("✅ PDF uploaded! Now ask questions below.")
        query = st.text_input("Ask a question about the document:")

        if st.button("Get Answer"):
            if query.strip():
                with st.spinner("Searching inside PDF..."):
                    reply = answer_query(query, pdf_file)
                st.success(reply)
            else:
                st.warning("Please enter a question.")

# -------------------------------
# Smart PDF Q&A (RAG + GPT)
# -------------------------------
elif mode == "Smart PDF Q&A":
    st.header("🧠 Smart PDF Q&A (RAG + GPT)")
    pdf_file = st.file_uploader("Upload a PDF document", type=["pdf"])

    if pdf_file:
        st.success("✅ PDF uploaded! Ask with GPT-powered answers.")
        query = st.text_input("Ask a question about the document:")

        if st.button("Get Smart Answer"):
            if query.strip():
                with st.spinner("Thinking with RAG + GPT..."):
                    # Step 1: Extract + chunk + embed
                    text = extract_text_from_pdf(pdf_file)
                    chunks = chunk_text(text)
                    embeddings = embed_chunks(chunks)

                    # Step 2: Retrieve context
                    top_chunks = retrieve_relevant_chunks(query, chunks, embeddings)
                    context = " ".join(top_chunks)

                    # Step 3: Build prompt for GPT
                    prompt = f"Use the following context to answer:\n\n{context}\n\nQuestion: {query}\n\nAnswer in a clear and concise way."

                    # Step 4: Ask GPT4All
                    reply = ask_local_gpt4all(prompt)

                st.success(reply)
            else:
                st.warning("Please enter a question.")


# -------------------------------
# Finance Calculators
# -------------------------------
elif mode == "Finance Calculators":
    st.header("🧮 Finance Calculators")

    calc_type = st.selectbox(
        "Choose a calculator:",
        ["Lumpsum Investment", "SIP Investment", "Loan EMI", "Retirement Corpus"]
    )

    if calc_type == "Lumpsum Investment":
        p = st.number_input("Initial Investment (₹)", min_value=1000.0, step=1000.0)
        r = st.number_input("Annual Return Rate (%)", min_value=1.0, max_value=50.0, step=0.5)
        t = st.number_input("Time (years)", min_value=1, step=1)
        if st.button("Calculate"):
            st.success(f"Future Value: ₹{lumpsum_investment(p, r, t):,.2f}")

    elif calc_type == "SIP Investment":
        p = st.number_input("Monthly Investment (₹)", min_value=500.0, step=500.0)
        r = st.number_input("Expected Annual Return (%)", min_value=1.0, max_value=50.0, step=0.5)
        t = st.number_input("Time (years)", min_value=1, step=1)
        if st.button("Calculate SIP"):
            st.success(f"Future Value: ₹{sip_investment(p, r, t):,.2f}")

    elif calc_type == "Loan EMI":
        p = st.number_input("Loan Amount (₹)", min_value=10000.0, step=10000.0)
        r = st.number_input("Annual Interest Rate (%)", min_value=1.0, max_value=30.0, step=0.5)
        t = st.number_input("Tenure (years)", min_value=1, step=1)
        if st.button("Calculate EMI"):
            st.success(f"Monthly EMI: ₹{loan_emi(p, r, t):,.2f}")

    elif calc_type == "Retirement Corpus":
        exp = st.number_input("Current Monthly Expense (₹)", min_value=1000.0, step=1000.0)
        infl = st.number_input("Expected Inflation Rate (%)", min_value=1.0, max_value=15.0, step=0.5)
        yrs = st.number_input("Years until retirement", min_value=1, step=1)
        if st.button("Calculate Corpus"):
            st.success(f"Required Retirement Corpus: ₹{retirement_corpus(exp, infl, yrs):,.2f}")
