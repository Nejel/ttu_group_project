# ttu_group_project


## Expected findings

* (1) Core skills such as Python, SQL, and statistics will have the highest frequency across job postings, indicating baseline requirements for data science roles. 
* (2) Job postings requiring advanced skill bundles (e.g., machine learning, cloud platforms, big data tools) will be associated with higher salary ranges. 
* (3) Remote positions will more frequently require specialized and self-directed skills compared to non-remote roles, which will emphasize broader skill sets. 
* (4) Job postings in technology and finance industries will exhibit higher average salaries and more advanced skill requirements than other sectors. 
* (5) Company-level attributes (e.g., size, rating, and revenue) will positively correlate with offered salary ranges in job listings. 
* (6) Remote data science postings will skew more senior and include fewer entry-level roles than non-remote postings.

## Project log and outcomes 

Researching the expected findins 1 we have started from collecting the data. The most of datasets available on the internet shows the lack of one of the fields required to make the whole project done: some have no precise job description, some have no payrange, some are just outdated. Collecting of the good data is one of the main challenges of this project. See details in Datasets part of this file. 


### Experiment 1

Experiment 1 focuses on Expected Finding 1 and its related topics. We began by analyzing the most commonly required skills in data science job postings across the U.S. and European markets. The initial results indicated that machine learning is the most frequently mentioned skill, which appeared somewhat suspicious.

To investigate this, we explored whether mentions of “machine learning” might sometimes be overstated—i.e., included for popularity rather than reflecting actual job requirements. Our first approach was to test this hypothesis using frequency-based analysis.

The results seemed too strong to be realistic: 74.5% of job descriptions mentioning “machine learning” did not reference any specific machine learning tools or related skills. However, upon closer inspection, it became clear that this method had significant limitations. Many job descriptions imply machine learning responsibilities through context or paraphrased language that simple keyword-based methods fail to capture.

To address this issue, we applied LLM-based text classification for deeper contextual understanding. After running batch LLM classification, we found that approximately 89% of job postings that mention “machine learning” genuinely require it (or supposed to). The remaining 11% include the term without providing additional context or specifying related skills, which may indicate an “overhyped” or superficial mention.

Details and all the explanations are available in the file: [`experiment_1.ipynb`](./experiment_1.ipynb)



### Experiment 6

Experiment 6 focuses on whether remote data science postings are equally accessible across experience levels. Using the unified dataset, we inferred seniority from `job_title` and identified remote roles from `location`.

The results show that remote postings are much less entry-level friendly than non-remote postings. Only about 0.3% of remote roles were classified as entry-level, compared with about 2.9% of non-remote roles, while remote roles were substantially more likely to be senior-level. This difference was statistically significant, supporting the idea that remote-only job search filters push candidates toward more experienced roles.

Details and all the explanations are available in the file: [`experiment_6.ipynb`](./experiment_6.ipynb)

## Datasets 

**Dataset 1**: GlassDoor Job Postings 2023 

>Source: https://www.kaggle.com/datasets/rrkcoder/glassdoor-data-science-job-listings
>
>Records amount: 1500 data science related jobs collected in September 2023

**Dataset 2**: DataScience Job Postings 2025

> Source: https://www.kaggle.com/datasets/elahehgolrokh/data-science-job-postings-with-salaries-2025
> 
> Records amount: 994 data science related jobs collected in 2025 


**Dataset 3**: DataScience Job Postings April 2026

> Source: Collected by authors during the project using web-scraper (internal tool)
> 
> Records amount: 1000 data science related jobs in USA and Europe, posted in April 2026

## Tools

**Internal Tool 1**: Job Postings parser to parse LinkedIn Job Postings

**External Tool 1**: LLM qwen/qwen3-4b-thinking-2507 running locally using LM Studio and requesting via API calls.