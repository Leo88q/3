import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  timeout: 120000,
  use: {
    baseURL: process.env.TEST_BASE_URL || "http://127.0.0.1:5173",
    launchOptions: {
      executablePath: process.env.CHROMIUM_PATH || undefined,
      args: process.env.CHROMIUM_PATH
        ? ["--no-sandbox", "--disable-dev-shm-usage"]
        : [],
    },
  },
  webServer: process.env.TEST_BASE_URL
    ? undefined
    : {
        command: "npm run dev",
        url: "http://127.0.0.1:5173",
        reuseExistingServer: true,
      },
});
