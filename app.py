from flask import Flask, render_template, Response, request, session, redirect, url_for, flash
from models import db, Job, Scholarship
from datetime import datetime
import json
import functools
import os
from scraper.job_scraper import scrape_sample_jobs
from scraper.scholarship_scraper import scrape_sample_scholarships

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agent.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Secret key for session authentication
    app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey123')

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # --- Authentication Decorator ---
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
        jobs = Job.query.filter_by(state='published').order_by(Job.date_posted.desc()).limit(20).all()
        return render_template('index.html', items=jobs, type='job')

    @app.route('/scholarships')
    def scholarships():
        scholars = Scholarship.query.filter_by(state='published').order_by(Scholarship.date_posted.desc()).limit(20).all()
        return render_template('index.html', items=scholars, type='scholarship')

    @app.route('/sitemap.xml')
    def sitemap():
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        pages = ['/', '/scholarships']
        for page in pages:
            xml += '  <url>\n'
            xml += f'    <loc>{request.url_root.rstrip("/")}{page}</loc>\n'
            xml += f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>\n'
            xml += '    <changefreq>daily</changefreq>\n'
            xml += '  </url>\n'
        xml += '</urlset>'
        return Response(xml, mimetype='application/xml')

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
        
        # Simple normalization for manual entry
        normalized = title.lower()
        
        if type == 'job':
            new_item = Job(
                title=title,
                normalized_title=normalized,
                description=description,
                apply_links=json.dumps([link]),
                company=request.form.get('company', 'Manual Entry'),
                location=request.form.get('location', 'Pakistan'),
                source='Admin Panel',
                state='published', # Publish immediately
                seo_title=title,
                slug=normalized.replace(" ", "-")
            )
        elif type == 'scholarship':
             new_item = Scholarship(
                title=title,
                normalized_title=normalized,
                description=description,
                official_apply_links=json.dumps([link]),
                country=request.form.get('country', 'Various'),
                degree_level=request.form.get('degree', 'Bachelors/Masters'),
                funding_type=request.form.get('funding', 'Fully Funded'),
                source='Admin Panel',
                state='published',
                seo_title=title,
                slug=normalized.replace(" ", "-")
             )
        
        db.session.add(new_item)
        db.session.commit()
        flash(f"Manually added new {type}: {title}")
        return redirect(url_for('admin'))

    @app.route('/trigger-scrape')
    def trigger_scrape():
        from ai_engine import process_pending_jobs, process_pending_scholarships
        
        # Scrape
        jobs = scrape_sample_jobs()
        scholars = scrape_sample_scholarships()
        
        # Clean up old jobs (older than 30 days) logic here
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        expired_jobs = Job.query.filter(Job.date_posted < thirty_days_ago).all()
        for ej in expired_jobs:
            db.session.delete(ej)
        
        # Add to DB
        for j in jobs:
            db.session.add(Job(**j))
        for s in scholars:
            db.session.add(Scholarship(**s))
        db.session.commit()
        
        # Run AI Merging Engine
        process_pending_jobs(app)
        process_pending_scholarships(app)
        
        return "Scraping and AI Merging ran successfully!", 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5002)
