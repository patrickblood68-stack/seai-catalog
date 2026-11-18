# Samsung product specifications

The Samsung catalogue uses the TechSpecs Product Record V2 schema. Record and
evidence paths in JSON and coverage.csv are relative to this directory.

Coverage includes 138 models, of which 125 were rebuilt. The coverage CSV
identifies 115 records that meet their category minimum, 10 rebuilt records
that need wider coverage and 13 records pending further source review. The
minimum is a coverage measure. Regional specifications apply to the cited
configuration, and all records retain their verification status.

Minimum fields by category are 15 across display, camera, battery, connectivity
and processor for phones, 15 including display, battery and connectivity for
tablets, and 12 including processor and display for computers. Audio, watches,
fitness trackers, displays and smart speakers need 12 fields across three
groups. Other categories require further coverage review.

Run `python techspecs/validate.py` from the repository root. Evidence files are
under `sources/samsung/` and manufacturer source links are recorded per section.

## Samsung imagery

The shared-style media index is `data/media/samsung-images.csv`. It links
52 primary WebP images to exact Samsung product record IDs. Each row
retains the manufacturer page and asset URL, matching basis, stored
dimensions, checksum, and rights status. When an exact SKU is listed it
matches the cited product record. A model-level manufacturer render can
illustrate a different finish or market version of the same model.
Reuse permission remains unverified. The 86 remaining records carry
pending photo status in the coverage CSV.
