import json


def load_diagnoses(path="data/diagnoses.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_romanian_knowledge(path="data/allergy_knowledge_ro.json"):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {item["name"].lower(): item for item in data}


def normalize_text(text):
    text = (text or "").lower().strip()

    replacements = {
        "stranut": "strănut",
        "lacrimare": "lăcrimare",
        "mancarime nazala": "prurit nazal",
        "mancarime oculara": "prurit ocular",
        "mancarime la ochi": "prurit ocular",
        "mancarime ochi": "prurit ocular",
        "mancarime piele": "prurit cutanat",
        "tuse noaptea": "tuse nocturnă",
        "respiratie grea": "dispnee",
        "nas infundat": "nas înfundat",
        "ochi rosii": "ochi roșii",
        "reactie dupa aliment": "reacție după aliment",
        "dupa masa": "după masă",
        "suieraturi": "șuierături",
        "varsaturi": "vărsături",
        "ameteala": "amețeală",
        "soc": "șoc",
        "voce ragusita": "voce răgușită",
        "dificultati la inghitire": "dificultăți la înghițire",
        "fara aer": "dispnee",
        "senzatie de sufocare": "dispnee severă",
        "limba umflata": "edem lingual",
        "buze umflate": "edem buze",
        "pleoape umflate": "edem pleoape",
        "curge nasul": "rinoree",
        "curge nas": "rinoree",
        "nas care curge": "rinoree",
        "pete pe piele": "urticarie",
        "blande": "urticarie",
        "eczema": "dermatită",
        "rosu in ochi": "ochi roșii",
        "apasare in piept": "constricție toracică",
        "strangere in piept": "constricție toracică",
        "mancarime in gat": "prurit faringian",
        "umflare gat": "edem faringian"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def contains_any(text, terms):
    return any(term in text for term in terms)


def deduplicate(items):
    seen = set()
    result = []
    for item in items:
        cleaned = (item or "").strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def parse_age(age_value):
    if age_value is None:
        return None

    if isinstance(age_value, (int, float)):
        return int(age_value)

    text = str(age_value).strip().replace(",", ".")
    digits = ""

    for ch in text:
        if ch.isdigit():
            digits += ch
        elif digits:
            break

    if not digits:
        return None

    try:
        return int(digits)
    except Exception:
        return None


def parse_weight(weight_value):
    if weight_value is None:
        return None

    if isinstance(weight_value, (int, float)):
        return float(weight_value)

    text = str(weight_value).strip().replace(",", ".")
    cleaned = ""
    dot_seen = False

    for ch in text:
        if ch.isdigit():
            cleaned += ch
        elif ch == "." and not dot_seen:
            cleaned += ch
            dot_seen = True
        elif cleaned:
            break

    if not cleaned or cleaned == ".":
        return None

    try:
        return float(cleaned)
    except Exception:
        return None


def age_group_label(age):
    if age is None:
        return "vârstă neprecizată"
    if age < 2:
        return "< 2 ani"
    if age <= 5:
        return "2–5 ani"
    if age <= 11:
        return "6–11 ani"
    if age <= 17:
        return "12–17 ani"
    return "adult"


def normalize_severity(severity_value, fallback_text=""):
    value = (severity_value or "").strip().lower()

    mapping = {
        "usoara": "ușoară",
        "ușoară": "ușoară",
        "moderata": "moderată",
        "moderată": "moderată",
        "severa": "severă",
        "severă": "severă"
    }

    if value in mapping:
        return mapping[value]

    if value:
        return value

    return classify_severity(fallback_text)


def score_to_probability(score):
    if score >= 10:
        return "mare"
    if score >= 5:
        return "moderată"
    return "redusă"


def classify_severity(text):
    text = normalize_text(text)

    severe_terms = [
        "dispnee severă", "hipotensiune", "șoc", "edem lingual",
        "angioedem", "stridor", "voce răgușită", "dificultăți la înghițire",
        "cianoză", "saturație mică", "pierderea conștienței", "lipotimie",
        "edem faringian"
    ]
    moderate_terms = [
        "wheezing", "dispnee", "tuse nocturnă", "șuierături",
        "edem buze", "edem pleoape", "urticarie extinsă", "constricție toracică"
    ]

    if contains_any(text, severe_terms):
        return "severă"
    if contains_any(text, moderate_terms):
        return "moderată"
    return "ușoară"


def infer_allergic_pattern(text):
    patterns = []

    if contains_any(text, ["polen", "primăvara", "sezon", "sezoniere", "iarbă", "ambrozie"]):
        patterns.append("pattern sezonier / polinic")

    if contains_any(text, ["acarieni", "praf", "praf de casă", "saltea", "pernă"]):
        patterns.append("pattern posibil peren, sugestiv pentru expunere la acarieni")

    if contains_any(text, ["pisică", "câine", "animal", "blană"]):
        patterns.append("pattern sugestiv pentru expunere la epitelii de animale")

    if contains_any(text, ["după masă", "aliment", "lapte", "ou", "arahide", "nuci", "fructe de mare"]):
        patterns.append("pattern sugestiv pentru reacție de cauză alimentară")

    if contains_any(text, ["tuse nocturnă", "șuierături", "wheezing", "efort"]):
        patterns.append("pattern sugestiv pentru afectare bronșică variabilă")

    return patterns


def determine_confidence(ranked):
    if not ranked:
        return "scăzută"

    if len(ranked) == 1:
        return "moderată"

    diff = ranked[0]["score"] - ranked[1]["score"]

    if ranked[0]["score"] >= 8 and diff >= 3:
        return "mare"
    if diff >= 2:
        return "moderată"
    return "scăzută"


def build_supports(text, primary_name):
    supports = []

    if contains_any(text, ["strănut", "rinoree", "prurit nazal", "nas înfundat"]):
        supports.append("Simptomatologia nazală este compatibilă cu afectare alergică de căi aeriene superioare.")

    if contains_any(text, ["lăcrimare", "prurit ocular", "ochi roșii"]):
        supports.append("Asocierea manifestărilor oculare susține o componentă de conjunctivită alergică.")

    if contains_any(text, ["wheezing", "șuierături", "dispnee", "tuse nocturnă", "constricție toracică"]):
        supports.append("Prezența wheezing-ului, dispneei, tusei nocturne sau a constricției toracice ridică suspiciunea de astm alergic.")

    if contains_any(text, ["urticarie", "angioedem", "edem buze", "edem pleoape"]):
        supports.append("Manifestările cutanate/edematoase susțin o reacție alergică sistemică sau cutaneo-mucoasă.")

    if contains_any(text, ["eczeme", "dermatită", "prurit cutanat", "leziuni", "piele uscată"]):
        supports.append("Leziunile cutanate pruriginoase și contextul atopic pot orienta către dermatită atopică.")

    if contains_any(text, ["după masă", "aliment", "prurit oral", "prurit faringian", "vărsături", "dureri abdominale", "diaree"]):
        supports.append("Corelația temporală cu ingestia alimentară susține suspiciunea de alergie alimentară.")

    if "anafilaxie" in (primary_name or "").lower():
        supports.append("Asocierea manifestărilor respiratorii, cutanate, digestive sau hemodinamice impune evaluarea posibilității de anafilaxie.")

    return deduplicate(supports)


def build_limits(text):
    limits = []

    if contains_any(text, ["febră", "frison", "hemoptizie", "durere toracică intensă", "spută purulentă"]):
        limits.append("Prezența unor simptome atipice pentru alergie impune excluderea unei cauze infecțioase, inflamatorii sau a altei patologii non-alergice.")
    else:
        limits.append("Absența semnelor infecțioase majore susține o cauză non-infecțioasă, dar nu stabilește singură diagnosticul.")

    if not contains_any(text, ["polen", "acarieni", "praf", "pisică", "câine", "aliment", "după masă", "sezon"]):
        limits.append("Lipsa unui factor declanșator clar reduce specificitatea orientării etiologice și necesită anamneză suplimentară.")

    return deduplicate(limits)


def build_red_flags(text):
    red_flags = []

    severe_allergy = [
        "dispnee severă", "hipotensiune", "șoc", "edem lingual",
        "angioedem", "stridor", "voce răgușită", "dificultăți la înghițire",
        "pierderea conștienței", "lipotimie", "edem faringian"
    ]
    non_allergic_alarm = [
        "febră", "hemoptizie", "durere toracică intensă", "cianoză"
    ]

    if contains_any(text, severe_allergy):
        red_flags.append("Semne compatibile cu reacție alergică severă / anafilaxie posibilă — necesită evaluare medicală de urgență.")

    if contains_any(text, ["wheezing sever", "dispnee severă", "nu poate vorbi", "tiraj"]):
        red_flags.append("Suspiciune de afectare respiratorie severă — necesită evaluare urgentă și monitorizare clinică.")

    if contains_any(text, non_allergic_alarm):
        red_flags.append("Prezența unor semne de alarmă impune excluderea altor cauze acute non-alergice.")

    return deduplicate(red_flags)


def build_recommended_tests(text, primary_name):
    tests = []

    primary_name = (primary_name or "").lower()

    if contains_any(primary_name, ["rinită", "conjunctivită"]):
        tests.extend([
            "Anamneză orientată pe sezonalitate, expuneri și context ocupațional/domestic.",
            "Teste cutanate prick sau IgE specifice pentru alergeni inhalatori, în funcție de contextul clinic.",
            "Evaluare ORL / oftalmologică dacă simptomatologia este persistentă sau atipică."
        ])

    if "astm" in primary_name or contains_any(text, ["wheezing", "dispnee", "șuierături", "tuse nocturnă", "constricție toracică"]):
        tests.extend([
            "Spirometrie cu test bronhodilatator, dacă este disponibilă.",
            "Monitorizarea variabilității simptomelor și a factorilor declanșatori.",
            "Evaluare alergologică pentru sensibilizări inhalatorii relevante clinic."
        ])

    if contains_any(primary_name, ["dermatită"]):
        tests.extend([
            "Examinare dermatologică / alergologică și evaluarea factorilor iritativi sau alergici.",
            "Corelare clinică atentă înainte de a atribui exclusiv etiologia alergică."
        ])

    if contains_any(primary_name, ["urticarie", "angioedem"]):
        tests.extend([
            "Anamneză pentru medicamente, alimente, înțepături, infecții și factori fizici declanșatori.",
            "Evaluare alergologică doar în context clinic sugestiv; nu toate urticariile sunt de cauză alergică."
        ])

    if "alergie alimentară" in primary_name:
        tests.extend([
            "Anamneză detaliată privind alimentul suspect, intervalul până la debut și reproducibilitatea reacției.",
            "Teste alergologice specifice doar în corelare cu tabloul clinic.",
            "Evaluare de specialitate dacă există reacții sistemice sau suspiciune de anafilaxie."
        ])

    if "anafilaxie" in primary_name:
        tests.extend([
            "Evaluare medicală de urgență; prioritatea este stabilizarea clinică, nu testarea imediată extensivă.",
            "Ulterior: evaluare alergologică pentru identificarea triggerului probabil."
        ])

    if not tests:
        tests.extend([
            "Anamneză extinsă privind contextul de apariție, expuneri și recurența simptomelor.",
            "Corelare clinică și alegerea investigațiilor în funcție de diagnosticul cel mai probabil."
        ])

    return deduplicate(tests)


def build_treatment_plan(text, primary_name, severity):
    plan = []
    primary_name = (primary_name or "").lower()

    if "rinită" in primary_name:
        plan.extend([
            "Măsuri de evitare a alergenului relevant clinic, dacă acesta poate fi identificat.",
            "Lavaj nazal cu ser salin, în funcție de toleranță și context.",
            "Antihistaminic oral și/sau corticosteroid intranazal, conform contextului clinic și recomandărilor medicale."
        ])

    if "conjunctivită" in primary_name:
        plan.extend([
            "Evitarea expunerilor iritative/alergenice și igiena oculară adecvată.",
            "Antihistaminic ocular/oral, după caz și conform recomandărilor medicale."
        ])

    if "astm" in primary_name:
        plan.extend([
            "Evaluare a controlului simptomelor și a frecvenței episoadelor respiratorii.",
            "Bronhodilatator de salvare și tratament controller conform severității și recomandării medicale.",
            "Educație privind tehnica inhalatorie și monitorizarea exacerbărilor."
        ])

    if "dermatită" in primary_name:
        plan.extend([
            "Emoliere susținută și evitare a iritanților cutanați.",
            "Tratament antiinflamator topic conform severității și recomandării medicale.",
            "Reevaluare dacă leziunile sunt extinse, infectate sau slab controlate."
        ])

    if "urticarie" in primary_name or "angioedem" in primary_name:
        plan.extend([
            "Identificarea și evitarea factorului declanșator posibil, dacă este plauzibil clinic.",
            "Antihistaminic conform recomandărilor medicale și reevaluare dacă episoadele recidivează.",
            "Urmărire atentă dacă apar semne respiratorii sau de afectare sistemică."
        ])

    if "alergie alimentară" in primary_name:
        plan.extend([
            "Evitarea alimentului suspect până la clarificare de specialitate, dacă relația temporală este convingătoare.",
            "Educație privind citirea etichetelor și evitarea expunerilor accidentale.",
            "Evaluare alergologică dacă tabloul este repetitiv sau sever."
        ])

    if "anafilaxie" in primary_name:
        plan.extend([
            "Situație cu potențial vital — necesită protocol de urgență și evaluare imediată.",
            "După stabilizare: clarificarea triggerului și plan de prevenție secundară."
        ])

    if severity == "severă":
        plan.append("Severitatea estimată impune prag scăzut pentru trimitere / evaluare medicală urgentă.")
    elif severity == "moderată":
        plan.append("Necesită reevaluare clinică și monitorizarea evoluției pe termen scurt.")

    if not plan:
        plan.append("Tratamentul trebuie individualizat în funcție de tabloul clinic, severitate și contextul pacientului.")

    return deduplicate(plan)


def build_notes(text, ranked):
    notes = []

    patterns = infer_allergic_pattern(text)
    if patterns:
        notes.append("Pattern clinic sugerat: " + "; ".join(patterns) + ".")

    if ranked:
        if len(ranked) >= 2 and ranked[0]["score"] == ranked[1]["score"]:
            notes.append("Există proximitate de scor între primele ipoteze diagnostice; este necesară diferențiere clinică suplimentară.")
        elif len(ranked) >= 2 and (ranked[0]["score"] - ranked[1]["score"] <= 1):
            notes.append("Diferențierea între primele ipoteze diagnostice rămâne moderată și necesită corelare clinică atentă.")

    notes.append("Rezultatul este orientativ și trebuie corelat cu anamneza completă, examenul clinic și investigațiile paraclinice.")
    return deduplicate(notes)


def format_weight_value(weight):
    if weight is None:
        return ""
    return f"{weight:.1f} kg"


def calculate_mg_per_kg(weight, mg_per_kg, max_total_mg=None):
    if weight is None:
        return None
    dose = weight * mg_per_kg
    if max_total_mg is not None:
        dose = min(dose, max_total_mg)
    return round(dose, 2)


def build_weight_hint(weight, text_if_missing, text_if_present):
    if weight is None:
        return text_if_missing
    return text_if_present


def build_medication_entry(
    med_class,
    active_substance,
    pharmacologic_name,
    administration_route,
    frequency,
    adult_dose,
    pediatric_dose,
    observations="",
    weight_based_dose="",
    severity_adjustment="",
    adverse_reactions=""
):
    return {
        "class": med_class,
        "active_substance": active_substance,
        "pharmacologic_name": pharmacologic_name,
        "administration_route": administration_route,
        "frequency": frequency,
        "adult_dose": adult_dose,
        "pediatric_dose": pediatric_dose,
        "observations": observations,
        "weight_based_dose": weight_based_dose,
        "severity_adjustment": severity_adjustment,
        "adverse_reactions": adverse_reactions
    }


def get_age_based_antihistamine_options(age, weight=None, severity=""):
    meds = []
    severity_text = normalize_severity(severity)

    cetirizine_weight = ""
    loratadine_weight = ""
    desloratadine_weight = ""

    if weight is not None:
        cet_dose = calculate_mg_per_kg(weight, 0.25, max_total_mg=10)
        lor_dose = calculate_mg_per_kg(weight, 0.2, max_total_mg=10)
        desl_dose = calculate_mg_per_kg(weight, 0.125, max_total_mg=5)

        cetirizine_weight = (
            f"Greutate introdusă: {format_weight_value(weight)}. "
            f"Orientativ, doza zilnică poate fi estimată la ~0,25 mg/kg/zi "
            f"(≈ {cet_dose} mg/zi, fără a depăși uzual 10 mg/zi), cu verificarea formei farmaceutice."
        )
        loratadine_weight = (
            f"Greutate introdusă: {format_weight_value(weight)}. "
            f"Orientativ, doza zilnică poate fi estimată la ~0,2 mg/kg/zi "
            f"(≈ {lor_dose} mg/zi, fără a depăși uzual 10 mg/zi), cu verificarea produsului disponibil."
        )
        desloratadine_weight = (
            f"Greutate introdusă: {format_weight_value(weight)}. "
            f"Orientativ, doza zilnică poate fi estimată la ~0,125 mg/kg/zi "
            f"(≈ {desl_dose} mg/zi, fără a depăși uzual 5 mg/zi), cu verificarea formei farmaceutice."
        )

    severity_adjustment = ""
    if severity_text == "moderată":
        severity_adjustment = "În forme moderate se poate prefera asocierea cu măsuri locale și reevaluare clinică precoce."
    elif severity_text == "severă":
        severity_adjustment = "În forme severe, antihistaminicul singur poate fi insuficient; reevaluează diagnosticul, afectarea sistemică și necesitatea trimiterii."

    cetirizine_adverse = "Somnolență, xerostomie, cefalee, ocazional amețeală."
    loratadine_adverse = "Cefalee, fatigabilitate, xerostomie; sedarea este de obicei redusă."
    desloratadine_adverse = "Cefalee, xerostomie, fatigabilitate; rar palpitații sau reacții de hipersensibilitate."

    if age is None:
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Cetirizină",
            pharmacologic_name="Cetirizină clorhidrat",
            administration_route="oral",
            frequency="o dată pe zi",
            adult_dose="5–10 mg/zi",
            pediatric_dose="2–5 ani: 2,5 mg/zi; dacă este necesar până la 5 mg/zi. ≥6 ani: 5–10 mg/zi.",
            observations="Ajustarea exactă depinde de forma farmaceutică și contextul clinic.",
            weight_based_dose=cetirizine_weight,
            severity_adjustment=severity_adjustment,
            adverse_reactions=cetirizine_adverse
        ))
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Loratadină",
            pharmacologic_name="Loratadină",
            administration_route="oral",
            frequency="o dată pe zi",
            adult_dose="10 mg/zi",
            pediatric_dose="2–5 ani: 5 mg/zi. ≥6 ani: 10 mg/zi.",
            observations="Sub 2 ani: este necesară evaluare medicală individuală.",
            weight_based_dose=loratadine_weight,
            severity_adjustment=severity_adjustment,
            adverse_reactions=loratadine_adverse
        ))
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Desloratadină",
            pharmacologic_name="Desloratadină",
            administration_route="oral",
            frequency="o dată pe zi",
            adult_dose="5 mg/zi",
            pediatric_dose="1–5 ani: 1,25 mg/zi; 6–11 ani: 2,5 mg/zi; ≥12 ani: 5 mg/zi.",
            observations="Utilă în rinită alergică și urticarie, în funcție de context.",
            weight_based_dose=desloratadine_weight,
            severity_adjustment=severity_adjustment,
            adverse_reactions=desloratadine_adverse
        ))
        return meds

    if age < 2:
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Cetirizină / Loratadină / Desloratadină",
            pharmacologic_name="Antihistaminice H1 de generația a 2-a",
            administration_route="oral",
            frequency="în funcție de produs",
            adult_dose="Nu se aplică",
            pediatric_dose="Sub 2 ani: alegerea și doza trebuie individualizate strict de medic, în funcție de produs și context.",
            observations="Evită automatizarea dozei la această grupă de vârstă.",
            weight_based_dose=f"Greutate introdusă: {format_weight_value(weight)}" if weight is not None else "",
            severity_adjustment=severity_adjustment,
            adverse_reactions="Somnolență, iritabilitate, xerostomie, tulburări digestive ușoare; profilul depinde de substanța aleasă."
        ))
        return meds

    if 2 <= age <= 5:
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Cetirizină",
            pharmacologic_name="Cetirizină clorhidrat",
            administration_route="oral",
            frequency="o dată pe zi sau divizat la 12 ore",
            adult_dose="Nu se aplică",
            pediatric_dose="2,5 mg/zi; dacă este necesar până la 5 mg/zi sau 2,5 mg la 12 ore.",
            observations="Orientează doza după forma farmaceutică disponibilă.",
            weight_based_dose=cetirizine_weight,
            severity_adjustment=severity_adjustment,
            adverse_reactions=cetirizine_adverse
        ))
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Loratadină",
            pharmacologic_name="Loratadină",
            administration_route="oral",
            frequency="o dată pe zi",
            adult_dose="Nu se aplică",
            pediatric_dose="5 mg/zi",
            observations="",
            weight_based_dose=loratadine_weight,
            severity_adjustment=severity_adjustment,
            adverse_reactions=loratadine_adverse
        ))
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Desloratadină",
            pharmacologic_name="Desloratadină",
            administration_route="oral",
            frequency="o dată pe zi",
            adult_dose="Nu se aplică",
            pediatric_dose="1,25 mg/zi",
            observations="",
            weight_based_dose=desloratadine_weight,
            severity_adjustment=severity_adjustment,
            adverse_reactions=desloratadine_adverse
        ))
        return meds

    if 6 <= age <= 11:
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Cetirizină",
            pharmacologic_name="Cetirizină clorhidrat",
            administration_route="oral",
            frequency="o dată pe zi",
            adult_dose="Nu se aplică",
            pediatric_dose="5–10 mg/zi",
            observations="Alege doza după severitate și toleranță.",
            weight_based_dose=cetirizine_weight,
            severity_adjustment=severity_adjustment,
            adverse_reactions=cetirizine_adverse
        ))
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Loratadină",
            pharmacologic_name="Loratadină",
            administration_route="oral",
            frequency="o dată pe zi",
            adult_dose="Nu se aplică",
            pediatric_dose="10 mg/zi",
            observations="",
            weight_based_dose=loratadine_weight,
            severity_adjustment=severity_adjustment,
            adverse_reactions=loratadine_adverse
        ))
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Desloratadină",
            pharmacologic_name="Desloratadină",
            administration_route="oral",
            frequency="o dată pe zi",
            adult_dose="Nu se aplică",
            pediatric_dose="2,5 mg/zi",
            observations="",
            weight_based_dose=desloratadine_weight,
            severity_adjustment=severity_adjustment,
            adverse_reactions=desloratadine_adverse
        ))
        return meds

    if 12 <= age <= 17:
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Cetirizină",
            pharmacologic_name="Cetirizină clorhidrat",
            administration_route="oral",
            frequency="o dată pe zi",
            adult_dose="Nu se aplică",
            pediatric_dose="5–10 mg/zi",
            observations="Doză uzuală de adolescent.",
            weight_based_dose=cetirizine_weight,
            severity_adjustment=severity_adjustment,
            adverse_reactions=cetirizine_adverse
        ))
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Loratadină",
            pharmacologic_name="Loratadină",
            administration_route="oral",
            frequency="o dată pe zi",
            adult_dose="Nu se aplică",
            pediatric_dose="10 mg/zi",
            observations="",
            weight_based_dose=loratadine_weight,
            severity_adjustment=severity_adjustment,
            adverse_reactions=loratadine_adverse
        ))
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Desloratadină",
            pharmacologic_name="Desloratadină",
            administration_route="oral",
            frequency="o dată pe zi",
            adult_dose="Nu se aplică",
            pediatric_dose="5 mg/zi",
            observations="",
            weight_based_dose=desloratadine_weight,
            severity_adjustment=severity_adjustment,
            adverse_reactions=desloratadine_adverse
        ))
        return meds

    meds.append(build_medication_entry(
        med_class="Antihistaminic oral",
        active_substance="Cetirizină",
        pharmacologic_name="Cetirizină clorhidrat",
        administration_route="oral",
        frequency="o dată pe zi",
        adult_dose="5–10 mg/zi",
        pediatric_dose="Nu se aplică",
        observations="",
        weight_based_dose=cetirizine_weight,
        severity_adjustment=severity_adjustment,
        adverse_reactions=cetirizine_adverse
    ))
    meds.append(build_medication_entry(
        med_class="Antihistaminic oral",
        active_substance="Loratadină",
        pharmacologic_name="Loratadină",
        administration_route="oral",
        frequency="o dată pe zi",
        adult_dose="10 mg/zi",
        pediatric_dose="Nu se aplică",
        observations="",
        weight_based_dose=loratadine_weight,
        severity_adjustment=severity_adjustment,
        adverse_reactions=loratadine_adverse
    ))
    meds.append(build_medication_entry(
        med_class="Antihistaminic oral",
        active_substance="Desloratadină",
        pharmacologic_name="Desloratadină",
        administration_route="oral",
        frequency="o dată pe zi",
        adult_dose="5 mg/zi",
        pediatric_dose="Nu se aplică",
        observations="",
        weight_based_dose=desloratadine_weight,
        severity_adjustment=severity_adjustment,
        adverse_reactions=desloratadine_adverse
    ))
    return meds


def get_intranasal_steroid_options(age, severity=""):
    meds = []
    severity_text = normalize_severity(severity)

    severity_adjustment = ""
    if severity_text == "moderată":
        severity_adjustment = "În forme moderate, folosirea regulată zilnică este de preferat față de administrarea sporadică."
    elif severity_text == "severă":
        severity_adjustment = "În forme severe, combină tratamentul local cu reevaluare clinică și control al triggerilor."

    mometasone_adverse = "Epistaxis, iritație nazală, senzație de uscăciune nazală, cefalee; rar candidoză locală."

    if age is not None and age < 2:
        meds.append(build_medication_entry(
            med_class="Corticosteroid intranazal",
            active_substance="Mometazonă",
            pharmacologic_name="Mometazonă furoat",
            administration_route="intranzal",
            frequency="o dată pe zi",
            adult_dose="Nu se aplică",
            pediatric_dose="Sub 2 ani: nu automatiza; necesită evaluare medicală individuală.",
            observations="Utilizarea sub 2 ani nu se recomandă fără evaluare dedicată.",
            severity_adjustment=severity_adjustment,
            adverse_reactions=mometasone_adverse
        ))
        return meds

    if age is not None and 2 <= age <= 11:
        meds.append(build_medication_entry(
            med_class="Corticosteroid intranazal",
            active_substance="Mometazonă",
            pharmacologic_name="Mometazonă furoat spray nazal",
            administration_route="intranzal",
            frequency="o dată pe zi",
            adult_dose="Nu se aplică",
            pediatric_dose="1 puf în fiecare nară o dată pe zi",
            observations="Pentru administrare regulată; adultul poate supraveghea copilul.",
            severity_adjustment=severity_adjustment,
            adverse_reactions=mometasone_adverse
        ))
        return meds

    meds.append(build_medication_entry(
        med_class="Corticosteroid intranazal",
        active_substance="Mometazonă",
        pharmacologic_name="Mometazonă furoat spray nazal",
        administration_route="intranzal",
        frequency="o dată pe zi",
        adult_dose="2 pufuri în fiecare nară o dată pe zi",
        pediatric_dose="≥12 ani: aceeași schemă ca la adult; 2–11 ani: 1 puf în fiecare nară o dată pe zi",
        observations="Se administrează regulat; nu spray în ochi sau gură.",
        severity_adjustment=severity_adjustment,
        adverse_reactions=mometasone_adverse
    ))
    return meds


def get_ophthalmic_options(age, severity=""):
    meds = []
    severity_text = normalize_severity(severity)

    severity_adjustment = ""
    if severity_text == "severă":
        severity_adjustment = "În simptomatologie oculară intensă, ia în calcul reevaluare oftalmologică și excluderea altor cauze."

    olopatadine_adverse = "Iritație oculară locală, senzație de arsură, gust amar, uscăciune oculară, cefalee."

    if age is not None and age < 2:
        meds.append(build_medication_entry(
            med_class="Antihistaminic oftalmic",
            active_substance="Olopatadină",
            pharmacologic_name="Olopatadină soluție oftalmică",
            administration_route="ocular",
            frequency="în funcție de produs",
            adult_dose="Nu se aplică",
            pediatric_dose="Sub 2 ani: evaluare medicală individuală.",
            observations="Nu automatiza doza sub 2 ani.",
            severity_adjustment=severity_adjustment,
            adverse_reactions=olopatadine_adverse
        ))
        return meds

    meds.append(build_medication_entry(
        med_class="Antihistaminic oftalmic",
        active_substance="Olopatadină",
        pharmacologic_name="Olopatadină soluție oftalmică",
        administration_route="ocular",
        frequency="1 picătură de 2 ori pe zi sau, pentru anumite concentrații, 1 dată pe zi",
        adult_dose="1 picătură în ochiul afectat de 2 ori/zi sau 1 dată/zi, în funcție de formulă",
        pediatric_dose="≥2 ani: aceeași schemă, în funcție de formulă",
        observations="Dacă se folosesc și alte produse oftalmice, păstrează interval între administrări.",
        severity_adjustment=severity_adjustment,
        adverse_reactions=olopatadine_adverse
    ))
    return meds


def get_asthma_options(age, weight=None, severity=""):
    meds = []
    severity_text = normalize_severity(severity)

    salbutamol_weight_based = ""
    budesonide_weight_based = ""
    severity_adjustment_reliever = ""
    severity_adjustment_controller = ""

    if weight is not None:
        salbutamol_weight_based = (
            f"Greutate introdusă: {format_weight_value(weight)}. "
            f"Pentru administrarea inhalatorie nu se folosește de rutină o formulă simplă mg/kg; "
            f"schema se adaptează după vârstă, dispozitiv, răspuns clinic și contextul exacerbării."
        )
        budesonide_weight_based = (
            f"Greutate introdusă: {format_weight_value(weight)}. "
            f"Pentru budesonid inhalator/nebulizat nu există o schemă unică sigură strict mg/kg; "
            f"doza se corelează cu vârsta, severitatea, produsul și dispozitivul folosit."
        )

    if severity_text == "moderată":
        severity_adjustment_reliever = "Necesită reevaluarea frecvenței utilizării; folosirea repetată sugerează control insuficient."
        severity_adjustment_controller = "În severitate moderată, este frecvent necesar controller zilnic și reevaluare a tehnicii."
    elif severity_text == "severă":
        severity_adjustment_reliever = "În severitate mare, bronhodilatatorul de salvare singur este insuficient; impune evaluare urgentă."
        severity_adjustment_controller = "În severitate mare, este necesară treaptă terapeutică superioară și reevaluare clinică rapidă."

    salbutamol_adverse = "Tremor, tahicardie, palpitații, agitație, hipokaliemie în utilizare repetată."
    budesonide_adverse = "Candidoză orală, disfonie, iritație locală; la doze mari sau utilizare prelungită pot apărea efecte sistemice."
    combo_adverse = "Tremor, palpitații, cefalee, candidoză orală, disfonie; profil combinat ICS + LABA."

    if age is not None and age < 4:
        meds.append(build_medication_entry(
            med_class="Bronhodilatator de salvare",
            active_substance="Salbutamol / Albuterol",
            pharmacologic_name="Beta2-agonist inhalator cu durată scurtă de acțiune",
            administration_route="inhalator",
            frequency="la nevoie",
            adult_dose="Nu se aplică",
            pediatric_dose="Sub 4 ani: schema trebuie individualizată; frecvent este necesar dispozitiv cu spacer și evaluare pediatrică.",
            observations="Nu automatiza doza doar după vârstă la această grupă.",
            weight_based_dose=salbutamol_weight_based,
            severity_adjustment=severity_adjustment_reliever,
            adverse_reactions=salbutamol_adverse
        ))
        meds.append(build_medication_entry(
            med_class="Controller inhalator",
            active_substance="Budesonid",
            pharmacologic_name="Corticosteroid inhalator",
            administration_route="inhalator / nebulizare",
            frequency="zilnic",
            adult_dose="Nu se aplică",
            pediatric_dose="La copilul mic, alegerea formei și dozei depinde de vârstă, dispozitiv și severitate.",
            observations="Necesită individualizare.",
            weight_based_dose=budesonide_weight_based,
            severity_adjustment=severity_adjustment_controller,
            adverse_reactions=budesonide_adverse
        ))
        return meds

    meds.append(build_medication_entry(
        med_class="Bronhodilatator de salvare",
        active_substance="Salbutamol / Albuterol",
        pharmacologic_name="Beta2-agonist inhalator cu durată scurtă de acțiune",
        administration_route="inhalator",
        frequency="la nevoie; pentru bronhospasm acut sau înainte de efort",
        adult_dose="2 pufuri la nevoie; uzual la 4–6 ore dacă este necesar",
        pediatric_dose="≥4 ani: 2 pufuri la nevoie; uzual la 4–6 ore dacă este necesar",
        observations="Tehnica inhalatorie și folosirea spacer-ului trebuie verificate.",
        weight_based_dose=salbutamol_weight_based,
        severity_adjustment=severity_adjustment_reliever,
        adverse_reactions=salbutamol_adverse
    ))

    meds.append(build_medication_entry(
        med_class="Controller inhalator",
        active_substance="Budesonid",
        pharmacologic_name="Corticosteroid inhalator",
        administration_route="inhalator / nebulizare",
        frequency="zilnic",
        adult_dose="Doza se stabilește după severitate; uzual scheme low-dose/medium-dose conform controlului clinic",
        pediatric_dose="Doza se adaptează după vârstă, dispozitiv și severitate; la copil mic poate fi folosită și suspensie pentru nebulizare",
        observations="Nu este medicament pentru criza acută.",
        weight_based_dose=budesonide_weight_based,
        severity_adjustment=severity_adjustment_controller,
        adverse_reactions=budesonide_adverse
    ))

    if age is not None and age >= 12:
        meds.append(build_medication_entry(
            med_class="Reliever / controller combinat",
            active_substance="Budesonid + Formoterol",
            pharmacologic_name="Asociere ICS-formoterol",
            administration_route="inhalator",
            frequency="în funcție de schema aleasă",
            adult_dose="Poate fi utilizat ca reliever sau în schemă maintenance-and-reliever, conform produsului și severității",
            pediatric_dose="≥12 ani: poate fi folosit similar adolescentului/adultului, conform produsului",
            observations="Verifică produsul disponibil și schema exactă.",
            severity_adjustment=severity_adjustment_controller,
            adverse_reactions=combo_adverse
        ))
    elif age is not None and 6 <= age <= 11:
        meds.append(build_medication_entry(
            med_class="Controller inhalator",
            active_substance="Budesonid + Formoterol",
            pharmacologic_name="Asociere ICS-formoterol",
            administration_route="inhalator",
            frequency="în funcție de schema aleasă",
            adult_dose="Nu se aplică",
            pediatric_dose="La copilul 6–11 ani, alegerea combinației și a schemei trebuie corelată cu ghidul și produsul aprobat local.",
            observations="Nu automatiza doza exactă doar după vârstă.",
            severity_adjustment=severity_adjustment_controller,
            adverse_reactions=combo_adverse
        ))

    return meds


def get_dermatitis_options(age, severity=""):
    severity_text = normalize_severity(severity)

    emollient_adjustment = ""
    antiinflam_adjustment = ""

    if severity_text == "moderată":
        antiinflam_adjustment = "În forme moderate, este frecvent necesar tratament antiinflamator local pe durată limitată și reevaluare."
    elif severity_text == "severă":
        antiinflam_adjustment = "În forme severe, extinse sau refractare, ia în calcul trimitere dermatologică/alergologică."

    return [
        build_medication_entry(
            med_class="Îngrijire de bază",
            active_substance="Emolient",
            pharmacologic_name="Emolient / cremă hidratantă",
            administration_route="topic cutanat",
            frequency="de mai multe ori pe zi",
            adult_dose="Aplicare repetată pe zonele afectate și pe tegumentul uscat",
            pediatric_dose="Aplicare repetată pe zonele afectate și pe tegumentul uscat",
            observations="Bază a tratamentului în dermatita atopică.",
            severity_adjustment=emollient_adjustment,
            adverse_reactions="De obicei bine tolerat; rar senzație de usturime, iritație locală sau intoleranță la excipienți."
        ),
        build_medication_entry(
            med_class="Antiinflamator topic",
            active_substance="Corticosteroid topic",
            pharmacologic_name="Corticosteroid topic",
            administration_route="topic cutanat",
            frequency="conform recomandării medicale",
            adult_dose="Alegerea potenței și duratei depinde de zonă, severitate și întindere",
            pediatric_dose="Necesită alegere atentă a potenței și duratei, mai ales la copil",
            observations="Nu automatiza potența sau durata fără context clinic.",
            severity_adjustment=antiinflam_adjustment,
            adverse_reactions="Atrofie cutanată, telangiectazii, iritație locală, hipopigmentare; risc mai mare la utilizare prelungită sau pe zone sensibile."
        )
    ]


def get_urticaria_options(age, weight=None, severity=""):
    meds = []
    meds.extend(get_age_based_antihistamine_options(age, weight=weight, severity=severity))
    meds.append(build_medication_entry(
        med_class="Măsură generală",
        active_substance="Evitarea triggerului",
        pharmacologic_name="Măsură non-farmacologică",
        administration_route="non-farmacologic",
        frequency="continuu",
        adult_dose="Identifică și evită factorul declanșator plauzibil",
        pediatric_dose="Identifică și evită factorul declanșator plauzibil",
        observations="Nu toate urticariile sunt de cauză alergică.",
        severity_adjustment="În severitate mare sau asociere cu afectare respiratorie, reevaluează imediat posibilitatea de anafilaxie." if normalize_severity(severity) == "severă" else "",
        adverse_reactions="Nu se aplică pentru măsura non-farmacologică."
    ))
    return meds


def get_food_allergy_options(age, weight=None, severity=""):
    meds = []
    meds.append(build_medication_entry(
        med_class="Măsură generală",
        active_substance="Evitarea alimentului suspect",
        pharmacologic_name="Măsură non-farmacologică",
        administration_route="non-farmacologic",
        frequency="continuu până la clarificare",
        adult_dose="Evitarea alimentului suspect dacă relația temporală este convingătoare",
        pediatric_dose="Evitarea alimentului suspect dacă relația temporală este convingătoare",
        observations="Necesită clarificare alergologică ulterioară.",
        severity_adjustment="În prezența semnelor sistemice, tratează ca urgență și exclude anafilaxia." if normalize_severity(severity) == "severă" else "",
        adverse_reactions="Nu se aplică pentru măsura non-farmacologică."
    ))
    meds.extend(get_age_based_antihistamine_options(age, weight=weight, severity=severity))
    return meds


def get_anaphylaxis_options(age, weight=None, severity=""):
    meds = []

    adult_dose = "Adrenalină IM 0,5 mg (0,5 mL din soluția 1 mg/mL), în coapsa anterolaterală"
    pediatric_dose = "Copil: 0,01 mg/kg IM (0,01 mL/kg din soluția 1 mg/mL), până la maximum uzual 0,3–0,5 mg"
    weight_based_dose = ""

    if weight is not None:
        adrenaline_mg = round(0.01 * weight, 3)
        adrenaline_ml = round(0.01 * weight, 3)
        if adrenaline_mg > 0.5:
            adrenaline_mg = 0.5
            adrenaline_ml = 0.5
        weight_based_dose = (
            f"La greutatea introdusă ({format_weight_value(weight)}): "
            f"adrenalină IM ≈ {adrenaline_mg} mg ({adrenaline_ml} mL din soluția 1 mg/mL), "
            f"fără a depăși doza maximă uzuală."
        )

    meds.append(build_medication_entry(
        med_class="Medicație de primă linie în urgență",
        active_substance="Adrenalină",
        pharmacologic_name="Epinefrină / adrenalină",
        administration_route="intramuscular",
        frequency="imediat; se poate repeta conform evaluării clinice",
        adult_dose=adult_dose,
        pediatric_dose=pediatric_dose,
        observations="La copil doza este dependentă de greutate, nu doar de vârstă. Necesită management de urgență.",
        weight_based_dose=weight_based_dose,
        severity_adjustment="Anafilaxia este o urgență medicală. Adrenalina IM este intervenția de primă linie și nu trebuie întârziată.",
        adverse_reactions="Tahicardie, palpitații, tremor, anxietate, cefalee; în context de anafilaxie, beneficiul depășește riscurile potențiale."
    ))

    meds.append(build_medication_entry(
        med_class="Măsură suportivă de urgență",
        active_substance="Oxigen",
        pharmacologic_name="Oxigenoterapie",
        administration_route="inhalator / mască",
        frequency="continuu, conform evaluării clinice",
        adult_dose="Se administrează în funcție de statusul respirator și saturație",
        pediatric_dose="Se administrează în funcție de statusul respirator și saturație",
        observations="Măsură suportivă; nu înlocuiește adrenalina IM.",
        severity_adjustment="Indicat în afectare respiratorie, hipoxemie sau instabilitate clinică.",
        adverse_reactions="Nu se aplică uzual în utilizarea corectă pe termen scurt."
    ))

    meds.append(build_medication_entry(
        med_class="Măsură suportivă de urgență",
        active_substance="Fluide i.v.",
        pharmacologic_name="Cristaloizi intravenos",
        administration_route="intravenos",
        frequency="conform evaluării clinice",
        adult_dose="În hipotensiune / șoc, conform protocolului de urgență",
        pediatric_dose="În hipotensiune / șoc, conform protocolului pediatric de urgență",
        observations="Necesită monitorizare și management medical de urgență.",
        severity_adjustment="Util dacă există hipotensiune, colaps circulator sau răspuns insuficient inițial.",
        adverse_reactions="Supraincărcare volemică în anumite contexte; necesită monitorizare."
    ))

    meds.append(build_medication_entry(
        med_class="Tratament adjuvant",
        active_substance="Antihistaminic H1",
        pharmacologic_name="Antihistaminic oral / parenteral",
        administration_route="oral / injectabil",
        frequency="după stabilizarea inițială",
        adult_dose="Doza depinde de produsul ales",
        pediatric_dose="Doza depinde de vârstă, greutate și produs",
        observations="Adjuvant pentru simptome cutanate; nu înlocuiește adrenalina.",
        severity_adjustment="Se administrează doar ca adjuvant, după inițierea măsurilor de urgență.",
        adverse_reactions="Somnolență, xerostomie, amețeală, rareori reacții paradoxale."
    ))

    meds.append(build_medication_entry(
        med_class="Tratament adjuvant",
        active_substance="Salbutamol / Albuterol",
        pharmacologic_name="Beta2-agonist inhalator cu durată scurtă de acțiune",
        administration_route="inhalator / nebulizare",
        frequency="la nevoie, ca adjuvant",
        adult_dose="Conform produsului și protocolului de urgență",
        pediatric_dose="Conform produsului, vârstei și răspunsului clinic",
        observations="Poate fi util în bronhospasm asociat, dar nu tratează cauza principală a anafilaxiei.",
        severity_adjustment="Util doar dacă există wheezing / bronhospasm asociat.",
        adverse_reactions="Tremor, tahicardie, palpitații, agitație."
    ))

    return meds


def get_medication_options(primary_name, age=None, weight=None, severity=""):
    primary_name = (primary_name or "").lower()

    if "anafilaxie" in primary_name:
        return get_anaphylaxis_options(age=age, weight=weight, severity=severity)

    if "alergie alimentară" in primary_name:
        return get_food_allergy_options(age=age, weight=weight, severity=severity)

    if "urticarie" in primary_name or "angioedem" in primary_name:
        return get_urticaria_options(age=age, weight=weight, severity=severity)

    if "dermatită" in primary_name:
        return get_dermatitis_options(age=age, severity=severity)

    if "astm" in primary_name:
        return get_asthma_options(age=age, weight=weight, severity=severity)

    meds = []

    if "rinită" in primary_name:
        meds.extend(get_age_based_antihistamine_options(age, weight=weight, severity=severity))
        meds.extend(get_intranasal_steroid_options(age, severity=severity))

    if "conjunctivită" in primary_name:
        meds.extend(get_age_based_antihistamine_options(age, weight=weight, severity=severity))
        meds.extend(get_ophthalmic_options(age, severity=severity))

    if not meds:
        meds.extend(get_age_based_antihistamine_options(age, weight=weight, severity=severity))

    return meds


def extract_diagnosis_terms(diagnosis):
    terms = []

    for key in ["name", "aliases", "synonyms", "keywords", "symptoms", "clinical_clues"]:
        value = diagnosis.get(key, [])
        if isinstance(value, str):
            value = [value]
        if isinstance(value, list):
            for item in value:
                if item:
                    terms.append(str(item).strip().lower())

    return deduplicate(terms)


def score_diagnosis(text, diagnosis):
    text = normalize_text(text)
    score = 0
    matched_terms = []

    name = (diagnosis.get("name") or "").strip().lower()
    symptoms = diagnosis.get("symptoms", [])
    keywords = diagnosis.get("keywords", [])
    red_flags = diagnosis.get("red_flags", [])
    triggers = diagnosis.get("triggers", [])

    if isinstance(symptoms, str):
        symptoms = [symptoms]
    if isinstance(keywords, str):
        keywords = [keywords]
    if isinstance(red_flags, str):
        red_flags = [red_flags]
    if isinstance(triggers, str):
        triggers = [triggers]

    for item in symptoms:
        item_norm = normalize_text(item)
        if item_norm and item_norm in text:
            score += 3
            matched_terms.append(item)

    for item in keywords:
        item_norm = normalize_text(item)
        if item_norm and item_norm in text:
            score += 2
            matched_terms.append(item)

    for item in triggers:
        item_norm = normalize_text(item)
        if item_norm and item_norm in text:
            score += 2
            matched_terms.append(item)

    for item in red_flags:
        item_norm = normalize_text(item)
        if item_norm and item_norm in text:
            score += 4
            matched_terms.append(item)

    if name and name in text:
        score += 1
        matched_terms.append(diagnosis.get("name", ""))

    # bonusuri clinice simple
    if "anafilaxie" in name:
        if contains_any(text, ["urticarie", "angioedem", "edem buze", "edem lingual"]) and contains_any(
            text,
            ["dispnee", "dispnee severă", "hipotensiune", "șoc", "voce răgușită", "dificultăți la înghițire"]
        ):
            score += 5

    if "rinită alergică" in name:
        if contains_any(text, ["strănut", "rinoree", "prurit nazal", "nas înfundat"]):
            score += 3
        if contains_any(text, ["polen", "ambrozie", "acarieni", "praf"]):
            score += 2

    if "conjunctivită alergică" in name:
        if contains_any(text, ["lăcrimare", "prurit ocular", "ochi roșii"]):
            score += 3

    if "astm alergic" in name:
        if contains_any(text, ["wheezing", "șuierături", "dispnee", "tuse nocturnă", "constricție toracică"]):
            score += 4

    if "dermatită atopică" in name:
        if contains_any(text, ["dermatită", "prurit cutanat", "piele uscată", "eczema"]):
            score += 4

    if "alergie alimentară" in name:
        if contains_any(text, ["după masă", "aliment", "vărsături", "prurit faringian", "prurit oral"]):
            score += 4

    return score, deduplicate(matched_terms)


def rank_diagnoses(text, diagnoses, top_n=5):
    ranked = []

    for diagnosis in diagnoses:
        score, matched = score_diagnosis(text, diagnosis)
        if score > 0:
            ranked.append({
                "name": diagnosis.get("name", "Diagnostic nespecificat"),
                "score": score,
                "probability": score_to_probability(score),
                "matched_terms": matched,
                "definition": diagnosis.get("definition", ""),
                "category": diagnosis.get("category", "")
            })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:top_n]


def find_primary_diagnosis(text, diagnoses):
    ranked = rank_diagnoses(text, diagnoses, top_n=5)
    if not ranked:
        return None, []
    return ranked[0], ranked


def enrich_from_knowledge(primary_name, knowledge_base):
    if not primary_name:
        return {}

    key = primary_name.strip().lower()
    return knowledge_base.get(key, {})


def merge_lists(*args):
    result = []
    for arg in args:
        if isinstance(arg, str):
            arg = [arg]
        if isinstance(arg, list):
            result.extend(arg)
    return deduplicate(result)


def build_prevention_plan(primary_name, text=""):
    primary_name = (primary_name or "").lower()
    prevention = []

    if "rinită" in primary_name or "conjunctivită" in primary_name:
        prevention.extend([
            "Reducerea expunerii la alergeni relevanți clinic (polen, acarieni, epitelii de animale), dacă sensibilizarea este confirmată sau foarte probabilă.",
            "Aerisește locuința strategic și adaptează expunerea în perioadele de polenizare intensă.",
            "Igienă nazală și oculară după expuneri relevante, în funcție de toleranță."
        ])

    if "astm" in primary_name:
        prevention.extend([
            "Evitarea triggerilor cunoscuți și monitorizarea controlului simptomelor.",
            "Verificarea tehnicii inhalatorii și a aderenței la tratamentul controller.",
            "Plan scris de acțiune pentru exacerbări, dacă este disponibil."
        ])

    if "dermatită" in primary_name:
        prevention.extend([
            "Îngrijire regulată cu emolient și evitare a iritanților cutanați.",
            "Alegerea produselor de igienă blânde și evitarea supraspălării tegumentului."
        ])

    if "urticarie" in primary_name or "angioedem" in primary_name:
        prevention.extend([
            "Identificarea contextului de apariție și evitarea triggerului plauzibil, dacă acesta poate fi stabilit.",
            "Reevaluare dacă episoadele recidivează sau devin sistemice."
        ])

    if "alergie alimentară" in primary_name:
        prevention.extend([
            "Evitarea alimentului suspect până la clarificare alergologică.",
            "Citirea atentă a etichetelor și educație privind expunerile accidentale."
        ])

    if "anafilaxie" in primary_name:
        prevention.extend([
            "Identificarea triggerului probabil prin evaluare alergologică după stabilizare.",
            "Educație privind recunoașterea precoce a simptomelor și conduita de urgență.",
            "Plan de urgență individualizat și, unde este indicat, autoinjector de adrenalină conform recomandării specialistului."
        ])

    if not prevention:
        prevention.append("Măsurile preventive trebuie individualizate în funcție de triggerii probabili și de contextul clinic.")

    return deduplicate(prevention)


def build_differential_diagnoses(ranked, primary_name):
    differential = []

    for item in ranked:
        name = item.get("name", "")
        if name and name.lower() != (primary_name or "").lower():
            differential.append(name)

    return differential[:4]


def build_case_summary(symptoms_text, age=None, sex=None, weight=None):
    parts = []

    if symptoms_text:
        parts.append(f"Simptome raportate: {symptoms_text.strip()}.")

    age_label = age_group_label(age)
    parts.append(f"Grupă de vârstă estimată: {age_label}.")

    if age is not None:
        parts.append(f"Vârstă declarată: {age} ani.")

    if sex:
        parts.append(f"Sex: {sex}.")

    if weight is not None:
        parts.append(f"Greutate declarată: {format_weight_value(weight)}.")

    return " ".join(parts)


def evaluate_allergy_case(symptoms_text, age=None, sex=None, weight=None,
                          diagnoses_path="data/diagnoses.json",
                          knowledge_path="data/allergy_knowledge_ro.json"):
    text = normalize_text(symptoms_text)
    age = parse_age(age)
    weight = parse_weight(weight)
    sex = (sex or "").strip()

    diagnoses = load_diagnoses(diagnoses_path)
    knowledge = load_romanian_knowledge(knowledge_path)

    primary, ranked = find_primary_diagnosis(text, diagnoses)
    severity = classify_severity(text)

    if not primary:
        return {
            "case_summary": build_case_summary(symptoms_text, age=age, sex=sex, weight=weight),
            "input": {
                "symptoms": symptoms_text,
                "age": age,
                "sex": sex,
                "weight": weight
            },
            "severity": severity,
            "confidence": "scăzută",
            "primary_diagnosis": None,
            "ranked_diagnoses": [],
            "differential_diagnoses": [],
            "supports": build_supports(text, ""),
            "limits": build_limits(text),
            "red_flags": build_red_flags(text),
            "recommended_tests": build_recommended_tests(text, ""),
            "treatment_plan": ["Nu a putut fi generată o ipoteză principală suficient de robustă. Este necesară completarea anamnezei și evaluarea clinică."],
            "prevention": ["Prevenția depinde de triggerul probabil și de diagnosticul final."],
            "medications": [],
            "notes": build_notes(text, []),
            "knowledge": {}
        }

    primary_name = primary.get("name", "")
    confidence = determine_confidence(ranked)
    knowledge_item = enrich_from_knowledge(primary_name, knowledge)

    supports = merge_lists(
        build_supports(text, primary_name),
        knowledge_item.get("supports", [])
    )

    limits = merge_lists(
        build_limits(text),
        knowledge_item.get("limits", [])
    )

    red_flags = merge_lists(
        build_red_flags(text),
        knowledge_item.get("red_flags", [])
    )

    recommended_tests = merge_lists(
        build_recommended_tests(text, primary_name),
        knowledge_item.get("recommended_tests", [])
    )

    treatment_plan = merge_lists(
        build_treatment_plan(text, primary_name, severity),
        knowledge_item.get("treatment_plan", [])
    )

    prevention = merge_lists(
        build_prevention_plan(primary_name, text),
        knowledge_item.get("prevention", [])
    )

    medications = get_medication_options(
        primary_name=primary_name,
        age=age,
        weight=weight,
        severity=severity
    )

    notes = merge_lists(
        build_notes(text, ranked),
        knowledge_item.get("notes", [])
    )

    result = {
        "case_summary": build_case_summary(symptoms_text, age=age, sex=sex, weight=weight),
        "input": {
            "symptoms": symptoms_text,
            "age": age,
            "sex": sex,
            "weight": weight
        },
        "severity": severity,
        "confidence": confidence,
        "primary_diagnosis": {
            "name": primary_name,
            "score": primary.get("score", 0),
            "probability": primary.get("probability", "redusă"),
            "definition": primary.get("definition", ""),
            "category": primary.get("category", "")
        },
        "ranked_diagnoses": ranked,
        "differential_diagnoses": build_differential_diagnoses(ranked, primary_name),
        "supports": supports,
        "limits": limits,
        "red_flags": red_flags,
        "recommended_tests": recommended_tests,
        "treatment_plan": treatment_plan,
        "prevention": prevention,
        "medications": medications,
        "notes": notes,
        "knowledge": knowledge_item
    }

    return result

def rank_differential_diagnoses(symptoms_text, diagnoses):
    text = normalize_text(symptoms_text)
    ranked = rank_diagnoses(text, diagnoses, top_n=10)

    severity = classify_severity(text)
    confidence = determine_confidence(ranked)

    primary_name = ranked[0]["name"] if ranked else ""
    primary_probability = ranked[0]["probability"] if ranked else None

    associated_diagnosis = None
    if len(ranked) > 1:
        top_names = [item.get("name", "").lower() for item in ranked[:3]]

        if any("rinit" in x for x in top_names) and any("astm" in x for x in top_names):
            associated_diagnosis = "Asociere probabilă rinită alergică + astm alergic"
        elif any("rinit" in x for x in top_names) and any("conjunctivit" in x for x in top_names):
            associated_diagnosis = "Asociere probabilă rinită alergică + conjunctivită alergică"
        elif any("urticarie" in x for x in top_names) and any("angioedem" in x for x in top_names):
            associated_diagnosis = "Asociere probabilă urticarie + angioedem"

    clinical_output = {
        "primary_diagnosis": primary_name if primary_name else None,
        "primary_probability": primary_probability,
        "associated_diagnosis": associated_diagnosis,
        "alternatives": build_differential_diagnoses(ranked, primary_name),
        "supports": build_supports(text, primary_name),
        "limits": build_limits(text),
        "recommended_tests": build_recommended_tests(text, primary_name),
        "treatment_plan": build_treatment_plan(text, primary_name, severity),
        "red_flags": build_red_flags(text),
        "notes": build_notes(text, ranked),
        "severity": severity,
        "confidence": confidence
    }

    return ranked, clinical_output


def get_treatment_details(diagnosis_name, knowledge_ro=None, age=None, weight=None, severity=None):
    name = (diagnosis_name or "").strip().lower()
    parsed_age = parse_age(age)
    parsed_weight = parse_weight(weight)
    normalized_severity = normalize_severity(severity)

    knowledge_item = {}
    if knowledge_ro and name in knowledge_ro:
        knowledge_item = knowledge_ro.get(name, {})

    diagnosis_label = knowledge_item.get("name", diagnosis_name)

    clinical_picture = merge_lists(
        knowledge_item.get("clinical_picture", []),
        knowledge_item.get("symptoms", []),
        knowledge_item.get("supports", [])
    )

    treatment = merge_lists(
        knowledge_item.get("treatment", []),
        knowledge_item.get("treatment_plan", [])
    )

    prevention = merge_lists(
        knowledge_item.get("prevention", []),
        build_prevention_plan(diagnosis_label)
    )

    allergen_avoidance = merge_lists(
        knowledge_item.get("allergen_avoidance", []),
        knowledge_item.get("avoidance", [])
    )

    medication_options = get_medication_options(
        primary_name=diagnosis_label,
        age=parsed_age,
        weight=parsed_weight,
        severity=normalized_severity
    )

    if not clinical_picture:
        if "rinit" in name:
            clinical_picture = [
                "Strănut",
                "Rinoree",
                "Prurit nazal",
                "Obstrucție nazală / nas înfundat"
            ]
        elif "conjunctivit" in name:
            clinical_picture = [
                "Prurit ocular",
                "Lăcrimare",
                "Hiperemie conjunctivală / ochi roșii"
            ]
        elif "astm" in name:
            clinical_picture = [
                "Wheezing / șuierături",
                "Dispnee variabilă",
                "Tuse, adesea nocturnă",
                "Constricție toracică"
            ]
        elif "dermatită" in name:
            clinical_picture = [
                "Prurit cutanat",
                "Leziuni eczematoase",
                "Piele uscată",
                "Evoluție recurentă"
            ]
        elif "urticarie" in name or "angioedem" in name:
            clinical_picture = [
                "Plăci pruriginoase și/sau edem localizat",
                "Episod acut sau recurent",
                "Posibilă legătură cu trigger medicamentos, alimentar sau infecțios"
            ]
        elif "alergie alimentară" in name:
            clinical_picture = [
                "Reacție în context alimentar",
                "Manifestări cutanate, digestive și/sau respiratorii",
                "Relație temporală sugestivă cu ingestia"
            ]
        elif "anafilaxie" in name:
            clinical_picture = [
                "Reacție acută sistemică cu potențial vital",
                "Afectare respiratorie, cardiovasculară, cutanată și/sau digestivă",
                "Necesită intervenție de urgență"
            ]

    if not treatment:
        if "rinit" in name:
            treatment = [
                "Evitarea expunerii la alergenii relevanți clinic.",
                "Lavaj nazal cu ser salin, după toleranță.",
                "Antihistaminic oral și/sau corticosteroid intranazal, în funcție de severitate și context."
            ]
        elif "conjunctivit" in name:
            treatment = [
                "Evitarea expunerilor alergene/iritative.",
                "Antihistaminic ocular sau oral, după caz.",
                "Reevaluare dacă simptomele sunt persistente sau severe."
            ]
        elif "astm" in name:
            treatment = [
                "Bronhodilatator de salvare la nevoie.",
                "Tratament controller în funcție de severitate și gradul de control.",
                "Verificarea tehnicii inhalatorii și monitorizarea exacerbărilor."
            ]
        elif "dermatită" in name:
            treatment = [
                "Emoliere susținută.",
                "Tratament antiinflamator topic în funcție de severitate.",
                "Evitarea iritanților cutanați și reevaluare dacă leziunile persistă."
            ]
        elif "urticarie" in name or "angioedem" in name:
            treatment = [
                "Antihistaminic H1 de generația a doua.",
                "Identificarea și evitarea posibilului trigger.",
                "Reevaluare promptă dacă apar semne respiratorii sau afectare sistemică."
            ]
        elif "alergie alimentară" in name:
            treatment = [
                "Evitarea alimentului suspect până la clarificare.",
                "Tratament simptomatic în funcție de manifestări.",
                "Evaluare alergologică dacă tabloul este repetitiv sau sever."
            ]
        elif "anafilaxie" in name:
            treatment = [
                "Adrenalină IM de primă linie.",
                "Măsuri suportive și monitorizare de urgență.",
                "După stabilizare: clarificarea triggerului și plan de prevenție secundară."
            ]
        else:
            treatment = [
                "Tratamentul trebuie individualizat în funcție de tabloul clinic, severitate și contextul pacientului."
            ]

    if not prevention:
        prevention = [
            "Măsurile preventive trebuie adaptate triggerilor relevanți clinic și contextului individual."
        ]

    if not allergen_avoidance:
        if "rinit" in name or "conjunctivit" in name:
            allergen_avoidance = [
                "Reducerea expunerii la polen, acarieni sau epitelii de animale, dacă sunt relevante clinic.",
                "Igienă nazală/oculară după expunere și adaptarea mediului domestic."
            ]
        elif "astm" in name:
            allergen_avoidance = [
                "Evitarea triggerilor respiratori relevanți clinic.",
                "Controlul expunerii la alergeni inhalatori atunci când aceștia sunt implicați."
            ]
        elif "dermatită" in name:
            allergen_avoidance = [
                "Evitarea iritanților cutanați și a produselor slab tolerate.",
                "Adaptarea rutinei de îngrijire și alegerea produselor blânde."
            ]
        elif "alergie alimentară" in name:
            allergen_avoidance = [
                "Evitarea alimentului suspect până la clarificare alergologică.",
                "Citirea atentă a etichetelor și prevenirea expunerilor accidentale."
            ]
        elif "anafilaxie" in name:
            allergen_avoidance = [
                "Identificarea și evitarea triggerului probabil după evaluare de specialitate.",
                "Plan de urgență pentru eventuale reexpuneri accidentale."
            ]
        else:
            allergen_avoidance = [
                "Evitarea triggerilor relevanți clinic trebuie individualizată."
            ]

    return {
        "diagnosis": diagnosis_label,
        "clinical_picture": deduplicate(clinical_picture),
        "treatment": deduplicate(treatment),
        "prevention": deduplicate(prevention),
        "allergen_avoidance": deduplicate(allergen_avoidance),
        "medication_options": medication_options,
        "age_group_used": age_group_label(parsed_age),
        "weight_used": parsed_weight if parsed_weight is not None else "",
        "severity_used": normalized_severity
    }