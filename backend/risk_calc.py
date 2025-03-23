##################################################################################
# risk_calc.py
#
# Includes:
#   - Legacy aggregator logic
#   - Advanced aggregator (time-decayed, repeated severity, etc.)
#   - fetch_global_stats(): queries average scores and violation trends
#   - generate_extended_report(): multi-paragraph with bullet points, category analysis,
#       next steps, and benchmark comparisons.
##################################################################################

import random
import numpy as np
from collections import defaultdict
from models import db, RiskClassification, Violation

try:
    from regulatory_mapping import REGULATORY_MAPPING
except ImportError:
    REGULATORY_MAPPING = {}

###############################################################################
# CSV-based compute_fine
###############################################################################
def compute_fine(category, violation_type):
    if not REGULATORY_MAPPING or violation_type not in REGULATORY_MAPPING:
        return 0
    row = REGULATORY_MAPPING[violation_type]
    numeric_fines = []
    for off_str in row["offenses"]:
        try:
            val = int(off_str)
            numeric_fines.append(val)
        except ValueError:
            pass
    if not numeric_fines:
        return 0
    return random.choice(numeric_fines)

###############################################################################
# Full line-by-line violation_type_severity_map from your CSV (NO lines omitted)
###############################################################################
violation_type_severity_map = {
    # 1) Personal Hygiene & Health Violations
    "Failure to report contagious diseases among workers": 4,
    "Workers with open wounds not properly covered": 3,
    "Failure to properly wash hands, especially after different uses": 4,
    "Poor personal hygiene practices while working": 3,
    "Failure to maintain personal cleanliness (hair, nails, etc.)": 3,
    "Failure to wear clean work attire, gloves, or head coverings": 3,
    "Failure to provide valid health cards for workers": 3,

    # 2) Food Source & Quality Violations
    "Receiving, using, displaying, or selling food from unapproved sources or produced in unauthorized manners": 4,
    "Using prohibited or non-compliant materials in food production, or exceeding permissible limits for flavors, colors, or preservatives": 5,
    "Failure to verify food safety before delivery or receipt (due to contamination, spoilage, pests, expired shelf life, or incorrect storage temperature)": 4,
    "Failure to transfer food to the designated storage area immediately after receipt": 3,
    "Lack of a back door for food receipt and unloading (unsuitable receiving area)": 2,

    # 3) Food Preparation & Handling Violations
    "Incorrect thawing of food and refreezing meals multiple times": 5,
    "Failure to cook food at appropriate temperatures": 5,
    "Inadequate reheating and improper cooling of food": 5,
    "Improper handling and presentation of food, equipment, or utensils": 4,
    "Food preparation outside the designated premises or during maintenance": 4,
    "Processing or manufacturing pork and its derivatives inside the establishment, or failing to separate pork and its equipment from other products (for authorized establishments only)": 5,
    "Unauthorized personnel in kitchen or food preparation areas": 3,
    "Use of unwashed vegetables": 3,

    # 4) Cross-Contamination Violations
    "Using utensils, equipment, or surfaces for vegetables and ready-to-eat food after handling raw meat without proper cleaning": 5,
    "Using unclean utensils, equipment, towels, or surfaces": 4,
    "Storing raw food with ready-to-eat food": 5,
    "Handling ready-to-eat food with bare hands": 5,
    "Draining wastewater into food preparation sinks": 4,
    "Placing food under leaking pipes or sinks": 4,
    "Washing hands or equipment in food washing sinks": 3,
    "Lack of barriers at sinks to separate food washing from hand washing": 3,
    "Condensed water dripping onto food": 3,

    # 5) Temperature & Time Control Violations
    "Improper storage temperature for hot and cold food": 5,
    "Failure to store dry, refrigerated, and frozen food at the correct temperature": 5,
    "Lack of temperature measuring devices and temperature recording logs": 4,
    "Inefficient temperature control in the establishment, kitchen, or storage areas, and failure to operate air conditioning": 4,
    "Leaving perishable food at unsafe temperatures for more than 4 hours or storing cooked food for more than 48 hours": 5,

    # 6) Food Storage & Display Violations
    "Storing food in containers previously used for hazardous or toxic substances": 5,
    "Placing food in uncovered containers exposed to contamination": 4,
    "Storing food directly on the floor without shelves or platforms": 3,
    "Failure to maintain cleanliness of food items on shelves and improper cleaning of storage shelves": 3,
    "Failure to remove or withdraw unfit food products": 5,

    # 7) Equipment & Utensil Violations
    "Failure to provide equipment and tools that meet specifications and activity requirements": 3,
    "Equipment and tools are made of unsuitable materials, improperly installed, or difficult to maintain": 4,
    "Using unclean, broken, or improperly stored utensils and equipment that are not suitable for the activity": 4,
    "Using unclean or improperly stored towels and disposable containers": 3,
    "Water tanks, plumbing, and filters are unsuitable or do not meet specifications": 4,
    "Placing newspapers or cardboard on shelves or inside refrigerators": 2,
    "Improper installation or placement of gas cylinders": 2,

    # 8) Food Storage Facility Violations
    "Storage area is unclean, damp, disorganized, too small, or lacks platforms and shelves": 3,
    "Storing food with non-food items that negatively affect it, such as detergents and pesticides": 4,
    "Failure to properly isolate expired or unfit food within the establishment": 4,
    "Storing different types of food together improperly": 4,
    "Storing or keeping fruits and vegetables in unsuitable crates": 3,

    # 9) Unsafe Food Violations
    "Selling or providing unfit or spoiled food": 5,
    "Selling or displaying expired food": 5,
    "Selling or serving food contaminated with insects, solid residues, or chemicals": 5,
    "Selling or displaying adulterated food": 5,
    "Providing food that resulted in food poisoning": 5,
    "Selling or using bulging canned food, or food showing leakage or rust": 4,
    "Selling or distributing food found to contain contaminants through laboratory testing": 5,
    "Reusing leftover food": 4,

    # 10) Pest Control Violations
    "Presence of insects, rodents, or their waste in the establishment": 4,
    "Failure to install protective mesh on doors and windows or presence of openings around doors, windows, air conditioners, or water pipes": 3,
    "Failure to provide insect and rodent traps or improper maintenance of these devices": 3,
    "Failure to obtain or renew a certified pest control contract": 3,
    "Failure to provide a pesticide storage area or not meeting the required specifications": 4,
    "Unlicensed pest control companies or employing unqualified workers for pesticide application": 5,
    "Failure to use protective equipment when handling pesticides": 3,
    "Food contamination due to pesticide spraying": 5,
    "Selling, displaying, or using expired, unregistered, or banned pesticides": 5,
    "Unlicensed pest control companies conducting business": 5,
    "Failure to provide pesticide-related documents, safety data sheets, or ministry approval certificates": 3,

    # 11) Sanitation & Cleaning Violations
    "Failure to regularly clean floors, walls, and ceilings, and properly sanitize surfaces, equipment, utensils, and towels": 3,
    "Failure to clean floors, walls, and ceilings": 2,
    "Failure to maintain cleanliness in restrooms or waste collection areas": 3,
    "Failure to provide adequate cleaning agents, disinfectants, and cleaning tools or improper storage of these materials": 3,
    "Incorrect use of cleaning agents, disinfectants, or sanitizers": 2,
    "Absence of sanitizing solution in dishwashing machines or inadequate water temperature": 4,
    "Failure to provide temperature monitoring screens or sanitizer concentration test strips": 3,
    "Failure to clean water tanks or replace filters regularly": 3,
    "Use of unsuitable or uncovered trash bins": 2,
    "Failure to provide dedicated sinks for washing hands, utensils, vegetables, or meat": 3,

    # 12) Waste Disposal Violations
    "Failure to provide adequate space for waste collection": 3,
    "Improper disposal of liquid and solid waste": 3,
    "Sewage leakage from designated drainage areas": 4,
    "Blocked drainage pipe causing wastewater backup due to lack of maintenance": 3,
    "Failure to provide or maintain grease traps": 3,
    "Accumulation of waste, unused equipment, or overgrown vegetation inside or outside the establishment": 2,
    "Improper floor slope preventing efficient drainage": 2,
    "Dumping waste in public or unauthorized areas": 3,
    "Dumping or abandoning construction materials and debris in unauthorized locations": 4,

    # 13) Food Transport Violations
    "Operating a food distribution vehicle without a license": 3,
    "Food transport vehicle is unclean, unsuitable, or does not meet specifications": 3,
    "Failure to maintain cleanliness and safety of plastic crates used for dairy, bread, and juices": 3,
    "Transporting food together with non-food items such as detergents or chemicals, or failing to separate returned/expired items": 4,
    "Failure to maintain appropriate temperature for food transport, lack of a thermometer, or use of a defective thermometer": 4,
    "Failure to submit required food samples to the laboratory": 3,

    # 14) Establishment Structural Violations
    "Insufficient space in the kitchen, lack of storage rooms or changing areas": 2,
    "Failure to maintain the establishment or non-compliance of decor with health regulations": 3,
    "Conducting maintenance or modifications without approval from the relevant authorities": 3,
    "Using the premises as a residence or having sleeping areas not separated from food preparation areas": 4,
    "Doors are not properly sealed or securely installed": 2,
    "Leaving front or back doors open, auto-closing doors not functioning, or absence of air curtains": 2,
    "Inadequate lighting and ventilation or unprotected light fixtures": 2,
    "Failure to provide grease traps or appropriate exhaust systems": 3,
    "Lack of clean and suitable hot or cold water supply for operations or ice from unapproved sources": 3,
    "Failure to provide adequate sanitary facilities": 2,
    "Failure to provide a designated sink for washing hands, food, or utensils": 3,
    "Keeping animals inside food establishments": 4,

    # 15) Food Packaging & Labeling Violations
    "Incomplete food label, incorrect production/expiration dates, or missing health instructions": 3,
    "Packing, distributing, or selling food in unauthorized or non-compliant containers": 3,
    "Removing, altering, or replacing production and expiration date labels": 4,
    "Repackaging food without authorization and without proper food labeling": 3,
    "Using newspapers or printed materials for food storage or wrapping": 2,
    "Packing and distributing drinking water in containers belonging to other companies": 3,
    "Failure to include expiration date or food label on stored or displayed food": 2,

    # 16) General Regulatory Violations
    "Failure to obtain or renew required training certificates for responsible personnel or workers": 2,
    "Failure to provide required documents (business license, health cards, inspection records, training certificates, etc.)": 2,
    "Failure to display 'No Smoking' signs": 2,
    "Smoking inside the establishment": 3,
    "Failure to cooperate with or show respect to the inspecting officer": 4,
    "Food products under special promotions must have a minimum shelf life of one month": 3,
    "Displaying or selling goods on sidewalks or outside designated areas": 2,
    "Using non-compliant or defective weighing scales": 2,
    "Failure to cover transport vehicles carrying goods": 2,
    "Collecting scrap, waste, or boxes without a permit (subject to confiscation)": 2,
    "Selling banned or non-compliant non-food products": 3,
    "Selling hazardous toys, fireworks, or prohibited products": 4
}

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

###############################################################################
# Legacy placeholders
###############################################################################
def compute_weighted_risk(total_violations, total_fines, violation_frequency, average_severity):
    impact = (total_fines / total_violations) * average_severity if total_violations else 0
    raw_score = violation_frequency * impact
    return raw_score / 1000

def compute_aggregated_risk(violation_frequency, average_fine, average_severity, violation_timestamps, risk_modifier):
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
        sorted_keys = sorted(month_counts.keys())
        counts = [month_counts[k] for k in sorted_keys]
        if len(counts) < 2:
            trend_risk = 0.0
        else:
            x = list(range(len(counts)))
            mean_x = sum(x) / len(x)
            mean_y = sum(counts) / len(counts)
            numerator = sum(x[i]*counts[i] for i in range(len(x))) - len(x)*mean_x*mean_y
            denominator = sum((xx - mean_x)**2 for xx in x)
            slope = numerator / denominator if denominator else 0
            slope = max(slope, 0.0)
            trend_risk = slope * 2

    base_score = freq_risk * 0.4 + imp_risk * 0.4 + trend_risk * 0.2
    return base_score * risk_modifier, freq_risk, imp_risk, trend_risk

###############################################################################
# Repeated category factor
###############################################################################
def compute_repeated_category_factor(cat_timestamps, days_window=60):
    if not cat_timestamps:
        return 0.0
    latest_time = max(ts for _, ts in cat_timestamps)
    cutoff = latest_time - np.timedelta64(days_window, 'D')
    cat_counts = defaultdict(int)
    for (cat, ctime) in cat_timestamps:
        if ctime >= cutoff:
            cat_counts[cat] += 1
    repeated_factor = 0.0
    for c, count in cat_counts.items():
        if count > 2:
            repeated_factor += 0.05
    return min(repeated_factor, 0.3)

###############################################################################
# Enhanced aggregator
###############################################################################
def compute_risk_score_enhanced(violations, business_type):
    """
    Already described advanced aggregator with repeated severity, time-decay, open penalty, etc.
    """
    if not violations:
        return 0.0

    total_decayed_fines = 0.0
    severities = []
    violation_timestamps = []
    cat_timestamps = []
    open_violation_penalty = 0.0

    for v in violations:
        total_decayed_fines += v["decayed_fine"]
        severities.append(v["effective_severity"])
        violation_timestamps.append(v["timestamp"])
        cat_timestamps.append((v["category"], np.datetime64(v["timestamp"])))
        if v["status"] == "Open" and v["days_since"] > 30:
            open_violation_penalty += 0.02

    total_violations = len(violations)
    avg_sev = sum(severities) / len(severities)

    min_ts = min(violation_timestamps)
    max_ts = max(violation_timestamps)
    total_days = (max_ts - min_ts).days if max_ts > min_ts else 1
    months_in_period = total_days / 30.0 if total_days > 0 else 1.0

    lamda = total_violations / months_in_period
    freq_risk = 1 - np.exp(-lamda)
    average_decayed_fine = total_decayed_fines / total_violations
    fine_norm = min(average_decayed_fine / 10000.0, 1.0)
    sev_norm = min(avg_sev / 5.0, 1.0)
    imp_risk = 0.5 * fine_norm + 0.5 * sev_norm

    month_counts = defaultdict(int)
    for t in violation_timestamps:
        k = t.strftime("%Y-%m")
        month_counts[k] += 1
    sorted_keys = sorted(month_counts.keys())
    counts = [month_counts[k] for k in sorted_keys]
    if len(counts) < 2:
        trend_risk = 0.0
    else:
        x = list(range(len(counts)))
        mean_x = sum(x) / len(x)
        mean_y = sum(counts) / len(counts)
        numerator = sum(x[i]*counts[i] for i in range(len(x))) - len(x)*mean_x*mean_y
        denominator = sum((xx - mean_x)**2 for xx in x)
        slope = numerator / denominator if denominator else 0
        slope = max(slope, 0.0)
        trend_risk = min(slope / 5.0, 1.0)

    repeated_factor = compute_repeated_category_factor(cat_timestamps, 60)

    base_score = freq_risk * 0.4 + imp_risk * 0.4 + trend_risk * 0.2
    base_score += repeated_factor
    base_score += open_violation_penalty

    prof = industry_profiles.get(business_type, {"compliance_factor": 1.0, "impact_factor": 1.0})
    industry_mod = (prof["compliance_factor"] + prof["impact_factor"]) / 2.0
    final_score = base_score * industry_mod
    final_score *= 1.25

    return final_score

###############################################################################
# Classification logic (user sets their own thresholds)
###############################################################################
def classify_risk(score):
    # Example: Above 2 => High, above 1 => Medium, else Low
    if score >= 2.0:
        return "High"
    elif score >= 1.0:
        return "Medium"
    else:
        return "Low"

###############################################################################
# A helper: fetch global stats for benchmarking & trend
###############################################################################
def fetch_global_stats(business_type):
    """
    - Averages across all businesses:
      * global_avg_score
      * count
    - Averages across same business_type
      * industry_avg_score
      * count
    - 6-month vs previous 6-month violation counts
    """
    global_data = db.session.query(
        db.func.avg(RiskClassification.advanced_risk_score),
        db.func.count(RiskClassification.id)
    ).all()
    global_avg = global_data[0][0] if global_data else 0.0
    global_count = global_data[0][1] if global_data else 0

    industry_data = db.session.query(
        db.func.avg(RiskClassification.advanced_risk_score),
        db.func.count(RiskClassification.id)
    ).filter(RiskClassification.business_type == business_type).all()
    industry_avg = industry_data[0][0] if industry_data else 0.0
    industry_count = industry_data[0][1] if industry_data else 0

    last_6_start = db.func.date(db.func.datetime('now','-6 months'))
    prior_6_start = db.func.date(db.func.datetime('now','-12 months'))

    last6_count = db.session.query(db.func.count(Violation.id)).filter(
        Violation.timestamp >= last_6_start
    ).scalar()
    prior6_count = db.session.query(db.func.count(Violation.id)).filter(
        Violation.timestamp < last_6_start,
        Violation.timestamp >= prior_6_start
    ).scalar()

    result_dict = {
        "global_avg_score": global_avg if global_avg else 0.0,
        "global_count": global_count,
        "industry_avg_score": industry_avg if industry_avg else 0.0,
        "industry_count": industry_count,
        "last6_violations": last6_count if last6_count else 0,
        "prior6_violations": prior6_count if prior6_count else 0
    }
    return result_dict

###############################################################################
# Extended multi-paragraph generator (new optional open_count, closed_count)
###############################################################################
def generate_extended_report(
    business_name,
    final_score,
    risk_level,
    top_categories,
    repeated_offenders,
    total_violations,
    last_violation_date,
    business_type,
    global_stats,
    open_count=0,
    closed_count=0
):
    """
    Creates a structured multi-paragraph report including:
      - Overall Risk Assessment
      - Categories & Repeated Offenses
      - Benchmarks & Trends
      - Next Steps / Recommendations
      - Conclusion
      - (Optional) mention open vs closed ratio if open_count + closed_count > 0
    """

    # If you had "PARAGRAPH 1/2/3" references, we comment them out, not remove them:
    # e.g. # "PARAGRAPH 1: Overall Risk Assessment"

    global_avg = global_stats["global_avg_score"]
    industry_avg = global_stats["industry_avg_score"]
    last6 = global_stats["last6_violations"]
    prior6 = global_stats["prior6_violations"]

    if prior6 > 0:
        global_trend_ratio = (last6 - prior6) / prior6
    else:
        global_trend_ratio = 0.0

    intro_lines = []
    if final_score >= 3.0:
        intro_lines.append(
            f"Business '{business_name}' exhibits an extremely concerning level of risk, with a final advanced risk score of {final_score:.2f}. "
            "Immediate and drastic corrective measures are strongly advised."
        )
    elif final_score >= 2.0:
        intro_lines.append(
            f"Business '{business_name}' has a HIGH risk score of {final_score:.2f}, "
            "placing it well above standard compliance thresholds."
        )
    elif final_score >= 1.0:
        intro_lines.append(
            f"Business '{business_name}' falls into the MEDIUM risk category, with a final score of {final_score:.2f}. "
            "Further improvements are recommended."
        )
    else:
        intro_lines.append(
            f"Business '{business_name}' demonstrates a LOW overall risk, scoring {final_score:.2f}. "
            "This indicates a generally good level of compliance."
        )

    if (open_count + closed_count) > 0:
        ratio_str = f"{open_count} open vs. {closed_count} closed"
        intro_lines.append(
            f"Currently, there are {ratio_str} violations on record."
        )

    intro_paragraph = " ".join(intro_lines)

    cat_lines = []
    if top_categories:
        cat_lines.append("Key violation categories observed for this business include:")
        for cat_name, cat_count in top_categories:
            cat_lines.append(f" • {cat_name} with {cat_count} recorded instances.")
    else:
        cat_lines.append("No distinct major violation categories were identified.")

    cat_commentary = "\n".join(cat_lines)

    if repeated_offenders:
        joined = ", ".join(repeated_offenders)
        repeated_line = (
            f"In addition, the following categories were repeated more than twice in the past 60 days: {joined}, "
            "significantly raising the business's risk profile."
        )
    else:
        repeated_line = "No single category was repeatedly violated beyond normal thresholds in recent months."

    bench_paragraphs = []
    if industry_avg > 0:
        if final_score > industry_avg:
            bench_paragraphs.append(
                f"This business's score of {final_score:.2f} exceeds the average risk score of {industry_avg:.2f} for the '{business_type}' industry, "
                "indicating above-average compliance concerns."
            )
        else:
            bench_paragraphs.append(
                f"This business's score of {final_score:.2f} is below the '{business_type}' industry average of {industry_avg:.2f}, "
                "suggesting comparatively stronger compliance than many peers."
            )
    else:
        bench_paragraphs.append(
            f"Industry-specific benchmarking data for '{business_type}' is unavailable or insufficient."
        )

    if global_avg > 0:
        if final_score > global_avg:
            bench_paragraphs.append(
                f"Compared to the global average advanced risk score of {global_avg:.2f} across all businesses, "
                "this business ranks higher, warranting closer monitoring."
            )
        else:
            bench_paragraphs.append(
                f"Relative to the global average advanced risk score of {global_avg:.2f}, "
                "this business appears to maintain a safer compliance profile."
            )
    else:
        bench_paragraphs.append("Global benchmarking data is insufficient to draw further comparisons.")

    if global_trend_ratio > 0.2:
        trend_comment = (
            f"Overall violations globally increased by about {global_trend_ratio*100:.1f}% in the last 6 months compared to the prior period. "
            "Administrators should be aware of a broader rising trend across all businesses."
        )
    elif global_trend_ratio > 0.0:
        trend_comment = (
            f"A minor global increase of {global_trend_ratio*100:.1f}% in violations was observed in the last 6 months, "
            "though this may not significantly impact individual risk ratings."
        )
    elif global_trend_ratio < -0.1:
        trend_comment = (
            f"Interestingly, global violations decreased by roughly {-global_trend_ratio*100:.1f}% over the last 6 months, "
            "indicating a potential improvement in overall compliance across the region."
        )
    else:
        trend_comment = "Global violation counts remained relatively stable over the past 6 months."

    benchmark_text = " ".join(bench_paragraphs)

    suggestions = [
        "Ensure repeated categories are addressed via targeted staff training and periodic internal audits.",
        "Review any open or unresolved violations older than 30 days and expedite corrective actions.",
        "Consider specialized inspections focusing on high-severity categories (if any).",
        "Maintain thorough documentation of compliance improvements to reduce future penalties."
    ]
    if risk_level == "High":
        suggestions.append("Schedule an immediate comprehensive re-inspection within 2 weeks.")
        suggestions.append("Engage external consultants if necessary to handle systemic compliance failures.")
    elif risk_level == "Medium":
        suggestions.append("Perform a follow-up internal check within 30 days to verify improved compliance.")
    else:
        suggestions.append("Continue routine inspections to maintain this strong compliance posture.")

    next_steps_lines = [f" • {step}" for step in suggestions]
    next_steps_str = "\n".join(next_steps_lines)

    conclusion_text = (
        "We strongly recommend addressing the listed categories promptly and following the above steps to minimize risk. "
        "Compliance improvements not only reduce fines but also help sustain a safer, more reputable operation."
    )

    full_report = f"""
OVERALL RISK ASSESSMENT
{intro_paragraph}

CATEGORIES & REPEATED OFFENSES
{cat_commentary}
{repeated_line}

BENCHMARKS & TRENDS
{benchmark_text}
{trend_comment}

NEXT STEPS / RECOMMENDATIONS:
{next_steps_str}

CONCLUSION:
{conclusion_text}
""".strip()

    return full_report

def generate_insight(business_name, total_violations, active_period, average_fine,
                     average_severity, violation_frequency, freq_risk, imp_risk,
                     trend_risk, final_score, repeated_offenders=None):
    """
    This is the older standard 'generate_insight' used by seed.py for backward compatibility.
    It's overshadowed by the new 'generate_extended_report', but we keep it to avoid code breaks.
    """
    if freq_risk >= imp_risk and freq_risk >= trend_risk:
        dominant = "frequency"
        dominant_phrase = "a persistently high rate of recurring non-compliance"
    elif imp_risk >= freq_risk and imp_risk >= trend_risk:
        dominant = "impact"
        dominant_phrase = "the significant adverse effects each violation imposes on operations and finances"
    else:
        dominant = "trend"
        dominant_phrase = "a worrying upward trend in violations over recent months"

    rlevel = classify_risk(final_score)

    templates = {
        "High": {
            "frequency": [
                f"Business '{business_name}' has a high level of repeated violations. Score={final_score:.2f}."
            ],
            "impact": [
                f"'{business_name}' is incurring serious fines. Score={final_score:.2f}."
            ],
            "trend": [
                f"A strong upward trend of violations at '{business_name}'. Score={final_score:.2f}."
            ]
        },
        "Medium": {
            "frequency": [
                f"'{business_name}' sees moderately frequent issues. Score={final_score:.2f}."
            ],
            "impact": [
                f"'{business_name}' experiences moderate financial strain from violations. Score={final_score:.2f}."
            ],
            "trend": [
                f"Moderate upward trend at '{business_name}'. Score={final_score:.2f}."
            ]
        },
        "Low": {
            "default": [
                f"'{business_name}' has low risk overall. Score={final_score:.2f}."
            ]
        }
    }
    if rlevel == "Low":
        return templates["Low"]["default"][0]
    cat_templates = templates[rlevel]
    if dominant in cat_templates:
        return cat_templates[dominant][0]
    return "Basic risk insight."
