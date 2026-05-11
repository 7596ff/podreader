"""NPR transcript extractor."""

from bs4 import BeautifulSoup

name = "npr"


def get_transcript_url(entry):
    """Extract transcript URL from NPR episode link.

    NPR links look like: https://www.npr.org/2026/05/08/nx-s1-5815284/title-slug
    Transcript lives at: https://www.npr.org/transcripts/{slug}
    """
    link = getattr(entry, "link", "")
    parts = link.rstrip("/").split("/")
    # Find the slug — it's the part that starts with "nx-" or is after the date
    for part in parts:
        if part.startswith("nx-"):
            return f"https://www.npr.org/transcripts/{part}"
    # Fallback: try the 5th path segment (after domain/year/month/day)
    if len(parts) >= 5:
        slug = parts[4]
        return f"https://www.npr.org/transcripts/{slug}"
    return None


def extract_transcript(html):
    """Extract transcript text from NPR transcript page.

    NPR transcript pages use minimal semantic HTML — paragraphs with
    speaker labels in plain text. No special transcript wrapper class.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove script, style, nav, header, footer elements
    for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    # Try to find the main content area
    main = soup.select_one("#mainContent") or soup.select_one("article") or soup.select_one("main")
    if main:
        paragraphs = main.find_all("p")
        if paragraphs:
            return "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

    # Broader fallback: all paragraphs in body
    paragraphs = soup.find_all("p")
    if paragraphs:
        return "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

    return soup.get_text(separator="\n", strip=True)
