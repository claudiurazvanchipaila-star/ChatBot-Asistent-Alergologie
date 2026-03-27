import os
import json
from io import BytesIO
from datetime import datetime

from flask import Flask, request, jsonify, render_template, send_file
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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


def initialize_resources():
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

    return diagnoses, knowledge_ro


DIAGNOSES, KNOWLEDGE_RO = initialize_resources()


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


def draw_wrapped_text(pdf, text, x, y, max_width=500, line_height=14, font_name="Helvetica", font_size=10, color=colors.black):
    pdf.setFont(font_name, font_size)
    pdf.setFillColor(color)

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


def estimate_text_height(text, max_width=500, font_name="Helvetica", font_size=10, line_height=14):
    words = (text or "").split()
    if not words:
        return line_height

    line = ""
    lines = 0
    for word in words:
        test_line = f"{line} {word}".strip()
        if pdfmetrics.stringWidth(test_line, font_name, font_size) <= max_width:
            line = test_line
        else:
            lines += 1
            line = word

    if line:
        lines += 1

    return lines * line_height


def ensure_page_space(pdf, y, needed_height, page_height, top_margin=40, bottom_margin=50):
    if y - needed_height < bottom_margin:
        pdf.showPage()
        return page_height - top_margin
    return y


def draw_section_header(pdf, title, x, y, width, fonts):
    pdf.setFillColor(colors.HexColor("#EAF2F8"))
    pdf.roundRect(x, y - 18, width, 22, 6, fill=1, stroke=0)

    pdf.setFillColor(colors.HexColor("#154360"))
    pdf.setFont(fonts["bold"], 11)
    pdf.drawString(x + 10, y - 4, title)

    return y - 28


def draw_bullet_list(pdf, items, x, y, width, fonts, page_height):
    arr = items if isinstance(items, list) else []
    if not arr:
        y = ensure_page_space(pdf, y, 20, page_height)
        return draw_wrapped_text(
            pdf, "-",
            x, y,
            max_width=width,
            line_height=14,
            font_name=fonts["regular"],
            font_size=10,
            color=colors.black
        )

    for item in arr:
        item_text = f"• {str(item).strip()}"
        needed = estimate_text_height(
            item_text,
            max_width=width,
            font_name=fonts["regular"],
            font_size=10,
            line_height=14
        ) + 4
        y = ensure_page_space(pdf, y, needed, page_height)
        y = draw_wrapped_text(
            pdf,
            item_text,
            x,
            y,
            max_width=width,
            line_height=14,
            font_name=fonts["regular"],
            font_size=10,
            color=colors.black
        )
        y -= 2

    return y


def draw_key_value_lines(pdf, rows, x, y, width, fonts, page_height):
    for label, value in rows:
        text = f"{label}: {value or '-'}"
        needed = estimate_text_height(
            text,
            max_width=width,
            font_name=fonts["regular"],
            font_size=10,
            line_height=14
        ) + 4
        y = ensure_page_space(pdf, y, needed, page_height)
        y = draw_wrapped_text(
            pdf,
            text,
            x,
            y,
            max_width=width,
            line_height=14,
            font_name=fonts["regular"],
            font_size=10
        )
        y -= 2
    return y


def draw_summary_box(pdf, analysis, x, y, width, fonts, page_height):
    box_height = 88
    y = ensure_page_space(pdf, y, box_height + 10, page_height)

    pdf.setFillColor(colors.HexColor("#F4F8FB"))
    pdf.setStrokeColor(colors.HexColor("#D6E2EA"))
    pdf.roundRect(x, y - box_height, width, box_height, 10, fill=1, stroke=1)

    pdf.setFillColor(colors.HexColor("#154360"))
    pdf.setFont(fonts["bold"], 13)
    pdf.drawString(x + 12, y - 20, f"Diagnostic principal: {analysis.get('primary_diagnosis', '-')}")

    pdf.setFillColor(colors.black)
    pdf.setFont(fonts["regular"], 10)

    left_x = x + 12
    right_x = x + (width / 2)

    pdf.drawString(left_x, y - 40, f"Probabilitate: {analysis.get('primary_probability', '-')}")
    pdf.drawString(left_x, y - 56, f"Severitate: {analysis.get('severity', '-')}")
    pdf.drawString(right_x, y - 40, f"Grad de încredere: {analysis.get('confidence', '-')}")
    pdf.drawString(right_x, y - 56, f"Asociate: {', '.join(analysis.get('associated_diagnoses', [])[:2]) or '-'}")

    return y - box_height - 14


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
        "pdf_support": False,
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
        triggers = data.get("triggers", "")
        extra = data.get("extra", "")

        response_text = (
            f"Date primite cu succes.\n"
            f"Simptome: {symptoms or '-'}\n"
            f"Vârstă: {age or '-'}\n"
            f"Sex: {sex or '-'}\n"
            f"Greutate: {weight or '-'}\n"
            f"Context: {context or '-'}\n"
            f"Expuneri și factori declanșatori: {triggers or '-'}\n"
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
        triggers = str(data.get("triggers", "")).strip()
        extra = str(data.get("extra", "")).strip()

        full_text = " ".join(part for part in [symptoms, context, triggers, extra] if part).strip()

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
                "triggers": triggers,
                "extra": extra
            },
            "warning": (
                "Instrument de suport pentru medic, bazat pe logică clinică orientativă și pe datele introduse. "
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
        triggers = str(data.get("triggers", "")).strip()
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
        guideline_query = " ".join(part for part in [diagnosis_name, symptoms, context, triggers, extra] if part).strip()

        try:
            guideline_results = get_guideline_recommendations(
                diagnosis_name=diagnosis_name,
                symptoms=symptoms,
                context=context,
                triggers=triggers,
                extra=extra,
                severity=severity,
                age=age,
                weight=weight,
                query=guideline_query
            ) or []
        except Exception as e:
            print(f"[EROARE] get_guideline_recommendations: {e}")
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
                    "dose_child": med.get("dose_child", ""),
                    "dose_adult": med.get("dose_adult", ""),
                    "dose": med.get("dose", ""),
                    "route": med.get("route", ""),
                    "frequency": med.get("frequency", ""),
                    "duration": med.get("duration", ""),
                    "notes": med.get("notes", ""),
                    "adverse_reactions": med.get("adverse_reactions", "")
                })

                label_parts = [
                    med.get("class", ""),
                    med.get("name", ""),
                    med.get("dose_adult", "") or med.get("dose", "")
                ]
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
            "context_used": context,
            "triggers_used": triggers,
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
        page_width, page_height = A4

        left = 40
        content_width = page_width - 80
        y = page_height - 42

        pdf.setTitle("Raport orientativ alergologie")

        pdf.setFillColor(colors.HexColor("#0F5F87"))
        pdf.roundRect(left, y - 26, content_width, 34, 10, fill=1, stroke=0)

        pdf.setFillColor(colors.white)
        pdf.setFont(fonts["bold"], 16)
        pdf.drawString(left + 14, y - 5, "Raport orientativ - Asistent clinic în alergologie")

        y -= 42
        pdf.setFillColor(colors.HexColor("#5B6B7A"))
        pdf.setFont(fonts["regular"], 9)
        pdf.drawString(left, y, f"Data generării: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        y -= 16

        y = draw_summary_box(pdf, analysis, left, y, content_width, fonts, page_height)

        patient_rows = [
            ("Simptome", patient.get("symptoms", "-")),
            ("Vârstă", patient.get("age", "-")),
            ("Greutate", patient.get("weight", "-")),
            ("Sex", patient.get("sex", "-")),
            ("Context clinic", patient.get("context", "-")),
            ("Expuneri și factori declanșatori", patient.get("triggers", "-")),
            ("Alte date clinice", patient.get("extra", "-")),
        ]

        sections = [
            ("Date introduse", patient_rows, "key_value"),
            ("Diagnostice alternative", analysis.get("alternatives", []), "list"),
            ("Elemente care susțin diagnosticul", analysis.get("supports", []), "list"),
            ("Elemente de interpretat cu prudență", analysis.get("limits", []), "list"),
            ("Investigații recomandate", analysis.get("recommended_tests", []), "list"),
            ("Conduită orientativă", analysis.get("treatment_plan", []), "list"),
            ("Red flags", analysis.get("red_flags", []), "list"),
            ("Note clinice", analysis.get("notes", []), "list"),
        ]

        for title, content, block_type in sections:
            estimated = 40
            if block_type == "key_value":
                estimated += len(content) * 18
            else:
                estimated += max(1, len(content)) * 18

            y = ensure_page_space(pdf, y, estimated, page_height)
            y = draw_section_header(pdf, title, left, y, content_width, fonts)

            if block_type == "key_value":
                y = draw_key_value_lines(pdf, content, left + 8, y, content_width - 16, fonts, page_height)
            else:
                y = draw_bullet_list(pdf, content, left + 8, y, content_width - 16, fonts, page_height)

            y -= 10

        disclaimer_box_height = 52
        y = ensure_page_space(pdf, y, disclaimer_box_height + 10, page_height)

        pdf.setFillColor(colors.HexColor("#FFF7E6"))
        pdf.setStrokeColor(colors.HexColor("#E7C978"))
        pdf.roundRect(left, y - disclaimer_box_height, content_width, disclaimer_box_height, 8, fill=1, stroke=1)

        pdf.setFillColor(colors.HexColor("#8A5A00"))
        pdf.setFont(fonts["italic"], 9)
        disclaimer = (
            "Document orientativ. Nu înlocuiește consultul medical, examenul clinic și decizia terapeutică. "
            "Dozele medicamentoase trebuie verificate în funcție de produs, greutate, vârstă și severitate."
        )
        draw_wrapped_text(
            pdf,
            disclaimer,
            left + 10,
            y - 16,
            max_width=content_width - 20,
            line_height=12,
            font_name=fonts["italic"],
            font_size=9,
            color=colors.HexColor("#8A5A00")
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