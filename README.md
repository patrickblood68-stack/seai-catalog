# SEAI home energy grants source index

A machine-readable catalog of 25 SEAI pages derived from 26 supplied HTML
snapshots. It indexes page titles, descriptions, headings and links between
records. The source URL points to SEAI. Details such as current eligibility
and grant amounts should be checked on the live source.

Start at [catalog.json](catalog.json). For agent integration, see
[llms.txt](llms.txt). Provenance includes the original ZIP member path and
SHA-256 for each snapshot. The attic insulation snapshots share a record
because they have the same canonical URL and matching visible main text.

To validate locally, run `python -m pip install -r requirements.txt` and
`python validate.py`. GitHub Actions runs the same check. To publish the
static catalog, serve catalog.json, data/, schemas/, llms.txt and llms-full.txt.

## Contractor profiles

`sh build-cloudflare.sh` builds the directory, one profile per listing and the
`/contractors/profiles.json` feed from both checked-in SEAI register files.
`python contractor_profiles.py --check` validates the records against
`schemas/contractor-profile-v1.json`.

Individual profiles use the SEAI contractor ID. One Stop Shop profiles use the
list type and a hash of the normalized provider name because those snapshots
carry no provider ID. A spelling change can change the profile URL. A business
that appears in multiple lists keeps a record for each listing.

The generated profiles contain SEAI snapshot information. Their company match
and review status start at `unmatched` and `to_check`. SoloCheck enrichment
requires a confirmed company match and is a separate review step.


Research records in `research/contractors/` are validated by `--check` and joined
by contractor ID. The normal build adds business contact fields and source links
from records with workflow status `published`. Register fields are taken from the
snapshots, and company matching and review notes stay in the research files.

To review contact details before publishing, run
`python contractor_profiles.py --preview-research --output /tmp/seai-profile-review`
and open the generated contractor pages locally.
