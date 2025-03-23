import React, { useState, useEffect, useRef } from "react";
import { NavLink } from "react-router-dom";
import classNames from "classnames";
import {
  ExclamationTriangleIcon,
  ChartBarIcon,
  BuildingOffice2Icon,
  Squares2X2Icon,
  PresentationChartLineIcon
} from "@heroicons/react/24/solid";

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef();

  useEffect(() => {
    // Close the mobile menu if clicking outside of it
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <nav
      className="
        shadow-lg 
        fixed top-0 w-full z-50
        bg-gradient-to-r
        from-[#931A23]   /* deeper burgundy */
        via-[#B41F2B]    /* primary brand red */
        to-[#CE4257]     /* lighter pinkish-red */
      "
    >
      {/* Relative wrapper so the silhouette can be absolutely positioned */}
      <div className="relative">
        {/*
          Skyline silhouette:
          - 'auto 100%' means the height always matches the container (the row with your logo)
            while width scales proportionally (no distortion).
          - Anchored to 'right center' for horizontal right alignment, vertical center.
          - pointer-events-none so it doesn't block clicks on the nav.
          - If the banner is short, the image will be quite small, but not distorted.
        */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage: "url('/fujairah-skyline.png')",
            backgroundPosition: "right center",
            backgroundRepeat: "no-repeat",
            backgroundSize: "auto 100%",
            opacity: 0.2
          }}
        />

        {/* Branding + Mobile Menu Toggle */}
        <div className="relative container mx-auto flex items-center justify-between px-4 py-3 md:py-4">
          <div className="flex items-center space-x-2">
            <img
              src="/fujairah-municipality-logo.jpeg"
              alt="Logo"
              className="h-10 w-auto"
            />
            <span className="text-white font-bold text-xl md:text-2xl">
              Fujairah Municipality
            </span>
          </div>

          <button
            onClick={() => setIsOpen(!isOpen)}
            className="text-white text-2xl md:hidden focus:outline-none"
          >
            ☰
          </button>
        </div>
      </div>

      {/* Dropdown (mobile) / Inline Menu (desktop) */}
      <div
        ref={menuRef}
        className={classNames(
          isOpen ? "block" : "hidden",
          "absolute top-full left-0 w-full bg-primary-dark transform transition-all duration-300 ease-in-out z-50",
          "md:block md:static md:bg-transparent"
        )}
      >
        {/* 
          We wrap the nav links + the Fujairah Digital Government label 
          in a single row. The left ~75% is for links; the right ~25% has the text.
        */}
        <div className="md:flex md:items-center w-full justify-between">
          {/* Nav links on the left ~75% */}
          <div className="flex md:flex-row flex-col md:items-center md:w-3/4">
            {/* Dashboard */}
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                classNames(
                  "flex items-center px-4 py-2 text-white hover:bg-primary-dark md:hover:bg-transparent md:hover:text-gray-200 transition-colors rounded",
                  { "bg-primary-dark": isActive }
                )
              }
            >
              <Squares2X2Icon className="w-5 h-5 mr-1" />
              Dashboard
            </NavLink>

            {/* Risk Analysis */}
            <NavLink
              to="/risk"
              className={({ isActive }) =>
                classNames(
                  "flex items-center px-4 py-2 text-white hover:bg-primary-dark md:hover:bg-transparent md:hover:text-gray-200 transition-colors rounded",
                  { "bg-primary-dark": isActive }
                )
              }
            >
              <ChartBarIcon className="w-5 h-5 mr-1" />
              Risk Analysis
            </NavLink>

            {/* Violations */}
            <NavLink
              to="/violations"
              className={({ isActive }) =>
                classNames(
                  "flex items-center px-4 py-2 text-white hover:bg-primary-dark md:hover:bg-transparent md:hover:text-gray-200 transition-colors rounded",
                  { "bg-primary-dark": isActive }
                )
              }
            >
              <ExclamationTriangleIcon className="w-5 h-5 mr-1" />
              Violations
            </NavLink>

            {/* Violation Trends */}
            <NavLink
              to="/trends"
              className={({ isActive }) =>
                classNames(
                  "flex items-center px-4 py-2 text-white hover:bg-primary-dark md:hover:bg-transparent md:hover:text-gray-200 transition-colors rounded",
                  { "bg-primary-dark": isActive }
                )
              }
            >
              <PresentationChartLineIcon className="w-5 h-5 mr-1" />
              Violation Trends
            </NavLink>

            {/* Business Overview */}
            <NavLink
              to="/business"
              className={({ isActive }) =>
                classNames(
                  "flex items-center px-4 py-2 text-white hover:bg-primary-dark md:hover:bg-transparent md:hover:text-gray-200 transition-colors rounded",
                  { "bg-primary-dark": isActive }
                )
              }
            >
              <BuildingOffice2Icon className="w-5 h-5 mr-1" />
              Business Overview
            </NavLink>
          </div>

        {/* Fujairah Digital Government on right ~30%, no wrapping */}
          <div
            className="
              md:w-[30%]       /* Wider than 25%, so less chance of wrapping */
              px-4 
              text-white 
              text-right 
              mt-2 
              md:mt-0
              text-2xl 
              font-bold 
              leading-none
              whitespace-nowrap /* Prevent text from wrapping onto next line */
            "
          >
            Fujairah Digital Government
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
