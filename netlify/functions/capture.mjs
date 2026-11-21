const OWNER = "hippolicalotapus";
const REPO = "Akashic-Records";
const SECRET = "akashic-bridge-4417";
const MAX = 5 * 1024 * 1024;

const bad = (m, s = 400) => new Response(JSON.stringify({ error: m }), { status: s, headers: { "content-type": "application/json" } });
const b64 = (s) => btoa(unescape(encodeURIComponent(s)));

async function ghGet(token, path) {
  const r = await fetch(`https://api.github.com/repos/${OWNER}/${REPO}/contents/${path}?ref=main`, {
    headers: { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json", "User-Agent": "akashic-agent" },
  });
  return r.ok ? r.json() : null;
}

async function ghPut(token, path, content, message, sha) {
  const r = await fetch(`https://api.github.com/repos/${OWNER}/${REPO}/contents/${path}`, {
    method: "PUT",
    headers: { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json", "User-Agent": "akashic-agent" },
    body: JSON.stringify({ message, content: b64(content), branch: "main", ...(sha ? { sha } : {}) }),
  });
  return r.status;
}

export default async (req) => {
  const u = new URL(req.url);
  if (u.searchParams.get("secret") !== SECRET) return bad("bad secret", 401);
  const token = u.searchParams.get("token");
  if (!token) return bad("no token", 401);
  const target = u.searchParams.get("url");
  const record = u.searchParams.get("record");
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
  const at = new Date().toISOString();
  const stamp = at.replace(/[:.]/g, "-");
  const key = `captures/${t.hostname}/${sha256.slice(0, 12)}-${stamp}.txt`;

  const head = [
    `url: ${t.href}`,
    `final_url: ${r.url}`,
    `status: ${r.status}`,
    `content_type: ${r.headers.get("content-type") || ""}`,
    `captured_at: ${at}`,
    `sha256: ${sha256}`,
    `bytes: ${body.byteLength}`,
    "mirror_status: dark",
    "----",
    "",
  ].join("\n");

  const capStatus = await ghPut(token, key, head + Buffer.from(body).toString("latin1"), `Capture ${t.href}`);
  if (capStatus !== 201 && capStatus !== 200) return bad(`capture commit failed: ${capStatus}`, 502);

  let patched = false;
  if (record) {
    const existing = await ghGet(token, record);
    if (existing) {
      const text = Buffer.from(existing.content || "", "base64").toString("utf8");
      const j = JSON.parse(text);
      j.captures = (j.captures || []).concat([{
        captured_at: at,
        sha256,
        bytes: body.byteLength,
        warc: key,
        tool: "netlify-fetch/1",
        mirror_status: "dark",
      }]);
      j.source.health = "live";
      j.source.checked_at = at;
      const st = await ghPut(token, record, JSON.stringify(j, null, 2) + "\n", `Record capture ${sha256.slice(0, 12)}`, existing.sha);
      patched = st === 200 || st === 201;
    }
  }

  return new Response(JSON.stringify({ ok: true, path: key, sha256, bytes: body.byteLength, status: r.status, record_patched: patched }), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
};
