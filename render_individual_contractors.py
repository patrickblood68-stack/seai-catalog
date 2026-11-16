"""Render the individual-grants register snapshot as searchable HTML."""
from html import escape
import json
from pathlib import Path

SNAPSHOT = Path("registers/individual-contractors.json")
ROUTE = "/contractors/individual/"


def filter_select(label, values, field):
    options = "".join(f"<option>{escape(value)}</option>" for value in sorted(values))
    return f'<label>{label} <select disabled data-field="{field}"><option value="">Any</option>{options}</select></label>'


def render_individual_contractors(output):
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    checked = escape(snapshot["checked"])
    contractors = sorted(snapshot["contractors"], key=lambda row: (row["name"].casefold(), row["id"]))
    rows = []
    service_areas = set()
    measures = set()
    for contractor in contractors:
        areas = contractor["serviceAreas"]
        upgrades = contractor["measures"]
        service_areas.update(areas)
        measures.update(upgrades)
        cells = [contractor["id"], contractor["name"], contractor["locatedIn"], ", ".join(areas), ", ".join(upgrades)]
        rows.append(
            f'<tr data-areas="{escape("|".join(areas))}" data-measures="{escape("|".join(upgrades))}">'
            + "".join(f"<td>{escape(cell)}</td>" for cell in cells) + "</tr>"
        )
    table = "\n".join(rows)
    area_filter = filter_select("Service area", service_areas, "areas")
    measure_filter = filter_select("Registered measure", measures, "measures")
    directory = output / ROUTE.strip("/")
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "index.html").write_text(f"""<!doctype html>
<html lang="en-IE">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SEAI contractors for individual home energy grants</title>
<style>
body {{font: 1rem/1.5 system-ui, sans-serif; color: #17291f; background: #f1f5f1;}}
main {{max-width: 76rem; margin: auto; padding: 1rem;}}
a {{color: #17533b;}}
form {{display: flex; flex-wrap: wrap; gap: 1rem;}}
label {{display: grid; gap: .25rem;}}
input, select {{font: inherit; max-width: 100%;}}
.table {{overflow-x: auto;}}
table {{width: 100%; border-collapse: collapse; background: white;}}
th, td {{padding: .55rem; text-align: left; vertical-align: top; border-bottom: 1px solid #cbd8cd;}}
</style>
</head>
<body><main>
<nav><a href="/contractors/">Contractors and One Stop Shops</a></nav>
<h1>SEAI contractors for individual home energy grants</h1>
<p>Each SEAI contractor ID appears once. Use the service area to find contractors who cover your home. The location column shows where each contractor is based.</p>
<p>Register checked <time datetime="{checked}">{checked}</time>. Confirm registration for your upgrade in the <a href="{escape(snapshot["sourceUrl"])}">live SEAI contractor register</a>.</p>
<form>
<label>Name or SEAI ID <input type="search" disabled></label>
{area_filter}
{measure_filter}
</form>
<p id="count" role="status">{len(rows):,} contractors</p>
<div class="table"><table>
<thead><tr><th scope="col">SEAI ID</th><th scope="col">Company</th><th scope="col">Located in</th><th scope="col">Service areas</th><th scope="col">Registered measures</th></tr></thead>
<tbody>{table}</tbody>
</table></div>
</main>
<script>
const form = document.querySelector("form");
const searchInput = form.querySelector("input");
const area = form.querySelector('[data-field="areas"]');
const measure = form.querySelector('[data-field="measures"]');
const count = document.querySelector("#count");
const rows = [...document.querySelectorAll("tbody tr")];
for (const field of [searchInput, area, measure]) field.disabled = false;
form.addEventListener("submit", event => event.preventDefault());
form.addEventListener("input", () => {{
  const query = searchInput.value.trim().toLocaleLowerCase("en-IE");
  let matches = 0;
  for (const row of rows) {{
    const label = row.cells[0].textContent + " " + row.cells[1].textContent;
    const visible = label.toLocaleLowerCase("en-IE").includes(query) &&
      (!area.value || row.dataset.areas.split("|").includes(area.value)) &&
      (!measure.value || row.dataset.measures.split("|").includes(measure.value));
    row.hidden = !visible;
    matches += Number(visible);
  }}
  count.textContent = matches.toLocaleString("en-IE") + " contractors";
}});
</script></body></html>
""", encoding="utf-8")
