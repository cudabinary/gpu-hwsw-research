# Provenance of the English edition

The translations preserve the historical experimental scope and leave the graph fixtures, traversal implementations, and numerical results intact. The original file bytes and historical manifests are available in the parent commit of this update. The repository retains legacy filenames, including some with a `_KO` suffix, so references and reproduction scripts continue to resolve.

The vendored RCC directory has five localized files. These are the three handoff documents in `reference/` and the report templates in `tools/report.py` and `tools/strong_control_audit.py`. [VENDOR_SHA256.json](VENDOR_SHA256.json) pins the English edition. Historical verification records refer to the pins at their original commits. The report generator leaves the translated handoff files in place and uses the original attachments in `input/handoff` when auditing historical data.

Public audit and command records use placeholders for the original Windows account and personal directory names. The placeholders represent historical paths and must be resolved locally if the original files are needed. The records' measurements, commands apart from those path components, and recorded artifact hashes are preserved.
