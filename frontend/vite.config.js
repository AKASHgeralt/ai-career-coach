import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // The backend's CORS allow-list only permits localhost:5173. Without
    // strictPort, Vite silently falls back to 5174 when 5173 is busy, and
    // every API response then gets blocked by the browser — which surfaces
    // as a misleading "invalid credentials" error. Fail loudly instead.
    port: 5173,
    strictPort: true,
  },
})
