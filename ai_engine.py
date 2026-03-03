import os
import json
from groq import Groq
from models import db, Job, Scholarship

def get_groq_client():
    """Lazy init Groq client only when needed."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("WARNING: GROQ_API_KEY not set. AI merging skipped.")
        return None
    return Groq(api_key=api_key)

def merge_jobs_with_ai(jobs_group):
    """Merge duplicate jobs using Groq AI."""
    if not jobs_group:
        return None

    client = get_groq_client()
    if not client:
        return None

    system_prompt = """You are an expert SEO content writer and job board manager.
    You will be provided with a JSON list of duplicate job postings (same title).
    Merge them into a single, high-quality, SEO-optimized job posting.
    
    Output JSON format ONLY:
    {
        "merged_description": "A comprehensive description combining all info in HTML format.",
        "seo_title": "SEO optimized title (max 70 chars)",
        "seo_meta": "SEO meta description (150-160 chars)",
        "json_ld": { "@context": "https://schema.org", "@type": "JobPosting", "title": "...", "datePosted": "...", "hiringOrganization": {"@type": "Organization", "name": "..."}, "jobLocation": {"@type": "Place", "address": "Pakistan"} }
    }
    """

    jobs_data = []
    for j in jobs_group:
        jobs_data.append({
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "salary": j.salary if hasattr(j, 'salary') else "Not Specified",
            "description": j.description
        })

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(jobs_data)}
            ],
            model="llama3-8b-8192",
            response_format={"type": "json_object"},
            temperature=0.2
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return None

def process_pending_jobs():
    """Finds pending jobs, groups duplicates, and merges them."""
    pending_jobs = Job.query.filter_by(state='pending').all()
    if not pending_jobs:
        print("No pending jobs to process.")
        return

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
            ai_result = merge_jobs_with_ai(group)
            if ai_result:
                primary_job = group[0]
                primary_job.description = ai_result.get('merged_description', primary_job.description)
                primary_job.seo_title = ai_result.get('seo_title')
                primary_job.seo_meta = ai_result.get('seo_meta')
                primary_job.json_ld = json.dumps(ai_result.get('json_ld', {}))

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
                primary_job.company = "Multiple: " + ", ".join([c for c in all_companies if c])
                primary_job.state = 'published'
                primary_job.slug = primary_job.seo_title.lower().replace(" ", "-") if primary_job.seo_title else str(primary_job.id)

                for j in group[1:]:
                    j.state = 'merged'

                db.session.commit()
                print(f"Merged {len(group)} jobs into ID {primary_job.id}")
            else:
                # AI failed, just publish them individually
                for j in group:
                    j.state = 'published'
                    j.slug = j.normalized_title.replace(" ", "-") + f"-{j.id}"
                db.session.commit()
        else:
            job = group[0]
            job.state = 'published'
            job.slug = job.normalized_title.replace(" ", "-") + f"-{job.id}"
            db.session.commit()
            print(f"Published single job ID {job.id}")

def process_pending_scholarships():
    """Find pending scholarships and publish them."""
    pending_sch = Scholarship.query.filter_by(state='pending').all()
    for sch in pending_sch:
        sch.state = 'published'
        sch.slug = sch.normalized_title.replace(" ", "-") + f"-{sch.id}"
    db.session.commit()
    print(f"Published {len(pending_sch)} scholarships.")
