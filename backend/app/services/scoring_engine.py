from typing import Any, Dict, List, Optional, Tuple
from app.services.skill_normalizer import NORMALIZATION_VERSION, skill_normalizer

SCORING_ALGORITHM_VERSION = "v1.0.0"

DEFAULT_WEIGHTS = {
    "required_skills": 0.60,
    "preferred_skills": 0.15,
    "experience": 0.25,
}


class ScoringEngineError(Exception):
    pass


class ScoringEngine:
    """Pure Python deterministic, reproducible candidate screening scoring engine."""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        self._validate_weights()

    def _validate_weights(self) -> None:
        total = (
            self.weights.get("required_skills", 0.0)
            + self.weights.get("preferred_skills", 0.0)
            + self.weights.get("experience", 0.0)
        )
        if abs(total - 1.0) > 1e-6:
            raise ScoringEngineError(f"Scoring weights must sum to 1.0 (got {total:.4f})")

    def get_scoring_config(self) -> Dict[str, Any]:
        """Return snapshot of the active scoring configuration."""
        return {
            "algorithm_version": SCORING_ALGORITHM_VERSION,
            "normalization_version": NORMALIZATION_VERSION,
            "weights": self.weights,
            "rules": {
                "required_skills_formula": "count(matched_required) / count(total_required) * 100",
                "preferred_skills_formula": "count(matched_preferred) / count(total_preferred) * 100 if preferred else 100",
                "unknown_experience_policy": "neutral_baseline_50_with_project_credit",
            },
        }

    def evaluate_skills(
        self,
        job_skills: List[str],
        evidenced_skills: List[Dict[str, Any]],
    ) -> Tuple[float, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Match job skills against evidenced candidate skills.
        Returns (score [0-100], matched_items, missing_items).
        """
        if not job_skills:
            return 100.0, [], []

        matched: List[Dict[str, Any]] = []
        missing: List[Dict[str, Any]] = []

        # Map evidenced skills by canonical name
        evidence_by_canon: Dict[str, Dict[str, Any]] = {}
        for ev in evidenced_skills:
            raw = ev.get("skill") or ev.get("canonical_skill") or ""
            canon, _ = skill_normalizer.normalize_skill(raw)
            if canon and canon.lower() not in evidence_by_canon:
                evidence_by_canon[canon.lower()] = ev

        for req in job_skills:
            canon_req, original_req = skill_normalizer.normalize_skill(req)
            if not canon_req:
                continue

            match_found = False
            for cand_lower, ev_item in evidence_by_canon.items():
                if skill_normalizer.are_skills_matching(canon_req, cand_lower):
                    matched.append({
                        "skill": original_req,
                        "canonical_skill": canon_req,
                        "evidence": ev_item.get("evidence", "Mentioned in resume"),
                        "evidence_type": ev_item.get("evidence_type", "RESUME"),
                        "confidence": ev_item.get("confidence", 1.0),
                    })
                    match_found = True
                    break

            if not match_found:
                missing.append({
                    "skill": original_req,
                    "canonical_skill": canon_req,
                    "reason": "Not evidenced in submitted resume",
                })

        score = (len(matched) / len(job_skills)) * 100.0
        return round(score, 2), matched, missing

    def evaluate_experience(
        self,
        experience_min: Optional[int],
        experience_max: Optional[int],
        extracted_experience: List[Dict[str, Any]],
        extracted_projects: List[Dict[str, Any]],
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate deterministic experience score with honest handling of unknown dates.
        Returns (experience_score [0-100], assessment_dict).
        """
        # Calculate documented professional years
        verified_years = 0.0
        dates_present = False
        roles_summary = []

        for exp in extracted_experience:
            role = exp.get("role") or "Role"
            company = exp.get("company") or "Company"
            roles_summary.append(f"{role} at {company}")
            # Years stated or calculated
            yrs = exp.get("years")
            if yrs is not None and isinstance(yrs, (int, float)) and yrs > 0:
                verified_years += float(yrs)
                dates_present = True
            elif exp.get("start_date") or exp.get("end_date"):
                dates_present = True
                # Minimum 1 year if dates indicated without detailed duration
                verified_years += 1.0

        project_count = len(extracted_projects)
        min_required = experience_min or 0

        # Scenario 1: Job does not require minimum experience
        if min_required == 0:
            exp_score = 100.0 if (verified_years > 0 or project_count > 0) else 85.0
            status_desc = "Requirements met (Entry level or no minimum experience specified)"
            return round(exp_score, 2), {
                "status": "SUFFICIENT",
                "verified_years": round(verified_years, 1),
                "required_min_years": min_required,
                "project_count": project_count,
                "roles": roles_summary,
                "note": status_desc,
            }

        # Scenario 2: Dates are missing or unclear across all roles
        if not dates_present and verified_years == 0.0:
            # Neutral baseline policy: 50 base points + credit for documented projects (up to 75)
            project_bonus = min(project_count * 10.0, 25.0)
            exp_score = 50.0 + project_bonus
            return round(exp_score, 2), {
                "status": "UNKNOWN_DATES",
                "verified_years": None,
                "required_min_years": min_required,
                "project_count": project_count,
                "roles": roles_summary,
                "note": "Employment dates are not clearly specified in the resume. Scored using neutral baseline with project evidence.",
            }

        # Scenario 3: Candidate has documented experience >= required minimum
        if verified_years >= min_required:
            exp_score = 100.0
            status_desc = f"Candidate has {verified_years:.1f} verified years (meets or exceeds required {min_required} years)"
            return round(exp_score, 2), {
                "status": "VERIFIED_SUFFICIENT",
                "verified_years": round(verified_years, 1),
                "required_min_years": min_required,
                "project_count": project_count,
                "roles": roles_summary,
                "note": status_desc,
            }

        # Scenario 4: Partial verified experience < required minimum
        ratio = (verified_years / min_required) * 100.0
        # Project and internship bonus (up to 20 additional points, capped at 90.0 since minimum wasn't fully met)
        project_credit = min(project_count * 5.0, 20.0)
        exp_score = min(ratio + project_credit, 90.0)
        status_desc = f"Candidate has {verified_years:.1f} of {min_required} required years with {project_count} supporting projects."

        return round(exp_score, 2), {
            "status": "PARTIAL",
            "verified_years": round(verified_years, 1),
            "required_min_years": min_required,
            "project_count": project_count,
            "roles": roles_summary,
            "note": status_desc,
        }

    def generate_explanation(
        self,
        total_score: float,
        req_score: float,
        pref_score: float,
        exp_score: float,
        matched_required: List[Dict[str, Any]],
        missing_required: List[Dict[str, Any]],
        matched_preferred: List[Dict[str, Any]],
        exp_assessment: Dict[str, Any],
    ) -> str:
        """Construct grounded, factual, explainable explanation text."""
        parts = [
            f"Overall Decision-Support Score: {total_score:.1f}/100.",
            f"Component breakdown: Required Skills ({req_score:.1f}%, weight 60%), "
            f"Preferred Skills ({pref_score:.1f}%, weight 15%), "
            f"Experience ({exp_score:.1f}%, weight 25%).",
        ]

        # Required skills narrative
        if matched_required:
            skills_list = ", ".join(m["skill"] for m in matched_required)
            parts.append(f"Evidenced required skills ({len(matched_required)}): {skills_list}.")
        else:
            parts.append("No required skills were evidenced in the submitted resume.")

        if missing_required:
            missing_list = ", ".join(m["skill"] for m in missing_required)
            parts.append(f"Required skills not evidenced ({len(missing_required)}): {missing_list}.")

        # Preferred skills narrative
        if matched_preferred:
            pref_list = ", ".join(m["skill"] for m in matched_preferred)
            parts.append(f"Evidenced preferred skills ({len(matched_preferred)}): {pref_list}.")

        # Experience narrative
        exp_note = exp_assessment.get("note", "")
        if exp_note:
            parts.append(f"Experience assessment: {exp_note}")

        parts.append(
            "Note: This score is an automated decision-support signal based on resume text evidence. "
            "Missing evidence does not establish that a candidate lacks a capability."
        )

        return " ".join(parts)

    def calculate_screening_score(
        self,
        required_skills: List[str],
        preferred_skills: List[str],
        experience_min: Optional[int],
        experience_max: Optional[int],
        evidenced_skills: List[Dict[str, Any]],
        extracted_experience: List[Dict[str, Any]],
        extracted_projects: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Execute full deterministic score calculation.
        """
        req_score, matched_req, missing_req = self.evaluate_skills(required_skills, evidenced_skills)
        pref_score, matched_pref, missing_pref = self.evaluate_skills(preferred_skills, evidenced_skills)
        exp_score, exp_assessment = self.evaluate_experience(
            experience_min, experience_max, extracted_experience, extracted_projects
        )

        w_req = self.weights["required_skills"]
        w_pref = self.weights["preferred_skills"]
        w_exp = self.weights["experience"]

        total_score = (req_score * w_req) + (pref_score * w_pref) + (exp_score * w_exp)
        total_score = round(min(max(total_score, 0.0), 100.0), 2)

        explanation = self.generate_explanation(
            total_score=total_score,
            req_score=req_score,
            pref_score=pref_score,
            exp_score=exp_score,
            matched_required=matched_req,
            missing_required=missing_req,
            matched_preferred=matched_pref,
            exp_assessment=exp_assessment,
        )

        # Confidence level calculation
        confidence = "HIGH"
        if exp_assessment.get("status") == "UNKNOWN_DATES":
            confidence = "MEDIUM"
        if len(evidenced_skills) == 0 and len(extracted_experience) == 0:
            confidence = "LOW"

        return {
            "total_score": total_score,
            "required_skill_score": req_score,
            "preferred_skill_score": pref_score,
            "experience_score": exp_score,
            "matched_skills": matched_req,
            "missing_evidence": missing_req,
            "preferred_skill_matches": matched_pref,
            "experience_assessment": exp_assessment,
            "explanation": explanation,
            "confidence_level": confidence,
            "scoring_config": self.get_scoring_config(),
        }


scoring_engine = ScoringEngine()
