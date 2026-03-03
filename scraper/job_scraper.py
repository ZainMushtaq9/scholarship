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
    # Lowercase, remove special characters, and remove common filler words
    title = title.lower()
    title = re.sub(r'[^a-z0-9\s]', '', title)
    fillers = ['urgently', 'hiring', 'needed', 'required', 'remote', 'hybrid', 'onsite']
    for filler in fillers:
        title = title.replace(filler, '')
    return clean_text(title)

def is_official_link(url):
    """Check if the apply link is highly likely to be official."""
    if not url:
        return False
    official_domains = ['.gov.pk', '.edu', '.edu.pk']
    return any(domain in url.lower() for domain in official_domains) or 'careers' in url.lower()

def scrape_rss_jobs(rss_url, source_name):
    """Scrape jobs from an RSS feed"""
    print(f"Scraping jobs from RSS feed: {rss_url}")
    jobs = []
    try:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            title = entry.get('title', '')
            link = entry.get('link', '')
            description = clean_text(BeautifulSoup(entry.get('summary', ''), "html.parser").get_text())
            
            # Simple heuristic for location extraction (often in titles like Software Engineer - Lahore)
            location = "Pakistan"
            if " - " in title:
                parts = title.split(" - ")
                if len(parts) > 1:
                   location = parts[-1].strip()
                   title = parts[0].strip()

            jobs.append({
                'title': title,
                'normalized_title': normalize_title(title),
                'company': 'Unknown (from feed)', # Often RSS feeds don't have separate company tags
                'location': location,
                'salary': 'Not Specified',
                'description': description,
                'apply_links': json.dumps([link] if is_official_link(link) else [{"url": link, "note": "Source Information Only"}]),
                'source': source_name,
                'date_posted': datetime.now() # Depending on feed might have pubDate but let's assume now for simplicity
            })
    except Exception as e:
         print(f"Error scraping RSS {rss_url}: {e}")
    return jobs

def scrape_sample_jobs():
     """A sample wrapper to test scraper"""
     all_jobs = []
     # Example using a generic tech job RSS feed as a placeholder since many PK job portals block simple scrapers
     # In a real scenario, you might use an API or a more complex scraper with Playwright for specific sites.
     rss_feeds = [
         {"url": "https://stackoverflow.blog/feed/", "name": "StackOverflow Blog (Sample)"},
         # You would add actual RSS feeds from Rozee, NJP if available.
     ]

     for feed in rss_feeds:
         all_jobs.extend(scrape_rss_jobs(feed['url'], feed['name']))
     
     return all_jobs

if __name__ == '__main__':
    jobs = scrape_sample_jobs()
    print(f"Scraped {len(jobs)} jobs.")
    if jobs:
        print("Sample Job:", jobs[0])
