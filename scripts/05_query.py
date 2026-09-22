import sys

import chromadb
import requests

LM_EMBED_URL = "http://localhost:1234/v1/embeddings"
LM_CHAT_URL = "http://localhost:1234/v1/chat/completions"
EMBED_MODEL = "text-embedding-bge-m3"
CHAT_MODEL = "qwen/qwen3.5-9b"


def embed(text: str) -> list[float]:
    r = requests.post(LM_EMBED_URL, json={"model": EMBED_MODEL, "input": text})
    r.raise_for_status()
    return r.json()["data"][0]["embedding"]


def main():
    if len(sys.argv) < 2:
        print('Pakai: python scripts/05_query.py "pertanyaan Anda"')
        return

    query = sys.argv[1]
    client = chromadb.PersistentClient(path="chroma_db")
    col = client.get_collection("whatastory_transcript")

    q_emb = embed(query)
    hits = col.query(query_embeddings=[q_emb], n_results=8)

    if not hits["documents"][0]:
        print("Tidak ada hasil — pastikan index sudah dibangun (04_build_index.py).")
        return

    context = "\n\n".join(
        f"[{m['title']} @ {m['url']}]\n{d}"
        for d, m in zip(hits["documents"][0], hits["metadatas"][0])
    )

    print("=== RETRIEVAL (mentah) ===")
    for d, m in zip(hits["documents"][0], hits["metadatas"][0]):
        print(f"- {m['title']} ({m['url']}): {d[:120]}...")

    print("\n=== SINTESIS ===")
    r = requests.post(LM_CHAT_URL, json={
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": "Rangkum pola dari kutipan video berikut untuk menjawab pertanyaan. Sertakan sumber (judul+url) tiap klaim. Jawab dalam Bahasa Indonesia."},
            {"role": "user", "content": f"Pertanyaan: {query}\n\nKutipan:\n{context}"},
        ],
    })
    r.raise_for_status()
    print(r.json()["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()
