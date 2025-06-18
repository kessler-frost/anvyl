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
      "/api": "http://anvyl-api:8000",
      "/docs": "http://anvyl-api:8000",
      "/openapi.json": "http://anvyl-api:8000",
    },
  },
})
