import React, { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ExclamationTriangleIcon } from "@heroicons/react/24/solid";

const ViolationList = () => {
  // ---------------------------
  // 1) Data: all violations
  // ---------------------------
  const [violations, setViolations] = useState([]);

  // Distinct fields for dropdown data
  const [distinctCategories, setDistinctCategories] = useState([]);
  const [distinctTypes, setDistinctTypes] = useState([]);
  const [distinctStatuses, setDistinctStatuses] = useState([]);

  // ---------------------------
  // 2) UI States (inputs before 'Search')
  // ---------------------------
  const [uiBusinessName, setUiBusinessName] = useState("");
  const [uiViolationType, setUiViolationType] = useState("");
  const [uiCategory, setUiCategory] = useState("");
  const [uiStatus, setUiStatus] = useState("");
  const [uiStartDate, setUiStartDate] = useState("");
  const [uiEndDate, setUiEndDate] = useState("");

  // ---------------------------
  // 3) Actual Filter States
  // ---------------------------
  const [filterBusinessName, setFilterBusinessName] = useState("");
  const [filterViolationType, setFilterViolationType] = useState("");
  const [filterCategory, setFilterCategory] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterStartDate, setFilterStartDate] = useState("");
  const [filterEndDate, setFilterEndDate] = useState("");

  // ---------------------------
  // Sorting & Pagination
  // ---------------------------
  const [sortField, setSortField] = useState("timestamp"); // Default sort
  const [sortOrder, setSortOrder] = useState("desc");      // Default order
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Final filtered array
  const [filteredData, setFilteredData] = useState([]);
  const [expandedRowId, setExpandedRowId] = useState(null);

  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

  // ----------------------------------------------------------------------------
  // A) Fetch violations
  // ----------------------------------------------------------------------------
  useEffect(() => {
    axios
      .get(`${API_URL}/violations`)
      .then((res) => {
        setViolations(res.data);
      })
      .catch((err) => console.error("Error fetching violations:", err));
  }, [API_URL]);

  // ----------------------------------------------------------------------------
  // B) Fetch distinct fields (categories, types, statuses)
  // ----------------------------------------------------------------------------
  useEffect(() => {
    axios
      .get(`${API_URL}/violations/distinct-fields`)
      .then((res) => {
        setDistinctCategories(res.data.categories || []);
        setDistinctTypes(res.data.violationTypes || []);
        setDistinctStatuses(res.data.statuses || []);
      })
      .catch((err) => {
        console.error("Error fetching distinct fields:", err);
      });
  }, [API_URL]);

  // ----------------------------------------------------------------------------
  // C) Read query params => update UI & filter states => immediate auto‑search
  // ----------------------------------------------------------------------------
  useEffect(() => {
    let updated = false;

    const paramMonth = searchParams.get("month");
    const paramBiz = searchParams.get("businessName");
    const paramType = searchParams.get("violationType");
    const paramCat = searchParams.get("category");
    const paramStatus = searchParams.get("status");

    // If there's a "month" param, set date range
    if (paramMonth) {
      const [yr, mn] = paramMonth.split("-");
      if (yr && mn) {
        const startD = new Date(parseInt(yr), parseInt(mn) - 1, 1);
        const endD = new Date(parseInt(yr), parseInt(mn), 0);
        const startStr = startD.toISOString().split("T")[0];
        const endStr = endD.toISOString().split("T")[0];

        setUiStartDate(startStr);
        setUiEndDate(endStr);
        setFilterStartDate(startStr);
        setFilterEndDate(endStr);
        updated = true;
      }
    }
    // businessName
    if (paramBiz) {
      setUiBusinessName(paramBiz);
      setFilterBusinessName(paramBiz);
      updated = true;
    }
    // violationType
    if (paramType) {
      setUiViolationType(paramType);
      setFilterViolationType(paramType);
      updated = true;
    }
    // category
    if (paramCat) {
      setUiCategory(paramCat);
      setFilterCategory(paramCat);
      updated = true;
    }
    // status
    if (paramStatus) {
      setUiStatus(paramStatus);
      setFilterStatus(paramStatus);
      updated = true;
    }

    if (updated) {
      setCurrentPage(1);
    }
  }, [searchParams]);

  // ----------------------------------------------------------------------------
  // D) Filter + sort data
  // ----------------------------------------------------------------------------
  useEffect(() => {
    let data = [...violations];

    // -- Filter Logic --
    const bnLow = filterBusinessName.trim().toLowerCase();
    if (bnLow && bnLow !== "all") {
      data = data.filter((v) => v.business_name.toLowerCase().includes(bnLow));
    }

    const vtLow = filterViolationType.trim().toLowerCase();
    if (vtLow && vtLow !== "all") {
      data = data.filter(
        (v) =>
          v.violation_type &&
          v.violation_type.toLowerCase().includes(vtLow)
      );
    }

    const catLow = filterCategory.trim().toLowerCase();
    if (catLow && catLow !== "all") {
      data = data.filter(
        (v) => v.category && v.category.toLowerCase().includes(catLow)
      );
    }

    const stLow = filterStatus.trim().toLowerCase();
    if (stLow && stLow !== "all") {
      data = data.filter(
        (v) => v.status && v.status.toLowerCase() === stLow
      );
    }

    if (filterStartDate && filterStartDate.toLowerCase() !== "all") {
      const sDate = new Date(filterStartDate);
      data = data.filter((v) => {
        if (!v.timestamp) return false;
        const vDate = new Date(v.timestamp);
        return vDate >= sDate;
      });
    }
    if (filterEndDate && filterEndDate.toLowerCase() !== "all") {
      const eDate = new Date(filterEndDate);
      eDate.setHours(23, 59, 59, 999);
      data = data.filter((v) => {
        if (!v.timestamp) return false;
        const vDate = new Date(v.timestamp);
        return vDate <= eDate;
      });
    }

    // -- Sort Logic --
    data.sort((a, b) => {
      let valA, valB;
      switch (sortField) {
        case "timestamp":
          valA = a.timestamp;
          valB = b.timestamp;
          break;
        case "fine":
          valA = a.fine;
          valB = b.fine;
          break;
        case "business_name":
          valA = a.business_name.toLowerCase();
          valB = b.business_name.toLowerCase();
          break;
        case "violation_type":
          valA = (a.violation_type || "").toLowerCase();
          valB = (b.violation_type || "").toLowerCase();
          break;
        default:
          valA = a[sortField] || "";
          valB = b[sortField] || "";
      }

      // If sorting by date
      if (sortField === "timestamp" && valA && valB) {
        valA = new Date(valA).getTime();
        valB = new Date(valB).getTime();
      }

      if (valA < valB) return sortOrder === "asc" ? -1 : 1;
      if (valA > valB) return sortOrder === "asc" ? 1 : -1;
      return 0;
    });

    setFilteredData(data);
    setCurrentPage(1);
  }, [
    violations,
    filterBusinessName,
    filterViolationType,
    filterCategory,
    filterStatus,
    filterStartDate,
    filterEndDate,
    sortField,
    sortOrder
  ]);

  // Expand row
  const toggleExpand = (id) => {
    setExpandedRowId(expandedRowId === id ? null : id);
  };

  const handleBusinessClick = (bizName) => {
    navigate(`/business/${encodeURIComponent(bizName)}`);
  };

  const handleViewDetails = (vID) => {
    navigate(`/violation/${vID}`);
  };

  // "Search" => copy UI -> filter states
  const handleSearch = () => {
    setFilterBusinessName(uiBusinessName);
    setFilterViolationType(uiViolationType);
    setFilterCategory(uiCategory);
    setFilterStatus(uiStatus);
    setFilterStartDate(uiStartDate);
    setFilterEndDate(uiEndDate);
    setCurrentPage(1);
  };

  // Helper to set both field & direction
  const handleSortColumn = (field, direction) => {
    setSortField(field);
    setSortOrder(direction);
  };

  // Show two arrows (▲, ▼) for each column, highlight the active arrow
  const renderArrowsForColumn = (field) => {
    const isAscActive = sortField === field && sortOrder === "asc";
    const isDescActive = sortField === field && sortOrder === "desc";

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
            (isAscActive ? "text-primary-dark font-bold" : "text-secondary-light")
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
            (isDescActive ? "text-primary-dark font-bold" : "text-secondary-light")
          }
        >
          ▼
        </span>
      </span>
    );
  };

  // Pagination
  const totalCount = filteredData.length;
  const totalPages = Math.ceil(totalCount / pageSize);
  const currentPageData = filteredData.slice(
    (currentPage - 1) * pageSize,
    (currentPage - 1) * pageSize + pageSize
  );

  return (
    <div className="min-h-screen pt-24 px-4 bg-neutralBg">
      <div className="bg-white shadow-lg rounded-lg p-4">
        {/* Heading */}
        <h1 className="flex items-center justify-center text-3xl font-bold mb-4 text-primary">
          <ExclamationTriangleIcon className="w-8 h-8 mr-2" />
          Violations
        </h1>

        {/* Filter UI */}
        <div className="bg-neutralBg p-4 rounded mb-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Business */}
            <div>
              <label className="block text-sm font-semibold text-secondary mb-1">
                Business
              </label>
              <input
                type="text"
                value={uiBusinessName}
                onChange={(e) => setUiBusinessName(e.target.value)}
                placeholder="(or 'all')"
                className="w-full border px-2 py-1 rounded text-secondary"
              />
            </div>

            {/* Violation Type */}
            <div>
              <label className="block text-sm font-semibold text-secondary mb-1">
                Violation Type
              </label>
              <select
                value={uiViolationType}
                onChange={(e) => setUiViolationType(e.target.value)}
                className="w-full border px-2 py-1 rounded text-secondary"
              >
                <option value="">(Select or 'all')</option>
                <option value="all">All</option>
                {distinctTypes.map((vt) => (
                  <option key={vt} value={vt}>
                    {vt}
                  </option>
                ))}
              </select>
            </div>

            {/* Category */}
            <div>
              <label className="block text-sm font-semibold text-secondary mb-1">
                Category
              </label>
              <select
                value={uiCategory}
                onChange={(e) => setUiCategory(e.target.value)}
                className="w-full border px-2 py-1 rounded text-secondary"
              >
                <option value="">(Select or 'all')</option>
                <option value="all">All</option>
                {distinctCategories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            {/* Status */}
            <div>
              <label className="block text-sm font-semibold text-secondary mb-1">
                Status
              </label>
              <select
                value={uiStatus}
                onChange={(e) => setUiStatus(e.target.value)}
                className="w-full border px-2 py-1 rounded text-secondary"
              >
                <option value="">(Select or 'all')</option>
                <option value="all">All</option>
                {distinctStatuses.map((st) => (
                  <option key={st} value={st}>
                    {st}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Date Range */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <div>
              <label className="block text-sm font-semibold text-secondary mb-1">
                Start Date
              </label>
              <input
                type="date"
                value={uiStartDate}
                onChange={(e) => setUiStartDate(e.target.value)}
                className="w-full border px-2 py-1 rounded text-secondary"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-secondary mb-1">
                End Date
              </label>
              <input
                type="date"
                value={uiEndDate}
                onChange={(e) => setUiEndDate(e.target.value)}
                className="w-full border px-2 py-1 rounded text-secondary"
              />
            </div>
          </div>

          {/* Search Button */}
          <div className="mt-4 flex justify-center">
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-primary text-white rounded hover:bg-primary-dark"
            >
              Search
            </button>
          </div>
        </div>

        {/* Main Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full border border-gray-300 bg-white rounded-lg">
            <thead>
              {/* Table Header */}
              <tr className="bg-primary-light text-white">
                {/* Business Name */}
                <th className="border px-4 py-2">
                  <div className="flex items-center">
                    <span className="mr-2">Business</span>
                    {renderArrowsForColumn("business_name")}
                  </div>
                </th>
                {/* Violation Type */}
                <th className="border px-4 py-2">
                  <div className="flex items-center">
                    <span className="mr-2">Violation Type</span>
                    {renderArrowsForColumn("violation_type")}
                  </div>
                </th>
                {/* Fine */}
                <th className="border px-4 py-2">
                  <div className="flex items-center">
                    <span className="mr-2">Fine (AED)</span>
                    {renderArrowsForColumn("fine")}
                  </div>
                </th>
                {/* Timestamp */}
                <th className="border px-4 py-2">
                  <div className="flex items-center">
                    <span className="mr-2">Date</span>
                    {renderArrowsForColumn("timestamp")}
                  </div>
                </th>
                {/* Actions */}
                <th className="border px-4 py-2">Actions</th>
              </tr>
            </thead>

            <tbody>
              {filteredData.length > 0 ? (
                currentPageData.map((v) => (
                  <React.Fragment key={v.id}>
                    <tr
                      className="border-t bg-neutralBg hover:bg-gray-100 cursor-pointer"
                      onClick={() => toggleExpand(v.id)}
                    >
                      {/* Business Name */}
                      <td className="border px-4 py-2">
                        <span
                          className="text-primary-dark font-semibold hover:underline"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleBusinessClick(v.business_name);
                          }}
                        >
                          {v.business_name}
                        </span>
                      </td>

                      {/* Violation Type */}
                      <td className="border px-4 py-2 text-secondary">
                        {v.violation_type}
                      </td>

                      {/* Fine */}
                      <td className="border px-4 py-2 font-semibold text-primary">
                        {v.fine} AED
                      </td>

                      {/* Date */}
                      <td className="border px-4 py-2 text-secondary">
                        {v.timestamp
                          ? new Date(v.timestamp).toLocaleString()
                          : "N/A"}
                      </td>

                      {/* Actions */}
                      <td
                        className="border px-4 py-2 text-center"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          onClick={() => handleViewDetails(v.id)}
                          className="px-3 py-1 bg-primary text-white rounded hover:bg-primary-dark"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>

                    {/* Expanded Row */}
                    {expandedRowId === v.id && (
                      <tr className="bg-white">
                        <td colSpan={5} className="border px-4 py-2 text-sm text-secondary">
                          <div className="flex flex-col space-y-2">
                            <div>
                              <strong>Category:</strong> {v.category}
                            </div>
                            <div>
                              <strong>Status:</strong> {v.status}
                            </div>
                            <div>
                              <strong>Severity:</strong> {v.severity}
                            </div>
                            {v.resolution_date && (
                              <div>
                                <strong>Resolution Date:</strong>{" "}
                                {new Date(v.resolution_date).toLocaleString()}
                              </div>
                            )}
                            {v.corrective_actions && (
                              <div>
                                <strong>Corrective Actions:</strong>{" "}
                                {v.corrective_actions}
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))
              ) : (
                <tr>
                  <td
                    colSpan={5}
                    className="border px-4 py-2 text-center text-secondary-light"
                  >
                    No records found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex justify-center items-center space-x-2 mt-4">
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
            <option value={50}>50 per page</option>
          </select>
        </div>
      </div>
    </div>
  );
};

export default ViolationList;
