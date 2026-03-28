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
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=timeout,
            allow_redirects=True
        )
        response.raise_for_status()
        return response.text
    except Exception:
        return ""


def extract_text_from_html(html: str) -> str:
    if not html:
        return ""

    try:
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "noscript", "svg"]):
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
        if 45 <= len(sentence) <= 260:
            cleaned.append(sentence)

    return cleaned


def clean_excerpt(text: str, max_len: int = 300) -> str:
    text = text or ""
    text = re.sub(r"read more", "", text, flags=re.IGNORECASE)
    text = re.sub(r"position papers?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"guidelines?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) > max_len:
        text = text[:max_len].rsplit(" ", 1)[0].strip() + "…"

    return text


def infer_topic_profile(
    diagnosis_name: str,
    symptoms: str,
    context: str,
    triggers: str,
    extra: str,
    query: str = ""
) -> Dict[str, bool]:
    diagnosis_norm = normalize_text(diagnosis_name)
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

    if contains_any(diagnosis_norm, ["rinita alergica", "rinita non alergica", "rinita virala", "rinoconjunctivita"]):
        profile["rhinitis"] = True

    if contains_any(diagnosis_norm, ["conjunctivita alergica"]):
        profile["conjunctivitis"] = True

    if contains_any(diagnosis_norm, ["astm alergic", "astm"]):
        profile["asthma"] = True

    if contains_any(diagnosis_norm, ["alergie alimentara", "alergie aliment"]):
        profile["food_allergy"] = True

    if contains_any(diagnosis_norm, ["urticarie", "angioedem"]):
        profile["urticaria_angioedema"] = True

    if contains_any(diagnosis_norm, ["anafilaxie"]):
        profile["anaphylaxis"] = True

    if contains_any(diagnosis_norm, ["dermatita atopica", "eczema", "atopic dermatitis"]):
        profile["atopic_dermatitis"] = True

    if contains_any(joined, [
        "rinit", "rinoree", "stranut", "strănut", "prurit nazal", "nas infundat",
        "nas înfundat", "congestie nazala", "congestie nazală", "rhin", "rhinoconj"
    ]):
        profile["rhinitis"] = True

    if contains_any(joined, [
        "conjunctivit", "ochi rosii", "ochi roșii", "lacrimare", "prurit ocular",
        "mancarime la ochi", "mâncărime la ochi", "edem palpebral", "pleoape umflate"
    ]):
        profile["conjunctivitis"] = True

    if contains_any(joined, [
        "astm", "wheezing", "suieraturi", "șuierături", "dispnee", "tuse nocturna",
        "tuse nocturnă", "constrictie toracica", "constricție toracică",
        "respiratie grea", "respirație grea", "fluierat in piept", "fluierat în piept",
        "asthma"
    ]):
        profile["asthma"] = True

    if contains_any(joined, [
        "aliment", "dupa masa", "după masă", "dupa ce a mancat", "după ce a mâncat",
        "prurit oral", "furnicaturi orale", "furnicături orale", "varsaturi", "vărsături",
        "diaree", "food allergy"
    ]):
        profile["food_allergy"] = True

    if contains_any(joined, [
        "urticarie", "angioedem", "edem buze", "edem pleoape", "bube care apar si dispar",
        "bube care apar și dispar", "bubite care apar si dispar", "bubițe care apar și dispar"
    ]):
        profile["urticaria_angioedema"] = True

    if contains_any(joined, [
        "anafilaxie", "soc", "șoc", "hipotensiune", "edem lingual",
        "stridor", "colaps", "anaphylaxis"
    ]):
        profile["anaphylaxis"] = True

    if contains_any(joined, [
        "dermatita", "dermatită", "eczeme", "prurit cutanat", "piele uscata",
        "piele uscată", "atopic dermatitis", "eczema", "leziune eritematoasa",
        "leziune eritematoasă", "pliuri", "coate", "genunchi"
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


def fallback_eaaci_card(topic: str) -> Dict:
    topic_map = {
        "rhinitis": make_card(
            source="EAACI",
            title="Guidelines & Position Papers / Allergic Rhinitis and Rhinoconjunctivitis",
            excerpt="EAACI include resurse relevante pentru rinita alergică și rinoconjunctivită, utile pentru orientarea diagnosticului și a conduitei.",
            recommendation="Corelează simptomele nazale și oculare cu sezonalitatea, expunerea la alergeni și contextul clinic; evaluarea alergologică și tratamentul trebuie individualizate.",
            url=EAACI_GUIDELINES_URL
        ),
        "food_allergy": make_card(
            source="EAACI",
            title="Guidelines & Position Papers / Food Allergy",
            excerpt="EAACI publică materiale utile pentru alergia alimentară, inclusiv orientare pentru confirmarea diagnosticului și prevenirea reacțiilor severe.",
            recommendation="Pentru suspiciunea de alergie alimentară, sunt importante corelarea temporală cu ingestia, evitarea alimentului suspect până la clarificare și planul de siguranță în caz de reacții severe.",
            url=EAACI_GUIDELINES_URL
        ),
        "urticaria_angioedema": make_card(
            source="EAACI",
            title="Guidelines & Position Papers / Urticaria and Angioedema",
            excerpt="EAACI oferă resurse utile pentru diferențierea urticariei și angioedemului și pentru evaluarea severității clinice.",
            recommendation="Diferențiază leziunile cutanate fugace de alte erupții și evaluează rapid eventualele semne de afectare respiratorie sau sistemică.",
            url=EAACI_GUIDELINES_URL
        ),
        "anaphylaxis": make_card(
            source="EAACI",
            title="Guidelines & Position Papers / Anaphylaxis",
            excerpt="EAACI include resurse relevante pentru recunoașterea și managementul anafilaxiei.",
            recommendation="Orice suspiciune de anafilaxie trebuie tratată ca urgență; după stabilizare, este importantă clarificarea cauzei și educația privind prevenirea recurenței.",
            url=EAACI_GUIDELINES_URL
        ),
        "atopic_dermatitis": make_card(
            source="EAACI",
            title="Guidelines & Position Papers / Atopic Dermatitis",
            excerpt="Resursele EAACI pot susține orientarea clinică în dermatita atopică și identificarea factorilor agravanți.",
            recommendation="În dermatita atopică, evaluarea trebuie să includă severitatea, impactul funcțional, rutina de îngrijire cutanată și eventualii factori agravanți.",
            url=EAACI_GUIDELINES_URL
        ),
        "general": make_card(
            source="EAACI",
            title="Guidelines & Position Papers",
            excerpt="EAACI pune la dispoziție o secțiune oficială de ghiduri și position papers relevante pentru alergologie și imunologie clinică.",
            recommendation="Folosește secțiunea EAACI ca punct de orientare pentru corelarea tabloului clinic cu ghidurile de specialitate.",
            url=EAACI_GUIDELINES_URL
        )
    }
    return topic_map.get(topic, topic_map["general"])


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

    if profile["rhinitis"] or profile["conjunctivitis"]:
        excerpt_candidates = extract_relevant_sentences(
            text,
            ["rhinitis", "rhinoconjunctivitis", "allergic rhinitis", "conjunctivitis"],
            limit=2
        )
        excerpt = clean_excerpt(" ".join(excerpt_candidates), 280)
        if not excerpt:
            results.append(fallback_eaaci_card("rhinitis"))
        else:
            results.append(make_card(
                source="EAACI",
                title="Guidelines & Position Papers / Allergic Rhinitis and Rhinoconjunctivitis",
                excerpt=excerpt,
                recommendation="Corelează simptomele nazale și oculare cu sezonalitatea, expunerea la alergeni și contextul clinic; evaluarea alergologică și conduita terapeutică trebuie individualizate.",
                url=EAACI_GUIDELINES_URL
            ))

    if profile["food_allergy"]:
        excerpt_candidates = extract_relevant_sentences(
            text,
            ["food allergy", "ige-mediated", "allergy", "anaphylaxis"],
            limit=2
        )
        excerpt = clean_excerpt(" ".join(excerpt_candidates), 280)
        if not excerpt:
            results.append(fallback_eaaci_card("food_allergy"))
        else:
            results.append(make_card(
                source="EAACI",
                title="Guidelines & Position Papers / Food Allergy",
                excerpt=excerpt,
                recommendation="Pentru suspiciunea de alergie alimentară, sunt importante corelarea temporală cu ingestia, evitarea alimentului suspect până la clarificare și planul de siguranță în caz de reacții severe.",
                url=EAACI_GUIDELINES_URL
            ))

    if profile["urticaria_angioedema"]:
        excerpt_candidates = extract_relevant_sentences(
            text,
            ["urticaria", "angioedema", "allergy"],
            limit=2
        )
        excerpt = clean_excerpt(" ".join(excerpt_candidates), 280)
        if not excerpt:
            results.append(fallback_eaaci_card("urticaria_angioedema"))
        else:
            results.append(make_card(
                source="EAACI",
                title="Guidelines & Position Papers / Urticaria and Angioedema",
                excerpt=excerpt,
                recommendation="Diferențiază leziunile cutanate fugace de alte erupții și evaluează rapid eventualele semne de afectare respiratorie sau sistemică.",
                url=EAACI_GUIDELINES_URL
            ))

    if profile["anaphylaxis"]:
        excerpt_candidates = extract_relevant_sentences(
            text,
            ["anaphylaxis", "emergency", "adrenaline"],
            limit=2
        )
        excerpt = clean_excerpt(" ".join(excerpt_candidates), 280)
        if not excerpt:
            results.append(fallback_eaaci_card("anaphylaxis"))
        else:
            results.append(make_card(
                source="EAACI",
                title="Guidelines & Position Papers / Anaphylaxis",
                excerpt=excerpt,
                recommendation="Orice suspiciune de anafilaxie trebuie tratată ca urgență; după stabilizare, este importantă clarificarea cauzei și educația privind prevenirea recurenței.",
                url=EAACI_GUIDELINES_URL
            ))

    if profile["atopic_dermatitis"]:
        excerpt_candidates = extract_relevant_sentences(
            text,
            ["atopic dermatitis", "eczema", "skin", "allergy"],
            limit=2
        )
        excerpt = clean_excerpt(" ".join(excerpt_candidates), 280)
        if not excerpt:
            results.append(fallback_eaaci_card("atopic_dermatitis"))
        else:
            results.append(make_card(
                source="EAACI",
                title="Guidelines & Position Papers / Atopic Dermatitis",
                excerpt=excerpt,
                recommendation="În dermatita atopică, evaluarea trebuie să includă severitatea, impactul funcțional, rutina de îngrijire cutanată și eventualii factori agravanți.",
                url=EAACI_GUIDELINES_URL
            ))

    if not results:
        results.append(fallback_eaaci_card("general"))

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
    results = []

    excerpt_general_candidates = extract_relevant_sentences(
        text,
        ["asthma", "guide", "management", "treatment", "controller", "reliever"],
        limit=2
    )
    excerpt_general = clean_excerpt(" ".join(excerpt_general_candidates), 280)

    if not excerpt_general:
        excerpt_general = (
            "GINA oferă resurse oficiale pentru managementul astmului, cu accent pe alegerea tratamentului în funcție de controlul simptomelor și severitate."
        )

    results.append(make_card(
        source="GINA",
        title="Global Initiative for Asthma / General asthma guidance",
        excerpt=excerpt_general,
        recommendation="Interpretarea terapeutică trebuie făcută în funcție de controlul simptomelor, istoricul exacerbărilor, vârstă și tehnica inhalatorie.",
        url=GINA_HOME_URL
    ))

    excerpt_step_candidates = extract_relevant_sentences(
        text,
        ["step", "controller", "reliever", "inhaled corticosteroid", "ics"],
        limit=2
    )
    excerpt_step = clean_excerpt(" ".join(excerpt_step_candidates), 280)

    if excerpt_step:
        results.append(make_card(
            source="GINA",
            title="Global Initiative for Asthma / Stepwise treatment approach",
            excerpt=excerpt_step,
            recommendation="Schema de tratament pentru astm nu trebuie automatizată doar după simptom; este necesară integrarea treptei terapeutice și a răspunsului clinic.",
            url=GINA_HOME_URL
        ))

    excerpt_severe_candidates = extract_relevant_sentences(
        text,
        ["severe asthma", "specialist", "expert", "phenotype", "difficult-to-treat"],
        limit=2
    )
    excerpt_severe = clean_excerpt(" ".join(excerpt_severe_candidates), 280)

    if excerpt_severe:
        results.append(make_card(
            source="GINA",
            title="Global Initiative for Asthma / Severe or difficult-to-control asthma",
            excerpt=excerpt_severe,
            recommendation="Dacă există control insuficient sau suspiciune de astm sever, este necesară reevaluarea diagnosticului, aderenței, tehnicii inhalatorii și a indicației de evaluare de specialitate.",
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

    excerpt_candidates = extract_relevant_sentences(
        text,
        ["rhinitis", "allergic rhinitis", "asthma", "control", "rhinoconjunctivitis"],
        limit=2
    )
    excerpt = clean_excerpt(" ".join(excerpt_candidates), 280)

    if not excerpt:
        excerpt = (
            "ARIA oferă resurse orientative pentru rinita alergică și relația acesteia cu astmul, subliniind importanța controlului simptomelor și a evaluării expunerii la alergeni."
        )

    return [
        make_card(
            source="ARIA",
            title="Allergic Rhinitis and its Impact on Asthma",
            excerpt=excerpt,
            recommendation="În rinita alergică, sunt importante evaluarea controlului simptomelor, reducerea expunerii la alergeni și alegerea tratamentului în funcție de severitate și persistență.",
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
            excerpt="Datele introduse sugerează posibilitatea unui tablou clinic mai sever, iar interpretarea trebuie făcută prudent, cu evaluare medicală rapidă atunci când există risc respirator sau hemodinamic.",
            recommendation="În prezența semnelor severe, conduita trebuie orientată spre evaluare urgentă și aplicarea protocoalelor corespunzătoare contextului clinic.",
            url=""
        ))

    seen = set()
    deduped = []

    for item in results:
        key = (
            normalize_text(item.get("source", "")),
            normalize_text(item.get("title", "")),
        )
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    return deduped[:5]