/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        void: '#06060e',
        abyss: '#0a0a1a',
        surface: '#0f1029',
        panel: '#141432',
        muted: '#1c1c4a',
        accent: '#00e5ff',
        'accent-dim': '#00b8cc',
        plasma: '#a855f7',
        'plasma-dim': '#7c3aed',
        nebula: '#ec4899',
        'text-primary': '#e4e4f7',
        'text-secondary': '#8888b0',
        'text-muted': '#555577',
      },
      boxShadow: {
        glow: '0 0 20px rgba(0, 229, 255, 0.15)',
        'glow-lg': '0 0 40px rgba(0, 229, 255, 0.2)',
        'glow-plasma': '0 0 20px rgba(168, 85, 247, 0.15)',
        'glow-nebula': '0 0 20px rgba(236, 72, 153, 0.15)',
      },
      backgroundImage: {
        'grid-pattern': 'linear-gradient(rgba(0,229,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,229,255,0.03) 1px, transparent 1px)',
      },
      backgroundSize: {
        'grid-pattern': '40px 40px',
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-pulse': 'glowPulse 3s ease-in-out infinite',
      },
      keyframes: {
        glowPulse: {
          '0%, 100%': { opacity: '0.6' },
          '50%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}

