const fs = require('fs/promises');
const path = require('path');
const crypto = require('crypto');
const dns = require('dns').promises;
const { neon } = require('@neondatabase/serverless');

const ROOT = path.resolve(process.cwd(), 'dist');
const DATABASE_URL = process.env.DATABASE_URL || process.env.NEON_DATABASE_URL;
const IP_HASH_SALT = process.env.GOOGLEBOT_LOG_SALT || 'jobs-enasla-mondo-googlebot-log-v1';

function getClientIp(req) {
  const forwarded = req.headers['x-forwarded-for'];
  const value = Array.isArray(forwarded) ? forwarded[0] : forwarded;
  return (value || req.socket?.remoteAddress || '').split(',')[0].trim();
}

function hashIp(ip) {
  if (!ip) return null;
  return crypto.createHash('sha256').update(`${IP_HASH_SALT}:${ip}`).digest('hex');
}

function crawlerFamily(userAgent) {
  const value = String(userAgent || '');
  if (/google-inspectiontool/i.test(value)) return 'google_inspection_tool';
  if (/googlebot/i.test(value)) return 'googlebot';
  if (/storebot-google/i.test(value)) return 'storebot_google';
  if (/googleother/i.test(value)) return 'google_other';
  if (/bingbot|slurp|duckduckbot|baiduspider|yandexbot|facebookexternalhit|twitterbot/i.test(value)) return 'other_bot';
  return 'browser_or_unknown';
}

function isClaimedGooglebot(userAgent) {
  return crawlerFamily(userAgent) !== 'browser_or_unknown';
}

async function verifyGooglebot(ip) {
  if (!ip) return { verified: false, method: 'missing_ip' };
  try {
    const names = await dns.reverse(ip);
    const googleName = names.find((name) => /\.googlebot\.com$|\.google\.com$|\.googleusercontent\.com$/i.test(name));
    if (!googleName) return { verified: false, method: 'reverse_dns_mismatch' };
    const addresses = await dns.lookup(googleName, { all: true });
    const verified = addresses.some((entry) => entry.address === ip);
    return { verified, method: verified ? 'reverse_and_forward_dns' : 'forward_dns_mismatch' };
  } catch {
    return { verified: false, method: 'dns_lookup_failed' };
  }
}

function safePathname(input) {
  let value = typeof input === 'string' && input.startsWith('/') ? input : '/';
  value = value.split('?')[0].split('#')[0];
  try { value = decodeURIComponent(value); } catch { return '/'; }
  if (value.includes('\0') || value.includes('..')) return '/';
  return value || '/';
}

async function resolveDocument(requestPath) {
  const clean = safePathname(requestPath);
  const candidates = clean === '/'
    ? ['index.html']
    : [`${clean.slice(1)}.html`, `${clean.slice(1)}/index.html`, '404.html'];
  for (const relative of candidates) {
    const absolute = path.resolve(ROOT, relative);
    if (!absolute.startsWith(`${ROOT}${path.sep}`) && absolute !== path.join(ROOT, 'index.html')) continue;
    try {
      const stat = await fs.stat(absolute);
      if (stat.isFile()) return { absolute, clean };
    } catch {}
  }
  return { absolute: path.join(ROOT, '404.html'), clean };
}

function contentType(file) {
  if (file.endsWith('.html')) return 'text/html; charset=utf-8';
  if (file.endsWith('.xml')) return 'application/xml; charset=utf-8';
  if (file.endsWith('.txt')) return 'text/plain; charset=utf-8';
  return 'text/html; charset=utf-8';
}

async function writeVisit(req, responseMs, statusCode, requestPath) {
  if (!DATABASE_URL) return;
  const userAgent = String(req.headers['user-agent'] || '');
  const ip = getClientIp(req);
  const family = crawlerFamily(userAgent);
  const claimed = isClaimedGooglebot(userAgent);
  const verification = claimed ? await verifyGooglebot(ip) : { verified: false, method: 'not_claimed_googlebot' };
  const sql = neon(DATABASE_URL);
  const correlationKey = `${hashIp(ip) || 'no-ip'}:${requestPath}`;
  let stage = 'ordinary_or_unknown';
  let confidence = 0;
  let reason = 'user-agent_not_google_family';
  if (family === 'google_inspection_tool') {
    stage = 'inspection_fetch';
    confidence = verification.verified ? 100 : 20;
    reason = verification.verified ? 'verified_google_inspection_tool' : 'inspection_user_agent_unverified';
  } else if (family === 'googlebot' && verification.verified) {
    const recent = await sql`
      SELECT 1 FROM googlebot_visits
      WHERE correlation_key = ${correlationKey}
        AND googlebot_verified = true
        AND visited_at > NOW() - INTERVAL '30 minutes'
      LIMIT 1
    `;
    if (recent.length) {
      stage = 'second_wave_render_candidate';
      confidence = 65;
      reason = 'verified_googlebot_repeat_same_path_within_30m';
    } else {
      stage = 'first_wave_fetch_candidate';
      confidence = 85;
      reason = 'first_verified_googlebot_fetch_for_path';
    }
  } else if (family === 'googlebot') {
    stage = 'unverified_googlebot_claim';
    confidence = 5;
    reason = verification.method;
  } else if (family === 'other_bot') {
    stage = 'other_bot';
    confidence = 90;
    reason = 'known_non_google_bot_user_agent';
  }
  await sql`
    INSERT INTO googlebot_visits (
      method, path, status_code, user_agent, ip_hash, host, referer,
      is_googlebot_claimed, googlebot_verified, verification_method,
      response_ms, deployment_id, metadata, crawler_family, fetch_stage,
      stage_confidence, stage_reason, correlation_key
    ) VALUES (
      ${req.method || 'GET'}, ${requestPath}, ${statusCode}, ${userAgent}, ${hashIp(ip)},
      ${req.headers.host || null}, ${req.headers.referer || null}, ${claimed},
      ${verification.verified}, ${verification.method}, ${responseMs},
      ${process.env.VERCEL_DEPLOYMENT_ID || null},
      ${JSON.stringify({ region: process.env.VERCEL_REGION || null, stage_model: 'heuristic-v1' })}::jsonb,
      ${family}, ${stage}, ${confidence}, ${reason}, ${correlationKey}
    )
  `;
}

module.exports = async function handler(req, res) {
  const started = Date.now();
  const requestPath = safePathname(req.query?.path || req.url || '/');
  const document = await resolveDocument(requestPath);
  const statusCode = document.absolute.endsWith('404.html') ? 404 : 200;
  const responseMs = Date.now() - started;

  try {
    await Promise.race([
      writeVisit(req, responseMs, statusCode, document.clean),
      new Promise((resolve) => setTimeout(resolve, 1800)),
    ]);
  } catch (error) {
    console.error('googlebot_visit_write_failed', error?.message || error);
  }

  res.statusCode = statusCode;
  res.setHeader('Content-Type', contentType(document.absolute));
  res.setHeader('Cache-Control', 'public, max-age=0, must-revalidate');
  if (req.method === 'HEAD') return res.end();
  try {
    const body = await fs.readFile(document.absolute);
    return res.end(body);
  } catch {
    return res.status(500).send('Internal Server Error');
  }
};
