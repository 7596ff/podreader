"""Episode matching — resolve episode references by guid, title substring, or index."""


def resolve_episode(feed_state, reference, latest=False):
    """
    Resolve an episode reference against feed state.

    reference can be:
    - A guid (exact match)
    - A title substring (fuzzy match)
    - An integer index

    Returns the guid of the matched episode.
    Raises ValueError on no match or ambiguous match (unless latest=True).
    """
    raise NotImplementedError
