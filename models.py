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


def build_medication_entry(
    med_class,
    active_substance,
    pharmacologic_name,
    administration_route,
    frequency,
    adult_dose,
    pediatric_dose,
    observations=""
):
    return {
        "class": med_class,
        "active_substance": active_substance,
        "pharmacologic_name": pharmacologic_name,
        "administration_route": administration_route,
        "frequency": frequency,
        "adult_dose": adult_dose,
        "pediatric_dose": pediatric_dose,
        "observations": observations
    }


def get_age_based_antihistamine_options(age):
    meds = []

    if age is None:
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Cetirizină",
            pharmacologic_name="Cetirizină clorhidrat",
            administration_route="oral",
            frequency="o dată pe zi",
            adult_dose="5–10 mg/zi",
            pediatric_dose="2–5 ani: 2,5 mg/zi; dacă este necesar până la 5 mg/zi. ≥6 ani: 5–10 mg/zi.",
            observations="Ajustarea exactă depinde de forma farmaceutică și contextul clinic."
        ))
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Loratadină",
            pharmacologic_name="Loratadină",
            administration_route="oral",
            frequency="o dată pe zi",
            adult_dose="10 mg/zi",
            pediatric_dose="2–5 ani: 5 mg/zi. ≥6 ani: 10 mg/zi.",
            observations="Sub 2 ani: este necesară evaluare medicală individuală."
        ))
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Desloratadină",
            pharmacologic_name="Desloratadină",
            administration_route="oral",
            frequency="o dată pe zi",
            adult_dose="5 mg/zi",
            pediatric_dose="1–5 ani: 1,25 mg/zi; 6–11 ani: 2,5 mg/zi; ≥12 ani: 5 mg/zi.",
            observations="Utilă în rinită alergică și urticarie, în funcție de context."
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
            observations="Evită automatizarea dozei la această grupă de vârstă."
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
            observations="Orientează doza după forma farmaceutică disponibilă."
        ))
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Loratadină",
            pharmacologic_name="Loratadină",
            administration_route="oral",
            frequency="o dată pe zi",
            adult_dose="Nu se aplică",
            pediatric_dose="5 mg/zi",
            observations=""
        ))
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Desloratadină",
            pharmacologic_name="Desloratadină",
            administration_route="oral",
            frequency="o dată pe zi",
            adult_dose="Nu se aplică",
            pediatric_dose="1,25 mg/zi",
            observations=""
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
            observations="Alege doza după severitate și toleranță."
        ))
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Loratadină",
            pharmacologic_name="Loratadină",
            administration_route="oral",
            frequency="o dată pe zi",
            adult_dose="Nu se aplică",
            pediatric_dose="10 mg/zi",
            observations=""
        ))
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Desloratadină",
            pharmacologic_name="Desloratadină",
            administration_route="oral",
            frequency="o dată pe zi",
            adult_dose="Nu se aplică",
            pediatric_dose="2,5 mg/zi",
            observations=""
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
            observations="Doză uzuală de adolescent."
        ))
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Loratadină",
            pharmacologic_name="Loratadină",
            administration_route="oral",
            frequency="o dată pe zi",
            adult_dose="Nu se aplică",
            pediatric_dose="10 mg/zi",
            observations=""
        ))
        meds.append(build_medication_entry(
            med_class="Antihistaminic oral",
            active_substance="Desloratadină",
            pharmacologic_name="Desloratadină",
            administration_route="oral",
            frequency="o dată pe zi",
            adult_dose="Nu se aplică",
            pediatric_dose="5 mg/zi",
            observations=""
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
        observations=""
    ))
    meds.append(build_medication_entry(
        med_class="Antihistaminic oral",
        active_substance="Loratadină",
        pharmacologic_name="Loratadină",
        administration_route="oral",
        frequency="o dată pe zi",
        adult_dose="10 mg/zi",
        pediatric_dose="Nu se aplică",
        observations=""
    ))
    meds.append(build_medication_entry(
        med_class="Antihistaminic oral",
        active_substance="Desloratadină",
        pharmacologic_name="Desloratadină",
        administration_route="oral",
        frequency="o dată pe zi",
        adult_dose="5 mg/zi",
        pediatric_dose="Nu se aplică",
        observations=""
    ))
    return meds


def get_intranasal_steroid_options(age):
    meds = []

    if age is not None and age < 2:
        meds.append(build_medication_entry(
            med_class="Corticosteroid intranazal",
            active_substance="Mometazonă",
            pharmacologic_name="Mometazonă furoat",
            administration_route="intranzal",
            frequency="o dată pe zi",
            adult_dose="Nu se aplică",
            pediatric_dose="Sub 2 ani: nu automatiza; necesită evaluare medicală individuală.",
            observations="Utilizarea sub 2 ani nu se recomandă fără evaluare dedicată."
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
            observations="Pentru administrare regulată; adultul poate supraveghea copilul."
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
        observations="Se administrează regulat; nu spray în ochi sau gură."
    ))
    return meds


def get_ophthalmic_options(age):
    meds = []

    if age is not None and age < 2:
        meds.append(build_medication_entry(
            med_class="Antihistaminic oftalmic",
            active_substance="Olopatadină",
            pharmacologic_name="Olopatadină soluție oftalmică",
            administration_route="ocular",
            frequency="în funcție de produs",
            adult_dose="Nu se aplică",
            pediatric_dose="Sub 2 ani: evaluare medicală individuală.",
            observations="Nu automatiza doza sub 2 ani."
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
        observations="Dacă se folosesc și alte produse oftalmice, păstrează interval între administrări."
    ))
    return meds


def get_asthma_options(age):
    meds = []

    if age is not None and age < 4:
        meds.append(build_medication_entry(
            med_class="Bronhodilatator de salvare",
            active_substance="Salbutamol / Albuterol",
            pharmacologic_name="Beta2-agonist inhalator cu durată scurtă de acțiune",
            administration_route="inhalator",
            frequency="la nevoie",
            adult_dose="Nu se aplică",
            pediatric_dose="Sub 4 ani: schema trebuie individualizată; frecvent este necesar dispozitiv cu spacer și evaluare pediatrică.",
            observations="Nu automatiza doza doar după vârstă la această grupă."
        ))
        meds.append(build_medication_entry(
            med_class="Controller inhalator",
            active_substance="Budesonid",
            pharmacologic_name="Corticosteroid inhalator",
            administration_route="inhalator / nebulizare",
            frequency="zilnic",
            adult_dose="Nu se aplică",
            pediatric_dose="La copilul mic, alegerea formei și dozei depinde de vârstă, dispozitiv și severitate.",
            observations="Necesită individualizare."
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
        observations="Tehnica inhalatorie și folosirea spacer-ului trebuie verificate."
    ))

    meds.append(build_medication_entry(
        med_class="Controller inhalator",
        active_substance="Budesonid",
        pharmacologic_name="Corticosteroid inhalator",
        administration_route="inhalator / nebulizare",
        frequency="zilnic",
        adult_dose="Doza se stabilește după severitate; uzual scheme low-dose/medium-dose conform controlului clinic",
        pediatric_dose="Doza se adaptează după vârstă, dispozitiv și severitate; la copil mic poate fi folosită și suspensie pentru nebulizare",
        observations="Nu este medicament pentru criza acută."
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
            observations="Preferință de ghid la adolescenți și adulți pentru anumite strategii; verifică produsul disponibil și schema exactă."
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
            observations="Nu automatiza doza exactă doar după vârstă."
        ))

    return meds


def get_dermatitis_options(age):
    return [
        build_medication_entry(
            med_class="Îngrijire de bază",
            active_substance="Emolient",
            pharmacologic_name="Emolient / cremă hidratantă",
            administration_route="topic cutanat",
            frequency="de mai multe ori pe zi",
            adult_dose="Aplicare repetată pe zonele afectate și pe tegumentul uscat",
            pediatric_dose="Aplicare repetată pe zonele afectate și pe tegumentul uscat",
            observations="Bază a tratamentului în dermatita atopică."
        ),
        build_medication_entry(
            med_class="Antiinflamator topic",
            active_substance="Corticosteroid topic",
            pharmacologic_name="Corticosteroid topic",
            administration_route="topic cutanat",
            frequency="conform recomandării medicale",
            adult_dose="Alegerea potenței și duratei depinde de zonă, severitate și întindere",
            pediatric_dose="Necesită alegere atentă a potenței și duratei, mai ales la copil",
            observations="Nu automatiza potența sau durata fără context clinic."
        )
    ]


def get_urticaria_options(age):
    meds = []
    meds.extend(get_age_based_antihistamine_options(age))
    meds.append(build_medication_entry(
        med_class="Măsură generală",
        active_substance="Evitarea triggerului",
        pharmacologic_name="Măsură non-farmacologică",
        administration_route="non-farmacologic",
        frequency="continuu",
        adult_dose="Identifică și evită factorul declanșator plauzibil",
        pediatric_dose="Identifică și evită factorul declanșator plauzibil",
        observations="Nu toate urticariile sunt de cauză alergică."
    ))
    return meds


def get_food_allergy_options(age):
    meds = []
    meds.append(build_medication_entry(
        med_class="Măsură generală",
        active_substance="Evitarea alimentului suspect",
        pharmacologic_name="Măsură non-farmacologică",
        administration_route="non-farmacologic",
        frequency="continuu până la clarificare",
        adult_dose="Evitarea alimentului suspect dacă relația temporală este convingătoare",
        pediatric_dose="Evitarea alimentului suspect dacă relația temporală este convingătoare",
        observations="Necesită clarificare alergologică ulterioară."
    ))
    meds.extend(get_age_based_antihistamine_options(age))
    return meds


def get_anaphylaxis_options(age):
    meds = []

    adult_dose = "Adrenalină IM 0,5 mg (0,5 mL din soluția 1 mg/mL), în coapsa anterolaterală"
    pediatric_dose = "Copil: 0,01 mg/kg IM (0,01 mL/kg din soluția 1 mg/mL), până la maximum uzual 0,3–0,5 mg"

    meds.append(build_medication_entry(
        med_class="Medicație de primă linie în urgență",
        active_substance="Adrenalină",
        pharmacologic_name="Epinefrină / adrenalină",
        administration_route="intramuscular",
        frequency="imediat; se poate repeta conform evaluării clinice",
        adult_dose=adult_dose,
        pediatric_dose=pediatric_dose,
        observations="La copil doza este dependentă de greutate, nu doar de vârstă. Necesită management de urgență."
    ))

    meds.append(build_medication_entry(
        med_class="Suport adjunct",
        active_substance="Oxigen / fluide / alte măsuri de urgență",
        pharmacologic_name="Măsuri de resuscitare și suport",
        administration_route="în funcție de intervenție",
        frequency="după necesitate",
        adult_dose="În funcție de severitate și protocol",
        pediatric_dose="În funcție de severitate și protocol",
        observations="Antihistaminicele și corticosteroizii nu înlocuiesc adrenalina în anafilaxie."
    ))

    return meds


def get_structured_treatment_by_diagnosis(diagnosis_name, age):
    name = (diagnosis_name or "").lower()

    if "rinit" in name:
        meds = []
        meds.extend(get_age_based_antihistamine_options(age))
        meds.extend(get_intranasal_steroid_options(age))
        meds.append(build_medication_entry(
            med_class="Măsură adjuvantă",
            active_substance="Ser salin",
            pharmacologic_name="Soluție salină / lavaj nazal",
            administration_route="intranzal",
            frequency="1–2 sau mai multe administrări/zi, după necesitate",
            adult_dose="Lavaj / irigare nazală după toleranță",
            pediatric_dose="Lavaj / irigare nazală după toleranță și cooperare",
            observations="Poate reduce simptomele și îmbunătăți confortul."
        ))
        return meds

    if "conjunctivit" in name:
        meds = []
        meds.extend(get_ophthalmic_options(age))
        meds.extend(get_age_based_antihistamine_options(age))
        return meds

    if "astm" in name:
        return get_asthma_options(age)

    if "dermatită" in name:
        return get_dermatitis_options(age)

    if "urticarie" in name or "angioedem" in name:
        return get_urticaria_options(age)

    if "alergie alimentară" in name:
        return get_food_allergy_options(age)

    if "anafilaxie" in name:
        return get_anaphylaxis_options(age)

    return [
        build_medication_entry(
            med_class="Tratament orientativ",
            active_substance="Individualizare clinică",
            pharmacologic_name="Abordare terapeutică personalizată",
            administration_route="în funcție de context",
            frequency="în funcție de context",
            adult_dose="Se stabilește după diagnosticul final, severitate și comorbidități",
            pediatric_dose="Se stabilește după diagnosticul final, vârstă și, dacă este cazul, greutate",
            observations="Necesită corelare clinică și terapeutică individuală."
        )
    ]


def build_clinical_output(symptoms_text, ranked):
    text = normalize_text(symptoms_text)

    output = {
        "primary_diagnosis": None,
        "primary_probability": None,
        "associated_diagnosis": None,
        "alternatives": [],
        "supports": [],
        "limits": [],
        "recommended_tests": [],
        "treatment_plan": [],
        "red_flags": [],
        "notes": [],
        "severity": classify_severity(text),
        "confidence": determine_confidence(ranked)
    }

    if ranked:
        output["primary_diagnosis"] = ranked[0]["name"]
        output["primary_probability"] = ranked[0]["probability"]

    if len(ranked) > 1:
        top_names = [x["name"].lower() for x in ranked[:3]]

        if any("rinit" in x for x in top_names) and any("astm" in x for x in top_names):
            output["associated_diagnosis"] = "Asociere probabilă rinită alergică + astm alergic"

        elif any("rinit" in x for x in top_names) and any("conjunctivit" in x for x in top_names):
            output["associated_diagnosis"] = "Asociere probabilă rinită alergică + conjunctivită alergică"

        elif any("urticarie" in x for x in top_names) and any("angioedem" in x for x in top_names):
            output["associated_diagnosis"] = "Asociere probabilă urticarie + angioedem"

    output["alternatives"] = [x["name"] for x in ranked[1:4]]

    primary_name = output["primary_diagnosis"] or ""

    output["supports"] = build_supports(text, primary_name)
    output["limits"] = build_limits(text)
    output["recommended_tests"] = build_recommended_tests(text, primary_name)
    output["treatment_plan"] = build_treatment_plan(text, primary_name, output["severity"])
    output["red_flags"] = build_red_flags(text)
    output["notes"] = build_notes(text, ranked)

    return output


def rank_differential_diagnoses(symptoms_text, diagnoses):
    symptoms_text = normalize_text(symptoms_text)
    ranked = []

    strong_terms = {
        "wheezing", "dispnee", "dispnee severă", "stridor", "hipotensiune",
        "edem lingual", "șoc", "șoc anafilactic", "angioedem",
        "urticarie", "edem buze", "edem pleoape", "prurit oral",
        "dificultăți la înghițire", "voce răgușită", "edem faringian"
    }

    medium_terms = {
        "șuierături", "tuse nocturnă", "prurit nazal", "prurit ocular",
        "lăcrimare", "ochi roșii", "rinoree", "strănut",
        "vărsături", "dureri abdominale", "diaree", "nas înfundat",
        "eczeme", "dermatită", "prurit cutanat", "constricție toracică"
    }

    for diagnosis in diagnoses:
        score = 0
        matched_keywords = []

        for keyword in diagnosis.get("keywords", []):
            keyword_lower = normalize_text(keyword)

            if keyword_lower in symptoms_text:
                matched_keywords.append(keyword)

                if keyword_lower in strong_terms:
                    score += 3
                elif keyword_lower in medium_terms:
                    score += 2
                else:
                    score += 1

        name = diagnosis["name"].lower()

        if "anafilaxie" in name:
            severe_signs = [
                "hipotensiune", "dispnee severă", "edem lingual",
                "șoc", "angioedem", "stridor", "voce răgușită",
                "dificultăți la înghițire", "pierderea conștienței", "edem faringian"
            ]
            skin_or_gi = ["urticarie", "prurit oral", "edem buze", "vărsături", "diaree"]
            if contains_any(symptoms_text, severe_signs):
                score += 5
            if contains_any(symptoms_text, skin_or_gi):
                score += 2
            if not contains_any(symptoms_text, severe_signs):
                score = max(score - 2, 0)

        if "alergie alimentară" in name:
            if contains_any(symptoms_text, ["după masă", "aliment", "reacție după aliment", "prurit oral", "prurit faringian"]):
                score += 3
            if contains_any(symptoms_text, ["vărsături", "dureri abdominale", "diaree", "urticarie"]):
                score += 2

        if "conjunctivit" in name:
            if contains_any(symptoms_text, ["lăcrimare", "prurit ocular", "ochi roșii"]):
                score += 3

        if "rinit" in name:
            if contains_any(symptoms_text, ["strănut", "rinoree", "prurit nazal", "nas înfundat"]):
                score += 3
            if contains_any(symptoms_text, ["polen", "sezon", "acarieni", "praf"]):
                score += 1

        if "astm" in name:
            if contains_any(symptoms_text, ["wheezing", "dispnee", "șuierături", "tuse nocturnă", "constricție toracică"]):
                score += 4
            if contains_any(symptoms_text, ["efort", "noaptea", "alergeni", "praf", "acarieni"]):
                score += 1
            if not contains_any(symptoms_text, ["wheezing", "dispnee", "șuierături", "tuse nocturnă", "constricție toracică"]):
                score = max(score - 1, 0)

        if "dermatită" in name:
            skin_signs = ["eczeme", "piele", "leziuni", "prurit cutanat", "dermatită", "piele uscată"]
            if contains_any(symptoms_text, skin_signs):
                score += 3
            else:
                score = max(score - 2, 0)

        if "urticarie" in name:
            if contains_any(symptoms_text, ["urticarie", "papule", "plăci pruriginoase", "prurit cutanat"]):
                score += 3

        if "angioedem" in name:
            if contains_any(symptoms_text, ["angioedem", "edem buze", "edem pleoape", "edem lingual", "edem faringian"]):
                score += 4

        if score > 0:
            ranked.append({
                "name": diagnosis["name"],
                "score": score,
                "probability": score_to_probability(score),
                "matched_keywords": matched_keywords
            })

    ranked.sort(key=lambda x: x["score"], reverse=True)

    clinical_output = build_clinical_output(symptoms_text, ranked)

    return ranked, clinical_output


def get_treatment_details(diagnosis_name, knowledge_ro=None, age=None):
    name = (diagnosis_name or "").lower()
    parsed_age = parse_age(age)
    age_label = age_group_label(parsed_age)

    if knowledge_ro and name in knowledge_ro:
        item = knowledge_ro[name]
        return {
            "diagnosis": item["name"],
            "clinical_picture": item.get("clinical_picture", []),
            "treatment": item.get("treatment", []),
            "prevention": item.get("prevention", []),
            "allergen_avoidance": item.get("allergen_avoidance", []),
            "medication_options": get_structured_treatment_by_diagnosis(item["name"], parsed_age),
            "age_group_used": age_label
        }

    fallback = {
        "diagnosis": diagnosis_name,
        "clinical_picture": [],
        "treatment": ["Tratamentul trebuie individualizat în funcție de contextul clinic, severitate și recomandările medicale."],
        "prevention": ["Prevenția depinde de identificarea și evitarea factorilor declanșatori relevanți clinic."],
        "allergen_avoidance": ["Evitarea alergenului se recomandă doar după corelare clinică și identificare corectă."],
        "medication_options": get_structured_treatment_by_diagnosis(diagnosis_name, parsed_age),
        "age_group_used": age_label
    }

    if "astm" in name:
        fallback["clinical_picture"] = [
            "Wheezing / șuierături",
            "Dispnee variabilă",
            "Tuse, adesea nocturnă",
            "Variabilitate a simptomelor la expunere/alergeni"
        ]
        fallback["treatment"] = [
            "Tratamentul trebuie adaptat severității și gradului de control.",
            "Se recomandă evaluarea controlului simptomelor și tehnicii inhalatorii.",
            "Necesită monitorizare clinică și eventual explorare funcțională respiratorie."
        ]

    elif "rinit" in name:
        fallback["clinical_picture"] = [
            "Strănut",
            "Rinoree",
            "Prurit nazal",
            "Nas înfundat"
        ]
        fallback["treatment"] = [
            "Se recomandă evitare alergenică, dacă este posibil.",
            "Pot fi utile antihistaminicele și/sau corticosteroizii intranazali, conform recomandării medicale."
        ]

    elif "conjunctivit" in name:
        fallback["clinical_picture"] = [
            "Prurit ocular",
            "Lăcrimare",
            "Hiperemie conjunctivală"
        ]
        fallback["treatment"] = [
            "Evitarea triggerilor relevanți clinic și tratament local/oral, după caz."
        ]

    elif "urticarie" in name or "angioedem" in name:
        fallback["clinical_picture"] = [
            "Plăci pruriginoase și/sau edem localizat"
        ]
        fallback["treatment"] = [
            "Tratament antihistaminic și monitorizare clinică; reevaluare dacă apar semne respiratorii sau progresie rapidă."
        ]

    elif "anafilaxie" in name:
        fallback["clinical_picture"] = [
            "Reacție acută cu potențial sever, cu afectare respiratorie, cardiovasculară, cutanată sau digestivă"
        ]
        fallback["treatment"] = [
            "Anafilaxia reprezintă urgență medicală.",
            "Prioritatea este stabilizarea imediată și evaluarea de urgență."
        ]

    return fallback