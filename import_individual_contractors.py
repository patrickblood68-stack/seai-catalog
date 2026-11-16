"""Refresh the SEAI contractor snapshot using the public search form."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from html import unescape
from html.parser import HTMLParser
from http.cookiejar import CookieJar
import json
from pathlib import Path
import re
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, build_opener

from render_individual_contractors import SNAPSHOT

SOURCE = "https://hes.seai.ie/GrantProcess/ContractorSearch.aspx"
LOCATION = "ctl00$DefaultContent$ContractorSearch1$dfSearch$County"
SEARCH = "ctl00$DefaultContent$ContractorSearch1$dfSearch$search"


class FormFields(HTMLParser):
    def __init__(self, document):
        super().__init__()
        self.values = {}
        self.feed(document)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "input" and attrs.get("type") in ("hidden", "text") and attrs.get("name"):
            self.values[attrs["name"]] = attrs.get("value", "")


def request(session, fields=None):
    data = None if fields is None else urlencode(fields).encode()
    with session.open(SOURCE, data, timeout=45) as response:
        return response.read().decode("utf-8")


def result_rows(page):
    for row in re.findall(r'<tr class="Grid(?:Alternating)?RowStyle">(.*?)</tr>', page, re.S):
        values = [unescape(re.sub(r"<[^>]+>", "", cell)).strip()
                  for cell in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
        contractor_id, name, _, _, _, location, areas, measures = values
        yield {
            "id": contractor_id,
            "name": name,
            "locatedIn": location,
            "serviceAreas": sorted({part.strip() for part in areas.split(",") if part.strip()}),
            "measures": sorted({part.strip() for part in measures.split(",") if part.strip()}),
        }


def collect_location(location):
    key, label = location
    session = build_opener(HTTPCookieProcessor(CookieJar()))
    fields = FormFields(request(session)).values
    page = request(session, {**fields, LOCATION: key, SEARCH: "Search"})
    count = re.search(r"Total items:\s*([\d,]+)", page)
    if not count and ("No records" in page or "No contractors" in page):
        return label, []
    if not count:
        raise ValueError(f"No result count for {label}")
    total = int(count[1].replace(",", ""))
    if not total:
        return label, []
    rows = {}
    while True:
        count = re.search(r"Total items:\s*([\d,]+)", page)
        if not count or int(count[1].replace(",", "")) != total:
            raise ValueError(f"Result count changed for {label}")
        batch = list(result_rows(page))
        ids = {row["id"] for row in batch}
        if len(ids) != len(batch) or rows.keys() & ids or not ids:
            raise ValueError(f"Invalid or repeated contractor IDs for {label}")
        rows.update((row["id"], row) for row in batch)
        if len(rows) == total:
            return label, list(rows.values())
        next_page = re.search(r'<input[^>]+title="Next Page"[^>]*>', page)
        if not next_page or len(rows) > total:
            raise ValueError(f"Collected {len(rows)} of {total} contractor IDs for {label}")
        target, argument = re.findall(r"'([^']+)'", unescape(next_page[0]))[:2]
        fields = FormFields(page).values
        page = request(session, {**fields, "__EVENTTARGET": target, "__EVENTARGUMENT": argument})


def merge_contractors(location_results):
    contractors = {}
    for label, rows in location_results:
        for row in rows:
            previous = contractors.setdefault(row["id"], row)
            if previous["name"] != row["name"] or previous["locatedIn"] != row["locatedIn"]:
                raise ValueError(f"Conflicting records for contractor {row['id']} in {label}")
            for key in ("serviceAreas", "measures"):
                previous[key] = sorted(set(previous[key]) | set(row[key]))
    return sorted(contractors.values(), key=lambda row: int(row["id"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checked", type=date.fromisoformat, required=True, help="Date of the register check in YYYY-MM-DD format")
    args = parser.parse_args()
    session = build_opener(HTTPCookieProcessor(CookieJar()))
    form = request(session)
    county = re.search(r'<select name="' + re.escape(LOCATION) + r'".*?</select>', form, re.S)
    if not county:
        raise ValueError("Could not find the SEAI location filter")
    options = re.findall(r'<option value="(\d+)">([^<]+)', county[0])
    if not options:
        raise ValueError("The SEAI location filter has no usable options")
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(collect_location, options))
    snapshot = {
        "checked": args.checked.isoformat(),
        "sourceUrl": SOURCE,
        "locationCounts": {label: len(rows) for label, rows in results},
        "contractors": merge_contractors(results),
    }
    candidate = Path(SNAPSHOT).with_suffix(".tmp")
    candidate.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    candidate.replace(SNAPSHOT)


if __name__ == "__main__":
    main()
