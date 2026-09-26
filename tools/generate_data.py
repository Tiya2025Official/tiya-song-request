import json
import re
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[1]


def blocks(path):
    doc = Document(path)
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            yield text


def clean_heading(text):
    return text.strip().strip("【】").rstrip("：:").strip()


def song_lines(text):
    return [line.strip() for line in text.splitlines() if line.strip()]


def parse_catalog(path, language, singer_headings=None):
    singer_headings = singer_headings or set()
    section = "其他"
    items = []
    for block in blocks(path):
        lines = song_lines(block)
        if not lines:
            continue
        first = lines[0]
        heading = None
        if first.startswith("【") and "】" in first:
            heading = clean_heading(first)
            lines = lines[1:]
        elif len(lines) == 1 and first.endswith(("：", ":")):
            heading = clean_heading(first)
            lines = []
        if heading:
            section = heading
        for title in lines:
            if title in {"小语种歌单"}:
                continue
            artist = section if section in singer_headings else ""
            style = "歌手专属" if artist else section
            items.append({
                "title": title,
                "artist": artist,
                "style": style,
                "language": language,
            })
    return items


def parse_queue(path):
    status = "已学"
    result = {"learned": [], "queued": []}
    for block in blocks(path):
        for line in song_lines(block):
            if line == "缇娅的学歌排队清单":
                continue
            if line.startswith("【"):
                status = clean_heading(line)
                continue
            target = result["learned" if status == "已学" else "queued"]
            # Only the long dash is consistently used as “requester — song”.
            # Plain hyphens are also part of several song titles and a few late
            # entries reverse the order, so preserve those lines verbatim.
            parts = re.split(r"\s*[—–]\s*", line, maxsplit=1)
            if len(parts) == 2:
                requester, title = parts
            else:
                requester, title = "", line
            target.append({"requester": requester.strip(), "title": title.strip()})
    return result


chinese_singers = {
    "邓紫棋", "陈奕迅", "周杰伦", "林俊杰", "毛不易", "王菲", "邓丽君",
    "张碧晨", "薛之谦", "张杰", "陈粒",
}
western_singers = {
    "Taylor Swift", "Bruno Mars", "Billie Eilish", "Lady Gaga", "Justin Bieber",
    "Avril Lavigne", "Ed Sheeran", "Maroon 5", "Britney Spears", "Imagine Dragons",
    "Adele", "Katy Perry", "Alan Walker", "Charlie Puth", "Rihanna", "Sia",
    "Lana Del Rey", "Meghan Trainor", "Coldplay", "Troye Sivan",
}

songs = []
songs += parse_catalog(ROOT / "中文歌单8.31.docx", "中文", chinese_singers)
songs += parse_catalog(ROOT / "小语种歌单8.31.docx", "小语种")
songs += parse_catalog(ROOT / "欧美歌单最新.docx", "欧美", western_singers)
queue = parse_queue(ROOT / "缇娅的学歌排队清单9.9版本.docx")

payload = {
    "updated": "2026-09-26",
    "songs": songs,
    "queue": queue,
}

output = ROOT / "site" / "data.js"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(
    "window.TIYA_DATA = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n",
    encoding="utf-8",
)
print(f"Wrote {len(songs)} songs, {len(queue['queued'])} queued, {len(queue['learned'])} learned to {output}")
