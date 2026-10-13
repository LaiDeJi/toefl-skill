#!/usr/bin/env python3
"""
Regression tests for the generator run-ownership guard (issue #2).

Run with:  python3 -m unittest discover -s tests -v

No network calls: edge-tts is stubbed out with a module that raises if
synthesis is ever attempted, so the listening generator can be imported
safely and the TTS-skip path is provable offline.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from types import ModuleType

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "toefl" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import run_guard as rg          # noqa: E402
import generate_reading as gr   # noqa: E402

# Stub edge-tts BEFORE generate_listening is imported: synthesis must never
# happen in tests, and the real module exits(1) when the package is absent.
_stub = ModuleType("edge_tts")


class _FailSynthesis:
    def __init__(self, *args, **kwargs):
        pass

    async def save(self, path):
        raise AssertionError("edge-tts synthesis was invoked during tests")


_stub.Communicate = _FailSynthesis
sys.modules["edge_tts"] = _stub
import generate_listening as gl  # noqa: E402


def exercises_in(dirpath):
    """Top-level entries of dirpath, excluding hidden files (the manifest)."""
    return sorted(d for d in os.listdir(dirpath) if not d.startswith("."))


class ContentHash(unittest.TestCase):
    def test_stable(self):
        item = {"difficulty": 2, "passage": "same text"}
        self.assertEqual(rg.content_hash(item), rg.content_hash(dict(item)))

    def test_key_order_does_not_matter(self):
        self.assertEqual(
            rg.content_hash({"a": 1, "b": 2}),
            rg.content_hash({"b": 2, "a": 1}),
        )

    def test_different_content_hashes_differently(self):
        self.assertNotEqual(
            rg.content_hash({"difficulty": 2, "passage": "text"}),
            rg.content_hash({"difficulty": 3, "passage": "text"}),
        )


class ManifestBasics(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="rg-basics-")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_load_missing_starts_empty(self):
        path = os.path.join(self.dir, "m.json")
        manifest = rg.load_manifest(path, "complete-words")
        self.assertEqual(manifest["type"], "complete-words")
        self.assertEqual(manifest["entries"], {})

    def test_commit_roundtrip_persists_entries(self):
        path = os.path.join(self.dir, "m.json")
        entries = {"exercise-01": {"hash": "aa", "files": ["exercise.md"]}}
        rg.commit_manifest(path, "complete-words", self.dir, entries, [1])
        self.assertEqual(rg.load_manifest(path, "complete-words")["entries"], entries)

    def test_commit_refuses_empty_run(self):
        path = os.path.join(self.dir, "m.json")
        with self.assertRaises(ValueError):
            rg.commit_manifest(path, "complete-words", self.dir, {}, [1])

    def test_corrupt_or_unsafe_entries_are_dropped(self):
        path = os.path.join(self.dir, "m.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({
                "type": "complete-words",
                "entries": {
                    "../escape": {"hash": "1", "files": ["a.md"]},
                    "ok-folder": {"hash": "1", "files": ["a.md"]},
                    "bad": {"hash": 3, "files": []},
                },
            }, fh)
        manifest = rg.load_manifest(path, "complete-words")
        self.assertEqual(list(manifest["entries"]), ["ok-folder"])


class ReusableCheck(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="rg-reuse-")
        self.item_hash = rg.content_hash({"a": 1})

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_true_when_hash_and_files_match(self):
        with open(os.path.join(self.dir, "audio.mp3"), "wb") as fh:
            fh.write(b"audio")
        entry = {"hash": self.item_hash, "files": ["audio.mp3"]}
        self.assertTrue(rg.reusable(entry, self.dir, self.item_hash))

    def test_false_when_hash_differs(self):
        with open(os.path.join(self.dir, "audio.mp3"), "wb") as fh:
            fh.write(b"audio")
        entry = {"hash": "different", "files": ["audio.mp3"]}
        self.assertFalse(rg.reusable(entry, self.dir, self.item_hash))

    def test_false_when_recorded_files_missing(self):
        entry = {"hash": self.item_hash, "files": ["audio.mp3"]}
        self.assertFalse(rg.reusable(entry, self.dir, self.item_hash))

    def test_false_when_no_files_recorded(self):
        with open(os.path.join(self.dir, "audio.mp3"), "wb") as fh:
            fh.write(b"audio")
        entry = {"hash": self.item_hash, "files": []}
        self.assertFalse(rg.reusable(entry, self.dir, self.item_hash))


class StalePrune(unittest.TestCase):
    """Ownership guard: prune only manifest-tracked stale folders."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="rg-prune-")
        self.scope = os.path.join(self.dir, "out")
        os.makedirs(self.scope)
        for name in ("conversation-01", "conversation-02", "old-stale"):
            os.makedirs(os.path.join(self.scope, name))
        # An untracked folder a user may have created: must never be touched.
        untracked = os.path.join(self.scope, "untracked-notes")
        os.makedirs(untracked)
        with open(os.path.join(untracked, "note.txt"), "w") as fh:
            fh.write("keep me")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_stale_tracked_folder_pruned_others_untouched(self):
        path = os.path.join(self.scope, rg.typed_manifest_name("conversation"))
        old_entries = {
            "conversation-01": {"hash": "h1", "files": ["audio.mp3"]},
            "old-stale": {"hash": "h2", "files": ["audio.mp3"]},
        }
        # First run establishes ownership of conversation-01 and old-stale.
        rg.commit_manifest(path, "conversation", self.scope, old_entries, [2])
        # Second run no longer produces old-stale → it is pruned as stale.
        new_entries = {"conversation-01": {"hash": "h1", "files": ["audio.mp3"]}}
        pruned = rg.commit_manifest(path, "conversation", self.scope, new_entries, [3])
        self.assertEqual(pruned, ["old-stale"])

        self.assertFalse(os.path.exists(os.path.join(self.scope, "old-stale")))
        # Tracked but still produced → kept.
        self.assertTrue(os.path.isdir(os.path.join(self.scope, "conversation-01")))
        # On disk but never tracked → never touched.
        self.assertTrue(os.path.isdir(os.path.join(self.scope, "conversation-02")))
        self.assertTrue(os.path.isfile(os.path.join(self.scope, "untracked-notes", "note.txt")))
        # Manifest now records only this run's entries.
        self.assertEqual(list(rg.load_manifest(path, "conversation")["entries"]),
                         ["conversation-01"])

    def test_second_prune_is_idempotent(self):
        path = os.path.join(self.scope, rg.typed_manifest_name("conversation"))
        oe = {
            "conversation-01": {"hash": "h1", "files": ["audio.mp3"]},
            "old-stale": {"hash": "h2", "files": ["audio.mp3"]},
        }
        rg.commit_manifest(path, "conversation", self.scope, oe, [2])
        ne = {"conversation-01": {"hash": "h1", "files": ["audio.mp3"]}}
        first = rg.commit_manifest(path, "conversation", self.scope, ne, [3])
        second = rg.commit_manifest(path, "conversation", self.scope, ne, [3])
        self.assertEqual(first, ["old-stale"])
        self.assertEqual(second, [])


class ReadingRegression(unittest.TestCase):
    """End-to-end scenarios from issue #2 against generate_reading.py."""

    def setUp(self):
        self.out = tempfile.mkdtemp(prefix="rg-reading-")

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)

    def cw_dir(self):
        return os.path.join(self.out, "complete-words")

    def test_all_then_easy_no_stale_mix(self):
        base = self.out
        gr.generate_complete_words(gr.COMPLETE_WORDS_ITEMS, base, [1, 2, 3])
        gr.generate_complete_words(gr.COMPLETE_WORDS_ITEMS, base, [1])

        folders = exercises_in(self.cw_dir())
        self.assertEqual(folders, ["exercise-01"])  # fails on pre-fix code: 02/03 were left stale
        with open(os.path.join(self.cw_dir(), "exercise-01", "meta.json")) as fh:
            meta = json.load(fh)
        self.assertEqual(meta["difficulty"], 1)

    def test_alternating_tiers_consistent(self):
        base = self.out
        gr.generate_complete_words(gr.COMPLETE_WORDS_ITEMS, base, [1])
        gr.generate_complete_words(gr.COMPLETE_WORDS_ITEMS, base, [2])
        self.assertEqual(exercises_in(self.cw_dir()), ["exercise-01"])
        with open(os.path.join(self.cw_dir(), "exercise-01", "meta.json")) as fh:
            meta = json.load(fh)
        self.assertEqual(meta["difficulty"], 2)  # manifest-owned rewrite intended

    def test_empty_selection_never_damages_existing_material(self):
        base = self.out
        gr.generate_complete_words(gr.COMPLETE_WORDS_ITEMS, base, [1, 2, 3])
        before = exercises_in(self.cw_dir())

        gr.generate_academic_passages(gr.ACADEMIC_PASSAGES, base, [1])  # no easy items exist
        self.assertFalse(os.path.exists(os.path.join(base, "academic-passages")))

        gr.generate_complete_words(gr.COMPLETE_WORDS_ITEMS, base, [99])  # simulated empty filter
        self.assertEqual(exercises_in(self.cw_dir()), before)

    def test_untracked_folder_survives_rerun(self):
        base = self.out
        gr.generate_complete_words(gr.COMPLETE_WORDS_ITEMS, base, [1, 2, 3])
        untracked = os.path.join(self.cw_dir(), "my-notes")
        os.makedirs(untracked)
        with open(os.path.join(untracked, "thoughts.md"), "w") as fh:
            fh.write("keep me")

        gr.generate_complete_words(gr.COMPLETE_WORDS_ITEMS, base, [1])
        self.assertTrue(os.path.isfile(os.path.join(untracked, "thoughts.md")))
        self.assertEqual(exercises_in(self.cw_dir()), ["exercise-01", "my-notes"])

    def test_academic_site_uses_passage_prefix(self):
        base = self.out
        gr.generate_academic_passages(gr.ACADEMIC_PASSAGES, base, [2, 3])
        ap_dir = os.path.join(base, "academic-passages")
        self.assertEqual(exercises_in(ap_dir), ["passage-01", "passage-02"])

        gr.generate_academic_passages(gr.ACADEMIC_PASSAGES, base, [2])  # one hard item pruned
        self.assertEqual(exercises_in(ap_dir), ["passage-01"])


class ListeningReuse(unittest.TestCase):
    """--type conversation rerun reuses TTS audio and prunes stale folders,
    with synthesis hard-disabled by the edge-tts stub."""

    def setUp(self):
        self.base = os.path.join(tempfile.mkdtemp(prefix="rg-listening-"), "listening")
        os.makedirs(self.base)
        item = gl.CONVERSATIONS[0]  # difficulty 2
        folder = os.path.join(self.base, "conversation-01")
        os.makedirs(folder)
        with open(os.path.join(folder, "audio.mp3"), "wb") as fh:
            fh.write(b"previous synthesis")
        manifest = {
            "type": "conversation",
            "difficulty": [2],
            "entries": {
                "conversation-01": {
                    "hash": rg.content_hash(item),
                    "files": ["audio.mp3"],
                },
                "conversation-99": {  # stale folder left by an earlier run
                    "hash": "old",
                    "files": ["audio.mp3"],
                },
            },
        }
        stale = os.path.join(self.base, "conversation-99")
        os.makedirs(stale)
        with open(os.path.join(stale, "audio.mp3"), "wb") as fh:
            fh.write(b"old")
        with open(os.path.join(self.base, rg.typed_manifest_name("conversation")), "w", encoding="utf-8") as fh:
            json.dump(manifest, fh)

    def tearDown(self):
        shutil.rmtree(os.path.dirname(self.base), ignore_errors=True)

    def _run(self, **kw):
        import asyncio
        ns = Namespace(type="conversation", output=self.base, week=None, **kw)
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            asyncio.run(gl.generate_all(ns))
        return buf.getvalue()

    def test_unchanged_item_skips_synthesis(self):
        self._run(difficulty="medium")
        with open(os.path.join(self.base, "conversation-01", "audio.mp3"), "rb") as fh:
            self.assertEqual(fh.read(), b"previous synthesis")
        self.assertTrue(os.path.isfile(os.path.join(self.base, "conversation-01", "transcript.md")))
        self.assertTrue(os.path.isfile(os.path.join(self.base, "conversation-01", "meta.json")))
        meta = None
        with open(os.path.join(self.base, "conversation-01", "meta.json")) as fh:
            meta = json.load(fh)
        self.assertEqual(meta["difficulty"], 2)

    def test_stale_tracked_folder_pruned_by_rerun(self):
        self._run(difficulty="medium")
        self.assertFalse(os.path.exists(os.path.join(self.base, "conversation-99")))
        manifest = rg.load_manifest(
            os.path.join(self.base, rg.typed_manifest_name("conversation")), "conversation")
        self.assertEqual(list(manifest["entries"]), ["conversation-01"])

    def test_empty_selection_reports_and_changes_nothing(self):
        self._run(difficulty="easy")  # no easy conversations exist
        self.assertTrue(os.path.isdir(os.path.join(self.base, "conversation-99")))
        self.assertTrue(os.path.isfile(os.path.join(self.base, "conversation-01", "audio.mp3")))


if __name__ == "__main__":
    unittest.main()
