import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json
import feedparser

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def normalize_title(title):
    """Normalize title for duplicate detection"""
    if not title:
        return ""
    title = title.lower()
    title = re.sub(r'[^a-z0-9\s]', '', title)
    fillers = ['fully funded', 'scholarship', 'applications open', 'apply now', 'in', 'for']
    for filler in fillers:
        title = title.replace(filler, '')
    return clean_text(title)

def is_official_link(url):
    """Check if the apply link is highly likely to be official university or gov link."""
    if not url:
        return False
    official_domains = ['.gov', '.edu', '.ac.uk', '.edu.au', '.edu.cn']
    return any(domain in url.lower() for domain in official_domains)

def scrape_rss_scholarships(rss_url, source_name):
    """Scrape scholarships from an RSS feed"""
    print(f"Scraping scholarships from RSS feed: {rss_url}")
    scholarships = []
    try:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            title = entry.get('title', '')
            link = entry.get('link', '')
            description = clean_text(BeautifulSoup(entry.get('summary', ''), "html.parser").get_text())
            
            # Simple heuristic extraction
            country = "Various"
            if "UK" in title or "United Kingdom" in title: country = "UK"
            elif "USA" in title or "US" in title: country = "USA"
            elif "Australia" in title: country = "Australia"
            elif "Canada" in title: country = "Canada"
            elif "China" in title: country = "China"

            degree_level = "Undergraduate, Masters, PhD"
            if "phd" in title.lower(): degree_level = "PhD"
            elif "master" in title.lower(): degree_level = "Masters"

            funding_type = "Funded"
            if "fully" in title.lower() or "fully funded" in description.lower():
                funding_type = "Fully Funded"

            scholarships.append({
                'title': title,
                'normalized_title': normalize_title(title),
                'country': country,
                'degree_level': degree_level,
                'deadline': 'Check Official Link',
                'funding_type': funding_type,
                'description': description,
                'official_apply_links': json.dumps([link] if is_official_link(link) else [{"url": link, "note": "Source Information Only"}]),
                'source': source_name,
                'date_posted': datetime.now()
            })
    except Exception as e:
         print(f"Error scraping RSS {rss_url}: {e}")
    return scholarships

def scrape_sample_scholarships():
     """A sample wrapper to test scholarship scraper"""
     all_scholarships = []
     # Example using generic RSS feed or actual blog feed later
     rss_feeds = [
         {"url": "https://www.scholars4dev.com/feed/", "name": "Scholars4Dev (Sample)"},
     ]

     for feed in rss_feeds:
         all_scholarships.extend(scrape_rss_scholarships(feed['url'], feed['name']))
     
     return all_scholarships

if __name__ == '__main__':
    scholarships = scrape_sample_scholarships()
    print(f"Scraped {len(scholarships)} scholarships.")
    if scholarships:
        print("Sample Scholarship:", scholarships[0])
