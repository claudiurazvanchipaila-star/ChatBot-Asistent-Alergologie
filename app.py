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

app = Flask(__name__)

BOOKS_DIR = "books"
CASES_DIR = "cases"
CASES_FILE = os.path.join(CASES_DIR, "saved_cases.json")

os.makedirs(CASES_DIR, exist_ok=True)

pdf_paths = []
if os.path.exists(BOOKS_DIR):
    pdf_paths = [
        os.path.join(BOOKS_DIR, f)
        for f in os.listdir(BOOKS_DIR)
        if f.lower().endswith(".pdf")
    ]

book_documents = load_books(pdf_paths) if pdf_paths else []
semantic_index = initialize_semantic_index(book_documents, pdf_paths, force_rebuild=False) if pdf_paths else None

diagnoses = load_diagnoses("data/diagnoses.json")
knowledge_ro = load_romanian_knowledge("data/allergy_knowledge_ro.json")


def register_pdf_fonts():
    regular_path = r"C:\Windows\Fonts\arial.ttf"
    bold_path = r"C:\Windows\Fonts\arialbd.ttf"
    italic_path = r"C:\Windows\Fonts\ariali.ttf"

    font_set = {
        "regular": "Helvetica",
        "bold": "Helvetica-Bold",
        "italic": "Helvetica-Oblique"
    }

    try:
        if os.path.exists(regular_path):
            pdfmetrics.registerFont(TTFont("ArialCustom", regular_path))
            font_set["regular"] = "ArialCustom"

        if os.path.exists(bold_path):
            pdfmetrics.registerFont(TTFont("ArialCustom-Bold", bold_path))
            font_set["bold"] = "ArialCustom-Bold"

        if os.path.exists(italic_path):
            pdfmetrics.registerFont(TTFont("ArialCustom-Italic", italic_path))
            font_set["italic"] = "ArialCustom-Italic"
    except Exception:
        pass

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


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(force=True)

    symptoms = data.get("symptoms", "")
    age = data.get("age", "")
    sex = data.get("sex", "")
    extra = data.get("extra", "")

    full_text = f"{symptoms} {extra}".strip()
    differential, clinical_output = rank_differential_diagnoses(full_text, diagnoses)

    semantic_query = f"{symptoms}. {extra}".strip()
    results = search_chunks(semantic_query, semantic_index, top_k=8) if semantic_index is not None else []

    return jsonify({
        "differential": differential[:5],
        "clinical_output": clinical_output,
        "results": results,
        "warning": "Instrument de suport pentru medic, bazat pe surse PDF. Nu stabilește autonom diagnosticul final."
    })


@app.route("/treatment", methods=["POST"])
def treatment():
    data = request.get_json(force=True)
    diagnosis_name = data.get("diagnosis", "")

    semantic_query = f"{diagnosis_name} tablou clinic tratament prevenție evitare alergen alergologie"
    source_results = search_chunks(semantic_query, semantic_index, top_k=5) if semantic_index is not None else []
    treatment_data = get_treatment_details(diagnosis_name, knowledge_ro)

    return jsonify({
        "diagnosis": treatment_data["diagnosis"],
        "clinical_picture": treatment_data["clinical_picture"],
        "treatment": treatment_data["treatment"],
        "prevention": treatment_data["prevention"],
        "allergen_avoidance": treatment_data["allergen_avoidance"],
        "source_results": source_results
    })


@app.route("/save_case", methods=["POST"])
def save_case():
    data = request.get_json(force=True)

    case_entry = {
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "patient_summary": data.get("patient_summary", {}),
        "analysis": data.get("analysis", {})
    }

    existing = []
    if os.path.exists(CASES_FILE):
        try:
            with open(CASES_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    existing.append(case_entry)

    with open(CASES_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    return jsonify({
        "message": "Caz salvat cu succes.",
        "count": len(existing),
        "path": CASES_FILE
    })


@app.route("/export_pdf", methods=["POST"])
def export_pdf():
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
            f"Sex: {patient.get('sex', '-')}",
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
    disclaimer = "Document orientativ. Nu înlocuiește consultul medical, examenul clinic și decizia terapeutică."
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)