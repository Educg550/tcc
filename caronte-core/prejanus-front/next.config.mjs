const isProd = process.env.NODE_ENV === "production";
/** @type {import('next').NextConfig} */

const nextConfig = {
	output: isProd ? "standalone" : undefined,
	basePath: "/prejanus",
	assetPrefix: "/prejanus/",
	typescript: {
		ignoreBuildErrors: true,
	},
	eslint: {
		ignoreDuringBuilds: false,
	},
	experimental: {
		allowedDevOrigins: ["http://localhost", "http://127.0.0.1"],
	},
	async rewrites() {
		return [
			{
				source: "/__nextjs_original-stack-frames",
				destination: "/prejanus/__nextjs_original-stack-frames",
			},
			{
				source: "/__nextjs_launch-editor",
				destination: "/prejanus/__nextjs_launch-editor",
			},
		];
	},
};

export default nextConfig;
