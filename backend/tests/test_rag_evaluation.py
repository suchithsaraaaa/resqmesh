"""
ResQMesh AI — 58-Question Golden RAG Evaluation Suite

Validates the expanded offline RAG retrieval pipeline against 58 realistic operational emergency questions:
- Medical & Trauma (Adult, Child, Infant CPR, Tourniquets, Crush syndrome, Snakebite, Burns)
- Fire (Structure, EV batteries, LPG BLEVE, PASS)
- Flood (Swiftwater hierarchy, Submerged cars)
- Earthquake (Drop/Cover/Hold, Aftershocks, Utilities)
- Structural Collapse (Voids, Shoring, Air-horn signals)
- Hazmat (Zoning, Level A-D PPE)
- Dedicated Substances (Chlorine, Ammonia, H2S, CO, LPG, Fuel)
- Radiological (Exposure vs Contamination, Shielding, Lost source)
- Search & Rescue (INSARAG X-code marking, Confined space)
- Evacuation (Contra-flow, Vulnerable groups, Shelters)
- Mass Casualty (START triage, JumpSTART pediatric triage)
- Disaster Communications (Radio discipline, ResQMesh P2P mesh relay, METHANE SITREP)
- Transport & Industrial (Train derailment, OHE 25kV wire safety, Pileup fend-off)
- Incident Command System (ICS, Span of control 1:5, Unified command)
- Resource Prioritization (Scarcity rationing, Ambulance dispatch)
- India Disaster Management Framework (NDMA, NDRF, DDMA Collector command)
- Dedicated Telangana & Hyderabad Knowledge (GHMC DRF, 18 Nalas, Musi river, Heat Wave ban, Patancheru/Bollaram)
- Cyclones (IMD 4-stage warnings, Storm surge)
- Out-of-domain safe guardrails (No hallucinated procedures)
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from backend.app.ai.rag_pipeline import RAGPipeline
except ImportError:
    from app.ai.rag_pipeline import RAGPipeline


GOLDEN_TEST_CASES = [
    # 1. HAZMAT — CHLORINE
    {
        "id": 1,
        "question": "What should responders prioritize during a chlorine leak in a railway station?",
        "expected_substance": "chlorine",
        "expected_keywords": ["chlorine", "toxic", "isolation", "plume", "heavier than air"],
        "expected_doc_ids": ["erg_chlorine_response_02"],
    },
    {
        "id": 2,
        "question": "Can we spray water on a leaking liquid chlorine cylinder?",
        "expected_substance": "chlorine",
        "expected_keywords": ["never spray water", "hydrochloric acid", "corrosive", "react"],
        "expected_doc_ids": ["erg_chlorine_response_02"],
    },
    # 2. HAZMAT — AMMONIA
    {
        "id": 3,
        "question": "How should responders handle an anhydrous ammonia tanker release?",
        "expected_substance": "ammonia",
        "expected_keywords": ["ammonia", "water fog", "irrigation", "caustic", "un1005"],
        "expected_doc_ids": ["erg_ammonia_response_03"],
    },
    # 3. HAZMAT — H2S
    {
        "id": 4,
        "question": "Why is hydrogen sulfide gas especially dangerous for sewer workers?",
        "expected_substance": "hydrogen_sulfide",
        "expected_keywords": ["olfactory fatigue", "loss of smell", "knockdown", "scba", "heavier than air"],
        "expected_doc_ids": ["erg_special_substances_04"],
    },
    # 4. HAZMAT — CARBON MONOXIDE
    {
        "id": 5,
        "question": "How should carbon monoxide poisoning victims be treated in the field?",
        "expected_substance": "carbon_monoxide",
        "expected_keywords": ["carbon monoxide", "oxygen", "pulse oximet", "hyperbaric", "carboxyhemoglobin"],
        "expected_doc_ids": ["erg_special_substances_04"],
    },
    # 5. HAZMAT — LPG / BLEVE
    {
        "id": 6,
        "question": "What are the key warning signs of an impending LPG tank BLEVE?",
        "expected_substance": "lpg",
        "expected_keywords": ["bleve", "unmanned monitor", "shriek", "relief valve", "cooling", "vapor space"],
        "expected_doc_ids": ["erg_special_substances_04"],
    },
    # 6. HAZMAT — FUEL SPILL
    {
        "id": 7,
        "question": "How should a massive gasoline tanker fuel spill be contained?",
        "expected_substance": "fuel",
        "expected_keywords": ["foam", "afff", "ignition", "vapor", "non-sparking", "dike"],
        "expected_doc_ids": ["erg_special_substances_04"],
    },
    # 7. HAZMAT — ZONING & PPE
    {
        "id": 8,
        "question": "What are the rules for establishing Hazmat Hot, Warm and Cold zones?",
        "expected_keywords": ["hot zone", "warm zone", "cold zone", "decontamination", "upwind", "uphill"],
        "expected_doc_ids": ["erg_hazmat_response_01"],
    },
    {
        "id": 9,
        "question": "When is Level A encapsulated suit mandatory for chemical response?",
        "expected_keywords": ["level a", "scba", "vapor-protective", "unknown", "skin-absorption"],
        "expected_doc_ids": ["erg_hazmat_response_01"],
    },
    # 8. RADIOLOGICAL
    {
        "id": 10,
        "question": "What is the difference between radiation exposure and radioactive contamination?",
        "expected_keywords": ["exposure", "contamination", "irradiated", "radioactive", "decontamination", "spread"],
        "expected_doc_ids": ["iaea_radiological_emergency_01"],
    },
    {
        "id": 11,
        "question": "What is the protection triad against ionizing radiation?",
        "expected_keywords": ["time", "distance", "shielding", "inverse square law"],
        "expected_doc_ids": ["iaea_radiological_emergency_01"],
    },
    {
        "id": 12,
        "question": "How should responders handle a lost industrial radiography source like Cesium-137?",
        "expected_keywords": ["100 meters", "isolation", "survey meter", "cesium", "shielded"],
        "expected_doc_ids": ["iaea_radiological_emergency_01"],
    },
    # 9. MEDICAL — BLEEDING & TOURNIQUET
    {
        "id": 13,
        "question": "Where and how should an arterial windlass tourniquet be applied on an injured limb?",
        "expected_keywords": ["tourniquet", "2 to 3 inches", "arterial", "joint", "windlass", "time"],
        "expected_doc_ids": ["ifrc_trauma_first_aid_01"],
    },
    {
        "id": 14,
        "question": "How should a responder stabilize a casualty in traumatic hemorrhagic shock?",
        "expected_keywords": ["shock", "bleeding", "hypothermia", "blanket", "supine", "oxygen"],
        "expected_doc_ids": ["ifrc_trauma_first_aid_01"],
    },
    # 10. MEDICAL — CPR & AED (ADULT, CHILD, INFANT)
    {
        "id": 15,
        "question": "What is the compression-to-ventilation ratio and depth for adult CPR?",
        "expected_keywords": ["30:2", "adult", "2.0 to 2.4", "100 to 120", "recoil"],
        "expected_doc_ids": ["aha_cpr_aed_protocols_02"],
    },
    {
        "id": 16,
        "question": "How does child CPR differ from adult CPR in compressions and depth?",
        "expected_keywords": ["child", "15:2", "30:2", "2 inches", "one-third"],
        "expected_doc_ids": ["aha_cpr_aed_protocols_02"],
    },
    {
        "id": 17,
        "question": "How should CPR be performed on an infant under 1 year of age?",
        "expected_keywords": ["infant", "two fingers", "encircling", "1.5 inches", "nipple line"],
        "expected_doc_ids": ["aha_cpr_aed_protocols_02"],
    },
    {
        "id": 18,
        "question": "How should a conscious choking infant be treated?",
        "expected_keywords": ["infant", "back slap", "chest thrust", "choking", "finger sweep"],
        "expected_doc_ids": ["aha_cpr_aed_protocols_02"],
    },
    {
        "id": 19,
        "question": "Where should AED pads be placed on an infant or small child?",
        "expected_keywords": ["aed", "pediatric", "anterior", "posterior", "touching"],
        "expected_doc_ids": ["aha_cpr_aed_protocols_02"],
    },
    # 11. MEDICAL — CRUSH SYNDROME & SPINAL
    {
        "id": 20,
        "question": "Why is pre-extrication IV hydration critical before lifting heavy debris off a trapped victim?",
        "expected_keywords": ["crush syndrome", "hydration", "reperfusion", "potassium", "renal failure", "myoglobin"],
        "expected_doc_ids": ["who_trauma_special_injuries_03"],
    },
    {
        "id": 21,
        "question": "What is the proper log-roll technique for spinal immobilization on a rigid backboard?",
        "expected_keywords": ["c-spine", "log-roll", "collar", "in-line", "alignment"],
        "expected_doc_ids": ["who_trauma_special_injuries_03"],
    },
    {
        "id": 22,
        "question": "What are the clinical signs of a base of skull fracture in head trauma?",
        "expected_keywords": ["battle's sign", "raccoon eyes", "csf", "head injury", "pupil"],
        "expected_doc_ids": ["who_trauma_special_injuries_03"],
    },
    # 12. MEDICAL — BURNS & SNAKEBITE
    {
        "id": 23,
        "question": "How should severe thermal and chemical burns be initially cooled and dressed?",
        "expected_keywords": ["burn", "cooling", "clean water", "never apply ice", "sterile dressing", "flushing"],
        "expected_doc_ids": ["who_trauma_special_injuries_03"],
    },
    {
        "id": 24,
        "question": "What is the first aid protocol for a venomous snakebite in India?",
        "expected_keywords": ["snakebite", "immobiliz", "anti-snake venom", "never cut", "never apply tourniquet", "pressure bandage"],
        "expected_doc_ids": ["who_trauma_special_injuries_03"],
    },
    {
        "id": 25,
        "question": "What is the immediate field emergency treatment for severe anaphylaxis?",
        "expected_keywords": ["anaphylaxis", "epinephrine", "adrenaline", "thigh", "intramuscular", "oxygen"],
        "expected_doc_ids": ["who_trauma_special_injuries_03"],
    },
    # 13. ENVIRONMENTAL EMERGENCIES
    {
        "id": 26,
        "question": "How do responders differentiate and treat heat stroke versus heat exhaustion?",
        "expected_keywords": ["heat stroke", "heat exhaustion", "ice-water", "temperature", "mental status", "cooling"],
        "expected_doc_ids": ["who_environmental_emergencies_04"],
    },
    {
        "id": 27,
        "question": "What is the primary resuscitation priority for submersion drowning victims?",
        "expected_keywords": ["drowning", "hypoxia", "rescue breaths", "cpr", "submersion"],
        "expected_doc_ids": ["who_environmental_emergencies_04"],
    },
    {
        "id": 28,
        "question": "How should a patient experiencing an active grand mal seizure be positioned?",
        "expected_keywords": ["seizure", "recovery position", "mouth", "protect", "airway"],
        "expected_doc_ids": ["who_environmental_emergencies_04"],
    },
    {
        "id": 29,
        "question": "How should diabetic hypoglycemia be managed in conscious and unconscious patients?",
        "expected_keywords": ["hypoglycemia", "diabetic", "glucose", "unconscious", "dextrose"],
        "expected_doc_ids": ["who_environmental_emergencies_04"],
    },
    # 14. STRUCTURAL COLLAPSE
    {
        "id": 30,
        "question": "What should we do if a building partially collapses and people are trapped?",
        "expected_keywords": ["collapse", "void", "shoring", "perimeter", "acoustic", "secondary collapse"],
        "expected_doc_ids": ["insarag_building_collapse_01"],
    },
    {
        "id": 31,
        "question": "What are the rules for box cribbing dimensions and load stabilization?",
        "expected_keywords": ["cribbing", "timber", "height", "3 times", "foundation"],
        "expected_doc_ids": ["insarag_building_collapse_01"],
    },
    {
        "id": 32,
        "question": "What emergency horn signals indicate immediate evacuation from a damaged structure?",
        "expected_keywords": ["air-horn", "three short blasts", "evacuation", "all clear", "one long blast"],
        "expected_doc_ids": ["insarag_building_collapse_01"],
    },
    # 15. MASS CASUALTY TRIAGE (START & JumpSTART)
    {
        "id": 33,
        "question": "How does the START triage protocol categorize casualties using the 30-2-Can Do rule?",
        "expected_keywords": ["start triage", "respiration", "30", "radial pulse", "can do", "red", "yellow", "green", "black"],
        "expected_doc_ids": ["who_start_triage_01"],
    },
    {
        "id": 34,
        "question": "What is the 5 rescue breaths exception in the JumpSTART pediatric triage system?",
        "expected_keywords": ["jumpstart", "pediatric", "rescue breaths", "pulse", "apneic", "child"],
        "expected_doc_ids": ["who_start_triage_01"],
    },
    # 16. RESOURCE ALLOCATION
    {
        "id": 35,
        "question": "We have 30 casualties and only two ambulances. How should we prioritize?",
        "expected_keywords": ["life-safety", "red immediate", "transport", "prioritize", "ambulance"],
        "expected_doc_ids": ["ndma_resource_prioritization_01"],
    },
    # 17. FLOOD & SWIFTWATER
    {
        "id": 36,
        "question": "What is the low-to-high risk hierarchy for swiftwater rescue?",
        "expected_keywords": ["talk", "reach", "throw", "row", "go", "helo", "pfd", "swiftwater"],
        "expected_doc_ids": ["ndma_flood_sop_01"],
    },
    {
        "id": 37,
        "question": "Why is driving through flooded roads hazardous and how much water sweeps away a car?",
        "expected_keywords": ["turn around", "flooded", "12 inches", "24 inches", "submerged", "vehicle"],
        "expected_doc_ids": ["ndma_flood_sop_01"],
    },
    # 18. FIRE
    {
        "id": 38,
        "question": "What are the warning signs of rollover, flashover, and backdraft in structure fires?",
        "expected_keywords": ["flashover", "backdraft", "rollover", "smoke", "ceiling", "withdrawal"],
        "expected_doc_ids": ["usfa_structural_fire_01"],
    },
    {
        "id": 39,
        "question": "What is the PASS method for portable fire extinguishers?",
        "expected_keywords": ["pass", "pull", "aim", "squeeze", "sweep", "base of fire"],
        "expected_doc_ids": ["usfa_structural_fire_01"],
    },
    {
        "id": 40,
        "question": "How should an electric vehicle (EV) battery fire in thermal runaway be extinguished?",
        "expected_keywords": ["ev battery", "thermal runaway", "copious water", "lithium-ion", "undercarriage"],
        "expected_doc_ids": ["usfa_structural_fire_01"],
    },
    # 19. SEARCH AND RESCUE MARKING
    {
        "id": 41,
        "question": "What information is recorded in the four quadrants of the FEMA/INSARAG structural search marking X-box?",
        "expected_keywords": ["x-code", "quadrant", "team", "hazards", "victims", "date", "time"],
        "expected_doc_ids": ["ndrf_sar_operations_01"],
    },
    {
        "id": 42,
        "question": "What are the mandatory precautions before entering a confined space for rescue?",
        "expected_keywords": ["confined space", "ventilation", "atmospheric", "harness", "tripod", "oxygen"],
        "expected_doc_ids": ["ndrf_sar_operations_01"],
    },
    # 20. DISASTER COMMUNICATIONS
    {
        "id": 43,
        "question": "How should the team communicate if cellular networks are down?",
        "expected_keywords": ["mesh", "relay", "resqmesh", "plain language", "sitrep", "radio"],
        "expected_doc_ids": ["resqmesh_emergency_comms_01"],
    },
    {
        "id": 44,
        "question": "What are the 7 components of the METHANE emergency situation report format?",
        "expected_keywords": ["methane", "major incident", "exact location", "type", "hazards", "access", "casualties", "emergency services"],
        "expected_doc_ids": ["resqmesh_emergency_comms_01"],
    },
    # 21. TRANSPORT & RAIL ACCIDENTS
    {
        "id": 45,
        "question": "What electrical hazard must be isolated before touching a derailed passenger train?",
        "expected_keywords": ["overhead traction", "ohe", "25kv", "power", "railway", "derailment"],
        "expected_doc_ids": ["mha_transport_industrial_sop_01"],
    },
    {
        "id": 46,
        "question": "How should emergency vehicles be positioned during a multi-vehicle highway pileup?",
        "expected_keywords": ["fend-off", "45 degrees", "taper", "traffic", "highway"],
        "expected_doc_ids": ["mha_transport_industrial_sop_01"],
    },
    # 22. INCIDENT COMMAND
    {
        "id": 47,
        "question": "What is the recommended span of control in the Incident Command System?",
        "expected_keywords": ["span of control", "3 to 7", "optimum 5", "incident commander", "branches"],
        "expected_doc_ids": ["mha_incident_response_system_01"],
    },
    {
        "id": 48,
        "question": "When is Unified Command established under the Incident Response System?",
        "expected_keywords": ["unified command", "multi-agency", "shared", "objectives", "jurisdiction"],
        "expected_doc_ids": ["mha_incident_response_system_01"],
    },
    # 23. INDIA DISASTER FRAMEWORK
    {
        "id": 49,
        "question": "Who is the statutory Incident Commander at the district operational level in India?",
        "expected_keywords": ["district collector", "district magistrate", "ddma", "dm act 2005", "collector"],
        "expected_doc_ids": ["ndma_india_framework_01"],
    },
    {
        "id": 50,
        "question": "What is the organizational role of the National Disaster Response Force (NDRF)?",
        "expected_keywords": ["ndrf", "battalions", "cbrn", "usar", "specialized", "federal"],
        "expected_doc_ids": ["ndma_india_framework_01"],
    },
    # 24. TELANGANA & HYDERABAD KNOWLEDGE
    {
        "id": 51,
        "question": "How should we respond to urban flooding in Hyderabad?",
        "expected_keywords": ["hyderabad", "ghmc", "drf", "nalas", "musi", "begumpet", "flooding"],
        "expected_doc_ids": ["telangana_disaster_framework_01"],
    },
    {
        "id": 52,
        "question": "What actions are triggered when Hussainsagar lake reaches Full Tank Level in Hyderabad?",
        "expected_keywords": ["hussainsagar", "full tank level", "sluice", "musi river", "chaderghat", "downstream"],
        "expected_doc_ids": ["telangana_disaster_framework_01"],
    },
    {
        "id": 53,
        "question": "What work restrictions are enforced during Red Alert heatwaves in Telangana?",
        "expected_keywords": ["telangana", "heat wave", "12:00 pm", "3:00 pm", "prohibited", "ors", "chalivendram"],
        "expected_doc_ids": ["telangana_disaster_framework_01"],
    },
    {
        "id": 54,
        "question": "What hazardous chemical clusters exist in the Patancheru and Bollaram industrial corridor?",
        "expected_keywords": ["patancheru", "bollaram", "chemical", "pharma", "solvent", "chlorine", "tsdm"],
        "expected_doc_ids": ["telangana_disaster_framework_01"],
    },
    # 25. EARTHQUAKE
    {
        "id": 55,
        "question": "What are the immediate priorities during an earthquake ground tremor?",
        "expected_keywords": ["drop", "cover", "hold", "utility", "gas", "aftershock"],
        "expected_doc_ids": ["ndma_earthquake_sop_01"],
    },
    # 26. EVACUATION & SHELTERS
    {
        "id": 56,
        "question": "What SPHERE standards govern emergency temporary relief shelters?",
        "expected_keywords": ["sphere", "3.5 square meters", "15 liters", "latrine", "shelter", "water"],
        "expected_doc_ids": ["ndma_evacuation_sop_01"],
    },
    # 27. CYCLONES
    {
        "id": 57,
        "question": "What are the four warning stages issued by IMD for cyclonic storms?",
        "expected_keywords": ["imd", "cyclone", "pre-cyclone watch", "yellow alert", "orange", "red alert", "storm surge"],
        "expected_doc_ids": ["imd_cyclone_warning_sop_01"],
    },
    # 28. NUCLEAR DISASTER PROTOCOLS (AERB / IAEA / BARC)
    {
        "id": 58,
        "question": "What are the emergency classifications and cordon zones around a nuclear power plant?",
        "expected_keywords": ["aerb", "iaea", "exclusion zone", "sterilised zone", "epz", "general emergency"],
        "expected_doc_ids": ["aerb_nuclear_emergency_sop_01"],
    },
    {
        "id": 59,
        "question": "How is potassium iodide KI administered for thyroid blocking during radiation release?",
        "expected_keywords": ["potassium iodide", "ki", "130 mg", "thyroid", "iodine-131", "65 mg"],
        "expected_doc_ids": ["aerb_nuclear_emergency_sop_01"],
    },
    # 29. LANDSLIDES & DEBRIS FLOWS
    {
        "id": 60,
        "question": "What are the geological warning signs and immediate evacuation steps for an imminent landslide?",
        "expected_keywords": ["landslide", "tension cracks", "bulging", "muddy springs", "evacuate"],
        "expected_doc_ids": ["ndma_landslide_sop_01"],
    },
    # 30. INDUSTRIAL DISASTERS & EXPLOSIONS
    {
        "id": 61,
        "question": "What is the emergency protocol for an industrial boiler explosion and invisible superheated steam?",
        "expected_keywords": ["boiler", "explosion", "steam", "broom", "standoff", "exclusion zone"],
        "expected_doc_ids": ["ndma_industrial_disaster_sop_01"],
    },
    {
        "id": 62,
        "question": "How to prevent secondary industrial combustible dust explosions?",
        "expected_keywords": ["dust explosion", "dust pentagon", "secondary", "combustible dust", "fog"],
        "expected_doc_ids": ["ndma_industrial_disaster_sop_01"],
    },
    # 31. BIOLOGICAL EMERGENCIES & OUTBREAKS
    {
        "id": 63,
        "question": "What are the PPE donning and doffing sequences for high-consequence biological pathogens?",
        "expected_keywords": ["biological", "donning", "doffing", "n95", "gloves", "respirator"],
        "expected_doc_ids": ["who_epidemic_containment_sop_01"],
    },
    # 32. DISASTER LOGISTICS & SUPPLY CHAIN
    {
        "id": 64,
        "question": "How should an incident staging area and medical cold-chain fuel rationing be organized?",
        "expected_keywords": ["staging area", "cold chain", "fifo", "rationing", "generator", "fuel"],
        "expected_doc_ids": ["ndma_disaster_logistics_sop_01"],
    },
    # 33. PUBLIC HEALTH & WATER SANITATION
    {
        "id": 65,
        "question": "What is the procedure for emergency drinking water chlorination and latrine construction?",
        "expected_keywords": ["chlorine", "residual chlorine", "sphere", "latrine", "15 liters", "0.5 mg/l"],
        "expected_doc_ids": ["who_disaster_sanitation_sop_01"],
    },
    # 34. OUT-OF-DOMAIN SAFETY GUARDRAIL
    {
        "id": 66,
        "question": "What stocks should I invest in to make money in the stock market?",
        "expected_keywords": ["don't have enough verified guidance", "knowledge base"],
        "is_out_of_domain": True,
    },
]


@pytest.fixture(scope="module")
def rag_pipeline():
    return RAGPipeline()


@pytest.mark.parametrize("tc", GOLDEN_TEST_CASES, ids=[f"TC{tc['id']:02d}-{tc['question'][:30]}" for tc in GOLDEN_TEST_CASES])
def test_golden_rag_retrieval(rag_pipeline, tc):
    result = rag_pipeline.generate_sop_guidance(
        description=tc["question"],
        top_k=5,
        debug=True,
    )

    rec = result.get("recommendations", "").lower()
    retrieved = result.get("retrieved_sops", [])

    if tc.get("is_out_of_domain"):
        assert "don't have enough verified guidance" in rec or "consult" in rec
        return

    # 1. Verify that relevant documents were retrieved
    assert len(retrieved) > 0, f"No SOPs retrieved for question: {tc['question']}"

    # 2. Verify expected document is among top retrieved
    if "expected_doc_ids" in tc:
        retrieved_ids = [d["doc_id"] for d in retrieved]
        matched_doc = any(any(exp_id in r_id for exp_id in tc["expected_doc_ids"]) for r_id in retrieved_ids)
        assert matched_doc, f"Expected doc in {tc['expected_doc_ids']} but got {retrieved_ids} for: {tc['question']}"

    # 3. Verify content keywords appear in synthesized recommendation or top chunk
    all_text = (rec + " " + " ".join(d.get("snippet", "") for d in retrieved)).lower()
    matched_keywords = [kw for kw in tc.get("expected_keywords", []) if kw in all_text]
    assert len(matched_keywords) >= 1, f"None of keywords {tc.get('expected_keywords')} matched in response for: {tc['question']}"

    # 4. Verify verified offline sources are displayed
    assert len(result.get("retrieved_sops", [])) > 0
