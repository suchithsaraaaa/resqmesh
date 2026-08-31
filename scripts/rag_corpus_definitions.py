"""
ResQMesh AI — Authoritative Disaster SOP Corpus Definitions
Contains complete, structured SOP definitions across all 21 emergency domains.
"""

from typing import Dict, List, Any

MASTER_SOP_DEFINITIONS: List[Dict[str, Any]] = [   {   'category': 'medical',
        'chapters': [   {   'audience': 'responder',
                            'content': 'When treating severe, life-threatening external extremity hemorrhage:\n'
                                       '1. Direct Pressure & Hemostatic Packing: Apply immediate, forceful direct '
                                       'pressure with gloved hands using sterile gauze or hemostatic dressing directly '
                                       'into the bleeding wound cavity. Hold continuous pressure for at least 3 '
                                       'minutes.\n'
                                       '2. Arterial Tourniquet Placement: If severe extremity bleeding cannot be '
                                       'controlled with direct pressure, immediately apply an approved windlass '
                                       'tourniquet (such as CAT or SOFTT). Place the tourniquet 2 to 3 inches proximal '
                                       'to the injury site on the limb. NEVER place the tourniquet directly over a '
                                       'joint (knee or elbow); if the wound is just below a joint, apply the '
                                       'tourniquet above the joint.\n'
                                       '3. Windlass Tightening: Turn the windlass rod until all arterial spurting '
                                       'ceases and distal peripheral pulses disappear. Lock the windlass into the '
                                       'retention clip.\n'
                                       '4. Time Documentation: Prominently write the exact time of tourniquet '
                                       "application on the patient's forehead or on the tourniquet time-strap (format: "
                                       "'T-HH:MM'). NEVER cover or conceal a tourniquet with blankets.\n"
                                       '5. Sucking Chest Wounds: For penetrating open chest trauma, immediately apply '
                                       'a vented chest seal to allow air and blood to escape while preventing tension '
                                       'pneumothorax. Monitor for progressive respiratory distress.',
                            'hazards': ['trauma', 'bleeding', 'blood_loss', 'arterial_hemorrhage'],
                            'keywords': [   'bleeding',
                                            'tourniquet',
                                            'hemorrhage',
                                            'arterial',
                                            'wound',
                                            'hemostatic',
                                            'shock',
                                            'cat'],
                            'page': 8,
                            'region': 'global',
                            'section': 'Severe Arterial Bleeding & Tourniquet Application Protocols',
                            'subdomain': 'bleeding_control',
                            'substances': []},
                        {   'audience': 'responder',
                            'content': 'Hypovolemic and traumatic shock can rapidly lead to irreversible multi-organ '
                                       'failure. Immediate field actions:\n'
                                       '1. Control All Sources of External Bleeding: Bleeding control takes precedence '
                                       'over all other medical interventions except airway obstruction.\n'
                                       '2. Patient Positioning: Lay the patient supine. If no spinal or pelvic trauma '
                                       'is suspected, elevate the legs 6 to 12 inches (Trendelenburg position) to '
                                       'enhance venous return to the vital organs.\n'
                                       '3. Prevent Hypothermia (Lethal Triad): Hypothermia severely impairs blood '
                                       'clotting. Wrap the patient in an emergency foil thermal blanket or woolen '
                                       'blanket, insulating them from both cold ground and wind.\n'
                                       '4. High-Flow Oxygen Administration: Administer supplemental high-flow oxygen '
                                       'via a non-rebreather mask at 10-15 L/min if available.\n'
                                       '5. Continuous Vitals Monitoring: Re-assess radial pulse quality, capillary '
                                       'refill (normal < 2 seconds), and mental status every 5 minutes.',
                            'hazards': ['trauma', 'hypovolemic_shock', 'hypothermia'],
                            'keywords': ['shock', 'hypovolemic', 'perfusion', 'blanket', 'hypothermia', 'fluids'],
                            'page': 19,
                            'region': 'global',
                            'section': 'Shock Management & Patient Thermal Stabilization',
                            'subdomain': 'shock_management',
                            'substances': []}],
        'doc_id': 'ifrc_trauma_first_aid_01',
        'organization': 'International Federation of Red Cross / World Health Organization',
        'priority': 'critical',
        'publication_date': '2024-01-10',
        'source_url': 'https://www.ifrc.org/guidelines/trauma-first-aid',
        'title': 'IFRC / WHO Standard Operating Procedure for Severe Trauma, Hemorrhage & Wound Management'},
    {   'category': 'medical',
        'chapters': [   {   'audience': 'responder',
                            'content': 'When performing CPR, responders must strictly apply age-specific protocols:\n'
                                       '1. Adult CPR (Puberty and Older): Compression-to-ventilation ratio is 30:2. '
                                       'Position heel of one hand in the center of chest with other hand on top. '
                                       'Compress at a rate of 100 to 120 beats per minute to a depth of 2.0 to 2.4 '
                                       'inches (5 to 6 cm), allowing complete chest recoil between compressions.\n'
                                       '2. Child CPR (1 Year to Puberty): Compression-to-ventilation ratio is 30:2 '
                                       '(single rescuer) or 15:2 (two trained healthcare responders). Use 1 or 2 hands '
                                       "depending on child's size. Compress at 100 to 120 bpm to a depth of "
                                       'approximately 2 inches (5 cm, or one-third anterior-posterior chest '
                                       'diameter).\n'
                                       '3. Infant CPR (Under 1 Year): Compression-to-ventilation ratio is 30:2 (single '
                                       'rescuer) or 15:2 (two rescuers). For single rescuer, use 2 fingers in center '
                                       'of chest just below nipple line; for two rescuers, use 2-thumb '
                                       'encircling-hands technique. Compress at 100 to 120 bpm to a depth of 1.5 '
                                       'inches (4 cm, or one-third chest diameter). Give gentle rescue breaths '
                                       'watching for chest rise (never over-inflate infant lungs).\n'
                                       '4. Foreign Body Airway Obstruction (Choking): For conscious adults and '
                                       'children, perform rapid abdominal thrusts (Heimlich maneuver). For conscious '
                                       'infants, place infant face-down along rescuer forearm and deliver 5 sharp back '
                                       'slaps between shoulder blades, followed by turning infant face-up and '
                                       'delivering 5 chest thrusts. NEVER perform blind finger sweeps in infants or '
                                       'children.',
                            'hazards': ['cardiac_arrest', 'respiratory_arrest', 'choking'],
                            'keywords': [   'cpr',
                                            'adult',
                                            'child',
                                            'infant',
                                            'pediatric',
                                            'chest compressions',
                                            'rescue breaths',
                                            'aed',
                                            'choking'],
                            'page': 14,
                            'region': 'global',
                            'section': 'Cardiopulmonary Resuscitation (CPR) — Age-Differentiated Protocol (Adult vs '
                                       'Child vs Infant)',
                            'subdomain': 'cpr_resuscitation',
                            'substances': []},
                        {   'audience': 'responder',
                            'content': 'AED deployment guidelines for sudden cardiac arrest:\n'
                                       '1. Immediate Deployment: Power on AED immediately upon arrival and follow '
                                       'voice prompts. Do not interrupt chest compressions until AED voice instructs '
                                       'to stand clear for rhythm analysis.\n'
                                       '2. Electrode Pad Placement for Adults and Children > 8 Years: Apply one '
                                       "self-adhesive pad on patient's upper right chest below collarbone; apply "
                                       'second pad on lower left lateral chest (anterolateral placement). Wipe dry any '
                                       'sweat or water from chest surface.\n'
                                       '3. Pediatric AED Considerations (Infants and Children < 8 Years): Use '
                                       'pediatric attenuator cable or pediatric pads if available. If pediatric pads '
                                       'are not available, use adult pads, ensuring pads DO NOT TOUCH each other. For '
                                       'infants and small children, place one pad in the center of the chest '
                                       '(anterior) and the other pad in the center of the upper back (posterior).\n'
                                       '4. Shock Delivery Safety: Ensure nobody touches the casualty when AED '
                                       "announces 'Analyzing' or 'Delivering Shock'. Shout loudly: 'STAND CLEAR!'. "
                                       'Resume CPR immediately beginning with chest compressions following shock '
                                       'delivery.',
                            'hazards': ['cardiac_arrest', 'ventricular_fibrillation'],
                            'keywords': [   'aed',
                                            'defibrillator',
                                            'shock',
                                            'pads',
                                            'pediatric attenuator',
                                            'cardiac arrest'],
                            'page': 22,
                            'region': 'global',
                            'section': 'Automated External Defibrillator (AED) Operations & Electrode Placement',
                            'subdomain': 'aed_defibrillation',
                            'substances': []}],
        'doc_id': 'aha_cpr_aed_protocols_02',
        'organization': 'American Heart Association / European Resuscitation Council',
        'priority': 'critical',
        'publication_date': '2024-02-01',
        'source_url': 'https://cpr.heart.org/guidelines/cpr-aed',
        'title': 'American Heart Association / ERC Resuscitation Guidelines: CPR & AED Operations (Adult, Child, '
                 'Infant)'},
    {   'category': 'medical',
        'chapters': [   {   'audience': 'medical',
                            'content': 'When managing casualties trapped under structural rubble or heavy debris for '
                                       'greater than 15-30 minutes:\n'
                                       '1. Pathophysiology Warning (Reperfusion Injury): Sustained pressure causes '
                                       'muscle ischemia. Sudden release of pressure without pre-hydration releases '
                                       'massive quantities of intracellular potassium, myoglobin, and lactic acid into '
                                       'the bloodstream, triggering lethal cardiac arrhythmias (ventricular '
                                       'fibrillation) and acute renal failure within minutes.\n'
                                       '2. Pre-Extrication Intravenous Hydration: Establish IV access BEFORE lifting '
                                       'the crushing load off the limb. Infuse 0.9% Normal Saline at 1,000 to 1,500 '
                                       'mL/hour in adults (or 10-15 mL/kg/hr in pediatric patients) before and during '
                                       'extrication.\n'
                                       '3. Tourniquet Rule for Prolonged Entrapment: If life-threatening crush has '
                                       'lasted several hours and immediate IV hydration is impossible before emergency '
                                       'structural lifting, apply a tourniquet directly above the crush site '
                                       'immediately before lifting to temporarily prevent toxic washout until IV line '
                                       'is secured.\n'
                                       '4. Compartment Syndrome Recognition: Watch for the 5 Ps: Pain out of '
                                       'proportion, Pallor, Paresthesia (numbness), Pulselessness, and Paralysis. '
                                       'Avoid circumferential tight bandaging.',
                            'hazards': ['crush_syndrome', 'hyperkalemia', 'renal_failure', 'entrapment'],
                            'keywords': [   'crush injury',
                                            'crush syndrome',
                                            'trapped',
                                            'extrication',
                                            'hydration',
                                            'potassium',
                                            'kidney failure',
                                            'compartment syndrome'],
                            'page': 31,
                            'region': 'global',
                            'section': 'Crush Injury, Compartment Syndrome & Pre-Extrication Hydration',
                            'subdomain': 'crush_injury',
                            'substances': []},
                        {   'audience': 'responder',
                            'content': 'When managing casualties of falls, vehicular impacts, or structural collapse:\n'
                                       '1. Manual In-Line Cervical Stabilization: Immediately take manual hold of the '
                                       'head and neck in neutral alignment. Do not allow flexion, extension, or '
                                       'lateral rotation.\n'
                                       '2. Rigid Cervical Collar: Apply an appropriately sized rigid cervical collar '
                                       'while maintaining continuous manual stabilization until the patient is fully '
                                       'secured to a rigid backboard or vacuum mattress.\n'
                                       '3. Log-Roll Technique: Move the patient onto a spinal board using a '
                                       "coordinated 4-person log-roll command led by the team member at the head ('At "
                                       "the count of three: one, two, three, roll').\n"
                                       '4. Traumatic Brain Injury Signs: Assess pupil symmetry and reactivity. Monitor '
                                       "for signs of base-of-skull fracture: Battle's sign (bruising behind ears), "
                                       'Raccoon eyes (periorbital ecchymosis), and clear cerebrospinal fluid (CSF) '
                                       'leakage from nose or ears. Maintain high-flow oxygen and avoid '
                                       'hyperventilation.',
                            'hazards': ['spinal_injury', 'paralysis', 'traumatic_brain_injury'],
                            'keywords': [   'spinal',
                                            'c-spine',
                                            'cervical spine',
                                            'log roll',
                                            'concussion',
                                            'head injury',
                                            'intracranial',
                                            'collar'],
                            'page': 44,
                            'region': 'global',
                            'section': 'Spinal (C-Spine) Immobilization & Traumatic Brain Injury Protocols',
                            'subdomain': 'spinal_and_head_trauma',
                            'substances': []},
                        {   'audience': 'responder',
                            'content': 'Burn field management and estimation protocols:\n'
                                       '1. Immediate Burn Cooling: Stop the burning process immediately. Irrigate '
                                       'thermal burns with clean, cool running water for 10 to 20 minutes. NEVER apply '
                                       'ice, ice water, butter, or oil to burns as this causes severe tissue necrosis '
                                       'and deep hypothermia.\n'
                                       '2. Chemical Burn Flushing: Remove all contaminated clothing immediately while '
                                       'irrigating with copious volumes of clean water for at least 20 to 30 '
                                       'continuous minutes. Brush off dry powder chemicals before flushing.\n'
                                       '3. Burn Dressing: Cover partial and full-thickness burns loosely with clean, '
                                       'dry, non-adherent sterile dressings or clean plastic wrap. Do not pop '
                                       'blisters.\n'
                                       '4. Rule of Nines for Body Surface Area (BSA): In adults: Head and neck = 9%, '
                                       'each arm = 9%, anterior torso = 18%, posterior torso = 18%, each leg = 18%, '
                                       'groin = 1%. Any burn exceeding 15% BSA in adults (or 10% in children) requires '
                                       'immediate IV fluid resuscitation (Parkland formula: 4 mL × kg × %BSA over 24 '
                                       'hrs).',
                            'hazards': ['burns', 'hypothermia', 'fluid_loss', 'chemical_burn'],
                            'keywords': [   'burn',
                                            'burns',
                                            'thermal',
                                            'chemical burn',
                                            'rule of nines',
                                            'cooling',
                                            'scald'],
                            'page': 58,
                            'region': 'global',
                            'section': 'Thermal, Chemical and Electrical Burn Management',
                            'subdomain': 'burn_management',
                            'substances': []},
                        {   'audience': 'responder',
                            'content': 'Critical protocols for snakebites and severe acute allergic reactions:\n'
                                       '1. Snakebite Management (India / South Asia Protocol): Keep the casualty calm '
                                       'and strictly immobile. Immobilize the bitten limb below heart level with a '
                                       'splint. For neurotoxic snakebites (Cobra, Krait), apply a broad pressure '
                                       'immobilization bandage from fingers/toes upward toward the trunk (tension '
                                       'equal to an elastic bandage on a sprained ankle).\n'
                                       '2. Strict Snakebite Contraindications: NEVER cut, scarify, or apply suction to '
                                       'the bite wound. NEVER apply arterial tourniquets, chemical reagents, or ice '
                                       'packs. Transport immediately to the nearest hospital equipped with polyvalent '
                                       'anti-snake venom (ASV).\n'
                                       '3. Anaphylaxis Emergency: Symptoms include facial/lip swelling (angioedema), '
                                       'stridor, wheezing, hypotension, and hives. Immediately administer Epinephrine '
                                       '(Adrenaline) 1:1,000 via intramuscular injection into the anterolateral '
                                       'mid-thigh (Adult dose: 0.3 mg to 0.5 mg; Pediatric dose: 0.15 mg).\n'
                                       '4. Position & Oxygen: Place patient recumbent with legs elevated unless '
                                       'respiratory distress requires sitting upright. Administer high-flow oxygen.',
                            'hazards': ['snakebite_envenomation', 'anaphylaxis', 'airway_edema'],
                            'keywords': [   'snakebite',
                                            'anti-venom',
                                            'cobra',
                                            'viper',
                                            'krait',
                                            'anaphylaxis',
                                            'epinephrine',
                                            'allergy'],
                            'page': 72,
                            'region': 'india',
                            'section': 'Snakebite Envenomation & Anaphylactic Allergic Emergencies',
                            'subdomain': 'envenomation_and_allergies',
                            'substances': []}],
        'doc_id': 'who_trauma_special_injuries_03',
        'organization': 'World Health Organization / INSARAG Medical Working Group',
        'priority': 'critical',
        'publication_date': '2024-01-20',
        'source_url': 'https://www.who.int/emergencies/trauma-care-guidelines',
        'title': 'WHO / INSARAG Clinical Guidelines for Crush Syndrome, Burns, Spinal Trauma & Snakebite'},
    {   'category': 'hazmat',
        'chapters': [   {   'audience': 'commander',
                            'content': 'Establishment of tactical hazardous materials operational perimeters:\n'
                                       '1. Approach Discipline: Always approach the incident scene from UPWIND, '
                                       'UPHILL, and UPSTREAM. Never enter a visible vapor cloud or puddle without '
                                       'calibrated multi-gas detection.\n'
                                       '2. Hot Zone (Exclusion Zone): The contaminated area immediately surrounding '
                                       'the release source. Entry is strictly restricted to certified HazMat '
                                       'technicians wearing appropriate Level A or Level B PPE with logged entry/exit '
                                       'times and dedicated backup rescue team standing by.\n'
                                       '3. Warm Zone (Contamination Reduction Zone): Surrounds the Hot Zone. Contains '
                                       'the primary Decontamination Corridor. All personnel and casualties exiting the '
                                       'Hot Zone must pass through decontamination before entering the Cold Zone.\n'
                                       '4. Cold Zone (Support Zone): Clean, uncontaminated area. Houses the Incident '
                                       'Command Post (ICP), EMS staging, rehabilitation unit, and media holding area. '
                                       'Strictly no contaminated gear permitted.',
                            'hazards': ['chemical_release', 'toxic_gas', 'corrosive', 'contamination'],
                            'keywords': [   'hot zone',
                                            'warm zone',
                                            'cold zone',
                                            'exclusion zone',
                                            'decon corridor',
                                            'upwind',
                                            'uphill',
                                            'perimeter'],
                            'page': 10,
                            'region': 'global',
                            'section': 'Zoning Architecture: Hot, Warm & Cold Zone Perimeter Establishment',
                            'subdomain': 'hazmat_zones',
                            'substances': []},
                        {   'audience': 'responder',
                            'content': 'Chemical protective clothing ensemble classification:\n'
                                       '1. Level A (Maximum Respiratory & Skin Protection): Totally encapsulating '
                                       'chemical- and vapor-protective suit with self-contained breathing apparatus '
                                       '(SCBA) worn inside the suit. Mandatory when unknown chemical vapors, gases, or '
                                       'high skin-absorption toxins are present.\n'
                                       '2. Level B (Maximum Respiratory, Moderate Skin Protection): Highest '
                                       'respiratory protection (SCBA) worn with a liquid splash-protective chemical '
                                       'suit. Used when vapor hazard is low but splash or heavy particulate hazard '
                                       'exists, or when oxygen level is < 19.5%.\n'
                                       '3. Level C (Air-Purifying Respiratory & Splash Protection): Chemical splash '
                                       'suit with air-purifying full-face respirator (cartridge filter). Only '
                                       'permitted when the exact chemical agent is identified, concentration is '
                                       'measured below IDLH (Immediately Dangerous to Life or Health), and oxygen is > '
                                       '19.5%.\n'
                                       '4. Level D (Work Uniform): Standard turnout gear or coveralls with steel-toe '
                                       'boots, safety goggles, and hard hat. No chemical vapor or respiratory '
                                       'protection.',
                            'hazards': ['toxic_inhalation', 'skin_absorption', 'chemical_burns'],
                            'keywords': [   'level a',
                                            'level b',
                                            'level c',
                                            'level d',
                                            'ppe',
                                            'scba',
                                            'encapsulated suit',
                                            'vapor protective'],
                            'page': 24,
                            'region': 'global',
                            'section': 'Personal Protective Equipment (PPE) Levels (Level A, B, C, D)',
                            'subdomain': 'hazmat_ppe',
                            'substances': []}],
        'doc_id': 'erg_hazmat_response_01',
        'organization': 'National Disaster Management Authority (NDMA) / US DOT',
        'priority': 'critical',
        'publication_date': '2024-01-15',
        'source_url': 'https://ndma.gov.in/guidelines/chemical-disasters',
        'title': 'US DOT / NDMA Emergency Response Guidebook: Core Hazmat Zones, PPE & Decontamination'},
    {   'category': 'hazmat',
        'chapters': [   {   'audience': 'commander',
                            'content': 'Operational directive for Chlorine gas release incidents (UN 1017):\n'
                                       '1. Physical Characteristics: Chlorine is a greenish-yellow gas with a pungent, '
                                       'suffocating bleach odor. It is approximately 2.5 times HEAVIER THAN AIR, '
                                       'causing toxic vapor clouds to stay close to the ground, pool in basements, '
                                       'railway underpasses, track pits, drainage canals, and low-lying hollows.\n'
                                       '2. Initial Isolation Distances: Immediately isolate the hazard area in all '
                                       'directions by a minimum of 100 meters (330 feet) for small cylinder leaks, and '
                                       'at least 500 meters (1,600 feet) for rail tankers, bulk storage tanks, or '
                                       'major pipe ruptures.\n'
                                       '3. Downwind Protective Action Distance: For daytime releases, evacuate or '
                                       'shelter-in-place downwind for at least 1.5 km (small leak) to 4.0 km (large '
                                       'bulk release). For night releases with thermal inversion, extend downwind '
                                       'protection up to 8.0 km.\n'
                                       '4. Shelter-in-Place vs Evacuation Decision: In dense urban settlements and '
                                       'railway station corridors, evacuating on foot through a traveling chlorine '
                                       'cloud causes acute fatal inhalation. Direct civilian populations inside '
                                       'buildings: close all exterior windows, tape around doors, immediately shut off '
                                       'central air conditioning and ventilation, and move to highest available floors '
                                       '(since chlorine pools near ground level).',
                            'hazards': ['toxic_gas', 'pulmonary_edema', 'respiratory_arrest', 'chlorine_leak'],
                            'keywords': [   'chlorine',
                                            'un1017',
                                            'toxic gas',
                                            'yellow-green',
                                            'bleach odor',
                                            'isolation distance',
                                            'shelter in place',
                                            'evacuation'],
                            'page': 12,
                            'region': 'global',
                            'section': 'Chlorine (UN 1017) Physical Properties, Isolation Distances & Public '
                                       'Protection',
                            'subdomain': 'chlorine_emergency',
                            'substances': ['chlorine', 'un1017']},
                        {   'audience': 'responder',
                            'content': 'Tactical vapor suppression and responder precautions for chlorine leaks:\n'
                                       '1. CRITICAL WATER WARNING: NEVER spray water directly onto a leaking chlorine '
                                       'container or liquid chlorine pool. Water reacts violently with liquid '
                                       'chlorine, generating intense heat and forming highly corrosive hydrochloric '
                                       'and hypochlorous acids, which will exponentially accelerate container '
                                       'corrosion and catastrophic wall rupture!\n'
                                       '2. Vapor Knockdown Technique: Use wide-angle high-pressure water fog sprays '
                                       'directed OVER or AROUND the vapor cloud downwind from the source to absorb and '
                                       'knock down airborne chlorine vapors into ground runoff.\n'
                                       '3. Runoff Containment: Chlorine knockdown water is acidic and toxic. Dike '
                                       'runoff water to prevent entry into sewers, municipal water intakes, or '
                                       'waterways.\n'
                                       '4. Victim Decontamination: Strip affected clothing immediately while flushing '
                                       'patient skin and eyes with copious running water for at least 15 to 20 '
                                       'minutes. Administer humidified 100% oxygen. Watch for delayed non-cardiogenic '
                                       'pulmonary edema which can manifest 6 to 24 hours post-exposure.',
                            'hazards': ['chemical_burns', 'corrosive_fumes', 'toxic_plume'],
                            'keywords': [   'chlorine',
                                            'vapor suppression',
                                            'water fog',
                                            'water spray warning',
                                            'hydrochloric acid',
                                            'decontamination'],
                            'page': 28,
                            'region': 'global',
                            'section': 'Chlorine Vapor Knockdown, Water Application Warning & Decontamination',
                            'subdomain': 'chlorine_containment',
                            'substances': ['chlorine', 'un1017']}],
        'doc_id': 'erg_chlorine_response_02',
        'organization': 'National Disaster Management Authority (NDMA) / Emergency Response Guidebook',
        'priority': 'critical',
        'publication_date': '2024-01-25',
        'source_url': 'https://ndma.gov.in/guidelines/chlorine',
        'title': 'ERG Toxic Inhalation Hazard Directive: Chlorine Gas (UN 1017) Response Protocols'},
    {   'category': 'hazmat',
        'chapters': [   {   'audience': 'commander',
                            'content': 'Operational directive for Anhydrous Ammonia releases (UN 1005):\n'
                                       '1. Physical Characteristics: Ammonia is a colorless alkaline gas with an '
                                       'intensely sharp, pungent, suffocating odor. In dry air, ammonia is lighter '
                                       'than air (vapor density 0.6); however, when released as a pressurized liquid, '
                                       'rapid expansion creates a cryogenic aerosol fog that is DENSE AND HEAVIER THAN '
                                       'AIR, pooling near ground level.\n'
                                       '2. Initial Isolation: Minimum 100 meters initial isolation for small releases; '
                                       '800 meters for large tank or tanker truck breach.\n'
                                       '3. Flammability Hazard: Ammonia is combustible between 15% and 28% '
                                       'concentration in air when an ignition source is present. Never operate unrated '
                                       'electronics or vehicles in the vapor perimeter.\n'
                                       '4. Personal Protection: Responders must wear Level A or Level B encapsulated '
                                       'suits with positive-pressure SCBA. Ammonia reacts rapidly with moisture on the '
                                       'body (eyes, throat, moist skin) to form ammonium hydroxide, causing '
                                       'catastrophic caustic chemical burns and blindness.',
                            'hazards': ['toxic_gas', 'caustic_burns', 'flammable_gas', 'ammonia_leak'],
                            'keywords': [   'ammonia',
                                            'un1005',
                                            'anhydrous ammonia',
                                            'fertilizer',
                                            'cold burn',
                                            'isolation distance',
                                            'flammability'],
                            'page': 16,
                            'region': 'global',
                            'section': 'Anhydrous Ammonia (UN 1005) Properties, Isolation & Plume Dynamics',
                            'subdomain': 'ammonia_emergency',
                            'substances': ['ammonia', 'un1005']},
                        {   'audience': 'responder',
                            'content': 'Tactical mitigation and patient decontamination for ammonia exposure:\n'
                                       '1. Vapor Absorption via Water Fog: Ammonia is extremely soluble in water. '
                                       'Deploy high-capacity water fog nozzles across the travel path of the vapor '
                                       'plume to absorb and dissolve airborne ammonia. Contain runoff.\n'
                                       "2. Patient Decontamination & Eye Flushing: Immediately flush the victim's eyes "
                                       'and exposed skin with copious volumes of clean water for a minimum of 30 '
                                       'continuous minutes. Remove contacts and hold eyelids open.\n'
                                       '3. Frostbite / Cryogenic Burns: Rapid liquid ammonia depressurization causes '
                                       'extreme cold. Do not rub frostbitten tissue; rewarm gently with lukewarm '
                                       'water.\n'
                                       '4. Airway Protection: Severe inhalation causes immediate laryngeal edema and '
                                       'bronchospasm. Secure advanced airway (endotracheal intubation) early before '
                                       'glottic swelling prevents visualization.',
                            'hazards': ['caustic_burns', 'corneal_damage', 'laryngeal_edema'],
                            'keywords': [   'ammonia',
                                            'water fog',
                                            'vapor absorption',
                                            'copious irrigation',
                                            'eye flush',
                                            'respiratory distress'],
                            'page': 32,
                            'region': 'global',
                            'section': 'Ammonia Vapor Absorption, Cold Burns & Immediate Patient Irrigation',
                            'subdomain': 'ammonia_containment',
                            'substances': ['ammonia', 'un1005']}],
        'doc_id': 'erg_ammonia_response_03',
        'organization': 'National Disaster Management Authority (NDMA) / Emergency Response Guidebook',
        'priority': 'critical',
        'publication_date': '2024-01-28',
        'source_url': 'https://ndma.gov.in/guidelines/ammonia',
        'title': 'ERG Chemical Safety Directive: Anhydrous Ammonia (UN 1005) Response Protocols'},
    {   'category': 'hazmat',
        'chapters': [   {   'audience': 'responder',
                            'content': 'Critical safety directives for Hydrogen Sulfide (H2S / UN 1053):\n'
                                       '1. Deadly Olfactory Fatigue: While H2S has a distinct rotten-egg odor at trace '
                                       'concentrations (< 1 ppm), concentrations above 50-100 ppm cause IMMEDIATE '
                                       "PARALYSIS OF THE OLFACTORY NERVE (loss of smell). Responders who assume 'the "
                                       "gas is gone' because the smell disappeared enter lethal atmosphere and suffer "
                                       "instant collapse ('knockdown') within seconds.\n"
                                       '2. Physical Behavior: H2S is heavier than air (vapor density 1.19) and '
                                       'accumulates in sewers, manholes, storage tanks, and basements. Never enter '
                                       'without positive-pressure SCBA and calibrated H2S electronic monitor.\n'
                                       '3. Rescue Protocols: Never perform solo rescue. If a responder or worker '
                                       'collapses in a pit or sewer, do not enter without SCBA and lifeline retrieval '
                                       'harness. Administer 100% oxygen and initiate immediate artificial respiration '
                                       'outside the hot zone.',
                            'hazards': ['toxic_gas', 'chemical_asphyxiant', 'rapid_collapse'],
                            'keywords': [   'hydrogen sulfide',
                                            'h2s',
                                            'un1053',
                                            'sewer gas',
                                            'olfactory fatigue',
                                            'knockdown',
                                            'scba'],
                            'page': 11,
                            'region': 'global',
                            'section': 'Hydrogen Sulfide (H2S / UN 1053) — Olfactory Fatigue & Knockdown Hazards',
                            'subdomain': 'h2s_emergency',
                            'substances': ['hydrogen_sulfide', 'un1053']},
                        {   'audience': 'responder',
                            'content': 'Emergency protocols for Carbon Monoxide exposure (CO / UN 1016):\n'
                                       '1. Nature of the Hazard: Carbon monoxide is a colorless, odorless, tasteless, '
                                       'non-irritating toxic gas produced by incomplete combustion of organic fuels '
                                       '(generators, vehicle exhausts, building fires, gas heaters). It binds to '
                                       'hemoglobin with 200 times the affinity of oxygen.\n'
                                       '2. Pulse Oximetry Warning: Standard finger pulse oximeters CANNOT distinguish '
                                       'between oxyhemoglobin and carboxyhemoglobin, giving falsely normal readings '
                                       '(e.g. 99% SpO2) in deeply poisoned patients. Rely on clinical presentation: '
                                       'headache, cherry-red lips/skin (late sign), confusion, nausea, and seizures.\n'
                                       '3. Medical Protocol: Immediately remove victim to fresh air. Administer 100% '
                                       'high-flow oxygen via a tight-fitting non-rebreather mask (reduces CO half-life '
                                       'in blood from 320 minutes to 80 minutes). For severe cases (unconsciousness, '
                                       'seizures), arrange urgent transport to a hyperbaric oxygen therapy (HBOT) '
                                       'facility.',
                            'hazards': ['chemical_asphyxiant', 'hypoxia', 'carboxyhemoglobin'],
                            'keywords': [   'carbon monoxide',
                                            'co',
                                            'un1016',
                                            'silent killer',
                                            'smoke inhalation',
                                            'hyperbaric',
                                            'pulse oximeter'],
                            'page': 25,
                            'region': 'global',
                            'section': 'Carbon Monoxide (CO / UN 1016) — Silent Asphyxiation & Field Treatment',
                            'subdomain': 'co_emergency',
                            'substances': ['carbon_monoxide', 'un1016']},
                        {   'audience': 'commander',
                            'content': 'Critical procedures for LPG cylinder, bullet tank, or tanker fires (UN 1075):\n'
                                       '1. Boiling Liquid Expanding Vapor Explosion (BLEVE) Hazard: If flame impinges '
                                       'directly onto the metal shell of an LPG tank above the liquid line (in the '
                                       'vapor space), the uncooled steel softens and ruptures within 8 to 15 minutes, '
                                       'causing a catastrophic BLEVE with massive fireball and fragmentation over '
                                       'hundreds of meters.\n'
                                       '2. Massive Unmanned Cooling Streams: Direct water from UNMANNED monitor '
                                       'nozzles at a minimum rate of 500 gallons per minute (2,000 L/min) directly '
                                       'onto the upper vapor space of the impinged container. NEVER fight tank fires '
                                       'from the ends of the cylinder (ends rocket outward during rupture).\n'
                                       '3. Immediate Evacuation Warning Signals: Evacuate all personnel to at least '
                                       "800 meters (0.5 mile) IMMEDIATELY if the tank's pressure relief valve produces "
                                       'a rising shrieking pitch, or if the tank shell discolors/bulges.',
                            'hazards': ['bleve', 'vapor_cloud_explosion', 'flammable_gas'],
                            'keywords': [   'lpg',
                                            'propane',
                                            'butane',
                                            'un1075',
                                            'bleve',
                                            'unmanned monitor',
                                            'tank cooling',
                                            'explosion'],
                            'page': 39,
                            'region': 'global',
                            'section': 'Liquefied Petroleum Gas (LPG / UN 1075) — BLEVE Prevention & Tank Cooling',
                            'subdomain': 'lpg_emergency',
                            'substances': ['lpg', 'un1075']},
                        {   'audience': 'responder',
                            'content': 'Tactical procedures for bulk gasoline, petrol, or diesel fuel spills:\n'
                                       '1. Strict Ignition Source Elimination: Establish an immediate 100-meter '
                                       'minimum perimeter free of all ignition sources. Prohibit mobile phones, '
                                       'flares, smoking, running vehicle engines, and electrical switches.\n'
                                       '2. Vapor Blanketing with Class B Foam: Apply Aqueous Film-Forming Foam (AFFF) '
                                       'or alcohol-resistant foam gently over the fuel spill using the roll-on or '
                                       'bank-down technique. The foam blanket seals vapors and prevents ignition.\n'
                                       '3. Non-Sparking Tools: Use only non-sparking beryllium-copper or bronze tools '
                                       'for closing valves or spill containment.\n'
                                       '4. Storm Drain Diking: Dike storm drains and sewers with sand, earth, or '
                                       'absorbent booms to prevent fuel vapors from entering municipal drainage '
                                       'networks and causing underground explosions.',
                            'hazards': ['flammable_liquid', 'vapor_fire', 'explosion'],
                            'keywords': [   'fuel spill',
                                            'gasoline',
                                            'diesel',
                                            'petrol',
                                            'class b foam',
                                            'afff',
                                            'sparking tools',
                                            'ignition perimeter'],
                            'page': 53,
                            'region': 'global',
                            'section': 'Hydrocarbon Fuel Spills (UN 1203 / UN 1202) — Vapor Blanketing & Static '
                                       'Prevention',
                            'subdomain': 'fuel_spill_emergency',
                            'substances': ['fuel', 'un1203', 'un1202']}],
        'doc_id': 'erg_special_substances_04',
        'organization': 'National Disaster Management Authority (NDMA) / USFA',
        'priority': 'critical',
        'publication_date': '2024-02-05',
        'source_url': 'https://ndma.gov.in/guidelines/special-hazmat',
        'title': 'ERG Special Chemical Hazards: Hydrogen Sulfide, Carbon Monoxide, LPG & Hydrocarbon Fuel Spills'},
    {   'category': 'hazmat',
        'chapters': [   {   'audience': 'responder',
                            'content': 'Responders must maintain a rigorous scientific distinction between exposure '
                                       'and contamination:\n'
                                       "1. Radiation Exposure (Irradiation): Occurs when a person's body is irradiated "
                                       'by gamma rays or X-rays emitted from a sealed radioactive source outside the '
                                       'body. A person who has suffered radiation exposure DOES NOT BECOME '
                                       'RADIOACTIVE. They pose ZERO radiation danger to doctors, responders, or '
                                       'transport personnel. They do NOT require decontamination; medical treatment '
                                       'for acute trauma proceeds immediately!\n'
                                       '2. Radioactive Contamination: Occurs when radioactive particulate, dust, or '
                                       "liquid is deposited onto a person's skin, hair, clothing, or inhaled/ingested "
                                       'into the body. A contaminated person CAN spread radioactive material to clean '
                                       'areas, ambulances, and responders. They REQUIRE rapid decontamination.\n'
                                       '3. The Protection Triad: (1) TIME: Minimize time near the source; (2) '
                                       'DISTANCE: Maximize distance — radiation intensity drops by the INVERSE SQUARE '
                                       'LAW (doubling distance reduces dose to 25%; tripling distance reduces dose to '
                                       '11%); (3) SHIELDING: Use high-density shielding (lead, steel, concrete, thick '
                                       'earth) between responders and the source.',
                            'hazards': ['ionizing_radiation', 'radiation_exposure', 'radioactive_contamination'],
                            'keywords': [   'radiation',
                                            'radiological',
                                            'radiation exposure',
                                            'radioactive contamination',
                                            'irradiation',
                                            'decontamination',
                                            'time distance shielding'],
                            'page': 14,
                            'region': 'global',
                            'section': 'Fundamental Distinction: Radiation Exposure vs Radioactive Contamination',
                            'subdomain': 'radiological_fundamentals',
                            'substances': ['radiation']},
                        {   'audience': 'commander',
                            'content': 'Response to lost industrial radiography sources, transport accidents, or '
                                       'radiological dispersal:\n'
                                       '1. Industrial Source Recognition: Common industrial sources (used in pipe weld '
                                       'radiography, level gauges) contain Cesium-137, Cobalt-60, or Iridium-192. They '
                                       'are often marked with the international trefoil radiation symbol. Never touch '
                                       'or approach an unshielded source capsule!\n'
                                       '2. Initial Isolation Perimeter: Establish an immediate perimeter of at least '
                                       '100 meters (330 feet) in all directions around an unshielded source until '
                                       'certified radiation safety officers with calibrated survey meters '
                                       '(Geiger-Müller counters) establish the 10 µSv/h (1 mR/h) safe cordon line.\n'
                                       '3. Rapid Decontamination by Stripping Clothing: Carefully removing and bagging '
                                       "a casualty's outer clothing and shoes eliminates OVER 90% OF EXTERNAL "
                                       'RADIOACTIVE CONTAMINATION instantly. Double-bag clothing and label with hazard '
                                       'tape.\n'
                                       '4. Washing Protocol: Wash skin and hair with warm water and mild soap from '
                                       'head downward, taking care not to scrub vigorously or break skin integrity '
                                       '(which allows radioactive particles into bloodstream). Contain all runoff '
                                       'water.',
                            'hazards': ['ionizing_radiation', 'dirty_bomb', 'orphan_source'],
                            'keywords': [   'radiological isolation',
                                            'lost radioactive source',
                                            'cesium 137',
                                            'cobalt 60',
                                            'iridium 192',
                                            'dosimeter',
                                            'stripping clothing'],
                            'page': 32,
                            'region': 'global',
                            'section': 'Isolation Distances, Lost Industrial Sources & Mass Decontamination',
                            'subdomain': 'radiological_containment',
                            'substances': ['radiation', 'cesium', 'cobalt', 'iridium']}],
        'doc_id': 'iaea_radiological_emergency_01',
        'organization': 'International Atomic Energy Agency / NDMA India',
        'priority': 'critical',
        'publication_date': '2024-02-10',
        'source_url': 'https://ndma.gov.in/guidelines/radiological-emergencies',
        'title': 'IAEA / NDMA Guidelines for Response to Radiological Emergencies & Lost Industrial Sources'},
    {   'category': 'building_collapse',
        'chapters': [   {   'audience': 'commander',
                            'content': 'Structural collapse assessment and void analysis for Urban Search and Rescue '
                                       '(USAR):\n'
                                       '1. Collapse Zone Perimeter: Establish an exclusion zone around the collapsed '
                                       'structure equal to at least 1.5 TIMES THE HEIGHT of the standing wall facade. '
                                       'Position all command posts, triage stations, and heavy equipment outside this '
                                       'perimeter.\n'
                                       '2. Structural Void Typology: (1) Lean-To Floor Collapse: One side of floor '
                                       'breaks while opposite side remains attached, creating high-survivability '
                                       'triangular void near intact wall; (2) V-Shape Collapse: Floor collapses in '
                                       'center while both ends remain supported, creating voids on both outer flanks; '
                                       '(3) Pancake Collapse: Multiple floors stack flat with minimal void space, '
                                       'requiring acoustic probing and vertical core-drilling.\n'
                                       '3. Secondary Collapse Lookouts: Position a dedicated Safety Officer with a '
                                       'mechanical air-horn monitoring building movement continuously. Egress signals: '
                                       'THREE SHORT BLASTS = IMMEDIATE EVACUATION of all rescue personnel from the '
                                       'structure; ONE LONG BLAST = ALL CLEAR / CEASE WORK.\n'
                                       '4. Personnel Accountability: Conduct Personnel Accountability Reports (PAR) '
                                       'every 20 minutes and immediately following any aftershock, structural groan, '
                                       'or horn signal.',
                            'hazards': ['structural_collapse', 'entrapment', 'secondary_collapse'],
                            'keywords': [   'collapse',
                                            'building collapse',
                                            'voids',
                                            'pancake collapse',
                                            'lean-to',
                                            'v-shape',
                                            'collapse perimeter',
                                            'secondary collapse',
                                            'air-horn',
                                            'horn signals',
                                            'egress signals',
                                            'damaged structure'],
                            'page': 15,
                            'region': 'global',
                            'section': 'Structural Collapse Typology, Void Spaces & Collapse Safety Perimeters',
                            'subdomain': 'structural_voids',
                            'substances': []},
                        {   'audience': 'responder',
                            'content': 'Principles of temporary emergency structural stabilization:\n'
                                       '1. Never Work Under Unshored Debris: Rescue teams must shore up compromised '
                                       'structural overhead loads before entering voids to extricate trapped victims.\n'
                                       '2. Box Cribbing Guidelines: Use solid hardwood timbers (typically 4x4 or 6x6 '
                                       'inches). Cross-tie timbers in alternating tiers (2x2 or 3x3 layout). Maximum '
                                       'cribbing height must NOT exceed 3 times the width of the crib base. Overlap '
                                       'corners by at least one timber thickness.\n'
                                       '3. Vertical and T-Shoring: Deploy vertical dead shores and T-shores under '
                                       'compromised concrete beams to transfer load directly down to solid foundation '
                                       'slab.\n'
                                       '4. Atmospheric Void Monitoring: Before entering any subterranean void, test '
                                       'atmosphere with a multi-gas monitor for: Oxygen (19.5% - 23.5%), Lower '
                                       'Explosive Limit (LEL < 10%), Carbon Monoxide (CO < 35 ppm), and Hydrogen '
                                       'Sulfide (H2S < 10 ppm).',
                            'hazards': ['structural_instability', 'crush_hazard'],
                            'keywords': [   'shoring',
                                            'cribbing',
                                            'timber',
                                            'box cribbing',
                                            't-shore',
                                            'load transfer',
                                            'heavy rescue'],
                            'page': 35,
                            'region': 'global',
                            'section': 'Timber Cribbing, Shoring Principles & Heavy Rescue Safety',
                            'subdomain': 'structural_shoring',
                            'substances': []}],
        'doc_id': 'insarag_building_collapse_01',
        'organization': 'INSARAG / National Disaster Management Authority (NDMA India)',
        'priority': 'critical',
        'publication_date': '2024-01-18',
        'source_url': 'https://www.insarag.org/methodology/guidelines',
        'title': 'INSARAG / NDMA Urban Search and Rescue Guidelines for Structural Collapse & Entrapment'},
    {   'category': 'mass_casualty',
        'chapters': [   {   'audience': 'medical',
                            'content': 'Simple Triage and Rapid Treatment (START) algorithm for adult mass casualty '
                                       'response (< 60 seconds per casualty):\n'
                                       "1. Step 1 (Walking Wounded): Broadcast verbal instruction: 'Anyone who can "
                                       "hear my voice and walk, move to the designated green flag assembly point now'. "
                                       'All casualties who walk are categorized GREEN (Minor / Walking Wounded).\n'
                                       '2. Step 2 (Respiration Assessment): Check breathing: If NOT breathing, open '
                                       'airway (chin lift/jaw thrust). If still NOT breathing after opening airway, '
                                       'categorize BLACK (Deceased / Expectant). If breathing resumes or is GREATER '
                                       'THAN 30 breaths/minute, categorize RED (Immediate / Critical). If breathing is '
                                       '10 to 30 breaths/minute, move to Step 3.\n'
                                       '3. Step 3 (Perfusion Assessment): Check radial pulse or capillary refill. If '
                                       'radial pulse is ABSENT or capillary refill > 2 seconds, categorize RED '
                                       '(Immediate). Control any active arterial bleeding immediately. If radial pulse '
                                       'is present, move to Step 4.\n'
                                       '4. Step 4 (Mental Status Assessment): Assess ability to obey a simple command '
                                       "('Squeeze my hand'). If unable to follow simple commands, categorize RED "
                                       '(Immediate). If able to follow simple commands, categorize YELLOW (Delayed / '
                                       'Urgent).',
                            'hazards': ['mass_casualty', 'medical_crisis'],
                            'keywords': [   'start triage',
                                            'mci',
                                            'triage',
                                            'red immediate',
                                            'yellow delayed',
                                            'green minor',
                                            'black deceased',
                                            'respirations',
                                            'perfusion'],
                            'page': 10,
                            'region': 'global',
                            'section': 'START Triage Protocol for Adult Casualties (30-2-Can Do)',
                            'subdomain': 'start_triage',
                            'substances': []},
                        {   'audience': 'medical',
                            'content': 'JumpSTART pediatric triage protocol modified for children under 8 years of '
                                       'age:\n'
                                       '1. Normal Pediatric Physiology: Children naturally have higher respiratory '
                                       'rates (normal 15-45 breaths/min). Do not categorize a child Red solely because '
                                       'breathing rate is > 30.\n'
                                       '2. The 5 Rescue Breaths Exception: In children, cardiac arrest is almost '
                                       'always secondary to respiratory arrest. If child is apneic, open airway. If '
                                       'still apneic, check for peripheral pulse. If pulse is PRESENT, deliver 5 '
                                       'gentle rescue breaths. If breathing resumes, categorize RED (Immediate). If '
                                       'breathing does NOT resume after 5 rescue breaths, categorize BLACK '
                                       '(Deceased).\n'
                                       '3. Respiratory Thresholds: If spontaneous breathing is < 15 or > 45 '
                                       'breaths/min, categorize RED. If between 15-45, check pulse.\n'
                                       '4. Perfusion & Neurological (AVPU): If pulse is absent, categorize RED. For '
                                       'neurological check, use AVPU scale (Alert, Voice, Pain, Unresponsive). '
                                       'Inappropriate response to pain or unresponsive child = RED. Appropriate '
                                       'response = YELLOW.',
                            'hazards': ['mass_casualty', 'pediatric_trauma'],
                            'keywords': [   'jumpstart',
                                            'pediatric triage',
                                            'child',
                                            'infant',
                                            'rescue breaths',
                                            'pulse',
                                            'respiratory rate'],
                            'page': 24,
                            'region': 'global',
                            'section': 'JumpSTART Pediatric Triage for Infants & Children Under 8 Years',
                            'subdomain': 'pediatric_triage',
                            'substances': []}],
        'doc_id': 'who_start_triage_01',
        'organization': 'World Health Organization / NDMA India',
        'priority': 'critical',
        'publication_date': '2024-01-30',
        'source_url': 'https://www.who.int/emergencies/mass-casualty-guidelines',
        'title': 'WHO / NDMA Guidelines for Mass Casualty Incident (MCI) Triage (START & JumpSTART Algorithms)'},
    {   'category': 'floods',
        'chapters': [   {   'audience': 'responder',
                            'content': 'Standard operating procedures for flood waters, swiftwater currents, and boat '
                                       'rescue:\n'
                                       '1. Swiftwater Rescue Hierarchy (Low-to-High Risk): Always prioritize rescuer '
                                       'safety using the sequence: TALK (coach victim to safety) -> REACH (use rescue '
                                       'pole/paddle) -> THROW (throw floating rescue rope bag) -> ROW (launch '
                                       'boat/IRB) -> GO (enter water in swiftwater PFD with tethered backup) -> HELO '
                                       '(helicopter hoist). Never exceed team training limits.\n'
                                       '2. Inflatable Rescue Boat (IRB) Navigation: Operate IRBs with outboard motors '
                                       'in deep navigable channels. Rescuers must wear Type V rescue life jackets '
                                       '(minimum 22 lbs flotation), water rescue helmets, and neoprene thermal '
                                       "immersion suits. Never tie a rescue line around a rescuer's waist.\n"
                                       '3. Submerged Vehicles & Road Inundation: Six inches of swiftwater will knock '
                                       'over an adult. Twelve inches (1 foot) of flowing water will float and sweep '
                                       'away a passenger car. Two feet (24 inches) of water will sweep away SUVs, '
                                       'pickup trucks, and emergency vehicles. Responders must immediately cordon off '
                                       "submerged roads and bridges: 'Turn Around, Don't Drown'.\n"
                                       '4. Submerged Vehicle Extrication: Approach from the upstream side using safety '
                                       'tethers. Break vehicle side windows with center-punch (never windshield); '
                                       'extricate occupants immediately before vehicle rolls into deeper river '
                                       'currents.',
                            'hazards': ['swiftwater', 'drowning', 'submerged_vehicles', 'hypothermia'],
                            'keywords': [   'flood',
                                            'swiftwater',
                                            'boat rescue',
                                            'submerged car',
                                            'flash flood',
                                            'water rescue',
                                            'irb',
                                            'turn around dont drown',
                                            'water sweeps'],
                            'page': 8,
                            'region': 'india',
                            'section': 'Swiftwater Rescue Hierarchy, Boat Deployment & Submerged Vehicles',
                            'subdomain': 'swiftwater_rescue',
                            'substances': []},
                        {   'audience': 'responder',
                            'content': 'Operational protocol for catastrophic urban inundation and nala breach:\n'
                                       '1. Open Manhole & Drain Suction Hazard: In urban floodwaters, missing manhole '
                                       'covers and submerged storm drains create lethal whirlpool suction currents. '
                                       'Responders must probe flooded streets with wading poles before stepping.\n'
                                       '2. Underground Basement Inundation: Prohibit entry into subterranean parking '
                                       'garages or basements during active flood ingress. Rapid water flooding can '
                                       'trap occupants against fire exits within 90 seconds. Cut power before '
                                       'pumping.\n'
                                       '3. Rooftop Evacuation Staging: When ground floors are submerged, move '
                                       'residents vertically to rooftop assembly areas. Mark roof with fluorescent '
                                       'orange tarpaulins for aerial rescue.\n'
                                       '4. Inundated Electrical Transformer Cordon: Flooded transformer plinths and '
                                       'downed power cables electrify surrounding water pools. Maintain a 30-meter '
                                       'isolation perimeter until power utility confirms feeder trip.',
                            'hazards': ['urban_flooding', 'sewer_overflow', 'electrical_shock', 'submerged_openings'],
                            'keywords': [   'urban flood',
                                            'stormwater drain',
                                            'nala overflow',
                                            'musi river',
                                            'hussain sagar',
                                            'basement flooding',
                                            'urban inundation'],
                            'page': 22,
                            'region': 'india',
                            'section': 'Urban Flooding, Nala Overflow & Evacuation Staging in Metropolitan Sectors',
                            'subdomain': 'urban_flood_evacuation',
                            'substances': []},
                        {   'audience': 'medical',
                            'content': 'Post-flood disease surveillance and water purification directives:\n'
                                       '1. Drinking Water Disinfection: Treat all municipal and private drinking water '
                                       'supplies. Enforce boiling for at least 1 rolling minute. For chemical '
                                       'disinfection, add Chlorine/Halazone tablets (or 5% sodium hypochlorite '
                                       'solution at 2 drops per liter) and allow 30 minutes contact time before '
                                       'consumption.\n'
                                       '2. Leptospirosis Prophylaxis: Flood waters contaminated with rodent and animal '
                                       'urine carry Leptospira. Field rescue personnel working in flood waters must '
                                       'take Doxycycline 200 mg orally once weekly as chemoprophylaxis and wear '
                                       'waterproof thigh waders.\n'
                                       '3. Open Well Disinfection: Add 2.5 grams of Bleaching Powder (chlorinated '
                                       'lime, 33% available chlorine) per 1,000 liters of well water. Test for Free '
                                       'Residual Chlorine (target 0.5 mg/L after 1 hour).\n'
                                       '4. Carcass Removal & Sanitation: Remove and deeply bury drowned animal '
                                       'carcasses with lime to prevent fly breeding and water catchment contamination.',
                            'hazards': ['waterborne_epidemic', 'leptospirosis', 'contaminated_wells'],
                            'keywords': [   'flood health',
                                            'waterborne disease',
                                            'cholera',
                                            'leptospirosis',
                                            'water chlorination',
                                            'bleaching powder',
                                            'wells disinfection'],
                            'page': 36,
                            'region': 'india',
                            'section': 'Post-Flood Public Health: Water Disinfection & Disease Outbreak Prevention',
                            'subdomain': 'flood_public_health',
                            'substances': []}],
        'doc_id': 'ndma_flood_sop_01',
        'organization': 'National Disaster Management Authority (NDMA India)',
        'priority': 'critical',
        'publication_date': '2023-07-20',
        'source_url': 'https://ndma.gov.in/guidelines/floods',
        'title': 'NDMA Standard Operating Procedure for Flood Inundation & Swift Water Boat Rescue'},
    {   'category': 'fire',
        'chapters': [   {   'audience': 'responder',
                            'content': 'Structural firefighting directives and portable extinguisher operations:\n'
                                       '1. Flashover & Backdraft Warning Signs: Watch for rollover (flame licks in '
                                       'upper ceiling smoke), intense heat radiating downward, dense black oily smoke '
                                       'pulsing under door cracks, and sudden inward sucking of air through openings. '
                                       'If observed, cool the upper gas layer immediately and prepare for emergency '
                                       'withdrawal.\n'
                                       '2. Fire Extinguisher PASS Operation: Pull safety pin; Aim nozzle at BASE of '
                                       'fire; Squeeze lever smoothly; Sweep from side to side covering fire '
                                       'footprint.\n'
                                       '3. Extinguisher Classifications: Class A (Wood, paper, cloth — water/foam); '
                                       'Class B (Flammable liquids, fuel — dry chemical/foam); Class C (Energized '
                                       'electrical equipment — CO2/clean agent; de-energize first); Class D '
                                       '(Combustible metals — specialized dry powder); Class K (Cooking oils/greases — '
                                       'wet chemical).\n'
                                       '4. Electric Vehicle (EV) Lithium-Ion Battery Fires: EV battery thermal runaway '
                                       'generates intense chemical fires and toxic hydrogen fluoride gas. Apply '
                                       'massive, continuous water cooling (minimum 2,000 to 4,000 gallons) directed '
                                       'into the undercarriage battery pack for at least 1-2 hours until battery '
                                       'temperature drops below 50°C.',
                            'hazards': ['conflagration', 'smoke_inhalation', 'structural_failure', 'thermal_burns'],
                            'keywords': [   'fire',
                                            'structural fire',
                                            'flashover',
                                            'backdraft',
                                            'extinguisher',
                                            'pass technique',
                                            'ev battery',
                                            'thermal runaway'],
                            'page': 12,
                            'region': 'global',
                            'section': 'Structural Fire Attack, Flashover Indicators & Fire Extinguisher PASS',
                            'subdomain': 'fire_suppression',
                            'substances': []}],
        'doc_id': 'usfa_structural_fire_01',
        'organization': 'US Fire Administration / NDMA India',
        'priority': 'critical',
        'publication_date': '2023-11-15',
        'source_url': 'https://ndma.gov.in/guidelines/fire-safety',
        'title': 'USFA / NDMA Fire Suppression Protocols: Structural Fires, EV Battery Runaway & Extinguishers'},
    {   'category': 'search_and_rescue',
        'chapters': [   {   'audience': 'responder',
                            'content': 'International standardized search marking for structures (2-foot by 2-foot '
                                       "spray-paint 'X' on entry wall):\n"
                                       '1. Initial Slash (/): Painted upon entry. Indicates search team is currently '
                                       'inside the building.\n'
                                       '2. Completing the Cross (X): Completed upon search team exit. Enter '
                                       'operational data into the four quadrants:\n'
                                       "   - TOP QUADRANT: Date and time the search team exited (e.g. '29-AUG "
                                       "14:30').\n"
                                       "   - LEFT QUADRANT: Search team identifier (e.g. 'NDRF-BN10' or "
                                       "'RESQMESH-ALPHA').\n"
                                       '   - RIGHT QUADRANT: Critical hazards identified inside structure (e.g. '
                                       "'RATS', 'GAS', 'ASBESTOS', 'UNSTABLE 2ND FLOOR').\n"
                                       '   - BOTTOM QUADRANT: Number of victims found: Live (L) and Deceased (D) (e.g. '
                                       "'2L / 1D').\n"
                                       '3. Confined Space Entry: Continuous forced-air ventilation is mandatory. '
                                       'Responders must wear full-body harnesses with retrieval winch line attached to '
                                       'an overhead tripod before entry.',
                            'hazards': ['entrapment', 'lost_victims', 'toxic_atmosphere'],
                            'keywords': [   'sar',
                                            'marking',
                                            'x-code',
                                            'fema marking',
                                            'confined space',
                                            'vehicle extrication',
                                            'hazards'],
                            'page': 22,
                            'region': 'global',
                            'section': 'FEMA / INSARAG Structural Search Marking System (X-Code Box)',
                            'subdomain': 'sar_marking',
                            'substances': []}],
        'doc_id': 'ndrf_sar_operations_01',
        'organization': 'National Disaster Response Force (NDRF India) / INSARAG',
        'priority': 'critical',
        'publication_date': '2023-10-12',
        'source_url': 'https://ndrf.gov.in/sop/sar-operations',
        'title': 'NDRF / INSARAG Field Manual: Search Marking System, Confined Space & Vehicle Extrication'},
    {   'category': 'emergency_comms',
        'chapters': [   {   'audience': 'commander',
                            'content': 'Tactical emergency communications when cellular and internet infrastructure '
                                       'are down:\n'
                                       '1. Plain Language Mandate: Prohibit 10-codes. Use clear, plain language '
                                       "('Message received', 'Emergency traffic only', 'Officer needs assistance') "
                                       'across inter-agency channels.\n'
                                       '2. METHANE Standard Situation Report (SITREP): Broadcast structured status in '
                                       '7 lines: (M) Major incident declared; (E) Exact location; (T) Type of '
                                       'incident; (H) Hazards present; (A) Access routes; (N) Number and severity of '
                                       'casualties; (E) Emergency services present and required.\n'
                                       '3. ResQMesh Multi-Hop Network Routing: Position battery-operated ResQMesh '
                                       'relay nodes at high elevation points (rooftops, water towers, hilltops) to '
                                       'bridge communications across partitioned sectors. Mesh packets automatically '
                                       'hop up to TTL 5.\n'
                                       "4. Urgent Priority Preemption: Use 'EMERGENCY TRAFFIC, BREAK BREAK' to clear "
                                       'frequency for immediate life-safety broadcasts.',
                            'hazards': ['communication_failure', 'grid_outage'],
                            'keywords': [   'communications',
                                            'mesh',
                                            'resqmesh',
                                            'radio protocol',
                                            'plain language',
                                            'methane',
                                            'sitrep',
                                            'relay'],
                            'page': 10,
                            'region': 'global',
                            'section': 'Radio Protocol Discipline, Plain Language & ResQMesh Relay Routing',
                            'subdomain': 'mesh_communications',
                            'substances': []}],
        'doc_id': 'resqmesh_emergency_comms_01',
        'organization': 'ResQMesh AI Tactical Communications Directorate',
        'priority': 'high',
        'publication_date': '2024-02-15',
        'source_url': 'https://resqmesh.ai/docs/comms-standard',
        'title': 'ResQMesh Tactical Communications Standard: Mesh Relay, Radio Discipline & METHANE SITREP'},
    {   'category': 'logistics',
        'chapters': [   {   'audience': 'commander',
                            'content': 'Resource allocation rules when field demands exceed available assets:\n'
                                       '1. The Life-Safety Rule: Available critical resources (ambulances, trauma '
                                       'surgical kits, rescue boats, hydraulic cutters) must be allocated strictly to '
                                       'incidents with active Red (Immediate) casualties before allocating to Yellow '
                                       '(Delayed) or Green (Minor) incidents.\n'
                                       '2. Transport Prioritization: If multiple Red casualties compete for a single '
                                       'ambulance, transport the patient with the highest probability of survival '
                                       'given immediate intervention (e.g. controlled hemorrhage, airway compromise) '
                                       'over patients with unsalvageable severe head trauma.\n'
                                       '3. Emergency Generator & Fuel Rationing: Power generators and diesel stocks '
                                       'must be dedicated first to critical life-support facilities (ICUs, neonatal '
                                       'units, emergency surgical suites), second to tactical command communications '
                                       'nodes, and third to municipal drinking water pumping.',
                            'hazards': ['logistics_failure', 'equipment_shortage'],
                            'keywords': [   'resource prioritization',
                                            'scarcity',
                                            'ambulance allocation',
                                            'rationing',
                                            'generator',
                                            'supplies'],
                            'page': 14,
                            'region': 'global',
                            'section': 'Acute Scarcity Prioritization Principles (Life-Safety First)',
                            'subdomain': 'resource_prioritization',
                            'substances': []}],
        'doc_id': 'ndma_resource_prioritization_01',
        'organization': 'National Disaster Management Authority (NDMA India)',
        'priority': 'high',
        'publication_date': '2024-01-05',
        'source_url': 'https://ndma.gov.in/guidelines/logistics',
        'title': 'NDMA Logistics Directive: Resource Allocation & Triage Prioritization During Acute Scarcity'},
    {   'category': 'incident_command',
        'chapters': [   {   'audience': 'commander',
                            'content': 'Incident Response System (IRS) command framework:\n'
                                       '1. Incident Commander (IC): Has overall responsibility for management of '
                                       'incident operations, safety, and objectives. Only the IC or designated Public '
                                       'Information Officer (PIO) authorizes external media releases.\n'
                                       '2. Span of Control: An operational supervisor can supervise between 3 and 7 '
                                       'individuals, with an OPTIMUM SPAN OF CONTROL OF 5. If span exceeds 7, divide '
                                       'the sector into functional branches or geographic divisions.\n'
                                       '3. General Staff Sections: Operations (executes tactical missions), Planning '
                                       '(tracks resources, collects data, creates Incident Action Plan), Logistics '
                                       '(provides equipment, fuel, medical, communications), Finance/Admin (tracks '
                                       'vendor costs and compensation).\n'
                                       '4. Unified Command: When multi-agency jurisdictions overlap (e.g. Police, '
                                       'Fire, NDRF, Municipal Health), agency commanders sit jointly at the same table '
                                       'in the Incident Command Post to establish a single shared set of incident '
                                       'objectives.',
                            'hazards': ['command_failure', 'jurisdictional_conflict'],
                            'keywords': [   'incident command',
                                            'ics',
                                            'irs',
                                            'incident commander',
                                            'span of control',
                                            'operations',
                                            'planning',
                                            'logistics',
                                            'unified command'],
                            'page': 8,
                            'region': 'india',
                            'section': 'Incident Commander, General Staff & Span of Control Guidelines',
                            'subdomain': 'incident_command_system',
                            'substances': []}],
        'doc_id': 'mha_incident_response_system_01',
        'organization': 'Ministry of Home Affairs / NDMA India',
        'priority': 'high',
        'publication_date': '2023-09-25',
        'source_url': 'https://ndma.gov.in/guidelines/irs',
        'title': 'NDMA / MHA Guidelines: Incident Response System (IRS) Structure & Operational Periods'},
    {   'category': 'incident_command',
        'chapters': [   {   'audience': 'commander',
                            'content': 'Statutory disaster management structure in India under DM Act 2005:\n'
                                       '1. Apex National Authority: National Disaster Management Authority (NDMA), '
                                       'chaired by the Prime Minister of India, lays down national policies and '
                                       'guidelines.\n'
                                       '2. National Disaster Response Force (NDRF): Multi-disciplinary specialized '
                                       'federal force organized into 16 strategic battalions across India, equipped '
                                       'for Chemical, Biological, Radiological, Nuclear (CBRN) emergencies and USAR.\n'
                                       '3. State Level (SDMA): State Disaster Management Authority chaired by the '
                                       'Chief Minister, directing the State Disaster Response Force (SDRF).\n'
                                       '4. District Level (DDMA - The Operational Spearhead): District Disaster '
                                       'Management Authority, headed by the District Collector / District Magistrate / '
                                       'Deputy Commissioner. The District Collector is the statutory Incident '
                                       'Commander at the district operational level, empowered to requisition private '
                                       'vehicles, properties, and direct all municipal bodies during declared '
                                       'disasters.',
                            'hazards': ['national_disaster'],
                            'keywords': [   'ndma',
                                            'ndrf',
                                            'sdma',
                                            'ddma',
                                            'disaster management act',
                                            'district magistrate',
                                            'india framework'],
                            'page': 6,
                            'region': 'india',
                            'section': 'Statutory Command Hierarchy: NDMA, SDMA, DDMA & NDRF Battalions',
                            'subdomain': 'india_disaster_framework',
                            'substances': []}],
        'doc_id': 'ndma_india_framework_01',
        'organization': 'National Disaster Management Authority (NDMA India)',
        'priority': 'high',
        'publication_date': '2023-06-15',
        'source_url': 'https://ndma.gov.in/about-us/dm-act',
        'title': 'National Disaster Management Act 2005: NDMA, NDRF & Statutory Response Architecture'},
    {   'category': 'incident_command',
        'chapters': [   {   'audience': 'commander',
                            'content': 'Standard procedures for monsoon cloudbursts and urban flash flooding across '
                                       'Hyderabad metropolitan region:\n'
                                       '1. GHMC Disaster Response Force (DRF) Deployment: GHMC Directorate of '
                                       'Enforcement, Vigilance & Disaster Management (EV&DM) deploys specialized '
                                       'motorized DRF teams across 6 municipal zones (Charminar, Khairatabad, '
                                       'Secunderabad, Serilingampally, Kukatpally, LB Nagar).\n'
                                       '2. Major Nala Inundation Points: Monitor 18 primary nala corridors for '
                                       'immediate overflow: (1) Kukatpally Nala (draining into Hussainsagar); (2) '
                                       'Picket Nala; (3) Banjara Nala; (4) Murki Nala; (5) Balkapur Channel. '
                                       'Vulnerable inundation zones: Begumpet, Alwal, Malakpet, Musarambagh, Nadeem '
                                       'Colony (Tolichowki), and Ramanthapur.\n'
                                       '3. Hussainsagar Lake Sluice Operations: When water level in Hussainsagar '
                                       'reaches Full Tank Level (FTL 513.43 meters), coordinate controlled discharge '
                                       'via 4 surplus sluices into the Musi river corridor. Alert police stations in '
                                       'downstream low-lying colonies (Chaderghat, Moosarambagh, Puranapul).\n'
                                       '4. Musi River Overflow Alert: Continuous discharge from Osmansagar (Gandipet) '
                                       'and Himayatsagar reservoir gates triggers immediate evacuation along the Musi '
                                       'river bed colonies.',
                            'hazards': ['urban_flooding', 'nala_overflow', 'musi_flood'],
                            'keywords': [   'telangana',
                                            'hyderabad',
                                            'ghmc',
                                            'drf',
                                            'urban flooding',
                                            'musi river',
                                            'hussain sagar',
                                            'begumpet',
                                            'malakpet',
                                            'alwal',
                                            'nalas'],
                            'page': 15,
                            'region': 'telangana',
                            'section': 'Hyderabad Urban Flood Management: 18 Nalas, Musi River & Inundation Hotspots',
                            'subdomain': 'hyderabad_flooding',
                            'substances': []},
                        {   'audience': 'responder',
                            'content': 'Telangana State Heat Wave Action Plan (IMD Alert Architecture):\n'
                                       '1. Alert Categories: Yellow Alert (Advisory, 41°C to 43°C); Orange Alert '
                                       '(Severe, 43.1°C to 45°C); Red Alert (Emergency Warning, > 45°C for 2 '
                                       'consecutive days).\n'
                                       '2. Mandatory Labor Restrictions: Under Section 30 of DM Act, outdoor physical '
                                       'labor (construction workers, MGNREGS laborers, agricultural field workers) is '
                                       'STRICTLY PROHIBITED between 12:00 PM and 3:00 PM during Orange and Red alert '
                                       'periods.\n'
                                       '3. Chalivendram (Drinking Water & ORS Kiosks): GHMC and district '
                                       'administrations activate free drinking water and Oral Rehydration Salt (ORS) '
                                       'distribution centers at all bus stations, railway hubs, and public markets.\n'
                                       '4. Emergency Medical Protocol: Primary Health Centers (PHCs) and Area '
                                       'Hospitals maintain dedicated cool beds with ice-water sponging, IV normal '
                                       'saline, and active fan cooling for acute heat stroke patients.',
                            'hazards': ['heat_wave', 'heat_stroke', 'dehydration'],
                            'keywords': [   'telangana',
                                            'heat wave',
                                            'hyderabad',
                                            'imd alert',
                                            'heat stroke',
                                            'ors centers',
                                            'work hours ban'],
                            'page': 28,
                            'region': 'telangana',
                            'section': 'Telangana Heat Wave Action Plan & Critical Work Hour Restrictions',
                            'subdomain': 'telangana_heatwave',
                            'substances': []},
                        {   'audience': 'commander',
                            'content': 'Emergency protocols for industrial hazardous materials zones in Telangana:\n'
                                       '1. Major Chemical Corridors: (1) Patancheru - Bollaram Industrial Corridor '
                                       '(heavy bulk drug and active pharmaceutical ingredient manufacturing); (2) '
                                       'Jeedimetla - Sanathnagar Industrial Estate (chemical formulation, solvents, '
                                       'electroplating); (3) Nacharam - Mallapur Industrial Belt (gas storage, polymer '
                                       'processing); (4) Pashamylaram Special Economic Zone.\n'
                                       '2. Chlorine & Toxic Solvent Risks: High density of chlorine tonners and bulk '
                                       'solvent storage tanks (toluene, acetone, methanol). In event of breach, '
                                       'initiate automatic 500m isolation perimeter and coordinate with Telangana '
                                       'State Pollution Control Board (TSPCB) emergency flying squads.\n'
                                       '3. Outer Ring Road (ORR) Hazmat Transit: Bulk chemical tankers traversing the '
                                       '158 km Hyderabad ORR have dedicated turnaround emergency bays at junctions '
                                       '(Exit 3 Gachibowli, Exit 9 Dundigal, Exit 12 Shamshabad). In vehicular tanker '
                                       'collisions, isolate traffic in both carriageways immediately.',
                            'hazards': ['industrial_chemical', 'toxic_leak', 'solvent_fire'],
                            'keywords': [   'telangana',
                                            'hyderabad',
                                            'patancheru',
                                            'bollaram',
                                            'jeedimetla',
                                            'nacharam',
                                            'pashamylaram',
                                            'chemical spill',
                                            'pharma corridor'],
                            'page': 42,
                            'region': 'telangana',
                            'section': 'Industrial Hazardous Chemical Corridors in Hyderabad Metropolitan Area',
                            'subdomain': 'hyderabad_industrial_hazards',
                            'substances': ['chemical', 'solvent', 'ammonia', 'chlorine']}],
        'doc_id': 'telangana_disaster_framework_01',
        'organization': 'Telangana State Disaster Management Authority (TSDMA) / GHMC',
        'priority': 'critical',
        'publication_date': '2024-02-01',
        'source_url': 'https://sdma.telangana.gov.in',
        'title': 'Telangana Disaster Management Authority & GHMC Emergency Operations Manual'},
    {   'category': 'earthquakes',
        'chapters': [   {   'audience': 'responder',
                            'content': 'Immediate operational directives during and following earthquake seismic '
                                       'events:\n'
                                       '1. Drop, Cover, and Hold: Protect head and torso beneath sturdy furniture or '
                                       'against interior load-bearing walls. Stay away from glass windows, exterior '
                                       'facades, and heavy overhead fixtures. Do NOT run outdoors during active '
                                       'shaking.\n'
                                       '2. Rapid Utility Isolation: Immediately isolate main gas supply valves and '
                                       'main electrical circuit breakers in damaged sectors to prevent conflagrations '
                                       'from fractured gas mains and energized short circuits.\n'
                                       '3. Immediate Post-Shock Evacuation: Once shaking stops, evacuate occupants via '
                                       'designated stairwells. Never use elevators. Gather at open pre-designated '
                                       'assembly grounds away from power lines and brick walls.\n'
                                       '4. Incident Command Post (ICP) Staging: Establish ICP in an open field at a '
                                       'standoff distance equal to at least 1.5 times the height of the tallest '
                                       'standing wall.',
                            'hazards': ['earthquake', 'structural_damage', 'gas_leak', 'aftershock'],
                            'keywords': [   'earthquake',
                                            'drop cover hold',
                                            'aftershock',
                                            'seismic',
                                            'gas leak',
                                            'utility isolation',
                                            'shelter',
                                            'immediate earthquake response'],
                            'page': 12,
                            'region': 'india',
                            'section': 'Immediate Seismic Actions (Drop, Cover, Hold) & Utility Isolation',
                            'subdomain': 'earthquake_response',
                            'substances': []},
                        {   'audience': 'commander',
                            'content': 'Managing aftershocks and secondary seismic hazards:\n'
                                       '1. Expect Frequent Aftershocks: Aftershocks can occur within minutes, hours, '
                                       'or days, and can cause sudden complete collapse of previously weakened or '
                                       'cracked buildings. Position dedicated Safety Officers with mechanical '
                                       'air-horns continuously observing structural groans or shifts.\n'
                                       '2. ATC-20 Rapid Building Triage Placarding: (1) GREEN (Inspected / Safe to '
                                       'Occur): No structural hazard observed; (2) YELLOW (Restricted Use): Specific '
                                       'rooms or exterior damaged, entry restricted; (3) RED (Unsafe): Heavy '
                                       'structural damage, leaning columns, shear cracking; entry strictly '
                                       'prohibited.\n'
                                       '3. Critical Infrastructure Assessment: Immediate inspection of hospital '
                                       'generators, water treatment plants, communications towers, and underground '
                                       'sewer lines before resuming normal municipal load.\n'
                                       '4. Personnel Accountability Reports (PAR): Conduct PAR roll-call every 30 '
                                       'minutes for all search and rescue teams deployed near damaged structures.',
                            'hazards': ['secondary_collapse', 'compromised_structures', 'aftershocks'],
                            'keywords': [   'aftershocks',
                                            'secondary collapse',
                                            'structural assessment',
                                            'placarding',
                                            'red tag',
                                            'yellow tag',
                                            'green tag',
                                            'aftershock safety'],
                            'page': 28,
                            'region': 'india',
                            'section': 'Aftershock Protocols, Secondary Hazards & Structural Hazard Assessment',
                            'subdomain': 'earthquake_aftershocks',
                            'substances': []},
                        {   'audience': 'commander',
                            'content': 'Tactical logistics and road clearance for earthquake disaster zones:\n'
                                       '1. Flyover and Bridge Clearance: Enforce total closure of all elevated highway '
                                       'flyovers, overpasses, and bridges until certified structural engineers inspect '
                                       'piers for shear fracture and bearing displacement.\n'
                                       '2. Arterial Road Debris Clearing: Deploy heavy front-end loaders and '
                                       "excavators to establish a two-lane emergency corridor ('Lifeline Highway') "
                                       'connecting airports, helipads, and district civil hospitals.\n'
                                       '3. Rural Village Isolation Protocol: For collapsed masonry and mud houses in '
                                       'rural sectors, dispatch mobile NDRF / SDRF satellite communication units '
                                       'equipped with portable generators, medical trauma kits, and solar water '
                                       'purifiers.\n'
                                       '4. Public Information Broadcast: Issue continuous, plain-language radio '
                                       'advisories instructing citizens to remain out of cracked multi-story '
                                       'buildings, avoid unverified social media rumors, and keep roads clear for '
                                       'emergency vehicle convoys.',
                            'hazards': ['road_blockage', 'infrastructure_severance', 'isolated_communities'],
                            'keywords': [   'urban earthquake',
                                            'rural earthquake',
                                            'road blockage',
                                            'debris clearance',
                                            'heavy equipment',
                                            'collapsed roads',
                                            'flyover inspection'],
                            'page': 44,
                            'region': 'india',
                            'section': 'Rural vs Urban Earthquake Incident Command & Road Blockage Clearance',
                            'subdomain': 'earthquake_logistics_command',
                            'substances': []}],
        'doc_id': 'ndma_earthquake_sop_01',
        'organization': 'National Disaster Management Authority (NDMA India)',
        'priority': 'critical',
        'publication_date': '2023-05-15',
        'source_url': 'https://ndma.gov.in/guidelines/earthquake',
        'title': 'NDMA Guidelines for Earthquake Response, Seismic Hazards & Community Shelters'},
    {   'category': 'evacuation',
        'chapters': [   {   'audience': 'commander',
                            'content': 'Standard procedures for executing coordinated population evacuations:\n'
                                       '1. Evacuation vs Shelter-in-Place Protocol: Evacuate immediately if there is '
                                       'imminent threat of structural collapse, advancing wildfire, or rising flood '
                                       'waters. In rapid chemical toxic gas releases, shelter-in-place indoors with '
                                       'closed windows and sealed doors is safer than evacuating on foot into the '
                                       'toxic cloud.\n'
                                       '2. Prioritize Vulnerable Populations: Dedicate specialized transport for '
                                       'hospitals, nursing homes, mobility-impaired individuals, pregnant women, '
                                       'unaccompanied minors, and infants. Assign escort personnel to assist elderly '
                                       'residents.\n'
                                       '3. Primary & Alternate Corridors: Designate clear primary and secondary '
                                       'evacuation corridors. Implement contra-flow traffic control (reversing inbound '
                                       'highway lanes for outbound evacuation) to double corridor capacity.\n'
                                       '4. Temporary Relief Shelters (SPHERE Standards): Ensure minimum 3.5 square '
                                       'meters of covered living space per person. Provide 15 liters of potable '
                                       'drinking water per person per day, and a minimum ratio of 1 latrine per 20 '
                                       'persons separated by gender.',
                            'hazards': ['mass_evacuation', 'traffic_gridlock', 'exposure'],
                            'keywords': [   'evacuation',
                                            'evacuate',
                                            'shelter-in-place',
                                            'assembly point',
                                            'vulnerable populations',
                                            'children',
                                            'elderly',
                                            'mobility-impaired',
                                            'contra-flow'],
                            'page': 14,
                            'region': 'global',
                            'section': 'Evacuation Zoning, Primary/Alternate Routes & Vulnerable Group Priorities',
                            'subdomain': 'evacuation_planning',
                            'substances': []}],
        'doc_id': 'ndma_evacuation_sop_01',
        'organization': 'National Disaster Management Authority (NDMA India) / SPHERE',
        'priority': 'high',
        'publication_date': '2023-08-20',
        'source_url': 'https://ndma.gov.in/guidelines/evacuation',
        'title': 'NDMA / SPHERE Guidelines for Mass Evacuation, Vulnerable Populations & Shelters'},
    {   'category': 'incident_command',
        'chapters': [   {   'audience': 'responder',
                            'content': 'Operational protocol for major passenger train derailments and rail '
                                       'collisions:\n'
                                       '1. 25kV Overhead Traction Wire (OHE) Safety: Responders must NEVER approach, '
                                       'touch, or climb onto derailed rail coaches until the Railway Traction Power '
                                       'Controller (TPC) officially confirms OHE power de-energization and ground '
                                       'discharge rods are physically hooked to the catenary wire. Live 25,000V arcing '
                                       'is lethal at distances up to 2 meters.\n'
                                       '2. Passenger Coach Void Entry: Stabilize tilted coaches with heavy timber '
                                       'baulks and wire rope winches before entering. Use hydraulic shears, '
                                       'cold-cutting reciprocating saws, and plasma cutters to slice through coach '
                                       'end-vestibules and window bars (avoid flame torches where upholstery or '
                                       'spilled diesel fuel is present).\n'
                                       '3. Multi-Vehicle Highway Pileups: Position emergency vehicles in the '
                                       "'fend-off' position (angled at 45 degrees across active highway lanes with "
                                       'front wheels turned away from incident) to deflect oncoming traffic. Establish '
                                       'an advance warning taper with flares or retro-reflective cones 200 meters '
                                       'upstream.',
                            'hazards': ['rail_collision', 'electrocution', 'entrapment', 'crush'],
                            'keywords': [   'railway',
                                            'train derailment',
                                            'rail crash',
                                            'overhead traction',
                                            'ohe wire',
                                            'hydraulic cutters',
                                            'extrication',
                                            'pileup'],
                            'page': 16,
                            'region': 'india',
                            'section': 'Railway Passenger Derailments, Overhead Wire Isolation & Heavy Extrication',
                            'subdomain': 'transport_accidents',
                            'substances': []}],
        'doc_id': 'mha_transport_industrial_sop_01',
        'organization': 'Ministry of Railways / MHA India',
        'priority': 'critical',
        'publication_date': '2023-11-05',
        'source_url': 'https://indianrailways.gov.in/disaster-management',
        'title': 'MHA / Indian Railways Disaster Management Directive: Rail Derailments & Highway Multi-Vehicle '
                 'Crashes'},
    {   'category': 'medical',
        'chapters': [   {   'audience': 'medical',
                            'content': 'Field protocols for environmental emergencies and sudden medical crises:\n'
                                       '1. Heat Stroke (Life-Threatening Emergency): Characterized by core temperature '
                                       '> 40°C (104°F) and altered mental status (confusion, delirium, seizures, coma) '
                                       'with hot, dry or sweaty skin. Immediately initiate whole-body ice-water '
                                       'immersion or rapid evaporative cooling (mist cold water over body while '
                                       'fanning continuously). Place ice packs in axillae (armpits) and groin. Do NOT '
                                       'give antipyretic drugs (paracetamol/aspirin) as they damage the liver.\n'
                                       '2. Heat Exhaustion: Heavy sweating, pale clammy skin, normal mental status, '
                                       'nausea, dizziness. Move to shade, elevate legs, and administer Oral '
                                       'Rehydration Salts (ORS) or cool water slowly.\n'
                                       '3. Accidental Hypothermia: Core temperature < 35°C. Handle casualty extremely '
                                       'gently (rough movement triggers fatal ventricular fibrillation). Strip wet '
                                       'clothing, insulate with warm blankets, apply heat packs to torso only (never '
                                       'limbs first to avoid cold-shock vasodilation).\n'
                                       '4. Submersion Drowning: The primary insult is HYPOXIA. Responders must deliver '
                                       '5 prompt rescue breaths BEFORE initiating chest compressions, then continue '
                                       'standard CPR.\n'
                                       "5. Active Seizures: Protect patient's head from hard surfaces. NEVER force any "
                                       "object into the patient's mouth. Place in recovery position (left lateral "
                                       'recumbent) immediately after convulsions stop to protect airway.\n'
                                       '6. Diabetic Hypoglycemia: If conscious and able to swallow, administer 15 to '
                                       '20 grams of fast-acting oral glucose (fruit juice, candy, glucose tabs). If '
                                       'unconscious, do NOT force liquids into mouth; administer IM glucagon or IV 10% '
                                       'dextrose.',
                            'hazards': ['hyperthermia', 'hypothermia', 'asphyxia', 'metabolic_crisis'],
                            'keywords': [   'heat stroke',
                                            'heat exhaustion',
                                            'hypothermia',
                                            'drowning',
                                            'submersion',
                                            'seizure',
                                            'diabetic',
                                            'hypoglycemia'],
                            'page': 20,
                            'region': 'global',
                            'section': 'Heat Stroke vs Heat Exhaustion, Hypothermia & Submersion Drowning',
                            'subdomain': 'environmental_medical',
                            'substances': []}],
        'doc_id': 'who_environmental_emergencies_04',
        'organization': 'World Health Organization / ERC',
        'priority': 'high',
        'publication_date': '2024-02-12',
        'source_url': 'https://www.who.int/emergencies/environmental-health',
        'title': 'WHO / ERC Protocols for Heat Stroke, Hypothermia, Drowning, Seizures & Diabetic Crises'},
    {   'category': 'cyclones',
        'chapters': [   {   'audience': 'commander',
                            'content': 'India Meteorological Department (IMD) 4-stage cyclone warning framework:\n'
                                       '1. Stage 1 (Pre-Cyclone Watch): Issued 72 hours in advance. Early alert on '
                                       'depression formation in Bay of Bengal or Arabian Sea.\n'
                                       '2. Stage 2 (Cyclone Alert - Yellow): Issued 48 hours prior to expected '
                                       'commencement of adverse weather. Coastal warnings commence, fishing ban '
                                       'enforced.\n'
                                       '3. Stage 3 (Cyclone Warning - Orange): Issued 24 hours in advance. Specifies '
                                       'landfall point, expected wind speed, and estimated storm surge height.\n'
                                       '4. Stage 4 (Post-Landfall Outlook - Red): Issued 12 hours prior to landfall. '
                                       'Mandatory evacuation of coastal settlements within 5 km of shoreline and '
                                       'low-lying storm surge zones to multi-purpose cyclone shelters (MPCS).\n'
                                       '5. Eye of the Cyclone Danger: When the calm eye of the cyclone passes '
                                       'overhead, winds temporarily stop and skies may clear. Responders and citizens '
                                       'must NEVER leave shelter, as the opposite eyewall will strike suddenly with '
                                       'maximum hurricane-force winds from the reverse direction.',
                            'hazards': ['cyclone_winds', 'storm_surge', 'coastal_inundation'],
                            'keywords': [   'cyclone',
                                            'imd alert',
                                            'storm surge',
                                            'cyclone warning',
                                            'yellow alert',
                                            'orange alert',
                                            'red alert',
                                            'cyclone shelter'],
                            'page': 11,
                            'region': 'india',
                            'section': 'IMD 4-Stage Cyclone Warning Stages, Storm Surge & Cyclone Shelter Protocols',
                            'subdomain': 'cyclone_management',
                            'substances': []}],
        'doc_id': 'imd_cyclone_warning_sop_01',
        'organization': 'India Meteorological Department / NDMA India',
        'priority': 'critical',
        'publication_date': '2023-08-10',
        'source_url': 'https://mausam.imd.gov.in/cyclone',
        'title': 'IMD / NDMA Standard Operating Procedure for Cyclonic Storms, Storm Surges & Coastal Shelters'},
    {   'category': 'nuclear_disaster',
        'chapters': [   {   'audience': 'commander',
                            'content': 'AERB & IAEA Nuclear Power Plant (NPP) Emergency Classification and Cordon '
                                       'Zones:\n'
                                       '1. Emergency Classifications: (1) Emergency Alert: Abnormal plant condition, '
                                       'no radioactive release, internal alert only; (2) Plant Emergency: Incident '
                                       'confined within nuclear facility boundary, on-site personnel protected; (3) '
                                       'Site Area Emergency: Major plant degradation, localized release, site boundary '
                                       'monitoring active; (4) General Emergency: Core damage and substantial release '
                                       'of radioactive fission products outside the facility boundary.\n'
                                       '2. Indian Statutory Cordon Zones: (1) Exclusion Zone (0 to 1.6 km around '
                                       'reactor): Total civilian exclusion, high security, full automated perimeter '
                                       'monitoring; (2) Sterilised Zone (1.6 km to 5 km): Regulated residential '
                                       'development, rapid evacuation corridors maintained; (3) Emergency Planning '
                                       'Zone (EPZ, up to 16 km): Mandatory off-site emergency plans, pre-distributed '
                                       'potassium iodide (KI) tablets, dedicated siren alert system.\n'
                                       '3. Immediate Public Protection Directives: At General Emergency trigger, sound '
                                       'continuous undulating 3-minute mechanical sirens, broadcast urgent radio '
                                       'alerts over ResQMesh mesh channels, and enforce immediate shelter-in-place for '
                                       'all populations within the 16 km EPZ.',
                            'hazards': [   'nuclear_meltdown',
                                           'ionizing_radiation',
                                           'fission_products',
                                           'radioactive_plume'],
                            'keywords': [   'nuclear disaster',
                                            'nuclear emergency',
                                            'reactor accident',
                                            'aerb',
                                            'iaea',
                                            'exclusion zone',
                                            'sterilised zone',
                                            'epz',
                                            'radiation alert'],
                            'page': 10,
                            'region': 'india',
                            'section': 'Nuclear Emergency Classification (Alert, Plant, Site, General) & Emergency '
                                       'Planning Zones',
                            'subdomain': 'nuclear_emergency_classification',
                            'substances': ['radiation', 'iodine 131', 'cesium 137', 'strontium 90']},
                        {   'audience': 'responder',
                            'content': 'Operational guidelines for radioactive plume passage and fallout mitigation:\n'
                                       '1. Critical Shelter-in-Place Sealing: Immediately go indoors. Close all '
                                       'exterior windows, doors, and fireplace dampers. Crucial: TURN OFF ALL AIR '
                                       'CONDITIONERS, exhaust fans, HVAC systems, and air intakes to prevent sucking '
                                       'contaminated outside air indoors. Seal window cracks with heavy plastic '
                                       'sheeting and duct tape.\n'
                                       '2. Best Interior Shielding Locations: Move to the center of the building or '
                                       'lowest interior basement. Dense concrete, masonry brick, and earth provide '
                                       'maximum gamma radiation attenuation (a heavy concrete basement cuts gamma dose '
                                       'by 90% or more compared to outdoors).\n'
                                       '3. Safe Evacuation Navigation: Never evacuate directly downwind in the path of '
                                       'the traveling radioactive plume. Responders must route evacuation convoys '
                                       'strictly PERPENDICULAR (crosswind) to prevailing surface wind direction until '
                                       'clearing the 16 km boundary.\n'
                                       '4. Personal Protective Clothing: Responders entering warm zones must wear '
                                       'Level C or B protective suits with Powered Air-Purifying Respirators (PAPR) or '
                                       'SCBA equipped with P100 particulate and iodine vapor sorption filters.',
                            'hazards': ['radioactive_fallout', 'plume_inhalation', 'gamma_shine'],
                            'keywords': [   'radioactive plume',
                                            'shelter in place',
                                            'sealing',
                                            'hvac shutoff',
                                            'fallout',
                                            'downwind evacuation',
                                            'nuclear shelter'],
                            'page': 24,
                            'region': 'global',
                            'section': 'Radioactive Plume Shelter-in-Place, Sealing Protocols & Downwind Evacuation',
                            'subdomain': 'nuclear_shelter_evacuation',
                            'substances': ['radiation', 'fallout']},
                        {   'audience': 'medical',
                            'content': 'WHO / AERB / NDMA Guidelines for Thyroid Blocking with Stable Potassium Iodide '
                                       '(KI):\n'
                                       '1. Mechanism of Action: Potassium Iodide (KI) floods the thyroid gland with '
                                       'non-radioactive stable iodine, preventing the absorption and accumulation of '
                                       'carcinogenic radioactive Iodine-131 released during nuclear reactor accidents. '
                                       'KI protects ONLY the thyroid and does NOT protect against external radiation '
                                       'or other isotopes (e.g. Cesium, Strontium).\n'
                                       '2. Standard Age-Specific Doses: (1) Adults and Adolescents (>12 years / >45 '
                                       'kg): Single daily dose of 130 mg (one standard tablet); (2) Children (3 to 12 '
                                       'years): 65 mg (half tablet); (3) Infants (1 month to 3 years): 32 mg (quarter '
                                       'tablet dissolved in milk/water); (4) Neonates (birth to 1 month): 16 mg '
                                       '(one-eighth tablet).\n'
                                       '3. Optimum Administration Timing: Take KI within 2 to 4 hours BEFORE or '
                                       'IMMEDIATELY UPON exposure to the radioactive plume. Taking KI after 24 hours '
                                       'provides negligible protective value. Pregnant and breastfeeding women are '
                                       'prioritized for KI administration to protect fetal and infant thyroid tissue.\n'
                                       '4. Contraindications: Known iodine allergy, dermatitis herpetiformis, or '
                                       'hypocomplementemic vasculitis.',
                            'hazards': ['thyroid_carcinoma', 'internal_contamination'],
                            'keywords': [   'potassium iodide',
                                            'ki tablets',
                                            'thyroid protection',
                                            'iodine 131',
                                            'dosage',
                                            'thyroid cancer',
                                            'prophylaxis'],
                            'page': 38,
                            'region': 'india',
                            'section': 'Thyroid Prophylaxis: Potassium Iodide (KI) Administration & Dosages',
                            'subdomain': 'nuclear_medical_countermeasures',
                            'substances': ['potassium_iodide', 'iodine_131', 'radiation']},
                        {   'audience': 'responder',
                            'content': 'Field mass radiological decontamination and casualty triage protocols:\n'
                                       '1. Gross Decontamination by Outer Clothing Stripping: Carefully removing outer '
                                       'footwear, jacket, shirts, and pants eliminates OVER 90% OF EXTERNAL '
                                       'CONTAMINATION particles immediately. Place contaminated clothing in heavy '
                                       '6-mil polyethylene bags labeled with biohazard/trefoil tape.\n'
                                       '2. Lukewarm Water Wash: Wash exposed head, hair, face, and hands with lukewarm '
                                       'water and mild neutral detergent. Do NOT use abrasive brushes or hot water '
                                       '(which causes dermal vasodilation and pores to open, driving radioactive '
                                       'particles deeper into skin). Contain all gray wash runoff in lined holding '
                                       'bladders.\n'
                                       '3. Radiac Monitoring & Clearance Criteria: Screen each decontaminated person '
                                       'from head to toe using a calibrated Geiger-Müller survey probe held 1 cm away '
                                       'from the surface without touching. Clearance threshold: Radiation level below '
                                       '1 µSv/h (less than 2 times natural background or < 100 counts per minute).\n'
                                       '4. Internal Contamination Triage: Any casualty with suspected radioisotope '
                                       'ingestion or inhalation must be referred to medical physics units for '
                                       'whole-body counting and chelation therapy (e.g., Prussian Blue for Cesium-137, '
                                       'Ca-DTPA for transuranics).',
                            'hazards': ['external_contamination', 'radiation_exposure'],
                            'keywords': [   'radiological decontamination',
                                            'fallout decon',
                                            'dosimeter',
                                            'portal monitor',
                                            'stripping clothing',
                                            'survey meter'],
                            'page': 52,
                            'region': 'global',
                            'section': 'Mass Radioactive Fallout Decontamination Corridors & Portal Monitoring',
                            'subdomain': 'nuclear_decontamination',
                            'substances': ['radiation', 'fallout_particles']}],
        'doc_id': 'aerb_nuclear_emergency_sop_01',
        'organization': 'Atomic Energy Regulatory Board (AERB India) / IAEA / BARC',
        'priority': 'critical',
        'publication_date': '2024-03-01',
        'source_url': 'https://www.aerb.gov.in/guidelines/nuclear-emergency',
        'title': 'AERB / IAEA Standard Operating Procedure for Nuclear Power Plant Emergencies, Fallout & Thyroid '
                 'Protection'},
    {   'category': 'landslides',
        'chapters': [   {   'audience': 'responder',
                            'content': 'Field recognition of imminent slope failure and landslide evacuation:\n'
                                       '1. Critical Precursor Indicators: (1) Fresh tension cracks opening in soil, '
                                       'paved roads, or foundation slabs; (2) Bulging of ground at slope toe; (3) '
                                       'Sudden tilting of trees, telephone poles, or retaining walls; (4) Rapid change '
                                       'in water flow: crystal clear mountain streams turning suddenly muddy, or '
                                       'springs drying up abruptly; (5) Faint rumbling or cracking sounds of breaking '
                                       'roots and boulders.\n'
                                       '2. Immediate Evacuation Action: When precursor cracks or slope movement are '
                                       'observed, order immediate evacuation of all homes in the runout path. Move '
                                       'strictly LATERAL (sideways across the hill), NEVER run down the natural valley '
                                       'or drainage gulley where debris flows accelerate at speeds up to 50 km/h.\n'
                                       '3. Road Transport Lockdown: Immediately close mountain ghat roads and hill '
                                       'highway passes when cumulative 24-hour monsoon rainfall exceeds 150 mm, as '
                                       'soil pore-water pressure reaches critical saturation.',
                            'hazards': ['slope_failure', 'debris_flow', 'rockfall', 'mudslide'],
                            'keywords': [   'landslide',
                                            'mudflow',
                                            'debris flow',
                                            'slope instability',
                                            'tension cracks',
                                            'bulging slope',
                                            'muddy springs',
                                            'landslide evacuation'],
                            'page': 14,
                            'region': 'india',
                            'section': 'Landslide Geological Precursors (Tension Cracks, Bulges) & Immediate '
                                       'Evacuation',
                            'subdomain': 'landslide_early_warning',
                            'substances': []},
                        {   'audience': 'responder',
                            'content': 'Search and rescue tactical operations in mudflows and debris cones:\n'
                                       '1. Dedicated Secondary Slide Watchers: Position trained Safety Watchers '
                                       'equipped with air-horns and binoculars at high vantage points overlooking the '
                                       'crown of the slide. If upper slope movement or rockfall occurs: THREE BLASTS = '
                                       'IMMEDIATE EVACUATION of all searchers from the debris field.\n'
                                       '2. Tethered Search Lines: Rescuers entering deep fluidized mud must wear '
                                       'safety harnesses connected to belayed synthetic rescue ropes anchored to '
                                       'stable bedrock or large trees outside the slide path.\n'
                                       '3. Searching for Trapped Victims: Use 3-meter fiberglass probing poles in grid '
                                       'patterns. Deploy trained K9 disaster search dogs. In fluidized mud, victim '
                                       'survival time drops rapidly due to mechanical asphyxiation; prioritize surface '
                                       'void spaces and collapsed roof structures.',
                            'hazards': ['secondary_landslide', 'mud_asphyxiation', 'unstable_terrain'],
                            'keywords': [   'landslide sar',
                                            'mud search',
                                            'secondary slide',
                                            'safety lookout',
                                            'tethered search',
                                            'probing poles'],
                            'page': 30,
                            'region': 'india',
                            'section': 'Search & Rescue Operations on Unstable Slopes & Secondary Slide Lookouts',
                            'subdomain': 'landslide_rescue_safety',
                            'substances': []}],
        'doc_id': 'ndma_landslide_sop_01',
        'organization': 'National Disaster Management Authority (NDMA India) / Geological Survey of India',
        'priority': 'critical',
        'publication_date': '2023-09-15',
        'source_url': 'https://ndma.gov.in/guidelines/landslides',
        'title': 'NDMA / GSI Guidelines for Landslide Risk Management, Slope Stabilization & Debris Flow Search'},
    {   'category': 'industrial_disaster',
        'chapters': [   {   'audience': 'commander',
                            'content': 'Emergency procedures for industrial boiler catastrophic ruptures and pressure '
                                       'vessel failures:\n'
                                       '1. Blast Overpressure & Shrapnel Standoff: High-pressure boiler explosions '
                                       'produce supersonic blast waves and heavy metal shrapnel capable of penetrating '
                                       'reinforced concrete up to 500 meters away. Establish an initial safety '
                                       'exclusion zone of at least 800 meters.\n'
                                       '2. Superheated Steam Hazard: Superheated high-pressure steam leaks are '
                                       'INVISIBLE to the naked eye and can instantaneously sever limbs and cause fatal '
                                       'full-thickness scald burns. Responders must approach suspected steam zones '
                                       'holding a wooden corn broom in front of them; the broom fibers will char or '
                                       'ignite upon touching an invisible steam jet.\n'
                                       '3. Cascade Risk Assessment: Immediately check for damaged adjacent ammonia '
                                       'refrigeration lines, fuel oil storage tanks, or chemical pipelines. Enforce '
                                       'automated emergency shutdown (ESD) of all facility gas and fuel valves.',
                            'hazards': ['overpressure_blast', 'shrapnel_projection', 'steam_scalding'],
                            'keywords': [   'boiler explosion',
                                            'pressure vessel',
                                            'industrial accident',
                                            'steam explosion',
                                            'fragment trajectory',
                                            'factory explosion',
                                            'blast radius'],
                            'page': 16,
                            'region': 'india',
                            'section': 'High-Pressure Industrial Boiler Explosions & Fragment Exclusion Zones',
                            'subdomain': 'boiler_blast_response',
                            'substances': ['high_pressure_steam', 'flammable_vapors']},
                        {   'audience': 'responder',
                            'content': 'Tactical response to combustible industrial dust deflagrations:\n'
                                       '1. The Dust Explosion Pentagon: Requires (1) Combustible dust fuel, (2) '
                                       'Atmospheric oxygen, (3) Dispersion of dust into a cloud, (4) Confinement in an '
                                       'enclosed space, and (5) An ignition source (hot bearing, static spark, open '
                                       'flame).\n'
                                       '2. The Deadly Secondary Dust Explosion: The initial minor primary blast '
                                       'dislodges accumulated layers of dust from ceiling beams, rafters, and ducts '
                                       'into suspension, forming a massive dense dust cloud that ignites into a '
                                       'catastrophic secondary explosion destroying the entire facility. Never enter a '
                                       'facility immediately after an initial dust pop.\n'
                                       '3. Housekeeping & Suppression: NEVER use high-pressure air hoses or '
                                       'high-pressure water solid streams to clean or fight dust fires, as this lofts '
                                       'dust into the air creating an explosive cloud. Use fine water fog spray or '
                                       'Class D specialized extinguishing agents.',
                            'hazards': ['combustible_dust_flash', 'secondary_deflagration', 'confinement_blast'],
                            'keywords': [   'dust explosion',
                                            'combustible dust',
                                            'dust pentagon',
                                            'grain dust',
                                            'flour explosion',
                                            'coal dust',
                                            'secondary dust explosion'],
                            'page': 32,
                            'region': 'global',
                            'section': 'Combustible Industrial Dust Explosions (The Dust Explosion Pentagon)',
                            'subdomain': 'dust_explosion_mitigation',
                            'substances': ['organic_dust', 'metallic_dust']}],
        'doc_id': 'ndma_industrial_disaster_sop_01',
        'organization': 'National Disaster Management Authority (NDMA India) / Directorate General Factory Advice',
        'priority': 'critical',
        'publication_date': '2023-11-20',
        'source_url': 'https://ndma.gov.in/guidelines/industrial-disasters',
        'title': 'NDMA / Factory Inspectorate Standard Operating Procedure for Industrial Explosions & High-Pressure '
                 'Boiler Ruptures'},
    {   'category': 'biological_emergency',
        'chapters': [   {   'audience': 'medical',
                            'content': 'Operational guidelines for containment of acute biological outbreaks and '
                                       'respiratory epidemics:\n'
                                       '1. Primary Isolation Architecture: Establish negative-pressure isolation rooms '
                                       '(minimum 12 air changes per hour, exhausted outdoors away from air intakes) '
                                       'for airborne pathogens. Where negative pressure is unavailable, place patients '
                                       'in well-ventilated single rooms with exhaust fans directing air away from '
                                       'hospital corridors.\n'
                                       '2. Standard, Contact & Droplet Precautions: Enforce strict hand hygiene with '
                                       '70% alcohol hand rub or soap and water for 30 seconds. Maintain 2-meter '
                                       'physical distance from symptomatic patients.\n'
                                       '3. Quarantine Management: Contacts of confirmed index cases must complete '
                                       '14-day monitored home or facility quarantine with daily symptom and '
                                       'temperature screening. Restrict visitor access strictly to essential '
                                       'caregivers.',
                            'hazards': ['pathogen_transmission', 'epidemic_surge', 'biological_cross_contamination'],
                            'keywords': [   'biological emergency',
                                            'epidemic',
                                            'outbreak',
                                            'infectious disease',
                                            'quarantine',
                                            'isolation zone',
                                            'droplet precautions',
                                            'airborne precautions'],
                            'page': 12,
                            'region': 'india',
                            'section': 'Infectious Disease Outbreak Containment, Isolation Corridors & Quarantine '
                                       'Principles',
                            'subdomain': 'outbreak_containment',
                            'substances': ['infectious_aerosols', 'pathogens']},
                        {   'audience': 'responder',
                            'content': 'Strict personal protective equipment protocols for high-consequence biological '
                                       'hazards:\n'
                                       '1. Donning Sequence: Hand hygiene -> Gown/Tyvek coverall -> N95/FFP3 '
                                       'respirator (perform user seal check: positive and negative pressure tests) -> '
                                       'Eye protection (goggles or face shield) -> Double nitrile examination gloves '
                                       '(inner glove under cuff, outer glove over cuff).\n'
                                       '2. Doffing Sequence (Highest Risk of Self-Contamination): Clean gloved hands '
                                       'with sanitizer -> Remove outer gloves inside-out -> Remove gown pulling '
                                       'forward away from body -> Hand hygiene -> Remove goggles touching only '
                                       'head-strap -> Remove respirator touching only rear elastic straps (NEVER touch '
                                       'front of mask) -> Remove inner gloves -> Final alcohol hand rub.\n'
                                       '3. Biohazard Waste Management: Double-bag all contaminated PPE and patient '
                                       'dressings in yellow clinical waste bags. Disinfect surfaces with freshly '
                                       'prepared 0.5% (5,000 ppm) sodium hypochlorite solution leaving surface wet for '
                                       'at least 10 minutes before wiping.',
                            'hazards': ['self_contamination', 'biohazard_exposure'],
                            'keywords': [   'biological ppe',
                                            'donning doffing',
                                            'n95 respirator',
                                            'face shield',
                                            'biohazard waste',
                                            'autoclaving',
                                            'chlorine 0.5 percent'],
                            'page': 28,
                            'region': 'global',
                            'section': 'Biological PPE Donning/Doffing Sequences & Biohazard Waste Disinfection',
                            'subdomain': 'biological_ppe_safety',
                            'substances': ['biohazard']}],
        'doc_id': 'who_epidemic_containment_sop_01',
        'organization': 'World Health Organization / National Centre for Disease Control (NCDC India)',
        'priority': 'critical',
        'publication_date': '2024-01-25',
        'source_url': 'https://www.who.int/emergencies/infectious-disease-protocols',
        'title': 'WHO / NCDC Guidelines for Biological Epidemics, Infectious Outbreak Isolation & PPE Protocols'},
    {   'category': 'disaster_logistics',
        'chapters': [   {   'audience': 'commander',
                            'content': 'Disaster logistics and field supply chain management protocols:\n'
                                       '1. Staging Area Selection & Layout: Select flat, well-drained staging areas '
                                       'adjacent to major highway arteries or airport tarmac outside the disaster '
                                       'impact zone. Designate distinct zones: (1) Vehicle Ingress / Reception; (2) '
                                       'Unloading & Inspection; (3) Palletized Storage (dry food, non-food items, '
                                       'medical supplies); (4) Emergency Vehicle Marshalling & Dispatch; (5) Secure '
                                       'Security Cordon.\n'
                                       '2. First-In, First-Out (FIFO) Inventory Control: Stack goods on pallets at '
                                       'least 10 cm off the floor and 50 cm away from walls to prevent moisture damage '
                                       'and rodent infestation. Log all inbound consignments with cargo receipts, lot '
                                       'numbers, and expiration dates.\n'
                                       '3. Priority Dispatch Scheduling: Schedule relief dispatches during daylight '
                                       'hours with security escorts for high-value medical supplies and baby nutrition '
                                       'consignments.',
                            'hazards': ['logistics_bottleneck', 'relief_spoilage', 'transport_failure'],
                            'keywords': [   'disaster logistics',
                                            'staging area',
                                            'warehouse management',
                                            'marshalling yard',
                                            'supply chain',
                                            'cargo tracking',
                                            'relief supplies'],
                            'page': 14,
                            'region': 'india',
                            'section': 'Incident Staging Area Management, Marshalling Yards & Warehouse Layout',
                            'subdomain': 'staging_area_logistics',
                            'substances': []},
                        {   'audience': 'responder',
                            'content': 'Critical cold-chain and fuel security directives:\n'
                                       '1. Medical Cold-Chain Storage: Vaccines, insulin, and whole blood units must '
                                       'be maintained between +2°C and +8°C at all times. Use ice-lined refrigerators '
                                       '(ILR) with dedicated backup generator power or passive solar-powered vaccine '
                                       'coolers. Monitor temperatures twice daily.\n'
                                       '2. Emergency Fuel Rationing Matrix: When grid power fails and fuel supply '
                                       'lines are cut, fuel is strictly rationed according to priority: (1) Hospital '
                                       'ICU / Emergency Room generators (100% allocation); (2) Water pumping stations '
                                       '(80%); (3) Emergency response ambulances and fire tenders; (4) '
                                       'Telecommunications cell-tower generators; (5) General public transport.\n'
                                       '3. Diesel Storage Safety: Store emergency diesel in double-walled bunded tanks '
                                       'with dry powder fire extinguishers staged within 10 meters. Prohibit all '
                                       'smoking and open flames within 50 meters.',
                            'hazards': ['cold_chain_breakage', 'fuel_exhaustion'],
                            'keywords': [   'cold chain',
                                            'vaccine storage',
                                            'blood transport',
                                            'fuel rationing',
                                            'generator fuel',
                                            'diesel allocation'],
                            'page': 30,
                            'region': 'global',
                            'section': 'Cold-Chain Integrity, Vaccine/Blood Transport & Emergency Fuel Rationing',
                            'subdomain': 'cold_chain_fuel_rationing',
                            'substances': []}],
        'doc_id': 'ndma_disaster_logistics_sop_01',
        'organization': 'National Disaster Management Authority (NDMA India) / World Food Programme',
        'priority': 'high',
        'publication_date': '2023-10-25',
        'source_url': 'https://ndma.gov.in/guidelines/disaster-logistics',
        'title': 'NDMA / WFP Emergency Logistics Guidelines: Staging Areas, Warehouse Management & Cold-Chain Supply'},
    {   'category': 'public_health',
        'chapters': [   {   'audience': 'responder',
                            'content': 'Emergency water supply quality standards and field purification protocols:\n'
                                       '1. Minimum Water Quantity: Ensure minimum SPHERE quantity of 15 liters of '
                                       'potable water per person per day (3-5 L for drinking/cooking, 10 L for '
                                       'personal hygiene).\n'
                                       '2. Batch Chlorination of Water Tanks: Add 5 grams of high-test calcium '
                                       'hypochlorite (HTH, 70% available chlorine) per 1,000 liters of water. Dissolve '
                                       'granules in a plastic bucket before pouring into tank. Agitate thoroughly and '
                                       'allow at least 30 minutes contact time before public distribution.\n'
                                       '3. Free Residual Chlorine (FRC) Target: Test water at distribution taps using '
                                       'a DPD-1 colorimetric comparator. Target FRC is 0.5 mg/L (ppm) at delivery '
                                       'point; during active cholera or dysentery outbreaks, increase target FRC to '
                                       '1.0 mg/L.\n'
                                       '4. Turbidity Reduction: If raw water turbidity is > 5 NTU, pre-treat with '
                                       'chemical coagulation (alum / aluminium sulfate at 10-30 mg/L) or sand '
                                       'filtration prior to chlorination, as suspended silt protects bacteria from '
                                       'chlorine disinfection.',
                            'hazards': ['waterborne_disease', 'diarrheal_outbreak', 'arsenic_fluoride'],
                            'keywords': [   'public health',
                                            'water purification',
                                            'chlorination',
                                            'residual chlorine',
                                            'wash',
                                            'water testing',
                                            'potable water'],
                            'page': 10,
                            'region': 'global',
                            'section': 'Emergency Drinking Water Purification & Free Residual Chlorine Testing',
                            'subdomain': 'emergency_water_quality',
                            'substances': []},
                        {   'audience': 'responder',
                            'content': 'Field excreta disposal and vector management in displacement settlements:\n'
                                       '1. Immediate Phase Shallow Trench Latrines: Dig trenches 0.3 meters wide and 1 '
                                       'to 1.5 meters deep. Provide wooden foot-rests. Each user covers excreta with a '
                                       'layer of excavated soil. Fill and abandon trench when waste reaches within 30 '
                                       'cm of ground surface.\n'
                                       '2. Latrine Ratios & Placement: Minimum 1 latrine stall per 20 persons. '
                                       'Latrines must be located at least 30 meters away from any ground water source '
                                       '(well, spring) and at least 1.5 meters above the seasonal high water table. '
                                       'Separate male and female latrines with internal privacy locks and solar '
                                       'night-lighting.\n'
                                       '3. Handwashing Stations: Install tippy-tap or pedal-operated handwashing '
                                       'stands with soap within 5 meters of every latrine bank. Enforce handwashing '
                                       'with soap after defecation and before food preparation.\n'
                                       '4. Vector & Mosquito Control: Eliminate standing stagnant water puddles to '
                                       'suppress Aedes and Anopheles breeding. Apply larvicide (Bti or temephos) to '
                                       'unmanaged water pools and distribute insecticide-treated bed nets (ITNs) to '
                                       'shelter residents.',
                            'hazards': ['fecal_oral_transmission', 'vector_breeding', 'dengue_malaria'],
                            'keywords': [   'latrines',
                                            'excreta disposal',
                                            'sanitation',
                                            'vector control',
                                            'trench latrine',
                                            'handwashing stations',
                                            'fly breeding'],
                            'page': 24,
                            'region': 'global',
                            'section': 'Emergency Latrines, Excreta Disposal & Vector-Borne Disease Control',
                            'subdomain': 'emergency_sanitation_latrines',
                            'substances': []}],
        'doc_id': 'who_disaster_sanitation_sop_01',
        'organization': 'World Health Organization / Sphere Standards',
        'priority': 'high',
        'publication_date': '2024-02-18',
        'source_url': 'https://www.who.int/water_sanitation_health/emergencies',
        'title': 'WHO / Sphere Guidelines for Emergency Water Purification, Sanitation & Hygiene (WASH)'}]
