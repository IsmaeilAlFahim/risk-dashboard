import React, { useEffect, useState } from "react";
import axios from "axios";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Legend,
  BarChart,
  Bar
} from "recharts";
import API_URL from "../config";
import { useNavigate } from "react-router-dom";

// For heading icon consistency (if you want an icon next to the text):
import { PresentationChartLineIcon } from "@heroicons/react/24/solid";

/**
 * Map your risk levels to the same hex codes used in your Tailwind config.
 * 
 * tailwind.config.js includes:
 * high:    { DEFAULT: '#B41F2B', dark: '#931A23', light: '#CC2E38' },
 * medium:  { DEFAULT: '#FFC107', ... },
 * low:     { DEFAULT: '#28A745', ... },
 * unknown: { DEFAULT: '#A9A9A9', ... },
 */
const riskColors = {
  High: "#B41F2B",    // colors.high.DEFAULT
  Medium: "#FFC107",  // colors.medium.DEFAULT
  Low: "#28A745",     // colors.low.DEFAULT
  Unknown: "#A9A9A9", // colors.unknown.DEFAULT
};

const ViolationTrends = () => {
  // --------------------------------------------------------------------------
  // Main data states
  // --------------------------------------------------------------------------
  const [trendData, setTrendData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);      // For line chart
  const [filteredRawData, setFilteredRawData] = useState([]); // For bar chart

  // Filter states
  const [companies, setCompanies] = useState([]);
  const [violationTypes, setViolationTypes] = useState([]);
  const [categories, setCategories] = useState([]);

  const [selectedCompany, setSelectedCompany] = useState("");
  const [selectedViolation, setSelectedViolation] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedTimeRange, setSelectedTimeRange] = useState("12 Months");

  // Chart view: "line", "bar", or "comparison"
  const [chartView, setChartView] = useState("line");

  // Risk mapping for bar chart
  const [riskMapping, setRiskMapping] = useState({});

  // Comparison view states
  const [selectedCompanyComparison1, setSelectedCompanyComparison1] = useState("");
  const [selectedCompanyComparison2, setSelectedCompanyComparison2] = useState("");
  const [comparisonData, setComparisonData] = useState([]);

  // Navigation
  const navigate = useNavigate();

  // Time-range filter options
  const timeRangeOptions = ["12 Months", "6 Months", "3 Months", "All Data"];

  // --------------------------------------------------------------------------
  // 1) Fetch raw trend data
  // --------------------------------------------------------------------------
  useEffect(() => {
    const fetchTrends = async () => {
      try {
        const endpoint =
          selectedTimeRange === "All Data"
            ? `${API_URL}/trends/violations/all`
            : `${API_URL}/trends/violations`;

        const response = await axios.get(endpoint);
        console.log("[ViolationTrends] fetched trends:", response.data);
        setTrendData(response.data);
      } catch (error) {
        console.error("[ViolationTrends] error fetching trends:", error);
      }
    };

    fetchTrends();
  }, [selectedTimeRange]);

  // --------------------------------------------------------------------------
  // 2) Fetch businesses
  // --------------------------------------------------------------------------
  useEffect(() => {
    axios
      .get(`${API_URL}/businesses`)
      .then((res) => {
        const names = res.data.map((b) => b.business_name);
        const unique = ["", ...new Set(names)];
        setCompanies(unique);

        // Optional defaults for comparison
        if (unique.length > 2) {
          setSelectedCompanyComparison1(unique[1]);
          setSelectedCompanyComparison2(unique[2]);
        }
      })
      .catch((err) => console.error("[ViolationTrends] error fetching businesses:", err));
  }, []);

  // --------------------------------------------------------------------------
  // 3) Fetch all violations => distinct violation types + categories
  // --------------------------------------------------------------------------
  useEffect(() => {
    axios
      .get(`${API_URL}/violations`)
      .then((res) => {
        console.log("[ViolationTrends] fetched violations for type/category:", res.data);
        const distinctTypes = [...new Set(res.data.map((v) => v.violation_type || ""))];
        const distinctCats = [...new Set(res.data.map((v) => v.category || ""))];

        setViolationTypes(["", ...distinctTypes]);
        setCategories(["", ...distinctCats]);
      })
      .catch((err) => console.error("[ViolationTrends] error fetching violations:", err));
  }, []);

  // --------------------------------------------------------------------------
  // 3.5) Fetch risk => for stacked bar logic
  // --------------------------------------------------------------------------
  useEffect(() => {
    axios
      .get(`${API_URL}/risk`)
      .then((response) => {
        console.log("[ViolationTrends] Fetched Risk Mapping:", response.data);
        const mapping = {};
        response.data.forEach((item) => {
          // Convert to lowercase so we can easily match item.business_name
          mapping[item.business_name.trim().toLowerCase()] = item.risk_level;
        });
        setRiskMapping(mapping);
      })
      .catch((error) => console.error("[ViolationTrends] error fetching risk mapping:", error));
  }, []);

  // --------------------------------------------------------------------------
  // 4) Aggregation helpers
  // --------------------------------------------------------------------------
  const aggregateByMonth = (data) => {
    const agg = {};
    data.forEach((item) => {
      if (!agg[item.month]) {
        agg[item.month] = { month: item.month, total_violations: 0 };
      }
      agg[item.month].total_violations += item.total_violations;
    });
    return Object.values(agg).sort((a, b) => a.month.localeCompare(b.month));
  };

  const aggregateByMonthAndRisk = (data) => {
    if (Object.keys(riskMapping).length === 0) return [];
    const aggregator = {};
    data.forEach((item) => {
      // Default to "Unknown" if risk not found
      const level = riskMapping[item.business_name.trim().toLowerCase()] || "Unknown";
      if (!aggregator[item.month]) {
        aggregator[item.month] = {
          month: item.month,
          High: 0,
          Medium: 0,
          Low: 0,
          Unknown: 0,
        };
      }
      aggregator[item.month][level] += item.total_violations;
    });
    return Object.values(aggregator).sort((a, b) => a.month.localeCompare(b.month));
  };

  // --------------------------------------------------------------------------
  // 5) Filter logic for line/bar
  // --------------------------------------------------------------------------
  useEffect(() => {
    // Skip if in comparison view
    if (chartView === "comparison") return;

    let filtered = [...trendData];

    // Filter by business
    if (selectedCompany) {
      filtered = filtered.filter((item) => item.business_name === selectedCompany);
    }
    // Filter by violation type
    if (selectedViolation) {
      filtered = filtered.filter((item) => item.violation_type === selectedViolation);
    }
    // Filter by category
    if (selectedCategory) {
      filtered = filtered.filter((item) => item.category === selectedCategory);
    }

    // Time range
    if (selectedTimeRange !== "All Data") {
      let minDate = null;
      const now = new Date();

      if (selectedTimeRange === "12 Months") {
        now.setMonth(now.getMonth() - 12);
        now.setDate(1);
        minDate = now;
      } else if (selectedTimeRange === "6 Months") {
        now.setMonth(now.getMonth() - 6);
        now.setDate(1);
        minDate = now;
      } else if (selectedTimeRange === "3 Months") {
        now.setMonth(now.getMonth() - 3);
        now.setDate(1);
        minDate = now;
      }

      if (minDate) {
        // e.g., item.month => "2024-07"
        filtered = filtered.filter((item) => new Date(item.month + "-01") >= minDate);
      }
    }

    setFilteredRawData(filtered);

    // Aggregate for line chart
    const aggregated = aggregateByMonth(filtered);
    setFilteredData(aggregated);
  }, [
    selectedCompany,
    selectedViolation,
    selectedCategory,
    selectedTimeRange,
    trendData,
    chartView
  ]);

  // --------------------------------------------------------------------------
  // 6) Comparison view
  // --------------------------------------------------------------------------
  useEffect(() => {
    if (chartView !== "comparison") return;
    if (!selectedCompanyComparison1 || !selectedCompanyComparison2) return;

    const data1 = trendData.filter((item) => item.business_name === selectedCompanyComparison1);
    const data2 = trendData.filter((item) => item.business_name === selectedCompanyComparison2);

    const agg1 = aggregateByMonth(data1);
    const agg2 = aggregateByMonth(data2);

    const allMonths = Array.from(
      new Set([...agg1.map((x) => x.month), ...agg2.map((x) => x.month)])
    ).sort();

    const mergedArray = allMonths.map((m) => {
      const row = { month: m };
      const e1 = agg1.find((r) => r.month === m);
      const e2 = agg2.find((r) => r.month === m);
      row[selectedCompanyComparison1] = e1 ? e1.total_violations : 0;
      row[selectedCompanyComparison2] = e2 ? e2.total_violations : 0;
      return row;
    });

    setComparisonData(mergedArray);
  }, [chartView, selectedCompanyComparison1, selectedCompanyComparison2, trendData]);

  // --------------------------------------------------------------------------
  // 7) Chart Click => pass all needed filters to /violations
  // --------------------------------------------------------------------------
  const handleLineChartClick = (state) => {
    if (!state?.activePayload?.length) return;
    const { month = "" } = state.activePayload[0].payload || {};

    const link =
      `/violations?month=${encodeURIComponent(month)}` +
      `&businessName=${encodeURIComponent(selectedCompany || "")}` +
      `&violationType=${encodeURIComponent(selectedViolation || "")}` +
      `&category=${encodeURIComponent(selectedCategory || "")}`;

    navigate(link);
  };

  const handleBarChartClick = (state) => {
    if (!state?.activePayload?.length) return;
    const { month = "" } = state.activePayload[0].payload || {};

    const link =
      `/violations?month=${encodeURIComponent(month)}` +
      `&businessName=${encodeURIComponent(selectedCompany || "")}` +
      `&violationType=${encodeURIComponent(selectedViolation || "")}` +
      `&category=${encodeURIComponent(selectedCategory || "")}`;

    navigate(link);
  };

  // --------------------------------------------------------------------------
  // Return
  // --------------------------------------------------------------------------
  return (
    <div className="mt-24 p-6 bg-neutralBg shadow-lg rounded-lg min-h-screen">
      {/* Page Heading with icon for consistency */}
      <h1 className="text-3xl font-bold text-primary mb-4 text-center flex items-center justify-center">
        <PresentationChartLineIcon className="w-8 h-8 mr-2" />
        Violation Trends
      </h1>

      {/* Filter Container */}
      {chartView !== "comparison" ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6 p-4 bg-white shadow rounded-md">
          {/* Business */}
          <div>
            <label className="block text-secondary font-semibold mb-1">Business:</label>
            <select
              className="border px-4 py-2 rounded-md shadow-md w-full text-sm bg-white focus:ring-2 focus:ring-primary-dark"
              value={selectedCompany}
              onChange={(e) => setSelectedCompany(e.target.value)}
            >
              <option value="">(No filter)</option>
              {companies.map((comp) => (
                <option key={comp} value={comp}>
                  {comp}
                </option>
              ))}
            </select>
          </div>

          {/* Violation Type */}
          <div>
            <label className="block text-secondary font-semibold mb-1">Violation Type:</label>
            <select
              className="border px-4 py-2 rounded-md shadow-md w-full text-sm bg-white focus:ring-2 focus:ring-primary-dark"
              value={selectedViolation}
              onChange={(e) => setSelectedViolation(e.target.value)}
            >
              <option value="">(No filter)</option>
              {violationTypes.map((vt) => (
                <option key={vt} value={vt}>
                  {vt}
                </option>
              ))}
            </select>
          </div>

          {/* Category */}
          <div>
            <label className="block text-secondary font-semibold mb-1">Category:</label>
            <select
              className="border px-4 py-2 rounded-md shadow-md w-full text-sm bg-white focus:ring-2 focus:ring-primary-dark"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              <option value="">(No filter)</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          {/* Time Range */}
          <div>
            <label className="block text-secondary font-semibold mb-1">Time Range:</label>
            <select
              className="border px-4 py-2 rounded-md shadow-md w-full text-sm bg-white focus:ring-2 focus:ring-primary-dark"
              value={selectedTimeRange}
              onChange={(e) => setSelectedTimeRange(e.target.value)}
            >
              {timeRangeOptions.map((tr) => (
                <option key={tr} value={tr}>
                  {tr}
                </option>
              ))}
            </select>
          </div>
        </div>
      ) : (
        // Comparison filters
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6 p-4 bg-white shadow rounded-md">
          <div>
            <label className="block text-secondary font-semibold mb-1">
              Compare Company 1:
            </label>
            <select
              className="border px-4 py-2 rounded-md shadow-md w-full text-sm bg-white focus:ring-2 focus:ring-primary-dark"
              value={selectedCompanyComparison1}
              onChange={(e) => setSelectedCompanyComparison1(e.target.value)}
            >
              {companies
                .filter((c) => c)
                .map((comp) => (
                  <option key={comp} value={comp}>
                    {comp}
                  </option>
                ))}
            </select>
          </div>

          <div>
            <label className="block text-secondary font-semibold mb-1">
              Compare Company 2:
            </label>
            <select
              className="border px-4 py-2 rounded-md shadow-md w-full text-sm bg-white focus:ring-2 focus:ring-primary-dark"
              value={selectedCompanyComparison2}
              onChange={(e) => setSelectedCompanyComparison2(e.target.value)}
            >
              {companies
                .filter((c) => c)
                .map((comp) => (
                  <option key={comp} value={comp}>
                    {comp}
                  </option>
                ))}
            </select>
          </div>
        </div>
      )}

      {/* Chart View Buttons */}
      <div className="flex justify-center space-x-4 mb-4">
        <button
          onClick={() => setChartView("line")}
          className={`px-4 py-2 rounded-md shadow transition ${
            chartView === "line"
              ? "bg-primary text-white"
              : "bg-white text-secondary border border-secondary-light"
          }`}
        >
          Overall Trend
        </button>
        <button
          onClick={() => setChartView("bar")}
          className={`px-4 py-2 rounded-md shadow transition ${
            chartView === "bar"
              ? "bg-primary text-white"
              : "bg-white text-secondary border border-secondary-light"
          }`}
        >
          Risk Breakdown
        </button>
        <button
          onClick={() => setChartView("comparison")}
          className={`px-4 py-2 rounded-md shadow transition ${
            chartView === "comparison"
              ? "bg-primary text-white"
              : "bg-white text-secondary border border-secondary-light"
          }`}
        >
          Comparison View
        </button>
      </div>

      {/* Chart Container */}
      <div className="flex justify-center">
        <ResponsiveContainer width="100%" height={400}>
          {chartView === "line" && (
            <LineChart data={filteredData} onClick={handleLineChartClick}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" stroke="#2B2B2B" />
              <YAxis stroke="#2B2B2B" />
              <Tooltip />
              <Legend />
              {/*
                Use accent color or primary color as desired.
                For example, #007BFF is your accent.DEFAULT
              */}
              <Line
                type="monotone"
                dataKey="total_violations"
                stroke="#007BFF"
                strokeWidth={2}
              />
            </LineChart>
          )}

          {chartView === "bar" && (
            <BarChart
              data={aggregateByMonthAndRisk(filteredRawData)}
              onClick={handleBarChartClick}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" stroke="#2B2B2B" />
              <YAxis stroke="#2B2B2B" />
              <Tooltip />
              <Legend />
              {/*
                Pull color codes from your tailwind config by referencing riskColors
              */}
              <Bar dataKey="High" stackId="a" fill={riskColors.High} />
              <Bar dataKey="Medium" stackId="a" fill={riskColors.Medium} />
              <Bar dataKey="Low" stackId="a" fill={riskColors.Low} />
              <Bar dataKey="Unknown" stackId="a" fill={riskColors.Unknown} />
            </BarChart>
          )}

          {chartView === "comparison" && (
            <LineChart data={comparisonData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" stroke="#2B2B2B" />
              <YAxis stroke="#2B2B2B" />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey={selectedCompanyComparison1}
                stroke={riskColors.High}  // For example
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey={selectedCompanyComparison2}
                stroke={riskColors.Low}   // For example
                strokeWidth={2}
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* No Data Messages */}
      {chartView === "line" && filteredData.length === 0 && (
        <p className="text-center text-primary mt-4">
          ⚠ No data available for the selected filters.
        </p>
      )}
      {chartView === "bar" && aggregateByMonthAndRisk(filteredRawData).length === 0 && (
        <p className="text-center text-primary mt-4">
          ⚠ No data available for the selected filters.
        </p>
      )}
      {chartView === "comparison" && comparisonData.length === 0 && (
        <p className="text-center text-primary mt-4">
          ⚠ No data available for the selected filters.
        </p>
      )}
    </div>
  );
};

export default ViolationTrends;
