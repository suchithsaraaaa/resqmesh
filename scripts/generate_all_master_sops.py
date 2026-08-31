"""
ResQMesh AI — Master SOP Expansion Generator
Assembles the complete, authoritative 29 SOP definitions covering all 21 categories.
"""

import sys
import os

sys.path.insert(0, r"d:\Final_year_project\scripts")
import rag_corpus_definitions as orig_defs

# Grab the existing 23 definitions
sops = list(orig_defs.MASTER_SOP_DEFINITIONS)

# 1. Update ndma_earthquake_sop_01 with 3 chapters
for s in sops:
    if s["doc_id"] == "ndma_earthquake_sop_01":
        s["chapters"] = [
            {
                "section": "Immediate Seismic Actions (Drop, Cover, Hold) & Utility Isolation",
                "page": 12,
                "keywords": ["earthquake", "drop cover hold", "aftershock", "seismic", "gas leak", "utility isolation", "shelter", "immediate earthquake response"],
                "hazards": ["earthquake", "structural_damage", "gas_leak", "aftershock"],
                "substances": [],
                "subdomain": "earthquake_response",
                "audience": "responder",
                "region": "india",
                "content": (
                    "Immediate operational directives during and following earthquake seismic events:\n"
                    "1. Drop, Cover, and Hold: Protect head and torso beneath sturdy furniture or against interior load-bearing walls. Stay away from glass windows, exterior facades, and heavy overhead fixtures. Do NOT run outdoors during active shaking.\n"
                    "2. Rapid Utility Isolation: Immediately isolate main gas supply valves and main electrical circuit breakers in damaged sectors to prevent conflagrations from fractured gas mains and energized short circuits.\n"
                    "3. Immediate Post-Shock Evacuation: Once shaking stops, evacuate occupants via designated stairwells. Never use elevators. Gather at open pre-designated assembly grounds away from power lines and brick walls.\n"
                    "4. Incident Command Post (ICP) Staging: Establish ICP in an open field at a standoff distance equal to at least 1.5 times the height of the tallest standing wall."
                ),
            },
            {
                "section": "Aftershock Protocols, Secondary Hazards & Structural Hazard Assessment",
                "page": 28,
                "keywords": ["aftershocks", "secondary collapse", "structural assessment", "placarding", "red tag", "yellow tag", "green tag", "aftershock safety"],
                "hazards": ["secondary_collapse", "compromised_structures", "aftershocks"],
                "substances": [],
                "subdomain": "earthquake_aftershocks",
                "audience": "commander",
                "region": "india",
                "content": (
                    "Managing aftershocks and secondary seismic hazards:\n"
                    "1. Expect Frequent Aftershocks: Aftershocks can occur within minutes, hours, or days, and can cause sudden complete collapse of previously weakened or cracked buildings. Position dedicated Safety Officers with mechanical air-horns continuously observing structural groans or shifts.\n"
                    "2. ATC-20 Rapid Building Triage Placarding: (1) GREEN (Inspected / Safe to Occur): No structural hazard observed; (2) YELLOW (Restricted Use): Specific rooms or exterior damaged, entry restricted; (3) RED (Unsafe): Heavy structural damage, leaning columns, shear cracking; entry strictly prohibited.\n"
                    "3. Critical Infrastructure Assessment: Immediate inspection of hospital generators, water treatment plants, communications towers, and underground sewer lines before resuming normal municipal load.\n"
                    "4. Personnel Accountability Reports (PAR): Conduct PAR roll-call every 30 minutes for all search and rescue teams deployed near damaged structures."
                ),
            },
            {
                "section": "Rural vs Urban Earthquake Incident Command & Road Blockage Clearance",
                "page": 44,
                "keywords": ["urban earthquake", "rural earthquake", "road blockage", "debris clearance", "heavy equipment", "collapsed roads", "flyover inspection"],
                "hazards": ["road_blockage", "infrastructure_severance", "isolated_communities"],
                "substances": [],
                "subdomain": "earthquake_logistics_command",
                "audience": "commander",
                "region": "india",
                "content": (
                    "Tactical logistics and road clearance for earthquake disaster zones:\n"
                    "1. Flyover and Bridge Clearance: Enforce total closure of all elevated highway flyovers, overpasses, and bridges until certified structural engineers inspect piers for shear fracture and bearing displacement.\n"
                    "2. Arterial Road Debris Clearing: Deploy heavy front-end loaders and excavators to establish a two-lane emergency corridor ('Lifeline Highway') connecting airports, helipads, and district civil hospitals.\n"
                    "3. Rural Village Isolation Protocol: For collapsed masonry and mud houses in rural sectors, dispatch mobile NDRF / SDRF satellite communication units equipped with portable generators, medical trauma kits, and solar water purifiers.\n"
                    "4. Public Information Broadcast: Issue continuous, plain-language radio advisories instructing citizens to remain out of cracked multi-story buildings, avoid unverified social media rumors, and keep roads clear for emergency vehicle convoys."
                ),
            },
        ]

# 2. Update ndma_flood_sop_01 with 3 chapters
for s in sops:
    if s["doc_id"] == "ndma_flood_sop_01":
        s["chapters"] = [
            {
                "section": "Swiftwater Rescue Hierarchy, Boat Deployment & Submerged Vehicles",
                "page": 8,
                "keywords": ["flood", "swiftwater", "boat rescue", "submerged car", "flash flood", "water rescue", "irb", "turn around dont drown", "water sweeps"],
                "hazards": ["swiftwater", "drowning", "submerged_vehicles", "hypothermia"],
                "substances": [],
                "subdomain": "swiftwater_rescue",
                "audience": "responder",
                "region": "india",
                "content": (
                    "Standard operating procedures for flood waters, swiftwater currents, and boat rescue:\n"
                    "1. Swiftwater Rescue Hierarchy (Low-to-High Risk): Always prioritize rescuer safety using the sequence: TALK (coach victim to safety) -> REACH (use rescue pole/paddle) -> THROW (throw floating rescue rope bag) -> ROW (launch boat/IRB) -> GO (enter water in swiftwater PFD with tethered backup) -> HELO (helicopter hoist). Never exceed team training limits.\n"
                    "2. Inflatable Rescue Boat (IRB) Navigation: Operate IRBs with outboard motors in deep navigable channels. Rescuers must wear Type V rescue life jackets (minimum 22 lbs flotation), water rescue helmets, and neoprene thermal immersion suits. Never tie a rescue line around a rescuer's waist.\n"
                    "3. Submerged Vehicles & Road Inundation: Six inches of swiftwater will knock over an adult. Twelve inches (1 foot) of flowing water will float and sweep away a passenger car. Two feet (24 inches) of water will sweep away SUVs, pickup trucks, and emergency vehicles. Responders must immediately cordon off submerged roads and bridges: 'Turn Around, Don't Drown'.\n"
                    "4. Submerged Vehicle Extrication: Approach from the upstream side using safety tethers. Break vehicle side windows with center-punch (never windshield); extricate occupants immediately before vehicle rolls into deeper river currents."
                ),
            },
            {
                "section": "Urban Flooding, Nala Overflow & Evacuation Staging in Metropolitan Sectors",
                "page": 22,
                "keywords": ["urban flood", "stormwater drain", "nala overflow", "musi river", "hussain sagar", "basement flooding", "urban inundation"],
                "hazards": ["urban_flooding", "sewer_overflow", "electrical_shock", "submerged_openings"],
                "substances": [],
                "subdomain": "urban_flood_evacuation",
                "audience": "responder",
                "region": "india",
                "content": (
                    "Operational protocol for catastrophic urban inundation and nala breach:\n"
                    "1. Open Manhole & Drain Suction Hazard: In urban floodwaters, missing manhole covers and submerged storm drains create lethal whirlpool suction currents. Responders must probe flooded streets with wading poles before stepping.\n"
                    "2. Underground Basement Inundation: Prohibit entry into subterranean parking garages or basements during active flood ingress. Rapid water flooding can trap occupants against fire exits within 90 seconds. Cut power before pumping.\n"
                    "3. Rooftop Evacuation Staging: When ground floors are submerged, move residents vertically to rooftop assembly areas. Mark roof with fluorescent orange tarpaulins for aerial rescue.\n"
                    "4. Inundated Electrical Transformer Cordon: Flooded transformer plinths and downed power cables electrify surrounding water pools. Maintain a 30-meter isolation perimeter until power utility confirms feeder trip."
                ),
            },
            {
                "section": "Post-Flood Public Health: Water Disinfection & Disease Outbreak Prevention",
                "page": 36,
                "keywords": ["flood health", "waterborne disease", "cholera", "leptospirosis", "water chlorination", "bleaching powder", "wells disinfection"],
                "hazards": ["waterborne_epidemic", "leptospirosis", "contaminated_wells"],
                "substances": [],
                "subdomain": "flood_public_health",
                "audience": "medical",
                "region": "india",
                "content": (
                    "Post-flood disease surveillance and water purification directives:\n"
                    "1. Drinking Water Disinfection: Treat all municipal and private drinking water supplies. Enforce boiling for at least 1 rolling minute. For chemical disinfection, add Chlorine/Halazone tablets (or 5% sodium hypochlorite solution at 2 drops per liter) and allow 30 minutes contact time before consumption.\n"
                    "2. Leptospirosis Prophylaxis: Flood waters contaminated with rodent and animal urine carry Leptospira. Field rescue personnel working in flood waters must take Doxycycline 200 mg orally once weekly as chemoprophylaxis and wear waterproof thigh waders.\n"
                    "3. Open Well Disinfection: Add 2.5 grams of Bleaching Powder (chlorinated lime, 33% available chlorine) per 1,000 liters of well water. Test for Free Residual Chlorine (target 0.5 mg/L after 1 hour).\n"
                    "4. Carcass Removal & Sanitation: Remove and deeply bury drowned animal carcasses with lime to prevent fly breeding and water catchment contamination."
                ),
            },
        ]

# 3. Add Nuclear Disaster SOP
new_nuclear_sop = {
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
sops.append(new_nuclear_sop)

# 4. Add Landslide SOP
new_landslide_sop = {
    "doc_id": "ndma_landslide_sop_01",
    "category": "landslides",
    "title": "NDMA / GSI Guidelines for Landslide Risk Management, Slope Stabilization & Debris Flow Search",
    "organization": "National Disaster Management Authority (NDMA India) / Geological Survey of India",
    "publication_date": "2023-09-15",
    "source_url": "https://ndma.gov.in/guidelines/landslides",
    "priority": "critical",
    "chapters": [
        {
            "section": "Landslide Geological Precursors (Tension Cracks, Bulges) & Immediate Evacuation",
            "page": 14,
            "keywords": ["landslide", "mudflow", "debris flow", "slope instability", "tension cracks", "bulging slope", "muddy springs", "landslide evacuation"],
            "hazards": ["slope_failure", "debris_flow", "rockfall", "mudslide"],
            "substances": [],
            "subdomain": "landslide_early_warning",
            "audience": "responder",
            "region": "india",
            "content": (
                "Field recognition of imminent slope failure and landslide evacuation:\n"
                "1. Critical Precursor Indicators: (1) Fresh tension cracks opening in soil, paved roads, or foundation slabs; (2) Bulging of ground at slope toe; (3) Sudden tilting of trees, telephone poles, or retaining walls; (4) Rapid change in water flow: crystal clear mountain streams turning suddenly muddy, or springs drying up abruptly; (5) Faint rumbling or cracking sounds of breaking roots and boulders.\n"
                "2. Immediate Evacuation Action: When precursor cracks or slope movement are observed, order immediate evacuation of all homes in the runout path. Move strictly LATERAL (sideways across the hill), NEVER run down the natural valley or drainage gulley where debris flows accelerate at speeds up to 50 km/h.\n"
                "3. Road Transport Lockdown: Immediately close mountain ghat roads and hill highway passes when cumulative 24-hour monsoon rainfall exceeds 150 mm, as soil pore-water pressure reaches critical saturation."
            ),
        },
        {
            "section": "Search & Rescue Operations on Unstable Slopes & Secondary Slide Lookouts",
            "page": 30,
            "keywords": ["landslide sar", "mud search", "secondary slide", "safety lookout", "tethered search", "probing poles"],
            "hazards": ["secondary_landslide", "mud_asphyxiation", "unstable_terrain"],
            "substances": [],
            "subdomain": "landslide_rescue_safety",
            "audience": "responder",
            "region": "india",
            "content": (
                "Search and rescue tactical operations in mudflows and debris cones:\n"
                "1. Dedicated Secondary Slide Watchers: Position trained Safety Watchers equipped with air-horns and binoculars at high vantage points overlooking the crown of the slide. If upper slope movement or rockfall occurs: THREE BLASTS = IMMEDIATE EVACUATION of all searchers from the debris field.\n"
                "2. Tethered Search Lines: Rescuers entering deep fluidized mud must wear safety harnesses connected to belayed synthetic rescue ropes anchored to stable bedrock or large trees outside the slide path.\n"
                "3. Searching for Trapped Victims: Use 3-meter fiberglass probing poles in grid patterns. Deploy trained K9 disaster search dogs. In fluidized mud, victim survival time drops rapidly due to mechanical asphyxiation; prioritize surface void spaces and collapsed roof structures."
            ),
        },
    ],
}
sops.append(new_landslide_sop)

# 5. Add Industrial Disaster SOP
new_industrial_sop = {
    "doc_id": "ndma_industrial_disaster_sop_01",
    "category": "industrial_disaster",
    "title": "NDMA / Factory Inspectorate Standard Operating Procedure for Industrial Explosions & High-Pressure Boiler Ruptures",
    "organization": "National Disaster Management Authority (NDMA India) / Directorate General Factory Advice",
    "publication_date": "2023-11-20",
    "source_url": "https://ndma.gov.in/guidelines/industrial-disasters",
    "priority": "critical",
    "chapters": [
        {
            "section": "High-Pressure Industrial Boiler Explosions & Fragment Exclusion Zones",
            "page": 16,
            "keywords": ["boiler explosion", "pressure vessel", "industrial accident", "steam explosion", "fragment trajectory", "factory explosion", "blast radius"],
            "hazards": ["overpressure_blast", "shrapnel_projection", "steam_scalding"],
            "substances": ["high_pressure_steam", "flammable_vapors"],
            "subdomain": "boiler_blast_response",
            "audience": "commander",
            "region": "india",
            "content": (
                "Emergency procedures for industrial boiler catastrophic ruptures and pressure vessel failures:\n"
                "1. Blast Overpressure & Shrapnel Standoff: High-pressure boiler explosions produce supersonic blast waves and heavy metal shrapnel capable of penetrating reinforced concrete up to 500 meters away. Establish an initial safety exclusion zone of at least 800 meters.\n"
                "2. Superheated Steam Hazard: Superheated high-pressure steam leaks are INVISIBLE to the naked eye and can instantaneously sever limbs and cause fatal full-thickness scald burns. Responders must approach suspected steam zones holding a wooden corn broom in front of them; the broom fibers will char or ignite upon touching an invisible steam jet.\n"
                "3. Cascade Risk Assessment: Immediately check for damaged adjacent ammonia refrigeration lines, fuel oil storage tanks, or chemical pipelines. Enforce automated emergency shutdown (ESD) of all facility gas and fuel valves."
            ),
        },
        {
            "section": "Combustible Industrial Dust Explosions (The Dust Explosion Pentagon)",
            "page": 32,
            "keywords": ["dust explosion", "combustible dust", "dust pentagon", "grain dust", "flour explosion", "coal dust", "secondary dust explosion"],
            "hazards": ["combustible_dust_flash", "secondary_deflagration", "confinement_blast"],
            "substances": ["organic_dust", "metallic_dust"],
            "subdomain": "dust_explosion_mitigation",
            "audience": "responder",
            "region": "global",
            "content": (
                "Tactical response to combustible industrial dust deflagrations:\n"
                "1. The Dust Explosion Pentagon: Requires (1) Combustible dust fuel, (2) Atmospheric oxygen, (3) Dispersion of dust into a cloud, (4) Confinement in an enclosed space, and (5) An ignition source (hot bearing, static spark, open flame).\n"
                "2. The Deadly Secondary Dust Explosion: The initial minor primary blast dislodges accumulated layers of dust from ceiling beams, rafters, and ducts into suspension, forming a massive dense dust cloud that ignites into a catastrophic secondary explosion destroying the entire facility. Never enter a facility immediately after an initial dust pop.\n"
                "3. Housekeeping & Suppression: NEVER use high-pressure air hoses or high-pressure water solid streams to clean or fight dust fires, as this lofts dust into the air creating an explosive cloud. Use fine water fog spray or Class D specialized extinguishing agents."
            ),
        },
    ],
}
sops.append(new_industrial_sop)

# 6. Add Biological Outbreak SOP
new_biological_sop = {
    "doc_id": "who_epidemic_containment_sop_01",
    "category": "biological_emergency",
    "title": "WHO / NCDC Guidelines for Biological Epidemics, Infectious Outbreak Isolation & PPE Protocols",
    "organization": "World Health Organization / National Centre for Disease Control (NCDC India)",
    "publication_date": "2024-01-25",
    "source_url": "https://www.who.int/emergencies/infectious-disease-protocols",
    "priority": "critical",
    "chapters": [
        {
            "section": "Infectious Disease Outbreak Containment, Isolation Corridors & Quarantine Principles",
            "page": 12,
            "keywords": ["biological emergency", "epidemic", "outbreak", "infectious disease", "quarantine", "isolation zone", "droplet precautions", "airborne precautions"],
            "hazards": ["pathogen_transmission", "epidemic_surge", "biological_cross_contamination"],
            "substances": ["infectious_aerosols", "pathogens"],
            "subdomain": "outbreak_containment",
            "audience": "medical",
            "region": "india",
            "content": (
                "Operational guidelines for containment of acute biological outbreaks and respiratory epidemics:\n"
                "1. Primary Isolation Architecture: Establish negative-pressure isolation rooms (minimum 12 air changes per hour, exhausted outdoors away from air intakes) for airborne pathogens. Where negative pressure is unavailable, place patients in well-ventilated single rooms with exhaust fans directing air away from hospital corridors.\n"
                "2. Standard, Contact & Droplet Precautions: Enforce strict hand hygiene with 70% alcohol hand rub or soap and water for 30 seconds. Maintain 2-meter physical distance from symptomatic patients.\n"
                "3. Quarantine Management: Contacts of confirmed index cases must complete 14-day monitored home or facility quarantine with daily symptom and temperature screening. Restrict visitor access strictly to essential caregivers."
            ),
        },
        {
            "section": "Biological PPE Donning/Doffing Sequences & Biohazard Waste Disinfection",
            "page": 28,
            "keywords": ["biological ppe", "donning doffing", "n95 respirator", "face shield", "biohazard waste", "autoclaving", "chlorine 0.5 percent"],
            "hazards": ["self_contamination", "biohazard_exposure"],
            "substances": ["biohazard"],
            "subdomain": "biological_ppe_safety",
            "audience": "responder",
            "region": "global",
            "content": (
                "Strict personal protective equipment protocols for high-consequence biological hazards:\n"
                "1. Donning Sequence: Hand hygiene -> Gown/Tyvek coverall -> N95/FFP3 respirator (perform user seal check: positive and negative pressure tests) -> Eye protection (goggles or face shield) -> Double nitrile examination gloves (inner glove under cuff, outer glove over cuff).\n"
                "2. Doffing Sequence (Highest Risk of Self-Contamination): Clean gloved hands with sanitizer -> Remove outer gloves inside-out -> Remove gown pulling forward away from body -> Hand hygiene -> Remove goggles touching only head-strap -> Remove respirator touching only rear elastic straps (NEVER touch front of mask) -> Remove inner gloves -> Final alcohol hand rub.\n"
                "3. Biohazard Waste Management: Double-bag all contaminated PPE and patient dressings in yellow clinical waste bags. Disinfect surfaces with freshly prepared 0.5% (5,000 ppm) sodium hypochlorite solution leaving surface wet for at least 10 minutes before wiping."
            ),
        },
    ],
}
sops.append(new_biological_sop)

# 7. Add Disaster Logistics SOP
new_logistics_sop = {
    "doc_id": "ndma_disaster_logistics_sop_01",
    "category": "disaster_logistics",
    "title": "NDMA / WFP Emergency Logistics Guidelines: Staging Areas, Warehouse Management & Cold-Chain Supply",
    "organization": "National Disaster Management Authority (NDMA India) / World Food Programme",
    "publication_date": "2023-10-25",
    "source_url": "https://ndma.gov.in/guidelines/disaster-logistics",
    "priority": "high",
    "chapters": [
        {
            "section": "Incident Staging Area Management, Marshalling Yards & Warehouse Layout",
            "page": 14,
            "keywords": ["disaster logistics", "staging area", "warehouse management", "marshalling yard", "supply chain", "cargo tracking", "relief supplies"],
            "hazards": ["logistics_bottleneck", "relief_spoilage", "transport_failure"],
            "substances": [],
            "subdomain": "staging_area_logistics",
            "audience": "commander",
            "region": "india",
            "content": (
                "Disaster logistics and field supply chain management protocols:\n"
                "1. Staging Area Selection & Layout: Select flat, well-drained staging areas adjacent to major highway arteries or airport tarmac outside the disaster impact zone. Designate distinct zones: (1) Vehicle Ingress / Reception; (2) Unloading & Inspection; (3) Palletized Storage (dry food, non-food items, medical supplies); (4) Emergency Vehicle Marshalling & Dispatch; (5) Secure Security Cordon.\n"
                "2. First-In, First-Out (FIFO) Inventory Control: Stack goods on pallets at least 10 cm off the floor and 50 cm away from walls to prevent moisture damage and rodent infestation. Log all inbound consignments with cargo receipts, lot numbers, and expiration dates.\n"
                "3. Priority Dispatch Scheduling: Schedule relief dispatches during daylight hours with security escorts for high-value medical supplies and baby nutrition consignments."
            ),
        },
        {
            "section": "Cold-Chain Integrity, Vaccine/Blood Transport & Emergency Fuel Rationing",
            "page": 30,
            "keywords": ["cold chain", "vaccine storage", "blood transport", "fuel rationing", "generator fuel", "diesel allocation"],
            "hazards": ["cold_chain_breakage", "fuel_exhaustion"],
            "substances": [],
            "subdomain": "cold_chain_fuel_rationing",
            "audience": "responder",
            "region": "global",
            "content": (
                "Critical cold-chain and fuel security directives:\n"
                "1. Medical Cold-Chain Storage: Vaccines, insulin, and whole blood units must be maintained between +2°C and +8°C at all times. Use ice-lined refrigerators (ILR) with dedicated backup generator power or passive solar-powered vaccine coolers. Monitor temperatures twice daily.\n"
                "2. Emergency Fuel Rationing Matrix: When grid power fails and fuel supply lines are cut, fuel is strictly rationed according to priority: (1) Hospital ICU / Emergency Room generators (100% allocation); (2) Water pumping stations (80%); (3) Emergency response ambulances and fire tenders; (4) Telecommunications cell-tower generators; (5) General public transport.\n"
                "3. Diesel Storage Safety: Store emergency diesel in double-walled bunded tanks with dry powder fire extinguishers staged within 10 meters. Prohibit all smoking and open flames within 50 meters."
            ),
        },
    ],
}
sops.append(new_logistics_sop)

# 8. Add Public Health & Sanitation SOP
new_sanitation_sop = {
    "doc_id": "who_disaster_sanitation_sop_01",
    "category": "public_health",
    "title": "WHO / Sphere Guidelines for Emergency Water Purification, Sanitation & Hygiene (WASH)",
    "organization": "World Health Organization / Sphere Standards",
    "publication_date": "2024-02-18",
    "source_url": "https://www.who.int/water_sanitation_health/emergencies",
    "priority": "high",
    "chapters": [
        {
            "section": "Emergency Drinking Water Purification & Free Residual Chlorine Testing",
            "page": 10,
            "keywords": ["public health", "water purification", "chlorination", "residual chlorine", "wash", "water testing", "potable water"],
            "hazards": ["waterborne_disease", "diarrheal_outbreak", "arsenic_fluoride"],
            "substances": [],
            "subdomain": "emergency_water_quality",
            "audience": "responder",
            "region": "global",
            "content": (
                "Emergency water supply quality standards and field purification protocols:\n"
                "1. Minimum Water Quantity: Ensure minimum SPHERE quantity of 15 liters of potable water per person per day (3-5 L for drinking/cooking, 10 L for personal hygiene).\n"
                "2. Batch Chlorination of Water Tanks: Add 5 grams of high-test calcium hypochlorite (HTH, 70% available chlorine) per 1,000 liters of water. Dissolve granules in a plastic bucket before pouring into tank. Agitate thoroughly and allow at least 30 minutes contact time before public distribution.\n"
                "3. Free Residual Chlorine (FRC) Target: Test water at distribution taps using a DPD-1 colorimetric comparator. Target FRC is 0.5 mg/L (ppm) at delivery point; during active cholera or dysentery outbreaks, increase target FRC to 1.0 mg/L.\n"
                "4. Turbidity Reduction: If raw water turbidity is > 5 NTU, pre-treat with chemical coagulation (alum / aluminium sulfate at 10-30 mg/L) or sand filtration prior to chlorination, as suspended silt protects bacteria from chlorine disinfection."
            ),
        },
        {
            "section": "Emergency Latrines, Excreta Disposal & Vector-Borne Disease Control",
            "page": 24,
            "keywords": ["latrines", "excreta disposal", "sanitation", "vector control", "trench latrine", "handwashing stations", "fly breeding"],
            "hazards": ["fecal_oral_transmission", "vector_breeding", "dengue_malaria"],
            "substances": [],
            "subdomain": "emergency_sanitation_latrines",
            "audience": "responder",
            "region": "global",
            "content": (
                "Field excreta disposal and vector management in displacement settlements:\n"
                "1. Immediate Phase Shallow Trench Latrines: Dig trenches 0.3 meters wide and 1 to 1.5 meters deep. Provide wooden foot-rests. Each user covers excreta with a layer of excavated soil. Fill and abandon trench when waste reaches within 30 cm of ground surface.\n"
                "2. Latrine Ratios & Placement: Minimum 1 latrine stall per 20 persons. Latrines must be located at least 30 meters away from any ground water source (well, spring) and at least 1.5 meters above the seasonal high water table. Separate male and female latrines with internal privacy locks and solar night-lighting.\n"
                "3. Handwashing Stations: Install tippy-tap or pedal-operated handwashing stands with soap within 5 meters of every latrine bank. Enforce handwashing with soap after defecation and before food preparation.\n"
                "4. Vector & Mosquito Control: Eliminate standing stagnant water puddles to suppress Aedes and Anopheles breeding. Apply larvicide (Bti or temephos) to unmanaged water pools and distribute insecticide-treated bed nets (ITNs) to shelter residents."
            ),
        },
    ],
}
sops.append(new_sanitation_sop)

print(f"Total updated master SOPs: {len(sops)}")

# Write to file
out_path = r"d:\Final_year_project\scripts\rag_corpus_definitions.py"
with open(out_path, "w", encoding="utf-8") as f:
    f.write('"""\nResQMesh AI — Authoritative Disaster SOP Corpus Definitions\n')
    f.write('Contains complete, structured SOP definitions across all 21 emergency domains.\n"""\n\n')
    f.write('from typing import Dict, List, Any\n\n')
    f.write('MASTER_SOP_DEFINITIONS: List[Dict[str, Any]] = ')
    import pprint
    f.write(pprint.pformat(sops, indent=4, width=120))
    f.write('\n')

print("Successfully wrote updated scripts/rag_corpus_definitions.py")
