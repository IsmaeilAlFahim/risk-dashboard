##################################################################################
# seed.py
#
# Seeds the DB with advanced aggregator + new extended commentary from generate_extended_report()
# + multi-step violation_status_history table creation & seeding.
# 
# NO lines omitted, includes full expansions, advanced logic, multi-step statuses, etc.
##################################################################################

import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict

from models import db, Violation, RiskClassification
from risk_calc import (
    compute_fine,
    violation_type_severity_map,
    compute_risk_score_enhanced,
    classify_risk,
    compute_aggregated_risk,
    compute_weighted_risk,
    generate_insight,            # older simpler
    fetch_global_stats,          # new for benchmarking/trends
    generate_extended_report     # new multi-paragraph commentary
)

# NEW: import text for raw SQL
from sqlalchemy import text

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
file_path = os.path.join(BASE_DIR, "Violations_Dataset.csv")
if os.path.isfile(file_path):
    df = pd.read_csv(file_path)
    # Group the dataset by Category for random pick
    violation_data = df.groupby("Category")["Violation Type"].apply(list).to_dict()
else:
    violation_data = {}

def get_violation_count():
    # Probability distribution for how many violations each business might have
    p = random.random()
    if p < 0.05:
        return random.randint(60, 90)
    elif p < 0.25:
        return random.randint(20, 49)
    elif p < 0.50:
        return random.randint(6, 15)
    elif p < 0.98:
        return random.randint(1, 5)
    else:
        return 0

INSPECTION_NOTES = [
    "Routine inspection completed successfully.",
    "Moderate issues found—re-inspection scheduled soon.",
    "Follow-up needed after repeated non-compliance.",
    "Partial compliance improvement observed.",
    "Extensive check done, some areas still lacking."
]
def get_inspection_note():
    return random.choice(INSPECTION_NOTES)

def determine_industry_label(score):
    # user logic: above 2 => high, above 1 => med, else low
    if score >= 2.0:
        return "High"
    elif score >= 1.0:
        return "Medium"
    else:
        return "Low"

def get_business_info(business_name):
    low = business_name.lower()
    if "seafood" in low:
        return {"business_type": "Restaurant", "location": "Harbor District", "description": "Renowned for fresh seafood."}
    elif "trading" in low:
        return {"business_type": "Retail", "location": "Market Street", "description": "Reputable trading entity."}
    elif "bank" in low or "financial" in low or "capital" in low:
        return {"business_type": "Financial", "location": "Downtown", "description": "Financial & investment services."}
    elif "medical" in low or "hospital" in low or "pharmacy" in low:
        return {"business_type": "Healthcare", "location": "Downtown", "description": "Healthcare & diagnostics center."}
    elif "bakery" in low:
        return {"business_type": "Bakery", "location": "Residential Area", "description": "Artisan baked goods daily."}
    elif "auto" in low:
        return {"business_type": "Automotive", "location": "Suburban Zone", "description": "Auto repairs & servicing."}
    elif "logistics" in low:
        return {"business_type": "Logistics", "location": "Industrial Area", "description": "Transport & warehousing."}
    elif "furniture" in low:
        return {"business_type": "Home Goods", "location": "Retail Park", "description": "Quality furniture & décor."}
    elif "dairy" in low:
        return {"business_type": "Agriculture", "location": "Rural District", "description": "Farm-fresh dairy products."}
    elif "hardware" in low:
        return {"business_type": "Hardware", "location": "Industrial Area", "description": "Tools & building supplies."}
    elif "catering" in low:
        return {"business_type": "Food Service", "location": "Commercial District", "description": "Events catering solutions."}
    elif "coffee" in low:
        return {"business_type": "Food Service", "location": "Downtown", "description": "Cozy coffee & pastries."}
    elif "electronics" in low:
        return {"business_type": "Electronics", "location": "Industrial Area", "description": "Gadgets & tech solutions."}
    elif "construction" in low:
        return {"business_type": "Real Estate", "location": "Industrial Area", "description": "Building & infrastructure."}
    elif "food court" in low:
        return {"business_type": "Food Service", "location": "Downtown", "description": "Diverse food court."}
    elif "florist" in low:
        return {"business_type": "Retail", "location": "Downtown", "description": "Floral arrangements & bouquets."}
    elif "investment" in low:
        return {"business_type": "Financial", "location": "Downtown", "description": "Wealth & portfolio management."}
    elif "jewelry" in low:
        return {"business_type": "Retail", "location": "Downtown", "description": "Fine gems & accessories."}
    elif "food" in low or "souk" in low:
        return {"business_type": "Retail", "location": "Downtown", "description": "Bustling marketplace."}
    return {"business_type": "General Business", "location": "City Center", "description": "Versatile business operation."}

################################################################################
# Original + expanded business list (no omissions)
################################################################################
original_business_list = [
    "Fujairah Seafood Restaurant","Emirates Trading Co.","Fujairah Souk Supermarket",
    "Al Hamra Electronics","Gulf Construction Supplies","Fujairah General Hospital",
    "Sunrise Bakery","Blue Ocean Seafood","Al Faseel Trading","Coastal Fresh Foods",
    "Fujairah Textile Mills","Pearl Jewelry","Marina Leisure Center","Emirates Hardware",
    "Fujairah Dairy Farm","Golden Date Establishment","Al Noor Bookstore",
    "Fujairah Medical Clinic","Royal Motors","Fujairah IT Solutions","Desert Wind Apparel",
    "Oasis Furniture","Harbor View Restaurant","Al Jazeera Trading","Blue Horizon Catering"
]

# Full 400 expansions below (no lines removed)
expanded_business_list = [
    # ---------------- SEAFOOD (20) ----------------
    "Al Falaj Seafood Shack",
    "Marina Pearl Seafood",
    "Harbor Catch Seafood",
    "Al Bahr Seafood House",
    "Mina Coast Seafood",
    "Fujairah Wave Seafood",
    "Umbaqain Seafood Cafe",
    "Sakamkam Seafood Delight",
    "FishNet Seafood Delights",
    "Rawdah Seafood Station",
    "Mirbah Seafood Supply",
    "Rugaylat Seafood Express",
    "Dibba Bay Seafood Outlet",
    "Murbeh Seafood Platter",
    "Al Halfa Seafood Kitchen",
    "Qidfa Seafood Corner",
    "Al Ramlah Seafood Spot",
    "Habhab Seafood & Grill",
    "Al Bidyah Seafood Hub",
    "Al Usfar Seafood Cuisine",

    # ---------------- TRADING (20) ----------------
    "Al Falaj Trading Co.",
    "Marina Pearl Trading",
    "Harbor Catch Trading",
    "Al Bahr Trading House",
    "Mina Coast Trading",
    "Fujairah Wave Trading",
    "Umbaqain Trading Enterprise",
    "Sakamkam Trading Hub",
    "Al Shariah General Trading",
    "Rawdah World Trading",
    "Mirbah International Trading",
    "Rugaylat Unified Trading",
    "Dibba Bay Global Trading",
    "Murbeh Multi-Trading",
    "Al Halfa Gulf Trading",
    "Qidfa Advanced Trading",
    "Al Ramlah Mega Trading",
    "Habhab Cross-Border Trading",
    "Al Bidyah Commerce",
    "Al Usfar Grand Trading",

    # ---------------- SOUK (20) ----------------
    "Al Falaj Souk Center",
    "Marina Pearl Souk",
    "Harbor Catch Souk",
    "Mina Coast Souk",
    "Sakamkam Retail Souk",
    "Rawdah Bazaar Souk",
    "Mirbah Downtown Souk",
    "Rugaylat Cultural Souk",
    "Murbeh Heritage Souk",
    "Al Halfa Modern Souk",
    "Qidfa Vibrant Souk",
    "Al Ramlah Market Souk",
    "Habhab Old Souk",
    "Al Bidyah Traditional Souk",
    "Umbaqain Urban Souk",
    "Fujairah Wave Souk",
    "Dibba Bay Souk District",
    "Al Bahr Souk Pavilion",
    "Coastal Fresh Souk",
    "Al Usfar Marketplace Souk",

    # ---------------- ELECTRONICS (20) ----------------
    "Al Falaj Electronics Mart",
    "Marina Pearl Electronics",
    "Harbor Catch Electronics",
    "Al Bahr Tech Electronics",
    "Mina Coast Electronics",
    "Fujairah Wave Electronics",
    "Umbaqain Tech Store",
    "Sakamkam Electronic Hub",
    "Rawdah Digital Solutions",
    "Mirbah Electronic Outlet",
    "Rugaylat Circuit City",
    "Dibba Bay Gadget Zone",
    "Murbeh Smart Electronics",
    "Al Halfa Digital Systems",
    "Qidfa Tech Innovations",
    "Al Ramlah Electronics Depot",
    "Habhab Tech Market",
    "Al Bidyah E-Devices",
    "Umbaqain Circuit World",
    "Al Usfar TechPoint",

    # ---------------- CONSTRUCTION (20) ----------------
    "Al Falaj Construction",
    "Marina Pearl Construction",
    "Harbor Catch Construction",
    "Al Bahr Builders",
    "Mina Coast Construction",
    "Fujairah Wave Builders",
    "Umbaqain Construction Co.",
    "Sakamkam Engineering Works",
    "Rawdah Infrastructure",
    "Mirbah Industrial Build",
    "Rugaylat Urban Projects",
    "Dibba Bay Construct",
    "Murbeh Modern Builders",
    "Al Halfa Civil Works",
    "Qidfa Structural Innovations",
    "Al Ramlah Development LLC",
    "Habhab Real Estate Construction",
    "Al Bidyah Infra Solutions",
    "Umbaqain Civil Projects",
    "Al Usfar Building Solutions",

    # ---------------- HOSPITAL (20) ----------------
    "Al Falaj General Hospital",
    "Marina Pearl Hospital",
    "Harbor Catch Hospital",
    "Al Bahr Healthcare",
    "Mina Coast Hospital",
    "Fujairah Wave Hospital",
    "Umbaqain Medical Center",
    "Sakamkam Care Hospital",
    "Rawdah City Hospital",
    "Mirbah Advanced Healthcare",
    "Rugaylat Specialty Hospital",
    "Dibba Bay Medical Center",
    "Murbeh Community Hospital",
    "Al Halfa Regional Hospital",
    "Qidfa Comprehensive Hospital",
    "Al Ramlah Medical Institute",
    "Habhab Hospital & Clinic",
    "Al Bidyah Primary Hospital",
    "Umbaqain Family Hospital",
    "Al Usfar Infirmary",

    # ---------------- FOOD COURT (20) ----------------
    "Al Falaj Food Court",
    "Marina Pearl Food Court",
    "Harbor Catch Food Court",
    "Al Bahr Dining Court",
    "Mina Coast Culinary Court",
    "Fujairah Wave Food Plaza",
    "Umbaqain Food Hub",
    "Sakamkam Eateries Court",
    "Rawdah Family Food Court",
    "Mirbah Gourmet Court",
    "Rugaylat Tastes Court",
    "Dibba Bay Cuisine Court",
    "Murbeh Flavors Court",
    "Al Halfa Dining Arena",
    "Qidfa Food Center",
    "Al Ramlah Food Haven",
    "Habhab Quick Bites Court",
    "Al Bidyah Food Deck",
    "Umbaqain Meal Zone",
    "Al Usfar Culinary Space",

    # ---------------- AUTO (20) ----------------
    "Al Falaj Auto Center",
    "Marina Pearl Auto Services",
    "Harbor Catch Auto Repairs",
    "Al Bahr Automotive",
    "Mina Coast Auto Clinic",
    "Fujairah Wave Auto Shop",
    "Umbaqain Auto Solutions",
    "Sakamkam Motors",
    "Rawdah Car Care",
    "Mirbah Vehicle Services",
    "Rugaylat Auto Tune",
    "Dibba Bay Mechanics",
    "Murbeh Auto Garage",
    "Al Halfa Car Fix",
    "Qidfa Drive Services",
    "Al Ramlah Motor Hub",
    "Habhab Car Workshop",
    "Al Bidyah Auto Tech",
    "Umbaqain Auto Depot",
    "Al Usfar Auto Zone",

    # ---------------- BAKERY (20) ----------------
    "Al Falaj Artisan Bakery",
    "Marina Pearl Bakery",
    "Harbor Catch Bakery",
    "Al Bahr Bread House",
    "Mina Coast Bakery",
    "Fujairah Wave Artisan Bakes",
    "Umbaqain Bake & Cafe",
    "Sakamkam Sweet Breads",
    "Rawdah Daily Bakery",
    "Mirbah Fresh Bakes",
    "Rugaylat Oven Delights",
    "Dibba Bay Pastry Co.",
    "Murbeh Sunrise Bakery",
    "Al Halfa Dough & More",
    "Qidfa Bakery & Sweets",
    "Al Ramlah Breadworks",
    "Habhab Village Bakery",
    "Al Bidyah Baking Co.",
    "Umbaqain Gourmet Bakery",
    "Al Usfar Pastry Station",

    # ---------------- JEWELRY (20) ----------------
    "Al Falaj Jewelry",
    "Marina Pearl Jewelry",
    "Harbor Catch Jewelers",
    "Al Bahr Gemstones",
    "Mina Coast Jewels",
    "Fujairah Wave Jewels",
    "Umbaqain Gold & Diamonds",
    "Sakamkam Bridal Jewelry",
    "Rawdah Precious Stones",
    "Mirbah Fine Jewelry",
    "Rugaylat Luxury Jewels",
    "Dibba Bay Silver & Gold",
    "Murbeh Ornamental Crafts",
    "Al Halfa Diamond House",
    "Qidfa Gem Boutique",
    "Al Ramlah Royal Jewelry",
    "Habhab Vintage Jewels",
    "Al Bidyah Gem Collections",
    "Umbaqain Classic Gems",
    "Al Usfar Jewel Haven",

    # ---------------- COFFEE (20) ----------------
    "Al Falaj Coffee House",
    "Marina Pearl Coffee",
    "Harbor Catch Coffee",
    "Al Bahr Cafe & Coffee",
    "Mina Coast Coffee Bar",
    "Fujairah Wave Cafe",
    "Umbaqain Espresso Spot",
    "Sakamkam Coffee Roasters",
    "Rawdah Mocha Lounge",
    "Mirbah Coffee Haven",
    "Rugaylat Beans & Brews",
    "Dibba Bay Coffee Corner",
    "Murbeh Latte Place",
    "Al Halfa Arabica Brew",
    "Qidfa Coffee Roast",
    "Al Ramlah Java Cafe",
    "Habhab Daily Coffee",
    "Al Bidyah Coffee & Co.",
    "Umbaqain Brew Station",
    "Al Usfar Roast & Sip",

    # ---------------- MEDICAL (20) ----------------
    "Al Falaj Medical Clinic",
    "Marina Pearl Medical Center",
    "Harbor Catch Medical Clinic",
    "Al Bahr Medical Hub",
    "Mina Coast Medical Solutions",
    "Fujairah Wave Medical Practice",
    "Umbaqain Health Clinic",
    "Sakamkam Medical Diagnostics",
    "Rawdah Health & Care",
    "Mirbah Medical Facility",
    "Rugaylat Health Services",
    "Dibba Bay Medical Checkup",
    "Murbeh Primary Medical",
    "Al Halfa Med Clinic",
    "Qidfa Healthcare Center",
    "Al Ramlah Family Medical",
    "Habhab Community Clinic",
    "Al Bidyah Medical Suite",
    "Umbaqain Physician Group",
    "Al Usfar Treatment Clinic",

    # ---------------- INVESTMENT (20) ----------------
    "Al Falaj Investment Group",
    "Marina Pearl Investments",
    "Harbor Catch Investment Corp",
    "Al Bahr Investment House",
    "Mina Coast Investment",
    "Fujairah Wave Investment",
    "Umbaqain Wealth Invest",
    "Sakamkam Capital Invest",
    "Rawdah Equity Investments",
    "Mirbah Growth Investments",
    "Rugaylat Investment Portfolio",
    "Dibba Bay Venture Group",
    "Murbeh Invest Strategies",
    "Al Halfa Market Investments",
    "Qidfa Future Invest",
    "Al Ramlah Prosperity Fund",
    "Habhab Strategic Investments",
    "Al Bidyah Stock & Shares",
    "Umbaqain Financial Invest",
    "Al Usfar Capital Ventures",

    # ---------------- CAPITAL (20) ----------------
    "Al Falaj Capital",
    "Marina Pearl Capital",
    "Harbor Catch Capital",
    "Al Bahr Capital Advisors",
    "Mina Coast Capital",
    "Fujairah Wave Capital Fund",
    "Umbaqain Capital Partners",
    "Sakamkam Capital Holdings",
    "Rawdah Capital Solutions",
    "Mirbah Capital Ventures",
    "Rugaylat Capital Growth",
    "Dibba Bay Capital Estate",
    "Murbeh Capital Management",
    "Al Halfa Capital Assets",
    "Qidfa Capital Investments",
    "Al Ramlah Capital Trading",
    "Habhab Global Capital",
    "Al Bidyah Capital Markets",
    "Umbaqain Premier Capital",
    "Al Usfar Capital Group",

    # ---------------- BANK (20) ----------------
    "Al Falaj Bank",
    "Marina Pearl Bank",
    "Harbor Catch Bank",
    "Al Bahr Savings Bank",
    "Mina Coast Bank",
    "Fujairah Wave Bank",
    "Umbaqain Bank & Trust",
    "Sakamkam Banking Corp",
    "Rawdah National Bank",
    "Mirbah Commerce Bank",
    "Rugaylat Banking Group",
    "Dibba Bay Bank",
    "Murbeh Financial Bank",
    "Al Halfa Secure Bank",
    "Qidfa Deposit Bank",
    "Al Ramlah City Bank",
    "Habhab Credit Bank",
    "Al Bidyah Central Bank",
    "Umbaqain Cooperative Bank",
    "Al Usfar Banking House",

    # ---------------- LOGISTICS (20) ----------------
    "Al Falaj Logistics",
    "Marina Pearl Logistics",
    "Harbor Catch Logistics",
    "Al Bahr Freight & Logistics",
    "Mina Coast Cargo Logistics",
    "Fujairah Wave Logistics",
    "Umbaqain Supply Chain",
    "Sakamkam Transport & Logistics",
    "Rawdah Warehousing Logistics",
    "Mirbah Distribution Network",
    "Rugaylat Logistics Services",
    "Dibba Bay Shipping",
    "Murbeh Forwarding Logistics",
    "Al Halfa Bulk Transport",
    "Qidfa Transit Solutions",
    "Al Ramlah Logistics Hub",
    "Habhab Freight Systems",
    "Al Bidyah Global Logistics",
    "Umbaqain Express Cargo",
    "Al Usfar Freight Lines",

    # ---------------- FURNITURE (20) ----------------
    "Al Falaj Furniture",
    "Marina Pearl Furniture",
    "Harbor Catch Furniture",
    "Al Bahr Home Furnishings",
    "Mina Coast Furnish Decor",
    "Fujairah Wave Furniture",
    "Umbaqain Interior Furnishings",
    "Sakamkam Living Furniture",
    "Rawdah Decor & Furniture",
    "Mirbah Furniture Designs",
    "Rugaylat Modern Furniture",
    "Dibba Bay Home Goods",
    "Murbeh Stylish Furniture",
    "Al Halfa Furnishing House",
    "Qidfa Furniture Mart",
    "Al Ramlah Furniture Studio",
    "Habhab Wood & Furnishings",
    "Al Bidyah Interior Solutions",
    "Umbaqain Sofas & More",
    "Al Usfar Furniture Store",

    # ---------------- DAIRY (20) ----------------
    "Al Falaj Dairy Farm",
    "Marina Pearl Dairy",
    "Harbor Catch Dairy Products",
    "Al Bahr Fresh Dairy",
    "Mina Coast Dairy Supplies",
    "Fujairah Wave Dairy",
    "Umbaqain Milk & Dairy",
    "Sakamkam Dairy Distributors",
    "Rawdah Cow Farm Dairy",
    "Mirbah Creamery",
    "Rugaylat Pure Dairy",
    "Dibba Bay Dairy Company",
    "Murbeh Cheese & Dairy",
    "Al Halfa Dairy Production",
    "Qidfa Organic Dairy",
    "Al Ramlah Dairy & Cattle",
    "Habhab Yogurt & Dairy",
    "Al Bidyah Farm Fresh Dairy",
    "Umbaqain Dairy & Livestock",
    "Al Usfar Dairy Holdings",

    # ---------------- HARDWARE (20) ----------------
    "Al Falaj Hardware",
    "Marina Pearl Hardware",
    "Harbor Catch Hardware",
    "Al Bahr Tools & Hardware",
    "Mina Coast DIY Hardware",
    "Fujairah Wave Hardware",
    "Umbaqain Industrial Hardware",
    "Sakamkam Builders Hardware",
    "Rawdah Handy Hardware",
    "Mirbah Warehouse Hardware",
    "Rugaylat Quality Hardware",
    "Dibba Bay Hardware Depot",
    "Murbeh Tech Hardware",
    "Al Halfa Steel & Hardware",
    "Qidfa Hardware Mart",
    "Al Ramlah Construction Hardware",
    "Habhab Tools Supply",
    "Al Bidyah Pro Hardware",
    "Umbaqain Equip Hardware",
    "Al Usfar Hardware Hub",

    # ---------------- PHARMACY (20) ----------------
    "Al Falaj Pharmacy",
    "Marina Pearl Pharmacy",
    "Harbor Catch Pharmacy",
    "Al Bahr Rx Pharmacy",
    "Mina Coast Pharmacy",
    "Fujairah Wave Pharmacy",
    "Umbaqain Medical Pharmacy",
    "Sakamkam Pharmacy & Supplies",
    "Rawdah Health Pharmacy",
    "Mirbah Pharma Center",
    "Rugaylat Pharmacy Hub",
    "Dibba Bay Rx Store",
    "Murbeh Primary Pharmacy",
    "Al Halfa Prescription Pharmacy",
    "Qidfa Wellness Pharmacy",
    "Al Ramlah City Pharmacy",
    "Habhab Cure Pharmacy",
    "Al Bidyah Patient Pharmacy",
    "Umbaqain Pharma Solutions",
    "Al Usfar Pharmacy Store",

    # ---------------- FLORIST (20) ----------------
    "Al Falaj Florist",
    "Marina Pearl Florist",
    "Harbor Catch Floral Shop",
    "Al Bahr Flower House",
    "Mina Coast Floral Creations",
    "Fujairah Wave Florist",
    "Umbaqain Bloom Studio",
    "Sakamkam Flower Boutique",
    "Rawdah Petals & Stems",
    "Mirbah Fresh Blooms",
    "Rugaylat Flower Designs",
    "Dibba Bay Floral Crafts",
    "Murbeh Garden Flowers",
    "Al Halfa Rose & Lily",
    "Qidfa Florist & Gifts",
    "Al Ramlah Bloomery",
    "Habhab Scenic Florals",
    "Al Bidyah Flower World",
    "Umbaqain Floral Arrangements",
    "Al Usfar Petal Haven",

    # ---------------- CATERING (20) ----------------
    "Al Falaj Catering",
    "Marina Pearl Catering",
    "Harbor Catch Catering",
    "Al Bahr Catering Services",
    "Mina Coast Catering",
    "Fujairah Wave Catering",
    "Umbaqain Banquet Catering",
    "Sakamkam Event Catering",
    "Rawdah Gourmet Catering",
    "Mirbah Party Catering",
    "Rugaylat Culinary Catering",
    "Dibba Bay Catering & Events",
    "Murbeh Premier Catering",
    "Al Halfa Elite Catering",
    "Qidfa Cuisine Catering",
    "Al Ramlah Festive Catering",
    "Habhab Catering Solutions",
    "Al Bidyah Grand Catering",
    "Umbaqain Celebration Catering",
    "Al Usfar Fine Catering"
]

good_companies = [
    "Emirates Investment Co.","Fujairah International Bank","Al Qasr Trading","Dubai Horizons FZE",
    "Rimal Real Estate","Gulf Engineering Services","Oasis Group International","Al Barakah Logistics",
    "Fujairah Pearl Industries","Emirates Commercial Bank","Al Saqr Financial","Desert Capital Investment"
]

def seed_db():
    print("🔨 [seed_db] Dropping + Creating the database now...")
    db.drop_all()
    db.create_all()

    # ------------------------------------------------------------------------
    # Create a violation_status_history table for multi-step statuses, wrapped in text(...)
    # ------------------------------------------------------------------------
    create_table_sql = text("""
    CREATE TABLE IF NOT EXISTS violation_status_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        violation_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        notes TEXT,
        updated_at DATETIME NOT NULL,
        FOREIGN KEY(violation_id) REFERENCES violation(id)
    );
    """)
    db.session.execute(create_table_sql)
    db.session.commit()

    def insert_violation_status_history(violation_id, timestamps):
        """
        Insert multiple departmental statuses for a single violation,
        picking from a random set. Timestamps should be sorted ascending.
        """
        possible_steps = [
            ("Open", "Violation just created; assigned to local inspector"),
            ("Pending Payment", "Invoiced business for payment of fines; awaiting response"),
            ("Assigned to Field Inspector", "Inspector visiting site for detailed check"),
            ("Legal Review", "Sent case to legal department for compliance check"),
            ("NOC Required", "Awaiting NOC from relevant authority"),
            ("Closed", "All requirements fulfilled; violation case closed"),
            ("Awaiting Documents", "Business asked to provide official documents"),
            ("Inspection Scheduled", "Follow-up inspection scheduled next week"),
            ("Escalated to Management", "High priority, manager involvement requested")
        ]
        num_steps = random.randint(2, 5)
        used_steps = random.sample(possible_steps, num_steps)

        sorted_ts = sorted(timestamps)
        final_ts = []
        for i in range(num_steps):
            if i < len(sorted_ts):
                final_ts.append(sorted_ts[i])
            else:
                # fallback if not enough timestamps
                final_ts.append(sorted_ts[-1] + timedelta(hours=2 * i))

        for i, (step, memo) in enumerate(used_steps):
            insert_sql = text("""
            INSERT INTO violation_status_history (violation_id, status, notes, updated_at)
            VALUES (:vid, :sts, :nts, :upd)
            """)
            db.session.execute(insert_sql, {
                "vid": violation_id,
                "sts": step,
                "nts": memo,
                "upd": final_ts[i]
            })
        db.session.commit()

    start_date = datetime(2023, 1, 1)
    end_date = datetime(2025, 2, 28)
    total_days = (end_date - start_date).days

    all_businesses = original_business_list + expanded_business_list

    for biz_name in all_businesses:
        info = get_business_info(biz_name)
        num_v = get_violation_count()

        if num_v == 0:
            rc0 = RiskClassification(
                business_name=biz_name,
                total_violations=0,
                total_fines=0,
                last_violation_date=None,
                risk_level="Low",
                weighted_risk_score=0.0,
                advanced_risk_score=0.0,
                industry_risk_factor="Low",
                violation_frequency_score=0.0,
                inspection_history="No violations recorded.",
                unpaid_fines=0,
                average_fine=0.0,
                risk_model_details="No violations, automatically Low risk.",
                description=info["description"],
                location=info["location"],
                business_type=info["business_type"]
            )
            db.session.add(rc0)
            db.session.commit()
            continue

        total_fines = 0
        v_timestamps = []
        cat_counts = defaultdict(int)
        severities = []

        violation_records = []
        recent_types = defaultdict(list)

        open_count = 0
        closed_count = 0

        for _ in range(num_v):
            if violation_data:
                cat_choice = random.choice(list(violation_data.keys()))
                vio_choice = random.choice(violation_data[cat_choice])
            else:
                cat_choice = "General Regulatory Violations"
                vio_choice = "Failure to provide required documents"

            base_f = compute_fine(cat_choice, vio_choice)
            offset = random.randint(0, total_days)
            v_date = start_date + timedelta(days=offset)

            base_sev = violation_type_severity_map.get(vio_choice, 3)
            # repeated severity logic
            cutoff_30 = v_date - timedelta(days=30)
            recent_types[vio_choice] = [ts for ts in recent_types[vio_choice] if ts > cutoff_30]
            eff_sev = base_sev + len(recent_types[vio_choice])
            recent_types[vio_choice].append(v_date)

            # time decay
            months_old = (end_date - v_date).days / 30.0
            alpha = 0.1
            decayed_f = base_f * np.exp(-alpha * months_old)

            status = "Open"
            resolution_date = None
            if random.random() < 0.2:
                status = "Closed"
                resolution_date = v_date + timedelta(days=random.randint(1, 15))

            if status == "Open":
                open_count += 1
            else:
                closed_count += 1

            new_v = Violation(
                business_name=biz_name,
                violation_type=vio_choice,
                category=cat_choice,
                severity=base_sev,
                fine=base_f,
                timestamp=v_date,
                location=info["location"],
                month=v_date.strftime("%Y-%m"),
                resolution_date=resolution_date,
                corrective_actions="",
                status=status
            )
            db.session.add(new_v)

            total_fines += base_f
            v_timestamps.append(v_date)
            cat_counts[cat_choice] += 1
            severities.append(base_sev)

            days_since = (end_date - v_date).days

            violation_records.append({
                "category": cat_choice,
                "base_severity": base_sev,
                "effective_severity": eff_sev,
                "fine": base_f,
                "decayed_fine": decayed_f,
                "timestamp": v_date,
                "status": status,
                "days_since": days_since,
                "seed_start": start_date
            })

        db.session.commit()

        last_violation_dt = max(v_timestamps)
        total_v = num_v
        avg_fine = total_fines / num_v
        avg_sev = sum(severities) / len(severities)

        final_score = compute_risk_score_enhanced(violation_records, info["business_type"])
        rlevel = classify_risk(final_score)

        # old aggregator
        min_dt = min(v_timestamps)
        freq_days = (last_violation_dt - min_dt).days if last_violation_dt > min_dt else 1
        months_in_period = freq_days / 30.0 if freq_days > 0 else 1.0
        vio_freq = num_v / months_in_period
        old_agg, old_fr, old_ir, old_tr = compute_aggregated_risk(vio_freq, avg_fine, avg_sev, v_timestamps, 1.0)
        old_weighted = compute_weighted_risk(num_v, total_fines, vio_freq, avg_sev)

        # repeated categories
        cutoff60 = last_violation_dt - timedelta(days=60)
        repeated_set = defaultdict(int)
        # We'll do repeated categories logic differently, but let's keep it simpler:

        repeated_offenders = []
        for c_name, c_count in cat_counts.items():
            if c_count > 3:
                repeated_offenders.append(c_name)

        # sort top categories by c_count descending
        top_cat_list = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
        top_categories = top_cat_list[:3]

        # new global stats fetch
        global_stats = fetch_global_stats(info["business_type"])

        extended_report_text = generate_extended_report(
            business_name=biz_name,
            final_score=final_score,
            risk_level=rlevel,
            top_categories=top_categories,
            repeated_offenders=repeated_offenders,
            total_violations=num_v,
            last_violation_date=last_violation_dt,
            business_type=info["business_type"],
            global_stats=global_stats,
            open_count=open_count,
            closed_count=closed_count
        )

        rc_new = RiskClassification(
            business_name=biz_name,
            total_violations=num_v,
            total_fines=total_fines,
            last_violation_date=last_violation_dt,
            risk_level=rlevel,
            weighted_risk_score=old_weighted,
            advanced_risk_score=final_score,
            industry_risk_factor=determine_industry_label(final_score),
            violation_frequency_score=vio_freq,
            inspection_history=get_inspection_note(),
            unpaid_fines=int(total_fines * 0.25),
            average_fine=avg_fine,
            risk_model_details=extended_report_text,
            description=info["description"],
            location=info["location"],
            business_type=info["business_type"]
        )
        db.session.add(rc_new)
        db.session.commit()

        # Insert multi-step statuses for each violation
        vio_list = Violation.query.filter_by(business_name=biz_name).all()
        for viol_obj in vio_list:
            # Generate random timestamps for departmental workflow
            base_ts = viol_obj.timestamp
            ts_count = random.randint(2, 5)
            ts_list = []
            for i in range(ts_count):
                offset_hours = random.randint(1, 48) * (i + 1)
                new_t = base_ts + timedelta(hours=offset_hours)
                ts_list.append(new_t)
            ts_list.sort()

            insert_violation_status_history(viol_obj.id, ts_list)

    # Good companies
    for gbiz in good_companies:
        info = get_business_info(gbiz)
        rc_good = RiskClassification(
            business_name=gbiz,
            total_violations=0,
            total_fines=0,
            last_violation_date=None,
            risk_level="Low",
            weighted_risk_score=0.0,
            advanced_risk_score=0.0,
            industry_risk_factor="Low",
            violation_frequency_score=0.0,
            inspection_history="Explicit good co. w/ zero violations.",
            unpaid_fines=0,
            average_fine=0.0,
            risk_model_details="No violations found.",
            description=info["description"],
            location=info["location"],
            business_type=info["business_type"]
        )
        db.session.add(rc_good)
    db.session.commit()

    print("\n✅ [seed_db] Seeding completed with advanced logic + extended reports + multi-step statuses!")
    print("-------------------------------------------------------")

if __name__ == "__main__":
    from models import app
    with app.app_context():
        seed_db()
