"""Tests for extractor loading, including user-defined plugins."""

import os
import tempfile
from podreader.extractors import load_extractors


def test_load_built_in_extractors():
    extractors = load_extractors()
    assert "npr" in extractors
    assert "democracynow" in extractors
    assert hasattr(extractors["npr"], "get_transcript_url")
    assert hasattr(extractors["npr"], "extract_transcript")


def test_load_user_extractor(tmp_path):
    plugin_dir = tmp_path / "extractors"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "mypodcast.py"
    plugin_file.write_text(
        'name = "mypodcast"\n'
        '\n'
        'def get_transcript_url(entry):\n'
        '    return "http://example.com/transcript"\n'
        '\n'
        'def extract_transcript(html):\n'
        '    return "extracted text"\n'
    )

    extractors = load_extractors(user_dir=str(plugin_dir))
    assert "mypodcast" in extractors
    assert extractors["mypodcast"].get_transcript_url(None) == "http://example.com/transcript"
    assert extractors["mypodcast"].extract_transcript("") == "extracted text"


def test_user_extractor_overrides_builtin(tmp_path):
    plugin_dir = tmp_path / "extractors"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "npr.py"
    plugin_file.write_text(
        'name = "npr"\n'
        '\n'
        'def get_transcript_url(entry):\n'
        '    return "http://custom-npr.com/transcript"\n'
        '\n'
        'def extract_transcript(html):\n'
        '    return "custom extraction"\n'
    )

    extractors = load_extractors(user_dir=str(plugin_dir))
    assert extractors["npr"].get_transcript_url(None) == "http://custom-npr.com/transcript"


def test_user_extractor_missing_name_skipped(tmp_path):
    plugin_dir = tmp_path / "extractors"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "broken.py"
    plugin_file.write_text(
        '# no name attribute\n'
        'def get_transcript_url(entry):\n'
        '    return None\n'
    )

    extractors = load_extractors(user_dir=str(plugin_dir))
    # Should not crash, just skip the broken plugin
    assert "broken" not in extractors


def test_user_extractor_dir_missing():
    extractors = load_extractors(user_dir="/nonexistent/path")
    # Should just return built-ins
    assert "npr" in extractors
    assert "democracynow" in extractors


def test_user_extractor_syntax_error_skipped(tmp_path):
    plugin_dir = tmp_path / "extractors"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "bad.py"
    plugin_file.write_text("def this is not valid python\n")

    extractors = load_extractors(user_dir=str(plugin_dir))
    # Should not crash
    assert "npr" in extractors
