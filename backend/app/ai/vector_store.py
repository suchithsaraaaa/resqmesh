import math
import os
import sys
import json
import re
from typing import Dict, List, Optional, Tuple, Any

try:
    from backend.app.ai.query_parser import QueryParser, ParsedQuery
except ImportError:
    try:
        from app.ai.query_parser import QueryParser, ParsedQuery
    except ImportError:
        QueryParser = None
        ParsedQuery = None


class SOPDocument:
    """Standard Operating Procedure document chunk with vector representation and rich metadata."""

    def __init__(
        self,
        doc_id: str,
        title: str,
        category: str,
        content: str,
        metadata: Optional[dict] = None,
    ):
        self.doc_id = doc_id
        self.title = title
        self.category = category.lower()
        self.content = content
        self.metadata = metadata or {}
        self.vector: Dict[str, float] = {}

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "category": self.category,
            "content": self.content,
            "metadata": self.metadata,
        }


STOP_WORDS = {
    "what", "are", "the", "is", "in", "for", "and", "or", "of", "to", "a", "an",
    "how", "should", "we", "do", "be", "with", "this", "that", "it", "on", "at",
    "by", "from", "as", "into", "during", "before", "after", "when", "where", "which",
    "who", "all", "any", "some", "such", "no", "not", "only", "own", "same", "so",
    "than", "too", "very", "can", "will", "just", "now", "might", "much", "must",
    "about", "been", "being", "have", "has", "had", "would", "could", "there", "their"
}


def normalize_category(cat: str) -> str:
    """Normalize category plurals and aliases to standard forms."""
    c = cat.lower().strip()
    mapping = {
        "earthquakes": "earthquake",
        "floods": "flood",
        "cyclones": "cyclone",
        "landslides": "landslides",
        "landslide": "landslides",
        "heat_waves": "heat_wave",
        "structural": "building_collapse",
        "structural_collapse": "building_collapse",
        "building_collapses": "building_collapse",
        "collapse": "building_collapse",
        "nuclear": "nuclear_disaster",
        "radiological": "nuclear_disaster",
        "radiation": "nuclear_disaster",
        "logistics": "disaster_logistics",
        "sanitation": "public_health",
        "biological": "biological_emergency",
        "industrial": "industrial_disaster",
    }
    return mapping.get(c, c)


def tokenize_and_vectorize(text: str) -> Dict[str, float]:
    """Tokenize, remove common stop words, and compute normalized term-frequency vector."""
    words = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", text.lower())
    filtered = [w for w in words if w not in STOP_WORDS]
    if not filtered:
        return {}

    tf: Dict[str, float] = {}
    for word in filtered:
        tf[word] = tf.get(word, 0.0) + 1.0

    # L2 normalize
    norm = math.sqrt(sum(v * v for v in tf.values()))
    if norm > 0.0:
        return {k: v / norm for k, v in tf.items()}
    return tf


def cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """Calculate cosine similarity between two normalized sparse vectors."""
    if not vec1 or not vec2:
        return 0.0

    # Dot product of normalized vectors
    dot_product = sum(vec1[k] * vec2[k] for k in vec1 if k in vec2)
    return max(0.0, min(1.0, dot_product))


class LocalVectorStore:
    """In-memory and indexed local vector store for disaster response Standard Operating Procedures (SOPs)."""

    def __init__(self):
        self.documents: Dict[str, SOPDocument] = {}
        self.load_knowledge_base()

    def load_knowledge_base(self) -> None:
        """Load persistent knowledge base with fallback to default SOPs."""
        # 1. Resolve persistent RAG metadata & vector index paths
        candidates = [
            # Packaged Electron sibling resource paths (e.g. resources/resqmesh-server/.. -> resources/rag)
            os.path.normpath(os.path.join(os.path.dirname(sys.executable), "..", "rag")),
            os.path.normpath(os.path.join(os.path.dirname(sys.executable), "rag")),
            # PyInstaller temp unpack path if bundled
            os.path.join(getattr(sys, "_MEIPASS", ""), "rag") if getattr(sys, "_MEIPASS", None) else "",
            # Source tree relative paths
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rag"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rag"),
            os.path.abspath("backend/app/rag"),
            os.path.abspath("app/rag"),
            os.path.abspath("rag"),
        ]

        rag_dir = None
        for cand in candidates:
            meta_path = os.path.join(cand, "metadata", "chunks_metadata.json")
            if os.path.exists(meta_path):
                rag_dir = cand
                break

        if not rag_dir:
            self.seed_default_sops()
            return

        meta_file = os.path.join(rag_dir, "metadata", "chunks_metadata.json")
        idx_file = os.path.join(rag_dir, "index", "vector_index.json")

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                chunks = json.load(f)

            if not chunks:
                self.seed_default_sops()
                return

            vector_index = {}
            if os.path.exists(idx_file):
                with open(idx_file, "r", encoding="utf-8") as f:
                    vector_index = json.load(f)

            for chunk in chunks:
                cid = chunk.get("chunk_id")
                if not cid:
                    continue
                doc = SOPDocument(
                    doc_id=cid,
                    title=chunk.get("title", "Disaster Response SOP"),
                    category=chunk.get("category", "general"),
                    content=chunk.get("content", ""),
                    metadata={
                        "organization": chunk.get("organization", "NDMA"),
                        "section": chunk.get("section", "Standard Operational Procedure"),
                        "page": chunk.get("page", 1),
                        "publication_date": chunk.get("publication_date", "2024"),
                        "source_url": chunk.get("source_url", ""),
                        "priority": chunk.get("priority", "high"),
                        "domain": chunk.get("domain", chunk.get("category", "general")),
                        "subdomain": chunk.get("subdomain", ""),
                        "hazards": chunk.get("hazards", []),
                        "substances": chunk.get("substances", []),
                        "audience": chunk.get("audience", "responder"),
                        "region": chunk.get("region", "global"),
                        "keywords": chunk.get("keywords", []),
                    },
                )
                if cid in vector_index:
                    doc.vector = vector_index[cid]
                else:
                    doc.vector = tokenize_and_vectorize(f"{doc.title} {doc.category} {doc.content}")
                self.documents[cid] = doc
        except Exception:
            pass

    def add_document(
        self,
        doc_id: str,
        title: str,
        category: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> SOPDocument:
        """Index a document and compute vector representation."""
        doc = SOPDocument(
            doc_id=doc_id,
            title=title,
            category=category,
            content=content,
            metadata=metadata,
        )
        combined_text = f"{title} {category} {content}"
        doc.vector = tokenize_and_vectorize(combined_text)
        self.documents[doc_id] = doc
        return doc

    def search(
        self,
        query: str,
        top_k: int = 3,
        category_filter: Optional[str] = None,
    ) -> List[Tuple[SOPDocument, float]]:
        """Legacy search: Top-k most relevant SOP documents by cosine similarity."""
        query_vector = tokenize_and_vectorize(query)
        if not query_vector:
            return []

        results: List[Tuple[SOPDocument, float]] = []

        for doc in self.documents.values():
            if category_filter:
                filter_norm = normalize_category(category_filter)
                doc_norm = normalize_category(doc.category)
                if doc.category != category_filter.lower() and doc_norm != filter_norm:
                    continue

            score = cosine_similarity(query_vector, doc.vector)
            if score > 0.0:
                results.append((doc, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def smart_search(
        self,
        query: str,
        incident_context: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        debug: bool = False,
    ) -> Tuple[List[Tuple[SOPDocument, float]], Dict[str, Any]]:
        """
        Smart multi-signal contextual retrieval:
        1. Extract structured query intent (domain, hazard, substance, region, role)
        2. Compute Base Cosine Score from L2-normalized sparse TF vectors
        3. Apply Exact Keyword Boosting
        4. Apply Substance-Specific Boosting (e.g. Chlorine, Ammonia)
        5. Apply Hazard & Domain Boosting
        6. Apply Regional Context Boosting (India, Telangana, Hyderabad)
        7. Apply Audience / Role Boosting
        8. Deduplicate redundant chunks
        9. Rerank and return top relevant chunks with score breakdown
        """
        parsed = None
        if QueryParser:
            parsed = QueryParser.parse(query, incident_context)

        # Build combined query text incorporating extracted substances and hazards
        enrichment_terms = []
        if parsed:
            enrichment_terms.extend(parsed.substances)
            enrichment_terms.extend(parsed.hazards)
            enrichment_terms.extend(parsed.regions)
        
        query_vector = tokenize_and_vectorize(f"{query} {' '.join(enrichment_terms)}")
        if not query_vector:
            return [], {"error": "Empty query vector"}

        candidates: List[Dict[str, Any]] = []

        is_emergency_query = bool(parsed and (parsed.domains or parsed.substances or parsed.hazards or parsed.symptoms or parsed.intents))

        for doc in self.documents.values():
            base_cosine = cosine_similarity(query_vector, doc.vector)
            
            # Non-emergency queries (e.g. stock market) do not receive emergency domain/audience boosts
            if not is_emergency_query:
                final_score = round(base_cosine, 4)
                if final_score > 0.04:
                    candidates.append({
                        "doc": doc,
                        "final_score": final_score,
                        "base_cosine": round(base_cosine, 4),
                        "keyword_boost": 0.0,
                        "substance_boost": 0.0,
                        "hazard_boost": 0.0,
                        "domain_boost": 0.0,
                        "region_boost": 0.0,
                        "audience_boost": 0.0,
                        "topic_boost": 0.0,
                    })
                continue

            # 1. Keyword Exact Matches Boost (+0.06 per matched key term, max +0.24)
            keyword_boost = 0.0
            if parsed and parsed.key_terms:
                doc_text = f"{doc.title} {doc.content} {' '.join(doc.metadata.get('keywords', []))}".lower()
                matches = sum(1 for term in parsed.key_terms if term in doc_text)
                keyword_boost = min(0.24, matches * 0.06)

            # 2. Substance-Specific Boost (+0.35 if substance matches)
            substance_boost = 0.0
            if parsed and parsed.substances:
                doc_substances = [str(s).lower() for s in doc.metadata.get("substances", [])]
                for target_sub in parsed.substances:
                    if target_sub in doc_substances or target_sub in doc.title.lower():
                        substance_boost = max(substance_boost, 0.35)
                    elif target_sub in doc.content.lower():
                        substance_boost = max(substance_boost, 0.20)

            # 3. Hazard Match Boost (+0.18)
            hazard_boost = 0.0
            if parsed and parsed.hazards:
                doc_hazards = [str(h).lower() for h in doc.metadata.get("hazards", [])]
                if any(h in doc_hazards for h in parsed.hazards):
                    hazard_boost = 0.18

            # 4. Domain / Category Boost (+0.15)
            domain_boost = 0.0
            if parsed and parsed.domains:
                doc_domain = normalize_category(doc.metadata.get("domain", doc.category))
                for d in parsed.domains:
                    if normalize_category(d) == doc_domain or d in doc.category:
                        domain_boost = 0.15
                        break

            # 5. Regional Context Boost (+0.22 for Telangana/Hyderabad, +0.10 for India)
            region_boost = 0.0
            if parsed and parsed.regions:
                doc_region = doc.metadata.get("region", "global").lower()
                if "hyderabad" in parsed.regions and (doc_region == "telangana" or "hyderabad" in doc.title.lower()):
                    region_boost = 0.22
                elif "telangana" in parsed.regions and doc_region == "telangana":
                    region_boost = 0.20
                elif "india" in parsed.regions and doc_region in ["india", "telangana"]:
                    region_boost = 0.10

            # 6. Audience Match Boost (+0.05)
            audience_boost = 0.0
            if parsed and parsed.audience:
                if doc.metadata.get("audience", "responder") == parsed.audience:
                    audience_boost = 0.05

            # 7. Topic & Section Specificity Boost (+0.25)
            topic_boost = 0.0
            if parsed and parsed.key_terms:
                sec_keywords = [str(k).lower() for k in doc.metadata.get("keywords", [])]
                sec_name = doc.metadata.get("section", "").lower()
                subdom = doc.metadata.get("subdomain", "").lower()
                for term in parsed.key_terms:
                    if term in sec_keywords or term in sec_name or term in subdom:
                        topic_boost = 0.25
                        break

            final_score = round(
                base_cosine + keyword_boost + substance_boost + hazard_boost + domain_boost + region_boost + audience_boost + topic_boost,
                4
            )

            if final_score > 0.04:
                candidates.append({
                    "doc": doc,
                    "final_score": final_score,
                    "base_cosine": round(base_cosine, 4),
                    "keyword_boost": round(keyword_boost, 4),
                    "substance_boost": round(substance_boost, 4),
                    "hazard_boost": round(hazard_boost, 4),
                    "domain_boost": round(domain_boost, 4),
                    "region_boost": round(region_boost, 4),
                    "audience_boost": round(audience_boost, 4),
                    "topic_boost": round(topic_boost, 4),
                })

        # Sort candidate pool descending
        candidates.sort(key=lambda x: x["final_score"], reverse=True)
        top_candidates = candidates[:30]

        # Context Deduplication: Avoid redundant chunks from same document with high overlap
        selected_results: List[Tuple[SOPDocument, float]] = []
        selected_doc_ids: Set[str] = set()

        for cand in top_candidates:
            doc = cand["doc"]
            # Deduplication key based on document and section
            parent_doc = doc.doc_id.split("-ch")[0]
            section = doc.metadata.get("section", "")
            dedup_key = f"{parent_doc}::{section}"

            if dedup_key in selected_doc_ids:
                continue

            selected_doc_ids.add(dedup_key)
            selected_results.append((doc, cand["final_score"]))

            if len(selected_results) >= top_k:
                break

        debug_info = {}
        if debug:
            debug_info = {
                "parsed_query": parsed.to_dict() if parsed else {},
                "total_candidates": len(candidates),
                "top_candidates": [
                    {
                        "doc_id": c["doc"].doc_id,
                        "title": c["doc"].title,
                        "section": c["doc"].metadata.get("section", ""),
                        "category": c["doc"].category,
                        "final_score": c["final_score"],
                        "score_breakdown": {
                            "base_cosine": c["base_cosine"],
                            "keyword_boost": c["keyword_boost"],
                            "substance_boost": c["substance_boost"],
                            "hazard_boost": c["hazard_boost"],
                            "domain_boost": c["domain_boost"],
                            "region_boost": c["region_boost"],
                            "audience_boost": c["audience_boost"],
                        }
                    }
                    for c in top_candidates[:8]
                ],
                "selected_count": len(selected_results),
            }

        return selected_results, debug_info

    def seed_default_sops(self) -> None:
        """Seed baseline emergency Standard Operating Procedures."""
        self.add_document(
            doc_id="sop-fire-01",
            title="Structural Fire Evacuation & Suppression SOP",
            category="fire",
            content=(
                "Establish a 100-meter safety perimeter. Cut electrical main switches immediately. "
                "Ensure breathing apparatus is deployed before interior search. "
                "Deploy Class A foam for structural fires and Class B foam for hydrocarbon fuels. "
                "Prioritize search and rescue of trapped occupants on higher floors."
            ),
            metadata={"organization": "National Disaster Management Authority", "priority": "high", "section": "Structural Fire Attack"},
        )
        self.add_document(
            doc_id="sop-flood-01",
            title="Flood Water Rescue & Inundation Containment SOP",
            category="flood",
            content=(
                "Never enter fast-moving flood waters on foot. Deploy motorized inflatable rescue boats. "
                "Responders must wear personal flotation devices (PFD) and safety helmets. "
                "Evacuate vulnerable populations to designated high-elevation relief shelters. "
                "Check for submerged power lines and hazardous material runoff before deployment."
            ),
            metadata={"organization": "Water Rescue Taskforce", "priority": "high", "section": "Swiftwater Rescue"},
        )
        self.add_document(
            doc_id="sop-medical-01",
            title="Mass Casualty Trauma Triage & Emergency Medical SOP",
            category="medical",
            content=(
                "Use START (Simple Triage and Rapid Treatment) protocol: Red (Immediate), "
                "Yellow (Delayed), Green (Minor), Black (Deceased). Control severe arterial bleeding "
                "using tourniquets placed 2-3 inches proximal to injury. Maintain open airways "
                "and stabilize spinal cervical spine before transport."
            ),
            metadata={"organization": "Emergency Medical Services", "priority": "critical", "section": "START Triage & Bleeding"},
        )
        self.add_document(
            doc_id="sop-struct-01",
            title="Building Collapse & Urban Search and Rescue (USAR) SOP",
            category="structural",
            content=(
                "Conduct structural triage and acoustic listening surveys before heavy machinery entry. "
                "Shore up unstable load-bearing walls using timber cribbing. "
                "Establish two independent egress routes for rescue teams. "
                "Monitor for hazardous gas leaks (methane, CO) using multi-gas detectors."
            ),
            metadata={"organization": "USAR Taskforce", "priority": "critical", "section": "Structural Collapse Voids"},
        )
        self.add_document(
            doc_id="sop-hazmat-01",
            title="Hazardous Materials Chemical Release Containment SOP",
            category="hazmat",
            content=(
                "Establish hot, warm, and cold contamination zones. Approach incident from upwind "
                "and uphill. Identify UN hazardous material chemical number from placard. "
                "Deploy Level A encapsulated suits for unknown toxic gases. "
                "Establish primary decontamination corridor for affected responders and casualties."
            ),
            metadata={"organization": "HazMat Protocol Directive", "priority": "high", "section": "HazMat Zoning & Level A PPE"},
        )
