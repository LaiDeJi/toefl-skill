#!/usr/bin/env python3
"""
Run-ownership guard for the exercise generators.

Every generator run records, per exercise type, which folders it produced and
the content hash of each item. The manifest is the ownership guard:

- A rerun overwrites only the folders the current selection produces;
  rewriting manifest-owned folders is intended behavior.
- Stale folders — produced by an earlier run's selection but not by the
  current one — are pruned only AFTER the new run finishes writing
  successfully. A fatal failure mid-run therefore never destroys old
  material; the next successful run prunes instead.
- Folders never recorded in a manifest are never touched.
- Each exercise type keeps its own manifest (listening re-runs several
  --type values into one output dir; a single shared manifest would make
  every rerun treat the other types as stale).
- Manifest entries key on a content hash, so the TTS generator can skip
  re-synthesis when nothing changed.
"""

import hashlib
import json
import os
import re
import shutil

MANIFEST_NAME = ".generation-manifest.json"


def typed_manifest_name(kind: str) -> str:
    """Manifest file name for a generator type that publishes folders
    directly into the output dir (no per-type subdirectory)."""
    return f".generation-manifest-{kind}.json"


def content_hash(item: dict) -> str:
    """Stable hash of an exercise item's content (key order does not matter)."""
    payload = json.dumps(item, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


_SAFE_NAME = re.compile(r"^[A-Za-z0-9._\-]+$")
_UNSAFE = {"", ".", ".."}


def _safe(name) -> bool:
    return isinstance(name, str) and name not in _UNSAFE and bool(_SAFE_NAME.match(name))


def _sanitize(entries) -> dict:
    """Keep only entries with safe folder names and well-formed values."""
    out = {}
    if not isinstance(entries, dict):
        return out
    for name, entry in entries.items():
        if not _safe(name) or not isinstance(entry, dict):
            continue
        files = entry.get("files")
        if isinstance(entry.get("hash"), str) and isinstance(files, list):
            out[name] = {"hash": entry["hash"], "files": [f for f in files if _safe(f)]}
    return out


def load_manifest(path: str, ex_type: str) -> dict:
    """Load a type manifest; a missing or corrupt file starts an empty one."""
    manifest = {"type": ex_type, "difficulty": [], "entries": {}}
    try:
        with open(path, encoding="utf-8") as fh:
            stored = json.load(fh)
    except FileNotFoundError:
        return manifest
    except (OSError, ValueError):
        print(f"⚠️  Manifest 档损毁或无法读取（{path}），本次执行会重建纪录")
        return manifest
    if isinstance(stored, dict) and stored.get("type") == ex_type:
        manifest["difficulty"] = stored.get("difficulty") if isinstance(stored.get("difficulty"), list) else []
        manifest["entries"] = _sanitize(stored.get("entries"))
    return manifest


def reusable(entry, folder_dir: str, item_hash: str) -> bool:
    """True when the manifest entry matches the item hash and every recorded
    output file still exists — the expensive synthesis can be skipped."""
    if not isinstance(entry, dict) or entry.get("hash") != item_hash:
        return False
    files = entry.get("files") or []
    if not files:  # never treat a run we recorded nothing for as reusable
        return False
    return all(os.path.exists(os.path.join(folder_dir, f)) for f in files)


def commit_manifest(path: str, ex_type: str, scope_dir: str, entries: dict, difficulty: list) -> list:
    """Prune folders recorded by previous runs but not produced by this run,
    then atomically replace the manifest. Never touches anything outside the
    manifest. Returns the pruned folder names."""
    if not isinstance(entries, dict) or not entries:
        raise ValueError("refusing to commit an empty run — old material would be pruned")

    old = load_manifest(path, ex_type)["entries"]
    pruned = []
    for name in old:
        if name in entries:
            continue
        target = os.path.join(scope_dir, name)
        if not os.path.isdir(target):
            pruned.append(name)
            continue
        try:
            shutil.rmtree(target)
            pruned.append(name)
        except OSError:
            print(f"⚠️  清除过期资料夹失败（接下来不会再管理它）：{target}")

    payload = {"type": ex_type, "difficulty": list(difficulty), "entries": entries}
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    return pruned
