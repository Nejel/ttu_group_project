#############################
#     LinkedIn Scraper      #
#---------------------------#
#         Group 15          #
#############################
# ==========================
# Config
# ==========================
citySearch = [("Dallas", "TX"), ("Los Angeles", "CA"), ("Chicago", "IL"), ("New York City", "NY"), ("Miami", "FL")]
jobKeywords = ["engineer", "analyst", "developer"]
searchDepth = 100
source = ["LinkedIn","builtIn","Glassdoor","Indeed"] #LinkedIn, builtIn, Glassdoor, Indeed
# ==========================
# Libraries
# ==========================
import requests as r
from bs4 import BeautifulSoup
import csv
import time
# ==========================
# Functions
# ==========================
def getLinked(cityQuery, jobQuery, howMany):
    allJobs = []
    
    for city, state in cityQuery:
        for job in jobQuery:
            print('Searching LinkedIn: ' + city + ', ' + state + ' | ' + job)
            
            results = linkedQuery(city, state, job)
            
            for listing in results:
                if len(allJobs) >= howMany:
                    break
                allJobs.append(listing)
            
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

def writeCSV(jobs):
    with open('jobs.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(['title', 'company', 'location', 'salary', 'workType', 'description', 'link', 'source'])
        
        for job in jobs:
            writer.writerow([job['title'], job['company'], job['location'], job['salary'], job['workType'], job['description'], job['link'], job['source']])
    
    print('Exported ' + str(len(jobs)) + ' jobs to jobs.csv')
# ==========================
# Main program
# ==========================
def main():
    print("[START] Scraping")
    jobs = getLinked(citySearch, jobKeywords, searchDepth)
    print("[COMPLETE] Scraping")
    
    writeCSV(jobs)
# ==========================
# Execution
# ==========================
if __name__ == '__main__':
    main()
