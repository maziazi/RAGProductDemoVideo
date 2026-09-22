import json
import os
import subprocess
import time

COOKIES = ["--cookies-from-browser", "brave"]
INITIAL_COOLDOWN = 5          # jeda awal sebelum request pertama (IP baru, tidak perlu cooldown panjang)
PER_REQUEST_DELAY = 5          # jeda normal antar video kalau tidak kena 429
BACKOFF_START = 60             # backoff pertama saat kena 429
BACKOFF_CAP = 1200             # backoff maksimum per siklus (20 menit)
MAX_CONSECUTIVE_429 = 25        # safety valve: berhenti total kalau 429 beruntun sebanyak ini

# state backoff GLOBAL — dipakai bersama oleh transcript & metadata,
# karena 429 ini blokir di level IP, bukan per-video.
_backoff = BACKOFF_START
_consecutive_429 = 0


def _handle_429():
    global _backoff, _consecutive_429
    _consecutive_429 += 1
    if _consecutive_429 > MAX_CONSECUTIVE_429:
        raise SystemExit(
            f"Berhenti: {MAX_CONSECUTIVE_429} kali 429 beruntun meski sudah backoff sampai {BACKOFF_CAP}s. "
            f"Blokir IP kemungkinan masih aktif lebih lama dari perkiraan — coba lagi nanti."
        )
    print(f"  kena 429 (beruntun ke-{_consecutive_429}), tunggu {_backoff}s...", flush=True)
    time.sleep(_backoff)
    _backoff = min(_backoff * 2, BACKOFF_CAP)


def _reset_backoff():
    global _backoff, _consecutive_429
    _backoff = BACKOFF_START
    _consecutive_429 = 0


def run_with_backoff(args):
    """Jalankan subprocess, retry lewat backoff GLOBAL kalau kena 429. Return CompletedProcess atau None (error non-429)."""
    while True:
        out = subprocess.run(args, capture_output=True, text=True, timeout=120)
        if out.returncode == 0:
            _reset_backoff()
            return out
        if "429" in out.stderr or "Too Many Requests" in out.stderr:
            _handle_429()
            continue
        return None  # error lain (mis. tidak ada subtitle) -> jangan retry


def parse_json3(path):
    data = json.load(open(path))
    segs = []
    for ev in data.get("events", []):
        if "segs" not in ev:
            continue
        text = "".join(s.get("utf8", "") for s in ev["segs"]).strip()
        if not text:
            continue
        segs.append({
            "text": text,
            "start": ev.get("tStartMs", 0) / 1000,
            "duration": ev.get("dDurationMs", 0) / 1000,
        })
    return segs


def fetch_transcript(vid, url):
    args = [
        "yt-dlp", *COOKIES, "--skip-download",
        "--write-auto-sub", "--sub-lang", "en.*", "--sub-format", "json3",
        "-o", f"data/_tmp_{vid}.%(ext)s", url,
    ]
    out = run_with_backoff(args)
    if out is None:
        return None
    candidates = [f for f in os.listdir("data") if f.startswith(f"_tmp_{vid}") and f.endswith(".json3")]
    if not candidates:
        return None
    segs = parse_json3(f"data/{candidates[0]}")
    for f in candidates:
        os.remove(f"data/{f}")
    return segs


def fetch_metadata(vid, url):
    args = ["yt-dlp", *COOKIES, "--skip-download", "--dump-json", url]
    out = run_with_backoff(args)
    if out is None:
        return None
    meta = json.loads(out.stdout)
    return {
        "title": meta.get("title"),
        "description": meta.get("description"),
        "tags": meta.get("tags", []),
        "duration": meta.get("duration"),
    }


def main():
    print(f"Cooldown awal {INITIAL_COOLDOWN}s sebelum mulai...", flush=True)
    time.sleep(INITIAL_COOLDOWN)

    videos = json.load(open("data/videos.json"))
    total = len(videos)
    ok_t, ok_m, skip_t, skip_m = 0, 0, 0, 0

    for i, v in enumerate(videos, 1):
        vid = v["id"]
        t_path = f"data/transcripts/{vid}.json"
        m_path = f"data/metadata/{vid}.json"

        if not os.path.exists(t_path):
            segs = fetch_transcript(vid, v["url"])
            if segs is not None:
                json.dump(segs, open(t_path, "w"), indent=2, ensure_ascii=False)
                ok_t += 1
            else:
                skip_t += 1

        if not os.path.exists(m_path):
            meta = fetch_metadata(vid, v["url"])
            if meta is not None:
                json.dump(meta, open(m_path, "w"), indent=2, ensure_ascii=False)
                ok_m += 1
            else:
                skip_m += 1

        if i % 10 == 0:
            print(f"progress {i}/{total} | transcript ok={ok_t} skip={skip_t} | metadata ok={ok_m} skip={skip_m}", flush=True)

        time.sleep(PER_REQUEST_DELAY)

    print(f"SELESAI | transcript ok={ok_t} skip={skip_t} | metadata ok={ok_m} skip={skip_m}", flush=True)


if __name__ == "__main__":
    main()
