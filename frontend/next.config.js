const path = require('path')

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  /** Anchor tracing to this app when another lockfile exists higher in the tree (avoids wrong root + odd chunk paths). */
  outputFileTracingRoot: path.join(__dirname),
  // Future: API integration will go here
  // env: {
  //   API_BASE_URL: process.env.API_BASE_URL,
  // },
}

module.exports = nextConfig
