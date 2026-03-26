import json
import re
import unicodedata


def load_diagnoses(path="data/diagnoses.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_romanian_knowledge(path="data/allergy_knowledge_ro.json"):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        normalized = {}
        for item in data:
            if isinstance(item, dict):
                name = item.get("diagnosis") or item.get("name")
                if name:
                    normalized[name] = item
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
    text = re.sub(r"[^a-z0-9\s/+-]", " ", text)
    text = re.sub(r"\s+", " ", text)

    replacements = {
        "nas infundat": "congestie nazala",
        "n as infundat": "congestie nazala",
        "obstructie nazala": "congestie nazala",
        "curge nasul": "rinoree",
        "scurgere nazala": "rinoree",
        "secretii nazale apoase": "rinoree",
        "mancarime nazala": "prurit nazal",
        "prurit nasal": "prurit nazal",
        "mancarime la nas": "prurit nazal",
        "mancarime oculara": "prurit ocular",
        "mancarime la ochi": "prurit ocular",
        "ochi rosii": "hiperemie oculara",
        "ochi care lacrimeaza": "lacrimare",
        "lacrimare oculara": "lacrimare",
        "suieraturi": "wheezing",
        "respiratie suieratoare": "wheezing",
        "dificultate la respiratie": "dispnee",
        "greutate in respiratie": "dispnee",
        "eczema": "eczeme",
        "eczematos": "eczeme",
        "eruptie cutanata": "eruptie",
        "reactie dupa aliment": "dupa aliment",
        "dupa masa": "dupa aliment",
        "dupa ingestie": "dupa aliment",
        "umflare buze": "edem buze",
        "umflare pleoape": "edem pleoape",
        "soc anafilactic": "anafilaxie",
        "febra mare": "febra",
        "subfebrilitate": "febra",
        "durere in gat": "odinofagie",
        "gat iritat": "odinofagie",
        "mirosuri puternice": "iritanti",
        "fum de tigara": "fum",
    }

    for src, dst in replacements.items():
        text = text.replace(src, dst)

    text = re.sub(r"\s+", " ", text).strip()
    return text


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

    for kw in keywords:
        kw_norm = normalize_text(kw)
        if kw_norm and kw_norm in norm_text:
            hits += 1

    return hits


def count_weighted_hits(text, weighted_keywords):
    if not text or not weighted_keywords:
        return 0

    norm_text = normalize_text(text)
    score = 0

    for item in weighted_keywords:
        if isinstance(item, dict):
            term = normalize_text(item.get("term", ""))
            weight = item.get("weight", 1)
        else:
            term = normalize_text(item)
            weight = 1

        if term and term in norm_text:
            try:
                score += int(weight)
            except Exception:
                score += 1

    return score


def infer_probability(score):
    if score >= 12:
        return "mare"
    if score >= 7:
        return "moderată"
    return "scăzută"


def infer_confidence(score):
    if score >= 12:
        return "mare"
    if score >= 7:
        return "moderată"
    return "redusă"


def infer_severity(text):
    severe_markers = [
        "dispnee severa", "edem laringian", "anafilaxie", "hipotensiune",
        "saturatie scazuta", "cianoza", "stridor", "bronhospasm sever",
        "colaps", "soc", "edem lingual"
    ]
    moderate_markers = [
        "wheezing", "tuse", "dispnee", "urticarie extinsa", "edem", "angioedem"
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
                    "adverse_reactions": str(item.get("adverse_reactions", "")).strip()
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
                        "adverse_reactions": ""
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
        "medication_options": medication_options
    }


def get_default_diagnosis_knowledge(diagnosis_name):
    return {
        "diagnosis": diagnosis_name,
        "clinical_picture": [
            "Tabloul clinic trebuie corelat cu anamneza, examenul clinic și contextul expunerii."
        ],
        "treatment": [
            "Conduită orientativă individualizată în funcție de severitate și context clinic.",
            "Monitorizare clinică și reevaluare dacă simptomatologia persistă sau se agravează."
        ],
        "prevention": [
            "Reducerea expunerii la alergeni sau triggeri relevanți.",
            "Educația pacientului privind recunoașterea simptomelor și monitorizarea evoluției."
        ],
        "allergen_avoidance": [
            "Identificarea și evitarea alergenului sau a factorului agravant, dacă poate fi stabilit."
        ],
        "medication_options": [],
        "age_group_used": "nespecificat",
        "weight_used": "",
        "severity_used": ""
    }


def get_weighted_keywords_for_diagnosis(name, keywords, strong_keywords):
    name_norm = normalize_text(name)

    default_weighted = [{"term": kw, "weight": 1} for kw in keywords]
    default_weighted += [{"term": kw, "weight": 2} for kw in strong_keywords]

    presets = {
        "rinita alergica": [
            {"term": "stranut", "weight": 3},
            {"term": "rinoree", "weight": 3},
            {"term": "prurit nazal", "weight": 4},
            {"term": "congestie nazala", "weight": 2},
            {"term": "prurit ocular", "weight": 3},
            {"term": "lacrimare", "weight": 2},
            {"term": "sezonier", "weight": 4},
            {"term": "polen", "weight": 4},
            {"term": "acarieni", "weight": 3},
            {"term": "conjunctivita", "weight": 2},
        ],
        "conjunctivita alergica": [
            {"term": "prurit ocular", "weight": 4},
            {"term": "lacrimare", "weight": 3},
            {"term": "hiperemie oculara", "weight": 3},
            {"term": "edem palpebral", "weight": 3},
            {"term": "secretii apoase", "weight": 2},
            {"term": "polen", "weight": 2},
        ],
        "astm alergic": [
            {"term": "wheezing", "weight": 4},
            {"term": "dispnee", "weight": 4},
            {"term": "tuse", "weight": 2},
            {"term": "tuse nocturna", "weight": 3},
            {"term": "constrictie toracica", "weight": 3},
            {"term": "alergeni", "weight": 2},
        ],
        "dermatita atopica": [
            {"term": "prurit", "weight": 3},
            {"term": "eczeme", "weight": 4},
            {"term": "eruptie", "weight": 2},
            {"term": "piele uscata", "weight": 3},
            {"term": "lichenificare", "weight": 3},
            {"term": "leziuni flexurale", "weight": 4},
            {"term": "dermatita", "weight": 2},
        ],
        "urticarie alergica / angioedem": [
            {"term": "urticarie", "weight": 4},
            {"term": "papule", "weight": 2},
            {"term": "placi pruriginoase", "weight": 3},
            {"term": "edem buze", "weight": 3},
            {"term": "edem pleoape", "weight": 3},
            {"term": "angioedem", "weight": 4},
            {"term": "eruptie fugace", "weight": 4},
        ],
        "alergie alimentara": [
            {"term": "dupa aliment", "weight": 5},
            {"term": "prurit oral", "weight": 4},
            {"term": "furnicaturi orale", "weight": 3},
            {"term": "edem buze", "weight": 3},
            {"term": "varsaturi", "weight": 3},
            {"term": "dureri abdominale", "weight": 3},
            {"term": "diaree", "weight": 2},
            {"term": "wheezing dupa aliment", "weight": 5},
        ],
        "anafilaxie": [
            {"term": "dispnee severa", "weight": 6},
            {"term": "wheezing", "weight": 2},
            {"term": "stridor", "weight": 6},
            {"term": "voce ragusita", "weight": 5},
            {"term": "hipotensiune", "weight": 6},
            {"term": "ameteli", "weight": 3},
            {"term": "colaps", "weight": 6},
            {"term": "edem lingual", "weight": 6},
            {"term": "dificultati la inghitire", "weight": 5},
            {"term": "reactie severa", "weight": 4},
        ],
        "rinita virala / infectioasa": [
            {"term": "rinoree", "weight": 1},
            {"term": "congestie nazala", "weight": 1},
            {"term": "febra", "weight": 5},
            {"term": "odinofagie", "weight": 4},
            {"term": "tuse", "weight": 2},
            {"term": "stare generala alterata", "weight": 4},
        ],
        "rinita non alergica": [
            {"term": "rinoree", "weight": 1},
            {"term": "congestie nazala", "weight": 1},
            {"term": "iritanti", "weight": 4},
            {"term": "fum", "weight": 4},
            {"term": "mirosuri puternice", "weight": 4},
            {"term": "schimbari de temperatura", "weight": 4},
        ],
        "sinuzita acuta": [
            {"term": "congestie nazala", "weight": 2},
            {"term": "durere faciala", "weight": 5},
            {"term": "presiune faciala", "weight": 5},
            {"term": "secretii nazale purulente", "weight": 6},
            {"term": "cefalee", "weight": 3},
            {"term": "febra", "weight": 3},
        ],
    }

    return presets.get(name_norm, default_weighted)


def compute_pattern_bonus(name, text):
    name_norm = normalize_text(name)
    bonus = 0

    if name_norm == "rinita alergica":
        if contains_any(text, ["stranut"]) and contains_any(text, ["rinoree"]):
            bonus += 4
        if contains_any(text, ["prurit nazal"]) and contains_any(text, ["lacrimare", "prurit ocular", "conjunctivita"]):
            bonus += 4
        if contains_any(text, ["polen", "acarieni", "sezonier"]):
            bonus += 4
        if contains_any(text, ["febra", "odinofagie", "secretii purulente"]):
            bonus -= 5

    elif name_norm == "conjunctivita alergica":
        if contains_any(text, ["prurit ocular"]) and contains_any(text, ["lacrimare", "hiperemie oculara"]):
            bonus += 4
        if contains_any(text, ["edem palpebral"]):
            bonus += 2

    elif name_norm == "astm alergic":
        if contains_any(text, ["wheezing"]) and contains_any(text, ["dispnee", "tuse", "tuse nocturna"]):
            bonus += 4
        if contains_any(text, ["alergeni", "polen", "acarieni"]):
            bonus += 2

    elif name_norm == "alergie alimentara":
        if contains_any(text, ["dupa aliment"]) and contains_any(text, ["prurit oral", "varsaturi", "diaree", "edem buze"]):
            bonus += 5

    elif name_norm == "anafilaxie":
        if contains_any(text, ["hipotensiune", "colaps", "stridor", "edem lingual"]):
            bonus += 6

    elif name_norm == "rinita virala / infectioasa":
        if contains_any(text, ["febra"]) and contains_any(text, ["odinofagie", "tuse", "stare generala alterata"]):
            bonus += 5
        if contains_any(text, ["prurit nazal", "prurit ocular", "polen", "acarieni"]):
            bonus -= 4

    elif name_norm == "rinita non alergica":
        if contains_any(text, ["iritanti", "fum", "mirosuri puternice", "schimbari de temperatura"]):
            bonus += 4
        if contains_any(text, ["prurit nazal", "prurit ocular", "polen", "acarieni", "sezonier"]):
            bonus -= 3

    elif name_norm == "sinuzita acuta":
        if contains_any(text, ["durere faciala", "presiune faciala"]) and contains_any(text, ["secretii nazale purulente", "febra"]):
            bonus += 5
        if contains_any(text, ["stranut", "prurit nazal", "lacrimare"]):
            bonus -= 3

    return bonus


def compute_exclusion_penalty(text, exclude_keywords):
    if not exclude_keywords:
        return 0

    penalty = 0
    for kw in exclude_keywords:
        kw_norm = normalize_text(kw)
        if kw_norm and kw_norm in text:
            penalty += 3

    return penalty


def build_ranked_entry(diag, text):
    name = str(diag.get("name", "")).strip()
    if not name:
        return None

    keywords = diag.get("keywords", []) or []
    strong_keywords = diag.get("strong_keywords", []) or []
    exclude_keywords = diag.get("exclude_keywords", []) or []
    associated_diagnoses = diag.get("associated_diagnoses", []) or []
    recommended_tests = diag.get("recommended_tests", []) or []
    treatment_plan = diag.get("treatment_plan", []) or []
    supports = diag.get("supports", []) or []
    limits = diag.get("limits", []) or []
    red_flags = diag.get("red_flags", []) or []
    notes = diag.get("notes", []) or []

    weighted_keywords = get_weighted_keywords_for_diagnosis(name, keywords, strong_keywords)

    base_score = count_weighted_hits(text, weighted_keywords)
    pattern_bonus = compute_pattern_bonus(name, text)
    exclude_penalty = compute_exclusion_penalty(text, exclude_keywords)

    score = base_score + pattern_bonus - exclude_penalty
    if score < 0:
        score = 0

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
        "has_any_match": has_any_match
    }


def build_fallback_analysis(text):
    return {
        "primary_diagnosis": "Nespecificat",
        "primary_probability": "scăzută",
        "severity": infer_severity(text),
        "confidence": "redusă",
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
        "alternatives": []
    }


def rank_differential_diagnoses(full_text, diagnoses):
    text = normalize_text(full_text)

    if not text:
        return [], {
            "primary_diagnosis": "Nespecificat",
            "primary_probability": "scăzută",
            "severity": "ușoară",
            "confidence": "redusă",
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
            "alternatives": []
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
            len(x.get("supports", []))
        ),
        reverse=True
    )

    positive_ranked = [item for item in ranked_all if item["score"] > 0]

    if positive_ranked:
        primary = positive_ranked[0]

        alternatives_pool = positive_ranked[1:]

        if len(alternatives_pool) < 4:
            zero_score_fill = [
                item for item in ranked_all
                if item["score"] == 0 and item["name"] != primary["name"]
            ]
            alternatives_pool.extend(zero_score_fill)

        ranked_display = [primary]
        for item in alternatives_pool:
            if item["name"] == primary["name"]:
                continue
            if len(ranked_display) >= 5:
                break
            ranked_display.append(item)
    else:
        ranked_display = ranked_all[:5]
        primary = ranked_display[0]

    for item in ranked_display:
        item.pop("has_any_match", None)

    alternatives = [item["name"] for item in ranked_display[1:5]]

    clinical_output = {
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
        "alternatives": alternatives
    }

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
        "severity_used": str(severity).strip()
    }

    return result