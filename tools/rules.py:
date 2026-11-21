import datetime

def check(r, path):
    """Returns (errors, notes). Notes are downgrades already applied."""
    errs, notes = [], []
    t = r.get("rights_tier")
    if r.get("image") and t == "A" and r.get("image_reuse_status") != "cleared":
        errs.append(f"{path}: tier A image without image_reuse_status: cleared")
    if t in ("A", "B") and not r.get("rights_checked_at"):
        errs.append(f"{path}: tier {t} needs rights_checked_at")
    if r.get("price") and r.get("commercial_reproduction_status") != "permitted":
        errs.append(f"{path}: priced but commercial reproduction not permitted")
    exp = r.get("permission_expiry")
    if exp and exp < datetime.date.today().isoformat() and t in ("A", "C"):
        r["rights_tier"] = "B"
        notes.append(f"{path}: permission expired {exp}, downgraded to B")
    if r.get("takedown", {}).get("state") == "complied" and r.get("rights_tier") != "D":
        r["rights_tier"] = "D"
        notes.append(f"{path}: takedown complied, forced to D")
    return errs, notes
