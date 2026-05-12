"""CLI argument parsing and command dispatch."""

import argparse
import json
import os
import sys

from podreader.config import load_config, save_config, add_feed, remove_feed, get_extractor_name
from podreader.state import load_state, save_state, guid_or_fallback, slugify, transition_status
from podreader.feeds import fetch_feed, new_episodes
from podreader.transcripts import resolve_transcript
from podreader.matching import resolve_episode
from podreader.extractors import load_extractors

DATA_DIR = os.path.expanduser("~/.podreader")
CONFIG_PATH = os.path.join(DATA_DIR, "config.toml")
STATE_PATH = os.path.join(DATA_DIR, "state.json")


def main():
    parser = argparse.ArgumentParser(prog="podreader", description="Podcast reader for AI agents")
    sub = parser.add_subparsers(dest="command")

    # add
    p_add = sub.add_parser("add", help="Subscribe to a feed")
    p_add.add_argument("url", help="RSS feed URL")
    p_add.add_argument("--name", help="Feed name (auto-derived if not given)")
    p_add.add_argument("--extractor", help="Extractor plugin name")

    # remove
    p_remove = sub.add_parser("remove", help="Unsubscribe from a feed")
    p_remove.add_argument("feed", help="Feed name")
    p_remove.add_argument("--keep-data", action="store_true", help="Keep transcripts and state")

    # list
    sub.add_parser("list", help="List all feeds and episode counts")

    # fetch
    p_fetch = sub.add_parser("fetch", help="Fetch new episodes")
    p_fetch.add_argument("feed", help="Feed name")
    p_fetch.add_argument("--last", type=int, default=None, help="Only fetch last N episodes")
    p_fetch.add_argument("--process", action="store_true", help="Process fetched episodes immediately")

    # process
    p_proc = sub.add_parser("process", help="Get transcript for an episode")
    p_proc.add_argument("feed", help="Feed name")
    p_proc.add_argument("episode", nargs="?", default=None, help="Episode reference (guid, title substring, or index). Omit to process all unprocessed.")
    p_proc.add_argument("--latest", action="store_true", help="Pick most recent on ambiguous match")

    # read
    p_read = sub.add_parser("read", help="Output transcript to stdout")
    p_read.add_argument("feed", help="Feed name")
    p_read.add_argument("episode", help="Episode reference")
    p_read.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    p_read.add_argument("--latest", action="store_true", help="Pick most recent on ambiguous match")

    # mark
    p_mark = sub.add_parser("mark", help="Mark episode as processed")
    p_mark.add_argument("feed", help="Feed name")
    p_mark.add_argument("episode", help="Episode reference")
    p_mark.add_argument("--latest", action="store_true", help="Pick most recent on ambiguous match")

    # status
    p_status = sub.add_parser("status", help="Show unprocessed episodes")
    p_status.add_argument("feed", nargs="?", help="Filter by feed")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    os.makedirs(DATA_DIR, exist_ok=True)

    try:
        if args.command == "add":
            cmd_add(args)
        elif args.command == "remove":
            cmd_remove(args)
        elif args.command == "list":
            cmd_list(args)
        elif args.command == "fetch":
            cmd_fetch(args)
        elif args.command == "process":
            cmd_process(args)
        elif args.command == "read":
            cmd_read(args)
        elif args.command == "mark":
            cmd_mark(args)
        elif args.command == "status":
            cmd_status(args)
    except (ValueError, KeyError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_add(args):
    config = load_config(CONFIG_PATH)
    # Auto-derive name from feed title if not given
    if args.name:
        name = args.name
    else:
        feed = fetch_feed(args.url)
        title = feed.feed.get("title", args.url)
        name = title.lower().replace(" ", "-").replace("!", "").replace("'", "")[:40]
    config = add_feed(config, name, args.url, extractor=args.extractor)
    save_config(config, CONFIG_PATH)
    print(f"Added feed: {name}")


def cmd_remove(args):
    """Unsubscribe from a feed. Removes config entry, state, and transcripts."""
    config_path = os.path.join(DATA_DIR, "config.toml")
    config = load_config(config_path)
    config = remove_feed(config, args.feed)
    save_config(config, config_path)

    if not args.keep_data:
        # Remove state for this feed
        state_path = os.path.join(DATA_DIR, "state.json")
        state = load_state(state_path)
        if args.feed in state:
            del state[args.feed]
            save_state(state, state_path)

        # Remove transcripts directory
        import shutil
        transcript_dir = os.path.join(DATA_DIR, "transcripts", args.feed)
        if os.path.isdir(transcript_dir):
            shutil.rmtree(transcript_dir)

        # Remove cache directory
        cache_dir = os.path.join(DATA_DIR, "cache", args.feed)
        if os.path.isdir(cache_dir):
            shutil.rmtree(cache_dir)

    print(f"Removed feed '{args.feed}'")


def cmd_list(args):
    config = load_config(CONFIG_PATH)
    state = load_state(STATE_PATH)

    if not config["feeds"]:
        print("No feeds subscribed.")
        return

    for name, feed_conf in config["feeds"].items():
        feed_state = state.get(name, {})
        counts = {}
        for ep in feed_state.values():
            s = ep.get("status", "unknown")
            counts[s] = counts.get(s, 0) + 1
        total = len(feed_state)
        parts = [f"{v} {k}" for k, v in sorted(counts.items())]
        summary = ", ".join(parts) if parts else "no episodes"
        extractor = feed_conf.get("extractor", "whisper")
        print(f"  {name} [{extractor}] — {total} episodes ({summary})")


def cmd_fetch(args):
    config = load_config(CONFIG_PATH)
    state = load_state(STATE_PATH)

    if args.feed not in config["feeds"]:
        raise KeyError(f"Feed '{args.feed}' not found. Run 'podreader list' to see feeds.")

    feed_conf = config["feeds"][args.feed]
    feed = fetch_feed(feed_conf["url"])
    feed_state = state.get(args.feed, {})

    episodes = new_episodes(feed, feed_state)
    if args.last:
        episodes = episodes[:args.last]

    if not episodes:
        print(f"{args.feed}: no new episodes")
        return

    if args.feed not in state:
        state[args.feed] = {}

    extractors = load_extractors()

    for entry in episodes:
        guid = guid_or_fallback(entry)
        pub_date = _parse_pub_date(entry)
        state[args.feed][guid] = {
            "title": entry.title,
            "status": "unprocessed",
            "pub_date": pub_date,
            "audio_url": _get_audio_url(entry),
        }
        print(f"  {entry.title} [new]")

        if args.process:
            try:
                _process_episode(entry, args.feed, feed_conf, extractors, state, guid)
            except ValueError as e:
                if "skip" in str(e).lower():
                    state[args.feed][guid]["status"] = "skipped"
                    print(f"    → skipped (no audio/extractor)")
                else:
                    state[args.feed][guid]["status"] = "failed"
                    print(f"    → failed: {e}")
            except Exception as e:
                state[args.feed][guid]["status"] = "failed"
                print(f"    → failed: {e}")

            # Incremental persistence
            save_state(state, STATE_PATH)

    if not args.process:
        save_state(state, STATE_PATH)

    print(f"{args.feed}: {len(episodes)} new episodes")


def cmd_process(args):
    config = load_config(CONFIG_PATH)
    state = load_state(STATE_PATH)

    if args.feed not in config["feeds"]:
        raise KeyError(f"Feed '{args.feed}' not found")

    feed_conf = config["feeds"][args.feed]
    feed_state = state.get(args.feed, {})
    extractors = load_extractors()

    # If no episode specified, process all unprocessed/failed episodes
    if args.episode is None:
        guids_to_process = [
            guid for guid, ep in feed_state.items()
            if ep.get("status") in ("unprocessed", "failed")
        ]
        if not guids_to_process:
            print(f"{args.feed}: nothing to process")
            return

        # Fetch feed once for all episodes
        feed = fetch_feed(feed_conf["url"])
        print(f"{args.feed}: processing {len(guids_to_process)} episodes")

        for guid in guids_to_process:
            ep = feed_state[guid]
            print(f"  {ep['title']}...")
            entry = None
            for e in feed.entries:
                if guid_or_fallback(e) == guid:
                    entry = e
                    break

            if entry is None:
                print(f"    → skipped (not in current feed XML)")
                state[args.feed][guid]["status"] = "skipped"
                save_state(state, STATE_PATH)
                continue

            try:
                _process_episode(entry, args.feed, feed_conf, extractors, state, guid)
            except ValueError as e:
                if "skip" in str(e).lower():
                    state[args.feed][guid]["status"] = "skipped"
                    print(f"    → skipped (no audio/extractor)")
                else:
                    state[args.feed][guid]["status"] = "failed"
                    print(f"    → failed: {e}")
            except Exception as e:
                state[args.feed][guid]["status"] = "failed"
                print(f"    → failed: {e}")

            # Incremental persistence
            save_state(state, STATE_PATH)

        return

    # Single episode mode
    guid = resolve_episode(feed_state, args.episode, latest=args.latest)
    ep = feed_state[guid]

    if ep["status"] not in ("unprocessed", "failed"):
        print(f"Episode already {ep['status']}: {ep['title']}")
        return

    # Re-fetch the feed to get the feedparser entry
    feed = fetch_feed(feed_conf["url"])
    entry = None
    for e in feed.entries:
        if guid_or_fallback(e) == guid:
            entry = e
            break

    if entry is None:
        raise ValueError(f"Episode {guid} not found in current feed XML")

    try:
        _process_episode(entry, args.feed, feed_conf, extractors, state, guid)
    except ValueError as e:
        if "skip" in str(e).lower():
            state[args.feed][guid]["status"] = "skipped"
            print(f"Skipped: {e}")
        else:
            state[args.feed][guid]["status"] = "failed"
            print(f"Failed: {e}")
    except Exception as e:
        state[args.feed][guid]["status"] = "failed"
        print(f"Failed: {e}")

    save_state(state, STATE_PATH)


def _process_episode(entry, feed_name, feed_conf, extractors, state, guid):
    """Process a single episode — resolve transcript and update state."""
    # Check ffmpeg before whisper path
    extractor_name = feed_conf.get("extractor")
    if not extractor_name:
        import shutil
        if not shutil.which("ffmpeg"):
            raise RuntimeError("ffmpeg not found — required for whisper transcription")

    text, path = resolve_transcript(entry, feed_name, feed_conf, extractors, DATA_DIR)
    state[feed_name][guid]["status"] = "transcript-fetched"
    state[feed_name][guid]["transcript_path"] = path
    print(f"    → transcript saved: {path}")


def cmd_read(args):
    config = load_config(CONFIG_PATH)
    state = load_state(STATE_PATH)

    if args.feed not in state:
        raise KeyError(f"No episodes for feed '{args.feed}'")

    feed_state = state[args.feed]
    guid = resolve_episode(feed_state, args.episode, latest=args.latest)
    ep = feed_state[guid]

    path = ep.get("transcript_path")
    if not path:
        raise ValueError(f"No transcript for '{ep['title']}'. Run 'podreader process' first.")

    # Resolve relative to data dir if not absolute
    if not os.path.isabs(path):
        path = os.path.join(DATA_DIR, path)

    if not os.path.exists(path):
        raise ValueError(f"Transcript file not found: {path}")

    with open(path, "r") as f:
        text = f.read()

    if args.format == "json":
        output = {
            "title": ep.get("title"),
            "pub_date": ep.get("pub_date"),
            "feed": args.feed,
            "audio_url": ep.get("audio_url"),
            "transcript": text,
        }
        print(json.dumps(output, indent=2))
    else:
        print(text)


def cmd_mark(args):
    config = load_config(CONFIG_PATH)
    state = load_state(STATE_PATH)

    if args.feed not in state:
        raise KeyError(f"No episodes for feed '{args.feed}'")

    feed_state = state[args.feed]
    guid = resolve_episode(feed_state, args.episode, latest=args.latest)
    ep = feed_state[guid]

    old_status = ep["status"]
    ep["status"] = transition_status(old_status, "processed")
    save_state(state, STATE_PATH)
    print(f"Marked as processed: {ep['title']}")


def cmd_status(args):
    state = load_state(STATE_PATH)

    if not state:
        print("No episodes tracked.")
        return

    feeds = [args.feed] if args.feed else list(state.keys())

    for feed_name in feeds:
        if feed_name not in state:
            print(f"  {feed_name}: no episodes")
            continue
        feed_state = state[feed_name]
        actionable = [
            (guid, ep) for guid, ep in feed_state.items()
            if ep.get("status") in ("unprocessed", "failed")
        ]
        if not actionable:
            done = len(feed_state)
            print(f"  {feed_name}: all done ({done} episodes)")
        else:
            for guid, ep in actionable:
                status = ep["status"]
                print(f"  {feed_name}: [{status}] {ep['title']}")


def _parse_pub_date(entry):
    """Extract a clean YYYY-MM-DD date from a feedparser entry."""
    # feedparser parses dates into published_parsed (time.struct_time)
    pp = getattr(entry, "published_parsed", None)
    if pp:
        return f"{pp.tm_year}-{pp.tm_mon:02d}-{pp.tm_mday:02d}"
    # Fallback: try to extract from raw published string
    raw = getattr(entry, "published", "")
    if raw:
        return raw[:10]
    return "unknown"


def _get_audio_url(entry):
    """Extract audio URL from a feedparser entry."""
    enclosures = getattr(entry, "enclosures", [])
    if enclosures:
        enc = enclosures[0]
        return enc.get("href") if isinstance(enc, dict) else getattr(enc, "href", None)
    return None
