# Documents to add (requested by team lead) - names, IDs, manifest entries

How to add one: (1) download from the OFFICIAL page, (2) PSI / overview web pages: Print -> Save as PDF,
(3) put the file in `data/raw_documents/`, (4) add its entry to `data/raw_documents/manifest.json`
(copy the template below, fill only what is printed on the document or verified), (5) `python rag_pipeline.py ingest`.
A source counts as ingested only after the file is downloaded and its text checked.
`url` below = from the register / team document, NOT yet verified by me.

| Priority | What | Register ID | Official page (from register/team doc) | content_type |
|---|---|---|---|---|
| 1 | PSI-25 BASS-II record page | S13 | https://psi.nasa.gov/physci/repo/data/investigations/PSI-25 | catalogue_record |
| 1 | PSI-98 SAFFIRE I record page | S18 | https://psi.nasa.gov/physci/repo/data/investigations/PSI-98 | catalogue_record |
| 1 | PSI-99 SAFFIRE-II / PSI-100 SAFFIRE III record pages | S19 / S20 | .../PSI-99 and .../PSI-100 | catalogue_record |
| 1 | PSI-102 SAME record page | S21 | .../PSI-102 | catalogue_record |
| 1 | PSI-101 SAME-R record page | S22 | .../PSI-101 | catalogue_record |
| 1 | PSI-107 SPICE record page | S24 | .../PSI-107 | catalogue_record |
| 2 | NASA Combustion Science overview (web page) | S35 | https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/ | document |
| 3 | Researcher's Guide to ISS Combustion Science | S2 | ALREADY INGESTED - only confirm it is the right document (see manifest note) | document |
| 4 | Saffire VI paper, ICES-2024-365 | S4 (S31 is a duplicate record of the same NTRS number) | https://ntrs.nasa.gov/citations/20240002981 | document |
| 5 | Apollo 1 fire - official NASA review board report | DOC-APOLLO1 (proposed) | ask Younus which document | document |
| 5 | Apollo 13 - official NASA review board report | DOC-APOLLO13 (proposed) | ask Younus which document | document |
| 5 | Mir fire (1997) - official NASA report/lessons learned | DOC-MIR-FIRE (proposed) | ask Younus which document | document |
Nice to have: S37 "Studying Combustion and Fire Safety" (https://www.nasa.gov/missions/station/iss-research/studying-combustion-and-fire-safety/),
S38 ACME page (https://science.nasa.gov/biological-physical/investigations/acme/), S47 SoFIE page.

IDs marked "proposed" are NOT in the register: they are created from the manifest entry (source_class "UNVERIFIED (added from manifest)").
PSI record pages are catalogue metadata, not experimental findings. Do not claim raw data is ingested unless data files are downloaded and inspected.

## Manifest template
```json
"Saffire_VI_ICES-2024-365.pdf": {
  "source_id": "S4", "register_id": "S4",
  "title": "<exact title printed on the document>",
  "publisher": "<as printed>", "year": "<as printed>",
  "url": "https://ntrs.nasa.gov/citations/20240002981",
  "content_type": "document", "note": "optional: anything unverified"
}
```
For PSI pages use `"content_type": "catalogue_record"` and the `S13`/`S18`/... register_id.
