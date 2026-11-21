const OWNER = "hippolicalotapus";
const REPO = "Akashic-Records";

const bad = (msg, status = 400) =>
  new Response(JSON.stringify({ error: msg }), { status, headers: { "content-type": "application/json" } });

export default async (req) => {
  const u = new URL(req.url);
  const token = u.searchParams.get("token");
  if (!token) return bad("no token", 401);

  const path = u.searchParams.get("path");
  if (!path) return bad("no path");
  const ref = u.searchParams.get("ref") || "main";

  const r = await fetch(
    `https://api.github.com/repos/${OWNER}/${REPO}/contents/${path}?ref=${ref}`,
    { headers: { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json", "User-Agent": "akashic-agent" } }
  );
  if (!r.ok) return bad(`github ${r.status}`, r.status === 404 ? 404 : 502);

  const j = await r.json();
  const text = Buffer.from(j.content || "", "base64").toString("utf8");
  return new Response(text, {
    status: 200,
    headers: { "content-type": "text/plain; charset=utf-8", "x-bytes": String(Buffer.byteLength(text)) },
  });
};
