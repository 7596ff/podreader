"""Episode matching — resolve episode references by guid, title substring, or index."""


def resolve_episode(feed_state, reference, latest=False):
    """
    Resolve an episode reference against feed state.

    reference can be:
    - A guid (exact match)
    - A title substring (fuzzy match)
    - An integer index (or string that looks like one)

    Returns the guid of the matched episode.
    Raises ValueError on no match or ambiguous match (unless latest=True).
    """
    # Try exact guid match first
    if reference in feed_state:
        return reference

    # Try index (string that looks like an integer)
    try:
        idx = int(reference)
        sorted_guids = sorted(
            feed_state.keys(),
            key=lambda g: feed_state[g].get("pub_date", ""),
        )
        return sorted_guids[idx]
    except (ValueError, IndexError):
        if reference.lstrip("-").isdigit():
            raise ValueError(f"Index {reference} out of range (0-{len(feed_state) - 1})")

    # Title substring match (case-insensitive)
    ref_lower = reference.lower()
    matches = [
        guid for guid, ep in feed_state.items()
        if ref_lower in ep.get("title", "").lower()
    ]

    if len(matches) == 0:
        raise ValueError(f"No episode matching '{reference}'")

    if len(matches) == 1:
        return matches[0]

    # Ambiguous match
    if latest:
        return max(matches, key=lambda g: feed_state[g].get("pub_date", ""))

    match_list = "\n".join(
        f"  [{i}] {feed_state[g]['title']} ({feed_state[g].get('pub_date', '?')})"
        for i, g in enumerate(matches)
    )
    raise ValueError(f"Ambiguous match for '{reference}' ({len(matches)} results):\n{match_list}")
