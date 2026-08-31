import logging
import re
from typing import Dict, List, Optional, Any, Tuple

try:
    from backend.app.ai.vector_store import LocalVectorStore, SOPDocument
    from backend.app.ai.llm_client import LocalLLMClient
    from backend.app.ai.query_parser import QueryParser
except ImportError:
    from app.ai.vector_store import LocalVectorStore, SOPDocument
    from app.ai.llm_client import LocalLLMClient
    try:
        from app.ai.query_parser import QueryParser
    except ImportError:
        QueryParser = None

logger = logging.getLogger("ResQMesh.RAG")

RAG_OPERATIONAL_PROMPT_TEMPLATE = """
[OFFICIAL DISASTER RESPONSE EVIDENCE & SOPS]
{sop_context}

[OPERATIONAL INCIDENT CONTEXT]
Category / Domain: {category}
Query / Report: {description}
Incident Details: {incident_details}

[OPERATIONAL MISSION]
You are ResQMesh AI, an emergency response decision support engine for field commanders and responders.
Based STRICTLY and EXCLUSIVELY on the official SOP evidence provided above, provide a specific, actionable response.

RULES:
1. Do NOT provide generic advice (e.g. do not just say "stay calm and evacuate").
2. Prioritize substance-specific, hazard-specific, and patient-specific protocols found in the evidence.
3. If the retrieved evidence is insufficient to answer the query, clearly state: "I don't have enough verified guidance in the local knowledge base to provide a specific procedure for that situation."
4. Structure operational instructions clearly:
   - IMMEDIATE PRIORITIES (numbered steps)
   - RESPONDER SAFETY
   - CASUALTY / VICTIM MANAGEMENT
   - RESOURCE & COMMAND CONSIDERATIONS
   - SOURCES (cite organization and section)

[TACTICAL GUIDANCE]
"""


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline combining local SOP vector search with LLM synthesis."""

    def __init__(
        self,
        vector_store: Optional[LocalVectorStore] = None,
        llm_client: Optional[LocalLLMClient] = None,
    ):
        if vector_store is None:
            self.vector_store = LocalVectorStore()
            self.vector_store.seed_default_sops()
        else:
            self.vector_store = vector_store

        self.llm_client = llm_client or LocalLLMClient()

    def generate_sop_guidance(
        self,
        description: str,
        category: Optional[str] = None,
        top_k: int = 5,
        incident_context: Optional[Dict[str, Any]] = None,
        debug: bool = False,
    ) -> Dict[str, Any]:
        """Retrieve relevant SOPs using smart multi-signal retrieval and synthesize field recommendations."""
        debug_output = {}

        # 1. Smart Vector Search with Multi-Signal Boosting
        search_results: List[Tuple[SOPDocument, float]] = []
        if hasattr(self.vector_store, "smart_search"):
            search_results, debug_output = self.vector_store.smart_search(
                query=description,
                incident_context=incident_context,
                top_k=top_k,
                debug=debug,
            )

        # Fallback to legacy search if smart_search yielded nothing
        if not search_results:
            search_results = self.vector_store.search(
                query=f"{category or ''} {description}".strip(),
                top_k=top_k,
                category_filter=category,
            )

        retrieved_docs: List[dict] = []
        sop_contexts: List[str] = []
        source_ids: List[str] = []

        for doc, score in search_results:
            source_ids.append(doc.doc_id)
            doc_meta = doc.metadata or {}
            retrieved_docs.append({
                "doc_id": doc.doc_id,
                "title": doc.title,
                "category": doc.category,
                "score": round(score, 4),
                "organization": doc_meta.get("organization", "Disaster Response Authority"),
                "section": doc_meta.get("section", "Standard Operational Procedure"),
                "page": doc_meta.get("page", 1),
                "publication_date": doc_meta.get("publication_date", "2024"),
                "source_url": doc_meta.get("source_url", ""),
                "priority": doc_meta.get("priority", "high"),
                "snippet": doc.content[:220] + "...",
            })
            sop_contexts.append(
                f"[{doc_meta.get('organization', 'NDMA')} — {doc.title}]\n"
                f"Section: {doc_meta.get('section', 'SOP')} (Page {doc_meta.get('page', 1)})\n"
                f"{doc.content}"
            )

        # Safety Guard: Check if retrieved SOP has sufficient relevance
        parsed = QueryParser.parse(description, incident_context) if QueryParser else None
        is_emergency = bool(parsed and (parsed.domains or parsed.substances or parsed.hazards or parsed.symptoms or parsed.intents))

        if not search_results or search_results[0][1] < 0.12 or (not is_emergency and search_results[0][1] < 0.30):
            no_info_msg = (
                "I don't have enough verified guidance in the local emergency SOP knowledge base to provide "
                "a specific procedure for that situation. Please consult the Incident Commander and verified field manuals."
            )
            res = {
                "incident_description": description,
                "category": category or "general",
                "retrieved_sops": [],
                "source_sop_ids": [],
                "recommendations": no_info_msg,
                "recommendation": no_info_msg,
            }
            if debug:
                res["debug"] = debug_output
            return res

        sop_context_text = "\n\n".join(sop_contexts)

        # 2. Prompt Construction
        incident_details = "None provided"
        if incident_context:
            parts = []
            if incident_context.get("title"):
                parts.append(f"Title: {incident_context['title']}")
            if incident_context.get("severity"):
                parts.append(f"Severity: {incident_context['severity']}")
            if incident_context.get("manualLocation"):
                parts.append(f"Location: {incident_context['manualLocation']}")
            if incident_context.get("description"):
                parts.append(f"Report: {incident_context['description']}")
            incident_details = " | ".join(parts)

        prompt = RAG_OPERATIONAL_PROMPT_TEMPLATE.format(
            sop_context=sop_context_text,
            category=category or "General Emergency",
            description=description,
            incident_details=incident_details,
        )

        # 3. LLM Generation (Local Phi-3 / Llama 3)
        llm_response = self.llm_client.generate(prompt)

        if llm_response and len(llm_response.strip()) > 30:
            recommendation_text = llm_response.strip()
        else:
            # High-Fidelity Grounded SOP Semantic Extraction Fallback (Air-Gapped / Zero-GPU Mode)
            best_doc, best_score = search_results[0]
            best_meta = best_doc.metadata or {}
            org = best_meta.get("organization", "NDMA")
            sec = best_meta.get("section", "Operational Directive")
            page = best_meta.get("page", 1)

            # Extract distinct numbered tactical steps
            raw_lines = [l.strip() for l in best_doc.content.split("\n") if l.strip()]
            action_lines = [l for l in raw_lines if re.match(r"^\d+\.\s+", l) or l.startswith(("-", "*"))]

            if len(action_lines) >= 3:
                steps_text = "\n".join(action_lines[:5])
            else:
                sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", best_doc.content) if s.strip()]
                steps_text = "\n".join(f"{idx}. {s}" for idx, s in enumerate(sentences[:4], 1))

            # Complementary safety notes from second chunk if available
            secondary_notes = ""
            if len(search_results) > 1:
                sec_doc, _ = search_results[1]
                sec_meta = sec_doc.metadata or {}
                sec_lines = [l.strip() for l in sec_doc.content.split("\n") if l.strip()]
                sec_actions = [l for l in sec_lines if re.match(r"^\d+\.\s+", l)]
                if sec_actions:
                    secondary_notes = f"\n\nRESPONDER SAFETY & CONTINGENCY ({sec_meta.get('section', 'Safety Directive')}):\n" + "\n".join(sec_actions[:2])

            # Verified sources citation
            sources_summary = "\n".join(
                f"- {d.metadata.get('organization', 'NDMA')} — {d.title} [Section: {d.metadata.get('section', 'SOP')}]"
                for d, _ in search_results[:3]
            )

            recommendation_text = (
                f"IMMEDIATE TACTICAL PRIORITIES ({org} — {sec}):\n\n"
                f"{steps_text}"
                f"{secondary_notes}\n\n"
                f"VERIFIED OFFLINE SOURCES:\n"
                f"{sources_summary}\n\n"
                f"Notice: Grounded extraction from ResQMesh offline emergency knowledge base."
            )

        response_dict = {
            "incident_description": description,
            "category": category or "general",
            "retrieved_sops": retrieved_docs,
            "source_sop_ids": source_ids,
            "recommendations": recommendation_text,
            "recommendation": recommendation_text,
        }

        if debug:
            response_dict["debug"] = debug_output

        return response_dict
