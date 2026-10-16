import type { NextConfig } from "next";
const config: NextConfig = {
  experimental: { middlewareClientMaxBodySize: 513 * 1024 * 1024 },
  async rewrites() { return [{ source: "/api/:path*", destination: "http://api:8000/:path*" }]; },
};
export default config;
