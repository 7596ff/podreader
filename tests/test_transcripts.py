import pytest
from unittest.mock import MagicMock, patch
from podreader.transcripts import resolve_transcript


def make_entry(title="Test Episode", link="https://example.com/ep1",
               audio_url="https://example.com/ep1.mp3", has_enclosure=True):
    entry = MagicMock()
    entry.title = title
    entry.link = link
    if has_enclosure:
        entry.enclosures = [{"href": audio_url, "type": "audio/mpeg"}]
    else:
        entry.enclosures = []
    return entry


def make_extractor(url="https://example.com/transcript", text="Transcript text here."):
    extractor = MagicMock()
    extractor.get_transcript_url = MagicMock(return_value=url)
    extractor.extract_transcript = MagicMock(return_value=text)
    return extractor


class TestFallbackChain:
    def test_extractor_succeeds(self, tmp_path):
        entry = make_entry()
        extractor = make_extractor()
        extractors = {"test-extractor": extractor}
        feed_config = {"extractor": "test-extractor"}

        text, path = resolve_transcript(
            entry, "test-feed", feed_config, extractors, str(tmp_path)
        )
        assert text == "Transcript text here."
        assert path is not None
        extractor.get_transcript_url.assert_called_once_with(entry)
        extractor.extract_transcript.assert_called_once()

    def test_extractor_returns_none_falls_back_to_whisper(self, tmp_path):
        entry = make_entry()
        extractor = make_extractor()
        extractor.get_transcript_url.return_value = None
        extractors = {"test-extractor": extractor}
        feed_config = {"extractor": "test-extractor"}

        with patch("podreader.transcripts.run_whisper", return_value="Whisper output") as mock_whisper:
            with patch("podreader.transcripts.download_audio", return_value=str(tmp_path / "audio.mp3")):
                text, path = resolve_transcript(
                    entry, "test-feed", feed_config, extractors, str(tmp_path)
                )
        assert text == "Whisper output"
        mock_whisper.assert_called_once()

    def test_no_extractor_uses_whisper(self, tmp_path):
        entry = make_entry()
        extractors = {}
        feed_config = {}  # no extractor field

        with patch("podreader.transcripts.run_whisper", return_value="Whisper output") as mock_whisper:
            with patch("podreader.transcripts.download_audio", return_value=str(tmp_path / "audio.mp3")):
                text, path = resolve_transcript(
                    entry, "test-feed", feed_config, extractors, str(tmp_path)
                )
        assert text == "Whisper output"

    def test_whisper_fails_raises(self, tmp_path):
        entry = make_entry()
        extractors = {}
        feed_config = {}

        with patch("podreader.transcripts.run_whisper", side_effect=RuntimeError("Whisper crashed")):
            with patch("podreader.transcripts.download_audio", return_value=str(tmp_path / "audio.mp3")):
                with pytest.raises(RuntimeError, match="Whisper crashed"):
                    resolve_transcript(
                        entry, "test-feed", feed_config, extractors, str(tmp_path)
                    )

    def test_no_enclosure_no_extractor_raises_skip(self, tmp_path):
        entry = make_entry(has_enclosure=False)
        extractors = {}
        feed_config = {}

        with pytest.raises(ValueError, match="[Ss]kip"):
            resolve_transcript(
                entry, "test-feed", feed_config, extractors, str(tmp_path)
            )
