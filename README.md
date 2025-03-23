
# Risk Analytics & Business Intelligence Dashboard

## Project Overview
Enhances Fujairah Municipality's digital inspection capabilities by integrating predictive analytics, risk assessments, and qualitative insights.

## Technical Stack & Dependencies

### Backend (Flask & Python)
- Flask (3.1.0)
- SQLAlchemy (2.0.38)
- Flask-SQLAlchemy (3.1.1)
- Pandas
- NumPy

**Installation:**
```bash
pip install -r requirements.txt
```

### Frontend (React.js & Vite)
- React.js (19.0.0)
- Axios (1.8.1)
- React Router DOM
- Tailwind CSS
- HeroIcons
- date-fns
- html2canvas
- jspdf
- classnames

**Installation:**
```bash
npm install
```

## Installation Guide

### Backend Setup
1. Navigate to the backend directory:
```bash
cd backend
```
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Seed the database:
```bash
python seed.py
```
4. Run the Flask server:
```bash
python app.py
```

### Frontend Setup
1. Navigate to the frontend directory:
```bash
cd frontend
```
2. Install dependencies:
```bash
npm install
```
3. Run the development server:
```bash
npm run dev
```

Access the dashboard at [http://localhost:5173](http://localhost:5173).

## Complete Folder Structure

```
backend/
├── app.py                 # Main Flask application
├── models.py              # Database ORM models
├── seed.py                # DB seeding and initialization
├── risk_calc.py           # Risk analytics logic
├── regulatory_mapping.py  # Regulatory compliance mapping
├── Violations_Dataset.csv # Initial data seed file
├── requirements.txt       # Python dependencies
└── instance/
    └── violations.db      # SQLite database file

frontend/risk-dashboard/
├── src/
│   ├── App.jsx            # React main app and routing
│   └── components/
│       ├── Dashboard.jsx  
│       ├── Navbar.jsx     
│       ├── KPIWidgets.jsx 
│       ├── GeoHotspots.jsx
│       ├── MiniTrendChart.jsx
│       ├── HighRiskBusinesses.jsx
│       ├── RiskDistributionChart.jsx
│       ├── RiskAnalysis.jsx
│       ├── ViolationTrends.jsx
│       ├── BusinessOverview.jsx
│       ├── ViolationList.jsx
│       ├── ViolationDetails.jsx
│       ├── LandingPage.jsx
│       └── Footer.jsx
├── package.json           # Frontend dependencies
├── tailwind.config.js     # Tailwind CSS configuration
├── vite.config.js         # Vite build config
└── index.html             # Main HTML entry point
```

## Comprehensive End-User Guide

### Landing Page
Professional welcoming page with clear navigation.

### General Navigation (Navbar)
Navigate through:
- Dashboard
- Risk Analysis
- Violation Trends
- Business Overview
- Violation List

### Dashboard Overview
Interact with:
- KPI Widgets
- Geographic Hotspots
- Mini Trend Chart
- High-Risk Businesses
- Risk Distribution Chart

### Risk Analysis
Detailed risk assessment with expandable rows and advanced search/filtering.

### Violation Trends
Interactive line/bar charts with legend filters and tooltips.

### Business Overview
Detailed business profiles, exportable PDF reports, and search functionality.

### Violation List
Search/filter violations, clickable rows, and update statuses.

### Violation Details
View chronological status updates and notes.

### Footer
Consistent footer providing system information.

### Consistent Styling
Unified professional appearance using Tailwind CSS.

### Search & Filtering
Robust search available in Violation List, Risk Analysis, and Business Overview.

### Interconnectivity
Seamless navigation through interconnected widgets and tabs.

## Testing & Verification
Follow backend and frontend verification steps as detailed in Installation Guide.

## Troubleshooting
Refer to backend/frontend troubleshooting steps provided in the Installation Guide.
