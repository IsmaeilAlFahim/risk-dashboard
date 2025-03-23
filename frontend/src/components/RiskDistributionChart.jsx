import React, { useEffect, useState } from "react";
import axios from "axios";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts";

// 1) Risk colors from your tailwind config
const RISK_COLORS = {
  High:   "#B41F2B", // or colors.high.DEFAULT
  Medium: "#FFC107", // or colors.medium.DEFAULT
  Low:    "#28A745", // or colors.low.DEFAULT
  Unknown: "#A9A9A9",
};

// 2) Status colors for open vs closed
const STATUS_COLORS = {
  Open: "#007BFF",   // or accent.DEFAULT
  Closed: "#808080", // or unknown.dark
  Fallback: "#C0C0C0"
};

// 3) Base colors for geographic hotspots
const GEO_COLORS = [
  "#B41F2B",
  "#FFC107",
  "#28A745",
  "#0056B3",
  "#8A2BE2",
  "#A9A9A9",
];

// Helper to get color for a given index in the hotspots array
const getHotspotColor = (index) => GEO_COLORS[index % GEO_COLORS.length];

const RiskDistributionChart = () => {
  const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

  // States
  const [openClosedData, setOpenClosedData] = useState([]);
  const [riskDistribution, setRiskDistribution] = useState([]);
  const [hotspotsData, setHotspotsData] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    // 1) Open vs. Closed
    axios.get(`${API_URL}/violations`)
      .then((resp) => {
        const violations = resp.data;
        let openCount = 0;
        let closedCount = 0;
        violations.forEach((v) => {
          if (v.status === "Open") openCount++;
          else if (v.status === "Closed") closedCount++;
        });
        setOpenClosedData([
          { name: "Open", value: openCount },
          { name: "Closed", value: closedCount }
        ]);
      })
      .catch((err) => {
        console.error("[RiskDistributionChart] Error fetching violations:", err);
        setError("Failed to load open/closed data.");
      });

    // 2) Risk distribution
    axios.get(`${API_URL}/risk`)
      .then((response) => {
        const counts = { High: 0, Medium: 0, Low: 0 };
        response.data.forEach((item) => {
          if (counts[item.risk_level] !== undefined) {
            counts[item.risk_level] += 1;
          }
        });
        const distribution = [
          { name: "High", value: counts.High },
          { name: "Medium", value: counts.Medium },
          { name: "Low", value: counts.Low },
        ];
        setRiskDistribution(distribution);
      })
      .catch((err) => {
        console.error("[RiskDistributionChart] Error fetching risk data:", err);
        setError("Failed to load risk distribution data.");
      });

    // 3) Geo Hotspots
    axios.get(`${API_URL}/trends/geo-hotspots`)
      .then((resp) => {
        // e.g. [ { location: "Downtown", total_violations: 10 }, ... ]
        const raw = resp.data || [];

        // Sort descending by total violations
        const sorted = [...raw].sort((a, b) => b.total_violations - a.total_violations);

        // Take top 3
        const topThree = sorted.slice(0, 3).map((item) => ({
          name: item.location,
          value: item.total_violations
        }));

        // Sum the remainder into "Other"
        const remainder = sorted.slice(3);
        const otherSum = remainder.reduce((acc, item) => acc + item.total_violations, 0);

        let finalData = [...topThree];
        if (otherSum > 0) {
          finalData.push({ name: "Other", value: otherSum });
        }
        setHotspotsData(finalData);
      })
      .catch((err) => {
        console.error("[RiskDistributionChart] Error fetching geo-hotspots:", err);
        setError("Failed to load geographic hotspots data.");
      });
  }, [API_URL]);

  // Sum function
  const sumData = (arr) => arr.reduce((sum, d) => sum + d.value, 0);

  const openClosedTotal = sumData(openClosedData);
  const riskTotal = sumData(riskDistribution);
  const hotspotsTotal = sumData(hotspotsData);

  // ======================
  // Chart render helpers
  // ======================
  const renderOpenClosedPie = () => {
    if (!openClosedTotal) {
      return <p className="text-center text-secondary-light">No open/closed data available.</p>;
    }
    return (
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={openClosedData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={80}
            label
          >
            {openClosedData.map((entry, index) => (
              <Cell
                key={`oc-cell-${index}`}
                fill={STATUS_COLORS[entry.name] || STATUS_COLORS.Fallback}
              />
            ))}
          </Pie>
          <Tooltip />
          <Legend verticalAlign="bottom" height={36} />
        </PieChart>
      </ResponsiveContainer>
    );
  };

  const renderRiskPie = () => {
    if (!riskTotal) {
      return <p className="text-center text-secondary-light">No risk distribution data available.</p>;
    }
    return (
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={riskDistribution}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={80}
            label
          >
            {riskDistribution.map((entry, index) => (
              <Cell
                key={`risk-cell-${index}`}
                fill={RISK_COLORS[entry.name] || RISK_COLORS.Unknown}
              />
            ))}
          </Pie>
          <Tooltip />
          <Legend verticalAlign="bottom" height={36} />
        </PieChart>
      </ResponsiveContainer>
    );
  };

  const renderHotspotsPie = () => {
    if (!hotspotsTotal) {
      return <p className="text-center text-secondary-light">No geographic hotspots data available.</p>;
    }
    return (
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={hotspotsData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={80}
            label
          >
            {hotspotsData.map((entry, index) => (
              <Cell key={`hot-cell-${index}`} fill={getHotspotColor(index)} />
            ))}
          </Pie>
          <Tooltip />
          <Legend verticalAlign="bottom" height={36} />
        </PieChart>
      </ResponsiveContainer>
    );
  };

  // For geo-hotspots color cycling
  const getHotspotColor = (index) => {
    return GEO_COLORS[index % GEO_COLORS.length];
  };

  // ======================
  // MAIN RETURN
  // ======================
  return (
    <div className="p-4 bg-white shadow-lg rounded-lg">
      <h2 className="text-lg font-bold text-primary mb-4 text-center">
        Advanced Analytics
      </h2>
      {error && <p className="text-center text-high mb-2">{error}</p>}

      {/* 3 Pie Charts in a row (stack on mobile) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Left: open vs closed */}
        <div className="bg-neutralBg p-4 rounded shadow">
          <h3 className="font-semibold text-secondary text-center mb-2">
            Open vs. Closed
          </h3>
          {renderOpenClosedPie()}
        </div>

        {/* Middle: Risk Distribution */}
        <div className="bg-neutralBg p-4 rounded shadow">
          <h3 className="font-semibold text-secondary text-center mb-2">
            Risk Distribution
          </h3>
          {renderRiskPie()}
        </div>

        {/* Right: top 3 geo hotspots + "Other" */}
        <div className="bg-neutralBg p-4 rounded shadow">
          <h3 className="font-semibold text-secondary text-center mb-2">
            Geo Hotspots
          </h3>
          {renderHotspotsPie()}
        </div>
      </div>
    </div>
  );
};

export default RiskDistributionChart;
