export const API_BASE = (import.meta.env.VITE_API_URL as string) || 'http://127.0.0.1:8000';

export interface CandidateProfile {
  id: string;
  user_id: string;
  email: string;
  full_name: string;
  phone?: string | null;
  location?: string | null;
  headline?: string | null;
  professional_summary?: string | null;
}

export interface EducationItem {
  institution?: string | null;
  degree?: string | null;
  field_of_study?: string | null;
  start_date?: string | null;
  end_date?: string | null;
}

export interface ExperienceItem {
  company?: string | null;
  job_title?: string | null;
  description?: string | null;
  start_date?: string | null;
  end_date?: string | null;
}

export interface ProjectItem {
  name?: string | null;
  description?: string | null;
  technologies?: string[];
}

export interface ParsedResumeData {
  full_name?: string | null;
  email?: string | null;
  phone?: string | null;
  professional_summary?: string | null;
  skills?: string[];
  education?: EducationItem[];
  experience?: ExperienceItem[];
  projects?: ProjectItem[];
  certifications?: string[];
}

export interface ResumeItem {
  id: string;
  candidate_id: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  sha256: string;
  extracted_text?: string | null;
  parsed_data?: ParsedResumeData | null;
  parsing_status: string;
  parsing_error?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CandidateMatch {
  id: string;
  name: string;
  score: number;
  yoe_status: string;
  matched_skills: string[];
  missing_skills: string[];
  reasoning: string;
}

export interface PublicJob {
  id: string;
  title: string;
  slug?: string | null;
  organization_name: string;
  department?: string | null;
  description: string;
  responsibilities?: string | null;
  qualifications?: string | null;
  location?: string | null;
  workplace_type: string;
  employment_type: string;
  experience_min?: number | null;
  experience_max?: number | null;
  salary_min?: number | null;
  salary_max?: number | null;
  salary_currency: string;
  required_skills: string[];
  preferred_skills: string[];
  published_at?: string | null;
  created_at: string;
}

export interface RecruiterJob {
  id: string;
  organization_id: string;
  created_by?: string | null;
  title: string;
  slug?: string | null;
  department?: string | null;
  description: string;
  responsibilities?: string | null;
  qualifications?: string | null;
  location?: string | null;
  workplace_type: string;
  employment_type: string;
  experience_min?: number | null;
  experience_max?: number | null;
  salary_min?: number | null;
  salary_max?: number | null;
  salary_currency: string;
  required_skills: string[];
  preferred_skills: string[];
  status: 'DRAFT' | 'PUBLISHED' | 'CLOSED' | 'ARCHIVED';
  published_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  role?: string;
}

export interface CandidateApplication {
  id: string;
  job_id: string;
  job_title: string;
  organization_id: string;
  organization_name: string;
  submitted_resume_id: string;
  resume_filename: string;
  status: 'SUBMITTED' | 'UNDER_REVIEW' | 'SHORTLISTED' | 'INTERVIEWING' | 'REJECTED' | 'HIRED' | 'WITHDRAWN';
  cover_letter?: string | null;
  submitted_at: string;
  status_updated_at: string;
  withdrawn_at?: string | null;
  job_location?: string | null;
  workplace_type?: string | null;
  employment_type?: string | null;
}

export interface RecruiterApplication {
  id: string;
  job_id: string;
  job_title: string;
  organization_id: string;
  candidate_id: string;
  candidate_name?: string | null;
  candidate_email?: string | null;
  candidate_headline?: string | null;
  submitted_resume_id: string;
  resume_filename: string;
  status: 'SUBMITTED' | 'UNDER_REVIEW' | 'SHORTLISTED' | 'INTERVIEWING' | 'REJECTED' | 'HIRED' | 'WITHDRAWN';
  submitted_at: string;
  status_updated_at: string;
  withdrawn_at?: string | null;
  cover_letter?: string | null;
}

export interface StatusHistoryItem {
  id: string;
  previous_status?: string | null;
  new_status: string;
  changed_by?: string | null;
  changed_at: string;
  internal_note?: string | null;
}

export interface RecruiterApplicationDetail extends RecruiterApplication {
  candidate_snapshot?: any;
  status_history: StatusHistoryItem[];
}

export interface ScreeningRun {
  id: string;
  organization_id: string;
  job_id: string;
  triggered_by?: string | null;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'PARTIAL' | 'FAILED';
  total_applications: number;
  processed_applications: number;
  failed_applications: number;
  scoring_config?: any;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
  error_summary?: string | null;
}

export interface KeyStrengthItem {
  title: string;
  description: string;
  supporting_evidence: string[];
  category: 'SKILL' | 'EXPERIENCE' | 'PROJECT' | 'EDUCATION' | 'CERTIFICATION';
}

export interface RelevantProjectItem {
  project_name: string;
  description: string;
  relevant_requirements: string[];
  supporting_evidence: string[];
}

export interface EvidenceGapItem {
  requirement: string;
  explanation: string;
}

export interface CandidateInsightData {
  summary: string;
  key_strengths: KeyStrengthItem[];
  relevant_projects: RelevantProjectItem[];
  evidence_gaps: EvidenceGapItem[];
  uncertainties: string[];
  score_explanation: string;
}

export interface ScreeningInsight {
  id: string;
  screening_result_id: string;
  screening_run_id: string;
  application_id: string;
  status: 'PENDING' | 'COMPLETED' | 'FAILED';
  model_id: string;
  prompt_version: string;
  insight_data: CandidateInsightData;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScreeningResultItem {
  id: string;
  screening_run_id: string;
  application_id: string;
  candidate_id: string;
  candidate_name?: string | null;
  candidate_email?: string | null;
  candidate_headline?: string | null;
  submitted_resume_id: string;
  resume_filename?: string | null;
  total_score?: number | null;
  required_skill_score?: number | null;
  preferred_skill_score?: number | null;
  experience_score?: number | null;
  matched_skills_count: number;
  missing_evidence_count: number;
  confidence_level?: string | null;
  processing_status: string;
  insight_summary?: string | null;
  insight_status?: string | null;
  created_at: string;
}

export interface ScreeningResultDetail extends ScreeningResultItem {
  matched_skills: Array<{
    skill: string;
    canonical_skill?: string;
    evidence: string;
    evidence_type?: string;
    confidence?: number;
  }>;
  missing_evidence: Array<{
    skill: string;
    canonical_skill?: string;
    reason: string;
  }>;
  preferred_skill_matches: Array<{
    skill: string;
    canonical_skill?: string;
    evidence: string;
    confidence?: number;
  }>;
  experience_assessment: {
    status?: string;
    verified_years?: number | null;
    required_min_years?: number;
    project_count?: number;
    roles?: string[];
    note?: string;
  };
  explanation: string;
  error_message?: string | null;
  insight?: ScreeningInsight | null;
}

export interface DeterministicFindingItem {
  category: string;
  level: string;
  message: string;
}

export interface DeterministicChecksData {
  word_count: number;
  char_count: number;
  sections_detected: string[];
  missing_sections: string[];
  empty_or_short_sections: string[];
  contact_info: {
    has_email: boolean;
    has_phone: boolean;
    has_linkedin: boolean;
    has_github: boolean;
  };
  dates_assessment: {
    roles_missing_dates?: string[];
    education_missing_dates?: string[];
  };
  duplicated_content: {
    has_duplicates: boolean;
    duplicate_snippets?: string[];
  };
  projects_assessment: {
    total_projects_count: number;
    projects_missing_descriptions?: string[];
  };
  measurable_outcomes: {
    has_metrics: boolean;
    metrics_count: number;
    sample_metrics?: string[];
  };
  findings: DeterministicFindingItem[];
  layout_notice?: string;
}

export interface StrengthItem {
  title: string;
  description: string;
  supporting_evidence: string[];
}

export interface SkillsAnalysisData {
  demonstrated_skills: string[];
  skills_with_limited_evidence: string[];
}

export interface ProjectAnalysisItem {
  project_name: string;
  what_is_demonstrated: string;
  what_is_missing: string;
  suggested_improvement: string;
}

export interface ExperienceAnalysisItem {
  role_or_experience: string;
  demonstrated_contributions: string;
  improvement_suggestions: string;
}

export interface ImprovementPriorityItem {
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  issue: string;
  why_it_matters: string;
  suggested_action: string;
}

export interface TargetRoleAlignmentData {
  target_role?: string | null;
  alignment_summary: string;
  relevant_strengths: string[];
  missing_relevant_evidence: string[];
}

export interface LLMAnalysisData {
  overall_summary: string;
  strengths: StrengthItem[];
  skills_analysis: SkillsAnalysisData;
  project_analysis: ProjectAnalysisItem[];
  experience_analysis: ExperienceAnalysisItem[];
  missing_information: string[];
  improvement_priorities: ImprovementPriorityItem[];
  target_role_alignment?: TargetRoleAlignmentData | null;
  limitations_and_uncertainties: string[];
}

export interface ResumeAnalysis {
  id: string;
  candidate_id: string;
  resume_id: string;
  resume_sha256: string;
  target_role?: string | null;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  deterministic_checks?: DeterministicChecksData | null;
  analysis_data?: LLMAnalysisData | null;
  error_message?: string | null;
  model_name?: string | null;
  prompt_version: string;
  schema_version: string;
  created_at: string;
  updated_at: string;
}

export interface ResumeAnalysisListItem {
  id: string;
  resume_id: string;
  target_role?: string | null;
  status: string;
  overall_summary?: string | null;
  created_at: string;
}

export interface CareerMessageItem {
  id: string;
  conversation_id: string;
  role: 'USER' | 'ASSISTANT' | 'SYSTEM';
  content: string;
  context_metadata?: {
    resume_id?: string | null;
    resume_sha256?: string | null;
    m7_analysis_id?: string | null;
    retrieved_sections?: string[];
    evidence_snippets?: string[];
    is_fallback?: boolean;
  } | null;
  model_name?: string | null;
  created_at: string;
}

export interface CareerConversationItem {
  id: string;
  candidate_id: string;
  resume_id?: string | null;
  resume_sha256?: string | null;
  target_role?: string | null;
  conversation_title: string;
  conversation_type: string;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  message_count?: number;
  last_message?: CareerMessageItem | null;
}

export interface CareerConversationDetail extends CareerConversationItem {
  messages: CareerMessageItem[];
}

export interface RecruiterAiMessageItem {
  id: string;
  conversation_id: string;
  role: 'USER' | 'ASSISTANT' | 'SYSTEM';
  content: string;
  context_metadata?: {
    organization_id?: string;
    intent?: string;
    retrieved_job_ids?: string[];
    retrieved_app_ids?: string[];
    screening_run_ids?: string[];
    sources_used?: string[];
    evidence_snippets?: string[];
    is_fallback?: boolean;
  } | null;
  model_name?: string | null;
  created_at: string;
}

export interface RecruiterAiConversationItem {
  id: string;
  organization_id: string;
  created_by_user_id: string;
  conversation_title: string;
  conversation_type: string;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  message_count?: number;
  last_message?: RecruiterAiMessageItem | null;
}

export interface RecruiterAiConversationDetail extends RecruiterAiConversationItem {
  messages: RecruiterAiMessageItem[];
}
