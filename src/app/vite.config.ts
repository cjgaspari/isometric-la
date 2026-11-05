import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig(({ mode }) => {
  // Load env file from project root (two levels up from src/app/).
  // Set the third parameter to '' to load all env regardless of the `VITE_` prefix.
  const env = loadEnv(mode, resolve(__dirname, "../.."), "");

  return {
    // Use /isometric-los-angeles/ base path for production (GitHub Pages)
    base: mode === "production" ? "/isometric-los-angeles/" : "/",
    plugins: [react()],
    resolve: {
      alias: {
        "@": resolve(__dirname, "src"),
      },
    },
    server: {
      port: 3000,
      open: true,
    },
    define: {
      // R2 URL for DZI tiles (served directly from R2 bucket)
      // Production: use R2 base URL (export dir is appended via config.ts)
      // Dev: use local public folder (empty string = same origin)
      __TILES_BASE_URL__: JSON.stringify(
        mode === "production"
          ? "https://isometric-los-angeles-tiles.cannoneyed.com"
          : ""
      ),
      // MAP_ID determines which subdirectory under public/dzi/ to load
      // Set via: MAP_ID=tiny-los-angeles in .env file or MAP_ID=tiny-los-angeles bun run dev
      __MAP_ID__: JSON.stringify(env.MAP_ID || ""),
      // LOCAL_R2 forces use of R2 tiles in dev mode
      // Set via: LOCAL_R2=true in .env file or LOCAL_R2=true bun run dev
      __LOCAL_R2__: JSON.stringify(env.LOCAL_R2 === "true"),
      // USE_R2_LOS_ANGELES fetches from R2 dzi/ directly (no map id subdir)
      // Set via: USE_R2_LOS_ANGELES=true in .env file or USE_R2_LOS_ANGELES=true bun run dev
      __USE_R2_LOS_ANGELES__: JSON.stringify(env.USE_R2_LOS_ANGELES === "true"),
    },
  };
});
