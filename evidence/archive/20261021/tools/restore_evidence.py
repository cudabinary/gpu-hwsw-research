"""Portable authenticated full/selected byte recovery into a NEW directory.

Uses only the independent reader, not the uploader or original source paths.
Run --prompt-key on another computer (a local DPAPI blob is not portable).
Exact raw files are recovered; do not open operational SQLite databases until
applying the separately verified snapshot map and suppressing their sidecars.
"""
import argparse
import collections
import hashlib
import io
import json
import os
import re
from pathlib import Path
import shutil
import sys
import zipfile

from independent_restore import Reader, relative_ok, windows_relative_ok, json_rows


def main(args):
    destination = Path(args.destination).resolve()
    if destination.exists():
        raise RuntimeError("NEW_EMPTY_DESTINATION_REQUIRED")
    parent = destination.parent
    if not parent.is_dir():
        raise RuntimeError("DESTINATION_PARENT_MUST_EXIST")
    reader = Reader(prompt_key=args.prompt_key)
    checkpoint_bytes = reader.download(args.root_file_id, args.root_sha256)
    checkpoint = json.loads(checkpoint_bytes)
    if checkpoint.get("schema_version") not in ("1.0.0", "1.1.0", "1.2.0"):
        raise RuntimeError("UNSUPPORTED_RECOVERY_SCHEMA")
    package_bytes = reader.download(checkpoint["private_metadata"]["file_id"], checkpoint["private_metadata"]["sha256"])
    package = zipfile.ZipFile(io.BytesIO(package_bytes))
    frozen = zipfile.ZipFile(io.BytesIO(package.read("PRIVATE_RECOVERY_MANIFEST_FROZEN.zip")))
    for archive in (package, frozen):
        for name, pin in json.loads(archive.read("METADATA_SHA256.json")).items():
            data = archive.read(name)
            if not relative_ok(name) or len(data) != pin["bytes"] or hashlib.sha256(data).hexdigest() != pin["sha256"]:
                raise RuntimeError("RECOVERY_METADATA_PIN_MISMATCH")
    requested = {value.removeprefix("sha256:") for value in (args.evidence_id or [])}
    locations = collections.defaultdict(list)
    for row in json_rows(frozen, "manifest/LOCATION_MANIFEST.jsonl"):
        if args.root_id and row["root_id"] not in args.root_id:
            continue
        if not args.all and row["sha256"] not in requested:
            continue
        if not relative_ok(row["relative_path"]) or not row["root_id"].replace("_", "").isalnum():
            raise RuntimeError("UNSAFE_LOCATION")
        if os.name == "nt" and not windows_relative_ok(row["relative_path"]):
            raise RuntimeError("NATIVE_POSIX_RESTORE_REQUIRED_FOR_SOME_NAMES")
        locations[row["sha256"]].append(row)
    direct = {}
    for row in checkpoint.get("supplemental_locations", []):
        if row["storage"] not in ("metadata_zip_member", "existing_logical_content"):
            raise RuntimeError("UNSUPPORTED_STORAGE_KIND")
        if args.root_id and row["root_id"] not in args.root_id:
            continue
        if not args.all and row["sha256"] not in requested:
            continue
        if not relative_ok(row["relative_path"]) or (os.name == "nt" and not windows_relative_ok(row["relative_path"])):
            raise RuntimeError("SUPPLEMENTAL_PATH_INVALID")
        locations[row["sha256"]].append(row)
        if row["storage"] == "metadata_zip_member":
            direct[row["sha256"]] = row["member"]
    if not locations or (requested and not requested.issubset(locations)):
        raise RuntimeError("REQUESTED_EVIDENCE_NOT_FOUND")
    logical_bytes = sum(r["bytes"] for group in locations.values() for r in group)
    if shutil.disk_usage(parent).free < logical_bytes + 1024 * 1024 * 1024:
        raise RuntimeError("INSUFFICIENT_FREE_SPACE_NO_PAYLOAD_WRITES")
    if os.name == "nt":
        seen = {}
        for key, group in locations.items():
            for row in group:
                target = (row["root_id"] + "/" + row["relative_path"]).casefold()
                if target in seen and seen[target] != key:
                    raise RuntimeError("NATIVE_CASE_SENSITIVE_FILESYSTEM_REQUIRED")
                seen[target] = key
    destination.mkdir()
    (destination / "ROOT_CHECKPOINT.json").write_bytes(checkpoint_bytes)
    (destination / "PRIVATE_RECOVERY_PACKAGE.zip").write_bytes(package_bytes)
    targets, positions, hashes = {}, collections.defaultdict(int), {}
    for key, group in locations.items():
        primary = destination / "roots" / group[0]["root_id"] / group[0]["relative_path"]
        if not primary.resolve().is_relative_to(destination):
            raise RuntimeError("RESTORE_PATH_ESCAPE")
        primary.parent.mkdir(parents=True, exist_ok=True)
        with primary.open("xb"):
            pass
        targets[key], hashes[key] = primary, hashlib.sha256()
        if key in direct:
            data = package.read(direct[key])
            if len(data) != group[0]["bytes"] or hashlib.sha256(data).hexdigest() != key:
                raise RuntimeError("DIRECT_METADATA_MEMBER_SHA256_MISMATCH")
            with primary.open("ab") as output:
                output.write(data)
            hashes[key].update(data)
            positions[key] = len(data)
    pack_map = {p["pack_index"]: p for p in checkpoint["packs"]}
    for pack in json_rows(frozen, "manifest/PACK_PLAN.jsonl"):
        members = [m for m in pack["members"] if m["sha256"] in locations]
        if not members:
            continue
        record = pack_map[pack["index"]]
        data = reader.download(record["remote"]["fileId"], record["pack_sha256"])
        for member in members:
            key = member["sha256"]
            if positions[key] != member["file_offset"]:
                raise RuntimeError("FILE_FRAGMENT_GAP_OR_OVERLAP")
            part = memoryview(data)[member["pack_offset"]:member["pack_offset"] + member["bytes"]]
            with targets[key].open("ab") as handle:
                handle.write(part)
            hashes[key].update(part)
            positions[key] += len(part)
        print(json.dumps({"pack": pack["index"], "downloaded_bytes": reader.downloaded}), flush=True)
    restored_locations = 0
    for key, group in locations.items():
        if hashes[key].hexdigest() != key or positions[key] != group[0]["bytes"]:
            raise RuntimeError("FULL_RESTORED_FILE_SHA256_MISMATCH")
        for number, row in enumerate(group):
            target = destination / "roots" / row["root_id"] / row["relative_path"]
            if not target.resolve().is_relative_to(destination):
                raise RuntimeError("RESTORE_PATH_ESCAPE")
            if number:
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    raise RuntimeError("RESTORE_LOCATION_COLLISION")
                shutil.copyfile(targets[key], target)
                digest = hashlib.sha256()
                with target.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
                        digest.update(chunk)
                if digest.hexdigest() != key:
                    raise RuntimeError("DUPLICATE_LOCATION_COPY_SHA256_MISMATCH")
            if row.get("mtime_ns") is not None:
                os.utime(target, ns=(row["mtime_ns"], row["mtime_ns"]))
            if os.name != "nt" and row.get("mode") is not None:
                os.chmod(target, row["mode"])
            restored_locations += 1
    # Preserve directory/link reconstruction metadata as data, without following
    # absolute links into the original computer or overwriting app databases.
    for name in ("private/inventory_scope_windows.json", "private/inventory_scope_wsl.json",
                 "manifest/SQLITE_APPLICATION_RESTORE_MAP.json", "manifest/BACKUP_PENDING.json"):
        target = destination / "recovery_notes" / Path(name).name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(frozen.read(name))
    receipt = {"status": "SELECTED_AVAILABLE_BYTES_RESTORED_AND_SHA256_VERIFIED", "logical_objects": len(locations),
               "restored_locations": restored_locations, "logical_bytes": logical_bytes,
               "downloaded_bytes": reader.downloaded, "original_source_access": False,
               "sqlite_application_overlay": "REQUIRED_BEFORE_OPENING_OPERATIONAL_DATABASES",
               "pending_originals": "See recovery_notes/BACKUP_PENDING.json",
               "absolute_original_paths_restored_in_place": False}
    (destination / "RESTORE_RESULT.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root-file-id", required=True)
    parser.add_argument("--root-sha256", required=True)
    parser.add_argument("--destination", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--evidence-id", action="append")
    parser.add_argument("--root-id", action="append")
    parser.add_argument("--prompt-key", action="store_true")
    args = parser.parse_args()
    try:
        main(args)
    except Exception as exc:
        safe = str(exc) if isinstance(exc, RuntimeError) and re.fullmatch("[A-Z0-9_]+", str(exc)) else type(exc).__name__
        print(json.dumps({"status": "SAFE_STOP", "error_class": type(exc).__name__, "safe_error_code": safe}), flush=True)
        sys.exit(1)
