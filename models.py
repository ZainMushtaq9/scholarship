from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255))
    location = db.Column(db.String(255))
    salary = db.Column(db.String(255))
    description = db.Column(db.Text)
    apply_links = db.Column(db.Text)
    source = db.Column(db.String(255))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Categorization
    department = db.Column(db.String(255), default='General')
    category = db.Column(db.String(255), default='Other')  # IT, Government, Education, etc.
    scale = db.Column(db.String(50), default='Not Specified')  # BPS-17, BPS-18, etc.
    job_type = db.Column(db.String(50), default='Full-time')  # Full-time, Part-time, Contract
    experience = db.Column(db.String(100), default='Not Specified')
    
    # Duplicate Detection & Merging
    normalized_title = db.Column(db.String(255), nullable=False)
    state = db.Column(db.String(50), default='pending')
    
    # SEO Fields
    slug = db.Column(db.String(255))
    seo_title = db.Column(db.String(255))
    seo_meta = db.Column(db.String(255))
    json_ld = db.Column(db.Text)

    def __repr__(self):
        return f'<Job {self.title}>'

class Scholarship(db.Model):
    __tablename__ = 'scholarships'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    country = db.Column(db.String(255))
    degree_level = db.Column(db.String(255))
    deadline = db.Column(db.String(255))
    funding_type = db.Column(db.String(255))
    official_apply_links = db.Column(db.Text)
    description = db.Column(db.Text)
    source = db.Column(db.String(255))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Categorization
    category = db.Column(db.String(255), default='International')  # International, HEC, Provincial
    
    # Duplicate Detection & Merging
    normalized_title = db.Column(db.String(255), nullable=False)
    state = db.Column(db.String(50), default='pending')
    
    # SEO Fields
    slug = db.Column(db.String(255))
    seo_title = db.Column(db.String(255))
    seo_meta = db.Column(db.String(255))
    json_ld = db.Column(db.Text)

    def __repr__(self):
        return f'<Scholarship {self.title}>'
