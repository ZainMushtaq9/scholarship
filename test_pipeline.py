from app import create_app
from models import db, Job, Scholarship
from scraper.job_scraper import scrape_sample_jobs
from scraper.scholarship_scraper import scrape_sample_scholarships
from ai_engine import process_pending_jobs, process_pending_scholarships

def run_test_pipeline():
    app = create_app()
    with app.app_context():
        print("--- 1. Scraping Data ---")
        jobs = scrape_sample_jobs()
        scholars = scrape_sample_scholarships()
        
        print(f"Adding {len(jobs)} jobs and {len(scholars)} scholarships to DB...")

        for j in jobs:
            db.session.add(Job(**j))
        for s in scholars:
            db.session.add(Scholarship(**s))
            
        db.session.commit()
        print("Data added successfully.")

        print("\n--- 2. Running AI Validation & SEO Tagging ---")
        process_pending_jobs(app)
        process_pending_scholarships(app)
        
        print("\n--- 3. Verifying Results in DB ---")
        published_jobs = Job.query.filter_by(state='published').all()
        for j in published_jobs:
            print(f"Job: {j.title}")
            print(f" -> SEO Title: {j.seo_title}")
            print(f" -> SEO Meta: {j.seo_meta}")
            print(f" -> Merged Companies: {j.company}")
            print(f" -> JSON-LD Present: {'Yes' if j.json_ld else 'No'}")
            print("-" * 20)
            
if __name__ == "__main__":
    run_test_pipeline()
