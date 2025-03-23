import React, { useEffect, useState } from "react";
import axios from "axios";
// For navigation within React Router
import { useNavigate } from "react-router-dom";

const KPIWidgets = () => {
  const [kpiData, setKpiData] = useState({
    totalViolations: 0,
    totalFines: 0,
    highRiskBusinesses: 0,
  });

  const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";
  const navigate = useNavigate();

  useEffect(() => {
    axios.get(`${API_URL}/risk`)
      .then((response) => {
        const riskData = response.data;
        const totalViolations = riskData.reduce((sum, item) => sum + item.total_violations, 0);
        const totalFines = riskData.reduce((sum, item) => sum + item.total_fines, 0);
        const highRiskBusinesses = riskData.filter(item => item.risk_level === "High").length;
        setKpiData({ totalViolations, totalFines, highRiskBusinesses });
      })
      .catch(error => console.error("Error fetching KPI data:", error));
  }, [API_URL]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Total Violations Widget */}
      <div
        className="p-4 bg-white shadow-lg rounded-lg text-center cursor-pointer hover:shadow-xl transition"
        onClick={() => navigate("/violations")}
      >
        <h2 className="text-lg font-semibold text-secondary">Total Violations</h2>
        {/* 
          Replace text-red-500 with text-primary to keep brand consistency.
          You can switch to text-primary-dark or text-primary-light if you prefer 
          a lighter/darker variant.
        */}
        <p className="text-3xl font-bold text-primary-light">{kpiData.totalViolations}</p>
      </div>

      {/* Total Fines Widget */}
      <div
        className="p-4 bg-white shadow-lg rounded-lg text-center cursor-pointer hover:shadow-xl transition"
        // Example: link to /trends/fines
        onClick={() => navigate("/trends/fines")}
      >
        <h2 className="text-lg font-semibold text-secondary">Total Fines</h2>
        {/* 
          If you want a distinct color for fines, you could use text-primary-light 
          or keep them all text-primary for uniformity.
        */}
        <p className="text-3xl font-bold text-primary-light">{kpiData.totalFines} AED</p>
      </div>

      {/* High Risk Businesses Widget */}
      <div
        className="p-4 bg-white shadow-lg rounded-lg text-center cursor-pointer hover:shadow-xl transition"
        onClick={() => navigate("/risk")}
      >
        <h2 className="text-lg font-semibold text-secondary">High Risk Businesses</h2>
        {/* 
          Using text-primary-dark for a contrasting variant, indicating seriousness. 
          Adjust as needed (text-primary, text-primary-light, etc.)
        */}
        <p className="text-3xl font-bold text-primary-light">{kpiData.highRiskBusinesses}</p>
      </div>
    </div>
  );
};

export default KPIWidgets;
