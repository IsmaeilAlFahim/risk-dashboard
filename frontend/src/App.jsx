import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from "react-router-dom";
import Navbar from "./components/Navbar";
import Dashboard from "./components/Dashboard";
import RiskAnalysis from "./components/RiskAnalysis";
import ViolationTrends from "./components/ViolationTrends";
import BusinessOverview from "./components/BusinessOverview";
import ViolationList from "./components/ViolationList";
import Footer from "./components/Footer";
import LandingPage from "./components/LandingPage";
import ViolationDetails from "./components/ViolationDetails";

// 404 component with updated branding & styling
const NotFound = () => (
  <div className="flex flex-col items-center justify-center h-screen bg-neutralBg">
    {/* 
      Use your custom brand color for the main 404 heading.
      text-primary => #B41F2B (Default) 
    */}
    <h1 className="text-6xl font-extrabold text-primary">404</h1>

    {/*
      Switch from `text-gray-700` to a brand-friendly color.
      You could use `text-secondary` (#2B2B2B) for consistency.
    */}
    <p className="text-lg text-secondary mt-2">
      Oops! The page you are looking for does not exist.
    </p>

    {/*
      Instead of an <a> tag, use <Link> for SPA navigation.
      The button uses your .btn.btn-primary classes from index.css
      which map to bg-primary + hover:bg-primary-dark
    */}
    <Link to="/" className="btn btn-primary mt-4">
      Go to Home
    </Link>
  </div>
);

const App = () => {
  return (
    <Router>
      <div className="bg-neutralBg min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-grow">
          <Routes>
            {/* Landing Page */}
            <Route path="/" element={<LandingPage />} />

            {/* Dashboard */}
            <Route path="/dashboard" element={<Dashboard />} />

            {/* Additional routes */}
            <Route path="/risk" element={<RiskAnalysis />} />
            <Route path="/trends" element={<ViolationTrends />} />
            <Route path="/business/:businessName?" element={<BusinessOverview />} />
            <Route path="/violations" element={<ViolationList />} />
            <Route path="/violation/:id" element={<ViolationDetails />} />

            {/* 404 fallback */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
};

export default App;
