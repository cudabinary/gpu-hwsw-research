# Provenance of the English edition

The translations preserve the historical experimental scope and leave the graph fixtures, traversal implementations, and numerical results intact. The original file bytes and historical manifests are available in the parent commit of this update. The repository retains legacy filenames, including some with a `_KO` suffix, so references and reproduction scripts continue to resolve.

The vendored RCC directory has five localized files. These are the three handoff documents in `reference/` and the report templates in `tools/report.py` and `tools/strong_control_audit.py`. [VENDOR_SHA256.json](VENDOR_SHA256.json) pins the English edition. Historical verification records refer to the pins at their original commits. The report generator leaves the translated handoff files in place and uses the original attachments in `input/handoff` when auditing historical data.

Public audit and command records use placeholders for the original Windows account and personal directory names. The placeholders represent historical paths and must be resolved locally if the original files are needed. The records' measurements, commands apart from those path components, and recorded artifact hashes are preserved.

## RCC-Scope, DistanceGuard, and historical replay

The extracted [RCC-Scope and DistanceGuard package](../../intake/rcc_scope_distance_20261021/package/RCC_SCOPE_CPU_MODULE_20261021/README_FIRST_KO.md) has six translated documents. Its current manifest verifies the English edition. The original 2,528,431-byte ZIP remains in commit `8753f466eba01ee17658e9548a8048b7f7d7cf89` and retains SHA-256 `c1ba7f6c6d595f84081dceb66052d76344a6685b902ccccde7e6e7c9f0a51d7c`.

To retrieve the original ZIP, use a clone with the historical commit available.

```sh
git show 8753f466eba01ee17658e9548a8048b7f7d7cf89:intake/rcc_scope_distance_20261021/original.zip > RCC_SCOPE_DISTANCE_CPU_20261021.zip
sha256sum RCC_SCOPE_DISTANCE_CPU_20261021.zip
```

In a clean copy of the English edition, `python3 tools/intake_scope_distance.py /path/to/RCC_SCOPE_DISTANCE_CPU_20261021.zip` accepts the original attachment and verifies its original manifest before extraction. The original package contents, including its original language, are extracted in that workflow.

Historical experiment manifests cover the precise files as first recorded. For byte-exact reproduction and receipt verification, check out the matching historical snapshot with its original pins and inputs.

| Experiment | Historical commit |
|---|---|
| OLD_P2 matched service | `1a79b1048cc639c3c23f1000373c3ed6e10bbf7c` |
| RCC-Scope and DistanceGuard intake audit | `5c489f154d4c7c0bb587972ee307fcaf03a313e2` |
| DistanceGuard API experiment | `8753f466eba01ee17658e9548a8048b7f7d7cf89` |
