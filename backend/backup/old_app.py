import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_cors import CORS
from datetime import datetime
import random
import numpy as np  # For Poisson distribution
from collections import defaultdict

# -------------------------------------
# Import regulatory mapping (CSV-based fines)
# -------------------------------------
try:
    from regulatory_mapping import REGULATORY_MAPPING
except ImportError:
    REGULATORY_MAPPING = {}

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, 'instance', 'violations.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -----------------------------
# Model Definitions
# -----------------------------
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
    # Extended fields:
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    business_type = db.Column(db.String(100), nullable=True)

# -----------------------------------------------------
# Severity Mapping by Category (based on research)
# -----------------------------------------------------
category_severity_map = {
    "Personal Hygiene & Health Violations": 4,
    "Food Source & Quality Violations": 4,
    "Food Preparation & Handling Violations": 5,
    "Cross-Contamination Violations": 5,
    "Temperature & Time Control Violations": 5,
    "Food Storage & Display Violations": 4,
    "Equipment & Utensil Violations": 3,
    "Food Storage Facility Violations": 4,
    "Unsafe Food Violations": 5,
    "Pest Control Violations": 4,
    "Sanitation & Cleaning Violations": 3,
    "Waste Disposal Violations": 3,
    "Food Transport Violations": 3,
    "Establishment Structural Violations": 2,
    "Food Packaging & Labeling Violations": 2,
    "General Regulatory Violations": 2,
}

# -----------------------------------------------------
# Industry Profiles: compliance_factor & impact_factor
# -----------------------------------------------------
industry_profiles = {
    "Healthcare": {"compliance_factor": 1.5, "impact_factor": 1.4},
    "Restaurant": {"compliance_factor": 1.4, "impact_factor": 1.3},
    "Food Service": {"compliance_factor": 1.4, "impact_factor": 1.3},
    "Retail": {"compliance_factor": 1.1, "impact_factor": 1.0},
    "Electronics": {"compliance_factor": 1.0, "impact_factor": 1.0},
    "Real Estate": {"compliance_factor": 1.1, "impact_factor": 1.1},
    "Automotive": {"compliance_factor": 1.0, "impact_factor": 1.0},
    "Bakery": {"compliance_factor": 1.4, "impact_factor": 1.3},
    "Financial": {"compliance_factor": 1.2, "impact_factor": 1.1},
    "Logistics": {"compliance_factor": 1.1, "impact_factor": 1.0},
    "Home Goods": {"compliance_factor": 1.0, "impact_factor": 1.0},
    "Agriculture": {"compliance_factor": 1.2, "impact_factor": 1.2},
    "Hardware": {"compliance_factor": 1.0, "impact_factor": 1.0},
    "General Business": {"compliance_factor": 1.0, "impact_factor": 1.0},
}

# -----------------------------------------------------
# CSV-based Fine Calculation
# -----------------------------------------------------
def compute_fine(category, violation_type):
    if not REGULATORY_MAPPING or violation_type not in REGULATORY_MAPPING:
        return 0
    offense_options = REGULATORY_MAPPING[violation_type].get("offenses", [])
    numeric_fines = []
    for off in offense_options:
        try:
            numeric_fines.append(int(off))
        except ValueError:
            pass
    if not numeric_fines:
        return 0
    return random.choice(numeric_fines)

# -----------------------------------------------------
# Legacy placeholder logic for backward compatibility
# (setup_db.py references these)
# -----------------------------------------------------
def compute_weighted_risk(total_violations, total_fines, violation_frequency, average_severity):
    """
    Old placeholder approach: normalizes the product of (frequency * impact).
    Maintained so setup_db.py doesn't break when it imports it.
    """
    impact = (total_fines / total_violations) * average_severity if total_violations > 0 else 0
    raw_score = violation_frequency * impact
    normalized_score = raw_score / 1000
    return normalized_score

def compute_aggregated_risk(violation_frequency, average_fine, average_severity, violation_timestamps, risk_modifier):
    """
    Old aggregator, also kept for backward compatibility.
    Weighted sum of freq, impact, trend with an arbitrary risk_modifier.
    """
    freq_risk = violation_frequency * 10
    norm_fine = average_fine / 5000.0
    norm_sev = average_severity / 5.0
    imp_risk = (norm_fine + norm_sev) * 5

    if len(violation_timestamps) < 2:
        trend_risk = 0.0
    else:
        month_counts = defaultdict(int)
        for ts in violation_timestamps:
            m = ts.strftime("%Y-%m")
            month_counts[m] += 1
        months_sorted = sorted(month_counts.keys())
        counts = [month_counts[m] for m in months_sorted]
        n = len(counts)
        if n < 2:
            trend_risk = 0.0
        else:
            x = list(range(n))
            mean_x = sum(x) / n
            mean_y = sum(counts) / n
            numerator = sum(x[i] * counts[i] for i in range(n)) - n * mean_x * mean_y
            denominator = sum(x[i]**2 for i in range(n)) - n * (mean_x**2)
            slope = numerator / denominator if denominator else 0
            slope = max(slope, 0.0)
            # old approach scaled slope by 2
            trend_risk = slope * 2

    base_score = freq_risk * 0.4 + imp_risk * 0.4 + trend_risk * 0.2
    final = base_score * risk_modifier
    return final, freq_risk, imp_risk, trend_risk

# -----------------------------------------------------
# New Poisson-based aggregator
# -----------------------------------------------------
def compute_risk_score(total_violations, months_in_period, average_fine, avg_severity,
                       violation_timestamps, business_type):
    """
    The new academically-informed aggregator (Poisson freq, severity, industry).
    """
    if months_in_period <= 0:
        freq_risk = 0.0
    else:
        lamda = total_violations / months_in_period
        freq_risk = 1 - np.exp(-lamda)  # scale 0..1

    fine_norm = min(average_fine / 10000.0, 1.0)
    sev_norm = min(avg_severity / 5.0, 1.0)
    imp_risk = 0.5 * fine_norm + 0.5 * sev_norm

    if len(violation_timestamps) < 2:
        trend_risk = 0.0
    else:
        month_counts = defaultdict(int)
        for ts in violation_timestamps:
            m = ts.strftime("%Y-%m")
            month_counts[m] += 1
        months_sorted = sorted(month_counts.keys())
        counts = [month_counts[m] for m in months_sorted]
        n = len(counts)
        if n < 2:
            trend_risk = 0.0
        else:
            x = list(range(n))
            mean_x = sum(x) / n
            mean_y = sum(counts) / n
            numerator = sum(x[i] * counts[i] for i in range(n)) - n * mean_x * mean_y
            denominator = sum(x[i]**2 for i in range(n)) - n * (mean_x**2)
            slope = numerator / denominator if denominator else 0
            slope = max(slope, 0.0)
            trend_risk = min(slope / 5.0, 1.0)

    base_score = freq_risk * 0.4 + imp_risk * 0.4 + trend_risk * 0.2

    profile = industry_profiles.get(business_type, {"compliance_factor": 1.0, "impact_factor": 1.0})
    industry_mod = (profile["compliance_factor"] + profile["impact_factor"]) / 2.0

    final_score = base_score * industry_mod
    return final_score, freq_risk, imp_risk, trend_risk

# -----------------------------------------------------
# classify_risk
# -----------------------------------------------------
def classify_risk(score):
    if score >= 0.75:
        return "High"
    elif score >= 0.40:
        return "Medium"
    else:
        return "Low"

# -----------------------------------------------------
# generate_insight
# -----------------------------------------------------
def generate_insight(business_name, total_violations, active_period, average_fine,
                     average_severity, violation_frequency, freq_risk, imp_risk,
                     trend_risk, final_score):
    if freq_risk >= imp_risk and freq_risk >= trend_risk:
        dominant = "frequency"
        dominant_phrase = "a persistently high rate of recurring non-compliance"
    elif imp_risk >= freq_risk and imp_risk >= trend_risk:
        dominant = "impact"
        dominant_phrase = "the significant adverse effects each violation imposes on operations and finances"
    else:
        dominant = "trend"
        dominant_phrase = "a worrying upward trend in violations over recent months"

    risk_category = classify_risk(final_score)

    templates = {
        "High": {
            "frequency": [
                f"Business '{business_name}' has demonstrated an exceptionally high level of non-compliance by registering {total_violations} violations in only {active_period} days. "
                f"This recurring pattern, driven by {dominant_phrase}, indicates deep systemic issues that critically undermine operational stability. "
                f"With a final risk score of {final_score:.2f}, the business is in the HIGH RISK category. Immediate, transformative corrective actions are imperative."
            ],
            "impact": [
                f"'{business_name}' is facing critical operational and financial challenges, as evidenced by {total_violations} violations over {active_period} days. "
                f"The high average fine and severity underscore the severe consequences, primarily driven by {dominant_phrase}. "
                f"The risk score of {final_score:.2f} places the business in HIGH RISK, necessitating immediate strategic reforms."
            ],
            "trend": [
                f"Business '{business_name}' is on a concerning trajectory, with a rapidly escalating number of violations over {active_period} days. "
                f"This trend, highlighted by {dominant_phrase}, has pushed the business into the HIGH RISK category with a final score of {final_score:.2f}. Decisive action is essential."
            ]
        },
        "Medium": {
            "frequency": [
                f"Business '{business_name}' has recorded {total_violations} violations in {active_period} days. "
                f"While the frequency is moderate, recurring issues—evidenced by {dominant_phrase}—suggest compliance gaps. "
                f"With a final risk score of {final_score:.2f}, the business is MEDIUM RISK. Targeted improvements are recommended."
            ],
            "impact": [
                f"'{business_name}' has experienced {total_violations} violations in {active_period} days, leading to noticeable strain. "
                f"The consequences, underscored by {dominant_phrase}, yield a MEDIUM RISK score of {final_score:.2f}. Proactive measures are advised."
            ],
            "trend": [
                f"Business '{business_name}' shows a modest upward trend over {active_period} days with {total_violations} incidents. "
                f"This gradual increase, driven by {dominant_phrase}, places the business in the MEDIUM RISK category with a final score of {final_score:.2f}. Preventive actions are recommended."
            ]
        },
        "Low": {
            "default": [
                f"Business '{business_name}' has maintained excellent compliance over {active_period} days with only {total_violations} violations. "
                f"This results in a LOW RISK score of {final_score:.2f} and reflects a strong culture of compliance."
            ]
        }
    }

    if risk_category == "Low":
        narrative = random.choice(templates["Low"]["default"])
    else:
        category_templates = templates.get(risk_category, {})
        narrative = random.choice(category_templates.get(dominant, category_templates.get("default", ["No narrative available."])))
    return narrative

# -----------------------------
# Flask API Endpoints (unchanged)
# -----------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Fujairah Municipality API is Running"}), 200

@app.route('/violations', methods=['GET'])
def get_violations():
    violations = Violation.query.all()
    return jsonify([
        {
            "id": v.id,
            "business_name": v.business_name,
            "violation_type": v.violation_type,
            "category": v.category,
            "severity": v.severity,
            "fine": v.fine,
            "timestamp": v.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "location": v.location,
            "month": v.month
        }
        for v in violations
    ])

@app.route('/risk', methods=['GET'])
def get_risk():
    risk_data = RiskClassification.query.all()
    return jsonify([
        {
            "business_name": r.business_name,
            "total_violations": r.total_violations,
            "total_fines": r.total_fines,
            "last_violation_date": r.last_violation_date.strftime("%Y-%m-%d %H:%M:%S") if r.last_violation_date else None,
            "risk_level": r.risk_level,
            "weighted_risk_score": r.weighted_risk_score,
            "advanced_risk_score": r.advanced_risk_score,
            "industry_risk_factor": r.industry_risk_factor,
            "violation_frequency_score": r.violation_frequency_score,
            "inspection_history": r.inspection_history,
            "unpaid_fines": r.unpaid_fines,
            "average_fine": r.average_fine,
            "risk_model_details": r.risk_model_details,
            "description": r.description,
            "location": r.location,
            "business_type": r.business_type
        }
        for r in risk_data
    ])

@app.route('/businesses', methods=['GET'])
def get_businesses():
    businesses = RiskClassification.query.with_entities(
        RiskClassification.business_name,
        RiskClassification.total_violations,
        RiskClassification.risk_level,
        RiskClassification.description,
        RiskClassification.location,
        RiskClassification.business_type
    ).all()
    return jsonify([
        {
            "business_name": b.business_name,
            "total_violations": b.total_violations,
            "risk_level": b.risk_level,
            "description": b.description,
            "location": b.location,
            "business_type": b.business_type
        }
        for b in businesses
    ])

@app.route('/analytics', methods=['GET'])
def get_analytics():
    analytics = db.session.execute(text("""
        SELECT violation_type, COUNT(*) AS occurrence, SUM(fine) AS total_fines
        FROM violation
        GROUP BY violation_type
        ORDER BY occurrence DESC;
    """)).fetchall()
    return jsonify([dict(row._mapping) for row in analytics])

@app.route('/trends/violations', methods=['GET'])
def get_violation_trends():
    try:
        trends = db.session.execute(text("""
            SELECT strftime('%Y-%m', timestamp) AS month, category, business_name, violation_type, COUNT(*) AS total_violations
            FROM violation
            WHERE timestamp >= date('now', '-12 months')
            GROUP BY month, category, business_name, violation_type
            ORDER BY month ASC;
        """)).fetchall()
        return jsonify([dict(row._mapping) for row in trends])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trends/violations/all', methods=['GET'])
def get_all_violation_trends():
    try:
        trends = db.session.execute(text("""
            SELECT strftime('%Y-%m', timestamp) AS month, category, business_name, violation_type, COUNT(*) AS total_violations
            FROM violation
            GROUP BY month, category, business_name, violation_type
            ORDER BY month ASC;
        """)).fetchall()
        return jsonify([dict(row._mapping) for row in trends])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trends/fines', methods=['GET'])
def get_fine_trends():
    try:
        fines = db.session.execute(text("""
            SELECT strftime('%Y-%m', timestamp) AS month, SUM(fine) AS total_fines
            FROM violation
            WHERE timestamp >= date('now', '-24 months')
            GROUP BY month
            ORDER BY month ASC;
        """)).fetchall()
        return jsonify([dict(row._mapping) for row in fines])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trends/business-risk', methods=['GET'])
def get_business_risk_trends():
    try:
        risk_trends = db.session.execute(text("""
            SELECT business_name, strftime('%Y-%m', last_violation_date) AS month, risk_level
            FROM risk_classification
            ORDER BY month ASC, risk_level DESC;
        """)).fetchall()
        return jsonify([dict(row._mapping) for row in risk_trends])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trends/repeat-offenders', methods=['GET'])
def get_repeat_offenders():
    try:
        offenders = db.session.execute(text("""
            SELECT business_name, COUNT(*) AS violation_count, MAX(timestamp) AS last_violation_date,
                CASE
                    WHEN COUNT(*) >= 7 THEN 'High Risk'
                    WHEN COUNT(*) BETWEEN 4 AND 6 THEN 'Medium Risk'
                    ELSE 'Low Risk'
                END AS risk_status
            FROM violation
            WHERE timestamp >= date('now', '-6 months')
            GROUP BY business_name
            ORDER BY violation_count DESC;
        """)).fetchall()
        return jsonify([dict(row._mapping) for row in offenders])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trends/geo-hotspots', methods=['GET'])
def get_geo_hotspots():
    try:
        hotspots = db.session.execute(text("""
            SELECT location, COUNT(*) AS total_violations
            FROM violation
            GROUP BY location
            ORDER BY total_violations DESC;
        """)).fetchall()
        return jsonify([dict(row._mapping) for row in hotspots])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate_report/<business_name>', methods=['GET'])
def generate_report(business_name):
    print(f"Report endpoint hit for business: {business_name}")
    record = RiskClassification.query.filter_by(business_name=business_name).first()
    if not record:
        print("No record found for business")
        return jsonify({"error": "Business not found"}), 404

    risk_details = record.risk_model_details or "No details provided."
    report_data = {
        "Business Name": record.business_name,
        "Total Violations": record.total_violations,
        "Total Fines": record.total_fines,
        "Last Violation Date": record.last_violation_date.strftime("%Y-%m-%d %H:%M:%S") if record.last_violation_date else "N/A",
        "Risk Level": record.risk_level,
        "Weighted Risk Score": record.weighted_risk_score,
        "Advanced Risk Score": record.advanced_risk_score,
        "Industry Risk Factor": record.industry_risk_factor,
        "Violation Frequency Score": record.violation_frequency_score,
        "Inspection History": record.inspection_history,
        "Unpaid Fines": record.unpaid_fines,
        "Average Fine": record.average_fine,
        "Risk Model Details": risk_details,
        "Description": record.description,
        "Location": record.location,
        "Business Type": record.business_type
    }
    
    report_text = f"""
**Business Risk Report for {record.business_name}**

**Risk Level:** {record.risk_level}
**Total Violations:** {record.total_violations}
**Total Fines:** {record.total_fines}
**Last Violation Date:** {report_data['Last Violation Date']}
**Weighted Risk Score:** {record.weighted_risk_score:.2f}
**Advanced Risk Score:** {record.advanced_risk_score:.2f}
**Industry Risk Factor:** {record.industry_risk_factor}
**Violation Frequency Score:** {record.violation_frequency_score:.2f}
**Inspection History:** {record.inspection_history}
**Unpaid Fines:** {record.unpaid_fines}
**Average Fine:** {record.average_fine:.2f}

**Description:** {record.description or "No description provided."}
**Location:** {record.location or "Not provided."}
**Business Type:** {record.business_type or "Not specified."}

**Detailed Analysis:**
{risk_details}
    """
    
    print("Report generated successfully.")
    return jsonify({
        "business_name": record.business_name,
        "report": report_text,
        "report_data": report_data
    })

# Minimal CLI command
#@app.cli.command("seed")
#def seed_cli():
#   from backend.backup.old_setup_db import seed_db
#   seed_db()

#if __name__ == '__main__':
#    app.run(debug=True)
