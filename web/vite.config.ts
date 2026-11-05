import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  // GitHub Pages serves the site from /HR-Analytics-Dashboard/
  base: '/HR-Analytics-Dashboard/',
  plugins: [react(), tailwindcss()],
  resolve: { alias: { '@': path.resolve(import.meta.dirname, './src') } },
  // data/HR.csv lives one level up so Power BI, SQL and the web app share one source
  server: { fs: { allow: ['..'] } },
})
