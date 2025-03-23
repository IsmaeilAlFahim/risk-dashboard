import React from "react";
import { Link } from "react-router-dom";
import { RocketLaunchIcon } from "@heroicons/react/24/solid";

const LandingPage = () => {
  return (
    <div className="relative w-full min-h-screen flex items-center justify-center overflow-hidden bg-secondary">
      {/*
        Background pattern.
        - Adjust the opacity or remove if you prefer a simpler background.
      */}
      <div
        className="absolute inset-0 bg-cover bg-center opacity-30"
        style={{ backgroundImage: 'url("/fujairah-red-skyline.jpeg")' }}
      ></div>

      {/*
        Gradient overlay in brand colors.
        - Mix-blend-mode and opacity help blend it with the pattern.
      */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary.dark via-primary to-primary.light opacity-80 mix-blend-multiply" />

      {/*
        Main Content
        - Centered text + logo.
        - Text color is set to neutralBg (light) for contrast.
      */}
      <div className="relative z-10 flex flex-col items-center max-w-3xl mx-auto px-6 text-center text-neutralBg">
        {/* Logo */}
        <img
          src="/fujairah-municipality.png"
          alt="Fujairah Municipality"
          className="
            w-40 h-40 mb-6 
            drop-shadow-lg
            transition-transform
            duration-500
            hover:scale-105
          "
        />

        {/* Headline */}
        <h1
          className="
            text-4xl 
            sm:text-5xl 
            md:text-6xl 
            font-extrabold 
            leading-tight
            drop-shadow-md
            transition-all
            duration-700
          "
        >
          Fujairah Municipality Dashboard
        </h1>

        {/* Subtext */}
        <p className="mt-4 text-lg sm:text-xl md:text-2xl text-neutralBg/90 leading-relaxed">
          Monitor violations, risk levels, and analytics in real-time.
        </p>

        {/* CTA Button */}
        <Link
          to="/dashboard"
          className="
            group
            inline-flex
            items-center
            mt-8
            px-8
            py-3
            rounded-full
            bg-primary
            text-neutralBg
            font-medium
            text-lg
            shadow-lg
            ring-2
            ring-transparent
            transition-all
            duration-300
            hover:bg-primary.dark
            hover:shadow-2xl
            focus:outline-none
            focus:ring-primary.light
          "
        >
          <RocketLaunchIcon
            className="
              w-6
              h-6
              mr-2
              transition-transform
              duration-300
              group-hover:rotate-12
            "
          />
          Start Dashboard
        </Link>
      </div>

      {/*
        Floating Decorative Element (Optional)
        - Pulsing circle with brand color.
        - Remove if you prefer a simpler look.
      */}
      <div
        className="
          pointer-events-none
          absolute
          bottom-[-5rem]
          left-[-5rem]
          w-[30rem]
          h-[30rem]
          rounded-full
          bg-primary.light
          opacity-20
          blur-3xl
          animate-pulseSlow
        "
      ></div>
    </div>
  );
};

export default LandingPage;
