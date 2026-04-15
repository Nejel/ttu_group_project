#############################
#     LinkedIn Scraper      #
#---------------------------#
#         Group 15          #
#############################



# ==========================
# Config
# ==========================

# Where to save the scraped data
filename = 'data/our_own_dataset/jobs_all_US_non_data_science_10000.csv'
# !_! Do not forget to change filename before running, otherwise will be overwritten !_!

searchDepth = 1000       # how many jobs to scrape in 
save_step = 50           # save the data to CSV every 50 jobs to avoid losing progress 

# USA search cities and states configuration 
citySearch = [
            #   ("Dallas", "TX"), 
            ("Austin", "TX"),
            ("Los Angeles", "CA"), ("Chicago", "IL"), ("New York City", "NY"), ("Miami", "FL")
            ]

# European search cities and states configuration
# citySearch = [
    # ("London", "United Kingdom"), 
    # ("Paris", "France"), ("Berlin", "Germany"), 
    # ("Amsterdam", "Netherlands"), ("Dublin", "Ireland"),("Barcelona", "Spain") ]


# Additional keyword set focused on title families that were still under-covered
# in experiment_8 TITLE_FAMILY_PATTERNS.

jobKeywords = [
    #     # Core data science / analytics roles  
    #     "data scientist",
    #     "senior data scientist",
    #     "junior data scientist",
    #     "data analyst",
    #     "business analyst",
    #     "business intelligence analyst",
    #     "bi analyst",
    #     "machine learning engineer",
    #     "ml engineer",
    #     "ai engineer",
    #     "applied scientist",
    #     "research scientist",
    #     "data engineer",
    #     "senior data engineer",
    #     "etl developer",
    #     "analytics engineer",
    #     "big data engineer",
    #     "decision scientist",
    #     "quantitative analyst",
    #     "statistical analyst",
    #     "predictive analyst",
    #     "nlp engineer",
    #     "computer vision engineer",
    #     "deep learning engineer",
    #     "ai/ml engineer",
    #     "data science engineer",
    #     "data architect",
    #     "ml scientist",
    #     "operations research analyst",


    # # Non direct DS jobs, but potentially related 
    # # Senior leadership / management
    # # Batch 1 starts here

    "vice president data",
    "vice president analytics",
    "vp data",
    "vp analytics",
    "director data science",
    "director analytics",
    "director machine learning",
    "data science manager",
    "analytics manager",
    "head of data",
    "head of analytics", # Dallas, TX has a 550 at that point 
    "chief data officer",

    # # Early-career / graduate pipeline
    "data science intern",
    "machine learning intern",
    "analytics intern",
    "data engineer intern", # Dallas, TX has a 850 at that point
    "graduate data scientist",
    "graduate data engineer",
    "new grad data scientist",
    "co-op data science", # Dallas, TX has a 1000 at that point

    # Consultant / architect / software 
    # Batch 2 starts here 
    "data consultant",
    "analytics consultant",
    "machine learning consultant",
    "solutions architect",
    "data architect",
    "software engineer machine learning",
    "data software engineer", # Dallas, TX has a 350 (Batch 2) at that point

    # NLP / LLM / GenAI
    "llm engineer",
    "llm scientist", # Dallas, TX has a 450 (Batch 2) at that point
    "language model engineer",
    "language model scientist",
    "generative ai engineer",
    "generative ai scientist",
    "prompt engineer",
    "natural language processing engineer",
    "natural language processing scientist",

    # MLOps / deployment
    "mlops engineer", # Dallas, TX has a 750 (Batch 2) at that point
    "machine learning ops engineer",
    "machine learning operations engineer",
    "model deployment engineer",
    "model serving engineer",

    # Visualization / reporting
    "power bi developer",
    "tableau developer",
    "report developer",
    "reporting developer",
    "dashboard developer",
    "visualization engineer",

    # Scientist / specialist / admin
    "associate scientist",
    "bioinformatics scientist",
    "data specialist",
    "analytics specialist",
    "database administrator",
    "database admin",
    "sql dba",
    "database engineer",

    # Extra data-engineering variants
    "data platform engineer",
    "data warehouse engineer",
    "pipeline engineer",
    "data developer",
    "hadoop developer"
]



# ==========================
# Libraries
# ==========================

import requests as r
from bs4 import BeautifulSoup
import csv
import time
from pathlib import Path



# ==========================
# Functions
# ==========================

def getLinked(cityQuery, jobQuery, howMany, saveEvery=None):
    allJobs = []
    saveEvery = saveEvery if saveEvery and saveEvery > 0 else None
    
    for city, state in cityQuery:
        for job in jobQuery:
            print('Searching LinkedIn: ' + city + ', ' + state + ' | ' + job)
            
            results = linkedQuery(city, state, job)
            
            for listing in results:
                if len(allJobs) >= howMany:
                    break
                allJobs.append(listing)
                if saveEvery and len(allJobs) % saveEvery == 0:
                    writeCSV(allJobs, is_checkpoint=True)
            
            time.sleep(2)
            
            if len(allJobs) >= howMany:
                break
    
    return allJobs


def linkedQuery(city, state, job):
    URL = 'https://www.linkedin.com/jobs/search/'
    
    params = {
        "keywords": job,
        "location": city + ', ' + state
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    res = r.get(URL, params=params, headers=headers)
    soup = BeautifulSoup(res.content, 'html.parser')
    listings = soup.find_all('div', attrs={'class': 'base-card'})
    
    jobs = []
    
    for listing in listings:
        title    = listing.find('h3', attrs={'class': 'base-search-card__title'})
        company  = listing.find('h4', attrs={'class': 'base-search-card__subtitle'})
        location = listing.find('span', attrs={'class': 'job-search-card__location'})
        link     = listing.find('a', attrs={'class': 'base-card__full-link'})
        
        description = 'N/A'
        salary      = 'N/A'
        workType    = 'N/A'

        if link:
            jobRes  = r.get(link['href'], headers=headers)
            jobSoup = BeautifulSoup(jobRes.content, 'html.parser')

            # Description
            descTag = jobSoup.find('div', attrs={'class': 'show-more-less-html__markup'})
            if descTag:
                description = descTag.get_text(strip=True)

            # Salary
            salaryTag = jobSoup.find('div', attrs={'class': 'salary compensation__salary'})
            if salaryTag:
                salary = salaryTag.get_text(strip=True)

            # Work Type (Remote / Hybrid / On-site)
            criteriaItems = jobSoup.find_all('li', attrs={'class': 'description__job-criteria-item'})
            for item in criteriaItems:
                header = item.find('h3', attrs={'class': 'description__job-criteria-subheader'})
                value  = item.find('span', attrs={'class': 'description__job-criteria-text'})
                if header and value:
                    if 'workplace' in header.text.strip().lower() or 'remote' in header.text.strip().lower():
                        workType = value.text.strip()

            time.sleep(1)

        jobs.append({
            'title':       title.text.strip()    if title    else 'N/A',
            'company':     company.text.strip()  if company  else 'N/A',
            'location':    location.text.strip() if location else 'N/A',
            'link':        link['href']          if link     else 'N/A',
            'salary':      salary,
            'workType':    workType,
            'description': description,
            'source':      'LinkedIn'
        })
    
    return jobs


def writeCSV(jobs, is_checkpoint=False):
    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(['title', 'company', 'location', 'salary', 'workType', 'description', 'link', 'source'])
        
        for job in jobs:
            writer.writerow([job['title'], job['company'], job['location'], job['salary'], job['workType'], job['description'], job['link'], job['source']])
    
    if is_checkpoint:
        print(f'[CHECKPOINT] Saved {len(jobs)} jobs to {output_path}')
    else:
        print(f'Exported {len(jobs)} jobs to {output_path}')



# ==========================
# Main program
# ==========================
def main():
    print("[START] Scraping")
    jobs = getLinked(citySearch, jobKeywords, searchDepth, save_step)
    print("[COMPLETE] Scraping")

    writeCSV(jobs)



# ==========================
# Execution
# ==========================
if __name__ == '__main__':
    main()
