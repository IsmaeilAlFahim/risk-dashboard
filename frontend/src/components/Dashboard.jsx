import React from "react";
import { Squares2X2Icon } from "@heroicons/react/24/solid";
import KPIWidgets from "./KPIWidgets";
import GeoHotspots from "./GeoHotspots";
import MiniTrendChart from "./MiniTrendChart";
import HighRiskBusinesses from "./HighRiskBusinesses";
import RiskDistributionChart from "./RiskDistributionChart";

const Dashboard = () => {
  return (
    <div className="bg-neutralBg min-h-screen pt-8 pb-10">
      <div className="container">
        {/* Heading (using your primary brand color) */}
        <h1 className="text-4xl font-extrabold text-primary text-center tracking-wide flex items-center justify-center">
          {/* Icon next to the text */}
          <Squares2X2Icon className="w-8 h-8 mr-2" />
          Dashboard Overview
        </h1>

        {/*
          Paragraph text switched from text-gray-700 to text-secondary
          to align with your brand’s secondary color (#2B2B2B).
        */}
        <p className="text-base text-secondary text-center mt-2 max-w-2xl mx-auto leading-relaxed">
          Monitor violations, risk levels, and advanced analytics in real-time.
          Our dashboard integrates research‑backed risk models that use frequency,
          impact, and trend analyses to provide a comprehensive view of business compliance.
        </p>

        {/* KPI Widgets Section */}
        <div className="mt-8">
          <KPIWidgets />
        </div>

        {/* Main Dashboard Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
          {/* High Risk Businesses */}
          <div className="card hover:shadow-xl transform transition-transform hover:scale-105">
            <HighRiskBusinesses />
          </div>

          {/* Mini Trend Chart */}
          <div className="card hover:shadow-xl transform transition-transform hover:scale-105">
            <MiniTrendChart />
          </div>

          {/* Geo Hotspots */}
          <div className="card hover:shadow-xl transform transition-transform hover:scale-105">
            <GeoHotspots />
          </div>
        </div>

        {/* Risk Distribution Chart */}
        <div className="mt-8 card hover:shadow-xl transform transition-transform hover:scale-105">
          <RiskDistributionChart />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
