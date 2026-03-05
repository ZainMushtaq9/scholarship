from flask import Flask, render_template, Response, request, session, redirect, url_for, flash
from models import db, Job, Scholarship
from datetime import datetime, timedelta
import json
import functools
import os
import threading
import time

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agent.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey123')

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # --- Authentication ---
    def admin_required(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function

    # --- Public Routes ---
    @app.route('/')
    def index():
        jobs = Job.query.filter_by(state='published').order_by(Job.date_posted.desc()).limit(50).all()
        return render_template('index.html', items=jobs, type='job', category_filter=None)

    @app.route('/jobs/<category>')
    def jobs_by_category(category):
        cat_map = {
            'government': 'Government',
            'private': 'Private',
            'it': 'IT/Tech',
            'education': 'Education',
        }
        cat_name = cat_map.get(category.lower(), category.capitalize())
        jobs = Job.query.filter_by(state='published', category=cat_name).order_by(Job.date_posted.desc()).limit(50).all()
        return render_template('index.html', items=jobs, type='job', category_filter=cat_name)

    @app.route('/scholarships')
    def scholarships():
        country = request.args.get('country')
        query = Scholarship.query.filter_by(state='published')
        if country:
            query = query.filter_by(country=country)
        scholars = query.order_by(Scholarship.date_posted.desc()).limit(50).all()
        return render_template('index.html', items=scholars, type='scholarship', category_filter=country)

    # --- Detail/Blog Pages ---
    @app.route('/job/<int:id>')
    @app.route('/job/<int:id>/<slug>')
    def job_detail(id, slug=None):
        job = Job.query.get_or_404(id)
        return render_template('detail.html', item=job, item_type='job')

    @app.route('/scholarship/<int:id>')
    @app.route('/scholarship/<int:id>/<slug>')
    def scholarship_detail(id, slug=None):
        sch = Scholarship.query.get_or_404(id)
        return render_template('detail.html', item=sch, item_type='scholarship')

    # --- Sitemap with all detail pages ---
    @app.route('/sitemap.xml')
    def sitemap():
        base = request.url_root.rstrip("/")
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        # Static pages
        for page in ['/', '/scholarships', '/jobs/government', '/jobs/private', '/jobs/it']:
            xml += f'  <url><loc>{base}{page}</loc><lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod><changefreq>daily</changefreq></url>\n'
        
        # Job detail pages
        with app.app_context():
            jobs = Job.query.filter_by(state='published').all()
            for j in jobs:
                slug = j.slug or j.id
                xml += f'  <url><loc>{base}/job/{j.id}/{slug}</loc><lastmod>{j.date_posted.strftime("%Y-%m-%d") if j.date_posted else datetime.now().strftime("%Y-%m-%d")}</lastmod></url>\n'
            
            scholars = Scholarship.query.filter_by(state='published').all()
            for s in scholars:
                slug = s.slug or s.id
                xml += f'  <url><loc>{base}/scholarship/{s.id}/{slug}</loc><lastmod>{s.date_posted.strftime("%Y-%m-%d") if s.date_posted else datetime.now().strftime("%Y-%m-%d")}</lastmod></url>\n'
        
        xml += '</urlset>'
        return Response(xml, mimetype='application/xml')

    # --- robots.txt for SEO ---
    @app.route('/robots.txt')
    def robots():
        txt = f"User-agent: *\nAllow: /\nSitemap: {request.url_root.rstrip('/')}/sitemap.xml\n"
        return Response(txt, mimetype='text/plain')

    # --- Admin Routes ---
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            if request.form['username'] == 'admin' and request.form['password'] == 'admin123':
                session['logged_in'] = True
                return redirect(url_for('admin'))
            else:
                flash("Invalid credentials")
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.pop('logged_in', None)
        return redirect(url_for('index'))

    @app.route('/admin')
    @admin_required
    def admin():
        jobs = Job.query.order_by(Job.date_posted.desc()).all()
        scholars = Scholarship.query.order_by(Scholarship.date_posted.desc()).all()
        return render_template('admin.html', jobs=jobs, scholars=scholars)

    @app.route('/admin/delete/<type>/<int:id>')
    @admin_required
    def admin_delete(type, id):
        if type == 'job':
            item = Job.query.get_or_404(id)
        elif type == 'scholarship':
            item = Scholarship.query.get_or_404(id)
        db.session.delete(item)
        db.session.commit()
        flash(f"Deleted {type} ID {id} successfully.")
        return redirect(url_for('admin'))

    @app.route('/admin/add/<type>', methods=['POST'])
    @admin_required
    def admin_add(type):
        title = request.form.get('title')
        description = request.form.get('description')
        link = request.form.get('link')
        normalized = title.lower()

        if type == 'job':
            new_item = Job(
                title=title, normalized_title=normalized,
                description=description, apply_links=json.dumps([link]),
                company=request.form.get('company', 'Manual Entry'),
                location=request.form.get('location', 'Pakistan'),
                category=request.form.get('category', 'Other'),
                source='Admin Panel', state='published',
                seo_title=title, slug=normalized.replace(" ", "-")
            )
        elif type == 'scholarship':
            new_item = Scholarship(
                title=title, normalized_title=normalized,
                description=description, official_apply_links=json.dumps([link]),
                country=request.form.get('country', 'Various'),
                degree_level=request.form.get('degree', 'Bachelors/Masters'),
                funding_type=request.form.get('funding', 'Fully Funded'),
                source='Admin Panel', state='published',
                seo_title=title, slug=normalized.replace(" ", "-")
            )
        db.session.add(new_item)
        db.session.commit()
        flash(f"Manually added new {type}: {title}")
        return redirect(url_for('admin'))

    # --- Scraping Trigger Route (non-blocking) ---
    @app.route('/trigger-scrape')
    def trigger_scrape():
        def bg_scrape():
            with app.app_context():
                run_scrape_pipeline(app)
        t = threading.Thread(target=bg_scrape, daemon=True)
        t.start()
        return "Scraping started in background! Refresh the homepage in 30-60 seconds to see results.", 200

    # --- Built-in Daily Scheduler (midnight) ---
    def start_scheduler():
        def scheduler_loop():
            while True:
                now = datetime.now()
                tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                wait_seconds = (tomorrow - now).total_seconds()
                print(f"[SCHEDULER] Next scrape in {wait_seconds/3600:.1f} hours (midnight)")
                time.sleep(wait_seconds)
                print(f"[SCHEDULER] Running auto-scrape at {datetime.now()}")
                with app.app_context():
                    run_scrape_pipeline(app)
                print(f"[SCHEDULER] Auto-scrape completed at {datetime.now()}")

        t = threading.Thread(target=scheduler_loop, daemon=True)
        t.start()
        print("[SCHEDULER] Daily auto-scrape scheduler started (triggers at midnight)")

    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        start_scheduler()

    return app

def run_scrape_pipeline(app):
    """Core scraping pipeline."""
    from scraper.job_scraper import scrape_sample_jobs
    from scraper.scholarship_scraper import scrape_sample_scholarships
    from ai_engine import process_pending_jobs, process_pending_scholarships

    try:
        print("=== SCRAPING JOBS ===")
        jobs = scrape_sample_jobs()
        print(f"=== SCRAPING SCHOLARSHIPS ===")
        scholars = scrape_sample_scholarships()

        with app.app_context():
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            expired = Job.query.filter(Job.date_posted < thirty_days_ago).all()
            for ej in expired:
                db.session.delete(ej)
            if expired:
                print(f"Removed {len(expired)} expired jobs")

            for j in jobs:
                db.session.add(Job(**j))
            for s in scholars:
                db.session.add(Scholarship(**s))
            db.session.commit()
            print(f"Added {len(jobs)} jobs and {len(scholars)} scholarships to DB")

            process_pending_jobs()
            process_pending_scholarships()

        return f"Success! Scraped {len(jobs)} jobs and {len(scholars)} scholarships."
    except Exception as e:
        print(f"[ERROR] Scrape pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5002)
