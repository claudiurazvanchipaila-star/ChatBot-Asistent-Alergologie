import os
import json
from io import BytesIO
from datetime import datetime

from flask import Flask, request, jsonify, render_template, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from utils import load_books, search_chunks, initialize_semantic_index
from models import (
    load_diagnoses,
    load_romanian_knowledge,
    rank_differential_diagnoses,
    get_treatment_details
)

try:
    from guidelines_service import get_guideline_recommendations
except Exception:
    def get_guideline_recommendations(*args, **kwargs):
        return []


app = Flask(__name__)

BOOKS_DIR = "books"
CASES_DIR = "cases"
CASES_FILE = os.path.join(CASES_DIR, "saved_cases.json")
DIAGNOSES_FILE = "data/diagnoses.json"
KNOWLEDGE_FILE = "data/allergy_knowledge_ro.json"

os.makedirs(CASES_DIR, exist_ok=True)


def safe_load_json_file(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def get_pdf_paths():
    if not os.path.exists(BOOKS_DIR):
        return []
    return [
        os.path.join(BOOKS_DIR, f)
        for f in os.listdir(BOOKS_DIR)
        if f.lower().endswith(".pdf")
    ]


def initialize_resources():
    pdf_paths = get_pdf_paths()

    book_documents = []
    semantic_index = None

    if pdf_paths:
        try:
            book_documents = load_books(pdf_paths)
        except Exception as e:
            print(f"[EROARE] load_books: {e}")
            book_documents = []

        try:
            semantic_index = initialize_semantic_index(
                book_documents,
                pdf_paths,
                force_rebuild=False
            )
        except Exception as e:
            print(f"[EROARE] initialize_semantic_index: {e}")
            semantic_index = None

    try:
        diagnoses = load_diagnoses(DIAGNOSES_FILE)
    except Exception as e:
        print(f"[EROARE] load_diagnoses: {e}")
        diagnoses = []

    try:
        knowledge_ro = load_romanian_knowledge(KNOWLEDGE_FILE)
    except Exception as e:
        print(f"[EROARE] load_romanian_knowledge: {e}")
        knowledge_ro = {}

    return pdf_paths, book_documents, semantic_index, diagnoses, knowledge_ro


PDF_PATHS, BOOK_DOCUMENTS, SEMANTIC_INDEX, DIAGNOSES, KNOWLEDGE_RO = initialize_resources()


def safe_search_chunks(query, top_k=5):
    if not query or not SEMANTIC_INDEX:
        return []
    try:
        return search_chunks(query, SEMANTIC_INDEX, top_k=top_k)
    except Exception as e:
        print(f"[EROARE] search_chunks: {e}")
        return []


def load_saved_cases():
    return safe_load_json_file(CASES_FILE, [])


def save_cases_to_disk(cases):
    with open(CASES_FILE, "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)


def register_pdf_fonts():
    candidate_fonts = [
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        ),
        (
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Italic.ttf",
        ),
        (
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\ariali.ttf",
        ),
    ]

    font_set = {
        "regular": "Helvetica",
        "bold": "Helvetica-Bold",
        "italic": "Helvetica-Oblique"
    }

    for regular_path, bold_path, italic_path in candidate_fonts:
        try:
            if os.path.exists(regular_path):
                pdfmetrics.registerFont(TTFont("AppRegular", regular_path))
                font_set["regular"] = "AppRegular"

            if os.path.exists(bold_path):
                pdfmetrics.registerFont(TTFont("AppBold", bold_path))
                font_set["bold"] = "AppBold"

            if os.path.exists(italic_path):
                pdfmetrics.registerFont(TTFont("AppItalic", italic_path))
                font_set["italic"] = "AppItalic"

            if font_set["regular"] != "Helvetica":
                break
        except Exception as e:
            print(f"[EROARE] register_pdf_fonts: {e}")

    return font_set


def draw_wrapped_text(pdf, text, x, y, max_width=500, line_height=14, font_name="Helvetica", font_size=10):
    pdf.setFont(font_name, font_size)

    words = (text or "").split()
    line = ""

    for word in words:
        test_line = f"{line} {word}".strip()
        if pdf.stringWidth(test_line, font_name, font_size) <= max_width:
            line = test_line
        else:
            pdf.drawString(x, y, line)
            y -= line_height
            line = word

    if line:
        pdf.drawString(x, y, line)
        y -= line_height

    return y


def to_clean_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        cleaned = []
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                cleaned.append(text)
        return cleaned
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, dict):
        cleaned = []
        for k, v in value.items():
            if isinstance(v, list):
                for sub in v:
                    sub_text = str(sub).strip()
                    if sub_text:
                        cleaned.append(f"{k}: {sub_text}")
            else:
                v_text = str(v).strip()
                if v_text:
                    cleaned.append(f"{k}: {v_text}")
        return cleaned
    text = str(value).strip()
    return [text] if text else []


def normalize_differential_list(differential):
    normalized = []

    if not isinstance(differential, list):
        return normalized

    for item in differential:
        if isinstance(item, dict):
            name = (
                item.get("name")
                or item.get("diagnosis")
                or item.get("label")
                or item.get("title")
                or "Diagnostic nedefinit"
            )

            score = item.get("score", 0)
            probability = item.get("probability", "")
            severity = item.get("severity", "")
            confidence = item.get("confidence", "")

            normalized.append({
                "name": str(name).strip(),
                "score": score,
                "probability": str(probability).strip() if probability is not None else "",
                "severity": str(severity).strip() if severity is not None else "",
                "confidence": str(confidence).strip() if confidence is not None else ""
            })
        else:
            text = str(item).strip()
            if text:
                normalized.append({
                    "name": text,
                    "score": 0,
                    "probability": "",
                    "severity": "",
                    "confidence": ""
                })

    return normalized


def build_fallback_analysis_from_differential(differential):
    primary = differential[0] if differential else {}

    primary_name = primary.get("name", "Nespecificat")
    severity = primary.get("severity", "ușoară")
    probability = primary.get("probability", "moderată")
    confidence = primary.get("confidence", "moderată")

    supports = [
        "Simptomatologia introdusă este compatibilă cu diagnosticul orientativ selectat.",
        "Încadrarea este bazată pe potrivirea simptomelor cu logica diferențială disponibilă."
    ]

    limits = [
        "Analiza este orientativă și nu poate înlocui anamneza completă, examenul clinic și investigațiile.",
        "Absența unor detalii despre debut, durată, expuneri și comorbidități reduce specificitatea concluziei."
    ]

    recommended_tests = [
        "Anamneză orientată pe sezonalitate, expuneri și contextul simptomelor.",
        "Investigații alergologice și/sau evaluare suplimentară în funcție de contextul clinic."
    ]

    treatment_plan = [
        "Evitarea expunerii la alergeni atunci când aceștia pot fi identificați.",
        "Reevaluare clinică dacă tabloul se modifică sau persistă.",
        "Individualizarea conduitei terapeutice în funcție de severitate și comorbidități."
    ]

    notes = [
        "Rezultatul este orientativ și trebuie corelat cu datele clinice complete."
    ]

    alternatives = [d.get("name", "") for d in differential[1:] if d.get("name")]

    return {
        "primary_diagnosis": primary_name,
        "primary_probability": probability,
        "severity": severity,
        "confidence": confidence,
        "associated_diagnoses": alternatives,
        "supports": supports,
        "limits": limits,
        "recommended_tests": recommended_tests,
        "treatment_plan": treatment_plan,
        "red_flags": [],
        "notes": notes,
        "alternatives": alternatives
    }


def normalize_clinical_output(clinical_output, differential):
    fallback = build_fallback_analysis_from_differential(differential)

    if isinstance(clinical_output, dict):
        primary_diagnosis = (
            clinical_output.get("primary_diagnosis")
            or clinical_output.get("diagnostic_principal")
            or fallback["primary_diagnosis"]
        )

        primary_probability = (
            clinical_output.get("primary_probability")
            or clinical_output.get("probability")
            or clinical_output.get("probabilitate")
            or fallback["primary_probability"]
        )

        severity = (
            clinical_output.get("severity")
            or clinical_output.get("severitate")
            or fallback["severity"]
        )

        confidence = (
            clinical_output.get("confidence")
            or clinical_output.get("grad_incredere")
            or clinical_output.get("confidence_level")
            or fallback["confidence"]
        )

        associated_diagnoses = to_clean_list(
            clinical_output.get("associated_diagnoses")
            or clinical_output.get("diagnostice_asociate")
        )

        supports = to_clean_list(
            clinical_output.get("supports")
            or clinical_output.get("supporting_elements")
            or clinical_output.get("elemente_sustinere")
            or clinical_output.get("argumente_pro")
        )

        limits = to_clean_list(
            clinical_output.get("limits")
            or clinical_output.get("prudence")
            or clinical_output.get("elemente_prudenta")
            or clinical_output.get("cautions")
        )

        recommended_tests = to_clean_list(
            clinical_output.get("recommended_tests")
            or clinical_output.get("investigations")
            or clinical_output.get("investigatii")
        )

        treatment_plan = to_clean_list(
            clinical_output.get("treatment_plan")
            or clinical_output.get("conduct")
            or clinical_output.get("conduita")
            or clinical_output.get("management")
        )

        red_flags = to_clean_list(
            clinical_output.get("red_flags")
            or clinical_output.get("alarms")
        )

        notes = to_clean_list(
            clinical_output.get("notes")
            or clinical_output.get("note")
        )

        alternatives = to_clean_list(
            clinical_output.get("alternatives")
            or clinical_output.get("alternative_diagnoses")
        )

        if not alternatives:
            alternatives = [d.get("name", "") for d in differential[1:] if d.get("name")]

        if not associated_diagnoses:
            associated_diagnoses = alternatives

        return {
            "primary_diagnosis": primary_diagnosis,
            "primary_probability": primary_probability,
            "severity": severity,
            "confidence": confidence,
            "associated_diagnoses": associated_diagnoses,
            "supports": supports or fallback["supports"],
            "limits": limits or fallback["limits"],
            "recommended_tests": recommended_tests or fallback["recommended_tests"],
            "treatment_plan": treatment_plan or fallback["treatment_plan"],
            "red_flags": red_flags,
            "notes": notes or fallback["notes"],
            "alternatives": alternatives
        }

    if isinstance(clinical_output, str) and clinical_output.strip():
        data = fallback.copy()
        data["notes"] = [clinical_output.strip()]
        return data

    return fallback


def build_guideline_cards(guideline_results):
    cards = []

    if not isinstance(guideline_results, list):
        return cards

    for item in guideline_results:
        if isinstance(item, dict):
            cards.append({
                "title": item.get("title", "Recomandare"),
                "source": item.get("source", ""),
                "excerpt": item.get("excerpt", ""),
                "url": item.get("url", ""),
                "recommendation": item.get("recommendation", ""),
            })
        else:
            text = str(item).strip()
            if text:
                cards.append({
                    "title": "Recomandare",
                    "source": "",
                    "excerpt": text,
                    "url": "",
                    "recommendation": text
                })

    return cards


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "pdf_count": len(PDF_PATHS),
        "semantic_index_ready": SEMANTIC_INDEX is not None,
        "diagnoses_loaded": len(DIAGNOSES) if isinstance(DIAGNOSES, list) else 0
    })


@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json(force=True)

        symptoms = data.get("symptoms", "")
        age = data.get("age", "")
        sex = data.get("sex", "")
        weight = data.get("weight", "")
        context = data.get("context", "")
        extra = data.get("extra", "")

        response_text = (
            f"Date primite cu succes.\n"
            f"Simptome: {symptoms or '-'}\n"
            f"Vârstă: {age or '-'}\n"
            f"Sex: {sex or '-'}\n"
            f"Greutate: {weight or '-'}\n"
            f"Context: {context or '-'}\n"
            f"Alte date: {extra or '-'}"
        )

        return jsonify({"response": response_text})
    except Exception as e:
        return jsonify({"response": f"Eroare la procesare: {str(e)}"}), 500


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json(force=True)

        symptoms = str(data.get("symptoms", "")).strip()
        age = str(data.get("age", "")).strip()
        sex = str(data.get("sex", "")).strip()
        weight = str(data.get("weight", "")).strip()
        context = str(data.get("context", "")).strip()
        extra = str(data.get("extra", "")).strip()

        full_text = " ".join(part for part in [symptoms, context, extra] if part).strip()

        if not full_text:
            return jsonify({
                "error": "Nu au fost introduse suficiente date clinice."
            }), 400

        try:
            raw_differential, raw_clinical_output = rank_differential_diagnoses(full_text, DIAGNOSES)
        except Exception as e:
            print(f"[EROARE] rank_differential_diagnoses: {e}")
            raw_differential, raw_clinical_output = [], "Nu s-a putut genera analiza clinică."

        differential = normalize_differential_list(raw_differential)
        analysis = normalize_clinical_output(raw_clinical_output, differential)

        semantic_query = " ".join(part for part in [symptoms, context, extra] if part).strip()
        results = safe_search_chunks(semantic_query, top_k=8)

        response = {
            "analysis": analysis,
            "main_diagnosis": {
                "name": analysis.get("primary_diagnosis", "Nespecificat"),
                "probability": analysis.get("primary_probability", ""),
                "severity": analysis.get("severity", ""),
                "confidence": analysis.get("confidence", ""),
                "associated_diagnoses": analysis.get("associated_diagnoses", [])
            },
            "differential": differential[:5],
            "clinical_output": analysis,
            "patient_context": {
                "age": age,
                "sex": sex,
                "weight": weight,
                "context": context,
                "extra": extra
            },
            "results": results,
            "warning": (
                "Instrument de suport pentru medic, bazat pe surse clinice și logică orientativă. "
                "Nu stabilește autonom diagnosticul final și nu înlocuiește decizia medicală."
            )
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({
            "error": f"Eroare la analiză: {str(e)}"
        }), 500


@app.route("/treatment", methods=["POST"])
def treatment():
    try:
        data = request.get_json(force=True)

        diagnosis_name = str(data.get("diagnosis", "")).strip()
        age = str(data.get("age", "")).strip()
        weight = str(data.get("weight", "")).strip()
        symptoms = str(data.get("symptoms", "")).strip()
        context = str(data.get("context", "")).strip()
        extra = str(data.get("extra", "")).strip()
        severity = str(data.get("severity", "")).strip()

        if not diagnosis_name:
            return jsonify({
                "error": "Diagnosticul nu a fost specificat."
            }), 400

        source_results = []

        try:
            treatment_data = get_treatment_details(
                diagnosis_name,
                KNOWLEDGE_RO,
                age=age,
                weight=weight,
                severity=severity
            )
        except Exception as e:
            print(f"[EROARE] get_treatment_details: {e}")
            treatment_data = {}

        guideline_results = []

        clinical_picture = to_clean_list(treatment_data.get("clinical_picture", []))
        treatment_plan = to_clean_list(treatment_data.get("treatment", []))
        prevention = to_clean_list(treatment_data.get("prevention", []))
        allergen_avoidance = to_clean_list(treatment_data.get("allergen_avoidance", []))

        medication_options_raw = treatment_data.get("medication_options", [])
        medication_options = medication_options_raw if isinstance(medication_options_raw, list) else []

        simple_medications = []
        medication_cards = []

        for med in medication_options:
            if isinstance(med, dict):
                medication_cards.append({
                    "class": med.get("class", ""),
                    "name": med.get("name", ""),
                    "substance": med.get("substance", ""),
                    "dose": med.get("dose", ""),
                    "route": med.get("route", ""),
                    "frequency": med.get("frequency", ""),
                    "duration": med.get("duration", ""),
                    "notes": med.get("notes", ""),
                    "adverse_reactions": med.get("adverse_reactions", "")
                })

                label_parts = [med.get("class", ""), med.get("name", ""), med.get("dose", "")]
                label = " | ".join([p for p in label_parts if p])
                if label:
                    simple_medications.append(label)
            else:
                text = str(med).strip()
                if text:
                    simple_medications.append(text)

        guideline_cards = build_guideline_cards(guideline_results)

        response = {
            "diagnosis": treatment_data.get("diagnosis", diagnosis_name),
            "clinical_picture": clinical_picture,
            "treatment": treatment_plan,
            "prevention": prevention,
            "allergen_avoidance": allergen_avoidance,
            "medication_options": medication_options,
            "medication_cards": medication_cards,
            "simple_medications": simple_medications,
            "age_group_used": treatment_data.get("age_group_used", "vârstă neprecizată"),
            "weight_used": treatment_data.get("weight_used", weight),
            "severity_used": treatment_data.get("severity_used", severity),
            "guideline_results": guideline_results,
            "guideline_cards": guideline_cards,
            "source_results": source_results,
            "warning": (
                "Dozele și exemplele de substanțe active sunt orientative și trebuie confirmate în funcție de "
                "produsul disponibil, indicația exactă, greutate, severitate, comorbidități, contraindicații și contextul clinic individual."
            )
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({
            "error": f"Eroare la tratament: {str(e)}"
        }), 500


@app.route("/save_case", methods=["POST"])
def save_case():
    try:
        data = request.get_json(force=True)

        case_entry = {
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "patient_summary": data.get("patient_summary", {}),
            "analysis": data.get("analysis", {})
        }

        existing = load_saved_cases()
        existing.append(case_entry)
        save_cases_to_disk(existing)

        return jsonify({
            "message": "Caz salvat cu succes.",
            "count": len(existing),
            "path": CASES_FILE
        })

    except Exception as e:
        return jsonify({
            "error": f"Eroare la salvarea cazului: {str(e)}"
        }), 500


@app.route("/export_pdf", methods=["POST"])
def export_pdf():
    try:
        data = request.get_json(force=True)

        patient = data.get("patient_summary", {})
        analysis = data.get("analysis", {})

        fonts = register_pdf_fonts()

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        _, height = A4

        y = height - 40

        pdf.setTitle("Raport orientativ alergologie")
        pdf.setFont(fonts["bold"], 16)
        pdf.drawString(40, y, "Raport orientativ - Asistent clinic în alergologie")
        y -= 28

        pdf.setFont(fonts["regular"], 10)
        y = draw_wrapped_text(
            pdf,
            f"Data generării: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            40,
            y,
            font_name=fonts["regular"]
        )
        y -= 8

        sections = [
            ("Date introduse", [
                f"Simptome: {patient.get('symptoms', '-')}",
                f"Vârstă: {patient.get('age', '-')}",
                f"Greutate: {patient.get('weight', '-')}",
                f"Sex: {patient.get('sex', '-')}",
                f"Context clinic: {patient.get('context', '-')}",
                f"Alte date clinice: {patient.get('extra', '-')}"
            ]),
            ("Diagnostic principal", [
                f"{analysis.get('primary_diagnosis', '-')}",
                f"Probabilitate: {analysis.get('primary_probability', '-')}",
                f"Severitate estimată: {analysis.get('severity', '-')}",
                f"Grad de încredere: {analysis.get('confidence', '-')}"
            ]),
            ("Diagnostice alternative", analysis.get("alternatives", [])),
            ("Elemente care susțin diagnosticul", analysis.get("supports", [])),
            ("Elemente de interpretat cu prudență", analysis.get("limits", [])),
            ("Investigații recomandate", analysis.get("recommended_tests", [])),
            ("Conduită orientativă", analysis.get("treatment_plan", [])),
            ("Red flags", analysis.get("red_flags", [])),
            ("Note", analysis.get("notes", []))
        ]

        for title, items in sections:
            if y < 100:
                pdf.showPage()
                y = height - 40

            pdf.setFont(fonts["bold"], 12)
            pdf.drawString(40, y, title)
            y -= 18

            pdf.setFont(fonts["regular"], 10)
            if not items:
                y = draw_wrapped_text(pdf, "-", 50, y, font_name=fonts["regular"])
            else:
                for item in items:
                    if y < 80:
                        pdf.showPage()
                        y = height - 40
                    y = draw_wrapped_text(pdf, f"- {item}", 50, y, font_name=fonts["regular"])
            y -= 8

        pdf.setFont(fonts["italic"], 9)
        disclaimer = (
            "Document orientativ. Nu înlocuiește consultul medical, examenul clinic și decizia terapeutică. "
            "Dozele medicamentoase trebuie verificate în funcție de produs, greutate, vârstă și severitate."
        )
        y = draw_wrapped_text(
            pdf,
            disclaimer,
            40,
            y,
            max_width=500,
            font_name=fonts["italic"],
            font_size=9
        )

        pdf.save()
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name="raport_alergologie_pacient.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        return jsonify({
            "error": f"Eroare la export PDF: {str(e)}"
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)