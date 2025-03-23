import React, { useEffect, useState } from "react";
import axios from "axios";

const GeoHotspots = () => {
  const [hotspots, setHotspots] = useState([]);
  const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

  useEffect(() => {
    axios
      .get(`${API_URL}/trends/geo-hotspots`)
      .then((response) => setHotspots(response.data.slice(0, 5))) // Show top 5
      .catch((error) => console.error("Error fetching geo-hotspots:", error));
  }, [API_URL]);

  return (
    <div className="p-4 bg-white shadow-lg rounded-lg">
      {/* Heading using your secondary color */}
      <h2 className="text-lg font-semibold text-secondary mb-2">
        Violation Hotspots
      </h2>

      {/* List items using secondary-light for body text */}
      <ul className="list-disc list-inside text-secondary-light">
        {hotspots.map((spot, index) => (
          <li key={index} className="py-1">
            {/* Highlight the location using the accent color */}
            <span className="font-bold text-primary-dark">{spot.location}</span> -{" "}
            {spot.total_violations} Violations
          </li>
        ))}
      </ul>
    </div>
  );
};

export default GeoHotspots;
