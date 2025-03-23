/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // =========================================
        // Existing brand & risk palettes
        // =========================================
        primary: {
          DEFAULT: '#B41F2B',
          dark: '#931A23',
          light: '#CC2E38',
        },
        secondary: {
          DEFAULT: '#2B2B2B',
          light: '#3C3C3C',
        },
        neutralBg: '#F7F7F7',
        accent: {
          DEFAULT: '#007BFF',
          dark: '#0056B3',
          light: '#66B2FF',
        },
        low: {
          DEFAULT: '#28A745',
          dark: '#218838',
          light: '#71dd8a',
        },
        medium: {
          DEFAULT: '#FFC107',
          dark: '#E0A800',
          light: '#FFE08A',
        },
        high: {
          DEFAULT: '#B41F2B',
          dark: '#931A23',
          light: '#CC2E38',
        },
        unknown: {
          DEFAULT: '#A9A9A9',
          dark: '#808080',
          light: '#D3D3D3',
        },

        // =========================================
        // NEW: Department Status Colors
        // Mapping the snippet's 'bg-green-100', 'border-green-400', 'text-green-800', etc.
        // to "light", "DEFAULT", and "dark" variants in Tailwind
        // =========================================

        // "Open": green-based
        statusOpen: {
          light: '#DCFCE7',  // Tailwind green-100
          DEFAULT: '#4ADE80', // green-400
          dark: '#065F46',   // green-800
        },

        // "Pending"/"Awaiting": yellow-based
        statusPending: {
          light: '#FEF9C3',  // yellow-100
          DEFAULT: '#FACC15', // yellow-400
          dark: '#854D0E',   // yellow-800
        },

        // "Closed": gray-based
        statusClosed: {
          light: '#E5E7EB', // gray-200
          DEFAULT: '#9CA3AF', // gray-400
          dark: '#1F2937',  // gray-800
        },

        // "Legal": red-based
        statusLegal: {
          light: '#FEE2E2', // red-100
          DEFAULT: '#F87171', // red-400
          dark: '#991B1B',  // red-800
        },

        // "Inspection"/"Assigned": blue-based
        statusInspection: {
          light: '#DBEAFE', // blue-100
          DEFAULT: '#60A5FA', // blue-400
          dark: '#1E40AF',  // blue-800
        },

        // "NOC"/"Documents": purple-based
        statusDocuments: {
          light: '#E9D5FF', // purple-100
          DEFAULT: '#A78BFA', // purple-400
          dark: '#5B21B6',  // purple-800
        },
      },
      keyframes: {
        pulseSlow: {
          '0%, 100%': { opacity: '0.2' },
          '50%': { opacity: '0.4' },
        },
      },
      animation: {
        pulseSlow: 'pulseSlow 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
};
