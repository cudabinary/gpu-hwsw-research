"""Independent remote-only recovery checker. Python standard library only.

Does NOT import uploader/layout code or read original research paths. Launch in
a fresh Python -I process and an empty destination. Credentials are decrypted
from user-bound DPAPI only, never passed in arguments or written as plaintext.
"""
import argparse
import base64
import collections
import ctypes
from ctypes import wintypes
import hashlib
import getpass
import io
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile

BASE = Path(__file__).resolve().parent
BUCKET = "172529a471525cb5aa1e0f12"
PREFIX = "research-archive/"
CAPABILITIES = {"listBuckets", "readBucketEncryption", "listFiles", "readFiles", "writeFiles"}
MAX_RESTORE_BYTES = 768 * 1024 * 1024
MAX_SELECTED_PACKS = 256


def decrypt_key():
    class Blob(ctypes.Structure):
        _fields_ = [("length", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]
    protected = (BASE / "local_only/backup_key.dpapi").read_bytes()
    buf = (ctypes.c_ubyte * len(protected)).from_buffer_copy(protected)
    src, dst = Blob(len(protected), buf), Blob()
    crypto, kernel = ctypes.WinDLL("crypt32", use_last_error=True), ctypes.WinDLL("kernel32", use_last_error=True)
    crypto.CryptUnprotectData.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                          ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    kernel.LocalFree.argtypes, kernel.LocalFree.restype = [wintypes.HLOCAL], wintypes.HLOCAL
    if not crypto.CryptUnprotectData(ctypes.byref(src), None, None, None, None, 1, ctypes.byref(dst)):
        raise RuntimeError("DPAPI_DECRYPT_FAILED")
    try:
        return json.loads(ctypes.string_at(dst.data, dst.length))
    finally:
        kernel.LocalFree(ctypes.cast(dst.data, wintypes.HLOCAL))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise RuntimeError("REDIRECT_REFUSED")


def safe_url(url):
    parsed = urllib.parse.urlsplit(url)
    return (parsed.scheme == "https" and (parsed.hostname or "").endswith(".backblazeb2.com")
            and parsed.port in (None, 443) and parsed.username is None and parsed.password is None)


def relative_ok(value):
    return (isinstance(value, str) and bool(value) and "\x00" not in value and not PurePosixPath(value).is_absolute()
            and all(x not in ("", ".", "..") for x in value.split("/")))


def windows_relative_ok(value):
    if not relative_ok(value):
        return False
    reserved = {"CON", "PRN", "AUX", "NUL", *("COM" + str(i) for i in range(1, 10)), *("LPT" + str(i) for i in range(1, 10))}
    return all(not any(c in part for c in ':*?"<>|\\') and not part.endswith((" ", "."))
               and part.split(".")[0].upper() not in reserved for part in value.split("/"))


class Reader:
    def __init__(self, prompt_key=False):
        self.validation_transport = "LIVE_B2_API"
        self.opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=ssl.create_default_context()))
        key = ({"applicationKeyId": input("B2 restricted Key ID: ").strip(),
                "applicationKey": getpass.getpass("B2 restricted Application Key (hidden): ").strip()}
               if prompt_key else decrypt_key())
        basic = base64.b64encode((key["applicationKeyId"] + ":" + key["applicationKey"]).encode()).decode()
        req = urllib.request.Request("https://api.backblazeb2.com/b2api/v4/b2_authorize_account",
                                     headers={"Authorization": "Basic " + basic})
        with self.opener.open(req, timeout=40) as response:
            auth = json.load(response)
        key, basic = None, None
        storage = auth["apiInfo"]["storageApi"]
        allowed = storage["allowed"]
        granted = set(allowed["capabilities"])
        if (not {"listBuckets", "readBucketEncryption", "readFiles"}.issubset(granted)
                or not granted.issubset(CAPABILITIES) or allowed.get("namePrefix") != PREFIX
                or [b["id"] for b in (allowed.get("buckets") or [])] != [BUCKET]):
            raise RuntimeError("KEY_SCOPE_MISMATCH")
        self.api, self.download_url, self.token, self.account = storage["apiUrl"], storage["downloadUrl"], auth["authorizationToken"], auth["accountId"]
        if not safe_url(self.api) or not safe_url(self.download_url):
            raise RuntimeError("UNTRUSTED_ENDPOINT")
        bucket = self.api_json("b2_list_buckets", {"accountId": self.account, "bucketId": BUCKET})["buckets"]
        if len(bucket) != 1 or bucket[0]["bucketType"] != "allPrivate":
            raise RuntimeError("BUCKET_NOT_PRIVATE")
        encryption = bucket[0].get("defaultServerSideEncryption", {}).get("value") or {}
        if encryption.get("mode") != "SSE-B2":
            raise RuntimeError("ENCRYPTION_NOT_CONFIRMED")
        self.downloaded = 0

    def api_json(self, method, body):
        if method not in ("b2_list_buckets", "b2_get_file_info"):
            raise RuntimeError("READ_ONLY_API_ALLOWLIST")
        req = urllib.request.Request(self.api + "/b2api/v4/" + method, data=json.dumps(body).encode(),
            headers={"Authorization": self.token, "Content-Type": "application/json"})
        with self.opener.open(req, timeout=60) as response:
            return json.load(response)

    def download(self, file_id, expected_sha256):
        info = self.api_json("b2_get_file_info", {"fileId": file_id})
        name = info["fileName"]
        if not name.startswith(PREFIX) or info["bucketId"] != BUCKET:
            raise RuntimeError("REMOTE_OBJECT_SCOPE_MISMATCH")
        size = info["contentLength"]
        if size > 128 * 1024 * 1024:
            raise RuntimeError("BOUNDED_REMOTE_READ_SIZE_EXCEEDED")
        ledger_path = BASE / "TRANSFER_BUDGET.json"
        ledger = (json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists()
                  else {"download_reserved_bytes": 0, "download_max_bytes": 85_000_000_000})
        if ledger["download_reserved_bytes"] + size > 85_000_000_000:
            raise RuntimeError("APPROVED_DOWNLOAD_BUDGET_EXCEEDED")
        ledger["download_reserved_bytes"] += size
        ledger["download_max_bytes"] = 85_000_000_000
        temporary = ledger_path.with_suffix(".restore-derived-tmp")
        temporary.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
        os.replace(temporary, ledger_path)
        req = urllib.request.Request(self.download_url + "/b2api/v4/b2_download_file_by_id?" + urllib.parse.urlencode({"fileId": file_id}),
                                     headers={"Authorization": self.token})
        sha, sha1, data = hashlib.sha256(), hashlib.sha1(), bytearray()
        with self.opener.open(req, timeout=180) as response:
            while True:
                part = response.read(1024 * 1024)
                if not part:
                    break
                data.extend(part)
                sha.update(part)
                sha1.update(part)
                if len(data) > size:
                    raise RuntimeError("REMOTE_SIZE_EXCEEDED")
        if len(data) != size or sha.hexdigest() != expected_sha256 or sha1.hexdigest() != info["contentSha1"]:
            raise RuntimeError("REMOTE_SHA256_OR_SIZE_MISMATCH")
        self.downloaded += size
        return bytes(data)

    def unauthenticated_denied(self, file_id):
        req = urllib.request.Request(self.download_url + "/b2api/v4/b2_download_file_by_id?" + urllib.parse.urlencode({"fileId": file_id}), method="HEAD")
        try:
            with self.opener.open(req, timeout=30) as response:
                return False
        except urllib.error.HTTPError as exc:
            return exc.code in (401, 403)


def json_rows(package, name):
    with package.open(name) as handle:
        for line in io.TextIOWrapper(handle, encoding="utf-8"):
            if line.strip():
                yield json.loads(line)


def category(row):
    suffix = PurePosixPath(row["relative_path"]).suffix.lower()
    if row.get("role") in ("GIT_BUNDLE", "CONSISTENT_SQLITE_SNAPSHOT"):
        return row["role"]
    if suffix == ".zip":
        return "ZIP"
    if suffix in (".csv", ".tsv"):
        return "TABLE"
    if suffix in (".log", ".out", ".err"):
        return "LOG"
    if suffix in (".cu", ".cuh", ".cpp", ".hpp", ".c", ".h", ".py"):
        return "CODE"
    if suffix in (".md", ".txt"):
        return "REPORT"
    if suffix in (".nsys-rep", ".ncu-rep", ".qdrep"):
        return "PROFILER"
    return "OTHER"


def main(args):
    # Uploader and restore reader must never race the shared cost ledger.
    import msvcrt
    lock = (BASE / "local_only/archive_upload.lock").open("a+b")
    lock.seek(0)
    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    destination = Path(args.destination).resolve()
    if destination.exists() or not destination.is_relative_to(BASE):
        raise RuntimeError("DESTINATION_MUST_BE_NEW_AND_WITHIN_BACKUP_WORKSPACE")
    destination.mkdir(parents=True)
    reader = Reader()
    if reader.validation_transport == "LIVE_B2_API" and not sys.flags.isolated:
        raise RuntimeError("INDEPENDENT_CHECK_REQUIRES_PYTHON_ISOLATED_MODE")
    root_bytes = reader.download(args.root_file_id, args.root_sha256)
    checkpoint = json.loads(root_bytes)
    if checkpoint.get("schema_version") not in ("1.0.0", "1.1.0", "1.2.0"):
        raise RuntimeError("UNSUPPORTED_RECOVERY_SCHEMA")
    (destination / "ROOT_CHECKPOINT.json").write_bytes(root_bytes)
    if checkpoint["status"] not in ("ALL_CONTENT_REMOTE_VERIFIED_RESTORE_PENDING", "BACKED_UP_VERIFIED_AVAILABLE_VERSION_SET"):
        raise RuntimeError("CHECKPOINT_NOT_READY_FOR_RESTORE")
    metadata = checkpoint["private_metadata"]
    package_bytes = reader.download(metadata["file_id"], metadata["sha256"])
    (destination / "PRIVATE_RECOVERY_PACKAGE.zip").write_bytes(package_bytes)
    package = zipfile.ZipFile(io.BytesIO(package_bytes))
    frozen_bytes = package.read("PRIVATE_RECOVERY_MANIFEST_FROZEN.zip")
    frozen = zipfile.ZipFile(io.BytesIO(frozen_bytes))
    # Verify every recovered metadata member without extracting unknown paths.
    for archive in (package, frozen):
        pins = json.loads(archive.read("METADATA_SHA256.json"))
        for name, pin in pins.items():
            if not relative_ok(name):
                raise RuntimeError("METADATA_PATH_ESCAPE")
            content = archive.read(name)
            if len(content) != pin["bytes"] or hashlib.sha256(content).hexdigest() != pin["sha256"]:
                raise RuntimeError("METADATA_CONTENT_MISMATCH")
    git_boundaries = None
    if "git/GIT_SHALLOW_BOUNDARIES.json" in package.namelist():
        boundary_data = json.loads(package.read("git/GIT_SHALLOW_BOUNDARIES.json"))
        git_boundaries = {}
        for entry in boundary_data["bundles"]:
            prior = git_boundaries.setdefault(entry["bundle_sha256"], entry)
            if prior["shallow_commit_ids"] != entry["shallow_commit_ids"]:
                raise RuntimeError("CONFLICTING_SHALLOW_METADATA")
        helper = BASE / "restore_git_history.py"
        if hashlib.sha256(helper.read_bytes()).hexdigest() != hashlib.sha256(package.read("tools/restore_git_history.py")).hexdigest():
            raise RuntimeError("GIT_RESTORE_HELPER_REMOTE_PIN_MISMATCH")
        specification = importlib.util.spec_from_file_location("archive_git_history_restorer", helper)
        git_helper = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(git_helper)
    resume = None
    if getattr(args, "resume_from", None):
        resume = Path(args.resume_from).resolve()
        if not resume.is_relative_to(BASE) or resume == BASE or resume == destination:
            raise RuntimeError("INVALID_REMOTE_RESTORE_CACHE_SCOPE")
        previous = (resume / "ROOT_CHECKPOINT.json").read_bytes()
        if hashlib.sha256(previous).hexdigest() != checkpoint.get("previous_root_sha256"):
            raise RuntimeError("REMOTE_RESTORE_CACHE_CHECKPOINT_MISMATCH")
        previous_root = json.loads(previous)
        if hashlib.sha256((resume / "PRIVATE_RECOVERY_PACKAGE.zip").read_bytes()).hexdigest() != previous_root["private_metadata"]["sha256"]:
            raise RuntimeError("REMOTE_RESTORE_CACHE_METADATA_MISMATCH")
    packs = list(json_rows(frozen, "manifest/PACK_PLAN.jsonl"))
    objects = {x["sha256"]: x["bytes"] for x in json_rows(frozen, "manifest/UNIQUE_OBJECTS.jsonl")}
    coverage, groups, must_restore, locations = collections.defaultdict(int), {}, {}, 0
    windows_incompatible = 0
    for row in json_rows(frozen, "manifest/LOCATION_MANIFEST.jsonl"):
        locations += 1
        rid, rel, digest = row["root_id"], row["relative_path"], row["sha256"]
        if not re.fullmatch(r"[A-Z0-9_]+", rid) or not relative_ok(rel) or objects.get(digest) != row["bytes"]:
            raise RuntimeError("LOCATION_MANIFEST_INVALID")
        if not windows_relative_ok(rel):
            windows_incompatible += 1
            continue
        cat = category(row)
        if cat in ("GIT_BUNDLE", "CONSISTENT_SQLITE_SNAPSHOT"):
            must_restore[digest] = row
        elif 100 <= row["bytes"] <= (32 * 1024 * 1024 if cat == "ZIP" else 2 * 1024 * 1024):
            key = (rid, row.get("study_id") or rid, cat)
            if key not in groups or row["bytes"] < groups[key]["bytes"]:
                groups[key] = row
    for index, pack in enumerate(packs):
        if pack["index"] != index:
            raise RuntimeError("PACK_ORDER_INVALID")
        cursor = 0
        for member in pack["members"]:
            digest = member["sha256"]
            if member["pack_offset"] != cursor or member["file_offset"] != coverage[digest] or digest not in objects:
                raise RuntimeError("PACK_EXTENT_GAP_OR_OVERLAP")
            cursor += member["bytes"]
            coverage[digest] += member["bytes"]
        if cursor != pack["bytes"]:
            raise RuntimeError("PACK_BYTE_COVERAGE_MISMATCH")
    if any(coverage[key] != size for key, size in objects.items()):
        raise RuntimeError("LOGICAL_OBJECT_EXTENT_COVERAGE_MISMATCH")
    memberships = collections.defaultdict(set)
    for pack in packs:
        for member in pack["members"]:
            memberships[member["sha256"]].add(pack["index"])
    selected = dict(must_restore)
    selected_packs = set().union(*(memberships[key] for key in selected)) if selected else set()
    for row in sorted(groups.values(), key=lambda x: (x["bytes"], x["sha256"])):
        key = row["sha256"]
        proposal = selected_packs | memberships[key]
        if len(proposal) <= MAX_SELECTED_PACKS and sum(r["bytes"] for r in selected.values()) + row["bytes"] <= MAX_RESTORE_BYTES:
            selected[key] = row
            selected_packs = proposal
    pack_receipts = {p["pack_index"]: p for p in checkpoint["packs"]}
    positions, hashes, restored, targets = collections.defaultdict(int), {}, [], {}
    for key, row in selected.items():
        target = destination / "roots" / row["root_id"] / row["relative_path"]
        if not target.resolve().is_relative_to(destination):
            raise RuntimeError("RESTORE_PATH_ESCAPE")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb"):
            pass
        targets[key] = target
        hashes[key] = hashlib.sha256()
    if resume is not None:
        log = package.read("diagnostics/independent_restore_1.stdout.log").decode("utf-8")
        prior_downloads = [json.loads(line)["restore_pack"] for line in log.splitlines() if '"restore_pack"' in line]
        if prior_downloads != sorted(selected_packs):
            raise RuntimeError("PREVIOUS_REMOTE_DOWNLOAD_COVERAGE_MISMATCH")
        for key, row in selected.items():
            cached = resume / "roots" / row["root_id"] / row["relative_path"]
            if not cached.resolve().is_relative_to(resume):
                raise RuntimeError("REMOTE_RESTORE_CACHE_PATH_ESCAPE")
            with cached.open("rb") as source, targets[key].open("ab") as output:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    output.write(chunk)
                    hashes[key].update(chunk)
                    positions[key] += len(chunk)
            if positions[key] != row["bytes"] or hashes[key].hexdigest() != key:
                raise RuntimeError("PREVIOUSLY_REMOTE_RESTORED_FILE_SHA256_MISMATCH")
        probe = pack_receipts[min(selected_packs)]
        reader.download(probe["remote"]["fileId"], probe["pack_sha256"])
        print(json.dumps({"resumed_remote_origin_files_rehashed": len(selected), "previous_remote_pack_downloads": len(prior_downloads),
                          "fresh_live_remote_pack_downloads": 1, "original_research_file_reads": 0}), flush=True)
    for index in ([] if resume is not None else sorted(selected_packs)):
        record = pack_receipts[index]
        body = reader.download(record["remote"]["fileId"], record["pack_sha256"])
        pack = packs[index]
        for member in pack["members"]:
            key = member["sha256"]
            if key not in selected:
                continue
            if positions[key] != member["file_offset"]:
                raise RuntimeError("ACTUAL_RESTORE_OFFSET_GAP")
            part = memoryview(body)[member["pack_offset"]:member["pack_offset"] + member["bytes"]]
            with targets[key].open("ab") as output:
                output.write(part)
            hashes[key].update(part)
            positions[key] += len(part)
        print(json.dumps({"restore_pack": index, "selected_pack_count": len(selected_packs), "downloaded_bytes": reader.downloaded}), flush=True)
    for key, row in selected.items():
        target = targets[key]
        if positions[key] != row["bytes"] or hashes[key].hexdigest() != key:
            raise RuntimeError("ACTUAL_RESTORED_FILE_SHA256_MISMATCH")
        cat = category(row)
        detail = {"sha256": key, "bytes": row["bytes"], "root_id": row["root_id"],
                  "relative_path": row["relative_path"], "category": cat, "full_file_sha256": "PASS"}
        if cat == "CONSISTENT_SQLITE_SNAPSHOT":
            with sqlite3.connect(target.as_uri() + "?mode=ro", uri=True) as database:
                if database.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                    raise RuntimeError("RESTORED_SQLITE_INTEGRITY_FAILED")
            detail["sqlite_integrity_check"] = "PASS"
        if cat == "ZIP":
            try:
                with zipfile.ZipFile(target) as original_zip:
                    declared = sum(i.file_size for i in original_zip.infolist())
                    if declared > 256 * 1024 * 1024:
                        detail["zip_crc"] = "NOT_RUN_DECLARED_SIZE_BOUND"
                    else:
                        detail["zip_crc"] = "PASS" if original_zip.testzip() is None else "ORIGINAL_ZIP_CRC_ERROR_BYTES_PRESERVED"
            except zipfile.BadZipFile:
                detail["zip_crc"] = "ORIGINAL_ZIP_FORMAT_ERROR_BYTES_PRESERVED"
        if cat == "GIT_BUNDLE" and git_boundaries is not None:
            if key not in git_boundaries:
                raise RuntimeError("GIT_BOUNDARY_METADATA_INCOMPLETE")
            git = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe"
            bare = destination / "restored_git" / (key[:16] + ".git")
            detail.update(git_helper.restore_bundle(git, target, bare, git_boundaries[key]["shallow_commit_ids"], key))
        if cat == "GIT_BUNDLE" and git_boundaries is None:
            git = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe"
            bare = destination / "restored_git" / (key + ".git")
            bare.parent.mkdir(exist_ok=True)
            env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
            clone = subprocess.run([str(git), "clone", "--bare", str(target), str(bare)],
                                   capture_output=True, env=env, timeout=120)
            check = subprocess.run([str(git), "-C", str(bare), "fsck", "--full"],
                                   capture_output=True, env=env, timeout=120) if clone.returncode == 0 else None
            if clone.returncode or check is None or check.returncode:
                raise RuntimeError("RESTORED_GIT_HISTORY_CHECK_FAILED")
            detail["git_clone_and_fsck"] = "PASS"
            heads = subprocess.run([str(git), "bundle", "list-heads", str(target)], capture_output=True, env=env, timeout=30)
            identifiers = [line.split()[0] for line in heads.stdout.decode("ascii").splitlines() if line.strip()]
            objects_check = subprocess.run([str(git), "-C", str(bare), "cat-file", "--batch-check"],
                input=("\n".join(identifiers) + "\n").encode("ascii"), capture_output=True, env=env, timeout=30)
            if heads.returncode or objects_check.returncode or b" missing" in objects_check.stdout:
                raise RuntimeError("RESTORED_GIT_REFERENCE_OBJECT_MISSING")
            detail["git_bundle_reference_objects"] = "PASS"
        restored.append(detail)
    supplemental_new_objects = 0
    for supplement in checkpoint.get("supplemental_locations", []):
        if supplement["storage"] not in ("metadata_zip_member", "existing_logical_content"):
            raise RuntimeError("UNSUPPORTED_SUPPLEMENTAL_STORAGE_KIND")
        if supplement["storage"] != "metadata_zip_member":
            continue
        data = package.read(supplement["member"])
        if len(data) != supplement["bytes"] or hashlib.sha256(data).hexdigest() != supplement["sha256"]:
            raise RuntimeError("SUPPLEMENTAL_STATE_HASH_MISMATCH")
        json.loads(data.decode("utf-8-sig"))
        if not windows_relative_ok(supplement["relative_path"]):
            raise RuntimeError("SUPPLEMENTAL_STATE_PATH_INVALID")
        target = destination / "roots" / supplement["root_id"] / supplement["relative_path"]
        if not target.resolve().is_relative_to(destination):
            raise RuntimeError("SUPPLEMENTAL_STATE_PATH_ESCAPE")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as output:
            output.write(data)
        restored.append({"sha256": supplement["sha256"], "bytes": len(data), "root_id": supplement["root_id"],
                         "relative_path": supplement["relative_path"], "category": supplement.get("role", "LIVE_JSON_STATE_SNAPSHOT"),
                         "full_file_sha256": "PASS", "json_parse": "PASS", "cross_file_atomicity": "NOT_PROVEN"})
        supplemental_new_objects += 1
    if not reader.unauthenticated_denied(checkpoint["packs"][0]["remote"]["fileId"]):
        raise RuntimeError("UNAUTHENTICATED_READ_WAS_NOT_DENIED")
    live = reader.validation_transport == "LIVE_B2_API"
    receipt = {"status": "INDEPENDENT_REMOTE_ONLY_RESTORE_PASS" if live else "OFFLINE_FIXTURE_RESTORE_PASS",
               "validation_transport": reader.validation_transport, "python_isolated_mode": bool(sys.flags.isolated),
               "environment": ("fresh Python -I process, new empty output, prior LIVE B2 downloads reused after complete cached-file SHA256 recheck, same physical PC" if resume is not None else "fresh Python -I process, empty directory, same physical PC") if live else "OFFLINE UNIT TEST FIXTURE",
               "root_checkpoint_sha256": args.root_sha256, "private_metadata_sha256": metadata["sha256"],
               "original_research_file_reads": 0, "uploader_code_imports": 0, "manifest_locations_validated": locations,
               "logical_extent_maps_validated": len(objects), "physical_files_restored": len(restored),
               "supplemental_metadata_member_objects_validated": supplemental_new_objects,
               "physical_restored_bytes": sum(r["bytes"] for r in restored), "packs_downloaded": 1 if resume is not None else len(selected_packs),
               "previous_remote_pack_downloads_reused": len(selected_packs) if resume is not None else 0,
               "prior_failed_restore_attempt_retained": resume is not None,
               "downloaded_bytes": reader.downloaded, "windows_incompatible_paths_require_native_posix": windows_incompatible,
               "all_files_physically_restored": False, "different_physical_computer_test": "NOT_PERFORMED",
               "independent_second_backup_fault_domain": "NOT_CREATED", "private_access_unauthenticated_denied": True,
               "restored": restored}
    (destination / "RESTORE_RECEIPT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    (BASE / "INDEPENDENT_RESTORE_RECEIPT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    lock.close()
    print(json.dumps({k: v for k, v in receipt.items() if k != "restored"}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root-file-id", required=True)
    parser.add_argument("--root-sha256", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--resume-from", help="Previous remote-only download directory; every reused file is rehashed")
    options = parser.parse_args()
    try:
        main(options)
    except Exception as exc:
        safe = str(exc) if isinstance(exc, RuntimeError) and re.fullmatch("[A-Z0-9_]+", str(exc)) else type(exc).__name__
        print(json.dumps({"status": "RESTORE_SAFE_STOP", "error_class": type(exc).__name__, "safe_error_code": safe}), flush=True)
        sys.exit(1)
