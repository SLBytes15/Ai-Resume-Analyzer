import os
import json
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor

def load_json_profile(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def create_resume_pdf(profile_data, output_path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )
    story = []
    PRIMARY_COLOR = HexColor("#1A365D")
    TEXT_COLOR = HexColor("#2D3748")
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=24, leading=28, textColor=PRIMARY_COLOR)
    subtitle_style = ParagraphStyle('Sub', parent=styles['Heading3'], fontName='Helvetica', fontSize=12, leading=16, textColor=TEXT_COLOR)
    section_heading = ParagraphStyle('Sec', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=PRIMARY_COLOR, spaceBefore=12, spaceAfter=4)
    body_style = ParagraphStyle('Body', parent=styles['BodyText'], fontName='Helvetica', fontSize=10, leading=14, textColor=TEXT_COLOR, spaceAfter=6)

    story.append(Paragraph(profile_data.get("candidate_name", "John Doe"), title_style))
    story.append(Paragraph(f"<b>Role:</b> {profile_data.get('current_role')} | <b>Experience:</b> {profile_data.get('years_of_experience')}", subtitle_style))
    story.append(Paragraph(f"<b>Education:</b> {profile_data.get('education')}", subtitle_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Professional Summary", section_heading))
    story.append(Paragraph(profile_data.get("summary", ""), body_style))
    
    story.append(Paragraph("Core Technical Expertise", section_heading))
    skills = profile_data.get("top_skills", profile_data.get("skills", []))
    story.append(Paragraph(", ".join(skills), body_style))
    
    story.append(Paragraph("Professional Work History", section_heading))
    exp_text = f"Executed operational initiatives as an expert {profile_data.get('current_role')}. Managed localized workflows utilizing industry standard safety protocols and fast-paced team coordination."
    story.append(Paragraph(exp_text, body_style))

    doc.build(story)

def build_pdf_dataset(profiles_dir="../candidate_profiles", output_dir="../data/resumes"):
    profiles_path = Path(profiles_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    json_profiles = list(profiles_path.glob("*.json"))
    print(f"--- Checking for missing PDF profiles ---")
    
    for json_file in json_profiles:
        resume_id = json_file.stem
        pdf_filename = output_path / f"{resume_id}.pdf"
        
        # Incremental check: Only build if the PDF doesn't exist
        if not pdf_filename.exists():
            profile_data = load_json_profile(json_file)
            create_resume_pdf(profile_data, pdf_filename)
            print(f"  ✓ Successfully compiled missing asset: {pdf_filename.name}")
        else:
            print(f"  · Skipping {pdf_filename.name} (Already exists)")

if __name__ == "__main__":
    build_pdf_dataset()