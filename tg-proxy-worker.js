// Cloudflare Worker — reverse proxy for Telegram Bot API.
// Deploy to Cloudflare Workers (free tier: 100k requests/day).
//
// After deploying, set TELEGRAM_API_SERVER in .env to:
//   https://<your-worker-name>.<your-subdomain>.workers.dev
//
// The worker forwards all requests to the official Telegram API,
// bypassing ISP-level blocks on api.telegram.org.

export default {
  async fetch(request) {
    const url = new URL(request.url);
    url.host = "api.telegram.org";
    url.protocol = "https:";

    const newRequest = new Request(url.toString(), {
      method: request.method,
      headers: request.headers,
      body: request.body,
    });

    return fetch(newRequest);
  },
};
