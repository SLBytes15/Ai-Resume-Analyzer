import re
from typing import Any, Dict, List, Optional
from app.schemas.resume_analysis import (
    DeterministicChecksData,
    DeterministicFinding,
)


class DeterministicResumeChecker:
    """
    Evaluates purely text-based and structural aspects of a candidate resume.
    Does NOT require LLM inference.
    Never claims to assess visual layout, font choices, margins, or graphic aesthetics.
    """

    EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
    PHONE_REGEX = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
    LINKEDIN_REGEX = re.compile(r"linkedin\.com/in/[\w-]+", re.IGNORECASE)
    GITHUB_REGEX = re.compile(r"github\.com/[\w-]+", re.IGNORECASE)

    SECTION_PATTERNS = {
        "summary": re.compile(r"(?:professional\s+summary|executive\s+summary|summary|profile|about\s+me|objective)", re.IGNORECASE),
        "skills": re.compile(r"(?:technical\s+skills|core\s+skills|skills|technologies|proficiencies|competencies)", re.IGNORECASE),
        "experience": re.compile(r"(?:work\s+experience|professional\s+experience|employment\s+history|experience|work\s+history)", re.IGNORECASE),
        "projects": re.compile(r"(?:key\s+projects|personal\s+projects|academic\s+projects|projects)", re.IGNORECASE),
        "education": re.compile(r"(?:education|academic\s+background|academics|qualifications)", re.IGNORECASE),
        "certifications": re.compile(r"(?:certifications|certificates|licenses)", re.IGNORECASE),
    }

    MEASURABLE_REGEX = re.compile(
        r"(?:\b\d+(?:\.\d+)?%\s*(?:increase|reduction|growth|improvement|decrease|boost|faster|saving|saved)?|"
        r"\$\s*\d+(?:,\d{3})*(?:\.\d+)?(?:\s*[kKmMbB]|\s*million|\s*thousand)?|"
        r"\b\d+(?:,\d{3})*\+?\s*(?:users|clients|customers|requests|rps|qps|endpoints|transactions|nodes|services|records|lines|stars|downloads|subscribers|ms|milliseconds|seconds|minutes)\b)",
        re.IGNORECASE
    )

    def analyze(
        self,
        text: Optional[str],
        parsed_data: Optional[Dict[str, Any]] = None,
    ) -> DeterministicChecksData:
        clean_text = (text or "").strip()
        words = clean_text.split()
        word_count = len(words)
        char_count = len(clean_text)

        findings: List[DeterministicFinding] = []

        # 1. Text Length Assessment
        if word_count < 60:
            findings.append(
                DeterministicFinding(
                    category="TEXT_LENGTH",
                    level="WARNING",
                    message="Resume contains fewer than 60 words. This is unusually brief and may hinder recruiter evaluation.",
                )
            )
        elif word_count < 150:
            findings.append(
                DeterministicFinding(
                    category="TEXT_LENGTH",
                    level="ADVISORY",
                    message="Resume word count is relatively low (< 150 words). Adding technical project details is recommended.",
                )
            )
        elif word_count > 1200:
            findings.append(
                DeterministicFinding(
                    category="TEXT_LENGTH",
                    level="ADVISORY",
                    message="Resume exceeds 1,200 words. Consider condensing older roles or verbose descriptions to maintain recruiter focus.",
                )
            )

        # 2. Contact Information
        parsed_data = parsed_data or {}
        has_email = bool(parsed_data.get("email") or self.EMAIL_REGEX.search(clean_text))
        has_phone = bool(parsed_data.get("phone") or self.PHONE_REGEX.search(clean_text))
        has_linkedin = bool(self.LINKEDIN_REGEX.search(clean_text))
        has_github = bool(self.GITHUB_REGEX.search(clean_text))

        contact_info = {
            "has_email": has_email,
            "has_phone": has_phone,
            "has_linkedin": has_linkedin,
            "has_github": has_github,
        }

        if not has_email:
            findings.append(
                DeterministicFinding(
                    category="CONTACT_INFO",
                    level="WARNING",
                    message="No valid email address was identified. Recruiters need direct contact details.",
                )
            )
        if not has_phone:
            findings.append(
                DeterministicFinding(
                    category="CONTACT_INFO",
                    level="ADVISORY",
                    message="No telephone number was identified in the resume text.",
                )
            )

        # 3. Section Presence & Completeness
        detected_sections: List[str] = []
        missing_sections: List[str] = []
        empty_or_short_sections: List[str] = []

        lines = [line.strip() for line in clean_text.split("\n") if line.strip()]

        for sec_name, pattern in self.SECTION_PATTERNS.items():
            found_in_text = any(pattern.search(line) for line in lines)
            found_in_parsed = False
            if sec_name == "skills" and parsed_data.get("skills"):
                found_in_parsed = True
            elif sec_name == "experience" and parsed_data.get("experience"):
                found_in_parsed = True
            elif sec_name == "education" and parsed_data.get("education"):
                found_in_parsed = True
            elif sec_name == "projects" and parsed_data.get("projects"):
                found_in_parsed = True
            elif sec_name == "summary" and (parsed_data.get("professional_summary") or parsed_data.get("summary")):
                found_in_parsed = True
            elif sec_name == "certifications" and parsed_data.get("certifications"):
                found_in_parsed = True

            if found_in_text or found_in_parsed:
                detected_sections.append(sec_name)
            else:
                missing_sections.append(sec_name)

        if "skills" in missing_sections:
            findings.append(
                DeterministicFinding(
                    category="SECTIONS",
                    level="WARNING",
                    message="No dedicated Skills section was detected. A structured skills section helps recruiters quickly identify competencies.",
                )
            )
        if "experience" in missing_sections and "projects" in missing_sections:
            findings.append(
                DeterministicFinding(
                    category="SECTIONS",
                    level="WARNING",
                    message="Neither Work Experience nor Projects sections were identified. Technical evidence requires demonstrated work.",
                )
            )
        if "education" in missing_sections:
            findings.append(
                DeterministicFinding(
                    category="SECTIONS",
                    level="ADVISORY",
                    message="No Education section was clearly detected.",
                )
            )

        # 4. Project Descriptions Check
        parsed_projects = parsed_data.get("projects") or []
        projects_missing_desc: List[str] = []
        for p in parsed_projects:
            p_name = p.get("name") or "Unnamed Project"
            desc = (p.get("description") or "").strip()
            if len(desc) < 15:
                projects_missing_desc.append(p_name)

        if projects_missing_desc:
            empty_or_short_sections.append("projects_descriptions_missing")
            findings.append(
                DeterministicFinding(
                    category="PROJECTS",
                    level="WARNING",
                    message=f"Projects with limited or missing descriptions: {', '.join(projects_missing_desc)}. Add architecture, stack, and problem solved.",
                )
            )

        projects_assessment = {
            "total_projects_count": len(parsed_projects),
            "projects_missing_descriptions": projects_missing_desc,
        }

        # 5. Experience & Education Dates Assessment
        parsed_exp = parsed_data.get("experience") or []
        missing_dates_roles: List[str] = []
        for exp in parsed_exp:
            role = exp.get("job_title") or exp.get("company") or "Role"
            start_date = exp.get("start_date")
            end_date = exp.get("end_date")
            if not start_date and not end_date:
                missing_dates_roles.append(role)

        parsed_edu = parsed_data.get("education") or []
        missing_edu_dates: List[str] = []
        for edu in parsed_edu:
            inst = edu.get("institution") or edu.get("degree") or "Degree"
            if not edu.get("start_date") and not edu.get("end_date"):
                missing_edu_dates.append(inst)

        if missing_dates_roles:
            findings.append(
                DeterministicFinding(
                    category="DATES",
                    level="ADVISORY",
                    message=f"Incomplete dates detected for employment roles: {', '.join(missing_dates_roles)}.",
                )
            )

        dates_assessment = {
            "roles_missing_dates": missing_dates_roles,
            "education_missing_dates": missing_edu_dates,
        }

        # 6. Duplicated Content Check
        seen_chunks: Dict[str, int] = {}
        duplicates: List[str] = []
        for line in lines:
            normalized = " ".join(line.lower().split())
            if len(normalized) > 35:
                seen_chunks[normalized] = seen_chunks.get(normalized, 0) + 1
                if seen_chunks[normalized] == 2:
                    duplicates.append(line[:60])

        if duplicates:
            findings.append(
                DeterministicFinding(
                    category="CONTENT",
                    level="ADVISORY",
                    message=f"Potentially repeated sentences or bullet points detected ({len(duplicates)} instances). Review to avoid redundancy.",
                )
            )

        duplicated_content = {
            "has_duplicates": bool(duplicates),
            "duplicate_snippets": duplicates[:3],
        }

        # 7. Measurable Outcomes & Metrics Check
        metrics_matches = self.MEASURABLE_REGEX.findall(clean_text)
        has_metrics = len(metrics_matches) > 0
        sample_metrics = [m.strip() for m in metrics_matches[:5]]

        if not has_metrics:
            findings.append(
                DeterministicFinding(
                    category="METRICS",
                    level="ADVISORY",
                    message="No measurable outcomes or quantitative metrics (e.g. % performance improvement, latency reduction, user scale) were detected. Adding quantitative results significantly strengthens engineering resumes.",
                )
            )
        else:
            findings.append(
                DeterministicFinding(
                    category="METRICS",
                    level="INFO",
                    message=f"Detected {len(metrics_matches)} quantitative metric(s) or measurable outcome(s). Example: {sample_metrics[0]}",
                )
            )

        measurable_outcomes = {
            "has_metrics": has_metrics,
            "metrics_count": len(metrics_matches),
            "sample_metrics": sample_metrics,
        }

        return DeterministicChecksData(
            word_count=word_count,
            char_count=char_count,
            sections_detected=detected_sections,
            missing_sections=missing_sections,
            empty_or_short_sections=empty_or_short_sections,
            contact_info=contact_info,
            dates_assessment=dates_assessment,
            duplicated_content=duplicated_content,
            projects_assessment=projects_assessment,
            measurable_outcomes=measurable_outcomes,
            findings=findings,
        )


deterministic_checker = DeterministicResumeChecker()
