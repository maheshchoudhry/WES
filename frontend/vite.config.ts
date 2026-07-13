/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Proxy /api to the backend. Use 127.0.0.1 (not "localhost") so the proxy always
// targets IPv4 — uvicorn binds 127.0.0.1 by default, and "localhost" can resolve
// to IPv6 ::1 first on some machines, which would fail to connect.
const apiProxy = {
  "/api": {
    target: process.env.VITE_API_PROXY ?? "http://127.0.0.1:8000",
    changeOrigin: true,
  },
};

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: apiProxy,
  },
  // `vite preview` (serving the production build locally) uses the same proxy so
  // /api reaches the backend instead of falling back to index.html.
  preview: {
    port: 4173,
    proxy: apiProxy,
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    css: false,
  },
});
