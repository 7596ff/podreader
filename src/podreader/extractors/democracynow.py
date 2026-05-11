"""Democracy Now transcript extractor.

DN transcripts require multiple page fetches:
1. Show index page: https://www.democracynow.org/shows/YYYY/M/D
2. Extract segment URLs from the index page
3. Fetch each segment page for its transcript
4. Combine all segments into one transcript
"""

import re
import requests
from bs4 import BeautifulSoup

name = "democracynow"


def get_transcript_url(entry):
    """Return the show index URL from the RSS entry link.

    DN RSS links look like: https://www.democracynow.org/shows/2026/5/8
    We return this directly — extract_transcript handles the multi-page fetch.
    """
    link = getattr(entry, "link", "")
    if "democracynow.org" in link:
        return link
    return None


def extract_transcript(html):
    """Extract transcript from DN show index page.

    This fetches the index page, finds all segment links,
    fetches each segment, and combines the transcripts.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Find the show date from the page to construct segment URLs
    # Look for segment links: /YYYY/M/D/slug pattern
    segment_links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Match /YYYY/M/D/slug but not /shows/ or /full_show
        if re.match(r"/\d{4}/\d{1,2}/\d{1,2}/\w+", href) and "full_show" not in href:
            segment_links.add(href)

    if not segment_links:
        # Fallback: try to extract transcript from this page directly
        return _extract_page_transcript(soup)

    # Sort segments — headlines typically comes first
    sorted_links = sorted(segment_links, key=lambda x: (0 if "headlines" in x else 1, x))

    # Fetch each segment and combine
    parts = []
    for link in sorted_links:
        url = f"https://www.democracynow.org{link}"
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                seg_soup = BeautifulSoup(resp.text, "html.parser")
                title = _extract_segment_title(seg_soup)
                transcript = _extract_page_transcript(seg_soup)
                if transcript:
                    header = f"## {title}" if title else f"## {link.split('/')[-1]}"
                    parts.append(f"{header}\n\n{transcript}")
        except requests.RequestException:
            parts.append(f"## {link.split('/')[-1]}\n\n[Failed to fetch segment]")

    return "\n\n---\n\n".join(parts) if parts else "[No transcript segments found]"


def _extract_segment_title(soup):
    """Extract the segment title from a DN segment page."""
    # Try h1 or the story headline
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    return None


def _extract_page_transcript(soup):
    """Extract transcript text from a single DN page."""
    # DN structure: .transcript is a label, the actual text is in a sibling div.text
    transcript_label = soup.select_one(".transcript")
    if transcript_label:
        # Look for the sibling div with class "text"
        for sib in transcript_label.next_siblings:
            if hasattr(sib, "name") and sib.name == "div" and "text" in (sib.get("class") or []):
                text = sib.get_text(separator="\n", strip=True)
                if len(text) > 100:
                    return text

    # Also try direct .text selector in case of different page structure
    text_div = soup.select_one("div.text")
    if text_div:
        text = text_div.get_text(separator="\n", strip=True)
        if len(text) > 100:
            return text

    # Fallback: look for the main content area and extract paragraphs
    for selector in [".story_body", "article", ".main_container", "#content", "main"]:
        content = soup.select_one(selector)
        if content:
            paragraphs = content.find_all("p")
            text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            if len(text) > 100:
                return text

    # Last resort: all paragraphs
    paragraphs = soup.find_all("p")
    text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
    if len(text) > 100:
        return text

    return None
