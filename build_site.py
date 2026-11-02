"""Build the public website (site/index.html) from the current model in registry/."""
import os, json
from dtwin import pipeline as pl

ROOT = pl.ROOT
os.makedirs(os.path.join(ROOT, "site"), exist_ok=True)
pl.export_web(os.path.join(ROOT, "web", "model.json"))
repo = os.environ.get("GITHUB_REPOSITORY", "")
branch = os.environ.get("GITHUB_REF_NAME", "main")
tpl = open(os.path.join(ROOT, "web", "template.html"), encoding="utf-8").read()
body = (tpl.replace("/*MODEL_JSON*/", open(os.path.join(ROOT, "web", "model.json"), encoding="utf-8").read())
           .replace("/*TWIN_JS*/", open(os.path.join(ROOT, "web", "twin.js"), encoding="utf-8").read()))
site_cfg = f"<script>window.SITE = {json.dumps({'repo': repo, 'branch': branch})};</script>\n"
html = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
        "<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}"
        "body{margin:0;font-size:14px;font-family:system-ui,-apple-system,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>\n"
        "</head>\n<body>\n" + site_cfg + body + "\n</body>\n</html>\n")
open(os.path.join(ROOT, "site", "index.html"), "w", encoding="utf-8").write(html)
open(os.path.join(ROOT, "site", ".nojekyll"), "w").write("")
print(f"site/index.html built with model {pl.champion()} ({len(html) // 1024} KB)")
