"""Validate the Samsung catalogue against TechSpecs Product Record V2."""
import csv
import json
from pathlib import Path
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def manufacturer(url):
    parsed = urlparse(url or "")
    host = parsed.hostname or ""
    return parsed.scheme == "https" and (host in {"samsung.com", "samsungmobilepress.com", "www.samsungmobilepress.com",
                       "api.samsungmobilepress.com"} or host.endswith(".samsung.com"))


def archive(relative):
    path = (ROOT / relative).resolve()
    require(path.is_relative_to(ROOT / "sources" / "samsung") and path.is_file(),
            f"Missing or invalid Samsung archive: {relative}")


def main():
    schema = json.loads((ROOT / "schemas/product-record-v2.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    with (ROOT / "coverage.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    coverage = {row["record_path"]: row for row in rows}
    require(len(rows) == len(coverage), "Coverage contains duplicate paths")
    files = sorted((ROOT / "data/samsung").rglob("*.json"))
    require({path.relative_to(ROOT).as_posix() for path in files} == set(coverage),
            "Coverage does not match the Samsung record files")
    for path in files:
        record = json.loads(path.read_text(encoding="utf-8"))
        validator.validate(record)
        product, source = record["product"], record["source"]
        require(product["brand"] == "Samsung" and product["model_slug"] == path.stem,
                f"Model identity mismatch: {path}")
        require(manufacturer(source["source_url"]), f"Invalid manufacturer URL: {path}")
        archive(source["source_file"])
        headings = set()
        for section in record["sections"]:
            headings.add(section["heading"])
            require(manufacturer(section.get("source_url")), f"Invalid section URL: {path}")
            archive(section["source_file"])
        fields = [field for group in record.get("normalized_specifications", {}).values()
                  for field in group.values()]
        require(all(field["source_section"] in headings for field in fields),
                f"Missing normalized-field evidence: {path}")
        row = coverage[path.relative_to(ROOT).as_posix()]
        require(row["model"] == product["model"] and row["source_url"] == source["source_url"]
                and int(row["fields"]) == len(fields) and int(row["sections"]) == len(record["sections"]),
                f"Coverage metadata does not match the record: {path}")
    print(f"Validated {len(files)} Samsung V2 records and their evidence references")


if __name__ == "__main__":
    main()
