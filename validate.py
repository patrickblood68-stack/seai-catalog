import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def validate():
    for dataset in load("catalog.json")["datasets"]:
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
        print(f"Validated {len(pages)} source records and {len(paths)} snapshot references")


if __name__ == "__main__":
    validate()
