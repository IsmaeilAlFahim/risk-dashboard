import os
import random
import pandas as pd
from datetime import datetime, timedelta
import numpy as np  # If you're using Poisson or advanced distributions

from backend.backup.old_app import (
    app, db,
    Violation, RiskClassification,
    # For CSV-based fines
    compute_fine,
    # Old aggregator references kept for backward compatibility
    compute_weighted_risk,
    compute_aggregated_risk,
    # The new aggregator & severity map
    compute_risk_score,
    category_severity_map,
    industry_profiles,
    # For final risk classification and insight
    classify_risk,
    generate_insight
)

# Ensure the 'instance' folder exists.
if not os.path.exists("instance"):
    os.makedirs("instance")

# -------------------------------
# Load Violation Categories from CSV
# -------------------------------
file_path = "./Violations_Dataset.csv"
df = pd.read_csv(file_path)
# For random selection of categories & types
violation_data = df.groupby("Category")["Violation Type"].apply(list).to_dict()

# -------------------------------
# Expanded Business Classification Mapping
# -------------------------------
business_info_mapping = {
    "seafood": {
        "business_type": "Restaurant",
        "location": "Harbor District",
        "description": (
            "Renowned for its succulent seafood dishes, freshly sourced from local fishermen "
            "and prepared to perfection in a coastal-inspired ambiance."
        )
    },
    "trading": {
        "business_type": "Retail",
        "location": "Market Street",
        "description": (
            "A reputable trading entity recognized for its wide range of goods and competitive pricing, "
            "serving both local and international customers."
        )
    },
    "souk": {
        "business_type": "Retail",
        "location": "Downtown",
        "description": (
            "A bustling marketplace offering a variety of traditional and modern products, "
            "enticing visitors with vibrant stalls and cultural charm."
        )
    },
    "electronics": {
        "business_type": "Electronics",
        "location": "Industrial Area",
        "description": (
            "Offers the latest in electronic devices, cutting-edge gadgets, and expert technical services "
            "for both personal and business needs."
        )
    },
    "construction": {
        "business_type": "Real Estate",
        "location": "Industrial Area",
        "description": (
            "Provides comprehensive construction and building solutions, leveraging innovation and "
            "engineering excellence to shape modern infrastructure."
        )
    },
    "hospital": {
        "business_type": "Healthcare",
        "location": "Downtown",
        "description": (
            "A state-of-the-art medical facility committed to patient-centered care, "
            "featuring specialized departments and advanced treatment options."
        )
    },
    "food court": {
        "business_type": "Food Service",
        "location": "Downtown",
        "description": (
            "A lively dining destination featuring diverse cuisines and communal seating, "
            "catering to families and on-the-go customers alike."
        )
    },
    "auto": {
        "business_type": "Automotive",
        "location": "Suburban Zone",
        "description": (
            "Renowned for reliable auto services and repairs, offering everything from routine maintenance "
            "to specialized tuning for a wide range of vehicles."
        )
    },
    "bakery": {
        "business_type": "Bakery",
        "location": "Residential Area",
        "description": (
            "Freshly baked artisan breads, pastries, and sweet treats, crafted daily in-house "
            "to delight local customers and connoisseurs alike."
        )
    },
    "jewelry": {
        "business_type": "Retail",
        "location": "Downtown",
        "description": (
            "An elegant boutique showcasing fine jewelry, precious gemstones, and luxury accessories "
            "for discerning customers seeking timeless style."
        )
    },
    "coffee": {
        "business_type": "Food Service",
        "location": "Downtown",
        "description": (
            "A cozy coffee haven with gourmet brews and a relaxed atmosphere, "
            "perfect for social gatherings and casual business meetings."
        )
    },
    "medical": {
        "business_type": "Healthcare",
        "location": "Downtown",
        "description": (
            "A comprehensive medical clinic providing primary care, diagnostic services, and specialized treatments "
            "under the guidance of certified healthcare professionals."
        )
    },
    "investment": {
        "business_type": "Financial",
        "location": "Downtown",
        "description": (
            "Expert investment services offering wealth management, strategic portfolios, "
            "and personalized financial consulting for both individual and corporate clients."
        )
    },
    "capital": {
        "business_type": "Financial",
        "location": "Downtown",
        "description": (
            "Provides comprehensive capital investment and management solutions, "
            "backed by extensive market research and financial expertise."
        )
    },
    "bank": {
        "business_type": "Financial",
        "location": "Downtown",
        "description": (
            "A robust banking institution, facilitating deposits, loans, and personalized financial services "
            "for a diverse clientele."
        )
    },
    "logistics": {
        "business_type": "Logistics",
        "location": "Industrial Area",
        "description": (
            "Expert in large-scale transportation, warehousing, and supply chain management solutions, "
            "optimizing efficiency across domestic and international markets."
        )
    },
    "furniture": {
        "business_type": "Home Goods",
        "location": "Retail Park",
        "description": (
            "Offers a curated selection of high-quality furniture and home décor, "
            "combining practicality and style for modern living spaces."
        )
    },
    "dairy": {
        "business_type": "Agriculture",
        "location": "Rural District",
        "description": (
            "Produces farm-fresh dairy products, focusing on high-quality, sustainable methods "
            "and an unwavering commitment to animal welfare."
        )
    },
    "hardware": {
        "business_type": "Hardware",
        "location": "Industrial Area",
        "description": (
            "Supplies building materials, tools, and hardware essentials, "
            "serving both professional contractors and DIY enthusiasts."
        )
    },
    "pharmacy": {
        "business_type": "Healthcare",
        "location": "Downtown",
        "description": (
            "Dispenses prescription medications, over-the-counter remedies, and health-related products, "
            "along with personalized pharmaceutical guidance."
        )
    },
    "florist": {
        "business_type": "Retail",
        "location": "Downtown",
        "description": (
            "Creates exquisite floral arrangements and bouquets for every occasion, "
            "utilizing fresh flowers and artistic design skills."
        )
    },
    "catering": {
        "business_type": "Food Service",
        "location": "Commercial District",
        "description": (
            "Provides on-site and off-site catering for events of all sizes, "
            "crafting customized menus that combine flavor and presentation."
        )
    },
}

def get_business_info(business_name):
    name_lower = business_name.lower()
    for key, info in business_info_mapping.items():
        if key in name_lower:
            return info
    return {
        "business_type": "General Business",
        "location": "City Center",
        "description": (
            "A versatile business operation offering broad services or products to the local community, "
            "with a reputation for consistent quality."
        )
    }

# -------------------------------
# Probability-based function for violation counts
# -------------------------------
def get_violation_count():
    """
    Returns an integer # of violations with a distribution:
      - 5% chance of 60–80 (outlier)
      - 10% chance of 20–39 (high)
      - 30% chance of 6–15 (medium)
      - 53% chance of 1–5 (low)
      - 2% chance of 0
    """
    prob = random.random()
    if prob < 0.05:
        return random.randint(60, 80)  # outliers
    elif prob < 0.15:
        return random.randint(20, 39)  # high
    elif prob < 0.45:
        return random.randint(6, 15)   # medium
    elif prob < 0.98:
        return random.randint(1, 5)    # low
    else:
        return 0                       # zero

def determine_industry_label(business_type):
    """
    Convert numeric factor to "High", "Medium", "Low".
    This ensures no placeholders for industry_risk_factor.
    """
    profile = industry_profiles.get(business_type, {"compliance_factor":1.0, "impact_factor":1.0})
    factor_avg = (profile["compliance_factor"] + profile["impact_factor"]) / 2.0
    if factor_avg >= 1.3:
        return "High"
    elif factor_avg >= 1.1:
        return "Medium"
    else:
        return "Low"

def seed_db():
    print("🔨 [seed_db] Dropping + Creating the database now...")
    db.drop_all()
    db.create_all()

    start_date = datetime(2023, 1, 1)
    end_date = datetime(2025, 2, 28)
    total_days = (end_date - start_date).days

    original_business_list = [
        "Fujairah Seafood Restaurant", "Emirates Trading Co.", "Fujairah Souk Supermarket",
        "Al Hamra Electronics", "Gulf Construction Supplies", "Fujairah General Hospital",
        "Sunrise Bakery", "Blue Ocean Seafood", "Al Faseel Trading", "Coastal Fresh Foods",
        "Fujairah Textile Mills", "Pearl Jewelry", "Marina Leisure Center", "Emirates Hardware",
        "Fujairah Dairy Farm", "Golden Date Establishment", "Al Noor Bookstore",
        "Fujairah Medical Clinic", "Royal Motors", "Fujairah IT Solutions", "Desert Wind Apparel",
        "Oasis Furniture", "Harbor View Restaurant", "Al Jazeera Trading", "Blue Horizon Catering"
    ]
# 400 new Fujairah-themed businesses (no repetition, varied naming)
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
    business_list = original_business_list + expanded_business_list

    good_companies = [
        "Emirates Investment Co.", "Fujairah International Bank", "Al Qasr Trading", "Dubai Horizons FZE",
        "Rimal Real Estate", "Gulf Engineering Services", "Oasis Group International", "Al Barakah Logistics",
        "Fujairah Pearl Industries", "Emirates Commercial Bank", "Al Saqr Financial", "Desert Capital Investment"
    ]

    for business in business_list:
        info = get_business_info(business)
        num_violations = get_violation_count()

        if num_violations == 0:
            # Zero-violation => straightforward Low
            new_risk = RiskClassification(
                business_name=business,
                total_violations=0,
                total_fines=0,
                last_violation_date=None,
                risk_level="Low",
                weighted_risk_score=0.0,
                advanced_risk_score=0.0,
                # No placeholders: dynamic industry factor
                industry_risk_factor=determine_industry_label(info["business_type"]),
                violation_frequency_score=0.0,
                inspection_history="No violations recorded.",
                unpaid_fines=0,
                average_fine=0.0,
                risk_model_details="No violations, auto-classified as Low risk.",
                description=info["description"],
                location=info["location"],
                business_type=info["business_type"]
            )
            db.session.add(new_risk)
            db.session.commit()
            continue

        total_fines = 0
        violation_timestamps = []
        severities = []

        for _ in range(num_violations):
            category_choice = random.choice(list(violation_data.keys()))
            violation_choice = random.choice(violation_data[category_choice])
            fine_amount = compute_fine(category_choice, violation_choice)
            day_offset = random.randint(0, total_days)
            violation_date = start_date + timedelta(days=day_offset)
            violation_timestamps.append(violation_date)

            assigned_severity = category_severity_map.get(category_choice, 3)
            severities.append(assigned_severity)

            new_violation = Violation(
                business_name=business,
                violation_type=violation_choice,
                category=category_choice,
                severity=assigned_severity,
                fine=fine_amount,
                timestamp=violation_date,
                location=info["location"],
                month=violation_date.strftime("%Y-%m")
            )
            db.session.add(new_violation)
            total_fines += fine_amount

        db.session.commit()

        last_violation_date = max(violation_timestamps) if violation_timestamps else None
        months_in_period = total_days / 30.0 if total_days else 1.0
        average_fine = total_fines / num_violations if num_violations else 0.0
        average_severity = sum(severities) / len(severities) if severities else 3.0

        # Use Poisson aggregator
        final_score, freq_risk, imp_risk, trend_risk = compute_risk_score(
            total_violations=num_violations,
            months_in_period=months_in_period,
            average_fine=average_fine,
            avg_severity=average_severity,
            violation_timestamps=violation_timestamps,
            business_type=info["business_type"]
        )
        risk_level = classify_risk(final_score)

        # For backward compatibility, we call old aggregator
        old_final_score, old_freq_risk, old_imp_risk, old_trend_risk = compute_aggregated_risk(
            (num_violations / (total_days / 30.0)) if total_days else 0.0,
            average_fine,
            average_severity,
            violation_timestamps,
            1.0
        )
        weighted_score = compute_weighted_risk(num_violations, total_fines, (num_violations / (total_days / 30.0)) if total_days else 0.0, average_severity)

        insight = generate_insight(
            business, num_violations, total_days, average_fine,
            average_severity, (num_violations / (total_days / 30.0)) if total_days else 0.0,
            freq_risk, imp_risk, trend_risk, final_score
        )

        new_record = RiskClassification(
            business_name=business,
            total_violations=num_violations,
            total_fines=total_fines,
            last_violation_date=last_violation_date,
            risk_level=risk_level,
            weighted_risk_score=weighted_score,    # old approach stored
            advanced_risk_score=final_score,       # new approach
            # dynamic industry factor label => no placeholders
            industry_risk_factor=determine_industry_label(info["business_type"]),
            violation_frequency_score=(num_violations / (total_days / 30.0)) if total_days else 0.0,
            inspection_history="Routine inspections",
            unpaid_fines=int(total_fines * 0.25),
            average_fine=average_fine,
            risk_model_details=insight,
            description=info["description"],
            location=info["location"],
            business_type=info["business_type"]
        )
        db.session.add(new_record)
        db.session.commit()

    # Seed "good" zero-violation companies
    for business in good_companies:
        info = get_business_info(business)
        new_good = RiskClassification(
            business_name=business,
            total_violations=0,
            total_fines=0,
            last_violation_date=None,
            risk_level="Low",
            weighted_risk_score=0.0,
            advanced_risk_score=0.0,
            industry_risk_factor=determine_industry_label(info["business_type"]),
            violation_frequency_score=0.0,
            inspection_history="No violations recorded.",
            unpaid_fines=0,
            average_fine=0.0,
            risk_model_details="Explicitly listed as a good company with zero violations.",
            description=info["description"],
            location=info["location"],
            business_type=info["business_type"]
        )
        db.session.add(new_good)
    db.session.commit()

    print("\n✅ Database seeded successfully!")
    print("   - Businesses:", len(business_list))
    print("   - Good companies (explicit zero violations):", len(good_companies))
    print("-------------------------------------------------------")

#if __name__ == "__main__":
#    with app.app_context():
#        seed_db()
