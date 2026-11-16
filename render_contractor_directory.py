"""Render the SEAI provider directory from dated register snapshots."""
from html import escape
import json
from pathlib import Path


def provider_table(title, providers, third_column=None):
    rows = []
    for provider in sorted(providers, key=lambda row: row["name"].casefold()):
        cells = [provider["name"], provider["coverage"]]
        if third_column:
            cells.append("Yes" if provider["individualUpgrades"] else "No")
        rows.append("<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in cells) + "</tr>")
    extra_heading = f"<th scope='col'>{third_column}</th>" if third_column else ""
    return (
        f"<section><h2>{title}</h2><p>{len(rows)} listings</p><table>"
        f"<thead><tr><th scope='col'>Provider</th><th scope='col'>Areas served</th>{extra_heading}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></section>"
    )


def render_directory(output):
    snapshot = json.loads(Path("registers/one-stop-shops.json").read_text(encoding="utf-8"))
    registered = provider_table("Registered One Stop Shops", snapshot["registered"], "Individual upgrades")
    participating = provider_table("Participating One Stop Shops for Better Energy Homes", snapshot["participating"])
    directory = output / "contractors"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "index.html").write_text(f"""<!doctype html>
<html lang="en-IE">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Find an SEAI contractor or One Stop Shop</title>
<style>
body {{ font: 1rem/1.55 system-ui, sans-serif; color: #17291f; background: #f1f5f1; }}
main {{ max-width: 65rem; margin: auto; padding: 1rem; }}
a {{ color: #17533b; }}
input {{ font: inherit; max-width: 100%; box-sizing: border-box; padding: .4rem; }}
table {{ width: 100%; border-collapse: collapse; background: white; }}
th, td {{ padding: .55rem; text-align: left; vertical-align: top; border-bottom: 1px solid #cbd8cd; }}
</style>
</head>
<body><main>
<nav><a href="/#guides">Home energy guides</a></nav>
<h1>Find an SEAI contractor or One Stop Shop</h1>
<section>
<h2>Contractors for individual grants</h2>
<p><a href="https://hes.seai.ie/GrantProcess/ContractorSearch.aspx">Search SEAI’s live contractor register</a> by service area, upgrade type, company name or contractor ID.</p>
</section>
<p>One Stop Shop listings checked <time datetime="{snapshot["checked"]}">16 November 2026</time>.
Check the <a href="https://www.seai.ie/find-grants-and-contractors/find-contractors/registered-one-stop-shops">live registered list</a>
or <a href="https://www.seai.ie/grants/find-a-registered-professional/energy-partners">live participating list</a> before choosing a provider.</p>
<div id="search" hidden>
  <label for="filter">Filter One Stop Shops by provider or county</label>
  <input id="filter" type="search">
  <p id="count" role="status"></p>
</div>
{registered}
{participating}
</main>
<script>
const search = document.querySelector("#search");
const filter = document.querySelector("#filter");
const count = document.querySelector("#count");
const rows = [...document.querySelectorAll("tbody tr")];
search.hidden = false;
filter.addEventListener("input", () => {{
  const query = filter.value.trim().toLocaleLowerCase("en-IE");
  let matches = 0;
  for (const row of rows) {{
    const text = row.cells[0].textContent + " " + row.cells[1].textContent;
    row.hidden = !text.toLocaleLowerCase("en-IE").includes(query) &&
      row.cells[1].textContent !== "All";
    matches += Number(!row.hidden);
  }}
  count.textContent = matches + " matching listings across both registers";
}});
</script>
</body></html>
""", encoding="utf-8")
