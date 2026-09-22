import json
import subprocess

CHANNEL_URL = "https://www.youtube.com/@whatastory/videos"

raw = subprocess.check_output([
    "yt-dlp", "--flat-playlist", "-J", CHANNEL_URL
])
data = json.loads(raw)

videos = [
    {"id": e["id"], "title": e["title"], "url": f"https://youtu.be/{e['id']}"}
    for e in data["entries"] if e.get("id")
]

with open("data/videos.json", "w") as f:
    json.dump(videos, f, indent=2, ensure_ascii=False)

print(f"{len(videos)} video terdaftar -> data/videos.json")
