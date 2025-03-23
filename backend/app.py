##################################################################################
# app.py
#
# Main Flask file with all endpoints, referencing:
#   - models.py
#   - seed.py
# with no omitted lines.
##################################################################################

import os
from flask import Flask, jsonify, request  # ADDED: request for POST
from flask_cors import CORS
from sqlalchemy import text
from datetime import datetime

# Import db and model classes (not 'app') from models
from models import db, Violation, RiskClassification
from seed import seed_db

# ------------------------------------------------------------------------------
# Create the Flask app here (instead of models.py) to avoid circular imports
# ------------------------------------------------------------------------------
app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, 'instance', 'violations.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with this app
db.init_app(app)

# ------------------------------------------------------------------------------
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Fujairah Municipality API is Running"}), 200

@app.route('/violations', methods=['GET'])
def get_violations():
    violations = Violation.query.all()
    out = []
    for v in violations:
        out.append({
            "id": v.id,
            "business_name": v.business_name,
            "violation_type": v.violation_type,
            "category": v.category,
            "severity": v.severity,
            "fine": v.fine,
            "timestamp": v.timestamp.strftime("%Y-%m-%d %H:%M:%S") if v.timestamp else None,
            "location": v.location,
            "month": v.month,
            "resolution_date": v.resolution_date.strftime("%Y-%m-%d %H:%M:%S") if v.resolution_date else None,
            "corrective_actions": v.corrective_actions,
            "status": v.status
        })
    return jsonify(out)

@app.route('/risk', methods=['GET'])
def get_risk():
    data = RiskClassification.query.all()
    result = []
    for r in data:
        result.append({
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
        })
    return jsonify(result)

@app.route('/businesses', methods=['GET'])
def get_businesses():
    rows = RiskClassification.query.with_entities(
        RiskClassification.business_name,
        RiskClassification.total_violations,
        RiskClassification.risk_level,
        RiskClassification.description,
        RiskClassification.location,
        RiskClassification.business_type
    ).all()
    data = []
    for b in rows:
        data.append({
            "business_name": b.business_name,
            "total_violations": b.total_violations,
            "risk_level": b.risk_level,
            "description": b.description,
            "location": b.location,
            "business_type": b.business_type
        })
    return jsonify(data)

@app.route('/analytics', methods=['GET'])
def get_analytics():
    sql = text("""
        SELECT violation_type, COUNT(*) AS occurrence, SUM(fine) AS total_fines
        FROM violation
        GROUP BY violation_type
        ORDER BY occurrence DESC;
    """)
    results = db.session.execute(sql).fetchall()
    return jsonify([dict(row._mapping) for row in results])

@app.route('/trends/violations', methods=['GET'])
def get_violation_trends():
    try:
        sql = text("""
            SELECT strftime('%Y-%m', timestamp) AS month, category, business_name, violation_type, COUNT(*) AS total_violations
            FROM violation
            WHERE timestamp >= date('now','-12 months')
            GROUP BY month, category, business_name, violation_type
            ORDER BY month ASC;
        """)
        data = db.session.execute(sql).fetchall()
        return jsonify([dict(row._mapping) for row in data])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trends/violations/all', methods=['GET'])
def get_all_violation_trends():
    try:
        sql = text("""
            SELECT strftime('%Y-%m', timestamp) AS month, category, business_name, violation_type, COUNT(*) AS total_violations
            FROM violation
            GROUP BY month, category, business_name, violation_type
            ORDER BY month ASC;
        """)
        data = db.session.execute(sql).fetchall()
        return jsonify([dict(row._mapping) for row in data])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trends/fines', methods=['GET'])
def get_fine_trends():
    try:
        sql = text("""
            SELECT strftime('%Y-%m', timestamp) AS month, SUM(fine) AS total_fines
            FROM violation
            WHERE timestamp >= date('now','-24 months')
            GROUP BY month
            ORDER BY month ASC;
        """)
        data = db.session.execute(sql).fetchall()
        return jsonify([dict(row._mapping) for row in data])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trends/business-risk', methods=['GET'])
def get_business_risk_trends():
    try:
        sql = text("""
            SELECT business_name, strftime('%Y-%m', last_violation_date) AS month, risk_level
            FROM risk_classification
            ORDER BY month ASC, risk_level DESC;
        """)
        data = db.session.execute(sql).fetchall()
        return jsonify([dict(row._mapping) for row in data])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trends/repeat-offenders', methods=['GET'])
def get_repeat_offenders():
    try:
        sql = text("""
            SELECT business_name, COUNT(*) AS violation_count, MAX(timestamp) AS last_violation_date,
                CASE
                    WHEN COUNT(*) >= 7 THEN 'High Risk'
                    WHEN COUNT(*) BETWEEN 4 AND 6 THEN 'Medium Risk'
                    ELSE 'Low Risk'
                END AS risk_status
            FROM violation
            WHERE timestamp >= date('now','-6 months')
            GROUP BY business_name
            ORDER BY violation_count DESC;
        """)
        data = db.session.execute(sql).fetchall()
        return jsonify([dict(row._mapping) for row in data])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trends/geo-hotspots', methods=['GET'])
def get_geo_hotspots():
    try:
        sql = text("""
            SELECT location, COUNT(*) AS total_violations
            FROM violation
            GROUP BY location
            ORDER BY total_violations DESC;
        """)
        data = db.session.execute(sql).fetchall()
        return jsonify([dict(row._mapping) for row in data])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate_report/<business_name>', methods=['GET'])
def generate_report(business_name):
    record = RiskClassification.query.filter_by(business_name=business_name).first()
    if not record:
        return jsonify({"error": "Business not found"}), 404

    risk_details = record.risk_model_details or "No details provided."
    rep_data = {
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

{risk_details}
    """
    return jsonify({
        "business_name": record.business_name,
        "report": report_text,
        "report_data": rep_data
    })

# ------------------------------------------------------------------------
# Existing seed CLI command
# ------------------------------------------------------------------------
@app.cli.command("seed")
def seed_cli():
    seed_db()

# ------------------------------------------------------------------------
# NEW: Single Violation Endpoint - GET /violations/<violation_id>
# This returns a single violation's main info, if you need it for details page
# ------------------------------------------------------------------------
@app.route('/violations/<int:violation_id>', methods=['GET'])
def get_single_violation(violation_id):
    violation = Violation.query.get(violation_id)
    if not violation:
        return jsonify({"error": "Violation not found"}), 404

    data = {
        "id": violation.id,
        "business_name": violation.business_name,
        "violation_type": violation.violation_type,
        "category": violation.category,
        "severity": violation.severity,
        "fine": violation.fine,
        "timestamp": violation.timestamp.strftime("%Y-%m-%d %H:%M:%S") if violation.timestamp else None,
        "location": violation.location,
        "month": violation.month,
        "resolution_date": violation.resolution_date.strftime("%Y-%m-%d %H:%M:%S") if violation.resolution_date else None,
        "corrective_actions": violation.corrective_actions,
        "status": violation.status
    }
    return jsonify(data), 200

# ------------------------------------------------------------------------
# Get Violations List filter parameters
# ------------------------------------------------------------------------

@app.route('/violations/distinct-fields', methods=['GET'])
def get_distinct_violation_fields():
    """
    Returns distinct categories, violation types, and statuses
    so the front end can populate dropdowns dynamically.
    e.g.
    {
      "categories": ["Food Handling", "Fire Code", "Pest Control"],
      "violationTypes": ["hygiene", "fire safety", "food"],
      "statuses": ["Open", "Closed", "Pending Payment", ...]
    }
    """
    try:
        # Distinct categories
        cat_sql = text("SELECT DISTINCT category FROM violation WHERE category != '' AND category IS NOT NULL ORDER BY category;")
        cats = db.session.execute(cat_sql).fetchall()
        categories = [row[0] for row in cats if row[0]]

        # Distinct violation types
        vt_sql = text("SELECT DISTINCT violation_type FROM violation WHERE violation_type != '' AND violation_type IS NOT NULL ORDER BY violation_type;")
        vts = db.session.execute(vt_sql).fetchall()
        violation_types = [row[0] for row in vts if row[0]]

        # Distinct statuses
        st_sql = text("SELECT DISTINCT status FROM violation WHERE status != '' AND status IS NOT NULL ORDER BY status;")
        sts = db.session.execute(st_sql).fetchall()
        statuses = [row[0] for row in sts if row[0]]

        return jsonify({
            "categories": categories,
            "violationTypes": violation_types,
            "statuses": statuses
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# ------------------------------------------------------------------------
# NEW: Status History Endpoints
# GET -> returns the multi-step departmental statuses for that violation
# POST -> appends a new status step with optional notes
# ------------------------------------------------------------------------
@app.route('/violations/<int:violation_id>/status-history', methods=['GET'])
def get_violation_status_history(violation_id):
    """
    Returns an array of status changes for the given violation,
    in ascending order of updated_at
    """
    # We'll do a raw query to the violation_status_history table
    sql = text("""
        SELECT id, violation_id, status, notes, updated_at
        FROM violation_status_history
        WHERE violation_id = :vid
        ORDER BY updated_at ASC
    """)
    result = db.session.execute(sql, {"vid": violation_id}).fetchall()
    history = []
    for row in result:
        rowd = dict(row._mapping)
        # Format the date
        rowd["updated_at"] = (
            rowd["updated_at"].strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(rowd["updated_at"], datetime)
            else str(rowd["updated_at"])
        )
        history.append(rowd)
    return jsonify(history), 200

@app.route('/violations/<int:violation_id>/status-history', methods=['POST'])
def add_violation_status_history(violation_id):
    """
    Expects JSON like:
    {
      "status": "Pending Payment",
      "notes": "Forwarded invoice #F123 for payment"
    }
    Appends a new step to the violation_status_history table.
    """
    violation = Violation.query.get(violation_id)
    if not violation:
        return jsonify({"error": "Violation not found"}), 404

    data = request.get_json()
    status_val = data.get("status")
    notes_val = data.get("notes", "")
    if not status_val:
        return jsonify({"error": "Status field is required"}), 400

    now = datetime.now()
    insert_sql = text("""
        INSERT INTO violation_status_history (violation_id, status, notes, updated_at)
        VALUES (:vid, :sts, :nts, :upd)
    """)
    db.session.execute(insert_sql, {
        "vid": violation_id,
        "sts": status_val,
        "nts": notes_val,
        "upd": now
    })
    db.session.commit()
    return jsonify({"message": "Status step added successfully"}), 201

if __name__ == "__main__":
    # Create DB tables if they don’t exist yet
    with app.app_context():
        db.create_all()
    app.run(debug=True)
