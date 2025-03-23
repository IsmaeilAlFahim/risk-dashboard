import React, { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import {
  ChartBarIcon,
} from "@heroicons/react/24/solid";

const RiskAnalysis = () => {
  // ---------------------------
  // Main data & expanded row
  // ---------------------------
  const [riskData, setRiskData] = useState([]);
  const [expandedRow, setExpandedRow] = useState(null);

  // ---------------------------
  // Sorting & Pagination
  // ---------------------------
  const [sortField, setSortField] = useState("business_name");
  const [sortOrder, setSortOrder] = useState("asc");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const navigate = useNavigate();
  const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

  // ---------------------------
  // Fetch risk data from /risk
  // ---------------------------
  useEffect(() => {
    axios
      .get(`${API_URL}/risk`)
      .then((response) => setRiskData(response.data))
      .catch((error) => console.error("Error fetching risk data:", error));
  }, [API_URL]);

  // ---------------------------
  // Sorting Logic
  // ---------------------------
  const sortedData = [...riskData].sort((a, b) => {
    let valA, valB;
    if (sortField === "business_name") {
      valA = a.business_name.toLowerCase();
      valB = b.business_name.toLowerCase();
    } else if (sortField === "total_violations") {
      valA = a.total_violations;
      valB = b.total_violations;
    } else if (sortField === "risk_level") {
      // Map High/Medium/Low to numeric
      const priority = { High: 3, Medium: 2, Low: 1 };
      valA = priority[a.risk_level] || 0;
      valB = priority[b.risk_level] || 0;
    } else {
      // Fallback if needed
      valA = a[sortField];
      valB = b[sortField];
    }

    if (valA < valB) return sortOrder === "asc" ? -1 : 1;
    if (valA > valB) return sortOrder === "asc" ? 1 : -1;
    return 0;
  });

  // ---------------------------
  // Pagination Logic
  // ---------------------------
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const pagedData = sortedData.slice(startIndex, endIndex);
  const totalPages = Math.ceil(sortedData.length / pageSize);

  // ---------------------------
  // Row Expansion
  // ---------------------------
  const toggleRow = (bizName) => {
    setExpandedRow(expandedRow === bizName ? null : bizName);
  };

  // ---------------------------
  // Sorting Helpers (Arrows)
  // ---------------------------
  const handleSortColumn = (field, direction) => {
    setSortField(field);
    setSortOrder(direction);
    setCurrentPage(1);
  };

  const renderArrowsForColumn = (field) => {
    const isAsc = sortField === field && sortOrder === "asc";
    const isDesc = sortField === field && sortOrder === "desc";

    return (
      <span className="ml-2">
        {/* Up arrow => asc */}
        <span
          onClick={(e) => {
            e.stopPropagation();
            handleSortColumn(field, "asc");
          }}
          className={
            "mx-1 cursor-pointer " +
            (isAsc ? "text-primary font-bold" : "text-gray-300")
          }
        >
          ▲
        </span>
        {/* Down arrow => desc */}
        <span
          onClick={(e) => {
            e.stopPropagation();
            handleSortColumn(field, "desc");
          }}
          className={
            "mx-1 cursor-pointer " +
            (isDesc ? "text-primary font-bold" : "text-gray-300")
          }
        >
          ▼
        </span>
      </span>
    );
  };

  return (
    <div className="mt-24 p-6 bg-white shadow-lg rounded-lg">
      {/* Main Heading with icon & text side-by-side, centered */}
      <h1 className="flex items-center justify-center text-3xl font-bold mb-4 text-primary">
        <ChartBarIcon className="w-8 h-8 mr-2" />
        Risk Analysis
      </h1>

      <p className="text-secondary text-center mb-4">
        This table presents a comprehensive analysis of each business's compliance
        performance using robust, research‑backed risk models. Our methodology integrates
        frequency, impact, and trend analyses—grounded in statistical probability, risk matrix
        principles, and regression‑based forecasting—to derive an aggregated risk score.
      </p>

      {/* Table / Data */}
      {pagedData.length === 0 ? (
        <p className="text-center text-secondary-light">
          No risk data available.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full border border-gray-300 bg-neutralBg rounded-lg">
            <thead>
              <tr className="bg-primary-light text-white">
                <th className="border px-4 py-3 text-left">
                  <div className="flex items-center">
                    <span className="mr-2">Business</span>
                    {renderArrowsForColumn("business_name")}
                  </div>
                </th>
                <th className="border px-4 py-3 text-center">
                  <div className="flex items-center justify-center">
                    <span className="mr-2">Total Violations</span>
                    {renderArrowsForColumn("total_violations")}
                  </div>
                </th>
                <th className="border px-4 py-3 text-center">
                  <div className="flex items-center justify-center">
                    <span className="mr-2">Risk Level</span>
                    {renderArrowsForColumn("risk_level")}
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              {pagedData.map((r, index) => (
                <React.Fragment key={index}>
                  <tr
                    className="border-t bg-white hover:bg-gray-100 cursor-pointer"
                    onClick={() => toggleRow(r.business_name)}
                  >
                    <td className="border px-4 py-3">
                      <span
                        className="text-primary-dark font-semibold hover:underline cursor-pointer"
                        onClick={(e) => {
                          // Prevent toggling expand if user just wants to navigate
                          e.stopPropagation();
                          navigate(
                            `/business/${encodeURIComponent(r.business_name)}`
                          );
                        }}
                      >
                        {r.business_name || "N/A"}
                      </span>
                    </td>
                    <td className="border px-4 py-3 text-center">
                      {r.total_violations || 0}
                    </td>
                    <td
                      className={`border px-4 py-3 text-center font-semibold ${
                        r.risk_level === "High"
                          ? "text-high"
                          : r.risk_level === "Medium"
                          ? "text-medium"
                          : "text-low"
                      }`}
                    >
                      {r.risk_level || "Unknown"}
                    </td>
                  </tr>
                  {/* Expanded Row */}
                  {expandedRow === r.business_name && (
                    <tr className="bg-neutralBg">
                      <td colSpan="3" className="border px-4 py-3 text-sm text-secondary">
                        <strong>Risk Insights:</strong> {r.risk_model_details}
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination Controls */}
      <div className="flex justify-center mt-4 items-center space-x-2">
        <button
          onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
          disabled={currentPage === 1}
          className="px-3 py-1 bg-gray-300 rounded hover:bg-gray-400 disabled:opacity-50"
        >
          Prev
        </button>
        <span className="px-2 text-secondary">
          Page {currentPage} of {totalPages}
        </span>
        <button
          onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))}
          disabled={currentPage === totalPages}
          className="px-3 py-1 bg-gray-300 rounded hover:bg-gray-400 disabled:opacity-50"
        >
          Next
        </button>

        <select
          value={pageSize}
          onChange={(e) => {
            setPageSize(parseInt(e.target.value));
            setCurrentPage(1);
          }}
          className="ml-4 border rounded p-1 text-secondary"
        >
          <option value={5}>5 per page</option>
          <option value={10}>10 per page</option>
          <option value={25}>25 per page</option>
        </select>
      </div>

      {/* Methodology & Risk Matrix */}
      <div className="mt-8 p-6 bg-gray-100 rounded-md shadow-md">
        <h2 className="text-xl font-semibold mb-4 text-primary">
          Risk Assessment Methodology
        </h2>
        <ul className="space-y-3 text-secondary">
          <li>
            <strong>Frequency Risk:</strong> Captures how often a business is non‑compliant.
            A higher recurrence signals potential systemic issues.
          </li>
          <li>
            <strong>Impact Risk:</strong> Evaluates the severity and financial/operational
            consequences of violations.
          </li>
          <li>
            <strong>Trend Risk:</strong> Assesses the direction and rate of change in violation
            frequency over time. An upward trend indicates deteriorating compliance.
          </li>
          <li>
            <strong>Final Risk Score:</strong> An aggregate measure derived from the three metrics
            using industry‑standard weightings. The resulting score is categorized into High,
            Medium, or Low risk, each with clear recommendations:
            <ul className="list-disc list-inside">
              <li>
                <span className="text-high font-semibold">High Risk:</span> Immediate
                corrective actions are required.
              </li>
              <li>
                <span className="text-medium font-semibold">Medium Risk:</span> Enhanced
                monitoring and targeted improvements are advised.
              </li>
              <li>
                <span className="text-low font-semibold">Low Risk:</span> The business is
                performing well; regular oversight is recommended.
              </li>
            </ul>
          </li>
        </ul>

        <div className="mt-6">
          <h3 className="text-lg font-semibold text-primary mb-2">Risk Matrix</h3>
          <table className="min-w-full border border-gray-300">
            <thead>
              <tr className="bg-gray-200">
                <th className="border px-4 py-2">Risk Level</th>
                <th className="border px-4 py-2">Score Range</th>
                <th className="border px-4 py-2">Recommendation</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border px-4 py-2 text-high font-semibold">High Risk</td>
                <td className="border px-4 py-2">≥ 2.00</td>
                <td className="border px-4 py-2">Immediate corrective actions required</td>
              </tr>
              <tr>
                <td className="border px-4 py-2 text-medium font-semibold">Medium Risk</td>
                <td className="border px-4 py-2">1.00 - 2.00</td>
                <td className="border px-4 py-2">
                  Enhanced monitoring and targeted improvements advised
                </td>
              </tr>
              <tr>
                <td className="border px-4 py-2 text-low font-semibold">Low Risk</td>
                <td className="border px-4 py-2">&lt; 1.00</td>
                <td className="border px-4 py-2">
                  Regular oversight recommended; maintain current practices
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="mt-8">
          <h3 className="text-lg font-semibold text-primary mb-2">
            Sponsors &amp; Bibliography
          </h3>
          <ul className="list-disc list-inside text-secondary space-y-1">
            <li>
              <strong>ISO 31000:</strong> Provides internationally recognized guidelines for risk
              management.
            </li>
            <li>
              <strong>Risk Matrix Principles:</strong> Utilized to assess both likelihood and
              impact.
            </li>
            <li>
              <strong>Regression-based Forecasting:</strong> Statistical methods to identify trends
              over time.
            </li>
            <li>
              <strong>World Economic Forum:</strong> Research on global risk trends.
            </li>
            <li>
              <strong>Deloitte Risk Assessment Models:</strong> Industry‑leading frameworks for
              financial and operational risk.
            </li>
            <li>
              <strong>Academic Research:</strong> Peer‑reviewed studies in statistical risk analysis
              and probability theory.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default RiskAnalysis;
