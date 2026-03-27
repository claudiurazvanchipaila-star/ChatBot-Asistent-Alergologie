import json
import re
import unicodedata


def load_diagnoses(path="data/diagnoses.json"):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def load_romanian_knowledge(path="data/allergy_knowledge_ro.json"):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        normalized = {}
        for item in data:
            if isinstance(item, dict):
                name = item.get("diagnosis") or item.get("name")
                if name:
                    normalized[str(name).strip()] = item
        return normalized

    if isinstance(data, dict):
        return data

    return {}


def strip_diacritics(text):
    if not text:
        return ""
    return "".join(
        ch for ch in unicodedata.normalize("NFD", str(text))
        if unicodedata.category(ch) != "Mn"
    )


def normalize_text(text):
    if not text:
        return ""

    text = str(text).lower().strip()
    text = strip_diacritics(text)

    replacements = {
        "nas infundat": "congestie nazala",
        "nas înfundat": "congestie nazala",
        "n as infundat": "congestie nazala",
        "obstructie nazala": "congestie nazala",
        "obstrucție nazală": "congestie nazala",
        "curge nasul": "rinoree",
        "scurgeri nazale": "rinoree",
        "scurgere nazala": "rinoree",
        "secretii nazale apoase": "rinoree apoasa",
        "secreții nazale apoase": "rinoree apoasa",
        "rinoree apoasă": "rinoree apoasa",
        "mancarime nazala": "prurit nazal",
        "mâncărime nazală": "prurit nazal",
        "prurit nasal": "prurit nazal",
        "mancarime la nas": "prurit nazal",
        "mancarime oculara": "prurit ocular",
        "mâncărime oculară": "prurit ocular",
        "mancarime la ochi": "prurit ocular",
        "ochi rosii": "hiperemie oculara",
        "ochi roșii": "hiperemie oculara",
        "ochi care lacrimeaza": "lacrimare",
        "ochi care lăcrimează": "lacrimare",
        "lacrimare oculara": "lacrimare",
        "suieraturi": "wheezing",
        "șuierături": "wheezing",
        "respiratie suieratoare": "wheezing",
        "respirație șuierătoare": "wheezing",
        "dificultate la respiratie": "dispnee",
        "dificultate la respirație": "dispnee",
        "greutate in respiratie": "dispnee",
        "greutate în respirație": "dispnee",
        "strangere in piept": "constrictie toracica",
        "strângere în piept": "constrictie toracica",
        "eczema": "eczeme",
        "eczematos": "eczeme",
        "eruptie cutanata": "eruptie",
        "erupție cutanată": "eruptie",
        "reactie dupa aliment": "dupa aliment",
        "reacție după aliment": "dupa aliment",
        "dupa masa": "dupa aliment",
        "după masă": "dupa aliment",
        "dupa ingestie": "dupa aliment",
        "după ingestie": "dupa aliment",
        "umflare buze": "edem buze",
        "umflare pleoape": "edem pleoape",
        "soc anafilactic": "anafilaxie",
        "șoc anafilactic": "anafilaxie",
        "febra mare": "febra",
        "febră mare": "febra",
        "subfebrilitate": "febra",
        "durere in gat": "odinofagie",
        "durere în gât": "odinofagie",
        "gat iritat": "odinofagie",
        "gât iritat": "odinofagie",
        "mirosuri puternice": "iritanti",
        "mirosuri intense": "iritanti",
        "fum de tigara": "fum",
        "fum de țigară": "fum",
        "polenuri": "polen",
        "praf de casa": "acarieni",
        "praf de casă": "acarieni",
        "dispnee de repaus": "dispnee severa",
        "greu respira": "dispnee",
        "greu respiră": "dispnee",
        "voce ingrosata": "voce ragusita",
        "voce îngroșată": "voce ragusita",
        "lesin": "colaps",
        "leșin": "colaps",
        "furnicaturi": "parestezii",
        "furnicături": "parestezii",
        "frica intensa": "teama intensa",
        "frică intensă": "teama intensa",
        "moarte iminenta": "senzatie de moarte iminenta",
        "moarte iminentă": "senzatie de moarte iminenta",
        "criza de panica": "atac de panica",
        "criză de panică": "atac de panica",
        "respiratie rapida": "hiperventilatie",
        "respirație rapidă": "hiperventilatie",
        "simptome la polen": "polen",
        "simptome la praf": "acarieni",
        "simptome la pisica": "pisica",
        "simptome la pisică": "pisica",
        "agravare nocturna": "tuse nocturna",
        "agravare nocturnă": "tuse nocturna",
        "contact cu persoane racite": "contact infectios",
        "contact cu persoane răcite": "contact infectios",
        "episod brusc": "debut brusc",
        "debut dupa stres": "debut in context emotional",
        "debut după stres": "debut in context emotional",
        "dupa stres": "context emotional",
        "după stres": "context emotional",
        "dupa emotie": "context emotional",
        "după emoție": "context emotional",
        "stres": "context emotional",
        "aer rece": "schimbari de temperatura",
        "frig": "schimbari de temperatura",
        "tuse productiva": "tuse productiva",
        "tuse productivă": "tuse productiva",
        "sputa": "sputa",
        "fumator": "fumator",
        "fumător": "fumator",
        "ortopnee": "ortopnee",
        "pierdere constienta": "colaps",
        "pierdere conștiență": "colaps",
        "detergent nou": "detergent",
        "substante chimice": "substante chimice",
        "substanțe chimice": "substante chimice",
        "balonare": "balonare",
        "lactate": "lactate",
    }

    for src, dst in replacements.items():
        text = text.replace(src, dst)

    text = re.sub(r"[^a-z0-9\s/+\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_text_tokens(text):
    norm_text = normalize_text(text)
    return set(norm_text.split()) if norm_text else set()


def contains_phrase(text, phrase):
    norm_text = normalize_text(text)
    norm_phrase = normalize_text(phrase)
    if not norm_text or not norm_phrase:
        return False
    return norm_phrase in norm_text


def contains_any(text, keywords):
    if not text or not keywords:
        return False

    norm_text = normalize_text(text)
    for kw in keywords:
        kw_norm = normalize_text(kw)
        if kw_norm and kw_norm in norm_text:
            return True
    return False


def count_keyword_hits(text, keywords):
    if not text or not keywords:
        return 0

    norm_text = normalize_text(text)
    hits = 0
    seen = set()

    for kw in keywords:
        kw_norm = normalize_text(kw)
        if kw_norm and kw_norm in norm_text and kw_norm not in seen:
            hits += 1
            seen.add(kw_norm)

    return hits


def count_weighted_hits(text, weighted_keywords):
    if not text or not weighted_keywords:
        return 0

    norm_text = normalize_text(text)
    score = 0
    matched_terms = set()

    for item in weighted_keywords:
        if isinstance(item, dict):
            term = normalize_text(item.get("term", ""))
            weight = item.get("weight", 1)
        else:
            term = normalize_text(item)
            weight = 1

        if not term or term in matched_terms:
            continue

        if term in norm_text:
            try:
                score += int(weight)
            except Exception:
                score += 1
            matched_terms.add(term)

    return score


def infer_probability(score):
    if score >= 22:
        return "mare"
    if score >= 12:
        return "moderată"
    if score >= 6:
        return "scăzută"
    return "foarte scăzută"


def infer_confidence(score):
    if score >= 22:
        return "mare"
    if score >= 12:
        return "moderată"
    if score >= 6:
        return "redusă"
    return "foarte redusă"


def infer_severity(text):
    severe_markers = [
        "dispnee severa",
        "edem laringian",
        "anafilaxie",
        "hipotensiune",
        "saturatie scazuta",
        "cianoza",
        "stridor",
        "bronhospasm sever",
        "colaps",
        "soc",
        "edem lingual",
    ]
    moderate_markers = [
        "wheezing",
        "tuse",
        "dispnee",
        "urticarie extinsa",
        "edem",
        "angioedem",
        "constrictie toracica",
    ]

    if contains_any(text, severe_markers):
        return "severă"
    if contains_any(text, moderate_markers):
        return "moderată"
    return "ușoară"


def get_age_group(age):
    try:
        age_value = float(str(age).replace(",", "."))
    except Exception:
        return "nespecificat"

    if age_value < 2:
        return "sugar"
    if age_value < 12:
        return "copil"
    if age_value < 18:
        return "adolescent"
    return "adult"


def safe_list(value):
    if value is None:
        return []

    if isinstance(value, list):
        out = []
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                out.append(text)
        return out

    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []

    if isinstance(value, dict):
        out = []
        for k, v in value.items():
            if isinstance(v, list):
                for sub in v:
                    sub_text = str(sub).strip()
                    if sub_text:
                        out.append(f"{k}: {sub_text}")
            else:
                v_text = str(v).strip()
                if v_text:
                    out.append(f"{k}: {v_text}")
        return out

    text = str(value).strip()
    return [text] if text else []


def normalize_medication_options(medication_options):
    if not medication_options:
        return []

    normalized = []

    if isinstance(medication_options, list):
        for item in medication_options:
            if isinstance(item, dict):
                normalized.append({
                    "class": str(item.get("class", "")).strip(),
                    "name": str(item.get("name", "")).strip(),
                    "substance": str(item.get("substance", "")).strip(),
                    "dose_child": str(item.get("dose_child", "")).strip(),
                    "dose_adult": str(item.get("dose_adult", "")).strip(),
                    "dose": str(item.get("dose", "")).strip(),
                    "route": str(item.get("route", "")).strip(),
                    "frequency": str(item.get("frequency", "")).strip(),
                    "duration": str(item.get("duration", "")).strip(),
                    "notes": str(item.get("notes", "")).strip(),
                    "adverse_reactions": str(item.get("adverse_reactions", "")).strip(),
                })
            else:
                text = str(item).strip()
                if text:
                    normalized.append({
                        "class": "Medicație orientativă",
                        "name": text,
                        "substance": "",
                        "dose_child": "",
                        "dose_adult": "",
                        "dose": "",
                        "route": "",
                        "frequency": "",
                        "duration": "",
                        "notes": "",
                        "adverse_reactions": "",
                    })

    return normalized


def extract_named_lists(clinical_entry):
    clinical_picture = safe_list(
        clinical_entry.get("clinical_picture")
        or clinical_entry.get("tablou_clinic")
        or clinical_entry.get("symptoms")
        or clinical_entry.get("manifestations")
    )

    treatment = safe_list(
        clinical_entry.get("treatment")
        or clinical_entry.get("tratament")
        or clinical_entry.get("management")
    )

    prevention = safe_list(
        clinical_entry.get("prevention")
        or clinical_entry.get("preventie")
        or clinical_entry.get("prevenție")
    )

    allergen_avoidance = safe_list(
        clinical_entry.get("allergen_avoidance")
        or clinical_entry.get("avoidance")
        or clinical_entry.get("evitare_alergen")
    )

    medication_options = normalize_medication_options(
        clinical_entry.get("medication_options")
        or clinical_entry.get("medicatie")
        or clinical_entry.get("medication")
    )

    return {
        "clinical_picture": clinical_picture,
        "treatment": treatment,
        "prevention": prevention,
        "allergen_avoidance": allergen_avoidance,
        "medication_options": medication_options,
    }


def get_default_diagnosis_knowledge(diagnosis_name):
    return {
        "diagnosis": diagnosis_name,
        "clinical_picture": [
            "Tabloul clinic trebuie corelat cu anamneza, examenul clinic și contextul expunerii."
        ],
        "treatment": [
            "Conduită orientativă individualizată în funcție de severitate și context clinic.",
            "Monitorizare clinică și reevaluare dacă simptomatologia persistă sau se agravează.",
        ],
        "prevention": [
            "Reducerea expunerii la alergeni sau triggeri relevanți.",
            "Educația pacientului privind recunoașterea simptomelor și monitorizarea evoluției.",
        ],
        "allergen_avoidance": [
            "Identificarea și evitarea alergenului sau a factorului agravant, dacă poate fi stabilit."
        ],
        "medication_options": [],
        "age_group_used": "nespecificat",
        "weight_used": "",
        "severity_used": "",
    }


def get_weighted_keywords_for_diagnosis(name, keywords, strong_keywords, high_value_terms=None):
    name_norm = normalize_text(name)
    high_value_terms = high_value_terms or []

    default_weighted = [{"term": kw, "weight": 1} for kw in keywords]
    default_weighted += [{"term": kw, "weight": 3} for kw in strong_keywords]
    default_weighted += [{"term": kw, "weight": 7} for kw in high_value_terms]

    presets = {
        "rinita alergica": [
            {"term": "stranut", "weight": 4},
            {"term": "rinoree", "weight": 2},
            {"term": "rinoree apoasa", "weight": 7},
            {"term": "prurit nazal", "weight": 8},
            {"term": "congestie nazala", "weight": 2},
            {"term": "prurit ocular", "weight": 7},
            {"term": "lacrimare", "weight": 5},
            {"term": "stranut in salve", "weight": 9},
            {"term": "sezonier", "weight": 6},
            {"term": "polen", "weight": 6},
            {"term": "acarieni", "weight": 6},
            {"term": "pisica", "weight": 5},
            {"term": "atopie", "weight": 2},
        ],
        "conjunctivita alergica": [
            {"term": "prurit ocular", "weight": 8},
            {"term": "lacrimare", "weight": 5},
            {"term": "hiperemie oculara", "weight": 5},
            {"term": "edem palpebral", "weight": 6},
            {"term": "secretii apoase", "weight": 4},
        ],
        "astm alergic": [
            {"term": "wheezing", "weight": 11},
            {"term": "dispnee", "weight": 2},
            {"term": "tuse", "weight": 1},
            {"term": "tuse nocturna", "weight": 8},
            {"term": "constrictie toracica", "weight": 7},
            {"term": "polen", "weight": 2},
            {"term": "acarieni", "weight": 2},
            {"term": "atopie", "weight": 4},
            {"term": "agravare la alergeni", "weight": 8},
            {"term": "episoade recurente", "weight": 5},
            {"term": "simptome la efort", "weight": 3},
        ],
        "dermatita atopica": [
            {"term": "prurit", "weight": 4},
            {"term": "eczeme", "weight": 7},
            {"term": "eruptie", "weight": 2},
            {"term": "piele uscata", "weight": 6},
            {"term": "lichenificare", "weight": 6},
            {"term": "leziuni flexurale", "weight": 8},
            {"term": "dermatita", "weight": 2},
            {"term": "atopie", "weight": 2},
        ],
        "urticarie alergica / angioedem": [
            {"term": "urticarie", "weight": 8},
            {"term": "papule", "weight": 2},
            {"term": "placi pruriginoase", "weight": 5},
            {"term": "edem buze", "weight": 6},
            {"term": "edem pleoape", "weight": 6},
            {"term": "angioedem", "weight": 9},
            {"term": "eruptie fugace", "weight": 8},
        ],
        "alergie alimentara": [
            {"term": "dupa aliment", "weight": 10},
            {"term": "prurit oral", "weight": 7},
            {"term": "furnicaturi orale", "weight": 4},
            {"term": "edem buze", "weight": 6},
            {"term": "varsaturi", "weight": 4},
            {"term": "dureri abdominale", "weight": 3},
            {"term": "diaree", "weight": 2},
            {"term": "urticarie", "weight": 4},
            {"term": "wheezing dupa aliment", "weight": 10},
            {"term": "balonare", "weight": 0},
            {"term": "lactate", "weight": 0},
        ],
        "anafilaxie": [
            {"term": "dispnee severa", "weight": 11},
            {"term": "wheezing", "weight": 2},
            {"term": "stridor", "weight": 12},
            {"term": "voce ragusita", "weight": 8},
            {"term": "hipotensiune", "weight": 12},
            {"term": "ameteli", "weight": 2},
            {"term": "colaps", "weight": 12},
            {"term": "edem lingual", "weight": 12},
            {"term": "dificultati la inghitire", "weight": 8},
            {"term": "reactie severa", "weight": 5},
            {"term": "dupa aliment", "weight": 4},
            {"term": "urticarie", "weight": 3},
            {"term": "angioedem", "weight": 4},
            {"term": "context emotional", "weight": -3},
        ],
        "rinita virala / infectioasa": [
            {"term": "rinoree", "weight": 2},
            {"term": "congestie nazala", "weight": 2},
            {"term": "febra", "weight": 10},
            {"term": "odinofagie", "weight": 8},
            {"term": "tuse", "weight": 3},
            {"term": "stare generala alterata", "weight": 9},
            {"term": "mialgii", "weight": 8},
            {"term": "frison", "weight": 8},
            {"term": "contact infectios", "weight": 7},
            {"term": "debut acut", "weight": 7},
        ],
        "rinita non alergica": [
            {"term": "rinoree", "weight": 2},
            {"term": "congestie nazala", "weight": 2},
            {"term": "iritanti", "weight": 8},
            {"term": "fum", "weight": 8},
            {"term": "mirosuri puternice", "weight": 8},
            {"term": "schimbari de temperatura", "weight": 8},
            {"term": "parfum", "weight": 8},
            {"term": "detergent", "weight": 5},
        ],
        "sinuzita acuta": [
            {"term": "congestie nazala", "weight": 2},
            {"term": "durere faciala", "weight": 10},
            {"term": "presiune faciala", "weight": 10},
            {"term": "secretii nazale purulente", "weight": 11},
            {"term": "cefalee", "weight": 3},
            {"term": "febra", "weight": 4},
            {"term": "durere maxilara", "weight": 9},
            {"term": "simptome persistente", "weight": 4},
        ],
        "atac de panica / hiperventilatie": [
            {"term": "atac de panica", "weight": 11},
            {"term": "hiperventilatie", "weight": 10},
            {"term": "palpitatii", "weight": 8},
            {"term": "tremor", "weight": 4},
            {"term": "ameteli", "weight": 3},
            {"term": "parestezii", "weight": 9},
            {"term": "nod in gat", "weight": 4},
            {"term": "teama intensa", "weight": 9},
            {"term": "senzatie de moarte iminenta", "weight": 10},
            {"term": "anxietate", "weight": 6},
            {"term": "dispnee in context emotional", "weight": 9},
            {"term": "context emotional", "weight": 7},
            {"term": "debut brusc", "weight": 5},
        ],
    }

    return presets.get(name_norm, default_weighted)


def compute_pattern_bonus(name, text):
    name_norm = normalize_text(name)
    bonus = 0

    if name_norm == "rinita alergica":
        if contains_any(text, ["stranut"]) and contains_any(text, ["rinoree", "rinoree apoasa"]):
            bonus += 5
        if contains_any(text, ["prurit nazal"]) and contains_any(text, ["lacrimare", "prurit ocular"]):
            bonus += 8
        if contains_any(text, ["polen", "acarieni", "sezonier"]):
            bonus += 6
        if contains_any(text, ["febra", "odinofagie", "secretii purulente", "stare generala alterata", "mialgii"]):
            bonus -= 10

    elif name_norm == "conjunctivita alergica":
        if contains_any(text, ["prurit ocular"]) and contains_any(text, ["lacrimare", "hiperemie oculara"]):
            bonus += 7
        if contains_any(text, ["edem palpebral"]):
            bonus += 3

    elif name_norm == "astm alergic":
        if contains_any(text, ["wheezing"]) and contains_any(text, ["dispnee", "tuse", "tuse nocturna", "constrictie toracica"]):
            bonus += 9
        if contains_any(text, ["polen", "acarieni", "atopie", "agravare la alergeni"]):
            bonus += 5
        if contains_any(text, ["palpitatii", "parestezii", "teama intensa", "senzatie de moarte iminenta"]) and not contains_any(text, ["wheezing"]):
            bonus -= 12
        if contains_any(text, ["febra", "odinofagie", "sputa", "tuse productiva", "fumator", "ortopnee"]) and not contains_any(text, ["wheezing"]):
            bonus -= 10

    elif name_norm == "alergie alimentara":
        if contains_any(text, ["dupa aliment"]) and contains_any(text, ["prurit oral", "varsaturi", "diaree", "edem buze", "urticarie"]):
            bonus += 9
        if contains_any(text, ["balonare", "lactate"]) and not contains_any(text, ["urticarie", "edem buze", "angioedem", "prurit oral"]):
            bonus -= 8

    elif name_norm == "anafilaxie":
        if contains_any(text, ["hipotensiune", "colaps", "stridor", "edem lingual"]):
            bonus += 12
        if contains_any(text, ["dupa aliment", "dupa intepatura", "dupa medicament"]) and contains_any(
            text,
            ["dispnee", "urticarie", "angioedem", "colaps", "ameteli"],
        ):
            bonus += 8
        if contains_any(text, ["context emotional"]) and not contains_any(text, ["urticarie", "angioedem", "hipotensiune", "stridor", "edem lingual"]):
            bonus -= 12

    elif name_norm == "rinita virala / infectioasa":
        if contains_any(text, ["febra"]) and contains_any(text, ["odinofagie", "tuse", "stare generala alterata", "mialgii", "frison"]):
            bonus += 10
        if contains_any(text, ["contact infectios", "debut acut"]):
            bonus += 5
        if contains_any(text, ["prurit nazal", "prurit ocular", "polen", "acarieni", "sezonier", "stranut in salve"]):
            bonus -= 8

    elif name_norm == "rinita non alergica":
        if contains_any(text, ["iritanti", "fum", "mirosuri puternice", "schimbari de temperatura", "parfum"]):
            bonus += 8
        if not contains_any(text, ["prurit nazal", "prurit ocular", "stranut in salve", "polen", "acarieni", "sezonier"]):
            bonus += 3
        if contains_any(text, ["prurit nazal", "prurit ocular", "polen", "acarieni", "sezonier"]):
            bonus -= 6

    elif name_norm == "sinuzita acuta":
        if contains_any(text, ["durere faciala", "presiune faciala"]) and contains_any(text, ["secretii nazale purulente", "febra"]):
            bonus += 9
        if contains_any(text, ["stranut", "prurit nazal", "lacrimare"]):
            bonus -= 5

    elif name_norm == "atac de panica / hiperventilatie":
        if contains_any(text, ["hiperventilatie", "palpitatii"]) and contains_any(text, ["parestezii", "teama intensa", "senzatie de moarte iminenta"]):
            bonus += 12
        if contains_any(text, ["anxietate", "debut in context emotional", "dispnee in context emotional", "context emotional", "debut brusc"]):
            bonus += 7
        if contains_any(text, ["wheezing", "tuse nocturna", "agravare la alergeni", "urticarie", "angioedem", "hipotensiune", "stridor"]):
            bonus -= 12

    return bonus


def compute_exclusion_penalty(text, exclude_keywords):
    if not exclude_keywords:
        return 0

    penalty = 0
    norm_text = normalize_text(text)
    for kw in exclude_keywords:
        kw_norm = normalize_text(kw)
        if kw_norm and kw_norm in norm_text:
            penalty += 5

    return penalty


def compute_contradiction_penalty(text, contradiction_terms):
    if not contradiction_terms:
        return 0

    penalty = 0
    norm_text = normalize_text(text)

    for kw in contradiction_terms:
        kw_norm = normalize_text(kw)
        if kw_norm and kw_norm in norm_text:
            penalty += 7

    return penalty


def compute_minimum_terms_adjustment(text, minimum_required_terms):
    if not minimum_required_terms:
        return 0

    hits = count_keyword_hits(text, minimum_required_terms)
    total = len(set(normalize_text(term) for term in minimum_required_terms if term))

    if total == 0:
        return 0

    ratio = hits / total

    if hits >= 3 or ratio >= 0.5:
        return 10
    if hits == 2:
        return 4
    if hits == 1:
        return -4
    return -14


def compute_high_value_bonus(text, high_value_terms):
    if not high_value_terms:
        return 0

    hits = count_keyword_hits(text, high_value_terms)

    if hits >= 3:
        return 14
    if hits == 2:
        return 8
    if hits == 1:
        return 3
    return 0


def apply_manual_adjustments(name, text, base_score):
    name_norm = normalize_text(name)
    score = base_score
    norm_text = normalize_text(text)

    allergic_markers = [
        "prurit nazal",
        "prurit ocular",
        "lacrimare",
        "stranut",
        "stranut in salve",
        "polen",
        "acarieni",
        "sezonier",
        "atopie",
        "rinoree apoasa",
    ]
    infectious_markers = [
        "febra",
        "odinofagie",
        "stare generala alterata",
        "mialgii",
        "frison",
        "secretii purulente",
        "contact infectios",
        "debut acut",
    ]
    panic_markers = [
        "hiperventilatie",
        "palpitatii",
        "parestezii",
        "teama intensa",
        "senzatie de moarte iminenta",
        "anxietate",
        "atac de panica",
        "context emotional",
    ]

    if name_norm == "astm alergic":
        if contains_any(norm_text, ["wheezing"]):
            score += 5
        if count_keyword_hits(norm_text, ["wheezing", "tuse nocturna", "constrictie toracica", "agravare la alergeni"]) >= 2:
            score += 6
        if not contains_any(norm_text, ["wheezing", "tuse nocturna", "constrictie toracica", "agravare la alergeni"]):
            score -= 10
        if contains_any(norm_text, panic_markers) and not contains_any(norm_text, ["wheezing", "tuse nocturna"]):
            score -= 12
        if contains_any(norm_text, ["febra", "sputa", "tuse productiva", "fumator", "ortopnee"]) and not contains_any(norm_text, ["wheezing"]):
            score -= 12

    elif name_norm == "rinita alergica":
        if count_keyword_hits(norm_text, ["stranut", "rinoree", "prurit nazal", "prurit ocular", "lacrimare"]) >= 2:
            score += 5
        if contains_any(norm_text, ["stranut in salve", "rinoree apoasa"]):
            score += 4
        if not contains_any(norm_text, ["prurit nazal", "prurit ocular", "stranut", "lacrimare", "polen", "acarieni"]):
            score -= 10
        if contains_any(norm_text, infectious_markers):
            score -= 9

    elif name_norm == "rinita virala / infectioasa":
        if count_keyword_hits(norm_text, ["febra", "odinofagie", "stare generala alterata", "mialgii", "frison"]) >= 2:
            score += 7
        if contains_any(norm_text, ["contact infectios", "debut acut"]):
            score += 4
        if count_keyword_hits(norm_text, allergic_markers) >= 2:
            score -= 8

    elif name_norm == "anafilaxie":
        if contains_any(norm_text, ["stridor", "hipotensiune", "colaps", "edem lingual"]):
            score = max(score, 24)
        elif contains_any(norm_text, ["dupa aliment", "dupa intepatura", "dupa medicament"]) and count_keyword_hits(
            norm_text,
            ["urticarie", "angioedem", "dispnee", "ameteli", "varsaturi"],
        ) >= 2:
            score = max(score, 18)
        elif count_keyword_hits(
            norm_text,
            ["dispnee", "urticarie", "angioedem", "ameteli"],
        ) >= 2 and contains_any(norm_text, ["dupa aliment", "dupa intepatura", "dupa medicament"]):
            score = max(score, 16)
        elif contains_any(norm_text, ["context emotional"]) and not contains_any(norm_text, ["urticarie", "angioedem", "hipotensiune", "stridor", "edem lingual"]):
            score -= 14
        elif not contains_any(norm_text, ["dispnee", "stridor", "hipotensiune", "colaps", "angioedem", "urticarie"]):
            score -= 8

    elif name_norm == "alergie alimentara":
        if contains_any(norm_text, ["dupa aliment"]):
            score += 6
        else:
            score -= 5
        if contains_any(norm_text, ["balonare", "lactate"]) and not contains_any(norm_text, ["urticarie", "edem buze", "angioedem", "prurit oral", "wheezing dupa aliment"]):
            score -= 10

    elif name_norm == "rinita non alergica":
        if contains_any(norm_text, ["iritanti", "fum", "mirosuri puternice", "parfum", "schimbari de temperatura"]) and not contains_any(norm_text, allergic_markers):
            score += 5
        if not contains_any(norm_text, ["prurit nazal", "prurit ocular", "stranut in salve", "polen", "acarieni", "sezonier"]):
            score += 2

    elif name_norm == "sinuzita acuta":
        if count_keyword_hits(norm_text, ["durere faciala", "presiune faciala", "secretii nazale purulente"]) >= 2:
            score += 6

    elif name_norm == "atac de panica / hiperventilatie":
        if count_keyword_hits(norm_text, ["hiperventilatie", "palpitatii", "parestezii", "teama intensa", "senzatie de moarte iminenta"]) >= 2:
            score += 10
        if contains_any(norm_text, ["debut in context emotional", "dispnee in context emotional", "anxietate", "context emotional", "debut brusc"]):
            score += 5
        if not contains_any(norm_text, ["hiperventilatie", "palpitatii", "parestezii", "teama intensa", "senzatie de moarte iminenta", "anxietate", "context emotional"]):
            score -= 8
        if contains_any(norm_text, ["wheezing", "tuse nocturna", "agravare la alergeni", "urticarie", "angioedem", "hipotensiune", "stridor"]):
            score -= 12

    return max(score, 0)


def build_ranked_entry(diag, text):
    name = str(diag.get("name", "")).strip()
    if not name:
        return None

    keywords = diag.get("keywords", []) or []
    strong_keywords = diag.get("strong_keywords", []) or []
    high_value_terms = diag.get("high_value_terms", []) or []
    minimum_required_terms = diag.get("minimum_required_terms", []) or []
    contradiction_terms = diag.get("contradiction_terms", []) or []
    exclude_keywords = diag.get("exclude_keywords", []) or []
    associated_diagnoses = diag.get("associated_diagnoses", []) or []
    recommended_tests = diag.get("recommended_tests", []) or []
    treatment_plan = diag.get("treatment_plan", []) or []
    supports = diag.get("supports", []) or []
    limits = diag.get("limits", []) or []
    red_flags = diag.get("red_flags", []) or []
    notes = diag.get("notes", []) or []

    weighted_keywords = get_weighted_keywords_for_diagnosis(name, keywords, strong_keywords, high_value_terms)

    base_score = count_weighted_hits(text, weighted_keywords)
    pattern_bonus = compute_pattern_bonus(name, text)
    exclude_penalty = compute_exclusion_penalty(text, exclude_keywords)
    contradiction_penalty = compute_contradiction_penalty(text, contradiction_terms)
    minimum_adjustment = compute_minimum_terms_adjustment(text, minimum_required_terms)
    high_value_bonus = compute_high_value_bonus(text, high_value_terms)

    raw_score = (
        base_score
        + pattern_bonus
        + minimum_adjustment
        + high_value_bonus
        - exclude_penalty
        - contradiction_penalty
    )

    score = apply_manual_adjustments(name, text, raw_score)
    score = max(score, 0)

    has_any_match = score > 0

    return {
        "name": name,
        "score": score,
        "probability": infer_probability(score),
        "severity": diag.get("severity") or infer_severity(text),
        "confidence": infer_confidence(score),
        "associated_diagnoses": safe_list(associated_diagnoses),
        "supports": safe_list(supports),
        "limits": safe_list(limits),
        "recommended_tests": safe_list(recommended_tests),
        "treatment_plan": safe_list(treatment_plan),
        "red_flags": safe_list(red_flags),
        "notes": safe_list(notes),
        "has_any_match": has_any_match,
    }


def build_fallback_analysis(text):
    return {
        "primary_diagnosis": "Nespecificat",
        "primary_probability": "foarte scăzută",
        "severity": infer_severity(text),
        "confidence": "foarte redusă",
        "associated_diagnoses": [],
        "supports": [
            "Nu au fost identificate suficiente criterii pentru un diagnostic diferențial robust."
        ],
        "limits": [
            "Datele clinice introduse sunt insuficiente sau prea nespecifice."
        ],
        "recommended_tests": [
            "Anamneză clinică mai detaliată.",
            "Corelare cu examenul clinic și investigațiile relevante."
        ],
        "treatment_plan": [
            "Reevaluare după completarea datelor clinice."
        ],
        "red_flags": [],
        "notes": [
            "Rezultatul este nespecific și orientativ."
        ],
        "alternatives": [],
    }


def enrich_primary_output(primary, alternatives, text):
    output = {
        "primary_diagnosis": primary["name"],
        "primary_probability": primary["probability"],
        "severity": primary["severity"],
        "confidence": primary["confidence"],
        "associated_diagnoses": primary.get("associated_diagnoses", []) or alternatives,
        "supports": primary.get("supports", []) or [
            "Simptomatologia introdusă este compatibilă cu diagnosticul orientativ selectat."
        ],
        "limits": primary.get("limits", []) or [
            "Rezultatul trebuie interpretat în context clinic complet."
        ],
        "recommended_tests": primary.get("recommended_tests", []) or [
            "Investigații suplimentare în funcție de suspiciunea clinică."
        ],
        "treatment_plan": primary.get("treatment_plan", []) or [
            "Conduită clinică individualizată în funcție de severitate."
        ],
        "red_flags": primary.get("red_flags", []),
        "notes": primary.get("notes", []) or [
            "Analiza este orientativă și nu înlocuiește decizia clinică."
        ],
        "alternatives": alternatives,
    }

    primary_name = normalize_text(primary["name"])

    if primary_name == "anafilaxie":
        if "Administrarea de urgență a adrenalinei intramuscular, conform protocolului clinic." not in output["treatment_plan"]:
            output["treatment_plan"].insert(
                0,
                "Administrarea de urgență a adrenalinei intramuscular, conform protocolului clinic.",
            )
        if "Evaluare și monitorizare de urgență." not in output["recommended_tests"]:
            output["recommended_tests"].insert(0, "Evaluare și monitorizare de urgență.")
        if not output["red_flags"]:
            output["red_flags"] = [
                "Stridor",
                "Hipotensiune",
                "Colaps",
                "Edem lingual / laringian",
                "Dispnee severă",
            ]
        output["notes"] = output["notes"] + [
            "Suspiciunea de anafilaxie impune conduită de urgență."
        ]

    elif primary_name == "astm alergic":
        if not output["supports"]:
            output["supports"] = [
                "Simptomatologia respiratorie inferioară este compatibilă cu hiperreactivitate bronșică.",
                "Agravarea la alergeni sau nocturn susține o componentă astmatică.",
            ]
        if not output["limits"]:
            output["limits"] = [
                "Tusea și dispneea au multiple cauze și necesită diferențiere față de alte patologii respiratorii sau cardiace.",
                "În lipsa confirmării funcționale, încadrarea rămâne orientativă.",
            ]

    elif primary_name == "rinita alergica":
        if not output["supports"]:
            output["supports"] = [
                "Asocierea dintre strănut, rinoree și prurit nazal susține etiologia alergică.",
                "Contextul sezonier sau expunerea la alergeni crește probabilitatea clinică.",
            ]

    elif primary_name == "atac de panica / hiperventilatie":
        if "Evaluare clinică pentru excluderea unei cauze respiratorii, cardiace sau alergice reale." not in output["recommended_tests"]:
            output["recommended_tests"].insert(
                0,
                "Evaluare clinică pentru excluderea unei cauze respiratorii, cardiace sau alergice reale."
            )

    if primary["score"] < 6:
        output["notes"] = output["notes"] + [
            "Scorul de potrivire este redus; concluzia are valoare orientativă limitată."
        ]
        if output["primary_probability"] == "foarte scăzută":
            output["confidence"] = "foarte redusă"

    if contains_any(text, ["stridor", "hipotensiune", "colaps", "edem lingual", "cianoza"]):
        merged_flags = output["red_flags"] + [
            "Stridor",
            "Hipotensiune",
            "Colaps",
            "Edem lingual",
            "Cianoză",
        ]
        dedup = []
        seen = set()
        for item in merged_flags:
            key = normalize_text(item)
            if key and key not in seen:
                seen.add(key)
                dedup.append(item)
        output["red_flags"] = dedup

    return output


def rank_differential_diagnoses(full_text, diagnoses):
    text = normalize_text(full_text)

    if not text:
        return [], {
            "primary_diagnosis": "Nespecificat",
            "primary_probability": "foarte scăzută",
            "severity": "ușoară",
            "confidence": "foarte redusă",
            "associated_diagnoses": [],
            "supports": [],
            "limits": [
                "Nu au fost introduse suficiente date clinice."
            ],
            "recommended_tests": [],
            "treatment_plan": [],
            "red_flags": [],
            "notes": [
                "Analiza nu a putut fi generată în absența datelor clinice."
            ],
            "alternatives": [],
        }

    ranked_all = []

    for diag in diagnoses:
        if not isinstance(diag, dict):
            continue

        entry = build_ranked_entry(diag, text)
        if entry:
            ranked_all.append(entry)

    if not ranked_all:
        return [], build_fallback_analysis(text)

    ranked_all = sorted(
        ranked_all,
        key=lambda x: (
            x["score"],
            len(x.get("associated_diagnoses", [])),
            len(x.get("supports", [])),
        ),
        reverse=True,
    )

    positive_ranked = [item for item in ranked_all if item["score"] > 0]

    if positive_ranked:
        primary = positive_ranked[0]
        alternatives_pool = positive_ranked[1:]
    else:
        ranked_display = ranked_all[:5]
        primary = ranked_display[0]
        for item in ranked_display:
            item.pop("has_any_match", None)
        alternatives = [item["name"] for item in ranked_display[1:5]]
        return ranked_display, enrich_primary_output(primary, alternatives, text)

    ranked_display = [primary]

    for item in alternatives_pool:
        if item["name"] == primary["name"]:
            continue
        if len(ranked_display) >= 5:
            break
        ranked_display.append(item)

    if len(ranked_display) < 5:
        zero_score_fill = [
            item for item in ranked_all
            if item["score"] == 0 and item["name"] != primary["name"]
        ]
        for item in zero_score_fill:
            if len(ranked_display) >= 5:
                break
            ranked_display.append(item)

    for item in ranked_display:
        item.pop("has_any_match", None)

    alternatives = [item["name"] for item in ranked_display[1:5]]
    clinical_output = enrich_primary_output(primary, alternatives, text)

    return ranked_display, clinical_output


def choose_age_specific_section(entry, age_group):
    if not isinstance(entry, dict):
        return entry

    age_specific = entry.get("age_specific")
    if not isinstance(age_specific, dict):
        return entry

    selected = age_specific.get(age_group)
    if isinstance(selected, dict):
        merged = dict(entry)
        for key, value in selected.items():
            merged[key] = value
        return merged

    return entry


def get_treatment_details(diagnosis_name, knowledge_ro, age="", weight="", severity=""):
    entry = knowledge_ro.get(diagnosis_name)

    if not isinstance(entry, dict):
        fallback = get_default_diagnosis_knowledge(diagnosis_name)
        fallback["weight_used"] = str(weight).strip()
        fallback["severity_used"] = str(severity).strip()
        fallback["age_group_used"] = get_age_group(age)
        return fallback

    age_group = get_age_group(age)
    entry = choose_age_specific_section(entry, age_group)
    extracted = extract_named_lists(entry)

    result = {
        "diagnosis": entry.get("diagnosis") or entry.get("name") or diagnosis_name,
        "clinical_picture": extracted["clinical_picture"] or [
            "Manifestările clinice trebuie corelate cu istoricul de expunere și examenul clinic."
        ],
        "treatment": extracted["treatment"] or [
            "Tratament orientativ în funcție de severitate și profilul pacientului."
        ],
        "prevention": extracted["prevention"] or [
            "Măsuri generale de prevenție și reducere a expunerii."
        ],
        "allergen_avoidance": extracted["allergen_avoidance"] or [
            "Evitarea alergenului relevant atunci când acesta poate fi identificat."
        ],
        "medication_options": extracted["medication_options"],
        "age_group_used": age_group,
        "weight_used": str(weight).strip(),
        "severity_used": str(severity).strip(),
    }

    return result