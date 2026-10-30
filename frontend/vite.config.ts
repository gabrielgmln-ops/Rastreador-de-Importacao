// rastreador-importacao/frontend/vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // polling: necessário para a recarga funcionar com volume do Docker no Windows
  server: { port: 5173, watch: { usePolling: true } },
});
