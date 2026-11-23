import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.candidate import Resume
from app.models.resume_analysis import ResumeAnalysis


class RetrievedContext(BaseModel):
    formatted_context: str
    retrieved_sections: List[str] = Field(default_factory=list)
    evidence_snippets: List[str] = Field(default_factory=list)
    has_resume: bool = False
    has_m7_analysis: bool = False
    target_role: Optional[str] = None


class CareerRetrievalService:
    """
    Section-aware, bounded retrieval service for Career Assistant.
    Retrieves only relevant resume sections and M7 qualitative findings
    based on intent and query relevance.
    Does not require an external vector database.
    """

    SKILL_KEYWORDS = re.compile(r"\b(?:skill|skills|learn|learning|roadmap|tech|stack|tools|languages?|frameworks?|libraries)\b", re.IGNORECASE)
    PROJECT_KEYWORDS = re.compile(r"\b(?:project|projects|built|build|portfolio|app|system|api|architecture|github|code)\b", re.IGNORECASE)
    EXPERIENCE_KEYWORDS = re.compile(r"\b(?:work|experience|job|company|employer|role|responsibilities|impact|metrics|achievement)\b", re.IGNORECASE)
    INTERVIEW_KEYWORDS = re.compile(r"\b(?:interview|questions?|prepare|preparation|behavioral|star|technical\s+round|mock|answers?)\b", re.IGNORECASE)
    GAP_KEYWORDS = re.compile(r"\b(?:gap|gaps|missing|improve|improvement|backend|frontend|data\s+scientist|devops|full\s*stack|target)\b", re.IGNORECASE)

    def retrieve_context(
        self,
        query: str,
        resume: Optional[Resume] = None,
        m7_analysis: Optional[ResumeAnalysis] = None,
        conversation_purpose: Optional[str] = None,
        target_role: Optional[str] = None,
    ) -> RetrievedContext:
        """
        Builds a compact, bounded context payload grounded strictly in candidate assets.
        """
        if not resume:
            return RetrievedContext(
                formatted_context="[NO RESUME SELECTED]\nThe candidate has not attached a resume version. Provide general, professional, and objective career advice based on software engineering best practices. Do not invent or assume personal background.",
                retrieved_sections=["general_knowledge"],
                evidence_snippets=[],
                has_resume=False,
                has_m7_analysis=False,
                target_role=target_role,
            )

        parsed = resume.parsed_data or {}
        raw_text = resume.extracted_text or ""

        skills = parsed.get("skills") or []
        projects = parsed.get("projects") or []
        experience = parsed.get("experience") or []
        education = parsed.get("education") or []
        summary = parsed.get("professional_summary") or ""

        q_lower = query.lower()
        purpose = (conversation_purpose or "GENERAL").upper()

        # Determine section relevance
        wants_skills = bool(self.SKILL_KEYWORDS.search(q_lower)) or purpose == "SKILL_DEVELOPMENT"
        wants_projects = bool(self.PROJECT_KEYWORDS.search(q_lower)) or purpose == "PROJECT_DISCUSSION"
        wants_exp = bool(self.EXPERIENCE_KEYWORDS.search(q_lower)) or purpose == "RESUME_IMPROVEMENT"
        wants_interview = bool(self.INTERVIEW_KEYWORDS.search(q_lower)) or purpose == "INTERVIEW_PREP"
        wants_gaps = bool(self.GAP_KEYWORDS.search(q_lower)) or purpose in ("CAREER_GUIDANCE", "SKILL_DEVELOPMENT")

        # If general question or ambiguous, retrieve balanced context
        if not (wants_skills or wants_projects or wants_exp or wants_interview or wants_gaps):
            wants_skills = True
            wants_projects = True
            wants_exp = True

        sections_used: List[str] = []
        evidence_snippets: List[str] = []
        context_parts: List[str] = []

        context_parts.append(f"Candidate Resume Version: '{resume.original_filename}' (SHA-256: {resume.sha256[:12]}...)")
        if target_role:
            context_parts.append(f"Target Role: {target_role}")

        if summary:
            sections_used.append("summary")
            context_parts.append(f"Professional Summary: {summary.strip()}")

        # 1. Skills Section
        if wants_skills or wants_interview or wants_gaps:
            sections_used.append("skills")
            if skills:
                context_parts.append(f"Technical Skills Listed: {', '.join(skills)}")
                evidence_snippets.append(f"Technical skills: {', '.join(skills[:8])}")
            else:
                context_parts.append("Technical Skills: None explicitly listed.")

        # 2. Projects Section
        if wants_projects or wants_interview or wants_exp:
            sections_used.append("projects")
            if projects:
                proj_summaries = []
                for p in projects[:4]:
                    p_name = p.get("name") or "Technical Project"
                    p_desc = p.get("description") or "No detailed description provided."
                    p_techs = ", ".join(p.get("technologies") or [])
                    proj_summaries.append(f"- {p_name} ({p_techs}): {p_desc}")
                    evidence_snippets.append(f"Project: {p_name} ({p_techs})")
                context_parts.append("Key Projects:\n" + "\n".join(proj_summaries))
            else:
                context_parts.append("Projects: None listed in resume.")

        # 3. Work Experience Section
        if wants_exp or wants_interview or wants_gaps:
            sections_used.append("experience")
            if experience:
                exp_summaries = []
                for e in experience[:3]:
                    role = e.get("job_title") or "Role"
                    company = e.get("company") or "Company"
                    dates = f" ({e.get('start_date') or ''} - {e.get('end_date') or ''})".strip()
                    desc = e.get("description") or ""
                    exp_summaries.append(f"- {role} at {company}{dates}: {desc[:200]}")
                    evidence_snippets.append(f"Experience: {role} at {company}")
                context_parts.append("Employment History:\n" + "\n".join(exp_summaries))
            else:
                context_parts.append("Employment History: None listed in resume.")

        # 4. Education
        if education and (wants_exp or len(context_parts) < 3):
            sections_used.append("education")
            edu_summaries = []
            for ed in education[:2]:
                deg = ed.get("degree") or "Degree"
                inst = ed.get("institution") or "Institution"
                edu_summaries.append(f"- {deg} from {inst}")
            context_parts.append("Education:\n" + "\n".join(edu_summaries))

        # 5. M7 Qualitative Findings (if available)
        has_m7 = False
        if m7_analysis and m7_analysis.analysis_data:
            has_m7 = True
            sections_used.append("m7_analysis")
            m7_data = m7_analysis.analysis_data

            m7_parts = []
            if m7_data.get("overall_summary"):
                m7_parts.append(f"Resume Review Summary: {m7_data['overall_summary']}")

            skills_ana = m7_data.get("skills_analysis") or {}
            demo_skills = skills_ana.get("demonstrated_skills") or []
            limited_skills = skills_ana.get("skills_with_limited_evidence") or []
            if demo_skills:
                m7_parts.append(f"Contextually Demonstrated Skills: {', '.join(demo_skills)}")
                evidence_snippets.append(f"Demonstrated skills in projects: {', '.join(demo_skills[:5])}")
            if limited_skills:
                m7_parts.append(f"Skills With Limited Project Context: {', '.join(limited_skills)}")

            priorities = m7_data.get("improvement_priorities") or []
            if priorities:
                top_priority = priorities[0]
                m7_parts.append(f"Top Improvement Priority: {top_priority.get('issue')} - Suggested: {top_priority.get('suggested_action')}")
                evidence_snippets.append(f"Identified area to improve: {top_priority.get('issue')}")

            if m7_parts:
                context_parts.append("M7 Qualitative Analysis Findings:\n" + "\n".join(m7_parts))

        # Bound context length (2800 chars max)
        full_context = "\n\n".join(context_parts)
        if len(full_context) > 2800:
            full_context = full_context[:2800] + "\n...[Context truncated for brevity]"

        return RetrievedContext(
            formatted_context=full_context,
            retrieved_sections=sections_used,
            evidence_snippets=evidence_snippets[:6],
            has_resume=True,
            has_m7_analysis=has_m7,
            target_role=target_role,
        )


career_retrieval_service = CareerRetrievalService()
