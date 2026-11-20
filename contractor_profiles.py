"""Build profile records from the checked-in SEAI register snapshots."""
import argparse
from hashlib import sha256
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REGISTER = ROOT / "registers"
SCHEMA = ROOT / "schemas" / "contractor-profile-v1.json"
ONE_STOP_SOURCES = {
    "registered": "https://www.seai.ie/find-grants-and-contractors/find-contractors/registered-one-stop-shops",
    "participating": "https://www.seai.ie/grants/find-a-registered-professional/energy-partners",
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def profile(key, reference, name, checked, source, **business):
    return {
        "schema_version": 1,
        "contractor_id": key,
        "listing_reference": reference,
        "trading_name": name,
        "business": {**business, "sources": [{"url": source, "checked_on": checked}]},
        "company": {"match_status": "unmatched"},
        "workflow": {"status": "to_check"},
    }


def shop_key(group, name):
    normalized = " ".join(name.casefold().split())
    digest = sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return f"oss-{group}-{digest}"


def records():
    individual = read(REGISTER / "individual-contractors.json")
    shops = read(REGISTER / "one-stop-shops.json")
    for row in individual["contractors"]:
        if not row["id"].isascii() or not row["id"].isdigit():
            raise ValueError(f"Invalid SEAI contractor ID: {row['id']}")
        base = {"base_location": row["locatedIn"]} if row["locatedIn"] else {}
        yield profile(
            f"seai-{row['id']}", f"SEAI contractor ID {row['id']}",
            row["name"], individual["checked"], individual["sourceUrl"],
            services=row["measures"], service_areas=row["serviceAreas"], **base,
        )
    for group, source in ONE_STOP_SOURCES.items():
        for row in shops[group]:
            name = row["name"]
            coverage = [area.strip() for area in row.get("coverage", "").split(",") if area.strip()]
            yield profile(
                shop_key(group, name), f"SEAI {group} One Stop Shop",
                name, shops["checked"], source, service_areas=coverage,
            )


def profile_href(key):
    return f"/contractors/profiles/{key}/"


def render(record, output):
    key = record["contractor_id"]
    name = escape(record["trading_name"])
    business = record["business"]
    source = business["sources"][0]
    details = {
        "SEAI listing": record["listing_reference"],
        "Based in": business.get("base_location"),
        "Service areas": ", ".join(business.get("service_areas", [])),
        "Registered measures": ", ".join(business.get("services", [])),
    }
    fields = "".join(
        f"<dt>{label}</dt><dd>{escape(value)}</dd>"
        for label, value in details.items() if value
    )
    directory = output / profile_href(key).strip("/")
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "index.html").write_text(f"""<!doctype html>
<html lang="en-IE">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} | Contractor profile</title>
<style>
body {{font: 1rem/1.55 system-ui, sans-serif; color: #17291f; background: #f1f5f1;}}
main {{max-width: 48rem; margin: 2rem auto; padding: 1rem;}}
a {{color: #17533b;}} article {{background: white; padding: 1.5rem;}}
dt {{font-weight: bold; margin-top: .75rem;}} dd {{margin: 0;}}
</style></head>
<body><main><nav><a href="/contractors/">Contractor directory</a></nav>
<article><h1>{name}</h1><dl>{fields}</dl>
<p><a href="{escape(source['url'])}">SEAI register</a> · checked {escape(source['checked_on'])}</p></article>
</main></body></html>
""", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("dist"))
    parser.add_argument("--check", action="store_true", help="Validate records without writing files")
    args = parser.parse_args()
    profiles = list(records())
    if len({row["contractor_id"] for row in profiles}) != len(profiles):
        raise ValueError("Duplicate contractor profile ID")
    if args.check:
        from jsonschema import Draft202012Validator, FormatChecker
        schema = read(SCHEMA)
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        for row in profiles:
            validator.validate(row)
    else:
        for row in profiles:
            render(row, args.output)
        target = args.output / "contractors" / "profiles.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(profiles, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{len(profiles):,} contractor listings")


if __name__ == "__main__":
    main()
