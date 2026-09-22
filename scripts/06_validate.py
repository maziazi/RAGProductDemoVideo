import chromadb
import requests

LM_EMBED_URL = "http://localhost:1234/v1/embeddings"
EMBED_MODEL = "text-embedding-bge-m3"

QUERIES = [
    "kalimat pembuka yang menyebutkan masalah user",
    "cara menyebutkan nama produk pertama kali",
    "kalimat penutup ajakan bertindak (CTA)",
    "durasi ideal video explainer",
    "cara menjelaskan fitur produk AI agent",
    "transisi antar scene saat demo produk",
    "nada/tone voice over yang dipakai",
    "struktur skrip video onboarding SaaS",
    "cara menunjukkan before after masalah user",
    "kata yang menciptakan urgensi dalam script",
    "cara memperkenalkan pembicara di video testimoni",
    "elemen visual yang ditampilkan saat reveal fitur",
    "jumlah kata ideal untuk video 60 detik",
    "pola musik latar untuk video explainer",
    "cara menutup video dengan call to action yang kuat",
]


def embed(text):
    r = requests.post(LM_EMBED_URL, json={"model": EMBED_MODEL, "input": text})
    r.raise_for_status()
    return r.json()["data"][0]["embedding"]


def main():
    client = chromadb.PersistentClient(path="chroma_db")
    col = client.get_collection("whatastory_transcript")

    for q in QUERIES:
        hits = col.query(query_embeddings=[embed(q)], n_results=3)
        print(f"\nQ: {q}")
        if not hits["documents"][0]:
            print("  (kosong)")
            continue
        for d, m, dist in zip(hits["documents"][0], hits["metadatas"][0], hits["distances"][0]):
            print(f"  [{dist:.3f}] {m['title'][:55]} :: {d[:80]}")


if __name__ == "__main__":
    main()
