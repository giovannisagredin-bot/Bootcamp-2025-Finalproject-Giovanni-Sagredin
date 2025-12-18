import express from "express";
import { createProxyMiddleware } from "http-proxy-middleware";
import { GoogleAuth } from "google-auth-library";
import { exec } from "child_process";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import fetch from "node-fetch";
import { spawn } from "child_process";

const app = express();
const port = 3030;

// REPLACE WITH YOUR CLOUD RUN URL
const CLOUD_RUN_URL =
  "https://scout-app-634359182056.europe-west1.run.app";

// REPLACE WITH YOUR GCP PROJECT ID
const PROJECT_ID = "ennova-bootcamp-2025";

// Check if user is authenticated with gcloud
const checkGcloudAuth = async (): Promise<boolean> => {
  return new Promise((resolve) => {
    exec(
      'gcloud auth list --filter=status:ACTIVE --format="value(account)"',
      (error, stdout) => {
        if (error || !stdout.trim()) {
          console.log("❌ No active gcloud account found");
          resolve(false);
        } else {
          console.log(`✅ Active gcloud account: ${stdout.trim()}`);
          resolve(true);
        }
      }
    );
  });
};

// Check if application default credentials exist
const checkAppDefaultCredentials = (): boolean => {
  const adcPath = path.join(
    os.homedir(),
    ".config",
    "gcloud",
    "application_default_credentials.json"
  );
  const exists = fs.existsSync(adcPath);
  if (exists) {
    console.log("✅ Application Default Credentials found");
  } else {
    console.log("❌ Application Default Credentials not found");
  }
  return exists;
};

// Open browser for user authentication
const openAuthBrowser = async (): Promise<void> => {
  return new Promise((resolve, reject) => {
    console.log("\n🔐 Opening browser for Google Cloud authentication...");

    // Command to authenticate and set application default credentials
    const command = `gcloud auth application-default login --project=${PROJECT_ID}`;

    // On Windows, use cmd.exe
    const isWindows = process.platform === "win32";
    const shell = isWindows ? "cmd.exe" : "sh";
    const shellArgs = isWindows ? ["/c", command] : ["-c", command];

    const authProcess = spawn(shell, shellArgs, {
      stdio: "inherit",
      detached: true,
    });

    authProcess.on("error", (error) => {
      console.error("❌ Error during authentication:", error);
      reject(error);
    });

    authProcess.on("exit", (code) => {
      if (code === 0) {
        console.log("✅ Authentication successful!");
        resolve();
      } else {
        console.error(`❌ Authentication process exited with code ${code}`);
        reject(new Error(`Authentication process exited with code ${code}`));
      }
    });
  });
};

// Get auth token for Cloud Run
const getAuthToken = async () => {
  try {
    const auth = new GoogleAuth();
    const client = await auth.getIdTokenClient(CLOUD_RUN_URL);
    const headers: any = await client.getRequestHeaders();
    return headers.Authorization || '';
  } catch (error) {
    console.error("❌ Error getting auth token:", error);

    // Check if we need to authenticate
    const isGcloudAuthed = await checkGcloudAuth();
    const hasADC = checkAppDefaultCredentials();

    if (!isGcloudAuthed || !hasADC) {
      console.log(
        "\n⚠️ You need to authenticate with Google Cloud to use this proxy."
      );
      await openAuthBrowser();

      // Try again after authentication
      const auth = new GoogleAuth();
      const client = await auth.getIdTokenClient(CLOUD_RUN_URL);
      const headers: any = await client.getRequestHeaders();
      return headers.Authorization || '';
    } else {
      throw error;
    }
  }
};

// Check if Cloud Run service is accessible
const checkCloudRunConnection = async (
  url: string,
  token: string
): Promise<boolean> => {
  try {
    const response = await fetch(`${url}/health`, {
      headers: {
        Authorization: token,
      },
    });

    if (response.ok) {
      console.log("✅ Successfully connected to Cloud Run service");
      return true;
    } else {
      console.error(
        `❌ Failed to connect to Cloud Run service: ${response.status} ${response.statusText}`
      );
      return false;
    }
  } catch (error) {
    console.error("❌ Error connecting to Cloud Run service:", error);
    return false;
  }
};

// Create proxy with authentication
const setupProxy = async () => {
  try {
    console.log("\n🔑 Getting authentication token...");
    let token = await getAuthToken();
    console.log("✅ Successfully obtained Google authentication token");

    // Check connection to Cloud Run service
    let isConnected = await checkCloudRunConnection(CLOUD_RUN_URL, token);
    let retryCount = 0;
    const maxRetries = 3;

    while (!isConnected && retryCount < maxRetries) {
      console.log(
        `\n⚠️ Retrying connection (${retryCount + 1}/${maxRetries})...`
      );
      // Refresh token and try again
      token = await getAuthToken();
      isConnected = await checkCloudRunConnection(CLOUD_RUN_URL, token);
      retryCount++;
    }

    if (!isConnected) {
      console.error(
        `\n❌ Failed to connect to Cloud Run service after ${maxRetries} attempts.`
      );
      console.log("\n⚠️ Please check:");
      console.log("  1. Your Cloud Run URL is correct");
      console.log("  2. The service is deployed and running");
      console.log("  3. Your Google Cloud account has access to the service");
      process.exit(1);
    }

    // Apply proxy to all routes
    app.use(
      "/",
      createProxyMiddleware({
        target: CLOUD_RUN_URL,
        changeOrigin: true,
        on: {
          proxyReq: (proxyReq: any, req: any, res: any) => {
            proxyReq.setHeader('Authorization', token);
            console.log(`🔄 Proxying ${req.method} ${req.path} to ${CLOUD_RUN_URL}`);
          },
          error: (err: any, req: any, res: any) => {
            console.error("❌ Proxy error:", err);
            res.writeHead(500, { "Content-Type": "text/plain" });
            res.end("Proxy error: " + err.message);
          },
          proxyRes: (proxyRes: any, req: any, res: any) => {
            console.log(`📤 Response from ${CLOUD_RUN_URL}: ${proxyRes.statusCode}`);
            proxyRes.headers["x-proxied-by"] = "freetech-mcp-proxy";
          }
        }
      })
    );

    // Start proxy server
    app.listen(port, () => {
      console.log(`\n🚀 MCP Proxy server running at http://localhost:${port}`);
      console.log(`🔗 Proxying requests to ${CLOUD_RUN_URL}`);
      console.log(`\n✨ Configure Cursor to use: http://localhost:${port}/sse`);
      console.log("\n📝 Press Ctrl+C to stop the proxy server");
    });

    // Refresh token periodically (tokens expire after 1 hour)
    setInterval(async () => {
      try {
        token = await getAuthToken();
        console.log("🔄 Authentication token refreshed");
      } catch (error) {
        console.error("❌ Failed to refresh authentication token:", error);
      }
    }, 45 * 60 * 1000); // Refresh every 45 minutes
  } catch (error) {
    console.error("❌ Failed to set up proxy:", error);
    process.exit(1);
  }
};

// Handle errors
process.on("uncaughtException", (error) => {
  console.error("❌ Uncaught exception:", error);
});

process.on("unhandledRejection", (reason, promise) => {
  console.error("❌ Unhandled rejection at:", promise, "reason:", reason);
});

// Handle termination signals
process.on("SIGINT", () => {
  console.log("\n👋 Shutting down proxy server...");
  process.exit(0);
});

process.on("SIGTERM", () => {
  console.log("\n👋 Shutting down proxy server...");
  process.exit(0);
});

console.log("🚀 Starting MCP proxy server...");
setupProxy();
