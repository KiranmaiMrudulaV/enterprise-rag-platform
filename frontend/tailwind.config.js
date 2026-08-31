/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#191C28",
        teal: "#005C5C",
      },
    },
  },
  plugins: [],
};
