/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: 'var(--bg)',
        fg: 'var(--fg)',
        muted: 'var(--muted)',
        line: 'var(--line)',
        panel: 'var(--panel)',
        accent: 'var(--accent)',
        danger: 'var(--danger)',
      },
      borderRadius: {
        base: 'var(--radius)',
      },
    },
  },
  plugins: [],
}
