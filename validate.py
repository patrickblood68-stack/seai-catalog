import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def validate():
    catalog = load("catalog.json")
    source_pages = {}
    for dataset in catalog["datasets"]:
        schema = load(dataset["schema"])
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        pages = load(dataset["records"])
        if not isinstance(pages, list) or len(pages) != dataset["recordCount"]:
            raise ValueError("Catalog record count does not match the data")
        for page in pages:
            validator.validate(page)
        ids = {page["id"] for page in pages}
        urls = {page["sourceUrl"] for page in pages}
        paths = [snapshot["archivePath"] for page in pages for snapshot in page["snapshots"]]
        if len(ids) != len(pages) or len(urls) != len(pages) or len(set(paths)) != len(paths):
            raise ValueError("Duplicate ID, source URL or snapshot path")
        for page in pages:
            if set(page["relatedIds"]) - (ids - {page["id"]}):
                raise ValueError(f"Invalid related record in {page['id']}")
        source_pages.update((page["id"], page) for page in pages)
        print(f"Validated {len(pages)} source records and {len(paths)} snapshot references")

    evidence = catalog.get("evidence")
    if evidence:
        validate_evidence(evidence, source_pages)


def validate_evidence(dataset, source_pages):
    schema = load(dataset["schema"])
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    items = load(dataset["records"])
    if not isinstance(items, list) or len(items) != dataset["recordCount"]:
        raise ValueError("Catalog evidence count does not match the data")
    seen = set()
    for item in items:
        validator.validate(item)
        source_id = item["sourcePageId"]
        source = source_pages.get(source_id)
        if source_id in seen or not source or source["sourceUrl"] != item["sourceUrl"]:
            raise ValueError(f"Invalid or duplicate evidence reference: {source_id}")
        if item["reviewBy"] < item["lastCheckedAt"]:
            raise ValueError(f"Review date precedes check date: {source_id}")
        headings = {heading["title"] for heading in source["headings"]}
        if any(section["heading"] not in headings for section in item["sections"]):
            raise ValueError(f"Evidence heading missing from source record: {source_id}")
        seen.add(source_id)
    print(f"Validated {len(items)} evidence records")


if __name__ == "__main__":
    validate()
