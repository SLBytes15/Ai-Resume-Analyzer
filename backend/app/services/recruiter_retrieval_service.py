import logging
import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Application, ApplicationStatus, ApplicationStatusHistory
from app.models.candidate import CandidateProfile, Resume
from app.models.job import Job, JobStatus
from app.models.screening import ScreeningInsight, ScreeningResult, ScreeningRun, ScreeningRunStatus

logger = logging.getLogger(__name__)


class QueryIntent(str, Enum):
    HIRING_OVERVIEW = "HIRING_OVERVIEW"
    JOB_SUMMARY = "JOB_SUMMARY"
    APPLICATION_STATUS_SUMMARY = "APPLICATION_STATUS_SUMMARY"
    SCREENING_SUMMARY = "SCREENING_SUMMARY"
    CANDIDATE_EVIDENCE = "CANDIDATE_EVIDENCE"
    CANDIDATE_COMPARISON = "CANDIDATE_COMPARISON"
    SKILL_DISTRIBUTION = "SKILL_DISTRIBUTION"
    RECRUITMENT_PIPELINE = "RECRUITMENT_PIPELINE"
    GENERAL_RECRUITMENT_QUESTION = "GENERAL_RECRUITMENT_QUESTION"


@dataclass
class RetrievedHiringContext:
    intent: QueryIntent
    formatted_context: str
    sources_used: List[str] = field(default_factory=list)
    retrieved_job_ids: List[str] = field(default_factory=list)
    retrieved_app_ids: List[str] = field(default_factory=list)
    screening_run_ids: List[str] = field(default_factory=list)
    evidence_snippets: List[str] = field(default_factory=list)
    structured_data: Dict[str, Any] = field(default_factory=dict)


class RecruiterRetrievalService:
    """
    Organization-aware, allowlisted retrieval engine for Recruiter AI Assistant.
    Retrieves authorized hiring data directly from PostgreSQL using structured queries.
    Never executes arbitrary or unvetted SQL.
    """

    COMPARISON_REGEX = re.compile(r"\b(compare|comparison|versus|vs|top\s+\d+|who\s+are\s+the\s+top|rank(?:ed|ing)?)\b", re.IGNORECASE)
    EVIDENCE_REGEX = re.compile(r"\b(why\s+did|candidate|applicant|evidence|score\s+breakdown|projects?\s+demonstrate|missing\s+in\s+this|resume\s+evidence|why\s+this\s+score)\b", re.IGNORECASE)
    SCREENING_REGEX = re.compile(r"\b(screening|screened|score\s+summary|scores|screening\s+results?|evaluat(?:ed|ion))\b", re.IGNORECASE)
    SKILL_REGEX = re.compile(r"\b(skill\s+distribution|common\s+skills|frequent\s+skills|missing\s+requirements?|frequently\s+missing)\b", re.IGNORECASE)
    PIPELINE_REGEX = re.compile(r"\b(pipeline|awaiting|under\s+review|shortlist(?:ed)?|hired|rejected|withdrawn|status\s+changes?)\b", re.IGNORECASE)
    JOB_REGEX = re.compile(r"\b(job|role|position|requisition|backend|frontend|engineer|developer|designer|manager)\b", re.IGNORECASE)
    OVERVIEW_REGEX = re.compile(r"\b(overview|how\s+many|total\s+applicants?|active\s+jobs?|published\s+jobs?|hiring\s+activity|summary\s+of\s+our\s+hiring|metrics)\b", re.IGNORECASE)

    def classify_intent(
        self,
        query: str,
        job_id: Optional[uuid.UUID] = None,
        application_id: Optional[uuid.UUID] = None,
    ) -> QueryIntent:
        """Classify recruiter query into an allowlisted query intent."""
        if application_id:
            return QueryIntent.CANDIDATE_EVIDENCE

        q_lower = query.lower()

        if self.COMPARISON_REGEX.search(q_lower):
            return QueryIntent.CANDIDATE_COMPARISON

        if self.EVIDENCE_REGEX.search(q_lower) and any(kw in q_lower for kw in ["why", "evidence", "experience", "projects", "missing"]):
            return QueryIntent.CANDIDATE_EVIDENCE

        if self.SKILL_REGEX.search(q_lower):
            return QueryIntent.SKILL_DISTRIBUTION

        if self.SCREENING_REGEX.search(q_lower):
            return QueryIntent.SCREENING_SUMMARY

        if self.PIPELINE_REGEX.search(q_lower):
            return QueryIntent.RECRUITMENT_PIPELINE

        if job_id or (self.JOB_REGEX.search(q_lower) and "summar" in q_lower):
            return QueryIntent.JOB_SUMMARY

        if self.OVERVIEW_REGEX.search(q_lower):
            return QueryIntent.HIRING_OVERVIEW

        # Default to hiring overview if asking broad metrics, else general recruitment
        if any(w in q_lower for w in ["count", "how many", "status", "distribution"]):
            return QueryIntent.HIRING_OVERVIEW

        return QueryIntent.GENERAL_RECRUITMENT_QUESTION

    async def retrieve_context(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        query: str,
        job_id: Optional[uuid.UUID] = None,
        application_id: Optional[uuid.UUID] = None,
    ) -> RetrievedHiringContext:
        """
        Orchestrates safe, allowlisted SQL retrieval based on classified query intent.
        All queries are strictly tenant-isolated to organization_id.
        """
        intent = self.classify_intent(query, job_id=job_id, application_id=application_id)

        if intent == QueryIntent.HIRING_OVERVIEW:
            return await self._get_hiring_overview(db, organization_id)

        elif intent == QueryIntent.JOB_SUMMARY:
            return await self._get_job_summary(db, organization_id, query, job_id)

        elif intent == QueryIntent.APPLICATION_STATUS_SUMMARY or intent == QueryIntent.RECRUITMENT_PIPELINE:
            return await self._get_recruitment_pipeline(db, organization_id, job_id)

        elif intent == QueryIntent.SCREENING_SUMMARY:
            return await self._get_screening_summary(db, organization_id, query, job_id)

        elif intent == QueryIntent.CANDIDATE_EVIDENCE:
            return await self._get_candidate_evidence(db, organization_id, query, application_id, job_id)

        elif intent == QueryIntent.CANDIDATE_COMPARISON:
            return await self._get_candidate_comparison(db, organization_id, query, job_id)

        elif intent == QueryIntent.SKILL_DISTRIBUTION:
            return await self._get_skill_distribution(db, organization_id, query, job_id)

        else:
            # Fallback to hiring overview with general context
            overview = await self._get_hiring_overview(db, organization_id)
            overview.intent = QueryIntent.GENERAL_RECRUITMENT_QUESTION
            return overview

    async def _get_hiring_overview(
        self, db: AsyncSession, organization_id: uuid.UUID
    ) -> RetrievedHiringContext:
        """Calculate organization-level hiring metrics and distributions."""
        # 1. Job statistics
        jobs_stmt = select(Job.status, func.count(Job.id)).where(
            Job.organization_id == organization_id
        ).group_by(Job.status)
        jobs_res = await db.execute(jobs_stmt)
        job_status_counts = {status: count for status, count in jobs_res.all()}
        total_jobs = sum(job_status_counts.values())
        published_jobs = job_status_counts.get(JobStatus.PUBLISHED.value, 0)
        draft_jobs = job_status_counts.get(JobStatus.DRAFT.value, 0)
        closed_jobs = job_status_counts.get(JobStatus.CLOSED.value, 0)

        # 2. Application statistics
        apps_stmt = select(Application.status, func.count(Application.id)).where(
            Application.organization_id == organization_id
        ).group_by(Application.status)
        apps_res = await db.execute(apps_stmt)
        app_status_counts = {status: count for status, count in apps_res.all()}
        total_apps = sum(app_status_counts.values())

        # 3. Top jobs by application volume
        top_jobs_stmt = (
            select(Job.id, Job.title, func.count(Application.id).label("app_count"))
            .outerjoin(Application, Application.job_id == Job.id)
            .where(Job.organization_id == organization_id)
            .group_by(Job.id, Job.title)
            .order_by(desc("app_count"))
            .limit(5)
        )
        top_jobs_res = await db.execute(top_jobs_stmt)
        top_jobs = [{"job_id": str(r[0]), "title": r[1], "applicants": r[2]} for r in top_jobs_res.all()]

        # 4. Jobs with 0 applications
        zero_apps_jobs = [j["title"] for j in top_jobs if j["applicants"] == 0]

        # Format context
        lines = [
            "### Verified Organization Hiring Overview:",
            f"- **Total Jobs**: {total_jobs} ({published_jobs} Published, {draft_jobs} Draft, {closed_jobs} Closed)",
            f"- **Total Applications**: {total_apps}",
            "- **Applications by Status**:",
        ]
        for st, count in sorted(app_status_counts.items()):
            lines.append(f"  • {st.replace('_', ' ').title()}: {count}")

        if top_jobs:
            lines.append("- **Top Jobs by Application Volume**:")
            for j in top_jobs:
                lines.append(f"  • {j['title']}: {j['applicants']} applicant(s)")

        if zero_apps_jobs:
            lines.append(f"- **Jobs Awaiting Applications**: {', '.join(zero_apps_jobs)}")

        structured = {
            "total_jobs": total_jobs,
            "published_jobs": published_jobs,
            "draft_jobs": draft_jobs,
            "total_applications": total_apps,
            "applications_by_status": app_status_counts,
            "top_jobs": top_jobs,
        }

        return RetrievedHiringContext(
            intent=QueryIntent.HIRING_OVERVIEW,
            formatted_context="\n".join(lines),
            sources_used=["Organization Jobs Table", "Organization Applications Table"],
            retrieved_job_ids=[j["job_id"] for j in top_jobs],
            structured_data=structured,
            evidence_snippets=[f"Total Applications: {total_apps}", f"Published Jobs: {published_jobs}"],
        )

    async def _get_job_summary(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        query: str,
        job_id: Optional[uuid.UUID],
    ) -> RetrievedHiringContext:
        """Fetch details for a specific job and its current applicant pool."""
        job = await self._resolve_job(db, organization_id, query, job_id)
        if not job:
            return RetrievedHiringContext(
                intent=QueryIntent.JOB_SUMMARY,
                formatted_context="No matching job found in your organization.",
                sources_used=["Organization Jobs Table"],
            )

        # Application counts for this job
        apps_stmt = select(Application.status, func.count(Application.id)).where(
            Application.job_id == job.id,
            Application.organization_id == organization_id,
        ).group_by(Application.status)
        apps_res = await db.execute(apps_stmt)
        status_counts = {st: cnt for st, cnt in apps_res.all()}
        total_apps = sum(status_counts.values())

        # Check latest screening run
        run_stmt = (
            select(ScreeningRun)
            .where(ScreeningRun.job_id == job.id, ScreeningRun.organization_id == organization_id)
            .order_by(desc(ScreeningRun.created_at))
            .limit(1)
        )
        run_res = await db.execute(run_stmt)
        latest_run = run_res.scalar_one_or_none()

        lines = [
            f"### Verified Job Summary: {job.title}",
            f"- **Status**: {job.status}",
            f"- **Department**: {job.department or 'General'}",
            f"- **Experience Requirement**: {job.experience_min} to {job.experience_max or '+'} years",
            f"- **Required Skills**: {', '.join(job.required_skills) if job.required_skills else 'None specified'}",
            f"- **Preferred Skills**: {', '.join(job.preferred_skills) if job.preferred_skills else 'None specified'}",
            f"- **Total Applicants**: {total_apps}",
        ]
        if status_counts:
            lines.append("- **Applicant Status Breakdown**:")
            for st, cnt in status_counts.items():
                lines.append(f"  • {st.replace('_', ' ').title()}: {cnt}")

        screening_run_ids = []
        if latest_run:
            screening_run_ids.append(str(latest_run.id))
            lines.append(
                f"- **Latest Screening Run**: Status {latest_run.status}, Screened {latest_run.processed_applications} of {latest_run.total_applications} applicants"
            )
        else:
            lines.append("- **Screening**: No screening runs executed for this job yet.")

        structured = {
            "job_id": str(job.id),
            "title": job.title,
            "status": job.status,
            "required_skills": job.required_skills,
            "preferred_skills": job.preferred_skills,
            "total_applications": total_apps,
            "status_counts": status_counts,
            "has_screening_run": latest_run is not None,
        }

        return RetrievedHiringContext(
            intent=QueryIntent.JOB_SUMMARY,
            formatted_context="\n".join(lines),
            sources_used=["Jobs Table", "Applications Table"] + (["ScreeningRuns Table"] if latest_run else []),
            retrieved_job_ids=[str(job.id)],
            screening_run_ids=screening_run_ids,
            structured_data=structured,
            evidence_snippets=[f"{job.title}: {total_apps} applicants, {len(job.required_skills or [])} required skills"],
        )

    async def _get_recruitment_pipeline(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        job_id: Optional[uuid.UUID],
    ) -> RetrievedHiringContext:
        """Fetch recruitment pipeline status and recent transition activity."""
        base_where = [Application.organization_id == organization_id]
        if job_id:
            base_where.append(Application.job_id == job_id)

        stmt = select(Application.status, func.count(Application.id)).where(*base_where).group_by(Application.status)
        res = await db.execute(stmt)
        status_map = {st: cnt for st, cnt in res.all()}

        # Recent status history changes
        history_stmt = (
            select(
                ApplicationStatusHistory.previous_status,
                ApplicationStatusHistory.new_status,
                ApplicationStatusHistory.changed_at,
                Job.title,
            )
            .join(Application, Application.id == ApplicationStatusHistory.application_id)
            .join(Job, Job.id == Application.job_id)
            .where(Application.organization_id == organization_id)
            .order_by(desc(ApplicationStatusHistory.changed_at))
            .limit(5)
        )
        hist_res = await db.execute(history_stmt)
        recent_changes = [
            f"{r[3]}: {r[0]} → {r[1]} ({r[2].strftime('%Y-%m-%d %H:%M')})"
            for r in hist_res.all()
        ]

        lines = [
            "### Verified Recruitment Pipeline Status:",
            f"- **Awaiting Initial Review (SUBMITTED)**: {status_map.get(ApplicationStatus.SUBMITTED.value, 0)}",
            f"- **Under Active Review**: {status_map.get(ApplicationStatus.UNDER_REVIEW.value, 0)}",
            f"- **Shortlisted**: {status_map.get(ApplicationStatus.SHORTLISTED.value, 0)}",
            f"- **Hired**: {status_map.get(ApplicationStatus.HIRED.value, 0)}",
            f"- **Rejected**: {status_map.get(ApplicationStatus.REJECTED.value, 0)}",
            f"- **Withdrawn by Candidate**: {status_map.get(ApplicationStatus.WITHDRAWN.value, 0)}",
        ]
        if recent_changes:
            lines.append("- **Recent Pipeline Transitions**:")
            for chg in recent_changes:
                lines.append(f"  • {chg}")

        structured = {
            "status_distribution": status_map,
            "awaiting_review": status_map.get(ApplicationStatus.SUBMITTED.value, 0),
            "shortlisted": status_map.get(ApplicationStatus.SHORTLISTED.value, 0),
            "recent_changes": recent_changes,
        }

        return RetrievedHiringContext(
            intent=QueryIntent.RECRUITMENT_PIPELINE,
            formatted_context="\n".join(lines),
            sources_used=["Applications Table", "ApplicationStatusHistory Table"],
            structured_data=structured,
            evidence_snippets=[f"Awaiting review: {status_map.get(ApplicationStatus.SUBMITTED.value, 0)}", f"Shortlisted: {status_map.get(ApplicationStatus.SHORTLISTED.value, 0)}"],
        )

    async def _get_screening_summary(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        query: str,
        job_id: Optional[uuid.UUID],
    ) -> RetrievedHiringContext:
        """Fetch screening statistics and top results for a job."""
        job = await self._resolve_job(db, organization_id, query, job_id)
        if not job:
            return RetrievedHiringContext(
                intent=QueryIntent.SCREENING_SUMMARY,
                formatted_context="Please specify a job to view screening results.",
                sources_used=["Jobs Table"],
            )

        # Get latest screening run
        run_stmt = (
            select(ScreeningRun)
            .where(ScreeningRun.job_id == job.id, ScreeningRun.organization_id == organization_id)
            .order_by(desc(ScreeningRun.created_at))
            .limit(1)
        )
        run_res = await db.execute(run_stmt)
        run = run_res.scalar_one_or_none()

        if not run:
            return RetrievedHiringContext(
                intent=QueryIntent.SCREENING_SUMMARY,
                formatted_context=f"No screening runs found for job '{job.title}'. Recruiters can trigger screening from the Job Screening dashboard.",
                sources_used=["ScreeningRuns Table"],
                retrieved_job_ids=[str(job.id)],
            )

        # Fetch top results
        results_stmt = (
            select(
                ScreeningResult.id,
                ScreeningResult.total_score,
                ScreeningResult.required_skill_score,
                ScreeningResult.preferred_skill_score,
                ScreeningResult.experience_score,
                ScreeningResult.matched_skills,
                ScreeningResult.missing_evidence,
                CandidateProfile.headline,
            )
            .join(CandidateProfile, CandidateProfile.id == ScreeningResult.candidate_id)
            .where(ScreeningResult.screening_run_id == run.id)
            .order_by(desc(ScreeningResult.total_score))
            .limit(10)
        )
        results_res = await db.execute(results_stmt)
        candidates = results_res.all()

        # Score stats
        scores = [float(c[1]) for c in candidates if c[1] is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

        # Skill demonstration frequency
        demonstrated_freq: Dict[str, int] = {}
        missing_freq: Dict[str, int] = {}
        for c in candidates:
            for s in (c[5] or []):
                demonstrated_freq[s] = demonstrated_freq.get(s, 0) + 1
            for m in (c[6] or []):
                missing_freq[m] = missing_freq.get(m, 0) + 1

        top_demonstrated = sorted(demonstrated_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        top_missing = sorted(missing_freq.items(), key=lambda x: x[1], reverse=True)[:5]

        lines = [
            f"### Screening Results Summary for '{job.title}':",
            f"- **Screening Run ID**: {str(run.id)[:8]}... (Status: {run.status})",
            f"- **Total Applications Screened**: {len(candidates)}",
            f"- **Average Screening Score**: {avg_score} / 100",
            f"- **Score Range**: {min(scores) if scores else 0} to {max(scores) if scores else 0}",
        ]
        if top_demonstrated:
            lines.append("- **Most Frequently Demonstrated Skills**:")
            for s, count in top_demonstrated:
                lines.append(f"  • {s}: {count} candidates")

        if top_missing:
            lines.append("- **Most Frequently Missing Evidence**:")
            for m, count in top_missing:
                lines.append(f"  • {m}: {count} candidates")

        if candidates:
            lines.append("\n**Top Ranked Candidates**:")
            for idx, c in enumerate(candidates[:5], 1):
                matched_str = ', '.join(c[5][:4]) if c[5] else 'None'
                lines.append(f"{idx}. Candidate Score: **{c[1]}/100** (Req: {c[2]}, Pref: {c[3]}, Exp: {c[4]}) — Demonstrated: {matched_str}")

        structured = {
            "job_title": job.title,
            "screening_run_id": str(run.id),
            "candidates_screened": len(candidates),
            "average_score": avg_score,
            "top_demonstrated_skills": top_demonstrated,
            "top_missing_requirements": top_missing,
        }

        return RetrievedHiringContext(
            intent=QueryIntent.SCREENING_SUMMARY,
            formatted_context="\n".join(lines),
            sources_used=["ScreeningRuns Table", "ScreeningResults Table", "Jobs Table"],
            retrieved_job_ids=[str(job.id)],
            screening_run_ids=[str(run.id)],
            structured_data=structured,
            evidence_snippets=[f"Average score: {avg_score}", f"Screened: {len(candidates)} candidates"],
        )

    async def _get_candidate_evidence(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        query: str,
        application_id: Optional[uuid.UUID],
        job_id: Optional[uuid.UUID],
    ) -> RetrievedHiringContext:
        """Retrieve factual screening evidence and resume data for a specific applicant."""
        app: Optional[Application] = None

        if application_id:
            stmt = (
                select(Application)
                .options(selectinload(Application.job), selectinload(Application.submitted_resume))
                .where(Application.id == application_id, Application.organization_id == organization_id)
            )
            res = await db.execute(stmt)
            app = res.scalar_one_or_none()
        else:
            # Try to find recent application in this organization
            base_stmt = (
                select(Application)
                .options(selectinload(Application.job), selectinload(Application.submitted_resume))
                .where(Application.organization_id == organization_id)
            )
            if job_id:
                base_stmt = base_stmt.where(Application.job_id == job_id)
            base_stmt = base_stmt.order_by(desc(Application.submitted_at)).limit(1)
            res = await db.execute(base_stmt)
            app = res.scalar_one_or_none()

        if not app:
            return RetrievedHiringContext(
                intent=QueryIntent.CANDIDATE_EVIDENCE,
                formatted_context="Applicant record not found in your organization.",
                sources_used=["Applications Table"],
            )

        # Retrieve ScreeningResult for this application
        s_stmt = (
            select(ScreeningResult)
            .where(
                ScreeningResult.application_id == app.id,
                ScreeningResult.organization_id == organization_id,
            )
            .order_by(desc(ScreeningResult.created_at))
            .limit(1)
        )
        s_res = await db.execute(s_stmt)
        screening_res = s_res.scalar_one_or_none()

        # Retrieve ScreeningInsight if exists
        insight: Optional[ScreeningInsight] = None
        if screening_res:
            i_stmt = select(ScreeningInsight).where(ScreeningInsight.screening_result_id == screening_res.id).limit(1)
            i_res = await db.execute(i_stmt)
            insight = i_res.scalar_one_or_none()

        candidate_name = (app.candidate_snapshot or {}).get("full_name") or "Applicant"
        job_title = app.job.title if app.job else "Target Role"

        lines = [
            f"### Verified Candidate Evidence for {candidate_name}:",
            f"- **Applied For**: {job_title}",
            f"- **Application Status**: {app.status}",
            f"- **Submitted Resume Version**: {app.submitted_resume.original_filename if app.submitted_resume else 'Pinned PDF'} (SHA-256: {app.submitted_resume.sha256[:12] if app.submitted_resume else 'N/A'}...)",
        ]

        evidence_snippets = []

        if screening_res:
            lines.extend([
                f"- **Overall Screening Score**: **{screening_res.total_score} / 100**",
                f"- **Score Breakdown**: Required Skills: {screening_res.required_skill_score}/100, Preferred Skills: {screening_res.preferred_skill_score}/100, Experience: {screening_res.experience_score}/100",
                f"- **Confidence Level**: {screening_res.confidence_level}",
            ])
            if screening_res.matched_skills:
                lines.append(f"- **Matched Required Skills**: {', '.join(screening_res.matched_skills)}")
                evidence_snippets.append(f"Matched skills: {', '.join(screening_res.matched_skills)}")
            if screening_res.preferred_skill_matches:
                lines.append(f"- **Matched Preferred Skills**: {', '.join(screening_res.preferred_skill_matches)}")
            if screening_res.missing_evidence:
                lines.append(f"- **Missing / Unverified Requirements**: {', '.join(screening_res.missing_evidence)}")
                evidence_snippets.append(f"Missing evidence: {', '.join(screening_res.missing_evidence)}")
            if screening_res.experience_assessment:
                lines.append(f"- **Experience Assessment**: {screening_res.experience_assessment}")

            if insight and insight.insight_data:
                idata = insight.insight_data
                if idata.get("summary"):
                    lines.append(f"\n**M6 Recruiter Insight Summary**: {idata.get('summary')}")
                if idata.get("key_strengths"):
                    lines.append("- **Key Strengths Identified**:")
                    for st in idata["key_strengths"][:3]:
                        lines.append(f"  • {st.get('title')}: {st.get('description')}")
        else:
            lines.append("- **Screening**: This applicant has not yet been processed by an AI screening run.")

        structured = {
            "application_id": str(app.id),
            "candidate_name": candidate_name,
            "job_title": job_title,
            "status": app.status,
            "has_screening": screening_res is not None,
            "score": float(screening_res.total_score) if screening_res and screening_res.total_score is not None else None,
            "matched_skills": screening_res.matched_skills if screening_res else [],
            "missing_evidence": screening_res.missing_evidence if screening_res else [],
        }

        return RetrievedHiringContext(
            intent=QueryIntent.CANDIDATE_EVIDENCE,
            formatted_context="\n".join(lines),
            sources_used=["Applications Table", "Resumes Table"] + (["ScreeningResults Table"] if screening_res else []),
            retrieved_job_ids=[str(app.job_id)],
            retrieved_app_ids=[str(app.id)],
            structured_data=structured,
            evidence_snippets=evidence_snippets,
        )

    async def _get_candidate_comparison(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        query: str,
        job_id: Optional[uuid.UUID],
    ) -> RetrievedHiringContext:
        """Structured side-by-side comparison of top candidates for a job evaluated in the same screening run."""
        job = await self._resolve_job(db, organization_id, query, job_id)
        if not job:
            return RetrievedHiringContext(
                intent=QueryIntent.CANDIDATE_COMPARISON,
                formatted_context="Please specify a job to compare candidates.",
                sources_used=["Jobs Table"],
            )

        # Get latest screening run
        run_stmt = (
            select(ScreeningRun)
            .where(ScreeningRun.job_id == job.id, ScreeningRun.organization_id == organization_id)
            .order_by(desc(ScreeningRun.created_at))
            .limit(1)
        )
        run_res = await db.execute(run_stmt)
        run = run_res.scalar_one_or_none()

        if not run:
            return RetrievedHiringContext(
                intent=QueryIntent.CANDIDATE_COMPARISON,
                formatted_context=f"Cannot compare candidates for '{job.title}': No screening run found. All candidates must be evaluated in a consistent screening run.",
                sources_used=["ScreeningRuns Table"],
                retrieved_job_ids=[str(job.id)],
            )

        # Parse comparison limit (e.g. "top 3", "top 5")
        top_n = 3
        match = re.search(r"top\s+(\d+)", query.lower())
        if match:
            top_n = min(max(int(match.group(1)), 2), 5)

        results_stmt = (
            select(
                ScreeningResult.application_id,
                ScreeningResult.total_score,
                ScreeningResult.required_skill_score,
                ScreeningResult.preferred_skill_score,
                ScreeningResult.experience_score,
                ScreeningResult.matched_skills,
                ScreeningResult.missing_evidence,
                CandidateProfile.headline,
                Application.candidate_snapshot,
            )
            .join(Application, Application.id == ScreeningResult.application_id)
            .join(CandidateProfile, CandidateProfile.id == ScreeningResult.candidate_id)
            .where(ScreeningResult.screening_run_id == run.id)
            .order_by(desc(ScreeningResult.total_score))
            .limit(top_n)
        )
        results_res = await db.execute(results_stmt)
        candidates = results_res.all()

        if not candidates:
            return RetrievedHiringContext(
                intent=QueryIntent.CANDIDATE_COMPARISON,
                formatted_context=f"No screened candidates found in screening run {str(run.id)[:8]} for '{job.title}'.",
                sources_used=["ScreeningResults Table"],
            )

        lines = [
            f"### Verified Candidate Comparison for '{job.title}' (Screening Run: {str(run.id)[:8]}):",
            f"Evaluated against consistent job requirements: {', '.join(job.required_skills or [])}\n",
            "| Rank | Candidate | Total Score | Req Skills | Pref Skills | Experience | Matched Skills | Missing Evidence |",
            "|---|---|:---:|:---:|:---:|:---:|---|---|",
        ]

        app_ids = []
        structured_candidates = []

        for idx, c in enumerate(candidates, 1):
            app_id = str(c[0])
            app_ids.append(app_id)
            c_name = (c[8] or {}).get("full_name") or f"Applicant {idx}"
            matched_str = ', '.join(c[5][:3]) if c[5] else 'None'
            missing_str = ', '.join(c[6][:2]) if c[6] else 'None'

            lines.append(
                f"| #{idx} | **{c_name}** | **{c[1]}** | {c[2]} | {c[3]} | {c[4]} | {matched_str} | {missing_str} |"
            )
            structured_candidates.append({
                "rank": idx,
                "name": c_name,
                "score": float(c[1]) if c[1] is not None else 0.0,
                "required_score": float(c[2]) if c[2] is not None else 0.0,
                "preferred_score": float(c[3]) if c[3] is not None else 0.0,
                "experience_score": float(c[4]) if c[4] is not None else 0.0,
                "matched_skills": c[5] or [],
                "missing_evidence": c[6] or [],
            })

        lines.append("\n> *All candidates above were evaluated under identical scoring weights and verified criteria.*")

        return RetrievedHiringContext(
            intent=QueryIntent.CANDIDATE_COMPARISON,
            formatted_context="\n".join(lines),
            sources_used=["ScreeningRuns Table", "ScreeningResults Table", "Jobs Table"],
            retrieved_job_ids=[str(job.id)],
            retrieved_app_ids=app_ids,
            screening_run_ids=[str(run.id)],
            structured_data={"job_title": job.title, "candidates": structured_candidates},
            evidence_snippets=[f"Top candidate score: {structured_candidates[0]['score'] if structured_candidates else 0}"],
        )

    async def _get_skill_distribution(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        query: str,
        job_id: Optional[uuid.UUID],
    ) -> RetrievedHiringContext:
        """Calculate frequency of demonstrated skills and missing evidence across applicants."""
        base_where = [ScreeningResult.organization_id == organization_id]
        job: Optional[Job] = None

        if job_id:
            job = await self._resolve_job(db, organization_id, query, job_id)
            if job:
                base_where.append(ScreeningResult.job_id == job.id)

        stmt = select(ScreeningResult.matched_skills, ScreeningResult.missing_evidence).where(*base_where)
        res = await db.execute(stmt)
        rows = res.all()

        demonstrated_freq: Dict[str, int] = {}
        missing_freq: Dict[str, int] = {}

        for row in rows:
            for s in (row[0] or []):
                demonstrated_freq[s] = demonstrated_freq.get(s, 0) + 1
            for m in (row[1] or []):
                missing_freq[m] = missing_freq.get(m, 0) + 1

        top_demonstrated = sorted(demonstrated_freq.items(), key=lambda x: x[1], reverse=True)[:8]
        top_missing = sorted(missing_freq.items(), key=lambda x: x[1], reverse=True)[:8]

        scope_label = f"for '{job.title}'" if job else "across all screened organization jobs"

        lines = [
            f"### Verified Skill Distribution {scope_label}:",
            f"- **Screened Candidate Records Evaluated**: {len(rows)}",
            "\n**Most Commonly Demonstrated Skills**:",
        ]
        if top_demonstrated:
            for s, cnt in top_demonstrated:
                pct = round((cnt / len(rows)) * 100, 1) if rows else 0
                lines.append(f"- **{s}**: {cnt} candidates ({pct}%)")
        else:
            lines.append("- No demonstrated skills recorded.")

        lines.append("\n**Most Frequently Missing / Unverified Requirements**:")
        if top_missing:
            for m, cnt in top_missing:
                pct = round((cnt / len(rows)) * 100, 1) if rows else 0
                lines.append(f"- **{m}**: {cnt} candidates ({pct}%)")
        else:
            lines.append("- No missing evidence items recorded.")

        structured = {
            "scope": scope_label,
            "sample_size": len(rows),
            "top_demonstrated_skills": top_demonstrated,
            "top_missing_requirements": top_missing,
        }

        return RetrievedHiringContext(
            intent=QueryIntent.SKILL_DISTRIBUTION,
            formatted_context="\n".join(lines),
            sources_used=["ScreeningResults Table"],
            retrieved_job_ids=[str(job.id)] if job else [],
            structured_data=structured,
            evidence_snippets=[f"Evaluated {len(rows)} candidate screening records"],
        )

    async def _resolve_job(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        query: str,
        job_id: Optional[uuid.UUID],
    ) -> Optional[Job]:
        """Resolve a specific job by ID or best title match within the organization."""
        if job_id:
            stmt = select(Job).where(Job.id == job_id, Job.organization_id == organization_id)
            res = await db.execute(stmt)
            return res.scalar_one_or_none()

        # Try to find a job matching words in query
        all_jobs_stmt = select(Job).where(Job.organization_id == organization_id).order_by(desc(Job.created_at))
        all_jobs_res = await db.execute(all_jobs_stmt)
        all_jobs = all_jobs_res.scalars().all()

        q_lower = query.lower()
        for j in all_jobs:
            if j.title.lower() in q_lower or any(word in q_lower for word in j.title.lower().split()):
                return j

        # Default to the most recent published or created job
        return all_jobs[0] if all_jobs else None


recruiter_retrieval_service = RecruiterRetrievalService()
