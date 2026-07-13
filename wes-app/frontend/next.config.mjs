/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    // Lint runs as a dedicated CI step (npm run lint); keep build focused on compilation.
    ignoreDuringBuilds: true,
  },
  env: {
    NEXT_PUBLIC_API_BASE_URL:
      process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1',
  },
};

export default nextConfig;
