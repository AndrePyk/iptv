#!/usr/bin/env python3
"""Build a compact BY/UA/RU IPTV playlist from Free-TV/IPTV."""

from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "playlist.m3u8"

SOURCES = [
    (
        "BY",
        "Беларусь",
        "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlists/playlist_belarus.m3u8",
        "https://raw.githubusercontent.com/Free-TV/IPTV/master/lists/belarus.md",
    ),
    (
        "UA",
        "Украина",
        "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlists/playlist_ukraine.m3u8",
        "https://raw.githubusercontent.com/Free-TV/IPTV/master/lists/ukraine.md",
    ),
    (
        "RU",
        "Россия",
        "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlists/playlist_russia.m3u8",
        "https://raw.githubusercontent.com/Free-TV/IPTV/master/lists/russia.md",
    ),
]

# Extra known regional IDs, as a fallback if upstream list formatting changes.
MANUAL_REGIONAL_IDS = {
    "BY": {
        "8kanal.by", "belarus4vitebsk.by", "nashetv.by", "vitebsk.by",
    },
    "UA": {
        "suspilnekyiv.ua", "suspilnednipro.ua", "suspilnezhytomyr.ua",
        "suspilneodesa.ua", "suspilnesumy.ua", "suspilnekhmelnytskyi.ua",
        "suspilnechernivtsi.ua", "suspilnekropyvnytskyi.ua",
        "suspilnelutsk.ua", "suspilnekrym.ua", "suspilneternopil.ua",
        "suspilnechernihiv.ua", "dniprotv.ua", "telekanalrai.ua",
        "ternopil1.ua", "sk1.ua", "pervyygorodskoyodessa.ua",
        "kyiv.ua", "itv.ua", "ntktv.ua", "tva.ua", "tv7plus.ua",
    },
    "RU": {
        "arktika24.ru", "arkhyz24.ru", "astrakhan24.ru",
        "bashkortostan24.ru", "belgorod24.ru", "vetta24.ru",
        "volgograd24.ru", "zapad24.ru", "katun24.ru", "crimea24.ru",
        "kuban24.ru", "lugansk24.ua", "mirbelogorya.ru", "moskva24.ru",
        "nizhniynovgorod24.ru", "samara24.ru", "saratov24.ru",
        "sibir24.ru", "tolyatti24.ru", "ural24.ru", "yakutiya24.ru",
        "360news.ru", "sever.ru",
    },
}

# Match radio names without matching ordinary TV names such as "РЕН ТВ".
RADIO_PATTERN = re.compile(
    r"(?:\bradio\b|\bradio[ -]?fm\b|\bрадио\b|\bфм\b|\bfm\b|\bвещание\s+радио\b)",
    re.IGNORECASE,
)


def download_text(url: str) -> str:
    request = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 IPTV-playlist-builder"},
    )
    with urlopen(request, timeout=90) as response:
        return response.read().decode("utf-8-sig")


def get_attr(line: str, name: str) -> str:
    match = re.search(
        r"\b" + re.escape(name) + r'="([^"]*)"',
        line,
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else ""


def set_attr(line: str, name: str, value: str) -> str:
    pattern = r"\b" + re.escape(name) + r'="[^"]*"'
    if re.search(pattern, line, re.IGNORECASE):
        return re.sub(
            pattern,
            f'{name}="{value}"',
            line,
            count=1,
            flags=re.IGNORECASE,
        )
    before, comma, after = line.partition(",")
