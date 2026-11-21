const OWNER = "hippolicalotapus";
const REPO = "Akashic-Records";
const SECRET = "akashic-bridge-4417";
const MAX = 5 * 1024 * 1024;

const bad = (m, s = 400) => new Response(JSON.stringify({ error: m }), { status: s, headers: { "content-type": "application/json" } });

async function gh(token, path, body, method = "PUT") {
  const api = `https://api.github.com/repos/${OWNER}/${REPO}/contents/${path}`;
  const headers = { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json", "User-Agent": "akashic-agent" };
  const head = await fetch(`${api}?ref=main`, { headers });
  const sha = head.ok ? (await head.json()).sha : undefined;
  const payload = method === "PUT" ? { ...body, ...(sha ? { sha } : {}) } : { ...body, sha };
  const r = await fetch(api, { method, headers, body: JSON.stringify(payload) });
  return { ok: r.ok, status: r.status, json: await r.json() };
}

const b64 = (s) => btoa(unescape(encodeURIComponent(s)));

export default async (req) => {
  const u = new URL(req.url);
  if (u.searchParams.get("secret") !== SECRET) return bad("bad secret", 401);
  const token = u.searchParams.get("token");
  if (!token) return bad("no token", 401);
  const target = u.searchParams.get("url");
  if (!target) return bad("no url");

  let t;
  try { t = new URL(target); } catch { return bad("bad url"); }
  if (!/^https?:$/.test(t.protocol)) return bad("http(s) only");

  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), 20000);
  let r, body;
  try {
    r = await fetch(t.href, { redirect: "follow", signal: ac.signal, headers: { "user-agent": "AkashicRecords/1.0 (+archive capture)" } });
    const buf = await r.arrayBuffer();
    if (buf.byteLength > MAX) return bad(`too large: ${buf.byteLength}`, 413);
    body = buf;
  } catch (e) {
    return bad(`fetch failed: ${e.message}`, 502);
  } finally {
    clearTimeout(timer);
  }

  const digest = await crypto.subtle.digest("SHA-256", body);
  const sha256 = [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const key = `${t.hostname}/${sha256.slice(0, 12)}-${stamp}`;

  const head = [
    `url: ${t.href}`,
    `final_url: ${r.url}`,
    `status: ${r.status}`,
    `content_type: ${r.headers.get("content-type") || ""}`,
    `captured_at: ${new Date().toISOString()}`,
    `sha256: ${sha256}`,
    `bytes: ${body.byteLength}`,
    `mirror_status: dark`,
    "----",
    "",
  ].join("\n");

  const text = head + Buffer.from(body).toString("latin1");
  const put = await gh(token, `captures/${key}.txt`, { message: `Capture ${t.href}`, content: b64(text), branch: "main" });
  if (!put.ok) return bad(`commit failed: ${put.status}`, 502);

  return new Response(JSON.stringify({ ok: true, path: `captures/${key}.txt`, sha256, bytes: body.byteLength, status: r.status }), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
};
