import re
from typing import List, Dict

import requests
from bs4 import BeautifulSoup


EAACI_GUIDELINES_URL = "https://eaaci.org/science/guidelines-position-papers/"
GINA_HOME_URL = "https://ginasthma.org/"
ARIA_INFO_URL = "https://www.whiar.org/"


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AllergyClinicalAssistant/1.0)"
}


def normalize_text(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def contains_any(text: str, terms: List[str]) -> bool:
    normalized = normalize_text(text)
    return any(normalize_text(term) in normalized for term in terms if term)


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


def split_sentences(text: str) -> List[str]:
    if not text:
        return []

    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[\.\!\?])\s+", text)
    cleaned = []

    for part in parts:
        sentence = part.strip()
        if len(sentence) >= 40:
            cleaned.append(sentence)

    return cleaned


def infer_topic_profile(
    diagnosis_name: str,
    symptoms: str,
    context: str,
    triggers: str,
    extra: str,
    query: str = ""
) -> Dict:
    joined = normalize_text(f"{diagnosis_name} {symptoms} {context} {triggers} {extra} {query}")

    profile = {
        "rhinitis": False,
        "conjunctivitis": False,
        "asthma": False,
        "food_allergy": False,
        "urticaria_angioedema": False,
        "anaphylaxis": False,
        "atopic_dermatitis": False
    }

    if contains_any(joined, [
        "rinit", "rinoree", "stranut", "strănut", "prurit nazal", "nas infundat",
        "nas înfundat", "congestie nazala", "congestie nazală", "rhin", "rhinoconj"
    ]):
        profile["rhinitis"] = True

    if contains_any(joined, [
        "conjunctivit", "ochi rosii", "ochi roșii", "lacrimare", "prurit ocular",
        "mancarime la ochi", "mâncărime la ochi", "edem palpebral"
    ]):
        profile["conjunctivitis"] = True

    if contains_any(joined, [
        "astm", "wheezing", "suieraturi", "șuierături", "dispnee", "tuse nocturna",
        "tuse nocturnă", "constrictie toracica", "constricție toracică",
        "respiratie grea", "respirație grea", "asthma"
    ]):
        profile["asthma"] = True

    if contains_any(joined, [
        "aliment", "dupa masa", "după masă", "prurit oral", "furnicaturi orale",
        "furnicături orale", "varsaturi", "vărsături", "diaree", "food allergy"
    ]):
        profile["food_allergy"] = True

    if contains_any(joined, [
        "urticarie", "angioedem", "edem buze", "edem pleoape"
    ]):
        profile["urticaria_angioedema"] = True

    if contains_any(joined, [
        "anafilaxie", "soc", "șoc", "hipotensiune", "edem lingual",
        "stridor", "colaps", "anaphylaxis"
    ]):
        profile["anaphylaxis"] = True

    if contains_any(joined, [
        "dermatita", "dermatită", "eczeme", "prurit cutanat", "piele uscata",
        "piele uscată", "atopic dermatitis", "eczema"
    ]):
        profile["atopic_dermatitis"] = True

    return profile


def extract_relevant_sentences(text: str, keywords: List[str], limit: int = 2) -> List[str]:
    if not text:
        return []

    sentences = split_sentences(text)
    results = []

    for sentence in sentences:
        normalized_sentence = normalize_text(sentence)
        if any(normalize_text(keyword) in normalized_sentence for keyword in keywords):
            results.append(sentence)

    deduped = []
    seen = set()

    for sentence in results:
        key = normalize_text(sentence)
        if key not in seen:
            seen.add(key)
            deduped.append(sentence)

    return deduped[:limit]


def make_card(source: str, title: str, excerpt: str, recommendation: str, url: str) -> Dict:
    return {
        "source": source,
        "title": title,
        "excerpt": excerpt,
        "recommendation": recommendation,
        "url": url
    }


def summarize_eaaci_guidelines(
    diagnosis_name: str,
    symptoms: str,
    context: str,
    triggers: str,
    extra: str,
    query: str = ""
) -> List[Dict]:
    html = fetch_page(EAACI_GUIDELINES_URL)
    text = extract_text_from_html(html)

    profile = infer_topic_profile(diagnosis_name, symptoms, context, triggers, extra, query)
    results = []

    if not text:
        text = ""

    if profile["rhinitis"] or profile["conjunctivitis"]:
        excerpt_candidates = extract_relevant_sentences(
            text,
            ["rhinitis", "rhinoconjunctivitis", "allergic rhinitis", "conjunctivitis"],
            limit=2
        )
        excerpt = " ".join(excerpt_candidates) if excerpt_candidates else (
            "Secțiunea EAACI de ghiduri și position papers include resurse relevante pentru rinoconjunctivita alergică și evaluarea clinică orientată pe triggeri, controlul expunerii și management individualizat."
        )

        results.append(make_card(
            source="EAACI",
            title="Guidelines & Position Papers / Allergic Rhinitis and Rhinoconjunctivitis",
            excerpt=excerpt,
            recommendation=(
                "Corelează simptomele nazale și oculare cu sezonalitatea, expunerea la alergeni și contextul clinic; evaluarea alergologică și conduita terapeutică trebuie individualizate."
            ),
            url=EAACI_GUIDELINES_URL
        ))

    if profile["food_allergy"]:
        excerpt_candidates = extract_relevant_sentences(
            text,
            ["food allergy", "ige-mediated", "allergy", "anaphylaxis"],
            limit=2
        )
        excerpt = " ".join(excerpt_candidates) if excerpt_candidates else (
            "EAACI publică resurse oficiale relevante pentru alergia alimentară, cu accent pe confirmarea diagnosticului, evitarea expunerii, educația pacientului și planul de acțiune pentru reacții severe."
        )

        results.append(make_card(
            source="EAACI",
            title="Guidelines & Position Papers / Food Allergy",
            excerpt=excerpt,
            recommendation=(
                "Pentru suspiciunea de alergie alimentară, sunt importante corelarea temporală cu ingestia, evitarea alimentului suspect până la clarificare și planul de siguranță în caz de reacții severe."
            ),
            url=EAACI_GUIDELINES_URL
        ))

    if profile["urticaria_angioedema"]:
        excerpt_candidates = extract_relevant_sentences(
            text,
            ["urticaria", "angioedema", "allergy"],
            limit=2
        )
        excerpt = " ".join(excerpt_candidates) if excerpt_candidates else (
            "Resursele EAACI pot fi utile pentru diferențierea urticariei și angioedemului, evaluarea triggerilor și orientarea managementului în funcție de severitate."
        )

        results.append(make_card(
            source="EAACI",
            title="Guidelines & Position Papers / Urticaria and Angioedema",
            excerpt=excerpt,
            recommendation=(
                "Diferențiază leziunile cutanate fugace de alte erupții și evaluează rapid eventualele semne de afectare respiratorie sau sistemică."
            ),
            url=EAACI_GUIDELINES_URL
        ))

    if profile["anaphylaxis"]:
        excerpt_candidates = extract_relevant_sentences(
            text,
            ["anaphylaxis", "emergency", "adrenaline"],
            limit=2
        )
        excerpt = " ".join(excerpt_candidates) if excerpt_candidates else (
            "EAACI include resurse relevante pentru recunoașterea și managementul anafilaxiei, subliniind importanța identificării rapide a reacțiilor severe și a planului de acțiune."
        )

        results.append(make_card(
            source="EAACI",
            title="Guidelines & Position Papers / Anaphylaxis",
            excerpt=excerpt,
            recommendation=(
                "Orice suspiciune de anafilaxie trebuie tratată ca urgență; după stabilizare, este importantă clarificarea cauzei și educația privind prevenirea recurenței."
            ),
            url=EAACI_GUIDELINES_URL
        ))

    if profile["atopic_dermatitis"]:
        excerpt_candidates = extract_relevant_sentences(
            text,
            ["atopic dermatitis", "eczema", "skin", "allergy"],
            limit=2
        )
        excerpt = " ".join(excerpt_candidates) if excerpt_candidates else (
            "Resursele EAACI pot susține orientarea clinică în dermatita atopică, în special prin integrarea contextului atopic, a barierei cutanate și a factorilor agravanți."
        )

        results.append(make_card(
            source="EAACI",
            title="Guidelines & Position Papers / Atopic Dermatitis",
            excerpt=excerpt,
            recommendation=(
                "În dermatita atopică, evaluarea trebuie să includă severitatea, impactul funcțional, rutina de îngrijire cutanată și eventualii factori agravanți."
            ),
            url=EAACI_GUIDELINES_URL
        ))

    if not results:
        results.append(make_card(
            source="EAACI",
            title="Guidelines & Position Papers",
            excerpt=(
                "EAACI pune la dispoziție o secțiune oficială de ghiduri și position papers relevante pentru alergologie și imunologie clinică."
            ),
            recommendation=(
                "Folosește secțiunea EAACI ca punct de orientare pentru corelarea tabloului clinic cu ghidurile de specialitate."
            ),
            url=EAACI_GUIDELINES_URL
        ))

    return results[:3]


def summarize_gina_guidelines(
    diagnosis_name: str,
    symptoms: str,
    context: str,
    triggers: str,
    extra: str,
    query: str = ""
) -> List[Dict]:
    profile = infer_topic_profile(diagnosis_name, symptoms, context, triggers, extra, query)

    if not profile["asthma"]:
        return []

    html = fetch_page(GINA_HOME_URL)
    text = extract_text_from_html(html)

    if not text:
        text = ""

    results = []

    excerpt_general = " ".join(
        extract_relevant_sentences(
            text,
            ["asthma", "guide", "management", "treatment"],
            limit=2
        )
    )

    if not excerpt_general:
        excerpt_general = (
            "GINA oferă resurse oficiale pentru managementul astmului, cu accent pe alegerea tratamentului în funcție de controlul simptomelor, severitate și reevaluare periodică."
        )

    results.append(make_card(
        source="GINA",
        title="Global Initiative for Asthma / General asthma guidance",
        excerpt=excerpt_general,
        recommendation=(
            "Interpretarea terapeutică trebuie făcută în funcție de controlul simptomelor, istoricul exacerbărilor, vârstă și tehnica inhalatorie."
        ),
        url=GINA_HOME_URL
    ))

    excerpt_step = " ".join(
        extract_relevant_sentences(
            text,
            ["step", "controller", "reliever", "inhaled corticosteroid", "ics"],
            limit=2
        )
    )

    if excerpt_step:
        results.append(make_card(
            source="GINA",
            title="Global Initiative for Asthma / Stepwise treatment approach",
            excerpt=excerpt_step,
            recommendation=(
                "Schema de tratament pentru astm nu trebuie automatizată doar după simptom; este necesară integrarea treptei terapeutice și a răspunsului clinic."
            ),
            url=GINA_HOME_URL
        ))

    excerpt_severe = " ".join(
        extract_relevant_sentences(
            text,
            ["severe asthma", "specialist", "expert", "phenotype"],
            limit=2
        )
    )

    if excerpt_severe:
        results.append(make_card(
            source="GINA",
            title="Global Initiative for Asthma / Severe or difficult-to-control asthma",
            excerpt=excerpt_severe,
            recommendation=(
                "Dacă există control insuficient sau suspiciune de astm sever, este necesară reevaluarea diagnosticului, aderenței, tehnicii inhalatorii și a indicației de evaluare de specialitate."
            ),
            url=GINA_HOME_URL
        ))

    return results[:3]


def summarize_aria_guidelines(
    diagnosis_name: str,
    symptoms: str,
    context: str,
    triggers: str,
    extra: str,
    query: str = ""
) -> List[Dict]:
    profile = infer_topic_profile(diagnosis_name, symptoms, context, triggers, extra, query)

    if not (profile["rhinitis"] or profile["conjunctivitis"]):
        return []

    html = fetch_page(ARIA_INFO_URL)
    text = extract_text_from_html(html)

    if not text:
        text = ""

    excerpt = " ".join(
        extract_relevant_sentences(
            text,
            ["rhinitis", "allergic rhinitis", "asthma", "control"],
            limit=2
        )
    )

    if not excerpt:
        excerpt = (
            "ARIA oferă resurse orientative pentru rinita alergică și relația acesteia cu astmul, subliniind importanța controlului simptomelor și a evaluării expunerii la alergeni."
        )

    return [
        make_card(
            source="ARIA",
            title="Allergic Rhinitis and its Impact on Asthma",
            excerpt=excerpt,
            recommendation=(
                "În rinita alergică, sunt importante evaluarea controlului simptomelor, reducerea expunerii la alergeni și alegerea tratamentului în funcție de severitate și persistență."
            ),
            url=ARIA_INFO_URL
        )
    ]


def get_guideline_recommendations(
    diagnosis_name: str = "",
    symptoms: str = "",
    context: str = "",
    triggers: str = "",
    extra: str = "",
    age=None,
    weight=None,
    severity: str = "",
    query: str = ""
) -> List[Dict]:
    results = []

    results.extend(summarize_eaaci_guidelines(diagnosis_name, symptoms, context, triggers, extra, query))
    results.extend(summarize_gina_guidelines(diagnosis_name, symptoms, context, triggers, extra, query))
    results.extend(summarize_aria_guidelines(diagnosis_name, symptoms, context, triggers, extra, query))

    severity_norm = normalize_text(severity)

    if contains_any(severity_norm, ["sever", "severa", "severă", "severe"]):
        results.append(make_card(
            source="Clinical safety note",
            title="Atenționare clinică pentru forme severe",
            excerpt=(
                "Datele introduse sugerează posibilitatea unui tablou clinic mai sever, iar interpretarea trebuie făcută prudent, cu evaluare medicală rapidă atunci când există risc respirator sau hemodinamic."
            ),
            recommendation=(
                "În prezența semnelor severe, conduita trebuie orientată spre evaluare urgentă și aplicarea protocoalelor corespunzătoare contextului clinic."
            ),
            url=""
        ))

    seen = set()
    deduped = []

    for item in results:
        key = (
            item.get("source", "").strip(),
            item.get("title", "").strip(),
            item.get("excerpt", "").strip(),
            item.get("recommendation", "").strip()
        )
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    return deduped[:5]