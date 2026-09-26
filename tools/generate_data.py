import json
import re
from datetime import date
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
            # The updated document consistently uses requester — song.
            # Split only once so hyphens inside song titles remain untouched.
            parts = re.split(r"\s*[—–]\s*", line, maxsplit=1)
            if len(parts) == 2:
                requester, title = parts
            else:
                raise ValueError(f"学歌清单请使用 点歌人—歌名 格式：{line}")
            if not requester.strip() or not title.strip():
                raise ValueError(f"学歌清单点歌人或歌名为空：{line}")
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

def build_payload():
    review_path = ROOT / "歌单表格核对" / "核对资料" / "review_records.json"
    reviewed = json.loads(review_path.read_text(encoding="utf-8"))
    # Match by language, original title and category, not title alone:
    # e.g. Paris has different approved artists in the retro/electronic groups.
    approved = {}
    for row in reviewed:
        if row["kind"] == "学歌":
            continue
        section = row["section"]
        approved[(row["kind"], row["original"], section)] = row

    songs = []
    for filename, language, singers in [
        ("中文歌单8.31.docx", "中文", chinese_singers),
        ("小语种歌单8.31.docx", "小语种", set()),
        ("欧美歌单最新.docx", "欧美", western_singers),
    ]:
        for song in parse_catalog(ROOT / filename, language, singers):
            if song["style"] == "二游/电子":
                song["style"] = "二游"
            if language == "小语种":
                hint = re.search(r"（(.*?)）", song["title"])
                if hint:
                    song["style"] = hint.group(1)
            section = song["artist"] if song["style"] == "歌手专属" else song["style"]
            row = approved.get((language, song["title"], section))
            if row:
                song["title"] = row["title"]
                song["artist"] = row["artist"]
            if song["style"] == "二游":
                song["artist"] = ""
            songs.append(song)

    # Always reread the live queue document, never the older review snapshot.
    queue = parse_queue(ROOT / "缇娅的学歌排队清单9.9版本.docx")
    return {"updated": date.today().isoformat(), "songs": songs, "queue": queue}


if __name__ == "__main__":
    payload = build_payload()
    output = ROOT / "site" / "data.js"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "window.TIYA_DATA = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(payload['songs'])} songs, {len(payload['queue']['queued'])} queued, {len(payload['queue']['learned'])} learned to {output}")
