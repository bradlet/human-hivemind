import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { SWRConfig } from "swr";
import App from "./App";
import { ApiError } from "./lib/api";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <SWRConfig
      value={{
        revalidateOnFocus: false,
        revalidateOnReconnect: true,
        // Cold-start gap: in dev, the frontend container can come up several
        // seconds before uvicorn is listening; in prod, a deploy can briefly
        // drop connections. Retry transient errors with exponential backoff
        // up to ~30s, but bail immediately on 4xx (e.g. 401 for /auth/me).
        onErrorRetry: (err, _key, _config, revalidate, { retryCount }) => {
          if (err instanceof ApiError && err.status >= 400 && err.status < 500) {
            return;
          }
          if (retryCount >= 5) return;
          const delay = Math.min(1000 * 2 ** retryCount, 8000);
          setTimeout(() => revalidate({ retryCount }), delay);
        },
      }}
    >
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </SWRConfig>
  </React.StrictMode>,
);
