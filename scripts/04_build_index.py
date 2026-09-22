import glob
import json
import os

import chromadb
import requests

LM_URL = "http://localhost:1234/v1/embeddings"
EMBED_MODEL = "text-embedding-bge-m3"

client = chromadb.PersistentClient(path="chroma_db")
col_transcript = client.get_or_create_collection("whatastory_transcript")
col_website = client.get_or_create_collection("whatastory_website")


def embed(text: str) -> list[float]:
    r = requests.post(LM_URL, json={"model": EMBED_MODEL, "input": text[:8000]})
    r.raise_for_status()
    return r.json()["data"][0]["embedding"]


def chunk_transcript(segs, window=45):
    if not segs:
        return []
    chunks, buf, t0 = [], [], segs[0]["start"]
    for s in segs:
        if s["start"] - t0 > window and buf:
            chunks.append((t0, " ".join(buf)))
            buf, t0 = [], s["start"]
        buf.append(s["text"])
    if buf:
        chunks.append((t0, " ".join(buf)))
    return chunks


# --- index transcript ---
existing_ids = set(col_transcript.get()["ids"]) if col_transcript.count() else set()
n_new = 0
for path in sorted(glob.glob("data/transcripts/*.json")):
    vid = os.path.basename(path).removesuffix(".json")
    meta_path = f"data/metadata/{vid}.json"
    if not os.path.exists(meta_path):
        continue
    meta = json.load(open(meta_path))
    segs = json.load(open(path))

    for start, text in chunk_transcript(segs):
        chunk_id = f"{vid}_{int(start)}"
        if chunk_id in existing_ids:
            continue
        if not text.strip():
            continue
        col_transcript.add(
            ids=[chunk_id],
            embeddings=[embed(text)],
            documents=[text],
            metadatas=[{
                "video_id": vid,
                "title": meta.get("title") or "",
                "start": start,
                "url": f"https://youtu.be/{vid}?t={int(start)}",
            }],
        )
        n_new += 1

print(f"transcript index: +{n_new} chunk baru, total {col_transcript.count()}")

# --- index website ---
existing_web_ids = set(col_website.get()["ids"]) if col_website.count() else set()
n_new_web = 0
for path in sorted(glob.glob("data/website/*.md")):
    text = open(path).read()
    for i in range(0, len(text), 1500):
        piece = text[i:i + 1500]
        if not piece.strip():
            continue
        chunk_id = f"{path}_{i}"
        if chunk_id in existing_web_ids:
            continue
        col_website.add(
            ids=[chunk_id],
            embeddings=[embed(piece)],
            documents=[piece],
            metadatas=[{"source": path}],
        )
        n_new_web += 1

print(f"website index: +{n_new_web} chunk baru, total {col_website.count()}")
