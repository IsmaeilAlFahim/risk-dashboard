import React, { useEffect, useState } from "react";
import axios from "axios";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from "recharts";
import { useNavigate } from "react-router-dom";

const MiniTrendChart = () => {
  const [trendData, setTrendData] = useState([]);
  const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";
  const navigate = useNavigate();

  useEffect(() => {
    axios
      .get(`${API_URL}/trends/violations`)
      .then((response) => {
        const rawData = response.data || [];
        const monthMap = {};

        // Group and sum total_violations by month
        rawData.forEach((item) => {
          const m = item.month;
          if (!monthMap[m]) {
            monthMap[m] = { month: m, total_violations: 0 };
          }
          monthMap[m].total_violations += item.total_violations;
        });

        // Convert object to array, sort by month, then grab last 6
        let aggregated = Object.values(monthMap);
        aggregated.sort((a, b) => a.month.localeCompare(b.month));
        const finalData = aggregated.slice(-6);

        setTrendData(finalData);
      })
      .catch((error) => console.error("Error fetching trends:", error));
  }, [API_URL]);

  // Handle clicks on the chart or data points
  const handleChartClick = (chartState) => {
    // If user clicks a data point, Recharts will provide activePayload
    if (
      chartState &&
      chartState.activePayload &&
      chartState.activePayload.length > 0
    ) {
      // Extract the data point info (e.g. month)
      const { month } = chartState.activePayload[0].payload || {};
      if (month) {
        // Navigate to /violations with the month param
        navigate(`/violations?month=${encodeURIComponent(month)}`);
        return;
      }
    }

    // Otherwise, user clicked the background – navigate to /trends
    navigate("/trends");
  };

  return (
    <div className="p-4 bg-white shadow-lg rounded-lg">
      {/* Subtle heading using your secondary color */}
      <h2 className="text-lg font-semibold text-secondary mb-2">
        Violation Trends (Last 6 Months)
      </h2>

      <ResponsiveContainer width="100%" height={100}>
        <LineChart data={trendData} onClick={handleChartClick}>
          {/* Axis colors: #2B2B2B is your secondary.DEFAULT */}
          <XAxis dataKey="month" stroke="#2B2B2B" />
          <YAxis stroke="#2B2B2B" hide />
          <Tooltip />

          {/*
            Use your "accent" color (#007BFF) for the line stroke.
            If you introduced an 'accent' palette in tailwind.config.js,
            keep this hex value consistent with accent.DEFAULT.
          */}
          <Line
            type="monotone"
            dataKey="total_violations"
            stroke="#007BFF"
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default MiniTrendChart;
