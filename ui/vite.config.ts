import { defineConfig } from "vite";

export default defineConfig({
  base: "/static/",
  build: {
    outDir: "../static",
    emptyOutDir: true,
  },
  server: {
    allowedHosts: true,
    proxy: {
      "/feeds": "http://127.0.0.1:8000",
      "/articles": "http://127.0.0.1:8000",
      "/sync": "http://127.0.0.1:8000",
      "/categories": "http://127.0.0.1:8000",
      "/tags": "http://127.0.0.1:8000",
      "/opml": "http://127.0.0.1:8000",
    },
  },
});
