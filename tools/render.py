import html, pathlib

T = pathlib.Path(__file__).parent
BASE = (T / "base.html").read_text()
CSS = (T / "style.css").read_text()
ACTIONS = (T / "actions.html").read_text()

def page(title, depth, body):
    return (BASE.replace("{{TITLE}}", html.escape(title))
        .replace("{{CSS}}", CSS)
        .replace("{{UP}}", "../" * depth)
        .replace("{{BODY}}", body))

def figure(r):
    if not r.get("image"):
        return ""
    c = r.get("credit") or r.get("external_id", {}).get("institution", "")
    return (f'<figure style="margin:2rem 0">'
            f'<img src="{r["image"]}" alt="{r.get("image_alt", "")}" '
            f'style="width:100%;height:auto;display:block">'
            f'<figcaption class="note" style="margin-top:.5rem">'
            f'{c}. Public domain.</figcaption></figure>')
