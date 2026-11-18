# Samsung product specifications

The Samsung catalogue uses the TechSpecs Product Record V2 schema. Record and
evidence paths in JSON and coverage.csv are relative to this directory.

Coverage includes 138 models, of which 85 were rebuilt. The coverage CSV
identifies 77 records that meet their category minimum, eight rebuilt records
that need wider coverage and 53 records pending further source review. The
minimum is a coverage measure. Regional specifications apply to the cited
configuration, and all records retain their verification status.

Minimum fields by category are 15 across display, camera, battery, connectivity
and processor for phones, 15 including display, battery and connectivity for
tablets, and 12 including processor and display for computers. Audio, watches,
fitness trackers, displays and smart speakers need 12 fields across three
groups. Other categories require further coverage review.

Run `python techspecs/validate.py` from the repository root. Evidence files are
under `sources/samsung/` and manufacturer source links are recorded per section.
