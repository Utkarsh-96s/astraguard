/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  images: {
    unoptimized: true,
  },
  async redirects() {
    return [
      {
        source: "/health",
        destination: "/dashboard/health",
        permanent: false,
      },
      {
        source: "/debris",
        destination: "/dashboard/debris",
        permanent: false,
      },
      {
        source: "/disaster",
        destination: "/dashboard/disaster",
        permanent: false,
      },
      {
        source: "/alerts",
        destination: "/dashboard/alerts",
        permanent: false,
      },
      {
        source: "/models",
        destination: "/dashboard/models",
        permanent: false,
      },
    ];
  },
  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/:path*`,
      },
    ];
  },
};

export default nextConfig;
