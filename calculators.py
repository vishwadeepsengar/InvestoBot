import math

# -------------------------------
# Lumpsum Investment Calculator
# -------------------------------
def lumpsum_investment(principal, annual_rate, years):
    """
    Formula: A = P * (1 + r/n)^(n*t)
    Assuming annual compounding (n = 1).
    """
    amount = principal * ((1 + annual_rate/100) ** years)
    return round(amount, 2)


# -------------------------------
# SIP Investment Calculator
# -------------------------------
def sip_investment(monthly_investment, annual_rate, years):
    """
    Formula: Future Value = P * [((1+r)^n - 1) / r] * (1+r)
    Where:
      P = monthly investment
      r = monthly rate of return
      n = number of months
    """
    n = years * 12
    r = annual_rate / 100 / 12
    future_value = monthly_investment * (((1 + r)**n - 1) / r) * (1 + r)
    return round(future_value, 2)


# -------------------------------
# Loan EMI Calculator
# -------------------------------
def loan_emi(principal, annual_rate, years):
    """
    Formula: EMI = [P * r * (1+r)^n] / [(1+r)^n - 1]
    Where:
      P = loan amount
      r = monthly interest rate
      n = number of months
    """
    n = years * 12
    r = annual_rate / 100 / 12
    emi = (principal * r * (1 + r)**n) / ((1 + r)**n - 1)
    return round(emi, 2)


# -------------------------------
# Retirement Corpus Calculator (basic)
# -------------------------------
def retirement_corpus(monthly_expense, inflation_rate, years_to_retire):
    """
    Calculates how much corpus you will need at retirement
    assuming expenses grow with inflation.
    """
    inflated_expense = monthly_expense * ((1 + inflation_rate/100) ** years_to_retire)
    annual_expense = inflated_expense * 12
    # Assuming corpus = 25x annual expenses (4% withdrawal rule)
    corpus = annual_expense * 25
    return round(corpus, 2)
