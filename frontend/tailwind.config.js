/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        "primary-blue": "#1c2b56",
        "secondary-blue": "#0d152b",
        "primary-yellow": "#ffb549",
        "secondary-yellow": "#ffd392",
      },
    },
  },
  plugins: [],
};
