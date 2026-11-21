const OWNER = "hippolicalotapus";
const REPO = "Akashic-Records";

export default async (req) => {
  const url = new URL(req.url);
  const token = url.searchParams.get("token") || process.env.GITHUB_TOKEN;
  if (!token) return json({ error: "no token" }, 401);

  const path = url.searchParams.get("path");
  const message = url.searchParams.get("message") || `update ${path}`;
  const content = url.searchParams.get("content");
  const branch = url.searchParams.get("branch") || "main";
  const del = url.searchParams.get("delete") === "1";
  if (!path) return json({ error: "no path" }, 400);

  const api = `https://api.github.com/repos/${OWNER}/${REPO}/contents/${path}`;
  const headers = {
    Authorization: `Bearer ${token}`,
    Accept: "application/vnd.github+json",
    "User-Agent": "akashic-agent",
  };

  let sha;
  const head = await fetch(`${api}?ref=${branch}`, { headers });
  if (head.ok) sha = (await head.json()).sha;

  if (del) {
    if (!sha) return json({ error: "not found" }, 404);
    const r = await fetch(api, {
      method: "DELETE",
      headers,
      body: JSON.stringify({ message, sha, branch }),
    });
    return json(await r.json(), r.status);
  }

  if (content == null) return json({ error: "no content" }, 400);
  const body = {
    message,
    branch,
    content: btoa(unescape(encodeURIComponent(content))),
  };
  if (sha) body.sha = sha;

  const r = await fetch(api, { method: "PUT", headers, body: JSON.stringify(body) });
  return json(await r.json(), r.status);
};

function json(o, status = 200) {
  return new Response(JSON.stringify(o), {
    status,
    headers: { "content-type": "application/json" },
  });
}
