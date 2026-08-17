/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: '#03070f',
        ink2: '#060d1a',
        ink3: '#0a1626',
        ink4: '#102138',
        line: 'rgba(125,190,255,0.12)',
        line2: 'rgba(125,190,255,0.26)',
        accent: '#4da6ff',
        accent2: '#8fd0ff',
        accentDim: '#2b7fd4',
        accentDeep: '#0f4d8a',
        mist: '#9db4cd',
        mistDim: '#5c748f',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      letterSpacing: {
        widest2: '0.28em',
      },
    },
  },
  plugins: [],
}
