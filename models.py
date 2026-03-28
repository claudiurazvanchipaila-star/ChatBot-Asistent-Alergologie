import json
import re
import unicodedata
import difflib


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


def get_normalization_replacements():
    return {
        # nazal / ORL
        "nas infundat": "congestie nazala",
        "nas înfundat": "congestie nazala",
        "se infunda nasul": "congestie nazala",
        "se înfundă nasul": "congestie nazala",
        "obstructie nazala": "congestie nazala",
        "obstructie": "congestie",
        "curge nasul": "rinoree",
        "nas care curge": "rinoree",
        "nas care picura": "rinoree",
        "nas care picură": "rinoree",
        "scurgeri nazale": "rinoree",
        "scurgere nazala": "rinoree",
        "hipersecretie nazala": "rinoree",
        "hipersecreție nazală": "rinoree",
        "secretii nazale": "rinoree",
        "secreții nazale": "rinoree",
        "secretii nazale apoase": "rinoree apoasa",
        "secreții nazale apoase": "rinoree apoasa",
        "scurgeri nazale apoase": "rinoree apoasa",
        "secretii seroase": "rinoree apoasa",
        "secreții seroase": "rinoree apoasa",
        "rinoree apoasa": "rinoree apoasa",
        "muci galbeni": "secretii nazale purulente",
        "muci verzi": "secretii nazale purulente",
        "secretii purulente": "secretii nazale purulente",
        "secreții purulente": "secretii nazale purulente",

        # alergie oculara
        "mancarime oculara": "prurit ocular",
        "mâncărime oculară": "prurit ocular",
        "mancarime la ochi": "prurit ocular",
        "mâncărime la ochi": "prurit ocular",
        "ochi care mananca": "prurit ocular",
        "ochi care mănâncă": "prurit ocular",
        "ochi rosii": "hiperemie oculara",
        "ochi roșii": "hiperemie oculara",
        "roseata oculara": "hiperemie oculara",
        "roșeață oculară": "hiperemie oculara",
        "ochi care lacrimeaza": "lacrimare",
        "ochi care lăcrimează": "lacrimare",
        "lacrimare oculara": "lacrimare",
        "pleoape umflate": "edem pleoape",
        "umflare ochi": "edem pleoape",

        # prurit
        "mancarime nazala": "prurit nazal",
        "mâncărime nazală": "prurit nazal",
        "mancarime la nas": "prurit nazal",
        "mâncărime la nas": "prurit nazal",
        "mancarime de piele": "prurit",
        "mâncărime de piele": "prurit",
        "mancarime pe piele": "prurit",
        "mâncărime pe piele": "prurit",
        "mancarime intensa": "prurit",
        "mâncărime intensă": "prurit",
        "mananca pielea": "prurit",
        "mănâncă pielea": "prurit",

        # respirator
        "suieraturi": "wheezing",
        "șuierături": "wheezing",
        "respiratie suieratoare": "wheezing",
        "respirație șuierătoare": "wheezing",
        "dificultate la respiratie": "dispnee",
        "dificultate la respirație": "dispnee",
        "greutate in respiratie": "dispnee",
        "greutate în respirație": "dispnee",
        "lipsa de aer": "dispnee",
        "lipsă de aer": "dispnee",
        "nu poate trage aer": "dispnee",
        "senzatie de sufocare": "dispnee",
        "senzație de sufocare": "dispnee",
        "sufocare": "dispnee",
        "greu respira": "dispnee",
        "greu respiră": "dispnee",
        "respira foarte greu": "dispnee severa",
        "respiră foarte greu": "dispnee severa",
        "nu poate respira": "dispnee severa",
        "dispnee de repaus": "dispnee severa",
        "strangere in piept": "constrictie toracica",
        "strângere în piept": "constrictie toracica",
        "apasare in piept": "constrictie toracica",
        "apăsare în piept": "constrictie toracica",
        "tuse cu expectoratie": "tuse productiva",
        "tuse cu expectorație": "tuse productiva",
        "tuse cu sputa": "tuse productiva",
        "tuse cu sputa": "tuse productiva",
        "tuse productiva": "tuse productiva",
        "tuse productivă": "tuse productiva",
        "flegma": "sputa",
        "flegmă": "sputa",
        "tuseste cu sputa": "tuse productiva",
        "tușește cu spută": "tuse productiva",
        "tuseste cu mucus": "tuse productiva",
        "tușește cu mucus": "tuse productiva",

        # infectios
        "febra mare": "febra",
        "febră mare": "febra",
        "subfebrilitate": "febra",
        "durere in gat": "odinofagie",
        "durere în gât": "odinofagie",
        "gat iritat": "odinofagie",
        "gât iritat": "odinofagie",
        "contact cu persoane racite": "contact infectios",
        "contact cu persoane răcite": "contact infectios",
        "colegi raciti": "colegi raciti",
        "colegi răciți": "colegi raciti",

        # panic / emotional
        "frica intensa": "teama intensa",
        "frică intensă": "teama intensa",
        "moarte iminenta": "senzatie de moarte iminenta",
        "moarte iminentă": "senzatie de moarte iminenta",
        "criza de panica": "atac de panica",
        "criză de panică": "atac de panica",
        "respiratie rapida": "hiperventilatie",
        "respirație rapidă": "hiperventilatie",
        "furnicaturi": "parestezii",
        "furnicături": "parestezii",
        "inima bate tare": "palpitatii",
        "episod brusc": "debut brusc",
        "debut dupa stres": "debut in context emotional",
        "debut după stres": "debut in context emotional",
        "dupa stres": "context emotional",
        "după stres": "context emotional",
        "dupa emotie": "context emotional",
        "după emoție": "context emotional",
        "stres": "context emotional",
        "emotie": "context emotional",
        "emoție": "context emotional",

        # urticarie / anafilaxie
        "umflare buze": "edem buze",
        "buza umflata": "edem buze",
        "buza umflată": "edem buze",
        "umflare pleoape": "edem pleoape",
        "soc anafilactic": "anafilaxie",
        "șoc anafilactic": "anafilaxie",
        "lesin": "colaps",
        "leșin": "colaps",
        "pierdere constienta": "colaps",
        "pierdere conștiență": "colaps",
        "limba umflata": "edem lingual",
        "limbă umflată": "edem lingual",
        "voce ingrosata": "voce ragusita",
        "voce îngroșată": "voce ragusita",

        # triggeri
        "simptome la polen": "polen",
        "simptome la praf": "acarieni",
        "simptome la pisica": "pisica",
        "simptome la pisică": "pisica",
        "praf de casa": "acarieni",
        "praf de casă": "acarieni",
        "mirosuri puternice": "iritanti",
        "mirosuri intense": "iritanti",
        "fum de tigara": "fum",
        "fum de țigară": "fum",
        "aer rece": "schimbari de temperatura",
        "frig": "schimbari de temperatura",
        "detergent nou": "detergent",
        "substante chimice": "substante chimice",
        "substanțe chimice": "substante chimice",

        # digestiv
        "reactie dupa aliment": "dupa aliment",
        "reacție după aliment": "dupa aliment",
        "dupa masa": "dupa aliment",
        "după masă": "dupa aliment",
        "dupa ingestie": "dupa aliment",
        "după ingestie": "dupa aliment",
        "dupa ce a mancat": "dupa aliment",
        "după ce a mâncat": "dupa aliment",
        "mancarime in gura": "prurit oral",
        "mâncărime în gură": "prurit oral",
        "crampe abdominale": "dureri abdominale",
        "greața": "greata",
        "greaţă": "greata",
        "greata": "greata",
        "varsaturi": "varsaturi",
        "vărsături": "varsaturi",
        "balonare": "balonare",
        "lactate": "lactate",
        "diaree dupa lactate": "lactate diaree",
        "diaree după lactate": "lactate diaree",

        # cutanat
        "eczema": "eczeme",
        "eczemă": "eczeme",
        "eczematos": "eczeme",
        "eruptie cutanata": "eruptie",
        "erupție cutanată": "eruptie",
        "piele uscata": "piele uscata",
        "piele uscată": "piele uscata",
        "piele foarte uscata": "piele uscata",
        "piele foarte uscată": "piele uscata",
        "piele aspra": "piele uscata",
        "piele aspră": "piele uscata",
        "pete rosii": "eritem",
        "pete roșii": "eritem",
        "pete rosiatice": "eritem",
        "pete roșiatice": "eritem",
        "pete rosii pe piele": "eritem",
        "pete roșii pe piele": "eritem",
        "leziuni rosiatice": "eritem",
        "leziuni roșiatice": "eritem",
        "zone rosii": "eritem",
        "zone roșii": "eritem",
        "roseata": "eritem",
        "roșeață": "eritem",
        "rosu pe piele": "eritem",
        "roșu pe piele": "eritem",
        "leziune eritematoasa": "eritem",
        "leziune eritematoasă": "eritem",
        "leziune eritematoasa tegumentara": "eritem",
        "leziune eritematoasă tegumentară": "eritem",
        "leziune tegumentara": "tegument",
        "leziune tegumentară": "tegument",
        "tegumentara": "tegument",
        "tegumentară": "tegument",
        "iritatie locala": "eritem local",
        "iritație locală": "eritem local",
        "iritatie": "iritatie",
        "iritație": "iritatie",
        "piele iritata": "iritatie",
        "piele iritată": "iritatie",

        # distributie leziuni
        "coate": "zone de flexie",
        "genunchi": "zone de flexie",
        "pliuri": "zone de flexie",
        "la incheieturi": "zone de flexie",
        "la încheieturi": "zone de flexie",
        "pe gat": "zone de flexie",
        "pe gât": "zone de flexie",
        "pe gatul": "zone de flexie",
        "pe gâtul": "zone de flexie",
        "in spatele genunchilor": "zone de flexie",
        "în spatele genunchilor": "zone de flexie",
        "in plica cotului": "zone de flexie",
        "în plica cotului": "zone de flexie",
        "in pliuri": "zone de flexie",
        "în pliuri": "zone de flexie",
        "leziuni pe zonele de flexie": "zone de flexie",
        "eczeme pe zone de flexie": "eczeme zone de flexie",

        # cardio
        "picioare umflate": "edeme gambiere",
        "nu poate sta intins": "dispnee la decubit",
        "nu poate sta întins": "dispnee la decubit",
        "se sufoca culcat": "dispnee la decubit",
        "se sufocă culcat": "dispnee la decubit",

        # typo fixes
        "amete li": "ameteli",
        "ameteli": "ameteli",
        "amețeli": "ameteli",
        "taba gic": "fumator",
    }


def normalize_text(text):
    if not text:
        return ""

    text = str(text).lower().strip()
    text = strip_diacritics(text)

    replacements = get_normalization_replacements()

    # cele mai lungi expresii se înlocuiesc primele
    for src in sorted(replacements.keys(), key=len, reverse=True):
        text = text.replace(strip_diacritics(src.lower()), replacements[src])

    text = re.sub(r"[^a-z0-9\s/+\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_text_tokens(text):
    norm_text = normalize_text(text)
    return set(norm_text.split()) if norm_text else set()


def similarity_ratio(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def fuzzy_phrase_in_text(norm_text, norm_phrase, threshold_phrase=0.88, threshold_token=0.9):
    if not norm_text or not norm_phrase:
        return False

    if norm_phrase in norm_text:
        return True

    text_tokens = norm_text.split()
    phrase_tokens = norm_phrase.split()

    if not text_tokens or not phrase_tokens:
        return False

    # 1 cuvânt
    if len(phrase_tokens) == 1:
        target = phrase_tokens[0]
        for token in text_tokens:
            if token == target:
                return True
            if similarity_ratio(token, target) >= threshold_token:
                return True
        return False

    # expresie cu mai multe cuvinte
    n = len(phrase_tokens)
    for i in range(len(text_tokens) - n + 1):
        window = " ".join(text_tokens[i:i + n])
        if window == norm_phrase:
            return True
        if similarity_ratio(window, norm_phrase) >= threshold_phrase:
            return True

    # fallback mai permisiv pentru expresii scurte
    compact_text = " ".join(text_tokens)
    if similarity_ratio(compact_text, norm_phrase) >= 0.93:
        return True

    return False


def contains_phrase(text, phrase):
    norm_text = normalize_text(text)
    norm_phrase = normalize_text(phrase)
    return fuzzy_phrase_in_text(norm_text, norm_phrase)


def contains_any(text, keywords):
    if not text or not keywords:
        return False

    norm_text = normalize_text(text)
    for kw in keywords:
        kw_norm = normalize_text(kw)
        if kw_norm and fuzzy_phrase_in_text(norm_text, kw_norm):
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
        if not kw_norm or kw_norm in seen:
            continue
        if fuzzy_phrase_in_text(norm_text, kw_norm):
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

        if fuzzy_phrase_in_text(norm_text, term):
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


def merge_weighted_terms(*weighted_lists):
    merged = {}

    for items in weighted_lists:
        if not items:
            continue
        for item in items:
            if isinstance(item, dict):
                term = normalize_text(item.get("term", ""))
                weight = item.get("weight", 1)
            else:
                term = normalize_text(item)
                weight = 1

            if not term:
                continue

            try:
                weight = int(weight)
            except Exception:
                weight = 1

            if term not in merged or weight > merged[term]:
                merged[term] = weight

    return [{"term": term, "weight": weight} for term, weight in merged.items()]


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
            {"term": "prurit", "weight": 5},
            {"term": "eczeme", "weight": 8},
            {"term": "eritem", "weight": 5},
            {"term": "eruptie", "weight": 2},
            {"term": "piele uscata", "weight": 7},
            {"term": "dermatita", "weight": 4},
            {"term": "zone de flexie", "weight": 8},
            {"term": "eczeme zone de flexie", "weight": 9},
            {"term": "atopie", "weight": 2},
            {"term": "mancarime", "weight": 3},
            {"term": "tegument", "weight": 1},
            {"term": "iritatie", "weight": 2},
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
            {"term": "colegi raciti", "weight": 5},
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
        "bpoc / bronsita cronica": [
            {"term": "fumator", "weight": 10},
            {"term": "tuse productiva", "weight": 9},
            {"term": "sputa", "weight": 8},
            {"term": "dispnee", "weight": 4},
            {"term": "simptome la efort", "weight": 4},
            {"term": "expunere la fum", "weight": 6},
        ],
        "insuficienta cardiaca": [
            {"term": "ortopnee", "weight": 12},
            {"term": "dispnee la decubit", "weight": 11},
            {"term": "edeme gambiere", "weight": 10},
            {"term": "dispnee", "weight": 3},
            {"term": "efort", "weight": 2},
            {"term": "varstnic", "weight": 2},
            {"term": "virstnic", "weight": 2},
        ],
        "dermatita de contact iritativa": [
            {"term": "detergent", "weight": 8},
            {"term": "substante chimice", "weight": 8},
            {"term": "eritem local", "weight": 9},
            {"term": "prurit", "weight": 3},
            {"term": "iritatie", "weight": 4},
        ],
        "sincopa vasovagala": [
            {"term": "colaps", "weight": 6},
            {"term": "ameteli", "weight": 3},
            {"term": "context emotional", "weight": 6},
            {"term": "lipotimie", "weight": 7},
        ],
        "intoleranta alimentara": [
            {"term": "balonare", "weight": 9},
            {"term": "dureri abdominale", "weight": 5},
            {"term": "lactate", "weight": 10},
            {"term": "intoleranta", "weight": 10},
            {"term": "dupa aliment", "weight": 3},
        ],
        "infectie respiratorie joasa": [
            {"term": "febra", "weight": 8},
            {"term": "sputa", "weight": 9},
            {"term": "tuse productiva", "weight": 9},
            {"term": "debut recent", "weight": 5},
            {"term": "infectie", "weight": 6},
            {"term": "bronsita", "weight": 8},
            {"term": "pneumonie", "weight": 10},
            {"term": "tuse", "weight": 2},
        ],
    }

    preset_weighted = presets.get(name_norm, [])
    return merge_weighted_terms(default_weighted, preset_weighted)


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
        if contains_any(text, ["febra", "odinofagie", "secretii nazale purulente", "stare generala alterata", "mialgii"]):
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
        if contains_any(text, ["context emotional"]) and not contains_any(
            text, ["urticarie", "angioedem", "hipotensiune", "stridor", "edem lingual"]
        ):
            bonus -= 12

    elif name_norm == "rinita virala / infectioasa":
        if contains_any(text, ["febra"]) and contains_any(text, ["odinofagie", "tuse", "stare generala alterata", "mialgii", "frison"]):
            bonus += 10
        if contains_any(text, ["contact infectios", "debut acut", "colegi raciti"]):
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

    elif name_norm == "bpoc / bronsita cronica":
        if contains_any(text, ["fumator", "tuse productiva"]) and contains_any(text, ["sputa", "dispnee"]):
            bonus += 10
        if contains_any(text, ["wheezing", "prurit nazal", "polen", "acarieni"]):
            bonus -= 6

    elif name_norm == "insuficienta cardiaca":
        if contains_any(text, ["ortopnee", "dispnee la decubit"]) or (
            contains_any(text, ["dispnee"]) and contains_any(text, ["edeme gambiere"])
        ):
            bonus += 12
        if contains_any(text, ["polen", "acarieni", "prurit nazal", "urticarie"]):
            bonus -= 5

    elif name_norm == "dermatita de contact iritativa":
        if contains_any(text, ["detergent", "substante chimice"]) and contains_any(text, ["eritem local", "prurit", "iritatie"]):
            bonus += 10
        if contains_any(text, ["angioedem", "urticarie generalizata", "dispnee"]):
            bonus -= 8

    elif name_norm == "sincopa vasovagala":
        if contains_any(text, ["context emotional", "stres"]) and contains_any(text, ["colaps", "ameteli", "lipotimie"]):
            bonus += 10
        if contains_any(text, ["urticarie", "angioedem", "stridor"]):
            bonus -= 10

    elif name_norm == "intoleranta alimentara":
        if contains_any(text, ["balonare", "lactate"]) and contains_any(text, ["dureri abdominale", "dupa aliment"]):
            bonus += 10
        if contains_any(text, ["urticarie", "edem buze", "prurit oral", "angioedem"]):
            bonus -= 10

    elif name_norm == "infectie respiratorie joasa":
        if contains_any(text, ["febra", "sputa", "tuse productiva"]):
            bonus += 10
        if contains_any(text, ["bronsita", "pneumonie"]):
            bonus += 8
        if contains_any(text, ["polen", "acarieni", "prurit nazal"]):
            bonus -= 6

    return bonus


def compute_exclusion_penalty(text, exclude_keywords):
    if not exclude_keywords:
        return 0

    penalty = 0
    norm_text = normalize_text(text)
    for kw in exclude_keywords:
        kw_norm = normalize_text(kw)
        if kw_norm and fuzzy_phrase_in_text(norm_text, kw_norm):
            penalty += 5

    return penalty


def compute_contradiction_penalty(text, contradiction_terms):
    if not contradiction_terms:
        return 0

    penalty = 0
    norm_text = normalize_text(text)

    for kw in contradiction_terms:
        kw_norm = normalize_text(kw)
        if kw_norm and fuzzy_phrase_in_text(norm_text, kw_norm):
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


def compute_required_feature_penalty(name, text):
    name_norm = normalize_text(name)
    norm_text = normalize_text(text)

    if name_norm == "rinita alergica":
        if not contains_any(norm_text, ["prurit nazal", "prurit ocular", "stranut", "lacrimare", "polen", "acarieni", "rinoree apoasa"]):
            return 18

    elif name_norm == "astm alergic":
        if not contains_any(norm_text, ["wheezing", "tuse nocturna", "constrictie toracica", "agravare la alergeni"]):
            return 20

    elif name_norm == "anafilaxie":
        if not contains_any(norm_text, ["hipotensiune", "colaps", "stridor", "edem lingual", "urticarie", "angioedem", "dispnee severa"]):
            return 22

    elif name_norm == "alergie alimentara":
        if not contains_any(norm_text, ["dupa aliment", "prurit oral", "urticarie", "edem buze", "angioedem", "wheezing dupa aliment"]):
            return 18

    elif name_norm == "dermatita atopica":
        # mai permisivă decât înainte
        if not contains_any(norm_text, ["prurit", "eczeme", "piele uscata", "eritem", "dermatita", "zone de flexie", "iritatie", "tegument"]):
            return 8

    elif name_norm == "urticarie alergica / angioedem":
        if not contains_any(norm_text, ["urticarie", "angioedem", "edem buze", "edem pleoape", "eruptie fugace"]):
            return 18

    elif name_norm == "atac de panica / hiperventilatie":
        if not contains_any(norm_text, ["hiperventilatie", "palpitatii", "parestezii", "teama intensa", "senzatie de moarte iminenta", "context emotional"]):
            return 14

    elif name_norm == "bpoc / bronsita cronica":
        if not contains_any(norm_text, ["fumator", "tuse productiva", "sputa"]):
            return 18

    elif name_norm == "insuficienta cardiaca":
        if not contains_any(norm_text, ["ortopnee", "dispnee la decubit", "edeme gambiere"]):
            return 18

    elif name_norm == "dermatita de contact iritativa":
        if not contains_any(norm_text, ["detergent", "substante chimice", "eritem local", "iritatie"]):
            return 14

    elif name_norm == "sincopa vasovagala":
        if not contains_any(norm_text, ["colaps", "context emotional", "stres", "lipotimie"]):
            return 14

    elif name_norm == "intoleranta alimentara":
        if not contains_any(norm_text, ["balonare", "lactate", "dureri abdominale"]):
            return 14

    elif name_norm == "infectie respiratorie joasa":
        if not contains_any(norm_text, ["febra", "sputa", "tuse productiva", "bronsita", "pneumonie"]):
            return 18

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
        "secretii nazale purulente",
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
        if contains_any(norm_text, panic_markers) and not contains_any(norm_text, ["wheezing", "tuse nocturna"]):
            score -= 12
        if contains_any(norm_text, ["febra", "sputa", "tuse productiva", "fumator", "ortopnee"]) and not contains_any(norm_text, ["wheezing"]):
            score -= 12

    elif name_norm == "rinita alergica":
        if count_keyword_hits(norm_text, ["stranut", "rinoree", "prurit nazal", "prurit ocular", "lacrimare"]) >= 2:
            score += 5
        if contains_any(norm_text, ["stranut in salve", "rinoree apoasa"]):
            score += 4
        if contains_any(norm_text, infectious_markers):
            score -= 9

    elif name_norm == "rinita virala / infectioasa":
        if count_keyword_hits(norm_text, ["febra", "odinofagie", "stare generala alterata", "mialgii", "frison"]) >= 2:
            score += 7
        if contains_any(norm_text, ["contact infectios", "debut acut", "colegi raciti"]):
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
        elif count_keyword_hits(norm_text, ["dispnee", "urticarie", "angioedem", "ameteli"]) >= 2 and contains_any(
            norm_text, ["dupa aliment", "dupa intepatura", "dupa medicament"]
        ):
            score = max(score, 16)
        elif contains_any(norm_text, ["context emotional"]) and not contains_any(
            norm_text, ["urticarie", "angioedem", "hipotensiune", "stridor", "edem lingual"]
        ):
            score -= 14
        elif not contains_any(norm_text, ["dispnee", "stridor", "hipotensiune", "colaps", "angioedem", "urticarie"]):
            score -= 8

    elif name_norm == "alergie alimentara":
        if contains_any(norm_text, ["dupa aliment"]):
            score += 6
        else:
            score -= 5
        if contains_any(norm_text, ["balonare", "lactate"]) and not contains_any(
            norm_text, ["urticarie", "edem buze", "angioedem", "prurit oral", "wheezing dupa aliment"]
        ):
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
        if contains_any(norm_text, ["wheezing", "tuse nocturna", "agravare la alergeni", "urticarie", "angioedem", "hipotensiune", "stridor"]):
            score -= 12

    elif name_norm == "bpoc / bronsita cronica":
        if contains_any(norm_text, ["fumator", "tuse productiva", "sputa"]):
            score += 8
        if contains_any(norm_text, ["wheezing", "prurit nazal", "polen", "acarieni"]) and not contains_any(
            norm_text, ["fumator", "tuse productiva", "sputa"]
        ):
            score -= 8

    elif name_norm == "insuficienta cardiaca":
        if contains_any(norm_text, ["ortopnee", "dispnee la decubit", "edeme gambiere"]):
            score += 10
        if contains_any(norm_text, ["polen", "acarieni", "prurit nazal", "wheezing"]):
            score -= 6

    elif name_norm == "dermatita de contact iritativa":
        if contains_any(norm_text, ["detergent", "substante chimice", "eritem local"]):
            score += 8
        if contains_any(norm_text, ["angioedem", "urticarie generalizata", "dispnee", "hipotensiune"]):
            score -= 10

    elif name_norm == "sincopa vasovagala":
        if contains_any(norm_text, ["context emotional", "stres"]) and contains_any(norm_text, ["colaps", "ameteli", "lipotimie"]):
            score += 8
        if contains_any(norm_text, ["urticarie", "angioedem", "stridor", "edem lingual"]):
            score -= 12

    elif name_norm == "intoleranta alimentara":
        if contains_any(norm_text, ["balonare", "lactate", "dureri abdominale"]):
            score += 8
        if contains_any(norm_text, ["urticarie", "edem buze", "prurit oral", "wheezing", "angioedem"]):
            score -= 12

    elif name_norm == "infectie respiratorie joasa":
        if contains_any(norm_text, ["febra", "sputa", "tuse productiva"]):
            score += 8
        if contains_any(norm_text, ["pneumonie", "bronsita"]):
            score += 8
        if contains_any(norm_text, ["wheezing", "polen", "acarieni"]) and not contains_any(norm_text, ["febra", "sputa", "tuse productiva"]):
            score -= 6

    elif name_norm == "dermatita atopica":
        # ajută când sunt descrieri vagi, dar cutanate
        if contains_any(norm_text, ["eritem", "tegument", "prurit", "iritatie", "piele uscata"]):
            score += 4
        if contains_any(norm_text, ["febra", "hipotensiune", "dispnee severa"]) and not contains_any(norm_text, ["prurit", "piele uscata", "eczeme"]):
            score -= 6

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
    required_feature_penalty = compute_required_feature_penalty(name, text)

    raw_score = (
        base_score
        + pattern_bonus
        + minimum_adjustment
        + high_value_bonus
        - exclude_penalty
        - contradiction_penalty
        - required_feature_penalty
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
        "primary_diagnosis": "Diagnostic neclar",
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

    elif primary_name == "dermatita atopica":
        output["notes"] = output["notes"] + [
            "Leziunile cutanate descrise vag necesită corelare cu distribuția, pruritul și istoricul de atopie."
        ]

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
            "primary_diagnosis": "Diagnostic neclar",
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

    if not positive_ranked:
        ranked_display = ranked_all[:5]
        for item in ranked_display:
            item.pop("has_any_match", None)
        return ranked_display, build_fallback_analysis(text)

    primary = positive_ranked[0]

    if primary["score"] < 6:
        ranked_display = ranked_all[:5]
        for item in ranked_display:
            item.pop("has_any_match", None)
        return ranked_display, build_fallback_analysis(text)

    ranked_display = [primary]

    for item in positive_ranked[1:]:
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