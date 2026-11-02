"""Import every CSV in batches/incoming through the pipeline (oldest first).

Imported files move to batches/imported/, rejected ones to batches/rejected/ with a .json reason
that the website shows in its batch log. Exit code 0 even when a batch is rejected.
"""
import os, glob, json, shutil, datetime
from dtwin import pipeline as pl

ROOT = pl.ROOT
inc = os.path.join(ROOT, "batches", "incoming")
files = sorted([f for f in glob.glob(os.path.join(inc, "*")) if f.lower().endswith((".csv", ".txt"))], key=os.path.getmtime)
if not files:
    print("no incoming batches")
for f in files:
    name = os.path.splitext(os.path.basename(f))[0]
    print(f"== {os.path.basename(f)}")
    try:
        _, meta = pl.read_batch(f)
        bid = (meta.get("batch_id") or name).strip()
        r = pl.import_batch(f, batch_id=bid, refit_mechanistic=os.environ.get("REFIT_MECH") == "1")
        errors = r.get("errors", []) if r["status"] == "rejected" else []
    except Exception as e:   # duplicate id, unreadable file, ...
        bid, errors, meta = name, [str(e)], {}
    if errors:
        json.dump(dict(id=bid, recipe=meta.get("recipe", ""), date=f"{datetime.date.today()}", file=os.path.basename(f), errors=errors),
                  open(os.path.join(ROOT, "batches", "rejected", f"{bid}.json"), "w"), indent=1)
        shutil.move(f, os.path.join(ROOT, "batches", "rejected", os.path.basename(f)))
        print("   rejected:", "; ".join(errors))
    else:
        shutil.move(f, os.path.join(ROOT, "batches", "imported", os.path.basename(f)))
print("current model:", pl.champion())
