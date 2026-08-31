"""
ResQMesh AI — Deterministic Query Understanding & Intent Extraction Engine

Extracts structured operational context from user queries and incident context:
- Incident Domain & Subdomain
- Hazards & Substances (e.g. chlorine, ammonia, H2S, LPG, radiation)
- Location & Environment (e.g. railway station, hospital, industrial, high-rise, underground)
- Geographic Context (India, Telangana, Hyderabad)
- Responder Role / Audience (responder, commander, triage/medical, logistics)
- Operational Intent (immediate priorities, isolation distance, decontamination, triage, evacuation, etc.)

Zero neural overhead: runs deterministically in < 1ms using tokenized pattern maps.
"""

import re
from typing import Dict, List, Optional, Set, Any

# Domain keyword mapping
DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "hazmat": [
        "chemical", "hazmat", "toxic", "gas", "plume", "spill", "leak", "chlorine",
        "ammonia", "h2s", "hydrogen sulfide", "sulfur", "co", "carbon monoxide", "acid",
        "corrosive", "bleve", "solvent", "un1017", "un1005", "un1053", "un1075", "level a",
        "decontamination", "decon", "hot zone", "warm zone", "vapor", "scba", "placard"
    ],
    "radiological": [
        "radiation", "radiological", "nuclear", "radioactive", "contamination", "cesium",
        "cobalt", "iridium", "alpha", "beta", "gamma", "sievert", "roentgen", "rad",
        "geiger", "dosimeter", "shielding", "half-life", "dirty bomb"
    ],
    "medical": [
        "medical", "first aid", "bleeding", "hemorrhage", "tourniquet", "cpr", "aed",
        "airway", "choking", "shock", "burn", "burns", "fracture", "splint", "c-spine",
        "spinal", "head injury", "concussion", "crush", "amputation", "eye injury",
        "poison", "hypothermia", "heat stroke", "heat exhaustion", "drowning", "snakebite",
        "anaphylaxis", "epinephrine", "seizure", "diabetic", "hypoglycemia", "chest injury",
        "infant", "child", "pediatric", "adult", "compression"
    ],
    "fire": [
        "fire", "blaze", "smoke", "wildfire", "forest fire", "structure fire", "high-rise fire",
        "flashover", "backdraft", "extinguisher", "class a", "class b", "class c", "lpg fire",
        "vehicle fire", "ev battery", "firefighter", "thermal runaway"
    ],
    "flood": [
        "flood", "flooding", "flooded", "flash flood", "inundation", "swiftwater", "river", "dam breach",
        "levee", "water rescue", "rescue boat", "irb", "submerged", "culvert", "drowning",
        "nala", "musi", "waterlogging", "rainstorm", "water sweeps"
    ],
    "earthquake": [
        "earthquake", "seismic", "aftershock", "tremor", "fault", "drop cover hold",
        "richter", "magnitude", "liquefaction", "ground rupture"
    ],
    "structural_collapse": [
        "collapse", "building collapse", "rubble", "void", "voids", "pancake collapse",
        "lean-to", "shoring", "cribbing", "acoustic listening", "geophone", "trapped",
        "usar", "insarag", "heavy rescue", "structural triage", "compromised structure",
        "damaged structure", "horn signals", "air-horn", "structural"
    ],
    "search_and_rescue": [
        "search and rescue", "sar", "usar", "canine", "k9", "missing person", "extrication",
        "confined space", "rope rescue", "victim marking", "fema marking", "x-code", "hasty search"
    ],
    "mass_casualty": [
        "mass casualty", "mci", "casualty", "casualties", "triage", "start triage", "jumpstart", "salt triage",
        "casualty collection", "ccp", "triage tag", "red immediate", "yellow delayed",
        "green minor", "black deceased", "surge capacity", "triage officer", "multiple victims"
    ],
    "evacuation": [
        "evacuate", "evacuation", "shelter-in-place", "shelter in place", "egress",
        "assembly point", "evacuation route", "traffic control", "contra-flow",
        "vulnerable population", "elderly evacuation", "relief shelter", "shelter", "shelters", "sphere"
    ],
    "disaster_communications": [
        "communication", "communications", "communicate", "communicating", "radio", "mesh", "resqmesh", "packet",
        "relay", "network down", "cellular down", "cellular", "offline comms", "sitrep", "emergency alert",
        "node failure", "ten-code", "plain language", "methane", "situation report"
    ],
    "transport_industrial": [
        "derailment", "derailed", "train crash", "train", "passenger train", "railway", "rail", "pileup", "vehicle collision",
        "highway", "freight train", "industrial accident", "machinery", "factory explosion",
        "arc flash", "fend-off", "ohe", "traction wire", "overhead wire"
    ],
    "incident_command": [
        "incident command", "ics", "incident commander", "unified command", "span of control",
        "safety officer", "operations section", "planning section", "logistics section",
        "command post", "icp", "incident action plan", "iap", "operational period"
    ],
    "resource_prioritization": [
        "resource prioritization", "scarce resource", "rationing", "prioritize ambulance",
        "prioritize supplies", "generator allocation", "resource triage", "ambulance", "ambulances",
        "resource allocation", "limited resources", "equipment shortage"
    ],
    "india_framework": [
        "ndma", "ndrf", "sdma", "ddma", "disaster management act", "irs", "incident response system",
        "imd", "mha", "national disaster"
    ],
    "telangana_framework": [
        "telangana", "hyderabad", "tsdma", "ghmc", "drf", "ev&dm", "hussain sagar", "musi river",
        "patancheru", "bollaram", "jeedimetla", "nacharam", "pashamylaram", "secunderabad",
        "outer ring road", "orr", "nala", "heat action plan"
    ],
    "nuclear_disaster": [
        "nuclear", "radiation", "reactor", "meltdown", "fallout", "plume", "potassium iodide",
        "ki", "ki tablets", "aerb", "barc", "iaea", "iodine 131", "dirty bomb", "thyroid protection",
        "exclusion zone", "sterilised zone", "epz", "dosimeter"
    ],
    "landslides": [
        "landslide", "mudflow", "debris flow", "slope instability", "tension cracks", "mudslide",
        "rockfall", "slope failure", "bulging slope", "muddy springs"
    ],
    "industrial_disaster": [
        "boiler explosion", "dust explosion", "pressure vessel", "steam explosion", "factory explosion",
        "industrial explosion", "combustible dust", "dust pentagon"
    ],
    "biological_emergency": [
        "epidemic", "outbreak", "infectious disease", "quarantine", "isolation zone", "pathogen",
        "droplet", "airborne", "biological ppe", "biohazard", "biohazard waste"
    ],
    "disaster_logistics": [
        "staging area", "warehouse", "supply chain", "cold chain", "fuel rationing", "relief supplies",
        "marshalling yard", "cargo", "fifo inventory"
    ],
    "public_health": [
        "water purification", "chlorination", "residual chlorine", "sanitation", "latrines",
        "excreta disposal", "potable water", "wash", "free residual chlorine", "bleaching powder"
    ],
}

# Substance-specific patterns
SUBSTANCE_PATTERNS: Dict[str, List[str]] = {
    "chlorine": ["chlorine", "un1017", "un 1017", "choking gas", "yellow-green gas", "yellowish-green"],
    "ammonia": ["ammonia", "nh3", "un1005", "un 1005", "anhydrous ammonia", "fertilizer gas"],
    "hydrogen_sulfide": ["hydrogen sulfide", "h2s", "un1053", "un 1053", "sewer gas", "rotten egg gas"],
    "carbon_monoxide": ["carbon monoxide", "co", "un1016", "un 1016", "silent killer", "carboxyhemoglobin"],
    "lpg": ["lpg", "liquefied petroleum gas", "propane", "butane", "un1075", "un 1075", "gas cylinder"],
    "fuel": ["fuel spill", "gasoline", "diesel", "petrol", "kerosene", "hydrocarbon", "un1203", "un 1203"],
    "acid": ["sulfuric acid", "hydrochloric acid", "nitric acid", "battery acid", "corrosive liquid"],
    "radiation": ["cesium", "cobalt", "iridium", "nuclear material", "radioactive source", "spent fuel", "fallout"],
    "potassium_iodide": ["potassium iodide", "ki tablets", "ki", "stable iodine"],
    "iodine_131": ["iodine 131", "i-131", "radioactive iodine"],
}

# Specific environment patterns
ENVIRONMENT_PATTERNS: Dict[str, List[str]] = {
    "railway": ["railway", "rail", "train", "station", "locomotive", "track", "platform"],
    "industrial": ["factory", "plant", "refinery", "warehouse", "chemical facility", "siding", "industrial"],
    "hospital": ["hospital", "clinic", "icu", "ward", "medical center"],
    "high_rise": ["high-rise", "multi-story", "skyscraper", "apartment building", "stairwell"],
    "underground": ["underground", "tunnel", "subway", "metro", "basement", "sewer"],
    "urban": ["urban", "city", "downtown", "street", "colony", "residential"],
    "water": ["river", "lake", "canal", "nala", "ocean", "sea", "coastal"],
}

# Specific symptom patterns
SYMPTOM_PATTERNS: Dict[str, List[str]] = {
    "respiratory_distress": ["breathing difficulty", "trouble breathing", "shortness of breath", "choking", "asphyxiation", "respiratory distress", "coughing"],
    "severe_bleeding": ["bleeding", "hemorrhage", "arterial spurting", "blood loss", "wound"],
    "unconscious": ["unconscious", "unresponsive", "fainted", "collapsed", "altered consciousness", "coma"],
    "burns": ["burn", "burns", "scald", "chemical burn", "blisters", "charred"],
    "crush": ["crush", "pinned", "trapped under debris", "compartment syndrome"],
    "anaphylaxis": ["anaphylaxis", "anaphylactic", "epinephrine", "adrenaline", "severe allergy", "allergic reaction"],
}

# Operational intent patterns
INTENT_PATTERNS: Dict[str, List[str]] = {
    "immediate_priorities": ["what should", "prioritize", "first step", "immediate", "what to do", "initial action", "protocol", "how to handle"],
    "isolation_distance": ["isolation distance", "how far", "perimeter", "protective action", "exclusion zone", "standoff"],
    "decontamination": ["decontamination", "decon", "wash", "strip clothing", "neutralize"],
    "triage": ["triage", "sort", "prioritize casualties", "who to treat", "mass casualty"],
    "evacuation": ["evacuate", "evacuation route", "shelter in place", "shelter-in-place", "leave"],
    "safety": ["responder safety", "ppe", "protective equipment", "safety precaution", "hazards to rescuers"],
}


class ParsedQuery:
    """Structured extraction of user query and operational context."""

    def __init__(self, raw_query: str):
        self.raw_query: str = raw_query
        self.domains: List[str] = []
        self.substances: List[str] = []
        self.hazards: List[str] = []
        self.environments: List[str] = []
        self.symptoms: List[str] = []
        self.intents: List[str] = []
        self.audience: str = "responder"
        self.regions: List[str] = []
        self.age_groups: List[str] = []
        self.key_terms: Set[str] = set()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_query": self.raw_query,
            "domains": self.domains,
            "substances": self.substances,
            "hazards": self.hazards,
            "environments": self.environments,
            "symptoms": self.symptoms,
            "intents": self.intents,
            "audience": self.audience,
            "regions": self.regions,
            "age_groups": self.age_groups,
            "key_terms": list(self.key_terms),
        }


class QueryParser:
    """Fast, deterministic NLP parser extracting incident attributes from queries."""

    @classmethod
    def parse(cls, query: str, incident_context: Optional[Dict[str, Any]] = None) -> ParsedQuery:
        parsed = ParsedQuery(query)

        # Merge incident context if available
        combined_text = query.lower()
        if incident_context:
            title = str(incident_context.get("title", "")).lower()
            cat = str(incident_context.get("category", "")).lower()
            desc = str(incident_context.get("description", "")).lower()
            loc = str(incident_context.get("manualLocation", "")).lower()
            combined_text = f"{combined_text} {title} {cat} {desc} {loc}".strip()

        # 1. Detect Substances (strict word boundary)
        for substance, patterns in SUBSTANCE_PATTERNS.items():
            if any(re.search(r"\b" + re.escape(p) + r"\b", combined_text) for p in patterns):
                parsed.substances.append(substance)
                parsed.key_terms.add(substance)

        # 2. Detect Domains (strict word boundary)
        for domain, keywords in DOMAIN_KEYWORDS.items():
            matched_count = sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", combined_text))
            if matched_count > 0:
                parsed.domains.append(domain)

        # Ensure substance maps to hazmat / radiological domain
        if any(s in parsed.substances for s in ["chlorine", "ammonia", "hydrogen_sulfide", "carbon_monoxide", "lpg", "fuel", "acid"]):
            if "hazmat" not in parsed.domains:
                parsed.domains.insert(0, "hazmat")
        if "radiation" in parsed.substances and "radiological" not in parsed.domains:
            parsed.domains.insert(0, "radiological")

        # 3. Detect Environments (strict word boundary)
        for env, patterns in ENVIRONMENT_PATTERNS.items():
            if any(re.search(r"\b" + re.escape(p) + r"\b", combined_text) for p in patterns):
                parsed.environments.append(env)

        # 4. Detect Symptoms (strict word boundary)
        for sym, patterns in SYMPTOM_PATTERNS.items():
            if any(re.search(r"\b" + re.escape(p) + r"\b", combined_text) for p in patterns):
                parsed.symptoms.append(sym)
                parsed.key_terms.add(sym)

        # 5. Detect Intents (strict word boundary)
        for intent, patterns in INTENT_PATTERNS.items():
            if any(re.search(r"\b" + re.escape(p) + r"\b", combined_text) for p in patterns):
                parsed.intents.append(intent)

        # 6. Detect Regions
        if any(w in combined_text for w in ["hyderabad", "secunderabad", "hussain sagar", "musi", "ghmc", "charminar", "hitec"]):
            parsed.regions.append("hyderabad")
            parsed.regions.append("telangana")
        elif any(w in combined_text for w in ["telangana", "warangal", "nizamabad", "karimnagar"]):
            parsed.regions.append("telangana")
        if any(w in combined_text for w in ["india", "ndma", "ndrf"]):
            parsed.regions.append("india")

        # 7. Detect Age Groups
        if any(w in combined_text for w in ["infant", "baby", "newborn"]):
            parsed.age_groups.append("infant")
        elif any(w in combined_text for w in ["child", "pediatric", "kid"]):
            parsed.age_groups.append("child")
        elif any(w in combined_text for w in ["adult", "elderly", "geriatric"]):
            parsed.age_groups.append("adult")

        # 8. Detect Audience / Role
        if any(w in combined_text for w in ["commander", "ic", "incident command", "command post", "dispatch"]):
            parsed.audience = "commander"
        elif any(w in combined_text for w in ["doctor", "paramedic", "ems", "nurse", "triage officer"]):
            parsed.audience = "medical"
        elif any(w in combined_text for w in ["public", "citizen", "resident", "civilian"]):
            parsed.audience = "public"
        else:
            parsed.audience = "responder"

        # 9. Extract Significant Non-Stop Key Terms
        stop_words = {
            "what", "should", "responders", "prioritize", "during", "after", "before", "the", "and",
            "for", "with", "how", "can", "they", "are", "there", "some", "people", "near", "from"
        }
        raw_words = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", query.lower())
        for w in raw_words:
            if w not in stop_words:
                parsed.key_terms.add(w)

        return parsed
