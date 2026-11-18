"""Validate the Samsung catalogue against TechSpecs Product Record V2."""
import csv
import json
from hashlib import sha256
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


def validate_media(coverage):
    media_dir = ROOT / "data/media"
    with (media_dir / "samsung-images.csv").open(newline="", encoding="utf-8") as handle:
        images = list(csv.DictReader(handle))
    seen_ids, seen_files, seen_hashes = set(), set(), set()
    for image in images:
        record_id = image["record_id"]
        require(record_id in coverage and record_id not in seen_ids,
                f"Unknown or duplicate Samsung image record: {record_id}")
        require(image["role"] == "primary" and image["format"] == "WEBP",
                f"Invalid primary image metadata: {record_id}")
        require(manufacturer(image["source_url"]) and manufacturer(image["original_url"]),
                f"Invalid manufacturer image provenance: {record_id}")
        file = (ROOT / "data" / image["local_path"]).resolve()
        require(file.is_relative_to(media_dir / record_id) and file.is_file(),
                f"Missing or misplaced image: {record_id}")
        content = file.read_bytes()
        digest = sha256(content).hexdigest()
        require(len(content) == int(image["bytes"]) and digest == image["sha256"],
                f"Image integrity mismatch: {record_id}")
        require(content[:4] == b"RIFF" and content[8:12] == b"WEBP"
                and min(int(image["width"]), int(image["height"])) >= 150,
                f"Invalid image format or dimensions: {record_id}")
        require(digest not in seen_hashes and file not in seen_files,
                f"Duplicate image contents: {record_id}")
        require(image["rights_status"] == "reuse_permission_unverified",
                f"Unexpected reuse status: {record_id}")
        if image["model_number"]:
            record = json.loads((ROOT / f"data/{record_id}.json").read_text(encoding="utf-8"))
            model_numbers = record["product"].get("model_numbers", [])
            require(image["model_number"].upper() in {code.upper() for code in model_numbers},
                    f"Image SKU mismatch: {record_id}")
        seen_hashes.add(digest)
        seen_files.add(file)
        seen_ids.add(record_id)
    require(seen_files == set((media_dir / "samsung").rglob("*.webp")),
            "Image files do not match the Samsung photo manifest")
    require(seen_ids == {record_id for record_id, row in coverage.items()
                         if row["primary_photo"] == "validated"},
            "Photo coverage does not match the Samsung photo manifest")
    print(f"Validated {len(seen_ids)} Samsung primary images")


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
    validate_media({key[5:-5]: row for key, row in coverage.items()})


if __name__ == "__main__":
    main()
