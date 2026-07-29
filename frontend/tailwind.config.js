/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#FFFFFF',
        foreground: '#222222',
        primary: {
          DEFAULT: '#222222', // Carbon Black
          foreground: '#FFFFFF',
        },
        accent: {
          DEFAULT: '#84DCC6', // Pearl Aqua
          foreground: '#222222',
          hover: '#6AC3AD', // Slightly darker Pearl Aqua for hover
        },
        secondary: {
          DEFAULT: '#4B4E6D', // Dusty Grape
          foreground: '#FFFFFF',
        },
        neutral: {
          DEFAULT: '#95A3B3', // Cool Steel
          light: '#F8F9FA', // Very subtle off-white for structuring whitespace
          dark: '#6B7280',
        },
        card: {
          DEFAULT: '#FFFFFF',
          foreground: '#222222',
        },
        border: '#E5E7EB', // Thin borders
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        // Enforcing flat design: only very subtle shadows for critical depth, otherwise rely on thin borders
        'subtle': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'none': 'none',
      },
      borderRadius: {
        // Reduced exaggerated roundness
        'sm': '0.125rem',
        'DEFAULT': '0.25rem',
        'md': '0.375rem',
        'lg': '0.5rem',
        'xl': '0.75rem',
      }
    },
  },
  plugins: [],
}
