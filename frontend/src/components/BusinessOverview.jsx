import React, { useEffect, useState } from "react";
import axios from "axios";
import { useParams, useNavigate } from "react-router-dom";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";
import { BuildingOffice2Icon } from "@heroicons/react/24/solid"; // Icon integrated

const BusinessOverview = () => {
  // Original states
  const { businessName } = useParams();
  const navigate = useNavigate();
  const [businesses, setBusinesses] = useState([]);
  const [filteredBusinesses, setFilteredBusinesses] = useState([]);
  const [violations, setViolations] = useState([]);

  const [selectedBusiness, setSelectedBusiness] = useState("");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // NEW states
  const [searchQuery, setSearchQuery] = useState("");

  // Instead of numeric pagination, we do “Load More”
  const [itemsToShow, setItemsToShow] = useState(9); // number of cards initially
  const LOAD_INCREMENT = 9; // how many more cards to load each time

  const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

  // ------------------------------------------------------------------------
  // 1) Fetch businesses + violations
  // ------------------------------------------------------------------------
  useEffect(() => {
    axios
      .get(`${API_URL}/businesses`)
      .then((response) => {
        console.log("[BusinessOverview] Fetched business list:", response.data);
        // Sort ascending by name
        const sorted = response.data.sort((a, b) =>
          a.business_name.localeCompare(b.business_name)
        );
        setBusinesses(sorted);
        setFilteredBusinesses(sorted);
      })
      .catch((err) => {
        console.error("Error fetching businesses:", err);
        setError("Failed to load business list.");
      });

    axios
      .get(`${API_URL}/violations`)
      .then((resp) => {
        console.log("[BusinessOverview] Fetched violations:", resp.data);
        setViolations(resp.data);
      })
      .catch((err) => {
        console.error("Error fetching violations:", err);
      });
  }, [API_URL]);

  // ------------------------------------------------------------------------
  // 2) Fetch report for selectedBusiness
  // ------------------------------------------------------------------------
  useEffect(() => {
    if (!selectedBusiness) return;
    console.log("[BusinessOverview] Fetching report for:", selectedBusiness);
    setLoading(true);

    axios
      .get(`${API_URL}/api/generate_report/${encodeURIComponent(selectedBusiness)}`)
      .then((res) => {
        console.log("[BusinessOverview] Report fetched:", res.data);
        setReport(res.data);
        setError(null);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching report:", err);
        setError("Failed to load report.");
        setLoading(false);
      });
  }, [API_URL, selectedBusiness]);

  // ------------------------------------------------------------------------
  // 3) Auto-load if URL param is present
  // ------------------------------------------------------------------------
  useEffect(() => {
    if (businessName && !selectedBusiness) {
      console.log("[BusinessOverview] Auto-loading business:", businessName);
      setSelectedBusiness(businessName);
      setReport(null);
    }
  }, [businessName, selectedBusiness]);

  // ------------------------------------------------------------------------
  // 4) Filter businesses based on search
  // ------------------------------------------------------------------------
  useEffect(() => {
    if (!searchQuery) {
      setFilteredBusinesses(businesses);
      setItemsToShow(9); // reset to first "page" of load-more
      return;
    }
    const lowerQuery = searchQuery.toLowerCase();
    const filtered = businesses.filter((b) =>
      b.business_name.toLowerCase().includes(lowerQuery)
    );
    setFilteredBusinesses(filtered);
    setItemsToShow(9); // reset to initial items
  }, [searchQuery, businesses]);

  // ------------------------------------------------------------------------
  // 5) PDF & CSV Download
  // ------------------------------------------------------------------------
  const downloadPDF = () => {
    const input = document.getElementById("report-content");
    if (!input) return;
    html2canvas(input).then((canvas) => {
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("p", "mm", "a4");
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
      pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);
      pdf.save(`${selectedBusiness}_report.pdf`);
    });
  };

  const downloadCSV = () => {
    if (!report || !report.report_data) return;
    const data = report.report_data;
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += Object.keys(data).join(",") + "\n";
    csvContent += Object.values(data).join(",") + "\n";
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `${selectedBusiness}_report.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // ------------------------------------------------------------------------
  // 6) Compute open vs. closed ratio
  // ------------------------------------------------------------------------
  const getOpenClosedRatio = (bizName) => {
    const relevant = violations.filter((v) => v.business_name === bizName);
    const openCount = relevant.filter((v) => v.status === "Open").length;
    const closedCount = relevant.filter((v) => v.status === "Closed").length;
    if (openCount === 0 && closedCount === 0) {
      return "No violations logged.";
    }
    return `${openCount} open / ${closedCount} closed`;
  };

  // ------------------------------------------------------------------------
  // 7) Select a business from card
  // ------------------------------------------------------------------------
  const handleSelectBusiness = (name) => {
    setSelectedBusiness(name);
    setReport(null);
    navigate(`/business/${encodeURIComponent(name)}`);
  };

  // ------------------------------------------------------------------------
  // 8) Load More
  // ------------------------------------------------------------------------
  const handleLoadMore = () => {
    setItemsToShow((prev) => prev + LOAD_INCREMENT);
  };

  // ------------------------------------------------------------------------
  // 9) Render business cards with “Load More” approach
  // ------------------------------------------------------------------------
  const renderBusinessCards = () => {
    if (!filteredBusinesses.length) {
      return (
        <p className="text-center mt-6 text-secondary">
          No matching businesses.
        </p>
      );
    }

    // Slice up to itemsToShow
    const visibleBusinesses = filteredBusinesses.slice(0, itemsToShow);

    return (
      <>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6 mt-8">
          {visibleBusinesses.map((b, index) => {
            const ratioStr = getOpenClosedRatio(b.business_name);
            return (
              <div
                key={index}
                onClick={() => handleSelectBusiness(b.business_name)}
                className="cursor-pointer bg-white shadow-md rounded-lg p-4 border border-neutralBg hover:shadow-xl transition duration-300"
              >
                <h3 className="text-xl font-semibold text-secondary">
                  {b.business_name}
                </h3>
                <p className="text-secondary-light mt-2">
                  Risk Level:{" "}
                  <span
                    className={
                      b.risk_level === "High"
                        ? "text-high"
                        : b.risk_level === "Medium"
                        ? "text-medium"
                        : b.risk_level === "Low"
                        ? "text-low"
                        : "text-unknown"
                    }
                  >
                    {b.risk_level}
                  </span>
                </p>
                <p className="text-secondary-light">
                  Total Violations: {b.total_violations}
                </p>
                <p className="text-secondary-light">Open/Closed: {ratioStr}</p>
                <p className="text-secondary-light">Description: {b.description}</p>
                <p className="text-secondary-light">Location: {b.location}</p>
                <p className="text-secondary-light">Type: {b.business_type}</p>
              </div>
            );
          })}
        </div>

        {/* If we still have more businesses beyond itemsToShow, show Load More */}
        {itemsToShow < filteredBusinesses.length && (
          <div className="flex justify-center mt-6">
            <button
              onClick={handleLoadMore}
              className="px-4 py-2 bg-primary text-white rounded shadow hover:bg-primary-dark transition"
            >
              Load More
            </button>
          </div>
        )}
      </>
    );
  };

  // ------------------------------------------------------------------------
  // 10) Render the “enhanced summary”
  // ------------------------------------------------------------------------
  const renderEnhancedSummary = () => {
    if (!report || !report.report_data) return null;
    const data = report.report_data;

    const weighted = data["Weighted Risk Score"] != null
      ? parseFloat(data["Weighted Risk Score"]).toFixed(2)
      : "N/A";
    const advanced = data["Advanced Risk Score"] != null
      ? parseFloat(data["Advanced Risk Score"]).toFixed(2)
      : "N/A";
    const freqScore = data["Violation Frequency Score"] != null
      ? parseFloat(data["Violation Frequency Score"]).toFixed(2)
      : "N/A";
    const avgFine = data["Average Fine"] != null
      ? parseFloat(data["Average Fine"]).toFixed(2)
      : "N/A";

    const summary = {
      "Business Name": data["Business Name"] || selectedBusiness,
      "Risk Level": data["Risk Level"] || "N/A",
      "Total Violations": data["Total Violations"] || "N/A",
      "Total Fines": data["Total Fines"] || "N/A",
      "Last Violation Date": data["Last Violation Date"] || "N/A",
      "Unpaid Fines": data["Unpaid Fines"] || "N/A",
      "Advanced Risk Score": advanced,
      "Weighted Risk Score": weighted,
      "Industry Risk Factor": data["Industry Risk Factor"] || "N/A",
      "Violation Frequency Score": freqScore,
      "Inspection History": data["Inspection History"] || "N/A",
      "Average Fine": avgFine,
      "Description": data["Description"] || "No description provided.",
      "Location": data["Location"] || "Not provided.",
      "Business Type": data["Business Type"] || "Not specified.",
    };

    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6 mt-8">
        {Object.entries(summary).map(([key, value], index) => (
          <div
            key={index}
            className="bg-white shadow-md rounded-lg p-4 border border-neutralBg"
          >
            <h4 className="font-semibold text-secondary mb-1">{key}</h4>
            <p className="text-secondary-light">{value}</p>
          </div>
        ))}
      </div>
    );
  };

  // ------------------------------------------------------------------------
  // 11) Format & render the “report” text
  // ------------------------------------------------------------------------
  const formatReportText = (rawText) => {
    const lines = rawText.split("\n");
    let structuredBlocks = [];
    let currentHeading = null;
    let currentContent = [];

    const pushBlock = () => {
      if (currentHeading || currentContent.length) {
        structuredBlocks.push({ heading: currentHeading, content: [...currentContent] });
        currentHeading = null;
        currentContent = [];
      }
    };

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      if (
        trimmed.startsWith("OVERALL RISK ASSESSMENT") ||
        trimmed.startsWith("CATEGORIES & REPEATED OFFENSES") ||
        trimmed.startsWith("BENCHMARKS & TRENDS") ||
        trimmed.startsWith("NEXT STEPS") ||
        trimmed.startsWith("CONCLUSION")
      ) {
        pushBlock();
        currentHeading = trimmed;
      } else {
        currentContent.push(trimmed);
      }
    }
    pushBlock();
    return structuredBlocks;
  };

  const renderFormattedReport = () => {
    if (!report?.report) return null;
    const blocks = formatReportText(report.report);

    return blocks.map((block, idx) => (
      <div key={idx} className="mb-6">
        {block.heading && (
          <h3 className="text-xl font-bold text-secondary mb-2">{block.heading}</h3>
        )}
        {block.content.map((paragraph, pindex) => (
          <p key={pindex} className="text-secondary-light mb-2 whitespace-pre-line">
            {paragraph}
          </p>
        ))}
      </div>
    ));
  };

  // ------------------------------------------------------------------------
  // 12) Render final “detailed report” after a business is selected
  // ------------------------------------------------------------------------
  const renderReportView = () => {
    if (!report) return null;

    const bizNameInData = report.report_data["Business Name"] || selectedBusiness;

    return (
      <div className="mt-8">
        <div
          id="report-content"
          className="bg-white p-6 shadow rounded-lg mb-6 max-w-3xl mx-auto"
        >
          <h2 className="text-3xl font-extrabold mb-6 text-center text-primary">
            {bizNameInData}
          </h2>
          {renderFormattedReport()}
        </div>
        {renderEnhancedSummary()}
        <div className="mt-6 flex justify-center space-x-4">
          <button
            onClick={downloadPDF}
            className="px-6 py-2 bg-primary text-white rounded-lg shadow hover:bg-primary-dark transition"
          >
            Download PDF
          </button>
          <button
            onClick={downloadCSV}
            className="px-6 py-2 bg-low text-white rounded-lg shadow hover:bg-low-dark transition"
          >
            Download CSV
          </button>
        </div>
      </div>
    );
  };

  // ------------------------------------------------------------------------
  // 13) Return: show either business cards or the selected report
  // ------------------------------------------------------------------------
  return (
    <div className="container mx-auto p-6 pt-24 bg-neutralBg min-h-screen">
      {/* Heading with building icon integrated */}
      <h1 className="text-3xl font-bold text-primary flex items-center justify-center mb-6">
        <BuildingOffice2Icon className="w-8 h-8 mr-2" />
        Business Overview
      </h1>

      {/* Search Bar */}
      <div className="flex justify-center mb-4">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => {
            console.log("[BusinessOverview] Search input changed:", e.target.value);
            setSearchQuery(e.target.value);
            setReport(null);
          }}
          placeholder="Search business name..."
          className="border rounded-md p-2 text-lg w-full max-w-md text-secondary"
        />
      </div>

      {/* Business Selection Dropdown */}
      <div className="flex justify-center mb-6">
        <select
          value={selectedBusiness}
          onChange={(e) => {
            console.log("[BusinessOverview] Dropdown changed:", e.target.value);
            setSelectedBusiness(e.target.value);
            setReport(null);
            navigate(`/business/${encodeURIComponent(e.target.value)}`);
          }}
          className="border rounded-md p-2 text-lg w-full max-w-md text-secondary"
        >
          <option value="">Select a Business</option>
          {filteredBusinesses.map((b, index) => (
            <option key={index} value={b.business_name}>
              {b.business_name}
            </option>
          ))}
        </select>
      </div>

      {loading && <p className="text-center mt-6 text-secondary">Loading report...</p>}
      {error && <p className="text-center mt-6 text-high">{error}</p>}

      {/* If a business is selected and report is loaded => show report, else show cards */}
      {selectedBusiness && report ? renderReportView() : renderBusinessCards()}
    </div>
  );
};

export default BusinessOverview;
