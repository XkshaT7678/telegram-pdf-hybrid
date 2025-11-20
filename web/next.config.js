/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  env: {
    BOT_USERNAME: process.env.BOT_USERNAME,
  },
}

module.exports = nextConfig
