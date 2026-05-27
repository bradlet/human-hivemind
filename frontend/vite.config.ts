import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  // Keep Vite's dep-optimizer cache out of node_modules so the named volume in
  // docker-compose can't get the .vite cache into a half-committed state across
  // container restarts (root cause of the deps_temp_*/_metadata.json ENOENT).
  cacheDir: process.env.VITE_CACHE_DIR || "node_modules/.vite",
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_API_TARGET || "http://localhost:8080",
        changeOrigin: true,
        secure: false,
      },
    },
    // inotify events don't reliably traverse the macOS bind mount; polling
    // gives us deterministic file-watching inside the container.
    watch: {
      usePolling: process.env.VITE_USE_POLLING === "1",
      interval: 200,
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test-setup.ts"],
  },
});
