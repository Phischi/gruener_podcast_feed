from __future__ import annotations

from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree

from ..config import PodcastConfig
from ..models import Episode


def _rfc2822(value: str) -> str:
    normalized = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return format_datetime(dt)


def write_feed(config: PodcastConfig, episodes: list[Episode], output_path: Path) -> None:
    rss = Element(
        "rss",
        attrib={
            "version": "2.0",
            "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
        },
    )
    channel = SubElement(rss, "channel")

    SubElement(channel, "title").text = config.name
    SubElement(channel, "link").text = config.site_url
    SubElement(channel, "description").text = config.description
    SubElement(channel, "language").text = config.language
    SubElement(channel, "itunes:author").text = config.author
    SubElement(channel, "itunes:summary").text = config.description
    SubElement(channel, "itunes:category", attrib={"text": config.category})
    SubElement(channel, "itunes:explicit").text = "true" if config.explicit else "false"
    if config.image_url:
        SubElement(channel, "itunes:image", attrib={"href": config.image_url})
    if config.owner_email:
        SubElement(channel, "managingEditor").text = config.owner_email
        owner = SubElement(channel, "itunes:owner")
        SubElement(owner, "itunes:email").text = config.owner_email

    for episode in episodes:
        item = SubElement(channel, "item")
        SubElement(item, "title").text = episode.title
        SubElement(item, "guid").text = episode.rss_item_url or f"{config.base_url}/episodes/{episode.slug}"
        SubElement(item, "link").text = episode.rss_item_url or config.site_url
        SubElement(item, "description").text = episode.summary
        SubElement(item, "pubDate").text = _rfc2822(episode.generated_at)
        SubElement(item, "itunes:author").text = config.author
        SubElement(item, "itunes:summary").text = episode.summary
        SubElement(item, "itunes:explicit").text = "true" if config.explicit else "false"
        if episode.audio_url:
            enclosure = SubElement(item, "enclosure")
            enclosure.set("url", episode.audio_url)
            enclosure.set("type", "audio/mpeg")
            enclosure.set("length", "0")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ElementTree(rss).write(output_path, encoding="utf-8", xml_declaration=True)
