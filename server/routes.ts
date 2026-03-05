import type { Express } from "express";
import type { Server } from "http";
import http from "http";

const FASTAPI_PORT = 8000;

function proxyToFastAPI(req: any, res: any) {
  const options: http.RequestOptions = {
    hostname: "127.0.0.1",
    port: FASTAPI_PORT,
    path: req.originalUrl,
    method: req.method,
    headers: { ...req.headers, host: `127.0.0.1:${FASTAPI_PORT}` },
  };

  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode || 500, proxyRes.headers);
    proxyRes.pipe(res, { end: true });
  });

  proxyReq.on("error", () => {
    if (!res.headersSent) {
      res.status(502).json({ message: "Backend unavailable" });
    }
  });

  if (req.body && Object.keys(req.body).length > 0) {
    const bodyData = JSON.stringify(req.body);
    proxyReq.setHeader("Content-Type", "application/json");
    proxyReq.setHeader("Content-Length", Buffer.byteLength(bodyData));
    proxyReq.write(bodyData);
  }

  req.pipe(proxyReq, { end: true });
}

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  app.use((req, res, next) => {
    if (req.path.startsWith("/api/") || req.path === "/health") {
      proxyToFastAPI(req, res);
    } else {
      next();
    }
  });

  return httpServer;
}
