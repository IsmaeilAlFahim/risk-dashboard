import React, { useEffect, useState } from "react";
import axios from "axios";
import { useParams } from "react-router-dom";
import { format } from "date-fns";

const ViolationDetails = () => {
  const { id } = useParams();
  const [violation, setViolation] = useState(null);
  const [statusHistory, setStatusHistory] = useState([]);

  const [newStatus, setNewStatus] = useState("");
  const [newNotes, setNewNotes] = useState("");

  const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

  // 1) Fetch single violation
  useEffect(() => {
    axios
      .get(`${API_URL}/violations/${id}`)
      .then((res) => {
        console.log("[ViolationDetails] Single violation:", res.data);
        setViolation(res.data);
      })
      .catch((err) => {
        console.error("[ViolationDetails] Error fetching violation:", err);
      });
  }, [API_URL, id]);

  // 2) Fetch status history
  useEffect(() => {
    axios
      .get(`${API_URL}/violations/${id}/status-history`)
      .then((res) => {
        console.log("[ViolationDetails] Status history:", res.data);
        setStatusHistory(res.data);
      })
      .catch((err) => {
        console.error("[ViolationDetails] Error fetching status history:", err);
      });
  }, [API_URL, id]);

  // Add new status step
  const addNewStatusStep = () => {
    if (!newStatus.trim()) {
      alert("Status is required.");
      return;
    }
    axios
      .post(`${API_URL}/violations/${id}/status-history`, {
        status: newStatus,
        notes: newNotes,
      })
      .then((res) => {
        console.log("[ViolationDetails] New status added:", res.data);
        // Re-fetch the history
        axios
          .get(`${API_URL}/violations/${id}/status-history`)
          .then((resp) => setStatusHistory(resp.data))
          .catch((error) => console.error("Error re-fetching status history:", error));
        // Reset form
        setNewStatus("");
        setNewNotes("");
      })
      .catch((error) => {
        console.error("[ViolationDetails] Error adding status step:", error);
      });
  };

  // Format date/time
  const formatDateTime = (dtStr) => {
    if (!dtStr) return "N/A";
    const d = new Date(dtStr);
    return format(d, "yyyy-MM-dd HH:mm:ss");
  };

  /**
   * Map the snippet’s “color-coded style” to your updated
   * Tailwind classes in tailwind.config.js:
   *
   *   statusOpen:       light, DEFAULT, dark
   *   statusPending:    light, DEFAULT, dark
   *   statusClosed:     light, DEFAULT, dark
   *   statusLegal:      light, DEFAULT, dark
   *   statusInspection: light, DEFAULT, dark
   *   statusDocuments:  light, DEFAULT, dark
   */
  const getStatusStyle = (statusName = "") => {
    const normalized = statusName.toLowerCase();
    if (normalized.includes("open")) {
      // from "bg-green-100 border-green-400 text-green-800"
      return "bg-statusOpen-light border-statusOpen-DEFAULT text-statusOpen-dark";
    } else if (normalized.includes("pending") || normalized.includes("awaiting")) {
      // was "bg-yellow-100 border-yellow-400 text-yellow-800"
      return "bg-statusPending-light border-statusPending-DEFAULT text-statusPending-dark";
    } else if (normalized.includes("closed")) {
      // was "bg-gray-200 border-gray-400 text-gray-800"
      return "bg-statusClosed-light border-statusClosed-DEFAULT text-statusClosed-dark";
    } else if (normalized.includes("legal")) {
      // was "bg-red-100 border-red-400 text-red-800"
      return "bg-statusLegal-light border-statusLegal-DEFAULT text-statusLegal-dark";
    } else if (normalized.includes("inspection") || normalized.includes("assigned")) {
      // was "bg-blue-100 border-blue-400 text-blue-800"
      return "bg-statusInspection-light border-statusInspection-DEFAULT text-statusInspection-dark";
    } else if (normalized.includes("noc") || normalized.includes("documents")) {
      // was "bg-purple-100 border-purple-400 text-purple-800"
      return "bg-statusDocuments-light border-statusDocuments-DEFAULT text-statusDocuments-dark";
    }
    // default fallback
    return "bg-white border-gray-300 text-secondary";
  };

  if (!violation) {
    return (
      <div className="pt-24 px-4 bg-neutralBg min-h-screen">
        <p className="text-secondary">Loading violation details...</p>
      </div>
    );
  }

  return (
    <div className="pt-24 px-4 bg-neutralBg min-h-screen text-secondary">
      <div className="bg-white shadow-md rounded p-4 max-w-3xl mx-auto">
        {/* Heading */}
        <h1 className="text-2xl font-bold text-primary mb-4">
          Violation Details (ID #{violation.id})
        </h1>

        {/* Main Violation Info */}
        <div className="mb-4 space-y-2">
          <p>
            <strong>Business Name:</strong> {violation.business_name}
          </p>
          <p>
            <strong>Violation Type:</strong> {violation.violation_type}
          </p>
          <p>
            <strong>Category:</strong> {violation.category}
          </p>
          <p>
            <strong>Severity:</strong> {violation.severity}
          </p>
          <p>
            <strong>Fine:</strong> {violation.fine} AED
          </p>
          <p>
            <strong>Date:</strong> {violation.timestamp ? formatDateTime(violation.timestamp) : "N/A"}
          </p>
          <p>
            <strong>Status:</strong> {violation.status}
          </p>
          {violation.corrective_actions && (
            <p>
              <strong>Corrective Actions:</strong> {violation.corrective_actions}
            </p>
          )}
          {violation.resolution_date && (
            <p>
              <strong>Resolution Date:</strong> {formatDateTime(violation.resolution_date)}
            </p>
          )}
        </div>

        {/* Status History - vertical timeline */}
        <div className="mb-6 bg-neutralBg p-4 rounded shadow">
          <h2 className="text-lg font-semibold text-primary mb-2">Status History</h2>
          {statusHistory.length === 0 ? (
            <p>No status history recorded yet.</p>
          ) : (
            <div className="relative border-l border-gray-300 pl-6 ml-2">
              {statusHistory.map((sh, index) => {
                const statusClass = getStatusStyle(sh.status || "");
                return (
                  <div key={sh.id} className="mb-8 ml-2 relative">
                    {/* Circle indicator */}
                    <span className="absolute -left-4 flex items-center justify-center w-8 h-8 bg-primary text-white rounded-full">
                      {index + 1}
                    </span>
                    {/* Content Card */}
                    <div className={`flex flex-col shadow p-3 rounded-md border space-y-1 ${statusClass}`}>
                      <p className="font-semibold">
                        {sh.status}
                        <span className="text-sm ml-2 block sm:inline-block sm:ml-2 text-gray-600">
                          ({formatDateTime(sh.updated_at)})
                        </span>
                      </p>
                      <p className="text-sm">
                        {sh.notes || "No notes provided."}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Add New Status Step */}
        <div className="bg-white p-4 rounded shadow">
          <h3 className="text-lg font-semibold text-primary mb-3">Add New Status Step</h3>
          <div className="mb-2">
            <label className="block text-sm font-semibold mb-1">Status:</label>
            <input
              type="text"
              value={newStatus}
              onChange={(e) => setNewStatus(e.target.value)}
              placeholder="e.g. Pending Payment, In Legal Dept..."
              className="w-full border px-2 py-1 rounded text-secondary"
            />
          </div>
          <div className="mb-2">
            <label className="block text-sm font-semibold mb-1">Notes:</label>
            <textarea
              value={newNotes}
              onChange={(e) => setNewNotes(e.target.value)}
              placeholder="Additional details or memos"
              className="w-full border px-2 py-1 rounded text-secondary h-20"
            />
          </div>
          <button
            onClick={addNewStatusStep}
            className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded"
          >
            Submit
          </button>
        </div>
      </div>
    </div>
  );
};

export default ViolationDetails;
