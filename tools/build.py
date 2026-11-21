#!/usr/bin/env python3
"""Build the site from data/records/*.json."""
import json, pathlib, shutil, sys
from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "records"
OUT = ROOT / "records"
SCHEMA = json.loads((ROOT / "schema" / "record.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)

CSS = """
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 2rem 1.25rem 4rem;
    background: #12100e; color: #e8e1d5;
    font: 400 17px/1.65 ui-serif, Georgia, serif;
    max-width: 44rem; margin-inline: auto;
  }
  a { color: #c9b48f; }
  h1 { font-size: clamp(1.7rem, 6vw, 2.5rem); line-height: 1.15; margin: 0 0 1rem; }
  h2 { font-size: .8rem; text-transform: uppercase; letter-spacing: .16em; color: #a2917a; margin: 2.75rem 0 .75rem; }
  ul { list-style: none; margin: 0; padding: 0; }
  li { border-top: 1px solid #2e2822; padding: 1rem 0; }
  li a { text-decoration: none; }
  li a:hover { text-decoration: underline; }
  .meta { display: block; font-size: .82rem; color: #a2917a; margin-top: .3rem; }
  dl { margin: 2rem 0; border-top: 1px solid #2e2822; }
  dt { font-size: .78rem; text-transform: uppercase; letter-spacing: .14em; color: #a2917a; margin-top: 1.25rem; }
  dd { margin: .2rem 0 0; }
  .flag { color: #d8a05a; }
  .note { font-size: .9rem; color: #a2917a; }
  .lede { font-size: 1.05rem; }
  footer { margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid #2e2822; font-size: .8rem; color: #7d6f5e; }
  .actions { margin: 2.5rem 0 0; border-top: 1px solid #2e2822; padding-top: 1.25rem; }
  .actions button { font: inherit; font-size: .85rem; color: #e8e1d5; background: #1b1815; border: 1px solid #3a332b; padding: .4rem .8rem; margin: 0 .4rem .4rem 0; cursor: pointer; }
  .actions button:hover { border-color: #c9b48f; color: #fff; }
  .said { font-size: .85rem; color: #a2917a; min-height: 1.3rem; }
"""

def page(title, depth, body):
    up = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Akashic Records</title>
<style>{CSS}</style>
</head>
<body>

<nav style="display:flex;gap:1.25rem;font-size:.78rem;text-transform:uppercase;letter-spacing:.2em;color:#a2917a;margin-bottom:1.25rem">
  <a href="{up}index.html" style="color:inherit;text-decoration:none">Home</a>
  <a href="{up}records/index.html" style="color:inherit;text-decoration:none">Records</a>
  <a href="{up}about.html" style="color:inherit;text-decoration:none">About</a>
</nav>

{body}

<footer>
  <a href="{up}index.html">Back to the index</a> · <a href="{up}about.html">About</a>
</footer>

</body>
</html>
"""

def figure(rec):
    if not rec.get("image"):
        return ""
    alt = rec.get("image_alt", "")
    credit = rec.get("credit") or rec.get("external_id", {}).get("institution", "")
    return f"""<figure style="margin:2rem 0">
  <img src="{rec['image']}" alt="{alt}" style="width:100%;height:auto;display:block">
  <figcaption class="note" style="margin-top:.5rem">{credit}. Public domain.</figcaption>
</figure>
"""

def record_page(rec, collection_name):
    body = [f'<p style="font-size:.78rem;text-transform:uppercase;letter-spacing:.2em;color:#a2917a;margin-bottom:1.25rem">{rec["type"].title()} · {collection_name}</p>',
            f"<h1>{rec['title']}</h1>"]
    if rec.get("summary"):
        body.append(f'<p class="lede">{rec["summary"]}</p>')
    for para in rec.get("body", []):
        body.append(f"<p>{para}</p>")
    body.append(figure(rec))

    rows = []
    if rec.get("external_id", {}).get("registration_number"):
        rows.append(("Institution", f"{collection_name} — {rec['external_id']['registration_number']}"))
    if rec.get("medium"):
        rows.append(("Medium", rec["medium"]))
    if rec.get("topics"):
        rows.append(("Topics", " · ".join(rec["topics"])))
    src = rec["source"]
    rows.append(("Source", f'<a href="{src["canonical_url"]}">{src.get("publisher", "Source")}</a><br>'
                           f'<span class="note">Accessed {src["accessed"]}. <span class="flag">Not yet captured.</span></span>'))
    if rec.get("iiif"):
        rows.append(("Digital copy", f'<a href="{rec["iiif"]}">IIIF manifest</a>'))
    if rec.get("evidence_status"):
        rows.append(("Evidence", rec["evidence_status"].replace("_", " ").capitalize()))
    rows.append(("Rights", f'<span class="flag">Tier {rec["rights_tier"]} — free to publish.</span><br>'
                           f'<span class="note">{rec.get("rights", {}).get("note", "")}</span>'))
    rows.append(("Revision", f'{rec["revision"]} — never superseded'))

    body.append("<dl>")
    for label, value in rows:
        body.append(f"  <dt>{label}</dt>\n  <dd>{value}</dd>\n")
    body.append("</dl>")
    inst = rec.get("external_id", {}).get("institution", "")
    body.append(f"""<div class="actions" data-title="{rec['title']}" data-institution="{inst}" data-accessed="{src['accessed']}">
  <p class="note">What would you like to do with this record?</p>
  <button data-act="cite">Copy citation</button>
  <button data-act="link">Copy link</button>
  <button data-act="translate">Translate</button>
  <button data-act="search">Find more about it</button>
  <p class="said"></p>
</div>
<script>
(function () {{
  var box = document.querySelector('.actions');
  var said = document.querySelector('.said');
  function say(t) {{ said.textContent = t; setTimeout(function () {{ said.textContent = ''; }}, 2500); }}
  function copy(t) {{
    navigator.clipboard.writeText(t).then(function () {{ say('Copied'); }},
      function () {{ say('Copy failed'); }});
  }}
  box.addEventListener('click', function (e) {{
    var b = e.target.closest('button');
    if (!b) return;
    var t = box.dataset.title, inst = box.dataset.institution, acc = box.dataset.accessed;
    var act = b.dataset.act;
    if (act === 'cite') copy(t + '. ' + inst + '. Accessed ' + acc + '. ' + location.href);
    if (act === 'link') copy(location.href);
    if (act === 'translate') window.open('https://translate.google.com/translate?sl=auto&tl=es&u=' + encodeURIComponent(location.href), '_blank');
    if (act === 'search') window.open('https://duckduckgo.com/?q=' + encodeURIComponent(t + ' ' + inst), '_blank');
  }});
}})();
</script>""")
    return page(rec["title"], 3, "\n".join(body))

def list_page(title, depth, intro, groups):
    body = [f"<h1>{title}</h1>"]
    if intro:
        body.append(f'<p class="note">{intro}</p>')
    for name, slug, items in groups:
        body.append(f'<h2><a href="collection/{slug}.html" style="color:inherit">{name}</a></h2>')
        body.append("<ul>")
        for rec in items:
            body.append(f'  <li>\n    <a href="{rec["_href"]}">{rec["title"]}</a>\n'
                        f'    <span class="meta">{rec["type"].title()} · tier {rec["rights_tier"]}</span>\n  </li>')
        body.append("</ul>\n")
    return page(title, depth, "\n".join(body))

def collection_page(name, slug, items):
    body = [f"<h1>{name}</h1>",
            f'<p class="note">Held records from {name}, catalogued one at a time. No bulk copying.</p>',
            "<h2>Records</h2>", "<ul>"]
    for rec in items:
        body.append(f'  <li>\n    <a href="../{rec["_type"]}/{rec["_collection"]}/{rec["_slug"]}.html">{rec["title"]}</a>\n'
                    f'    <span class="meta">{rec["type"].title()} · tier {rec["rights_tier"]}</span>\n  </li>')
    body.append("</ul>")
    return page(name, 2, "\n".join(body))

def main():
    if not DATA.exists():
        sys.exit("no data/records directory")
    errors, records = [], []
    for path in sorted(DATA.rglob("*.json")):
        rec = json.loads(path.read_text())
        for e in VALIDATOR.iter_errors(rec):
            errors.append(f"{path}: {e.json_path} {e.message}")
        if errors:
            continue
        rec["_type"] = path.parent.parent.name
        rec["_collection"] = path.parent.name
        rec["_slug"] = path.stem
        rec["_href"] = f'{rec["_type"]}/{rec["_collection"]}/{rec["_slug"]}.html'
        records.append(rec)
    if errors:
        sys.exit("\n".join(errors))

    for d in (OUT / "collection",):
        if d.exists():
            shutil.rmtree(d)

    collections = {}
    for rec in records:
        target = OUT / rec["_type"] / rec["_collection"] / f'{rec["_slug"]}.html'
        target.parent.mkdir(parents=True, exist_ok=True)
        name = rec["_collection"].replace("-", " ").title()
        target.write_text(record_page(rec, name))
        collections.setdefault((name, rec["_collection"]), []).append(rec)

    (OUT / "collection").mkdir(parents=True, exist_ok=True)
    for (name, slug), items in collections.items():
        (OUT / "collection" / f"{slug}.html").write_text(collection_page(name, slug, items))

    groups = [(name, slug, items) for (name, slug), items in sorted(collections.items())]
    (OUT / "index.html").write_text(
        list_page("Records", 1, "Grouped by collection. Every entry names its source or is flagged unsourced.", groups))

    print(f"{len(records)} records in {len(collections)} collections")

if __name__ == "__main__":
    main()
