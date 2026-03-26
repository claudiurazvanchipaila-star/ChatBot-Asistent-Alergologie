from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
import os
import pickle
import numpy as np
import re
import hashlib

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
INDEX_FILE = "books_index.pkl"

ALLERGY_TERMS = [
    "allergy", "allergic", "allergen", "allergens",
    "anaphylaxis", "rhinitis", "asthma", "urticaria",
    "angioedema", "eczema", "dermatitis", "atopic",
    "food allergy", "conjunctivitis", "wheezing",
    "immunotherapy", "ige",
    "alergie", "alergic", "alergen", "alergeni",
    "anafilaxie", "rinită", "rinita", "astm", "urticarie",
    "angioedem", "eczeme", "dermatită", "dermatita",
    "atopic", "conjunctivită", "conjunctivita",
    "wheezing", "prurit", "rinoree", "polen", "acarieni"
]

_model = None


def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def normalize_text(text):
    text = (text or "").lower()

    replacements = {
        "stranut": "strănut",
        "lacrimare": "lăcrimare",
        "mancarime": "mâncărime",
        "rinita": "rinită",
        "dermatita": "dermatită",
        "conjunctivita": "conjunctivită",
        "suieraturi": "șuierături",
        "varsaturi": "vărsături",
        "dureri abdominale": "dureri abdominale",
        "voce ragusita": "voce răgușită"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_books_signature(pdf_paths):
    parts = []

    for path in sorted(pdf_paths):
        if os.path.exists(path):
            stat = os.stat(path)
            parts.append(f"{os.path.basename(path)}|{stat.st_size}|{int(stat.st_mtime)}")

    raw = "||".join(parts)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def page_is_relevant(text):
    text_norm = normalize_text(text)
    hits = sum(1 for term in ALLERGY_TERMS if term in text_norm)
    return hits >= 2


def extract_text_from_pdf(path):
    pages = []

    try:
        reader = PdfReader(path)

        for page_index, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text() or ""
            except Exception as e:
                print(f"[AVERTISMENT] Nu am putut extrage textul din pagina {page_index + 1} a fișierului {os.path.basename(path)}: {e}")
                page_text = ""

            page_text = page_text.strip()
            if page_text:
                pages.append({
                    "page_content": page_text,
                    "metadata": {
                        "page": page_index + 1
                    }
                })

    except Exception as e:
        print(f"[AVERTISMENT] Nu am putut deschide PDF-ul {os.path.basename(path)}")
        print(f"[MOTIV] {e}")

    return pages


def load_books(pdf_paths):
    documents = []

    for path in pdf_paths:
        file_name = os.path.basename(path)
        print(f"[INFO] Încep încărcarea: {file_name}")

        try:
            loaded_pages = extract_text_from_pdf(path)

            filtered_docs = []
            for item in loaded_pages:
                page_text = (item.get("page_content") or "").strip()
                if not page_text:
                    continue

                if page_is_relevant(page_text):
                    filtered_docs.append({
                        "page_content": page_text,
                        "metadata": {
                            "source_name": file_name,
                            "page": item.get("metadata", {}).get("page", "?")
                        }
                    })

            documents.extend(filtered_docs)
            print(f"[OK] Încărcat: {file_name} | pagini relevante: {len(filtered_docs)} / {len(loaded_pages)}")

        except Exception as e:
            print(f"[AVERTISMENT] Nu am putut încărca: {file_name}")
            print(f"[MOTIV] {e}")
            continue

    return documents


def split_text(text, chunk_size=700, overlap=120):
    text = (text or "").strip()
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end == text_length:
            break

        start = max(end - overlap, 0)

    return chunks


def sentence_split(text):
    text = (text or "").strip()
    if not text:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 40]


def chunk_is_relevant(text):
    text_norm = normalize_text(text)
    hits = sum(1 for term in ALLERGY_TERMS if term in text_norm)
    return hits >= 2


def prepare_chunks(documents):
    prepared = []
    per_source_count = {}

    for doc in documents:
        page_text = (doc.get("page_content") or "").strip()
        if not page_text:
            continue

        metadata = doc.get("metadata", {})
        source = metadata.get("source_name", "Sursă necunoscută")
        page = metadata.get("page", "?")

        page_chunks = split_text(page_text)

        useful_chunks = []
        for chunk in page_chunks:
            if chunk_is_relevant(chunk):
                useful_chunks.append(chunk)

        useful_chunks = useful_chunks[:2]

        for chunk in useful_chunks:
            current_count = per_source_count.get(source, 0)

            if current_count >= 600:
                continue

            prepared.append({
                "text": chunk,
                "source": source,
                "page": page
            })
            per_source_count[source] = current_count + 1

    for source, count in per_source_count.items():
        print(f"[INFO] Chunk-uri păstrate pentru {source}: {count}")

    return prepared


def build_semantic_index(documents, books_signature):
    model = get_embedding_model()
    prepared_chunks = prepare_chunks(documents)

    texts = [item["text"] for item in prepared_chunks]
    if not texts:
        return {
            "chunks": [],
            "embeddings": np.array([]),
            "books_signature": books_signature
        }

    print(f"[INFO] Se generează embeddings pentru {len(texts)} chunk-uri...")
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        batch_size=16,
        show_progress_bar=True
    )

    return {
        "chunks": prepared_chunks,
        "embeddings": embeddings,
        "books_signature": books_signature
    }


def save_semantic_index(index_data, filepath=INDEX_FILE):
    with open(filepath, "wb") as f:
        pickle.dump(index_data, f)


def load_semantic_index(filepath=INDEX_FILE):
    if not os.path.exists(filepath):
        return None

    with open(filepath, "rb") as f:
        return pickle.load(f)


def initialize_semantic_index(documents, pdf_paths, force_rebuild=False):
    current_signature = get_books_signature(pdf_paths)

    if not force_rebuild:
        cached = load_semantic_index()
        if cached is not None:
            cached_signature = cached.get("books_signature")
            if cached_signature == current_signature:
                print("[INFO] Index semantic încărcat din cache. Nu s-au detectat modificări în folderul books.")
                return cached
            else:
                print("[INFO] S-au detectat modificări în folderul books. Se reconstruiește indexul semantic...")

    print("[INFO] Se construiește indexul semantic...")
    index_data = build_semantic_index(documents, current_signature)
    save_semantic_index(index_data)
    print("[INFO] Index semantic salvat.")
    return index_data


def pick_best_sentence(chunk_text, query_words):
    sentences = sentence_split(chunk_text)
    if not sentences:
        return chunk_text[:700].strip()

    scored_sentences = []

    for sentence in sentences:
        sentence_lower = sentence.lower()
        score = sum(1 for word in query_words if word in sentence_lower)
        scored_sentences.append((score, sentence))

    scored_sentences.sort(key=lambda x: x[0], reverse=True)

    best_score, best_sentence = scored_sentences[0]
    if best_score <= 0:
        return sentences[0][:700].strip()

    return best_sentence[:700].strip()


def cosine_similarity_manual(query_embedding, embeddings):
    if embeddings is None or len(embeddings) == 0:
        return np.array([])

    query_vector = query_embedding[0]
    return np.dot(embeddings, query_vector)


def search_chunks(query, semantic_index, top_k=8):
    query = (query or "").strip()
    if not query:
        return []

    chunks = semantic_index.get("chunks", [])
    embeddings = semantic_index.get("embeddings")

    if not chunks or embeddings is None or len(chunks) == 0:
        return []

    model = get_embedding_model()
    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    scores = cosine_similarity_manual(query_embedding, embeddings)
    ranked_idx = np.argsort(scores)[::-1]

    query_words = [w for w in re.findall(r"\w+", query.lower()) if len(w) > 3]

    results = []
    seen = set()

    for idx in ranked_idx:
        score = float(scores[idx])

        if score < 0.22:
            continue

        item = chunks[idx]
        snippet = pick_best_sentence(item["text"], query_words)

        dedup_key = (item["source"], item["page"], snippet[:140])
        if dedup_key in seen:
            continue

        seen.add(dedup_key)
        results.append({
            "score": round(score, 4),
            "text": snippet,
            "source": item["source"],
            "page": item["page"]
        })

        if len(results) >= top_k:
            break

    return results