##################################################################################
# models.py
#
# Defines:
#   - Flask & SQLAlchemy setup
#   - Violation model (with resolution tracking)
#   - RiskClassification model
##################################################################################

import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

# ----------------------------
# Original lines from older code:
# ----------------------------
# app = Flask(__name__)
# BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# db_path = os.path.join(BASE_DIR, 'instance', 'violations.db')
# app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db = SQLAlchemy(app)

# ----------------------------
# Updated approach: We'll use db = SQLAlchemy() here
# and let app.py call db.init_app(app).
# ----------------------------
db = SQLAlchemy()

class Violation(db.Model):
    __tablename__ = 'violation'
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(100), nullable=False)
    violation_type = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.Integer, nullable=False)
    fine = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    month = db.Column(db.String(7), nullable=True)  # e.g. "YYYY-MM"

    resolution_date = db.Column(db.DateTime, nullable=True)
    corrective_actions = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Open")

class RiskClassification(db.Model):
    __tablename__ = 'risk_classification'
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(100), unique=True, nullable=False)
    total_violations = db.Column(db.Integer, nullable=False)
    total_fines = db.Column(db.Integer, nullable=False)
    last_violation_date = db.Column(db.DateTime, nullable=True)
    risk_level = db.Column(db.String(20), nullable=False)
    weighted_risk_score = db.Column(db.Float, nullable=False)
    advanced_risk_score = db.Column(db.Float, nullable=False)
    industry_risk_factor = db.Column(db.String(20), nullable=False)
    violation_frequency_score = db.Column(db.Float, nullable=False)
    inspection_history = db.Column(db.String(200), nullable=True)
    unpaid_fines = db.Column(db.Integer, nullable=False)
    average_fine = db.Column(db.Float, nullable=False)
    risk_model_details = db.Column(db.Text, nullable=True)

    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    business_type = db.Column(db.String(100), nullable=True)
