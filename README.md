# whatastory-rag

Pipeline RAG lokal untuk menganalisis pola skrip, pacing, dan struktur video dari channel YouTube [@whatastory](https://www.youtube.com/@whatastory) (What a Story — studio explainer video SaaS/AI). Dibangun untuk riset pola produksi video demo hackathon, bukan untuk redistribusi konten channel tersebut.

100% lokal — embedding via [LM Studio](https://lmstudio.ai) (`text-embedding-bge-m3`), generation via `qwen3.5-9b`, vector store [ChromaDB](https://www.trychroma.com).

## Arsitektur

```
yt-dlp (daftar video)
   -> yt-dlp (transcript + metadata, cookies-from-browser + backoff 429)
   -> Crawl4AI (blog & case-studies whatastory.agency)
   -> chunking + embedding (LM Studio, bge-m3)
   -> ChromaDB (persistent, lokal)
   -> query: retrieval + sintesis (LM Studio, qwen3.5-9b)
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
crawl4ai-setup   # install browser Playwright, sekali saja
```

Butuh [LM Studio](https://lmstudio.ai) berjalan di `localhost:1234` dengan model `text-embedding-bge-m3` dan `qwen/qwen3.5-9b` sudah di-load.

## Menjalankan pipeline

```bash
python scripts/01_list_videos.py        # daftar video channel -> data/videos.json
python scripts/02_fetch_transcripts.py  # transcript + metadata per video (long-running)
python scripts/03_fetch_website.py      # crawl blog & case-studies
python scripts/04_build_index.py        # chunking + embedding -> chroma_db/
python scripts/06_validate.py           # cek kualitas retrieval (opsional)
```

## Query

```bash
python scripts/05_query.py "pertanyaan Anda dalam bahasa natural"
```

Setiap jawaban disertai sitasi (judul video + timestamp + link `youtu.be/{id}?t={detik}`) agar bisa ditelusuri balik ke sumber asli.

## Catatan

- **`data/` dan `chroma_db/` sengaja di-gitignore** — berisi transcript hasil scraping channel milik pihak lain; tidak untuk didistribusikan ulang secara publik. Regenerasi ulang lewat script di atas kalau dibutuhkan.
- Fetch transcript rawan kena rate-limit YouTube (HTTP 429) kalau dijalankan dari IP yang sama berulang kali. Script sudah punya backoff otomatis + dukungan `--cookies-from-browser`, tapi kalau IP benar-benar diblokir, satu-satunya solusi adalah ganti jaringan dan tunggu.
