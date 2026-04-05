import re

import numpy as np
import pandas as pd


# Hardcoded approximate exchange rates to USD.
CURRENCY_TO_USD = {
    "USD": 1.0,
    "EUR": 1.09,
    "GBP": 1.28,
    "JPY": 0.0067,
    "CAD": 0.74,
    "AUD": 0.65,
    "CHF": 1.13,
    "CNY": 0.14,
    "INR": 0.012,
    "BRL": 0.17,
    "MXN": 0.049,
    "SGD": 0.74,
    "HKD": 0.13,
    "NZD": 0.60,
    "SEK": 0.094,
    "NOK": 0.092,
    "DKK": 0.146,
    "ZAR": 0.054,
    "AED": 0.272,
    "SAR": 0.267,
    "KRW": 0.00074,
    "TRY": 0.031,
    "PLN": 0.26,
    "CZK": 0.043,
    "HUF": 0.0027,
    "RUB": 0.011,
    "ILS": 0.27,
    "MYR": 0.21,
    "THB": 0.029,
    "PHP": 0.018,
    "IDR": 0.000061,
}

MULTI_CHAR_CURRENCY_MARKERS = {
    "US$": "USD",
    "C$": "CAD",
    "A$": "AUD",
    "NZ$": "NZD",
    "S$": "SGD",
    "HK$": "HKD",
}

SINGLE_CHAR_CURRENCY_MARKERS = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "₹": "INR",
    "₩": "KRW",
    "₽": "RUB",
    "₪": "ILS",
}


def _detect_currency_code(salary_str):
    upper_salary = salary_str.upper()

    for marker, code in MULTI_CHAR_CURRENCY_MARKERS.items():
        if marker in upper_salary:
            return code

    for code in CURRENCY_TO_USD:
        if re.search(rf"\b{code}\b", upper_salary):
            return code

    for marker, code in SINGLE_CHAR_CURRENCY_MARKERS.items():
        if marker in salary_str:
            return code

    return "USD"


def parse_salary(salary_str):
    """Extract salary values, convert them to USD, and annualize small amounts.

    Salaries tagged with supported currencies are converted to USD using the
    hardcoded exchange-rate table above. After conversion, values below 20,000
    are treated as monthly salaries and multiplied by 12. 
    
    Values at or above
    20,000 USD are assumed to already be annual salaries.


    """
    if pd.isna(salary_str):
        return None

    salary_str = str(salary_str).strip()
    if not salary_str or salary_str == "-1":
        return None

    salary_str = salary_str.replace("\u202f", " ").replace("–", "-").replace("—", "-")
    currency_code = _detect_currency_code(salary_str)
    exchange_rate = CURRENCY_TO_USD.get(currency_code, 1.0)
    is_hourly = "hour" in salary_str.lower() or "per hour" in salary_str.lower()

    matches = re.findall(r'[$€£]?\s*(\d[\d,]*(?:\.\d+)?)\s*([KMB]?)', salary_str, flags=re.IGNORECASE)
    if not matches:
        return None

    numbers = []
    for num_str, suffix in matches:
        try:
            num = float(num_str.replace(',', ''))
            suffix = suffix.upper()
            if suffix == 'K':
                num *= 1000
            elif suffix == 'M':
                num *= 1_000_000
            elif suffix == 'B':
                num *= 1_000_000_000
            elif is_hourly:
                num *= 2000

            num *= exchange_rate

            if num < 20_000:
                num *= 12

            numbers.append(num)
        except ValueError:
            continue

    if not numbers:
        return None

    return np.mean(numbers)