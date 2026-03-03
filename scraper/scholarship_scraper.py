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
    fillers = ['fully funded', 'scholarship', 'applications open', 'apply now', 'in', 'for']
    for filler in fillers:
        title = title.replace(filler, '')
    return clean_text(title)

def is_official_link(url):
    if not url:
        return False
    official_domains = ['.gov', '.edu', '.ac.uk', '.edu.au', '.edu.cn', '.org']
    return any(domain in url.lower() for domain in official_domains)

def safe_request(url, timeout=15):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return resp
    except Exception as e:
        print(f"  [SKIP] Failed to fetch {url}: {e}")
        return None

# ============================================================
# Individual Scraper Functions for Each Scholarship Blog
# ============================================================

def scrape_studyvista(max_items=10):
    """Scrape from StudyVista.pk"""
    print("Scraping StudyVista.pk...")
    scholarships = []
    resp = safe_request("https://studyvista.pk/scholarships-for-pakistani-students/")
    if not resp:
        return scholarships
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = soup.select('article, .post, a[href*="scholarship"]')
    for item in listings[:max_items]:
        title_tag = item.select_one('h2, h3, .entry-title, .title') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://studyvista.pk' + link
        if title and len(title) > 5 and len(title) < 300:
            scholarships.append(_build_scholarship(title, link, 'StudyVista.pk'))
    return scholarships

def scrape_edify(max_items=10):
    """Scrape from Edify.pk"""
    print("Scraping Edify.pk...")
    scholarships = []
    resp = safe_request("https://edify.pk/blog/scholarship-for-undergraduate-students-in-pakistan")
    if not resp:
        return scholarships
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = soup.select('article, .post, a[href*="scholarship"]')
    for item in listings[:max_items]:
        title_tag = item.select_one('h2, h3, .title') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://edify.pk' + link
        if title and len(title) > 5 and len(title) < 300:
            scholarships.append(_build_scholarship(title, link, 'Edify.pk'))
    return scholarships

def scrape_edworld(max_items=10):
    """Scrape from EdWorld.com.pk"""
    print("Scraping EdWorld.com.pk...")
    scholarships = []
    resp = safe_request("https://edworld.com.pk/blog/")
    if not resp:
        return scholarships
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = soup.select('article, .post, a[href*="scholarship"], a[href*="blog"]')
    for item in listings[:max_items]:
        title_tag = item.select_one('h2, h3, .title') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://edworld.com.pk' + link
        if title and len(title) > 5 and len(title) < 300:
            scholarships.append(_build_scholarship(title, link, 'EdWorld'))
    return scholarships

def scrape_fespak(max_items=10):
    """Scrape from FESPak.com"""
    print("Scraping FESPak.com...")
    scholarships = []
    resp = safe_request("https://fespak.com/blog/")
    if not resp:
        return scholarships
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = soup.select('article, .post, a[href*="scholarship"]')
    for item in listings[:max_items]:
        title_tag = item.select_one('h2, h3, .title') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://fespak.com' + link
        if title and len(title) > 5 and len(title) < 300:
            scholarships.append(_build_scholarship(title, link, 'FESPak'))
    return scholarships

def scrape_edifyelite(max_items=10):
    """Scrape from EdifyElite.com.pk"""
    print("Scraping EdifyElite.com.pk...")
    scholarships = []
    resp = safe_request("https://edifyelite.com.pk/blog/masters-scholarships-for-pakistani-students-what-s-new-in-2025")
    if not resp:
        return scholarships
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = soup.select('article, .post, a[href*="scholarship"]')
    for item in listings[:max_items]:
        title_tag = item.select_one('h2, h3, .title') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://edifyelite.com.pk' + link
        if title and len(title) > 5 and len(title) < 300:
            scholarships.append(_build_scholarship(title, link, 'EdifyElite'))
    return scholarships

def scrape_studyabroad_pk(max_items=10):
    """Scrape from StudyAbroad.pk"""
    print("Scraping StudyAbroad.pk...")
    scholarships = []
    resp = safe_request("https://www.studyabroad.pk/")
    if not resp:
        return scholarships
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = soup.select('article, .post, a[href*="scholarship"]')
    for item in listings[:max_items]:
        title_tag = item.select_one('h2, h3, .title') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://www.studyabroad.pk' + link
        if title and len(title) > 5 and len(title) < 300:
            scholarships.append(_build_scholarship(title, link, 'StudyAbroad.pk'))
    return scholarships

def scrape_paragon_edu(max_items=10):
    """Scrape from ParagonEducation.pk"""
    print("Scraping ParagonEducation.pk...")
    scholarships = []
    resp = safe_request("https://paragoneducation.pk/international-scholarships-for-pakistani-students/")
    if not resp:
        return scholarships
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = soup.select('article, .post, a[href*="scholarship"], li')
    for item in listings[:max_items]:
        title_tag = item.select_one('h2, h3, .title, strong') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://paragoneducation.pk' + link
        if title and len(title) > 5 and len(title) < 300:
            scholarships.append(_build_scholarship(title, link, 'ParagonEducation'))
    return scholarships

def scrape_timesconsultant(max_items=10):
    """Scrape from TimesConsultant.com"""
    print("Scraping TimesConsultant.com...")
    scholarships = []
    resp = safe_request("https://timesconsultant.com/blog/usa-scholarships-for-international-and-pakistani-students/")
    if not resp:
        return scholarships
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = soup.select('article, .post, a[href*="scholarship"], h2, h3')
    for item in listings[:max_items]:
        title = clean_text(item.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://timesconsultant.com' + link
        if title and len(title) > 5 and len(title) < 300:
            scholarships.append(_build_scholarship(title, link, 'TimesConsultant'))
    return scholarships

def scrape_scholarships_com(max_items=10):
    """Scrape from Scholarships.com Pakistani section"""
    print("Scraping Scholarships.com...")
    scholarships = []
    resp = safe_request("https://www.scholarships.com/financial-aid/college-scholarships/scholarship-directory/ethnicity/pakistani")
    if not resp:
        return scholarships
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = soup.select('a[href*="scholarship"], .scholarship-item, li')
    for item in listings[:max_items]:
        title_tag = item.select_one('h2, h3, .title') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://www.scholarships.com' + link
        if title and len(title) > 5 and len(title) < 300:
            scholarships.append(_build_scholarship(title, link, 'Scholarships.com'))
    return scholarships

def scrape_intl_scholarships(max_items=10):
    """Scrape from InternationalScholarships.com"""
    print("Scraping InternationalScholarships.com...")
    scholarships = []
    resp = safe_request("https://www.internationalscholarships.com/")
    if not resp:
        return scholarships
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = soup.select('a[href*="scholarship"], article, .post')
    for item in listings[:max_items]:
        title_tag = item.select_one('h2, h3, .title') or item
        title = clean_text(title_tag.get_text())
        link = item.get('href', '') or ''
        if link and not link.startswith('http'):
            link = 'https://www.internationalscholarships.com' + link
        if title and len(title) > 5 and len(title) < 300:
            scholarships.append(_build_scholarship(title, link, 'InternationalScholarships.com'))
    return scholarships

# ============================================================
# Helper to build a standard scholarship dict
# ============================================================

def _build_scholarship(title, link, source, description=''):
    country = "Various"
    if "UK" in title or "United Kingdom" in title: country = "UK"
    elif "USA" in title or "US " in title: country = "USA"
    elif "Australia" in title: country = "Australia"
    elif "Canada" in title: country = "Canada"
    elif "China" in title: country = "China"
    elif "Germany" in title: country = "Germany"
    elif "Turkey" in title or "Turkiye" in title: country = "Turkey"

    degree_level = "Undergraduate, Masters, PhD"
    if "phd" in title.lower(): degree_level = "PhD"
    elif "master" in title.lower(): degree_level = "Masters"
    elif "undergraduate" in title.lower() or "bachelors" in title.lower(): degree_level = "Undergraduate"

    funding_type = "Funded"
    if "fully" in title.lower(): funding_type = "Fully Funded"

    return {
        'title': title,
        'normalized_title': normalize_title(title),
        'country': country,
        'degree_level': degree_level,
        'deadline': 'Check Official Link',
        'funding_type': funding_type,
        'description': description or title,
        'official_apply_links': json.dumps([link] if is_official_link(link) else [{"url": link, "note": "Source Information Only"}]),
        'source': source,
        'date_posted': datetime.now()
    }

# ============================================================
# Main scrape function — calls all scrapers
# ============================================================

ALL_SCRAPERS = [
    scrape_studyvista,
    scrape_edify,
    scrape_edworld,
    scrape_fespak,
    scrape_edifyelite,
    scrape_studyabroad_pk,
    scrape_paragon_edu,
    scrape_timesconsultant,
    scrape_scholarships_com,
    scrape_intl_scholarships,
]

def scrape_sample_scholarships():
    """Run all scholarship scrapers and combine results."""
    all_scholarships = []
    for scraper_fn in ALL_SCRAPERS:
        try:
            items = scraper_fn(max_items=10)
            all_scholarships.extend(items)
            print(f"  -> Got {len(items)} from {scraper_fn.__name__}")
        except Exception as e:
            print(f"  [ERROR] {scraper_fn.__name__}: {e}")
        time.sleep(1)
    
    print(f"\nTotal scholarships scraped: {len(all_scholarships)}")
    return all_scholarships

if __name__ == '__main__':
    scholarships = scrape_sample_scholarships()
    print(f"\nScraped {len(scholarships)} total scholarships.")
    for s in scholarships[:5]:
        print(f"  - {s['title']} ({s['source']})")
