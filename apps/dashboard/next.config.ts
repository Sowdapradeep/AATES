import type { NextConfig } from "next";

const apiHost = process.env.API_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiHost}/:path*`,
      },
    ];
  },
};

export default nextConfig;
