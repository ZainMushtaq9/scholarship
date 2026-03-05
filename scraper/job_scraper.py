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

def safe_request(url, timeout=15):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return resp
    except Exception as e:
        print(f"  [SKIP] {url}: {e}")
        return None

def detect_category(title, company='', description=''):
    """Auto-detect job category from title and content."""
    text = f"{title} {company} {description}".lower()
    if any(w in text for w in ['government', 'ministry', 'gov.pk', 'public sector', 'fpsc', 'ppsc', 'nts', 'kppsc', 'spsc', 'bpsc', 'commissioner', 'deputy', 'director general']):
        return 'Government'
    if any(w in text for w in ['software', 'developer', 'engineer', 'python', 'java', 'react', 'node', 'data scientist', 'ai ', 'machine learning', 'web developer', 'it ', 'full stack', 'backend', 'frontend', 'devops', 'cloud']):
        return 'IT/Tech'
    if any(w in text for w in ['teacher', 'professor', 'lecturer', 'university', 'college', 'education', 'school', 'faculty', 'hec ']):
        return 'Education'
    if any(w in text for w in ['doctor', 'nurse', 'hospital', 'medical', 'health', 'pharma', 'surgeon']):
        return 'Healthcare'
    if any(w in text for w in ['bank', 'finance', 'accountant', 'audit', 'accounting']):
        return 'Banking/Finance'
    return 'Private'

def detect_scale(title, description=''):
    """Extract BPS scale if mentioned."""
    text = f"{title} {description}".upper()
    match = re.search(r'BPS[- ]?(\d{1,2})', text)
    if match:
        return f"BPS-{match.group(1)}"
    match = re.search(r'PPS[- ]?(\d{1,2})', text)
    if match:
        return f"PPS-{match.group(1)}"
    match = re.search(r'GRADE[- ]?(\d{1,2})', text)
    if match:
        return f"Grade-{match.group(1)}"
    return 'Not Specified'

def fetch_detail_page(url, timeout=10):
    """Follow a job link and extract the full description from the detail page."""
    if not url or not url.startswith('http'):
        return ''
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Remove scripts and styles
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        # Try common content selectors
        content = None
        for sel in ['.job-description', '.job-detail', '.job-content', '.description',
                    '#job-description', '#job-detail', 'article', '.post-content',
                    '.entry-content', '.content-area', 'main']:
            content = soup.select_one(sel)
            if content:
                break
        if not content:
            content = soup.find('body')
        if content:
            text = content.get_text(separator='\n', strip=True)
            # Clean up excessive whitespace but keep paragraph breaks
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return '\n'.join(lines[:50])  # Max 50 lines
        return ''
    except Exception as e:
        return ''

def _build_job(title, link, source, company='Unknown', location='Pakistan', description='', salary='Not Specified'):
    """Build a standardized job dict with category and scale detection."""
    # Try to fetch full details from the job link
    if not description or description == title or len(description) < 30:
        detail = fetch_detail_page(link, timeout=8)
        if detail and len(detail) > 20:
            description = detail
        else:
            description = f"{title} - {company} - {location}. Apply via {source}."

    category = detect_category(title, company, description)
    scale = detect_scale(title, description)

    # Extract location from title if pattern "Title - City"
    if ' - ' in title:
        parts = title.rsplit(' - ', 1)
        if len(parts[1]) < 30:
            location = parts[1].strip()
            title = parts[0].strip()

    return {
        'title': title,
        'normalized_title': normalize_title(title),
        'company': company,
        'location': location,
        'salary': salary,
        'description': description if description else title,
        'apply_links': json.dumps([link]),
        'source': source,
        'date_posted': datetime.now(),
        'category': category,
        'scale': scale,
        'department': company,
        'job_type': 'Full-time',
    }

# ============================================================
# Individual Scrapers
# ============================================================

def scrape_njp(max_jobs=15):
    """Scrape NJP.gov.pk - Government Jobs"""
    print("Scraping NJP.gov.pk...")
    jobs = []
    resp = safe_request("https://www.njp.gov.pk/")
    if not resp:
        return jobs
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    for a_tag in soup.select('a[href*="/jobs/"]')[:max_jobs]:
        href = a_tag.get('href', '')
        if '/jobs/live' in href or not href:
            continue
        link = href if href.startswith('http') else 'https://www.njp.gov.pk' + href
        
        # Get title from the link text or parent
        title = clean_text(a_tag.get_text())
        if not title or len(title) < 5:
            parent = a_tag.find_parent(['div', 'li', 'tr'])
            if parent:
                title = clean_text(parent.get_text())
        
        if title and len(title) > 5 and len(title) < 200:
            # Extract company from parent container
            parent = a_tag.find_parent(['div', 'li', 'tr', 'article'])
            company = 'Government of Pakistan'
            if parent:
                comp_tag = parent.select_one('.company, .org, .employer')
                if comp_tag:
                    company = clean_text(comp_tag.get_text())
            
            jobs.append(_build_job(title, link, 'NJP.gov.pk', company=company))
            
    return jobs

def scrape_mustakbil(max_jobs=15):
    """Scrape Mustakbil.com"""
    print("Scraping Mustakbil.com...")
    jobs = []
    resp = safe_request("https://www.mustakbil.com/jobs")
    if not resp:
        return jobs
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    listings = soup.select('.job-listing, .job-item, a[href*="/job/"]')
    for item in listings[:max_jobs]:
        if item.name == 'a':
            title = clean_text(item.get_text())
            link = item.get('href', '')
        else:
            title_tag = item.select_one('h2, h3, .job-title, a')
            title = clean_text(title_tag.get_text()) if title_tag else ''
            link_tag = item.select_one('a[href]')
            link = link_tag.get('href', '') if link_tag else ''
        
        if link and not link.startswith('http'):
            link = 'https://www.mustakbil.com' + link
        
        company_tag = item.select_one('.company, .employer') if item.name != 'a' else None
        company = clean_text(company_tag.get_text()) if company_tag else 'Unknown'
        
        if title and len(title) > 3:
            jobs.append(_build_job(title, link, 'Mustakbil', company=company))
            
    return jobs

def scrape_brightspyre(max_jobs=15):
    """Scrape BrightSpyre"""
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
        if title and len(title) > 3 and len(title) < 200:
            jobs.append(_build_job(title, link, 'BrightSpyre'))
            
    return jobs

def scrape_jobz_pk(max_jobs=15):
    """Scrape Jobz.pk"""
    print("Scraping Jobz.pk...")
    jobs = []
    resp = safe_request("https://www.jobz.pk/jobs/")
    if not resp:
        return jobs
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    for item in soup.select('article, .post, a[href*="job"]')[:max_jobs]:
        title_tag = item.select_one('h2, h3, .entry-title, .title') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if not link:
            link_tag = item.select_one('a[href]')
            link = link_tag.get('href', '') if link_tag else ''
        if link and not link.startswith('http'):
            link = 'https://www.jobz.pk' + link
        if title and len(title) > 5 and len(title) < 200:
            jobs.append(_build_job(title, link, 'Jobz.pk'))
            
    return jobs

def scrape_careerokay(max_jobs=15):
    """Scrape CareerOkay.com"""
    print("Scraping CareerOkay.com...")
    jobs = []
    resp = safe_request("https://www.careerokay.com/jobs")
    if not resp:
        return jobs
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    for item in soup.select('.job-listing, .job-item, a[href*="job"]')[:max_jobs]:
        title_tag = item.select_one('h2, h3, .title') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://www.careerokay.com' + link
        if title and len(title) > 3 and len(title) < 200:
            jobs.append(_build_job(title, link, 'CareerOkay'))
            
    return jobs

def scrape_punjab_jobs(max_jobs=15):
    """Scrape Punjab Jobs Portal"""
    print("Scraping Punjab Jobs Portal...")
    jobs = []
    resp = safe_request("https://jobs.punjab.gov.pk/new_recruit/jobs")
    if not resp:
        return jobs
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    for item in soup.select('tr, .job-row, a[href*="job"]')[:max_jobs]:
        title = clean_text(item.get_text())
        link = item.get('href', '') or ''
        if not link:
            link_tag = item.select_one('a[href]')
            link = link_tag.get('href', '') if link_tag else ''
        if link and not link.startswith('http'):
            link = 'https://jobs.punjab.gov.pk' + link
        if title and len(title) > 5 and len(title) < 200 and not title.startswith('Sr'):
            jobs.append(_build_job(title, link, 'Punjab Jobs Portal', company='Government of Punjab'))
            
    return jobs

def scrape_rozee(max_jobs=15):
    """Scrape Rozee.pk"""
    print("Scraping Rozee.pk...")
    jobs = []
    resp = safe_request("https://www.rozee.pk/job/jsearch/q/all/fc/pak")
    if not resp:
        return jobs
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    for item in soup.select('.job, .jlist, a[href*="/job/detail/"]')[:max_jobs]:
        title_tag = item.select_one('h3, h2, .jtitle, .job-title') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://www.rozee.pk' + link
        if title and len(title) > 3:
            jobs.append(_build_job(title, link, 'Rozee.pk'))
            
    return jobs

def scrape_ilmkidunya(max_jobs=10):
    """Scrape Ilmkidunya"""
    print("Scraping Ilmkidunya.com...")
    jobs = []
    resp = safe_request("https://www.ilmkidunya.com/jobs/", timeout=20)
    if not resp:
        return jobs
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    for item in soup.select('a[href*="jobs"], .job-item, article')[:max_jobs]:
        title_tag = item.select_one('h2, h3, .title') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://www.ilmkidunya.com' + link
        if title and len(title) > 5 and len(title) < 200:
            jobs.append(_build_job(title, link, 'Ilmkidunya'))
    return jobs

# ============================================================
ALL_SCRAPERS = [
    scrape_njp,
    scrape_mustakbil,
    scrape_brightspyre,
    scrape_jobz_pk,
    scrape_careerokay,
    scrape_punjab_jobs,
    scrape_rozee,
    scrape_ilmkidunya,
]

def scrape_sample_jobs():
    """Run all scrapers and combine results."""
    all_jobs = []
    for scraper_fn in ALL_SCRAPERS:
        try:
            jobs = scraper_fn()
            all_jobs.extend(jobs)
            print(f"  -> Got {len(jobs)} from {scraper_fn.__name__}")
        except Exception as e:
            print(f"  [ERROR] {scraper_fn.__name__}: {e}")
        time.sleep(1)
    
    print(f"\nTotal jobs scraped: {len(all_jobs)}")
    return all_jobs

if __name__ == '__main__':
    jobs = scrape_sample_jobs()
    print(f"\nScraped {len(jobs)} total jobs.")
    for j in jobs[:5]:
        print(f"  - [{j['category']}] [{j['scale']}] {j['title']} ({j['source']})")
        print(f"    Desc: {j['description'][:100]}...")
