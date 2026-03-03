import os
import json
from groq import Groq
from models import db, Job, Scholarship
from app import create_app

# Set API Key directly or from environment variable
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY environment variable is not set. AI merging will fail.")
    
client = Groq(api_key=GROQ_API_KEY)

def merge_jobs_with_ai(jobs_group):
    """
    Takes a list of Job objects (duplicates) and uses Groq to merge them.
    Returns a dictionary with merged content and SEO data.
    """
    if not jobs_group:
        return None
        
    system_prompt = """You are an expert SEO content writer and job board manager.
    You will be provided with a JSON list of duplicate job postings (same title).
    Your task is to merge them into a single, high-quality, SEO-optimized job posting.
    
    Output JSON format ONLY:
    {
        "merged_description": "A comprehensive description combining all requirements, responsibilities, and benefits in HTML format (using <ul>, <li>, <strong> etc.).",
        "seo_title": "SEO optimized title (max 70 chars)",
        "seo_meta": "SEO meta description (150-160 chars)",
        "json_ld": { ... standard JobPosting schema.org JSON-LD ... }
    }
    """
    
    # Prepare data for AI
    jobs_data = []
    for j in jobs_group:
        jobs_data.append({
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "salary": j.salary,
            "description": j.description
        })
        
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(jobs_data)}
            ],
            model="llama3-8b-8192", # Using a fast, free tier model
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
        
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return None

def process_pending_jobs(app):
    """Finds pending jobs, groups duplicates, and merges them using AI."""
    with app.app_context():
        # Get all pending jobs
        pending_jobs = Job.query.filter_by(state='pending').all()
        
        # Group by normalized_title and location
        groups = {}
        for job in pending_jobs:
            key = f"{job.normalized_title}_{job.location}"
            if key not in groups:
                groups[key] = []
            groups[key].append(job)
            
        for key, group in groups.items():
            print(f"Processing group: {key} ({len(group)} duplicates)")
            
            if len(group) > 1:
                # Merge logic
                ai_result = merge_jobs_with_ai(group)
                if ai_result:
                    # Create a new merged job or update the primary one
                    primary_job = group[0]
                    primary_job.description = ai_result.get('merged_description', primary_job.description)
                    primary_job.seo_title = ai_result.get('seo_title')
                    primary_job.seo_meta = ai_result.get('seo_meta')
                    primary_job.json_ld = json.dumps(ai_result.get('json_ld', {}))
                    
                    # Merge apply links and companies
                    all_links = []
                    all_companies = set()
                    for j in group:
                        if j.apply_links:
                            try:
                                links = json.loads(j.apply_links)
                                all_links.extend(links)
                            except:
                                pass
                        all_companies.add(j.company)
                    
                    primary_job.apply_links = json.dumps(all_links)
                    primary_job.company = "Multiple Companies: " + ", ".join([c for c in all_companies if c])
                    primary_job.state = 'published'
                    primary_job.slug = primary_job.seo_title.lower().replace(" ", "-") if primary_job.seo_title else str(primary_job.id)
                    
                    # Mark others as merged
                    for j in group[1:]:
                        j.state = 'merged'
                        
                    db.session.commit()
                    print(f"Successfully merged {len(group)} jobs into ID {primary_job.id}")
            else:
                # Just publish single jobs, maybe run AI for SEO too, but for now just mark published
                job = group[0]
                job.state = 'published'
                job.slug = job.normalized_title.replace(" ", "-") + f"-{job.id}"
                db.session.commit()
                print(f"Published single job ID {job.id}")

def process_pending_scholarships(app):
    """Find pending scholarships... (similar logic, skipped full AI for brevity, just marking published)"""
    with app.app_context():
        pending_sch = Scholarship.query.filter_by(state='pending').all()
        for sch in pending_sch:
            sch.state = 'published'
            sch.slug = sch.normalized_title.replace(" ", "-") + f"-{sch.id}"
        db.session.commit()
        print(f"Published {len(pending_sch)} scholarships.")

if __name__ == '__main__':
    app = create_app()
    print("Starting AI Merging Engine...")
    process_pending_jobs(app)
    process_pending_scholarships(app)
    print("Finished processing.")
