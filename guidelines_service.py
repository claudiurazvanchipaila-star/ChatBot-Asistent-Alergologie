import re
from typing import List, Dict

import requests
from bs4 import BeautifulSoup


EAACI_GUIDELINES_URL = "https://eaaci.org/science/guidelines-position-papers/"
GINA_SUMMARY_GUIDE_URL = "https://ginasthma.org/2025-gina-summary-guide/"
GINA_HOME_URL = "https://ginasthma.org/"


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AllergyClinicalAssistant/1.0)"
}


def normalize_text(text: str) -> str:
    return (text or "").strip().lower()


def contains_any(text: str, terms: List[str]) -> bool:
    text = normalize_text(text)
    return any(term in text for term in terms)


def fetch_page(url: str, timeout: int = 15) -> str:
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception:
        return ""


def extract_text_from_html(html: str) -> str:
    if not html:
        return ""

    try:
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text)
        return text
    except Exception:
        return ""


def infer_topic_terms(diagnosis_name: str, symptoms: str, context: str, extra: str) -> List[str]:
    joined = normalize_text(f"{diagnosis_name} {symptoms} {context} {extra}")

    topic_terms = []

    if contains_any(joined, ["rinit", "rinoree", "strănut", "prurit nazal", "nas înfundat", "conjunctivit", "ochi roșii", "lăcrimare"]):
        topic_terms.extend(["rhinitis", "rhinoconjunctivitis", "allergic rhinitis", "conjunctivitis"])

    if contains_any(joined, ["astm", "wheezing", "șuierături", "dispnee", "tuse nocturnă", "constricție toracică"]):
        topic_terms.extend(["asthma", "inhaled corticosteroid", "formoterol", "reliever", "controller"])

    if contains_any(joined, ["aliment", "după masă", "prurit oral", "prurit faringian", "vărsături", "diaree"]):
        topic_terms.extend(["food allergy", "ige-mediated food allergy", "adrenaline", "auto-injector"])

    if contains_any(joined, ["urticarie", "angioedem", "edem buze", "edem pleoape"]):
        topic_terms.extend(["urticaria", "angioedema", "antihistamine"])

    if contains_any(joined, ["anafilaxie", "șoc", "hipotensiune", "edem lingual", "stridor"]):
        topic_terms.extend(["anaphylaxis", "adrenaline", "emergency"])

    if contains_any(joined, ["dermatită", "eczeme", "prurit cutanat", "piele uscată"]):
        topic_terms.extend(["atopic dermatitis", "eczema", "emollient", "topical corticosteroid"])

    return list(dict.fromkeys(topic_terms))


def summarize_eaaci_guidelines(diagnosis_name: str, symptoms: str, context: str, extra: str) -> List[Dict]:
    html = fetch_page(EAACI_GUIDELINES_URL)
    text = extract_text_from_html(html)

    if not text:
        return []

    topic_terms = infer_topic_terms(diagnosis_name, symptoms, context, extra)
    text_lower = text.lower()
    results = []

    if any(term in text_lower for term in topic_terms):
        if any(term in text_lower for term in ["food allergy", "ige-mediated food allergy"]):
            results.append({
                "source": "EAACI",
                "title": "Guidelines & Position Papers / Food Allergy",
                "year": "actualizat pe site-ul oficial",
                "summary": (
                    "EAACI publică ghiduri și position papers oficiale; pentru alergia alimentară IgE-mediată, accentul este pe "
                    "confirmarea diagnosticului, evitare alergenică, plan scris de tratament, educație privind recunoașterea simptomelor "
                    "și utilizarea adrenalinei când este indicată."
                )
            })

        if any(term in text_lower for term in ["rhinitis", "rhinoconjunctivitis", "allergic rhinitis"]):
            results.append({
                "source": "EAACI",
                "title": "Guidelines & Position Papers / Allergic Rhinoconjunctivitis",
                "year": "actualizat pe site-ul oficial",
                "summary": (
                    "EAACI are resurse oficiale pentru rinoconjunctivita alergică; răspunsul clinic trebuie corelat cu triggerii, "
                    "controlul expunerii, terapia simptomatică și selecția atentă a cazurilor pentru imunoterapie alergen-specifică."
                )
            })

        if any(term in text_lower for term in ["anaphylaxis", "adrenaline", "emergency"]):
            results.append({
                "source": "EAACI",
                "title": "Guidelines & Position Papers / Anaphylaxis-related guidance",
                "year": "actualizat pe site-ul oficial",
                "summary": (
                    "Pentru reacțiile sistemice severe, abordarea trebuie să rămână una de urgență, cu recunoașterea rapidă a anafilaxiei, "
                    "plan terapeutic scris și instruirea pacientului privind managementul episoadelor viitoare."
                )
            })

    if not results:
        results.append({
            "source": "EAACI",
            "title": "Guidelines & Position Papers",
            "year": "actualizat pe site-ul oficial",
            "summary": (
                "EAACI pune la dispoziție o secțiune oficială de ghiduri și position papers care poate fi folosită ca referință "
                "pentru alergologie, astm și imunologie clinică."
            )
        })

    return results[:3]


def summarize_gina_guidelines(diagnosis_name: str, symptoms: str, context: str, extra: str) -> List[Dict]:
    joined = normalize_text(f"{diagnosis_name} {symptoms} {context} {extra}")

    if not contains_any(joined, ["astm", "wheezing", "șuierături", "dispnee", "tuse nocturnă", "constricție toracică"]):
        return []

    html = fetch_page(GINA_SUMMARY_GUIDE_URL)
    text = extract_text_from_html(html)

    if not text:
        home_html = fetch_page(GINA_HOME_URL)
        home_text = extract_text_from_html(home_html)

        if not home_text:
            return []

        return [{
            "source": "GINA",
            "title": "GINA official website",
            "year": "2025",
            "summary": (
                "GINA menține resurse oficiale actualizate pentru managementul astmului. Pentru interpretarea clinică, "
                "schema terapeutică trebuie aleasă în funcție de treapta de tratament, vârstă și controlul simptomelor."
            )
        }]

    results = []

    if contains_any(text, ["ics-formoterol", "summary guide", "step", "maintenance", "reliever"]):
        results.append({
            "source": "GINA",
            "title": "2025 GINA Summary Guide",
            "year": "2025",
            "summary": (
                "GINA 2025 rezumă managementul astmului pe trepte terapeutice și subliniază alegerea tratamentului în funcție de "
                "vârstă, controlul simptomelor, reliever și controller, cu evaluare periodică a răspunsului clinic."
            )
        })

    if contains_any(text, ["6–11 years", "6-11", "children"]):
        results.append({
            "source": "GINA",
            "title": "2025 GINA Summary Guide / children 6–11 years",
            "year": "2025",
            "summary": (
                "Pentru copilul școlar, recomandările GINA trebuie interpretate pe grupe de vârstă și dispozitive disponibile local; "
                "alegerea reliever/controller nu trebuie automatizată exclusiv după simptom."
            )
        })

    if contains_any(text, ["step 5", "severe asthma", "expert assessment"]):
        results.append({
            "source": "GINA",
            "title": "2025 GINA Summary Guide / severe asthma",
            "year": "2025",
            "summary": (
                "În suspiciunea de astm sever sau control insuficient, GINA recomandă evaluare de specialitate, fenotipare și "
                "reconsiderarea treptei terapeutice, nu doar creșterea empirică a dozelor."
            )
        })

    return results[:3]


def get_guideline_recommendations(
    diagnosis_name: str = "",
    symptoms: str = "",
    context: str = "",
    extra: str = "",
    age=None,
    weight=None,
    severity: str = ""
) -> List[Dict]:
    results = []

    results.extend(summarize_eaaci_guidelines(diagnosis_name, symptoms, context, extra))
    results.extend(summarize_gina_guidelines(diagnosis_name, symptoms, context, extra))

    seen = set()
    deduped = []

    for item in results:
        key = (item.get("source", ""), item.get("title", ""), item.get("summary", ""))
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    return deduped[:5]