from render import page, figure, ACTIONS

CLAIM = {
    "primary_account": "Primary account — a document or object from the time.",
    "established": "Established — settled and well supported.",
    "emerging": "Emerging — a serious argument, still contested.",
    "speculative": "Speculative — a guess, presented as one.",
    "disputed": "Disputed — two sides, both kept.",
}

OUTREACH = {
    "not_contacted": "Not contacted.",
    "sent": "Contacted, no reply yet.",
    "awaiting_response": "Awaiting response.",
    "responded": "Reply received.",
    "permission_granted": "Permission granted.",
    "declined": "Declined.",
    "bounced": "Address bounced.",
}

def record_page(r, name):
    b = [f'<p class="kicker">{r["type"].title()} · {name}</p>',
         f'<h1>{r["title"]}</h1>']
    if r.get("summary"):
        b.append(f'<p class="lede">{r["summary"]}</p>')
    for p in r.get("body", []):
        b.append(f"<p>{p}</p>")
    b.append(figure(r))

    cs = r.get("claim_status")
    if cs:
        b.append(f'<p class="claim">{CLAIM.get(cs, cs)}')
        if r.get("claim_status_note"):
            b.append(f' <span class="note">{r["claim_status_note"]}</span>')
        b.append("</p>")

    s = r["source"]
    health = s.get("health", "unchecked")
    if health in ("dead", "gone"):
        b.append('<p class="flag">Source dead. ' +
                 (f'<a href="{s["replacement_url"]}">Replacement found.</a>' if s.get("replacement_url")
                  else "No replacement known.") + "</p>")

    rows = []
    ref = r.get("external_catalogue_id") or r.get("external_id", {}).get("registration_number")
    if ref:
        rows.append(("Institution", f"{name} — {ref}"))
    if r.get("medium"):
        rows.append(("Medium", r["medium"]))
    if r.get("topics"):
        rows.append(("Topics", " · ".join(r["topics"])))
    rows.append(("Source", f'<a href="{s["canonical_url"]}">{s.get("publisher", "Source")}</a><br>'
                           f'<span class="note">Accessed {s["accessed"]}. {health.capitalize()}.</span>'))
    if r.get("iiif"):
        rows.append(("Digital copy", f'<a href="{r["iiif"]}">IIIF manifest</a>'))
    if r.get("evidence_status"):
        rows.append(("Evidence", r["evidence_status"].replace("_", " ").capitalize()))
    basis = r.get("rights_basis", "unverified").replace("_", " ")
    rows.append(("Rights", f'<span class="flag">Tier {r["rights_tier"]} · {basis}</span><br>'
                           f'<span class="note">{r.get("attribution_text", "")} {r.get("rights", {}).get("note", "")}</span>'))
    rows.append(("Revision", f'{r["revision"]} — never superseded'))

    b.append("<dl>")
    for k, v in rows:
        b.append(f"  <dt>{k}</dt>\n  <dd>{v}</dd>\n")
    b.append("</dl>")

    inst = r.get("external_id", {}).get("institution", "")
    b.append(ACTIONS.replace("{{T}}", r["title"]).replace("{{I}}", inst).replace("{{A}}", s["accessed"]))
    return page(r["title"], 3, "\n".join(b))

def item(r, href):
    return (f'  <li>\n    <a href="{href}">{r["title"]}</a>\n'
            f'    <span class="meta">{r["type"].title()} · tier {r["rights_tier"]}</span>\n  </li>')

def list_page(title, depth, intro, groups):
    b = [f"<h1>{title}</h1>"]
    if intro:
        b.append(f'<p class="note">{intro}</p>')
    for name, slug, items in groups:
        b.append(f'<h2><a href="collection/{slug}.html" style="color:inherit">{name}</a></h2>')
        b.append("<ul>")
        b.extend(item(r, r["_href"]) for r in items)
        b.append("</ul>\n")
    return page(title, depth, "\n".join(b))

def collection_page(name, slug, items):
    b = [f"<h1>{name}</h1>",
         f'<p class="note">Held records from {name}, catalogued one at a time. No bulk copying.</p>',
         "<h2>Records</h2>", "<ul>"]
    for r in items:
        b.append(item(r, f'../{r["_type"]}/{r["_collection"]}/{r["_slug"]}.html'))
    b.append("</ul>")
    return page(name, 2, "\n".join(b))

def institutions_page(insts, counts):
    b = ["<h1>Institutions</h1>",
         '<p class="note">Where each source stands. Nothing here claims partnership.</p>']
    for i in insts:
        b.append(f'<h2>{i["name"]}</h2>')
        b.append("<dl>")
        b.append(f'  <dt>Catalogue</dt>\n  <dd><a href="{i["catalogue_url"]}">{i["catalogue_url"]}</a></dd>\n')
        b.append(f'  <dt>Outreach</dt>\n  <dd>{OUTREACH.get(i.get("outreach_status"), i.get("outreach_status"))}'
                 f'{f" Last contact {i[chr(39)+chr(39)]}" if False else ""}</dd>\n')
        if i.get("last_contacted_at"):
            b.append(f'  <dt>Last contact</dt>\n  <dd>{i["last_contacted_at"]}</dd>\n')
        if i.get("expected_response"):
            b.append(f'  <dt>Expected</dt>\n  <dd>{i["expected_response"]}</dd>\n')
        if i.get("licence_note"):
            b.append(f'  <dt>Licence</dt>\n  <dd>{i["licence_note"]}</dd>\n')
        if i.get("api_docs"):
            b.append(f'  <dt>API</dt>\n  <dd><a href="{i["api_docs"]}">Documentation</a> · bulk status: {i.get("bulk_api_status", "unknown")}</dd>\n')
        b.append(f'  <dt>Records</dt>\n  <dd>{counts.get(i["name"], 0)}</dd>\n')
        b.append("</dl>")
    return page("Institutions", 1, "\n".join(b))
