# Samsung product specifications

The Samsung catalogue uses the TechSpecs Product Record V2 schema. Record and
evidence paths in JSON and coverage.csv are relative to this directory.

Coverage includes 138 records. The coverage CSV tracks whether each model meets
its category minimum, has partial technical coverage, or needs further source
review. A category minimum measures technical coverage. Regional values apply
to the configurations identified in the evidence.

The minimum is 15 fields across display, camera, battery, connectivity and
processor for phones, 15 including display, battery and connectivity for
tablets, and 12 including processor and display for computers.
Audio, watches, fitness trackers, displays and smart speakers need 12 fields
across three groups. Keyboard covers require supported tablets, connector,
key count, dimensions and weight. Trackers require device compatibility,
radio and range, battery type and life, dimensions and weight. XR headsets
require display, processor, memory and storage, tracking, connectivity,
battery runtime and weight. Other categories require further coverage review.

Run `python techspecs/validate.py` from the repository root. Evidence files are
under `sources/samsung/` and manufacturer source links are recorded per section.

## Samsung imagery

The shared-style media index is `data/media/samsung-images.csv`. It links
primary WebP images to exact Samsung product record IDs. Each row
retains the manufacturer page and asset URL, matching basis, stored
dimensions, checksum, and rights status. When an exact SKU is listed it
matches the cited product record. A model-level manufacturer render can
illustrate a different finish or market version of the same model.
Reuse permission remains unverified. Records awaiting a suitable image carry pending photo status in the coverage CSV.
