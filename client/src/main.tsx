import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

const configuredApiBase = (import.meta.env.VITE_API_BASE_URL || "").trim();
const isStaticWebAppHost = window.location.hostname.toLowerCase().endsWith(".azurestaticapps.net");
// Use SWA route rewrites in Azure Static Web Apps to avoid browser CORS preflight issues.
const apiBase = isStaticWebAppHost ? "" : configuredApiBase;

const originalFetch = window.fetch.bind(window);
window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => {
	const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
	const shouldRewrite = url.startsWith("/api/") || url === "/health";

	if (shouldRewrite) {
		if (apiBase) {
			const rewritten = `${apiBase}${url}`;
			return originalFetch(rewritten, init);
		}
		return originalFetch(url, init);
	}

	return originalFetch(input as RequestInfo, init);
}) as typeof window.fetch;

createRoot(document.getElementById("root")!).render(<App />);
