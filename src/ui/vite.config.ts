import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      "/api": "http://sindri-api:8000",
      "/docs": "http://sindri-api:8000",
      "/openapi.json": "http://sindri-api:8000",
    },
  },
})
