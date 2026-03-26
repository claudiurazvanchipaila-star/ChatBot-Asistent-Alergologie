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

    # PDF-urile rămân opționale. Dacă lipsesc sau apar erori, aplicația merge în continuare.
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


# Pe Render evităm încărcarea resurselor grele la startup,
# astfel încât aplicația să deschidă portul rapid.
# Local poți păstra inițializarea completă.
if os.environ.get("RENDER") or os.environ.get("IS_RENDER") or os.environ.get("RENDER_SERVICE_ID"):
    PDF_PATHS = []
    BOOK_DOCUMENTS = []
    SEMANTIC_INDEX = None

    try:
        DIAGNOSES = load_diagnoses(DIAGNOSES_FILE)
    except Exception as e:
        print(f"[EROARE] load_diagnoses: {e}")
        DIAGNOSES = []

    try:
        KNOWLEDGE_RO = load_romanian_knowledge(KNOWLEDGE_FILE)
    except Exception as e:
        print(f"[EROARE] load_romanian_knowledge: {e}")
        KNOWLEDGE_RO = {}
else:
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
    """
    Render nu are fonturile Windows, deci încercăm mai multe variante.
    Dacă nu găsim nimic, folosim Helvetica.
    """
    candidate_fonts = [
        ("ArialCustom", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ("ArialCustom-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("ArialCustom-Italic", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"),

        ("ArialCustom", r"C:\Windows\Fonts\arial.ttf"),
        ("ArialCustom-Bold", r"C:\Windows\Fonts\arialbd.ttf"),
        ("ArialCustom-Italic", r"C:\Windows\Fonts\ariali.ttf"),
    ]

    font_set = {
        "regular": "Helvetica",
        "bold": "Helvetica-Bold",
        "italic": "Helvetica-Oblique"
    }

    try:
        for font_name, font_path in candidate_fonts:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                except Exception:
                    pass

        if "ArialCustom" in pdfmetrics.getRegisteredFontNames():
            font_set["regular"] = "ArialCustom"
        if "ArialCustom-Bold" in pdfmetrics.getRegisteredFontNames():
            font_set["bold"] = "ArialCustom-Bold"
        if "ArialCustom-Italic" in pdfmetrics.getRegisteredFontNames():
            font_set["italic"] = "ArialCustom-Italic"

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


def clean_text(value):
    return str(value or "").strip()


def extract_patient_data(data):
    return {
        "symptoms": clean_text(data.get("symptoms")),
        "age": clean_text(data.get("age")),
        "sex": clean_text(data.get("sex")),
        "weight": clean_text(data.get("weight")),
        "context": clean_text(data.get("context")),
        "extra": clean_text(data.get("extra")),
        "severity": clean_text(data.get("severity")),
        "personal_history": clean_text(data.get("personal_history")),
        "family_history": clean_text(data.get("family_history")),
    }


def build_full_text(patient_data):
    return " ".join([
        patient_data.get("symptoms", ""),
        patient_data.get("context", ""),
        patient_data.get("extra", ""),
        patient_data.get("personal_history", ""),
        patient_data.get("family_history", "")
    ]).strip()


def build_semantic_query(patient_data):
    return ". ".join([
        patient_data.get("symptoms", ""),
        patient_data.get("context", ""),
        patient_data.get("extra", ""),
        patient_data.get("personal_history", ""),
        patient_data.get("family_history", "")
    ]).strip(" .")


def run_analysis_logic(data):
    patient_data = extract_patient_data(data)
    full_text = build_full_text(patient_data)

    if not full_text:
        return {
            "error": "Nu au fost introduse suficiente date clinice."
        }, 400

    try:
        differential, clinical_output = rank_differential_diagnoses(full_text, DIAGNOSES)
    except Exception as e:
        print(f"[EROARE] rank_differential_diagnoses: {e}")
        differential, clinical_output = [], "Nu s-a putut genera analiza clinică."

    semantic_query = build_semantic_query(patient_data)
    results = safe_search_chunks(semantic_query, top_k=8)

    response_payload = {
        "differential": differential[:5] if isinstance(differential, list) else [],
        "clinical_output": clinical_output,
        "patient_context": {
            "age": patient_data.get("age", ""),
            "sex": patient_data.get("sex", ""),
            "weight": patient_data.get("weight", ""),
            "context": patient_data.get("context", ""),
            "extra": patient_data.get("extra", ""),
            "personal_history": patient_data.get("personal_history", ""),
            "family_history": patient_data.get("family_history", "")
        },
        "results": results,
        "warning": (
            "Instrument de suport pentru medic, bazat pe surse clinice și logică orientativă. "
            "Nu stabilește autonom diagnosticul final și nu înlocuiește decizia medicală."
        )
    }

    return response_payload, 200


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
    """
    Frontend-ul poate chema /ask.
    Îi dăm aceeași logică precum /analyze.
    """
    try:
        data = request.get_json(force=True)
        payload, status_code = run_analysis_logic(data)
        return jsonify(payload), status_code
    except Exception as e:
        return jsonify({
            "error": f"Eroare la procesare: {str(e)}"
        }), 500


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json(force=True)
        payload, status_code = run_analysis_logic(data)
        return jsonify(payload), status_code
    except Exception as e:
        return jsonify({
            "error": f"Eroare la analiză: {str(e)}"
        }), 500


@app.route("/treatment", methods=["POST"])
def treatment():
    try:
        data = request.get_json(force=True)
        patient_data = extract_patient_data(data)

        diagnosis_name = clean_text(data.get("diagnosis"))

        if not diagnosis_name:
            return jsonify({
                "error": "Diagnosticul nu a fost specificat."
            }), 400

        semantic_query = (
            f"{diagnosis_name} tablou clinic tratament prevenție evitare alergen alergologie "
            f"{patient_data.get('symptoms', '')} "
            f"{patient_data.get('context', '')} "
            f"{patient_data.get('extra', '')} "
            f"{patient_data.get('personal_history', '')} "
            f"{patient_data.get('family_history', '')}"
        ).strip()

        source_results = safe_search_chunks(semantic_query, top_k=5)

        try:
            treatment_data = get_treatment_details(
                diagnosis_name,
                KNOWLEDGE_RO,
                age=patient_data.get("age", ""),
                weight=patient_data.get("weight", ""),
                severity=patient_data.get("severity", "")
            )
        except Exception as e:
            print(f"[EROARE] get_treatment_details: {e}")
            treatment_data = {}

        try:
            guideline_results = get_guideline_recommendations(
                diagnosis_name=diagnosis_name,
                symptoms=patient_data.get("symptoms", ""),
                context=patient_data.get("context", ""),
                extra=patient_data.get("extra", ""),
                age=patient_data.get("age", ""),
                weight=patient_data.get("weight", ""),
                severity=patient_data.get("severity", ""),
                personal_history=patient_data.get("personal_history", ""),
                family_history=patient_data.get("family_history", "")
            )
        except Exception as e:
            print(f"[EROARE] get_guideline_recommendations: {e}")
            guideline_results = []

        return jsonify({
            "diagnosis": treatment_data.get("diagnosis", diagnosis_name),
            "clinical_picture": treatment_data.get("clinical_picture", []),
            "treatment": treatment_data.get("treatment", []),
            "prevention": treatment_data.get("prevention", []),
            "allergen_avoidance": treatment_data.get("allergen_avoidance", []),
            "medication_options": treatment_data.get("medication_options", []),
            "age_group_used": treatment_data.get("age_group_used", "vârstă neprecizată"),
            "weight_used": treatment_data.get("weight_used", patient_data.get("weight", "")),
            "severity_used": treatment_data.get("severity_used", patient_data.get("severity", "")),
            "guideline_results": guideline_results,
            "source_results": source_results,
            "patient_context": {
                "age": patient_data.get("age", ""),
                "weight": patient_data.get("weight", ""),
                "sex": patient_data.get("sex", ""),
                "context": patient_data.get("context", ""),
                "extra": patient_data.get("extra", ""),
                "personal_history": patient_data.get("personal_history", ""),
                "family_history": patient_data.get("family_history", "")
            },
            "warning": (
                "Dozele și exemplele de substanțe active sunt orientative și trebuie confirmate în funcție de "
                "produsul disponibil, indicația exactă, greutate, severitate, comorbidități, contraindicații și contextul clinic individual."
            )
        })

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
                f"Alte date clinice: {patient.get('extra', '-')}",
                f"Antecedente personale patologice: {patient.get('personal_history', '-')}",
                f"Antecedente heredocolaterale: {patient.get('family_history', '-')}"
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