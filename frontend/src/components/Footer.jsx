import React from "react";

const Footer = () => {
  return (
    <footer className="bg-gray-900 text-gray-300 text-center py-4 mt-8 text-sm sm:text-base">
      <p>
        © {new Date().getFullYear()} Fujairah Municipality. All rights reserved.
      </p>
    </footer>
  );
};

export default Footer;
