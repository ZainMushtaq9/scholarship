import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def normalize_title(title):
    if not title:
        return ""
    title = title.lower()
    title = re.sub(r'[^a-z0-9\s]', '', title)
    fillers = ['urgently', 'hiring', 'needed', 'required', 'remote', 'hybrid', 'onsite']
    for filler in fillers:
        title = title.replace(filler, '')
    return clean_text(title)

def is_official_link(url):
    if not url:
        return False
    official_domains = ['.gov.pk', '.edu', '.edu.pk']
    return any(domain in url.lower() for domain in official_domains) or 'careers' in url.lower()

def safe_request(url, timeout=15):
    """Make a safe HTTP request with error handling."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return resp
    except Exception as e:
        print(f"  [SKIP] Failed to fetch {url}: {e}")
        return None

# ============================================================
# Individual Scraper Functions for Each Portal
# ============================================================

def scrape_rozee(max_jobs=10):
    """Scrape jobs from Rozee.pk"""
    print("Scraping Rozee.pk...")
    jobs = []
    resp = safe_request("https://www.rozee.pk/job/jsearch/q/all/fc/pak")
    if not resp:
        return jobs
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = soup.select('.job, .jlist, a[href*="/job/detail/"]')
    for item in listings[:max_jobs]:
        title_tag = item.select_one('h3, h2, .jtitle, .job-title') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://www.rozee.pk' + link
        if title:
            jobs.append(_build_job(title, link, 'Rozee.pk'))
    return jobs

def scrape_njp(max_jobs=10):
    """Scrape jobs from National Job Portal (njp.gov.pk)"""
    print("Scraping NJP.gov.pk...")
    jobs = []
    resp = safe_request("https://www.njp.gov.pk/")
    if not resp:
        return jobs
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = soup.select('a[href*="job"], .job-listing, tr')
    for item in listings[:max_jobs]:
        title = clean_text(item.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://www.njp.gov.pk' + link
        if title and len(title) > 5 and len(title) < 200:
            jobs.append(_build_job(title, link, 'NJP.gov.pk'))
    return jobs

def scrape_indeed_pk(max_jobs=10):
    """Scrape jobs from Indeed Pakistan"""
    print("Scraping Indeed Pakistan...")
    jobs = []
    resp = safe_request("https://pk.indeed.com/jobs?q=&l=Pakistan")
    if not resp:
        return jobs
    soup = BeautifulSoup(resp.text, 'html.parser')
    cards = soup.select('.job_seen_beacon, .jobsearch-ResultsList .result, div[data-jk]')
    for card in cards[:max_jobs]:
        title_tag = card.select_one('h2 a, .jobTitle a, a[data-jk]')
        company_tag = card.select_one('.company, .companyName, [data-testid="company-name"]')
        location_tag = card.select_one('.companyLocation, [data-testid="text-location"]')
        if title_tag:
            title = clean_text(title_tag.get_text())
            link = title_tag.get('href', '') or ''
            if link and not link.startswith('http'):
                link = 'https://pk.indeed.com' + link
            company = clean_text(company_tag.get_text()) if company_tag else 'Unknown'
            location = clean_text(location_tag.get_text()) if location_tag else 'Pakistan'
            jobs.append(_build_job(title, link, 'Indeed PK', company=company, location=location))
    return jobs

def scrape_mustakbil(max_jobs=10):
    """Scrape jobs from Mustakbil.com"""
    print("Scraping Mustakbil.com...")
    jobs = []
    resp = safe_request("https://www.mustakbil.com/jobs")
    if not resp:
        return jobs
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = soup.select('.job-listing, .job-item, a[href*="/job/"]')
    for item in listings[:max_jobs]:
        title_tag = item.select_one('h2, h3, .job-title') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://www.mustakbil.com' + link
        if title and len(title) > 3:
            jobs.append(_build_job(title, link, 'Mustakbil'))
    return jobs

def scrape_brightspyre(max_jobs=10):
    """Scrape jobs from BrightSpyre"""
    print("Scraping BrightSpyre...")
    jobs = []
    resp = safe_request("https://www.brightspyre.com/jobs")
    if not resp:
        return jobs
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = soup.select('.job-listing, .listing-item, a[href*="jobs"]')
    for item in listings[:max_jobs]:
        title_tag = item.select_one('h2, h3, .title') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://www.brightspyre.com' + link
        if title and len(title) > 3:
            jobs.append(_build_job(title, link, 'BrightSpyre'))
    return jobs

def scrape_jobz_pk(max_jobs=10):
    """Scrape jobs from Jobz.pk"""
    print("Scraping Jobz.pk...")
    jobs = []
    resp = safe_request("https://www.jobz.pk/jobs/")
    if not resp:
        return jobs
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = soup.select('a[href*="job"], .post, article, .entry-title')
    for item in listings[:max_jobs]:
        title_tag = item.select_one('h2, h3, .entry-title') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://www.jobz.pk' + link
        if title and len(title) > 5 and len(title) < 200:
            jobs.append(_build_job(title, link, 'Jobz.pk'))
    return jobs

def scrape_careerokay(max_jobs=10):
    """Scrape jobs from CareerOkay.com"""
    print("Scraping CareerOkay.com...")
    jobs = []
    resp = safe_request("https://www.careerokay.com/jobs")
    if not resp:
        return jobs
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = soup.select('.job-listing, .job-item, a[href*="job"]')
    for item in listings[:max_jobs]:
        title_tag = item.select_one('h2, h3, .title') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://www.careerokay.com' + link
        if title and len(title) > 3:
            jobs.append(_build_job(title, link, 'CareerOkay'))
    return jobs

def scrape_ilmkidunya(max_jobs=10):
    """Scrape jobs from Ilmkidunya.com"""
    print("Scraping Ilmkidunya.com...")
    jobs = []
    resp = safe_request("https://www.ilmkidunya.com/jobs/")
    if not resp:
        return jobs
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = soup.select('a[href*="jobs"], .job-item, article')
    for item in listings[:max_jobs]:
        title_tag = item.select_one('h2, h3, .title') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://www.ilmkidunya.com' + link
        if title and len(title) > 5 and len(title) < 200:
            jobs.append(_build_job(title, link, 'Ilmkidunya'))
    return jobs

def scrape_paperjobz(max_jobs=10):
    """Scrape jobs from PaperJobz.com"""
    print("Scraping PaperJobz.com...")
    jobs = []
    resp = safe_request("https://www.paperjobz.com/")
    if not resp:
        return jobs
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = soup.select('article, .post, a[href*="jobs"]')
    for item in listings[:max_jobs]:
        title_tag = item.select_one('h2, h3, .entry-title, .title') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://www.paperjobz.com' + link
        if title and len(title) > 5 and len(title) < 200:
            jobs.append(_build_job(title, link, 'PaperJobz'))
    return jobs

def scrape_bayt_pk(max_jobs=10):
    """Scrape from Bayt.com Pakistan"""
    print("Scraping Bayt.com Pakistan...")
    jobs = []
    resp = safe_request("https://www.bayt.com/en/pakistan/jobs/")
    if not resp:
        return jobs
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = soup.select('a[href*="/job/"], .job-item, li[data-job-id]')
    for item in listings[:max_jobs]:
        title_tag = item.select_one('h2, h3, .jb-title, .title') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://www.bayt.com' + link
        if title and len(title) > 3:
            jobs.append(_build_job(title, link, 'Bayt.com'))
    return jobs

def scrape_punjab_jobs(max_jobs=10):
    """Scrape from Punjab Jobs Portal"""
    print("Scraping Punjab Jobs Portal...")
    jobs = []
    resp = safe_request("https://jobs.punjab.gov.pk/new_recruit/jobs")
    if not resp:
        return jobs
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = soup.select('tr, .job-row, a[href*="job"]')
    for item in listings[:max_jobs]:
        title = clean_text(item.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://jobs.punjab.gov.pk' + link
        if title and len(title) > 5 and len(title) < 200 and not title.startswith('Sr'):
            jobs.append(_build_job(title, link, 'Punjab Jobs Portal'))
    return jobs

# ============================================================
# Helper function to build a standard job dict
# ============================================================

def _build_job(title, link, source, company='Unknown', location='Pakistan', salary='Not Specified', description=''):
    return {
        'title': title,
        'normalized_title': normalize_title(title),
        'company': company,
        'location': location,
        'salary': salary,
        'description': description or title,
        'apply_links': json.dumps([link] if is_official_link(link) else [{"url": link, "note": "Source Information Only"}]),
        'source': source,
        'date_posted': datetime.now()
    }

# ============================================================
# Main scrape function — calls all scrapers
# ============================================================

ALL_SCRAPERS = [
    scrape_rozee,
    scrape_njp,
    scrape_indeed_pk,
    scrape_mustakbil,
    scrape_brightspyre,
    scrape_jobz_pk,
    scrape_careerokay,
    scrape_ilmkidunya,
    scrape_paperjobz,
    scrape_bayt_pk,
    scrape_punjab_jobs,
]

def scrape_sample_jobs():
    """Run all scrapers and combine results."""
    all_jobs = []
    for scraper_fn in ALL_SCRAPERS:
        try:
            jobs = scraper_fn(max_jobs=10)
            all_jobs.extend(jobs)
            print(f"  -> Got {len(jobs)} from {scraper_fn.__name__}")
        except Exception as e:
            print(f"  [ERROR] {scraper_fn.__name__}: {e}")
        time.sleep(1)  # Be polite, 1 second delay between sites
    
    print(f"\nTotal jobs scraped: {len(all_jobs)}")
    return all_jobs

if __name__ == '__main__':
    jobs = scrape_sample_jobs()
    print(f"\nScraped {len(jobs)} total jobs.")
    for j in jobs[:5]:
        print(f"  - {j['title']} ({j['source']})")
