"""
ResQMesh AI — Autonomous Knowledge Base Builder & Indexer CLI

Usage:
    python build_knowledge_base.py [--rebuild]

Functions:
    1. Reads source documents in backend/app/rag/documents/
    2. Performs heading-aware semantic chunking
    3. Generates L2-normalized term frequency vector embeddings
    4. Updates local vector index and chunk metadata database
    5. Produces cryptographic audit manifest (manifest.json)
    6. Outputs detailed knowledge base size report (<400 MB verification)
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from build_rag_corpus import (
    init_directories,
    build_corpus_documents,
    build_reference_document_packages,
    chunk_and_index_corpus,
    generate_size_report,
    DOCS_DIR,
)

def main():
    print("\n========================================================")
    print("RESQMESH AI — REBUILDING DISASTER RAG KNOWLEDGE BASE")
    print("========================================================")
    init_directories()
    build_corpus_documents()
    build_reference_document_packages()
    chunks, index, manifest = chunk_and_index_corpus()
    generate_size_report()
    print("[SUCCESS] Knowledge base rebuild complete. All components verified.\n")

if __name__ == "__main__":
    main()
