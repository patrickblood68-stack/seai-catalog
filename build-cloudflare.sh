#!/bin/sh
set -eu

mkdir -p dist
cp public/index.html public/404.html public/robots.txt public/sitemap.xml llms.txt llms-full.txt dist/
cp -R data schemas inventory dist/

python3 - <<'PY'
import json
from pathlib import Path

catalog = json.loads(Path("catalog.json").read_text(encoding="utf-8"))
evidence = json.loads(Path(catalog["evidence"]["records"]).read_text(encoding="utf-8"))
pilot = next(record for record in evidence
             if record["sourcePageId"] == "individual-grants-attic-insulation")
public_catalog = {"featuredEvidence": pilot, **catalog}
Path("dist/catalog.json").write_text(
    json.dumps(public_catalog, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
PY
