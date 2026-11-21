const SECRET = "akashic-bridge-4417";

const ALLOW = [
  "wellcomecollection.org",
  "iiif.wellcomecollection.org",
  "loc.gov",
  "britishmuseum.org",
  "github.com",
  "api.github.com",
  "raw.githubusercontent.com",
];

const PRIVATE = [/^127\./, /^10\./, /^192\.168\./, /^169\.254\./, /^172\.(1[6-9]|2\d|3[01])\./];
const MAX = 10 * 1024 * 1024;

const bad = (msg, status = 400) =>
  new Response(JSON.stringify({ error: msg }), { status, headers: { "content-type": "application/json" } });

export default async (req) => {
  const u = new URL(req.url);
  if (u.searchParams.get("secret") !== SECRET) return bad("bad secret", 401);

  const target = u.searchParams.get("url");
  if (!target) return bad("no url");

  let t;
  try { t = new URL(target); } catch { return bad("bad url"); }
  if (!/^https?:$/.test(t.protocol)) return bad("http(s) only");
  if (PRIVATE.some((re) => re.test(t.hostname))) return bad("private host");
  if (!ALLOW.some((d) => t.hostname === d || t.hostname.endsWith("." + d))) return bad(`host not allowed: ${t.hostname}`);

  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), 20000);
  try {
    const r = await fetch(t.href, {
      redirect: "follow",
      signal: ac.signal,
      headers: { "user-agent": "AkashicRecords/1.0 (+archive capture)" },
    });
    const buf = await r.arrayBuffer();
    if (buf.byteLength > MAX) return bad(`too large: ${buf.byteLength}`, 413);
    return new Response(buf, {
      status: r.status,
      headers: {
        "content-type": r.headers.get("content-type") || "application/octet-stream",
        "x-final-url": r.url,
        "x-bytes": String(buf.byteLength),
      },
    });
  } catch (e) {
    return bad(`fetch failed: ${e.message}`, 502);
  } finally {
    clearTimeout(timer);
  }
};
