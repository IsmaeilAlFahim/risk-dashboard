import React, { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const HighRiskBusinesses = () => {
  const [highRisk, setHighRisk] = useState([]);
  const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";
  const navigate = useNavigate();

  useEffect(() => {
    axios.get(`${API_URL}/risk`)
      .then((response) => {
        const sortedBusinesses = response.data
          .filter((business) => business.risk_level === "High")
          .sort((a, b) => b.total_violations - a.total_violations)
          .slice(0, 3);
        setHighRisk(sortedBusinesses);
      })
      .catch((error) => console.error("Error fetching high risk businesses:", error));
  }, [API_URL]);

  return (
    <div className="p-4 bg-white shadow-lg rounded-lg">
      {/* Heading: use text-secondary for a subtle, consistent heading style */}
      <h2 className="text-lg font-semibold text-secondary mb-2">Top High-Risk Businesses</h2>

      {highRisk.length === 0 ? (
        // For the empty state, use a lighter neutral or secondary-light
        <p className="text-secondary-light">No high risk businesses found.</p>
      ) : (
        <ul className="list-disc list-inside text-secondary-light">
          {highRisk.map((business, index) => (
            <li
              key={index}
              className="py-1 cursor-pointer hover:underline"
              onClick={() => navigate(`/business/${encodeURIComponent(business.business_name)}`)}
            >
              {/* High-risk name in a bolder brand color (primary.dark) */}
              <span className="font-bold text-primary-dark">
                {business.business_name}
              </span>{" "}
              - {business.total_violations} Violations
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default HighRiskBusinesses;
