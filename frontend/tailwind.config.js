/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // InstantMusic Brand Colors
        primary: {
          50: '#FEF2F2',
          100: '#FDE8E8',
          200: '#FACACA',
          300: '#F5A3A6',
          400: '#E8636B',
          500: '#DC3842',
          600: '#C42F38',
          700: '#B82D35',
          800: '#9A252C',
          900: '#7F1D22',
        },
        cream: {
          50: '#FDFBF9',
          100: '#f9efe7',
          200: '#F5E5D9',
          300: '#EDE3DA',
          400: '#E0D3C7',
          500: '#D4C4B5',
        },
        dark: {
          DEFAULT: '#222222',
          50: '#F5F5F5',
          100: '#E0E0E0',
          200: '#BDBDBD',
          300: '#999999',
          400: '#666666',
          500: '#444444',
          600: '#333333',
          700: '#222222',
          800: '#1A1A1A',
          900: '#111111',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
