# Knowledge Base Upgrade: ChromaDB with Semantic Retrieval

## What to change

Replace the keyword search in `src/tools/knowledge_base.py` with ChromaDB
using Anthropic's Voyager embeddings (or sentence-transformers if you want
to avoid an extra API dependency).

## Current state

- 44 tactics as Python dicts in a list (`TACTICS_LIBRARY` + `FIELD_TESTED_TACTICS`)
- Keyword search: splits query into words, counts matches, returns top N
- Works but misses semantic matches (e.g. "VP has gone quiet" won't match
  a tactic about "executive sponsor silence" unless exact words overlap)

## Target state

- ChromaDB local persistent collection storing all 44 tactics
- Embeddings generated at index time (one-time cost)
- Semantic search at query time: orchestrator's natural language query
  finds conceptually related tactics even without keyword overlap
- Field-tested tactics get a 1.3x relevance boost (metadata filter)
- Falls back to keyword search if ChromaDB is unavailable

## Implementation

### Step 1: Add dependencies

In `pyproject.toml`:
```
"chromadb>=0.5.0",
"sentence-transformers>=3.0.0",
```

sentence-transformers keeps everything local (no extra API key needed).
Use `all-MiniLM-L6-v2` — it's small, fast, and good enough for 44 docs.

### Step 2: Rewrite knowledge_base.py

```python
"""Knowledge Base Tool — semantic retrieval over change management tactics."""

from __future__ import annotations

import os
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

# Keep the full TACTICS_LIBRARY + FIELD_TESTED_TACTICS lists as before
# (they serve as the source of truth for indexing)

CHROMA_PATH = Path("data/knowledge_base/chroma_db")
COLLECTION_NAME = "deployment_tactics"

# Use sentence-transformers for local embeddings (no API key needed)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class KnowledgeBaseTool:
    """Semantic search over change management tactics using ChromaDB."""

    def __init__(self, reindex: bool = False):
        self.chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_PATH)
        )
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )

        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"},
        )

        # Index if empty or reindex requested
        if self.collection.count() == 0 or reindex:
            self._index_tactics()

    def _index_tactics(self):
        """Index all tactics into ChromaDB."""
        # Combine both tactic lists
        all_tactics = TACTICS_LIBRARY + FIELD_TESTED_TACTICS

        # Clear existing
        if self.collection.count() > 0:
            existing = self.collection.get()
            if existing["ids"]:
                self.collection.delete(ids=existing["ids"])

        ids = []
        documents = []
        metadatas = []

        for tactic in all_tactics:
            ids.append(tactic["id"])

            # The document is what gets embedded — combine searchable fields
            doc = (
                f"{tactic['tactic']} "
                f"{tactic['best_for']} "
                f"{tactic['stage']} "
                f"{tactic['framework']}"
            )
            documents.append(doc)

            metadatas.append({
                "id": tactic["id"],
                "framework": tactic["framework"],
                "stage": tactic["stage"],
                "is_field_tested": "Field-tested" in tactic["framework"],
                "tactic": tactic["tactic"],
                "best_for": tactic["best_for"],
            })

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        print(f"Indexed {len(ids)} tactics into ChromaDB")

    def query(self, query: str, max_results: int = 3) -> list[dict[str, str]]:
        """
        Semantic search for tactics matching the query.

        Field-tested tactics get a relevance boost by querying for
        more results and reranking with a 1.3x multiplier.
        """
        # Fetch more than needed so we can rerank
        fetch_n = min(max_results * 3, self.collection.count())

        results = self.collection.query(
            query_texts=[query],
            n_results=fetch_n,
            include=["metadatas", "distances"],
        )

        if not results["metadatas"] or not results["metadatas"][0]:
            return []

        # Rerank: field-tested tactics get a 1.3x boost
        scored = []
        for meta, distance in zip(
            results["metadatas"][0], results["distances"][0]
        ):
            # ChromaDB cosine distance: 0 = identical, 2 = opposite
            # Convert to similarity: 1 - (distance / 2)
            similarity = 1 - (distance / 2)

            if meta.get("is_field_tested"):
                similarity *= 1.3  # field-tested boost

            scored.append((similarity, {
                "id": meta["id"],
                "framework": meta["framework"],
                "stage": meta["stage"],
                "tactic": meta["tactic"],
                "best_for": meta["best_for"],
            }))

        # Sort by boosted similarity, return top N
        scored.sort(key=lambda x: x[0], reverse=True)
        return [tactic for _, tactic in scored[:max_results]]

    def reindex(self):
        """Force reindex all tactics (call after updating tactic lists)."""
        self._index_tactics()


# ── Keyword fallback (used if ChromaDB fails) ──

def keyword_query(
    tactics: list[dict], query: str, max_results: int = 3
) -> list[dict[str, str]]:
    """Fallback keyword search if ChromaDB is unavailable."""
    query_terms = set(query.lower().split())
    scored = []
    for tactic in tactics:
        searchable = (
            tactic["tactic"].lower() + " " +
            tactic["best_for"].lower() + " " +
            tactic["stage"].lower() + " " +
            tactic["framework"].lower()
        )
        score = sum(1 for term in query_terms if term in searchable)
        if "Field-tested" in tactic["framework"]:
            score *= 1.3
        if score > 0:
            scored.append((score, tactic))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in scored[:max_results]]
```

### Step 3: Add an index command to main.py

```python
# Add to the subparsers in main.py
index_parser = subparsers.add_parser("index-kb", help="Reindex the knowledge base")

# In the command handler:
elif args.command == "index-kb":
    from src.tools.knowledge_base import KnowledgeBaseTool
    kb = KnowledgeBaseTool(reindex=True)
    console.print(f"Knowledge base indexed: {kb.collection.count()} tactics")
```

### Step 4: Update .gitignore

Add `data/knowledge_base/` to .gitignore — the ChromaDB files are
generated at index time, not committed.

### Step 5: Update CLAUDE.md

Change the KB description to:
```
- **Knowledge base**: ChromaDB with sentence-transformer embeddings
  (all-MiniLM-L6-v2). 44 tactics indexed locally. Semantic search with
  1.3x relevance boost for field-tested entries. Keyword fallback if
  ChromaDB unavailable. Reindex with `python -m src.main index-kb`.
```

## Testing

After implementation, verify:

1. `python -m src.main index-kb` indexes 44 tactics without errors
2. Semantic query works: query "executive sponsor has gone silent for
   two weeks" should return `field_silent_vp_pattern` even though those
   exact words don't appear in it
3. Field-tested boost works: for a query that matches both a generic
   ADKAR entry and a field-tested entry equally well, the field-tested
   one should rank higher
4. Fallback works: if ChromaDB path is deleted, keyword search kicks in
5. Run a quick Nova Tech simulation and verify the orchestrator's tool
   use logs show it retrieving semantically relevant tactics

## Architecture note for interviews

"The knowledge base uses ChromaDB with sentence-transformer embeddings
for semantic retrieval over 44 change management tactics. I use a 1.3x
relevance boost for field-tested entries so the orchestrator
preferentially selects battle-tested interventions over generic framework
tactics when both are relevant. The embedding model runs locally — no
external API calls during retrieval, which keeps latency under 50ms per
query."
