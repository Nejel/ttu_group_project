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


def extract_skill_frequencies(job_descriptions, skill_patterns):
    """Extract skill frequencies from job descriptions using regex patterns.
    
    Args:
        job_descriptions: pandas Series of job description strings
        skill_patterns: dict mapping skill names to regex patterns
        
    Returns:
        pandas DataFrame with columns: Skill, Mention Count, Percentage of Postings
    """
    posting_count = len(job_descriptions)
    frequency_rows = []
    
    for skill, pattern in skill_patterns.items():
        mention_count = job_descriptions.str.contains(pattern, case=False, regex=True).sum()
        frequency_rows.append({
            "Skill": skill,
            "Mention Count": int(mention_count),
            "Percentage of Postings": round(mention_count / posting_count * 100, 2),
        })
    
    skill_frequency = (
        pd.DataFrame(frequency_rows)
        .sort_values(by="Mention Count", ascending=False)
        .reset_index(drop=True)
    )
    
    return skill_frequency


# Skill patterns for data science job postings
SKILL_PATTERNS = {
    # Core programming / query
    "Python": r"\bpython\b",
    "R": r"(?<![A-Za-z0-9])r(?![A-Za-z0-9])|\br[- ]studio\b|\btidyverse\b",
    "SQL": r"\bsql\b|\bpostgresql\b|\bmysql\b|\btsql\b|\bt-sql\b|\bpl/sql\b",
    "SAS": r"\bsas\b",
    "Excel": r"\bexcel\b|\bmicrosoft excel\b|\bspreadsheets?\b",

    # Statistics / math / analytics
    "Statistics": r"\bstatistic(?:s|al)?\b|\bprobability\b|\bhypothesis testing\b|\bstatistical modeling\b",
    "A/B Testing": r"\ba/?b testing\b|\bexperiment(?:ation|s)?\b|\bmultivariate testing\b",
    "Regression": r"\bregression\b|\blinear regression\b|\blogistic regression\b",
    "Time Series": r"\btime series\b|\bforecasting\b|\barima\b|\bprophet\b",
    "Optimization": r"\boptimization\b|\blinear programming\b|\bconvex optimization\b",

    # ML / AI
    "Machine Learning": r"\bmachine learning\b|\bml\b",
    "Deep Learning": r"\bdeep learning\b|\bneural networks?\b|\bcnn\b|\brnn\b|\blstm\b|\btransformers?\b",
    "NLP": r"\bnlp\b|\bnatural language processing\b|\btext mining\b|\btext analytics\b",
    "Computer Vision": r"\bcomputer vision\b|\bimage processing\b|\bobject detection\b",
    "Generative AI": r"\bgenerative ai\b|\bgenai\b|\bllms?\b|\blarge language models?\b|\bfoundation models?\b",
    "Reinforcement Learning": r"\breinforcement learning\b|\brl\b",

    # ML libraries
    "Scikit-learn": r"\bscikit[- ]learn\b|\bsklearn\b",
    "TensorFlow": r"\btensorflow\b",
    "PyTorch": r"\bpytorch\b",
    "Keras": r"\bkeras\b",
    "XGBoost": r"\bxgboost\b",
    "LightGBM": r"\blightgbm\b",
    "CatBoost": r"\bcatboost\b",

    # Data manipulation / notebooks
    "Pandas": r"\bpandas\b",
    "NumPy": r"\bnumpy\b",
    "SciPy": r"\bscipy\b",
    "Jupyter": r"\bjupyter\b|\bjupyter notebook\b|\bnotebooks?\b",

    # Visualization / BI
    "Tableau": r"\btableau\b",
    "Power BI": r"\bpower bi\b|\bpowerbi\b",
    "Looker": r"\blooker\b|\blooker studio\b",
    "Matplotlib": r"\bmatplotlib\b",
    "Seaborn": r"\bseaborn\b",
    "Plotly": r"\bplotly\b",
    "Data Visualization": r"\bdata visualization\b|\bdata visualisation\b|\bdashboard(?:s)?\b",

    # Big data / distributed
    "Spark": r"\bspark\b|\bapache spark\b|\bpyspark\b",
    "Hadoop": r"\bhadoop\b",
    "Hive": r"\bhive\b",
    "Kafka": r"\bkafka\b|\bapache kafka\b",
    "Databricks": r"\bdatabricks\b",

    # Data engineering / orchestration
    "ETL": r"\betl\b|\belt\b|\bdata pipelines?\b",
    "Airflow": r"\bairflow\b|\bapache airflow\b",
    "dbt": r"\bdbt\b",
    "Snowflake": r"\bsnowflake\b",
    "Redshift": r"\bredshift\b",
    "BigQuery": r"\bbigquery\b|\bgoogle bigquery\b",

    # Cloud
    "AWS": r"\baws\b|\bamazon web services\b",
    "Azure": r"\bazure\b|\bmicrosoft azure\b",
    "GCP": r"\bgcp\b|\bgoogle cloud\b|\bgoogle cloud platform\b",

    # Databases / storage
    "NoSQL": r"\bnosql\b|\bmongodb\b|\bcassandra\b|\bdynamodb\b",
    "MongoDB": r"\bmongodb\b",
    "PostgreSQL": r"\bpostgresql\b|\bpostgres\b",
    "MySQL": r"\bmysql\b",

    # Software / deployment
    "Git": r"\bgit\b|\bgithub\b|\bgitlab\b",
    "Docker": r"\bdocker\b",
    "Kubernetes": r"\bkubernetes\b|\bk8s\b",
    "Linux": r"\blinux\b",
    "API": r"\bapi(?:s)?\b|\brest api(?:s)?\b",

    # Business / product-oriented analytics
    "Business Intelligence": r"\bbusiness intelligence\b|\bbi\b",
    "Data Mining": r"\bdata mining\b",
    "Feature Engineering": r"\bfeature engineering\b",
    "Model Deployment": r"\bmodel deployment\b|\bmodel serving\b|\bmachine learning ops\b|\bmlops\b",
    "Data Warehousing": r"\bdata warehouse\b|\bdata warehousing\b",

    # Common DS adjacent tools
    "PowerPoint": r"\bpowerpoint\b|\bmicrosoft powerpoint\b",
    "Communication": r"\bcommunication skills?\b|\bpresentation skills?\b|\bstakeholder management\b",
}


def extract_skill_lists(job_descriptions, skill_patterns):
    """Extract lists of skills present in each job description.
    
    Args:
        job_descriptions: pandas Series of job description strings
        skill_patterns: dict mapping skill names to regex patterns
        
    Returns:
        list of lists: each sublist contains skills found in that job description
    """
    skill_lists = []
    for desc in job_descriptions:
        skills_present = []
        for skill, pattern in skill_patterns.items():
            if re.search(pattern, desc, re.IGNORECASE):
                skills_present.append(skill)
        skill_lists.append(skills_present)
    return skill_lists