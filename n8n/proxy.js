#!/usr/bin/env node
/**
 * proxy.js - Mini reverse proxy for n8n
 *
 * Listens on port 8080, proxies to n8n on port 5678.
 * Strips X-Frame-Options and Content-Security-Policy headers
 * to allow embedding n8n in an iframe on 1crypten.space.
 *
 * Also handles WebSocket upgrades for n8n real-time features.
 */

const http = require('http');

const TARGET_HOST = '127.0.0.1';
const TARGET_PORT = 5678;
const PROXY_PORT = 8080;

// Headers that block iframe embedding — these get stripped
const HEADERS_TO_STRIP = [
  'x-frame-options',
  'content-security-policy',
  'x-content-security-policy',
  'x-webkit-csp',
];

const server = http.createServer((req, res) => {
  const targetPath = req.url;
  const options = {
    hostname: TARGET_HOST,
    port: TARGET_PORT,
    path: targetPath,
    method: req.method,
    headers: { ...req.headers },
  };

  // Remove hop-by-hop headers that shouldn't be forwarded
  delete options.headers['connection'];
  delete options.headers['upgrade'];

  const proxyReq = http.request(options, (proxyRes) => {
    // Strip iframe-blocking response headers
    HEADERS_TO_STRIP.forEach((header) => {
      const key = Object.keys(proxyRes.headers).find(
        (k) => k.toLowerCase() === header,
      );
      if (key) delete proxyRes.headers[key];
    });

    // Fix cookies for iframe embedding (Third-Party Context)
    if (proxyRes.headers['set-cookie']) {
      let cookies = proxyRes.headers['set-cookie'];
      if (!Array.isArray(cookies)) cookies = [cookies];
      proxyRes.headers['set-cookie'] = cookies.map(cookie => {
        let newCookie = cookie;
        newCookie = newCookie.replace(/;\s*SameSite=(Lax|Strict|None)/ig, '');
        newCookie = newCookie.replace(/;\s*Secure/ig, '');
        return newCookie + '; SameSite=None; Secure';
      });
    }

    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res);
  });

  proxyReq.on('error', (err) => {
    console.error(`[PROXY] Error proxying to ${targetPath}: ${err.message}`);
    res.writeHead(502, { 'Content-Type': 'text/plain' });
    res.end('Bad Gateway');
  });

  req.pipe(proxyReq);
});

// Handle WebSocket upgrades (for n8n live updates)
server.on('upgrade', (req, socket, head) => {
  const targetPath = req.url;
  const options = {
    hostname: TARGET_HOST,
    port: TARGET_PORT,
    path: targetPath,
    method: 'GET',
    headers: { ...req.headers },
  };

  const proxyReq = http.request(options);
  proxyReq.on('upgrade', (proxyRes, proxySocket, proxyHead) => {
    // Forward ALL 101 response headers (not just sec-websocket-accept)
    let raw = 'HTTP/1.1 101 Switching Protocols\r\n';
    for (const [k, v] of Object.entries(proxyRes.headers)) {
      raw += `${k}: ${Array.isArray(v) ? v.join(', ') : v}\r\n`;
    }
    raw += '\r\n';
    socket.write(raw);

    // Forward any initial data from target or client
    if (proxyHead && proxyHead.length) socket.write(proxyHead);
    if (head && head.length) proxySocket.write(head);

    // Bidirectional pipes
    proxySocket.pipe(socket);
    socket.pipe(proxySocket);
  });

  proxyReq.on('error', (err) => {
    console.error(`[PROXY] WebSocket error: ${err.message}`);
    socket.destroy();
  });

  proxyReq.end();
});

server.listen(PROXY_PORT, () => {
  console.log(`[PROXY] Listening on port ${PROXY_PORT}`);
  console.log(`[PROXY] Forwarding to ${TARGET_HOST}:${TARGET_PORT}`);
  console.log(`[PROXY] Stripped headers: ${HEADERS_TO_STRIP.join(', ')}`);
});
