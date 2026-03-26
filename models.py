import json

def load_diagnoses(path="data/diagnoses.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_romanian_knowledge(path="data/allergy_knowledge_ro.json"):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {item["name"].lower(): item for item in data}


def score_to_probability(score):
    if score >= 6:
        return "mare"
    if score >= 3:
        return "moderată"
    return "redusă"


def classify_severity(text):
    text = text.lower()

    severe = [
        "dispnee severă", "hipotensiune", "șoc", "edem lingual",
        "angioedem", "stridor", "voce răgușită", "dificultăți la înghițire"
    ]
    moderate = ["wheezing", "dispnee", "tuse nocturnă", "șuierături", "edem buze"]

    if any(x in text for x in severe):
        return "severă"
    if any(x in text for x in moderate):
        return "moderată"
    return "ușoară"


def normalize_text(text):
    text = text.lower()

    replacements = {
        "stranut": "strănut",
        "lacrimare": "lăcrimare",
        "mancarime nazala": "prurit nazal",
        "mancarime oculara": "prurit ocular",
        "mancarime la ochi": "prurit ocular",
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
        "dificultati la inghitire": "dificultăți la înghițire"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


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
        "confidence": "scăzută"
    }

    if ranked:
        output["primary_diagnosis"] = ranked[0]["name"]
        output["primary_probability"] = ranked[0]["probability"]

    if len(ranked) >= 2:
        diff = ranked[0]["score"] - ranked[1]["score"]
        output["confidence"] = "mare" if diff >= 2 else "moderată"
    elif len(ranked) == 1:
        output["confidence"] = "moderată"

    if len(ranked) > 1:
        top_names = [x["name"].lower() for x in ranked[:2]]

        if any("rinit" in x for x in top_names) and any("astm" in x for x in top_names):
            output["associated_diagnosis"] = "Asociere probabilă rinită alergică + astm alergic"

        if any("rinit" in x for x in top_names) and any("conjunctivit" in x for x in top_names):
            if not output["associated_diagnosis"]:
                output["associated_diagnosis"] = "Asociere probabilă rinită alergică + conjunctivită alergică"

    output["alternatives"] = [x["name"] for x in ranked[1:4]]

    if any(x in text for x in ["strănut", "rinoree", "prurit nazal", "lăcrimare", "prurit ocular", "ochi roșii"]):
        output["supports"].append("Simptomatologia nazală și/sau oculară susține o afectare alergică de căi aeriene superioare.")

    if any(x in text for x in ["wheezing", "dispnee", "tuse", "tuse nocturnă", "șuierături"]):
        output["supports"].append("Prezența wheezing-ului sau a simptomelor respiratorii inferioare ridică suspiciunea de astm alergic asociat.")

    if any(x in text for x in ["polen", "sezon", "sezoniere", "acarieni"]):
        output["supports"].append("Caracterul sezonier sau expunerea la alergeni inhalatori susține o cauză alergică respiratorie.")

    if any(x in text for x in ["eczeme", "piele", "leziuni", "prurit cutanat", "dermatită"]):
        output["supports"].append("Manifestările cutanate sugerează teren atopic și necesită diferențiere dermatologică/alergologică.")

    if any(x in text for x in ["după masă", "aliment", "prurit oral", "edem buze", "vărsături"]):
        output["supports"].append("Asocierea simptomelor cu ingestia alimentară susține suspiciunea de alergie alimentară.")

    if not any(x in text for x in ["febră", "frison", "durere toracică intensă", "hemoptizie"]):
        output["limits"].append("Lipsa semnelor infecțioase sau a simptomelor de alarmă susține o cauză non-infecțioasă.")
    else:
        output["limits"].append("Prezența unor simptome atipice pentru alergie impune excluderea altor cauze non-alergice.")

    if any(x in text for x in ["dispnee severă", "hipotensiune", "șoc", "edem lingual", "angioedem", "stridor", "voce răgușită", "dificultăți la înghițire"]):
        output["red_flags"].append("Semne de reacție alergică severă / anafilaxie posibilă — necesită evaluare medicală de urgență.")

    if any(x in text for x in ["febră", "hemoptizie", "durere toracică intensă"]):
        output["red_flags"].append("Prezența unor simptome atipice pentru alergie impune excluderea altor cauze non-alergice.")

    output["notes"].append("Rezultatul este orientativ și trebuie corelat cu anamneza completă, examenul clinic și investigațiile paraclinice.")

    return output


def rank_differential_diagnoses(symptoms_text, diagnoses):
    symptoms_text = normalize_text(symptoms_text)
    ranked = []

    strong_terms = {
        "wheezing", "dispnee", "stridor", "hipotensiune",
        "edem lingual", "șoc", "șoc anafilactic", "angioedem",
        "urticarie", "edem buze", "edem pleoape", "prurit oral"
    }

    medium_terms = {
        "șuierături", "tuse nocturnă", "prurit nazal", "prurit ocular",
        "lăcrimare", "ochi roșii", "rinoree", "strănut",
        "vărsături", "dureri abdominale", "diaree"
    }

    for diagnosis in diagnoses:
        score = 0
        matched_keywords = []

        for keyword in diagnosis["keywords"]:
            keyword_lower = normalize_text(keyword.lower())

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
                "dificultăți la înghițire"
            ]
            if any(s in symptoms_text for s in severe_signs):
                score += 4
            else:
                score = 0

        if "alergie alimentară" in name:
            if any(x in symptoms_text for x in ["după masă", "aliment", "reacție după aliment"]):
                score += 2

        if "conjunctivit" in name:
            if any(s in symptoms_text for s in ["lăcrimare", "prurit ocular", "ochi roșii"]):
                score += 2

        if "rinit" in name:
            if any(s in symptoms_text for s in ["strănut", "rinoree", "prurit nazal", "nas înfundat"]):
                score += 2

        if "astm" in name:
            if any(s in symptoms_text for s in ["wheezing", "dispnee", "șuierături", "tuse nocturnă"]):
                score += 3
            else:
                score = max(score - 1, 0)

        if "dermatită" in name:
            skin_signs = ["eczeme", "piele", "leziuni", "prurit cutanat", "dermatită"]
            if not any(s in symptoms_text for s in skin_signs):
                score = max(score - 2, 0)

        if "urticarie" in name or "angioedem" in name:
            if any(s in symptoms_text for s in ["urticarie", "papule", "plăci pruriginoase", "angioedem", "edem buze", "edem pleoape"]):
                score += 2

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


def get_treatment_details(diagnosis_name, knowledge_ro=None):
    name = diagnosis_name.lower()

    if knowledge_ro and name in knowledge_ro:
        item = knowledge_ro[name]
        return {
            "diagnosis": item["name"],
            "clinical_picture": item.get("clinical_picture", []),
            "treatment": item.get("treatment", []),
            "prevention": item.get("prevention", []),
            "allergen_avoidance": item.get("allergen_avoidance", [])
        }

    return {
        "diagnosis": diagnosis_name,
        "clinical_picture": [],
        "treatment": ["Tratamentul trebuie individualizat în funcție de contextul clinic."],
        "prevention": ["Prevenția depinde de cauza exactă și de factorii declanșatori."],
        "allergen_avoidance": ["Evitarea alergenului se recomandă doar după corelare clinică și identificare corectă."]
    }