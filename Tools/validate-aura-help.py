#!/usr/bin/env python3
"""Validate the public Ask Aura product-help feed without app dependencies.

The app performs the authoritative validation again before downloaded text can
become evidence. This site-side gate catches malformed, stale, oversized, or
off-domain content before GitHub Pages publishes it.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / "apps" / "AzureMastery" / "aura-help.json"
BYTE_LIMIT = 128_000
ARTICLE_LIMIT = 100
ALLOWED_HOSTS = {"azuremastery.app", "moonbeamalpha.github.io"}
ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{1,80}$")


def fail(message: str) -> None:
    raise ValueError(message)


def parse_version(value: object, field: str) -> tuple[int, int, int]:
    if not isinstance(value, str) or not re.fullmatch(r"\d{1,3}\.\d{1,3}\.\d{1,3}", value):
        fail(f"{field} must be a three-part numeric version below 1000 per part")
    parts = tuple(int(part) for part in value.split("."))
    if any(part >= 1_000 for part in parts):
        fail(f"{field} must keep each version part below 1000")
    return parts


def parse_day(value: object, field: str) -> date:
    if not isinstance(value, str):
        fail(f"{field} must be a YYYY-MM-DD string")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field} must be a valid YYYY-MM-DD date") from error
    if parsed.isoformat() != value:
        fail(f"{field} must use canonical YYYY-MM-DD form")
    return parsed


def validate_source_url(value: object, article_id: str) -> None:
    if not isinstance(value, str):
        fail(f"{article_id}: sourceURL must be a string")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        fail(f"{article_id}: sourceURL must use HTTPS on an approved Azure Mastery host")
    if parsed.username or parsed.password or parsed.port or parsed.query or parsed.fragment:
        fail(f"{article_id}: sourceURL cannot contain credentials, a port, query, or fragment")
    prefix = "/apps/AzureMastery/"
    if not parsed.path.startswith(prefix) or ".." in Path(parsed.path).parts:
        fail(f"{article_id}: sourceURL must stay under {prefix}")
    local_source = ROOT / parsed.path.removeprefix("/")
    if not local_source.is_file():
        fail(f"{article_id}: sourceURL has no matching site file: {local_source.relative_to(ROOT)}")


def validate() -> None:
    raw = FEED.read_bytes()
    if len(raw) > BYTE_LIMIT:
        fail(f"feed is {len(raw)} bytes; maximum is {BYTE_LIMIT}")
    try:
        feed = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON: {error}") from error

    if feed.get("schemaVersion") != 1:
        fail("schemaVersion must be 1")
    if not isinstance(feed.get("contentVersion"), int) or isinstance(feed["contentVersion"], bool) or feed["contentVersion"] <= 0:
        fail("contentVersion must be a positive integer")
    revision = feed.get("revision")
    if not isinstance(revision, str) or not revision or len(revision) > 100:
        fail("revision must contain 1 to 100 characters")
    articles = feed.get("articles")
    if not isinstance(articles, list) or not 1 <= len(articles) <= ARTICLE_LIMIT:
        fail(f"articles must contain 1 to {ARTICLE_LIMIT} entries")

    seen: set[str] = set()
    today = date.today()
    for index, article in enumerate(articles):
        if not isinstance(article, dict):
            fail(f"article {index}: must be an object")
        article_id = article.get("id")
        if not isinstance(article_id, str) or not ID_PATTERN.fullmatch(article_id):
            fail(f"article {index}: id must use 1 to 80 ASCII letters, digits, or hyphens")
        if article_id in seen:
            fail(f"{article_id}: duplicate article id")
        seen.add(article_id)

        title = article.get("title")
        text = article.get("text")
        if not isinstance(title, str) or not title.strip() or len(title) > 160:
            fail(f"{article_id}: title must contain 1 to 160 characters")
        if not isinstance(text, str) or not text.strip() or len(text) > 4_000:
            fail(f"{article_id}: text must contain 1 to 4000 characters")

        validate_source_url(article.get("sourceURL"), article_id)
        reviewed = parse_day(article.get("reviewedOn"), f"{article_id}.reviewedOn")
        expires = parse_day(article.get("expiresOn"), f"{article_id}.expiresOn")
        if reviewed > today:
            fail(f"{article_id}: reviewedOn is in the future")
        if expires <= today:
            fail(f"{article_id}: reviewed help has expired")
        if expires <= reviewed or expires > reviewed + timedelta(days=180):
            fail(f"{article_id}: expiresOn must be after review and within 180 days")

        minimum = parse_version(article.get("minimumAppVersion"), f"{article_id}.minimumAppVersion")
        maximum = parse_version(article.get("maximumAppVersion"), f"{article_id}.maximumAppVersion")
        if minimum > maximum:
            fail(f"{article_id}: minimumAppVersion exceeds maximumAppVersion")

    print(
        f"Ask Aura help feed passed: {len(articles)} reviewed articles, "
        f"contentVersion {feed['contentVersion']}, {len(raw)} bytes."
    )


if __name__ == "__main__":
    try:
        validate()
    except (OSError, ValueError) as error:
        print(f"Ask Aura help feed failed: {error}", file=sys.stderr)
        raise SystemExit(1)
