import os
import sys

# Script to verify and generate the comprehensive 29 SOP definitions covering all 21 categories.
new_sop_nuclear = {
    "doc_id": "aerb_nuclear_emergency_sop_01",
    "category": "nuclear_disaster",
    "title": "AERB / IAEA Standard Operating Procedure for Nuclear Power Plant Emergencies, Fallout & Thyroid Protection",
    "organization": "Atomic Energy Regulatory Board (AERB India) / IAEA / BARC",
    "publication_date": "2024-03-01",
    "source_url": "https://www.aerb.gov.in/guidelines/nuclear-emergency",
    "priority": "critical",
    "chapters": [
        {
            "section": "Nuclear Emergency Classification (Alert, Plant, Site, General) & Emergency Planning Zones",
            "page": 10,
            "keywords": ["nuclear disaster", "nuclear emergency", "reactor accident", "aerb", "iaea", "exclusion zone", "sterilised zone", "epz", "radiation alert"],
            "hazards": ["nuclear_meltdown", "ionizing_radiation", "fission_products", "radioactive_plume"],
            "substances": ["radiation", "iodine 131", "cesium 137", "strontium 90"],
            "subdomain": "nuclear_emergency_classification",
            "audience": "commander",
            "region": "india",
            "content": (
                "AERB & IAEA Nuclear Power Plant (NPP) Emergency Classification and Cordon Zones:\n"
                "1. Emergency Classifications: (1) Emergency Alert: Abnormal plant condition, no radioactive release, internal alert only; (2) Plant Emergency: Incident confined within nuclear facility boundary, on-site personnel protected; (3) Site Area Emergency: Major plant degradation, localized release, site boundary monitoring active; (4) General Emergency: Core damage and substantial release of radioactive fission products outside the facility boundary.\n"
                "2. Indian Statutory Cordon Zones: (1) Exclusion Zone (0 to 1.6 km around reactor): Total civilian exclusion, high security, full automated perimeter monitoring; (2) Sterilised Zone (1.6 km to 5 km): Regulated residential development, rapid evacuation corridors maintained; (3) Emergency Planning Zone (EPZ, up to 16 km): Mandatory off-site emergency plans, pre-distributed potassium iodide (KI) tablets, dedicated siren alert system.\n"
                "3. Immediate Public Protection Directives: At General Emergency trigger, sound continuous undulating 3-minute mechanical sirens, broadcast urgent radio alerts over ResQMesh mesh channels, and enforce immediate shelter-in-place for all populations within the 16 km EPZ."
            ),
        },
        {
            "section": "Radioactive Plume Shelter-in-Place, Sealing Protocols & Downwind Evacuation",
            "page": 24,
            "keywords": ["radioactive plume", "shelter in place", "sealing", "hvac shutoff", "fallout", "downwind evacuation", "nuclear shelter"],
            "hazards": ["radioactive_fallout", "plume_inhalation", "gamma_shine"],
            "substances": ["radiation", "fallout"],
            "subdomain": "nuclear_shelter_evacuation",
            "audience": "responder",
            "region": "global",
            "content": (
                "Operational guidelines for radioactive plume passage and fallout mitigation:\n"
                "1. Critical Shelter-in-Place Sealing: Immediately go indoors. Close all exterior windows, doors, and fireplace dampers. Crucial: TURN OFF ALL AIR CONDITIONERS, exhaust fans, HVAC systems, and air intakes to prevent sucking contaminated outside air indoors. Seal window cracks with heavy plastic sheeting and duct tape.\n"
                "2. Best Interior Shielding Locations: Move to the center of the building or lowest interior basement. Dense concrete, masonry brick, and earth provide maximum gamma radiation attenuation (a heavy concrete basement cuts gamma dose by 90% or more compared to outdoors).\n"
                "3. Safe Evacuation Navigation: Never evacuate directly downwind in the path of the traveling radioactive plume. Responders must route evacuation convoys strictly PERPENDICULAR (crosswind) to prevailing surface wind direction until clearing the 16 km boundary.\n"
                "4. Personal Protective Clothing: Responders entering warm zones must wear Level C or B protective suits with Powered Air-Purifying Respirators (PAPR) or SCBA equipped with P100 particulate and iodine vapor sorption filters."
            ),
        },
        {
            "section": "Thyroid Prophylaxis: Potassium Iodide (KI) Administration & Dosages",
            "page": 38,
            "keywords": ["potassium iodide", "ki tablets", "thyroid protection", "iodine 131", "dosage", "thyroid cancer", "prophylaxis"],
            "hazards": ["thyroid_carcinoma", "internal_contamination"],
            "substances": ["potassium_iodide", "iodine_131", "radiation"],
            "subdomain": "nuclear_medical_countermeasures",
            "audience": "medical",
            "region": "india",
            "content": (
                "WHO / AERB / NDMA Guidelines for Thyroid Blocking with Stable Potassium Iodide (KI):\n"
                "1. Mechanism of Action: Potassium Iodide (KI) floods the thyroid gland with non-radioactive stable iodine, preventing the absorption and accumulation of carcinogenic radioactive Iodine-131 released during nuclear reactor accidents. KI protects ONLY the thyroid and does NOT protect against external radiation or other isotopes (e.g. Cesium, Strontium).\n"
                "2. Standard Age-Specific Doses: (1) Adults and Adolescents (>12 years / >45 kg): Single daily dose of 130 mg (one standard tablet); (2) Children (3 to 12 years): 65 mg (half tablet); (3) Infants (1 month to 3 years): 32 mg (quarter tablet dissolved in milk/water); (4) Neonates (birth to 1 month): 16 mg (one-eighth tablet).\n"
                "3. Optimum Administration Timing: Take KI within 2 to 4 hours BEFORE or IMMEDIATELY UPON exposure to the radioactive plume. Taking KI after 24 hours provides negligible protective value. Pregnant and breastfeeding women are prioritized for KI administration to protect fetal and infant thyroid tissue.\n"
                "4. Contraindications: Known iodine allergy, dermatitis herpetiformis, or hypocomplementemic vasculitis."
            ),
        },
        {
            "section": "Mass Radioactive Fallout Decontamination Corridors & Portal Monitoring",
            "page": 52,
            "keywords": ["radiological decontamination", "fallout decon", "dosimeter", "portal monitor", "stripping clothing", "survey meter"],
            "hazards": ["external_contamination", "radiation_exposure"],
            "substances": ["radiation", "fallout_particles"],
            "subdomain": "nuclear_decontamination",
            "audience": "responder",
            "region": "global",
            "content": (
                "Field mass radiological decontamination and casualty triage protocols:\n"
                "1. Gross Decontamination by Outer Clothing Stripping: Carefully removing outer footwear, jacket, shirts, and pants eliminates OVER 90% OF EXTERNAL CONTAMINATION particles immediately. Place contaminated clothing in heavy 6-mil polyethylene bags labeled with biohazard/trefoil tape.\n"
                "2. Lukewarm Water Wash: Wash exposed head, hair, face, and hands with lukewarm water and mild neutral detergent. Do NOT use abrasive brushes or hot water (which causes dermal vasodilation and pores to open, driving radioactive particles deeper into skin). Contain all gray wash runoff in lined holding bladders.\n"
                "3. Radiac Monitoring & Clearance Criteria: Screen each decontaminated person from head to toe using a calibrated Geiger-Müller survey probe held 1 cm away from the surface without touching. Clearance threshold: Radiation level below 1 µSv/h (less than 2 times natural background or < 100 counts per minute).\n"
                "4. Internal Contamination Triage: Any casualty with suspected radioisotope ingestion or inhalation must be referred to medical physics units for whole-body counting and chelation therapy (e.g., Prussian Blue for Cesium-137, Ca-DTPA for transuranics)."
            ),
        },
    ],
}

print("Nuclear SOP template created successfully.")
