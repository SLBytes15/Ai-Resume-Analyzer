import React, { useState, useEffect, useRef } from 'react';

const API_BASE = 'http://127.0.0.1:8000';

interface CandidateProfile {
  id: string;
  user_id: string;
  email: string;
  full_name: string;
  phone?: string | null;
  location?: string | null;
  headline?: string | null;
  professional_summary?: string | null;
}

interface EducationItem {
  institution?: string | null;
  degree?: string | null;
  field_of_study?: string | null;
  start_date?: string | null;
  end_date?: string | null;
}

interface ExperienceItem {
  company?: string | null;
  job_title?: string | null;
  description?: string | null;
  start_date?: string | null;
  end_date?: string | null;
}

interface ProjectItem {
  name?: string | null;
  description?: string | null;
  technologies?: string[];
}

interface ParsedResumeData {
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

interface ResumeItem {
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

interface CandidateMatch {
  id: string;
  name: string;
  score: number;
  yoe_status: string;
  matched_skills: string[];
  missing_skills: string[];
  reasoning: string;
}

interface PublicJob {
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

interface RecruiterJob {
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

interface Organization {
  id: string;
  name: string;
  slug: string;
  role?: string;
}

interface CandidateApplication {
  id: string;
  job_id: string;
  job_title: string;
  organization_id: string;
  organization_name: string;
  submitted_resume_id: string;
  resume_filename: string;
  status: 'SUBMITTED' | 'UNDER_REVIEW' | 'SHORTLISTED' | 'REJECTED' | 'HIRED' | 'WITHDRAWN';
  cover_letter?: string | null;
  submitted_at: string;
  status_updated_at: string;
  withdrawn_at?: string | null;
  job_location?: string | null;
  workplace_type?: string | null;
  employment_type?: string | null;
}

interface RecruiterApplication {
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
  status: 'SUBMITTED' | 'UNDER_REVIEW' | 'SHORTLISTED' | 'REJECTED' | 'HIRED' | 'WITHDRAWN';
  submitted_at: string;
  status_updated_at: string;
  withdrawn_at?: string | null;
  cover_letter?: string | null;
}

interface StatusHistoryItem {
  id: string;
  previous_status?: string | null;
  new_status: string;
  changed_by?: string | null;
  changed_at: string;
  internal_note?: string | null;
}

interface RecruiterApplicationDetail extends RecruiterApplication {
  candidate_snapshot?: any;
  status_history: StatusHistoryItem[];
}

interface ScreeningRun {
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

interface KeyStrengthItem {
  title: string;
  description: string;
  supporting_evidence: string[];
  category: 'SKILL' | 'EXPERIENCE' | 'PROJECT' | 'EDUCATION' | 'CERTIFICATION';
}

interface RelevantProjectItem {
  project_name: string;
  description: string;
  relevant_requirements: string[];
  supporting_evidence: string[];
}

interface EvidenceGapItem {
  requirement: string;
  explanation: string;
}

interface CandidateInsightData {
  summary: string;
  key_strengths: KeyStrengthItem[];
  relevant_projects: RelevantProjectItem[];
  evidence_gaps: EvidenceGapItem[];
  uncertainties: string[];
  score_explanation: string;
}

interface ScreeningInsight {
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

interface ScreeningResultItem {
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

interface ScreeningResultDetail extends ScreeningResultItem {
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

// Milestone 7: Candidate Resume Intelligence & Career Guidance Interfaces
interface DeterministicFindingItem {
  category: string;
  level: string;
  message: string;
}

interface DeterministicChecksData {
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

interface StrengthItem {
  title: string;
  description: string;
  supporting_evidence: string[];
}

interface SkillsAnalysisData {
  demonstrated_skills: string[];
  skills_with_limited_evidence: string[];
}

interface ProjectAnalysisItem {
  project_name: string;
  what_is_demonstrated: string;
  what_is_missing: string;
  suggested_improvement: string;
}

interface ExperienceAnalysisItem {
  role_or_experience: string;
  demonstrated_contributions: string;
  improvement_suggestions: string;
}

interface ImprovementPriorityItem {
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  issue: string;
  why_it_matters: string;
  suggested_action: string;
}

interface TargetRoleAlignmentData {
  target_role?: string | null;
  alignment_summary: string;
  relevant_strengths: string[];
  missing_relevant_evidence: string[];
}

interface LLMAnalysisData {
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

interface ResumeAnalysis {
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

interface ResumeAnalysisListItem {
  id: string;
  resume_id: string;
  target_role?: string | null;
  status: string;
  overall_summary?: string | null;
  created_at: string;
}

// Milestone 8: Candidate AI Career Assistant Interfaces
interface CareerMessageItem {
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

interface CareerConversationItem {
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

interface CareerConversationDetail extends CareerConversationItem {
  messages: CareerMessageItem[];
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'public-jobs' | 'candidate' | 'recruiter'>('public-jobs');

  // Auth state
  const [token, setToken] = useState<string>(() => localStorage.getItem('talentlens_token') || '');
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authFullName, setAuthFullName] = useState('');
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [authError, setAuthError] = useState('');

  // Candidate Profile state
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileForm, setProfileForm] = useState({
    phone: '',
    location: '',
    headline: '',
    professional_summary: '',
  });
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMessage, setProfileMessage] = useState('');

  // Resume state
  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [resumesLoading, setResumesLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [selectedResume, setSelectedResume] = useState<ResumeItem | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Recruiter Match state
  const [jdText, setJdText] = useState('');
  const [matchCandidates, setMatchCandidates] = useState<CandidateMatch[]>([]);
  const [matchLoading, setMatchLoading] = useState(false);
  const [matchError, setMatchError] = useState('');

  // Public Jobs State
  const [publicJobs, setPublicJobs] = useState<PublicJob[]>([]);
  const [publicLoading, setPublicLoading] = useState(false);
  const [publicError, setPublicError] = useState('');
  const [selectedPublicJob, setSelectedPublicJob] = useState<PublicJob | null>(null);
  const [publicKeyword, setPublicKeyword] = useState('');
  const [publicLocation, setPublicLocation] = useState('');
  const [publicWorkplace, setPublicWorkplace] = useState('');
  const [publicEmployment, setPublicEmployment] = useState('');
  const [publicSkill, setPublicSkill] = useState('');
  const [publicSort, setPublicSort] = useState<'newest' | 'oldest'>('newest');

  // Recruiter Management State
  const [recruiterSubTab, setRecruiterSubTab] = useState<'jobs' | 'applications' | 'screening' | 'matcher'>('jobs');
  const [userOrgs, setUserOrgs] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [recruiterJobs, setRecruiterJobs] = useState<RecruiterJob[]>([]);
  const [recruiterJobsLoading, setRecruiterJobsLoading] = useState(false);
  const [recruiterJobStatusFilter, setRecruiterJobStatusFilter] = useState('');
  const [recruiterJobKeywordFilter, setRecruiterJobKeywordFilter] = useState('');
  const [recruiterActionMessage, setRecruiterActionMessage] = useState('');

  // Candidate Sub-Tabs: 'profile-resumes' | 'career-guidance' | 'career-assistant' | 'my-applications'
  const [candidateSubTab, setCandidateSubTab] = useState<'profile-resumes' | 'career-guidance' | 'career-assistant' | 'my-applications'>('profile-resumes');
  const [myApplications, setMyApplications] = useState<CandidateApplication[]>([]);
  const [myApplicationsLoading, setMyApplicationsLoading] = useState(false);
  const [myAppStatusFilter, setMyAppStatusFilter] = useState('');
  const [myAppKeyword, setMyAppKeyword] = useState('');
  const [selectedCandidateApp, setSelectedCandidateApp] = useState<CandidateApplication | null>(null);

  // M7: Candidate Resume Intelligence & Career Guidance State
  const [selectedAnalysisResumeId, setSelectedAnalysisResumeId] = useState<string>('');
  const [targetRoleInput, setTargetRoleInput] = useState<string>('');
  const [analysesList, setAnalysesList] = useState<ResumeAnalysisListItem[]>([]);
  const [analysesLoading, setAnalysesLoading] = useState<boolean>(false);
  const [currentAnalysis, setCurrentAnalysis] = useState<ResumeAnalysis | null>(null);
  const [analysisInProgress, setAnalysisInProgress] = useState<boolean>(false);
  const [analysisError, setAnalysisError] = useState<string>('');
  const [retryingAnalysisId, setRetryingAnalysisId] = useState<string | null>(null);

  // M8: Candidate AI Career Assistant State
  const [conversationsList, setConversationsList] = useState<CareerConversationItem[]>([]);
  const [conversationsLoading, setConversationsLoading] = useState<boolean>(false);
  const [activeConversation, setActiveConversation] = useState<CareerConversationDetail | null>(null);
  const [activeConvLoading, setActiveConvLoading] = useState<boolean>(false);
  const [messageInput, setMessageInput] = useState<string>('');
  const [sendingMessage, setSendingMessage] = useState<boolean>(false);
  const [chatError, setChatError] = useState<string>('');

  // New Conversation Modal State
  const [isNewConvModalOpen, setIsNewConvModalOpen] = useState<boolean>(false);
  const [newConvResumeId, setNewConvResumeId] = useState<string>('');
  const [newConvTargetRole, setNewConvTargetRole] = useState<string>('');
  const [newConvPurpose, setNewConvPurpose] = useState<string>('CAREER_GUIDANCE');
  const [newConvTitle, setNewConvTitle] = useState<string>('');
  const [newConvInitialMsg, setNewConvInitialMsg] = useState<string>('');
  const [creatingConv, setCreatingConv] = useState<boolean>(false);

  // Apply to Job Modal State
  const [isApplyModalOpen, setIsApplyModalOpen] = useState(false);
  const [applyJob, setApplyJob] = useState<PublicJob | null>(null);
  const [selectedResumeId, setSelectedResumeId] = useState('');
  const [coverLetter, setCoverLetter] = useState('');
  const [applyLoading, setApplyLoading] = useState(false);
  const [applyError, setApplyError] = useState('');
  const [applySuccess, setApplySuccess] = useState('');

  // Recruiter Applications State
  const [recruiterApplications, setRecruiterApplications] = useState<RecruiterApplication[]>([]);
  const [recruiterAppsLoading, setRecruiterAppsLoading] = useState(false);
  const [recruiterAppJobFilter, setRecruiterAppJobFilter] = useState('');
  const [recruiterAppStatusFilter, setRecruiterAppStatusFilter] = useState('');
  const [recruiterAppKeyword, setRecruiterAppKeyword] = useState('');
  const [selectedRecruiterAppDetail, setSelectedRecruiterAppDetail] = useState<RecruiterApplicationDetail | null>(null);
  const [isRecruiterAppModalOpen, setIsRecruiterAppModalOpen] = useState(false);
  const [statusUpdateVal, setStatusUpdateVal] = useState('');
  const [statusUpdateNote, setStatusUpdateNote] = useState('');
  const [statusUpdating, setStatusUpdating] = useState(false);
  const [statusUpdateError, setStatusUpdateError] = useState('');

  // AI Screening State
  const [screeningJobId, setScreeningJobId] = useState<string>('');
  const [screeningRuns, setScreeningRuns] = useState<ScreeningRun[]>([]);
  const [screeningRunsLoading, setScreeningRunsLoading] = useState(false);
  const [selectedRunId, setSelectedRunId] = useState<string>('');
  const [screeningResults, setScreeningResults] = useState<ScreeningResultItem[]>([]);
  const [screeningResultsLoading, setScreeningResultsLoading] = useState(false);
  const [screeningScoreFilter, setScreeningScoreFilter] = useState<string>('');
  const [screeningKeyword, setScreeningKeyword] = useState<string>('');
  const [selectedResultDetail, setSelectedResultDetail] = useState<ScreeningResultDetail | null>(null);
  const [isResultDetailModalOpen, setIsResultDetailModalOpen] = useState(false);
  const [resultDetailLoading, setResultDetailLoading] = useState(false);
  const [isTriggerModalOpen, setIsTriggerModalOpen] = useState(false);
  const [triggerJob, setTriggerJob] = useState<RecruiterJob | null>(null);
  const [triggerLoading, setTriggerLoading] = useState(false);
  const [triggerError, setTriggerError] = useState('');
  const [expandedResultIds, setExpandedResultIds] = useState<Record<string, boolean>>({});
  const [retryingInsight, setRetryingInsight] = useState(false);

  // Job Form Modal State (Create / Edit)
  const [isJobModalOpen, setIsJobModalOpen] = useState(false);
  const [editingJob, setEditingJob] = useState<RecruiterJob | null>(null);
  const [jobFormData, setJobFormData] = useState({
    title: '',
    department: '',
    description: '',
    responsibilities: '',
    qualifications: '',
    location: '',
    workplace_type: 'ONSITE',
    employment_type: 'FULL_TIME',
    experience_min: '',
    experience_max: '',
    salary_min: '',
    salary_max: '',
    salary_currency: 'INR',
    required_skills: '',
    preferred_skills: '',
  });
  const [jobFormError, setJobFormError] = useState('');
  const [jobFormSaving, setJobFormSaving] = useState(false);

  // New Organization Modal
  const [isOrgModalOpen, setIsOrgModalOpen] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  const [newOrgSlug, setNewOrgSlug] = useState('');
  const [orgError, setOrgError] = useState('');

  // Fetch Public Jobs on mount or filter change
  useEffect(() => {
    fetchPublicJobs();
  }, [publicKeyword, publicLocation, publicWorkplace, publicEmployment, publicSkill, publicSort]);

  // On token change, persist & fetch candidate profile, resumes, & user orgs
  useEffect(() => {
    if (token) {
      localStorage.setItem('talentlens_token', token);
      fetchProfile();
      fetchResumes();
      fetchUserOrganizations();
    } else {
      localStorage.removeItem('talentlens_token');
      setProfile(null);
      setResumes([]);
      setUserOrgs([]);
      setSelectedOrgId('');
      setRecruiterJobs([]);
    }
  }, [token]);

  // When selected organization changes, fetch recruiter jobs
  useEffect(() => {
    if (token && selectedOrgId) {
      fetchRecruiterJobs();
    }
  }, [selectedOrgId, recruiterJobStatusFilter, recruiterJobKeywordFilter]);

  // Auth handlers
  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError('');
    const endpoint = isRegisterMode ? '/api/v1/auth/register' : '/api/v1/auth/login';
    const payload = isRegisterMode
      ? { email: authEmail, password: authPassword, full_name: authFullName }
      : { email: authEmail, password: authPassword };

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }
      setToken(data.access_token);
      setAuthPassword('');
    } catch (err: any) {
      setAuthError(err.message || 'Authentication error');
    }
  };

  const handleLogout = () => {
    setToken('');
    setProfile(null);
    setResumes([]);
    setUserOrgs([]);
    setSelectedOrgId('');
  };

  // Public Jobs Operations
  const fetchPublicJobs = async () => {
    setPublicLoading(true);
    setPublicError('');
    try {
      const params = new URLSearchParams();
      if (publicKeyword.trim()) params.append('keyword', publicKeyword.trim());
      if (publicLocation.trim()) params.append('location', publicLocation.trim());
      if (publicWorkplace) params.append('workplace_type', publicWorkplace);
      if (publicEmployment) params.append('employment_type', publicEmployment);
      if (publicSkill.trim()) params.append('skill', publicSkill.trim());
      params.append('sort', publicSort);

      const res = await fetch(`${API_BASE}/api/v1/jobs?${params.toString()}`);
      if (!res.ok) throw new Error('Failed to load published jobs');
      const data = await res.json();
      setPublicJobs(data);
    } catch (err: any) {
      setPublicError(err.message || 'Failed to load public jobs');
    } finally {
      setPublicLoading(false);
    }
  };

  // Recruiter Organizations
  const fetchUserOrganizations = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/recruiter/organizations`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setUserOrgs(data);
        if (data.length > 0 && !selectedOrgId) {
          setSelectedOrgId(data[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to fetch user organizations', err);
    }
  };

  const handleCreateOrganization = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !newOrgName.trim()) return;
    setOrgError('');
    try {
      const res = await fetch(`${API_BASE}/api/v1/recruiter/organizations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: newOrgName.trim(),
          slug: newOrgSlug.trim() || undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to create organization');
      setUserOrgs((prev) => [...prev, data]);
      setSelectedOrgId(data.id);
      setIsOrgModalOpen(false);
      setNewOrgName('');
      setNewOrgSlug('');
    } catch (err: any) {
      setOrgError(err.message || 'Error creating organization');
    }
  };

  // Recruiter Jobs Operations
  const fetchRecruiterJobs = async () => {
    if (!token || !selectedOrgId) return;
    setRecruiterJobsLoading(true);
    try {
      const params = new URLSearchParams();
      if (recruiterJobStatusFilter) params.append('status', recruiterJobStatusFilter);
      if (recruiterJobKeywordFilter.trim()) params.append('keyword', recruiterJobKeywordFilter.trim());

      const res = await fetch(
        `${API_BASE}/api/v1/organizations/${selectedOrgId}/jobs?${params.toString()}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (res.ok) {
        const data = await res.json();
        setRecruiterJobs(data);
      }
    } catch (err) {
      console.error('Failed to fetch recruiter jobs', err);
    } finally {
      setRecruiterJobsLoading(false);
    }
  };

  const openCreateJobModal = () => {
    setEditingJob(null);
    setJobFormData({
      title: '',
      department: '',
      description: '',
      responsibilities: '',
      qualifications: '',
      location: '',
      workplace_type: 'ONSITE',
      employment_type: 'FULL_TIME',
      experience_min: '',
      experience_max: '',
      salary_min: '',
      salary_max: '',
      salary_currency: 'INR',
      required_skills: '',
      preferred_skills: '',
    });
    setJobFormError('');
    setIsJobModalOpen(true);
  };

  const openEditJobModal = (job: RecruiterJob) => {
    setEditingJob(job);
    setJobFormData({
      title: job.title,
      department: job.department || '',
      description: job.description,
      responsibilities: job.responsibilities || '',
      qualifications: job.qualifications || '',
      location: job.location || '',
      workplace_type: job.workplace_type,
      employment_type: job.employment_type,
      experience_min: job.experience_min !== null && job.experience_min !== undefined ? String(job.experience_min) : '',
      experience_max: job.experience_max !== null && job.experience_max !== undefined ? String(job.experience_max) : '',
      salary_min: job.salary_min !== null && job.salary_min !== undefined ? String(job.salary_min) : '',
      salary_max: job.salary_max !== null && job.salary_max !== undefined ? String(job.salary_max) : '',
      salary_currency: job.salary_currency || 'INR',
      required_skills: job.required_skills.join(', '),
      preferred_skills: job.preferred_skills.join(', '),
    });
    setJobFormError('');
    setIsJobModalOpen(true);
  };

  const handleSaveJob = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !selectedOrgId) return;
    setJobFormError('');
    setJobFormSaving(true);

    const parseList = (str: string) =>
      str
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

    const reqSkills = parseList(jobFormData.required_skills);
    const prefSkills = parseList(jobFormData.preferred_skills);

    // Client validation: skills overlap
    const reqSet = new Set(reqSkills.map((s) => s.toLowerCase()));
    for (const p of prefSkills) {
      if (reqSet.has(p.toLowerCase())) {
        setJobFormError(`Skill "${p}" cannot appear in both required and preferred skills.`);
        setJobFormSaving(false);
        return;
      }
    }

    // Client validation: ranges
    const expMin = jobFormData.experience_min ? parseInt(jobFormData.experience_min) : null;
    const expMax = jobFormData.experience_max ? parseInt(jobFormData.experience_max) : null;
    if (expMin !== null && expMax !== null && expMin > expMax) {
      setJobFormError('Minimum experience cannot exceed maximum experience.');
      setJobFormSaving(false);
      return;
    }

    const salMin = jobFormData.salary_min ? parseFloat(jobFormData.salary_min) : null;
    const salMax = jobFormData.salary_max ? parseFloat(jobFormData.salary_max) : null;
    if (salMin !== null && salMax !== null && salMin > salMax) {
      setJobFormError('Minimum salary cannot exceed maximum salary.');
      setJobFormSaving(false);
      return;
    }

    const payload = {
      title: jobFormData.title.trim(),
      department: jobFormData.department.trim() || null,
      description: jobFormData.description.trim(),
      responsibilities: jobFormData.responsibilities.trim() || null,
      qualifications: jobFormData.qualifications.trim() || null,
      location: jobFormData.location.trim() || null,
      workplace_type: jobFormData.workplace_type,
      employment_type: jobFormData.employment_type,
      experience_min: expMin,
      experience_max: expMax,
      salary_min: salMin,
      salary_max: salMax,
      salary_currency: jobFormData.salary_currency.trim() || 'INR',
      required_skills: reqSkills,
      preferred_skills: prefSkills,
    };

    try {
      const endpoint = editingJob
        ? `${API_BASE}/api/v1/organizations/${selectedOrgId}/jobs/${editingJob.id}`
        : `${API_BASE}/api/v1/organizations/${selectedOrgId}/jobs`;
      const method = editingJob ? 'PATCH' : 'POST';

      const res = await fetch(endpoint, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to save job');
      }

      setIsJobModalOpen(false);
      await fetchRecruiterJobs();
      if (activeTab === 'public-jobs') fetchPublicJobs();
      setRecruiterActionMessage(editingJob ? 'Job updated successfully!' : 'Job created as DRAFT!');
      setTimeout(() => setRecruiterActionMessage(''), 4000);
    } catch (err: any) {
      setJobFormError(err.message || 'Error saving job');
    } finally {
      setJobFormSaving(false);
    }
  };

  const handleJobLifecycleAction = async (jobId: string, action: 'publish' | 'close' | 'archive') => {
    if (!token || !selectedOrgId) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/organizations/${selectedOrgId}/jobs/${jobId}/${action}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `Failed to ${action} job`);

      setRecruiterActionMessage(`Job status transitioned to ${data.status}!`);
      setTimeout(() => setRecruiterActionMessage(''), 4000);
      await fetchRecruiterJobs();
      fetchPublicJobs();
    } catch (err: any) {
      alert(`Action error: ${err.message}`);
    }
  };

  // ==========================================
  // Milestone 5: Application Operations
  // ==========================================

  const fetchMyApplications = async () => {
    if (!token) return;
    setMyApplicationsLoading(true);
    try {
      const params = new URLSearchParams();
      if (myAppStatusFilter) params.append('status', myAppStatusFilter);
      if (myAppKeyword.trim()) params.append('keyword', myAppKeyword.trim());
      const res = await fetch(`${API_BASE}/api/v1/applications/me?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setMyApplications(data.items || []);
      }
    } catch (err) {
      console.error('Failed to fetch candidate applications', err);
    } finally {
      setMyApplicationsLoading(false);
    }
  };

  const fetchRecruiterApplications = async () => {
    if (!token || !selectedOrgId) return;
    setRecruiterAppsLoading(true);
    try {
      const params = new URLSearchParams();
      if (recruiterAppJobFilter) params.append('job_id', recruiterAppJobFilter);
      if (recruiterAppStatusFilter) params.append('status', recruiterAppStatusFilter);
      if (recruiterAppKeyword.trim()) params.append('keyword', recruiterAppKeyword.trim());
      const res = await fetch(
        `${API_BASE}/api/v1/organizations/${selectedOrgId}/applications?${params.toString()}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setRecruiterApplications(data.items || []);
      }
    } catch (err) {
      console.error('Failed to fetch recruiter applications', err);
    } finally {
      setRecruiterAppsLoading(false);
    }
  };

  useEffect(() => {
    if (token && activeTab === 'candidate' && candidateSubTab === 'my-applications') {
      fetchMyApplications();
    }
  }, [token, activeTab, candidateSubTab, myAppStatusFilter, myAppKeyword]);

  useEffect(() => {
    if (token && selectedOrgId && recruiterSubTab === 'applications') {
      fetchRecruiterApplications();
    }
  }, [token, selectedOrgId, recruiterSubTab, recruiterAppJobFilter, recruiterAppStatusFilter, recruiterAppKeyword]);

  // AI Screening Handlers
  const fetchScreeningRuns = async (jobId: string) => {
    if (!token || !selectedOrgId || !jobId) return;
    setScreeningRunsLoading(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/organizations/${selectedOrgId}/jobs/${jobId}/screenings?limit=20`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        const runs: ScreeningRun[] = data.items || [];
        setScreeningRuns(runs);
        if (runs.length > 0) {
          // If current selected run is not in runs, pick the first one
          if (!runs.some((r) => r.id === selectedRunId)) {
            setSelectedRunId(runs[0].id);
          }
        } else {
          setSelectedRunId('');
          setScreeningResults([]);
        }
      }
    } catch (err) {
      console.error('Failed to fetch screening runs', err);
    } finally {
      setScreeningRunsLoading(false);
    }
  };

  const fetchScreeningResults = async (runId: string) => {
    if (!token || !selectedOrgId || !runId) return;
    setScreeningResultsLoading(true);
    try {
      const params = new URLSearchParams();
      if (screeningScoreFilter) params.append('score_min', screeningScoreFilter);
      const res = await fetch(
        `${API_BASE}/api/v1/organizations/${selectedOrgId}/screenings/${runId}/results?${params.toString()}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setScreeningResults(data.items || []);
      }
    } catch (err) {
      console.error('Failed to fetch screening results', err);
    } finally {
      setScreeningResultsLoading(false);
    }
  };

  const openResultDetailModal = async (resultId: string) => {
    if (!token || !selectedOrgId) return;
    setResultDetailLoading(true);
    setIsResultDetailModalOpen(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/organizations/${selectedOrgId}/screenings/results/${resultId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setSelectedResultDetail(data);
      }
    } catch (err) {
      console.error('Failed to fetch screening result detail', err);
    } finally {
      setResultDetailLoading(false);
    }
  };

  const toggleExpandResult = (resultId: string) => {
    setExpandedResultIds((prev) => ({
      ...prev,
      [resultId]: !prev[resultId],
    }));
  };

  const handleRetryInsight = async (resultId: string) => {
    if (!token || !selectedOrgId || !resultId) return;
    setRetryingInsight(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/organizations/${selectedOrgId}/screenings/results/${resultId}/insight/retry`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
        }
      );
      if (res.ok) {
        const updatedInsight: ScreeningInsight = await res.json();
        if (selectedResultDetail && selectedResultDetail.id === resultId) {
          setSelectedResultDetail({
            ...selectedResultDetail,
            insight: updatedInsight,
          });
        }
        if (selectedRunId) {
          await fetchScreeningResults(selectedRunId);
        }
      }
    } catch (err) {
      console.error('Failed to retry candidate insight', err);
    } finally {
      setRetryingInsight(false);
    }
  };

  const openScreeningForJob = (job: RecruiterJob) => {
    setScreeningJobId(job.id);
    setRecruiterSubTab('screening');
    fetchScreeningRuns(job.id);
  };

  const handleOpenTriggerModal = (job?: RecruiterJob) => {
    const targetJob = job || recruiterJobs.find((j) => j.id === screeningJobId) || recruiterJobs[0] || null;
    setTriggerJob(targetJob);
    setTriggerError('');
    setIsTriggerModalOpen(true);
  };

  const handleTriggerScreening = async () => {
    if (!token || !selectedOrgId || !triggerJob) return;
    setTriggerLoading(true);
    setTriggerError('');
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/organizations/${selectedOrgId}/jobs/${triggerJob.id}/screenings`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({}),
        }
      );
      if (res.ok || res.status === 201 || res.status === 202) {
        const newRun = await res.json();
        setRecruiterActionMessage(`Screening run triggered successfully for "${triggerJob.title}"!`);
        setIsTriggerModalOpen(false);
        setScreeningJobId(triggerJob.id);
        setRecruiterSubTab('screening');
        await fetchScreeningRuns(triggerJob.id);
        setSelectedRunId(newRun.id);
        await fetchScreeningResults(newRun.id);
      } else {
        const errData = await res.json().catch(() => ({}));
        setTriggerError(errData.detail || 'Failed to trigger candidate screening run');
      }
    } catch (err: any) {
      setTriggerError(err.message || 'Network error triggering screening');
    } finally {
      setTriggerLoading(false);
    }
  };

  useEffect(() => {
    if (token && selectedOrgId && recruiterSubTab === 'screening') {
      if (!screeningJobId && recruiterJobs.length > 0) {
        setScreeningJobId(recruiterJobs[0].id);
        fetchScreeningRuns(recruiterJobs[0].id);
      } else if (screeningJobId) {
        fetchScreeningRuns(screeningJobId);
      }
    }
  }, [token, selectedOrgId, recruiterSubTab, screeningJobId, recruiterJobs]);

  useEffect(() => {
    if (token && selectedOrgId && recruiterSubTab === 'screening' && selectedRunId) {
      fetchScreeningResults(selectedRunId);
    }
  }, [token, selectedOrgId, recruiterSubTab, selectedRunId, screeningScoreFilter]);

  const openApplyModal = (job: PublicJob) => {
    if (!token) {
      setActiveTab('candidate');
      return;
    }
    setApplyJob(job);
    const activeResume = resumes.find((r) => r.is_active);
    setSelectedResumeId(activeResume ? activeResume.id : resumes[0]?.id || '');
    setCoverLetter('');
    setApplyError('');
    setApplySuccess('');
    setIsApplyModalOpen(true);
  };

  const handleApplySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !applyJob || !selectedResumeId) return;
    setApplyLoading(true);
    setApplyError('');
    setApplySuccess('');
    try {
      const res = await fetch(`${API_BASE}/api/v1/jobs/${applyJob.id}/applications`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          resume_id: selectedResumeId,
          cover_letter: coverLetter.trim() || undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to submit application');
      }
      setApplySuccess('Application successfully submitted! The exact resume version has been pinned.');
      fetchMyApplications();
      setTimeout(() => {
        setIsApplyModalOpen(false);
        setApplySuccess('');
      }, 2500);
    } catch (err: any) {
      setApplyError(err.message || 'Error submitting application');
    } finally {
      setApplyLoading(false);
    }
  };

  const handleWithdrawApplication = async (appId: string) => {
    if (!confirm('Are you sure you want to withdraw this application? This action cannot be undone.')) {
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/v1/applications/${appId}/withdraw`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to withdraw application');
      alert('Application withdrawn successfully.');
      fetchMyApplications();
      if (selectedCandidateApp?.id === appId) {
        setSelectedCandidateApp(null);
      }
    } catch (err: any) {
      alert(`Withdrawal error: ${err.message}`);
    }
  };

  const handleDownloadSubmittedResume = async (appId: string, filename: string) => {
    if (!token || !selectedOrgId) return;
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/organizations/${selectedOrgId}/applications/${appId}/resume`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) throw new Error('Failed to download resume file');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || 'submitted_resume.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(`Download error: ${err.message}`);
    }
  };

  const openRecruiterAppDetail = async (app: RecruiterApplication) => {
    if (!token || !selectedOrgId) return;
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/organizations/${selectedOrgId}/applications/${app.id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setSelectedRecruiterAppDetail(data);
        setStatusUpdateVal('');
        setStatusUpdateNote('');
        setStatusUpdateError('');
        setIsRecruiterAppModalOpen(true);
      }
    } catch (err) {
      console.error('Failed to fetch application detail', err);
    }
  };

  const handleUpdateAppStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !selectedOrgId || !selectedRecruiterAppDetail || !statusUpdateVal) return;
    setStatusUpdating(true);
    setStatusUpdateError('');
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/organizations/${selectedOrgId}/applications/${selectedRecruiterAppDetail.id}/status`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            status: statusUpdateVal,
            internal_note: statusUpdateNote.trim() || undefined,
          }),
        }
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to update application status');
      setSelectedRecruiterAppDetail(data);
      setStatusUpdateVal('');
      setStatusUpdateNote('');
      fetchRecruiterApplications();
      setRecruiterActionMessage(`Application status updated to ${data.status}!`);
      setTimeout(() => setRecruiterActionMessage(''), 4000);
    } catch (err: any) {
      setStatusUpdateError(err.message || 'Status update error');
    } finally {
      setStatusUpdating(false);
    }
  };

  // Candidate Profile operations
  const fetchProfile = async () => {
    if (!token) return;
    setProfileLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/candidates/me/profile`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setProfile(data);
        setProfileForm({
          phone: data.phone || '',
          location: data.location || '',
          headline: data.headline || '',
          professional_summary: data.professional_summary || '',
        });
      } else if (res.status === 404) {
        setProfile(null);
      }
    } catch (err) {
      console.error('Failed to fetch profile', err);
    } finally {
      setProfileLoading(false);
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setProfileSaving(true);
    setProfileMessage('');

    try {
      const isCreate = !profile;
      const endpoint = '/api/v1/candidates/me/profile';
      const method = isCreate ? 'POST' : 'PATCH';

      const res = await fetch(`${API_BASE}${endpoint}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(profileForm),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to save profile');

      setProfile(data);
      setProfileMessage('Profile saved successfully!');
      setTimeout(() => setProfileMessage(''), 3000);
    } catch (err: any) {
      setProfileMessage(`Error: ${err.message}`);
    } finally {
      setProfileSaving(false);
    }
  };

  // Resume operations
  const fetchResumes = async () => {
    if (!token) return;
    setResumesLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/resumes`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setResumes(data);
      }
    } catch (err) {
      console.error('Failed to fetch resumes', err);
    } finally {
      setResumesLoading(false);
    }
  };

  const handleUploadResume = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !token) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadError('Only PDF documents are supported.');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setUploadError('File exceeds 5MB limit.');
      return;
    }

    setUploading(true);
    setUploadError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/api/v1/resumes/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Upload failed');
      }

      await fetchResumes();
      setSelectedResume(data);
    } catch (err: any) {
      setUploadError(err.message || 'Failed to upload and parse resume');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleSetActive = async (resumeId: string) => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/resumes/${resumeId}/active`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        await fetchResumes();
      }
    } catch (err) {
      console.error('Failed to set active resume', err);
    }
  };

  const handleDownload = async (resumeId: string) => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/resumes/${resumeId}/download`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Download failed');

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `resume-${resumeId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      console.error('Download error', err);
    }
  };

  const handleDeleteResume = async (resumeId: string, filename: string) => {
    if (!token) return;
    if (!confirm(`Are you sure you want to delete ${filename}?`)) return;

    try {
      const res = await fetch(`${API_BASE}/api/v1/resumes/${resumeId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        if (selectedResume?.id === resumeId) setSelectedResume(null);
        await fetchResumes();
      }
    } catch (err) {
      console.error('Failed to delete resume', err);
    }
  };

  const handleViewResume = async (resumeId: string) => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/resumes/${resumeId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedResume(data);
      }
    } catch (err) {
      console.error('Failed to fetch resume details', err);
    }
  };

  // Milestone 7: Career Guidance Handlers
  const fetchResumeAnalyses = async (resumeId: string) => {
    if (!token || !resumeId) return;
    setAnalysesLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/resumes/${resumeId}/analyses`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setAnalysesList(data);
      }
    } catch (err) {
      console.error('Failed to fetch resume analyses', err);
    } finally {
      setAnalysesLoading(false);
    }
  };

  const fetchAnalysisDetail = async (analysisId: string) => {
    if (!token || !analysisId) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/analyses/${analysisId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentAnalysis(data);
      }
    } catch (err) {
      console.error('Failed to fetch analysis details', err);
    }
  };

  const handleStartAnalysis = async () => {
    if (!token || !selectedAnalysisResumeId) return;
    setAnalysisInProgress(true);
    setAnalysisError('');
    try {
      const res = await fetch(`${API_BASE}/api/v1/resumes/${selectedAnalysisResumeId}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          target_role: targetRoleInput.trim() || null,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setAnalysisError(data.detail || 'Analysis request failed');
      } else {
        setCurrentAnalysis(data);
        fetchResumeAnalyses(selectedAnalysisResumeId);
      }
    } catch (err: any) {
      setAnalysisError(err.message || 'Network error initiating analysis');
    } finally {
      setAnalysisInProgress(false);
    }
  };

  const handleRetryAnalysis = async (analysisId: string) => {
    if (!token || !analysisId) return;
    setRetryingAnalysisId(analysisId);
    try {
      const res = await fetch(`${API_BASE}/api/v1/analyses/${analysisId}/retry`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (res.ok) {
        setCurrentAnalysis(data);
        if (selectedAnalysisResumeId) {
          fetchResumeAnalyses(selectedAnalysisResumeId);
        }
      } else {
        alert(data.detail || 'Failed to retry analysis');
      }
    } catch (err) {
      console.error('Failed to retry analysis', err);
    } finally {
      setRetryingAnalysisId(null);
    }
  };

  // Milestone 8: Candidate AI Career Assistant Handlers
  const fetchConversations = async () => {
    if (!token) return;
    setConversationsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/career/conversations`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setConversationsList(data);
      }
    } catch (err) {
      console.error('Failed to fetch career conversations', err);
    } finally {
      setConversationsLoading(false);
    }
  };

  const fetchConversationDetail = async (convId: string) => {
    if (!token || !convId) return;
    setActiveConvLoading(true);
    setChatError('');
    try {
      const res = await fetch(`${API_BASE}/api/v1/career/conversations/${convId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setActiveConversation(data);
      }
    } catch (err) {
      console.error('Failed to fetch conversation detail', err);
    } finally {
      setActiveConvLoading(false);
    }
  };

  const handleCreateConversation = async () => {
    if (!token) return;
    setCreatingConv(true);
    setChatError('');
    try {
      const res = await fetch(`${API_BASE}/api/v1/career/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          resume_id: newConvResumeId || null,
          target_role: newConvTargetRole.trim() || null,
          conversation_purpose: newConvPurpose,
          title: newConvTitle.trim() || null,
          initial_message: newConvInitialMsg.trim() || null,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.detail || 'Failed to create conversation');
      } else {
        setIsNewConvModalOpen(false);
        setNewConvInitialMsg('');
        setNewConvTitle('');
        await fetchConversations();
        await fetchConversationDetail(data.id);
      }
    } catch (err) {
      console.error('Failed to create conversation', err);
    } finally {
      setCreatingConv(false);
    }
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!token || !activeConversation || !messageInput.trim() || sendingMessage) return;

    const content = messageInput.trim();
    setMessageInput('');
    setSendingMessage(true);
    setChatError('');

    const tempUserMsg: CareerMessageItem = {
      id: 'temp-' + Date.now(),
      conversation_id: activeConversation.id,
      role: 'USER',
      content,
      created_at: new Date().toISOString(),
    };
    setActiveConversation((prev) =>
      prev ? { ...prev, messages: [...prev.messages, tempUserMsg] } : prev
    );

    try {
      const res = await fetch(`${API_BASE}/api/v1/career/conversations/${activeConversation.id}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ content, include_m7_analysis: true }),
      });
      const data = await res.json();
      if (!res.ok) {
        setChatError(data.detail || 'Failed to send message');
        fetchConversationDetail(activeConversation.id);
      } else {
        setActiveConversation((prev) => {
          if (!prev) return prev;
          const filtered = prev.messages.filter((m) => m.id !== tempUserMsg.id);
          return {
            ...prev,
            messages: [...filtered, data.user_message, data.assistant_message],
            updated_at: new Date().toISOString(),
          };
        });
        fetchConversations();
      }
    } catch (err: any) {
      setChatError(err.message || 'Network error sending message');
    } finally {
      setSendingMessage(false);
    }
  };

  const handleDeleteConversation = async (convId: string, title: string) => {
    if (!token) return;
    if (!confirm(`Delete conversation "${title}"?`)) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/career/conversations/${convId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        if (activeConversation?.id === convId) {
          setActiveConversation(null);
        }
        fetchConversations();
      }
    } catch (err) {
      console.error('Failed to delete conversation', err);
    }
  };

  // Recruiter Match execution
  const handleMatch = async () => {
    if (!jdText.trim()) return;
    setMatchLoading(true);
    setMatchError('');

    try {
      const response = await fetch(`${API_BASE}/match`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: jdText }),
      });

      if (!response.ok) throw new Error('API server rejected the runtime execution schema.');
      const data = await response.json();
      setMatchCandidates(data.candidate || []);
    } catch (err: any) {
      setMatchError(err.message || 'Failed to sync with match pipeline.');
    } finally {
      setMatchLoading(false);
    }
  };

  const activeOrg = userOrgs.find((o) => o.id === selectedOrgId);
  const isRecruiterOrAbove = activeOrg?.role && ['OWNER', 'ADMIN', 'RECRUITER'].includes(activeOrg.role);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 font-sans">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-950/70 backdrop-blur px-8 py-4 flex flex-wrap justify-between items-center gap-4 sticky top-0 z-20">
        <div className="flex items-center gap-6">
          <h1 className="text-xl font-bold text-indigo-400 tracking-wide flex items-center gap-2">
            <span>✨</span> TalentLens AI Platform
          </h1>
          <nav className="flex gap-2">
            <button
              onClick={() => setActiveTab('public-jobs')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === 'public-jobs'
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              Browse Jobs
            </button>
            <button
              onClick={() => setActiveTab('candidate')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === 'candidate'
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              Candidate Portal
            </button>
            <button
              onClick={() => setActiveTab('recruiter')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === 'recruiter'
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              Recruiter Workspace
            </button>
          </nav>
        </div>

        {/* User Status / Logout */}
        {token ? (
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-400">
              Logged in as <strong className="text-slate-200">{profile?.email || 'Authenticated User'}</strong>
            </span>
            <button
              onClick={handleLogout}
              className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition"
            >
              Log Out
            </button>
          </div>
        ) : (
          <span className="text-xs text-amber-400 bg-amber-950/40 border border-amber-800/50 px-3 py-1 rounded-full">
            Not Authenticated
          </span>
        )}
      </header>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto p-8">
        {/* TAB 1: PUBLIC JOB BOARD */}
        {activeTab === 'public-jobs' && (
          <div className="flex flex-col gap-8">
            <div>
              <h2 className="text-2xl font-bold text-slate-100 mb-1">Explore Open Positions</h2>
              <p className="text-sm text-slate-400">
                Discover published opportunities across top engineering teams.
              </p>
            </div>

            {/* Filter Bar */}
            <div className="bg-slate-950/60 border border-slate-800 rounded-2xl p-6 shadow-lg flex flex-col gap-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <input
                  type="text"
                  placeholder="Search title, department, description..."
                  value={publicKeyword}
                  onChange={(e) => setPublicKeyword(e.target.value)}
                  className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
                <input
                  type="text"
                  placeholder="Location (e.g. Bengaluru, Remote)..."
                  value={publicLocation}
                  onChange={(e) => setPublicLocation(e.target.value)}
                  className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
                <input
                  type="text"
                  placeholder="Required Skill (e.g. Python, React)..."
                  value={publicSkill}
                  onChange={(e) => setPublicSkill(e.target.value)}
                  className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-slate-800/60">
                <div className="flex flex-wrap gap-3">
                  <select
                    value={publicWorkplace}
                    onChange={(e) => setPublicWorkplace(e.target.value)}
                    className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="">All Workplace Types</option>
                    <option value="ONSITE">Onsite</option>
                    <option value="REMOTE">Remote</option>
                    <option value="HYBRID">Hybrid</option>
                  </select>

                  <select
                    value={publicEmployment}
                    onChange={(e) => setPublicEmployment(e.target.value)}
                    className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="">All Employment Types</option>
                    <option value="FULL_TIME">Full Time</option>
                    <option value="PART_TIME">Part Time</option>
                    <option value="CONTRACT">Contract</option>
                    <option value="INTERNSHIP">Internship</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">Sort:</span>
                  <select
                    value={publicSort}
                    onChange={(e) => setPublicSort(e.target.value as 'newest' | 'oldest')}
                    className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="newest">Newest First</option>
                    <option value="oldest">Oldest First</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Public Job Listings */}
            {publicLoading ? (
              <div className="text-center py-12 text-indigo-400 animate-pulse text-sm">
                Fetching open roles...
              </div>
            ) : publicError ? (
              <div className="p-4 bg-red-950/60 border border-red-800 text-red-300 text-sm rounded-xl">
                {publicError}
              </div>
            ) : publicJobs.length === 0 ? (
              <div className="text-center py-16 text-slate-500 border border-dashed border-slate-800 rounded-2xl">
                <p className="text-base font-medium">No published jobs match your filters.</p>
                <p className="text-xs text-slate-600 mt-1">Try adjusting keywords or clearing specific constraints.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {publicJobs.map((job) => (
                  <div
                    key={job.id}
                    onClick={() => setSelectedPublicJob(job)}
                    className="bg-slate-950/50 border border-slate-800 hover:border-indigo-500/70 rounded-2xl p-6 transition cursor-pointer flex flex-col justify-between gap-4 group"
                  >
                    <div>
                      <div className="flex justify-between items-start gap-2 mb-2">
                        <h3 className="text-lg font-bold text-slate-100 group-hover:text-indigo-400 transition">
                          {job.title}
                        </h3>
                        <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800 font-semibold whitespace-nowrap">
                          {job.employment_type.replace('_', ' ')}
                        </span>
                      </div>

                      <div className="text-sm font-medium text-indigo-300 mb-3 flex items-center gap-2">
                        <span>🏢</span> {job.organization_name}
                        {job.department && <span className="text-slate-400">· {job.department}</span>}
                      </div>

                      <div className="flex flex-wrap gap-2 text-xs text-slate-400 mb-4">
                        {job.location && (
                          <span className="flex items-center gap-1 bg-slate-900 px-2 py-1 rounded">
                            📍 {job.location}
                          </span>
                        )}
                        <span className="flex items-center gap-1 bg-slate-900 px-2 py-1 rounded">
                          💼 {job.workplace_type}
                        </span>
                        {(job.salary_min !== null || job.salary_max !== null) && (
                          <span className="flex items-center gap-1 bg-slate-900 px-2 py-1 rounded text-emerald-400 font-mono">
                            💰 {job.salary_min?.toLocaleString()} - {job.salary_max?.toLocaleString()} {job.salary_currency}
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-slate-300 line-clamp-3 mb-4">
                        {job.description}
                      </p>
                    </div>

                    <div>
                      <div className="flex flex-wrap gap-1.5 mb-3">
                        {job.required_skills.slice(0, 5).map((skill, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 text-[11px] bg-indigo-950/80 text-indigo-300 border border-indigo-800/80 rounded"
                          >
                            {skill}
                          </span>
                        ))}
                        {job.required_skills.length > 5 && (
                          <span className="text-[10px] text-slate-500 self-center">
                            +{job.required_skills.length - 5} more
                          </span>
                        )}
                      </div>

                      <div className="flex justify-between items-center text-[11px] text-slate-500 border-t border-slate-800/80 pt-3">
                        <span>
                          Published: {job.published_at ? new Date(job.published_at).toLocaleDateString() : 'Recent'}
                        </span>
                        <span className="text-indigo-400 group-hover:translate-x-1 transition font-medium">
                          View Details →
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Public Job Details Modal */}
            {selectedPublicJob && (
              <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 shadow-2xl flex flex-col gap-4">
                  <div className="flex justify-between items-start border-b border-slate-800 pb-3">
                    <div>
                      <h2 className="text-xl font-bold text-slate-100">{selectedPublicJob.title}</h2>
                      <div className="text-sm text-indigo-400 font-medium">
                        {selectedPublicJob.organization_name} {selectedPublicJob.department && `· ${selectedPublicJob.department}`}
                      </div>
                    </div>
                    <button
                      onClick={() => setSelectedPublicJob(null)}
                      className="text-slate-400 hover:text-slate-100 text-lg font-bold p-1"
                    >
                      ✕
                    </button>
                  </div>

                  <div className="flex flex-wrap gap-2 text-xs">
                    <span className="bg-slate-800 text-slate-200 px-2.5 py-1 rounded-full">
                      📍 {selectedPublicJob.location || 'Location Not Specified'}
                    </span>
                    <span className="bg-slate-800 text-slate-200 px-2.5 py-1 rounded-full">
                      💼 {selectedPublicJob.workplace_type}
                    </span>
                    <span className="bg-slate-800 text-slate-200 px-2.5 py-1 rounded-full">
                      ⏱ {selectedPublicJob.employment_type.replace('_', ' ')}
                    </span>
                    {(selectedPublicJob.experience_min !== null || selectedPublicJob.experience_max !== null) && (
                      <span className="bg-slate-800 text-slate-200 px-2.5 py-1 rounded-full">
                        🎓 {selectedPublicJob.experience_min ?? 0} - {selectedPublicJob.experience_max ?? '+'} Yrs Experience
                      </span>
                    )}
                    {(selectedPublicJob.salary_min !== null || selectedPublicJob.salary_max !== null) && (
                      <span className="bg-emerald-950 text-emerald-400 border border-emerald-800 px-2.5 py-1 rounded-full font-mono">
                        💰 {selectedPublicJob.salary_min?.toLocaleString()} - {selectedPublicJob.salary_max?.toLocaleString()} {selectedPublicJob.salary_currency}
                      </span>
                    )}
                  </div>

                  <div className="space-y-4 text-xs text-slate-300">
                    <div>
                      <h4 className="font-semibold text-slate-100 text-sm mb-1">Description</h4>
                      <p className="whitespace-pre-line leading-relaxed text-slate-300">{selectedPublicJob.description}</p>
                    </div>

                    {selectedPublicJob.responsibilities && (
                      <div>
                        <h4 className="font-semibold text-slate-100 text-sm mb-1">Responsibilities</h4>
                        <p className="whitespace-pre-line leading-relaxed text-slate-300">{selectedPublicJob.responsibilities}</p>
                      </div>
                    )}

                    {selectedPublicJob.qualifications && (
                      <div>
                        <h4 className="font-semibold text-slate-100 text-sm mb-1">Qualifications</h4>
                        <p className="whitespace-pre-line leading-relaxed text-slate-300">{selectedPublicJob.qualifications}</p>
                      </div>
                    )}

                    <div>
                      <h4 className="font-semibold text-slate-100 text-sm mb-1.5">Required Skills</h4>
                      <div className="flex flex-wrap gap-1.5">
                        {selectedPublicJob.required_skills.map((s, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 bg-indigo-950 text-indigo-300 border border-indigo-800 rounded font-medium"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>

                    {selectedPublicJob.preferred_skills.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-slate-100 text-sm mb-1.5">Preferred Skills</h4>
                        <div className="flex flex-wrap gap-1.5">
                          {selectedPublicJob.preferred_skills.map((s, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-0.5 bg-slate-800 text-slate-300 border border-slate-700 rounded"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="border-t border-slate-800 pt-3 flex justify-between items-center text-xs text-slate-500">
                    <span>Published: {selectedPublicJob.published_at ? new Date(selectedPublicJob.published_at).toLocaleDateString() : 'Recent'}</span>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setSelectedPublicJob(null)}
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition"
                      >
                        Close
                      </button>
                      <button
                        onClick={() => {
                          const job = selectedPublicJob;
                          setSelectedPublicJob(null);
                          openApplyModal(job);
                        }}
                        className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg shadow-md transition flex items-center gap-1.5"
                      >
                        <span>🚀</span> Apply Now
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: CANDIDATE PORTAL */}
        {activeTab === 'candidate' && (
          <div>
            {!token ? (
              /* Authentication Banner */
              <div className="max-w-md mx-auto bg-slate-950/80 border border-slate-800 rounded-2xl p-8 shadow-xl mt-8">
                <h2 className="text-2xl font-bold text-slate-100 mb-2">
                  {isRegisterMode ? 'Create Candidate Account' : 'Sign In to Candidate Portal'}
                </h2>
                <p className="text-sm text-slate-400 mb-6">
                  Manage your candidate profile, upload resumes, and view AI-parsed skills.
                </p>

                {authError && (
                  <div className="mb-4 p-3 bg-red-950/50 border border-red-800 text-red-300 text-sm rounded-lg">
                    {authError}
                  </div>
                )}

                <form onSubmit={handleAuth} className="flex flex-col gap-4">
                  {isRegisterMode && (
                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1">Full Name</label>
                      <input
                        type="text"
                        required
                        value={authFullName}
                        onChange={(e) => setAuthFullName(e.target.value)}
                        placeholder="Jane Doe"
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  )}
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">Email Address</label>
                    <input
                      type="email"
                      required
                      value={authEmail}
                      onChange={(e) => setAuthEmail(e.target.value)}
                      placeholder="jane@example.com"
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">Password</label>
                    <input
                      type="password"
                      required
                      value={authPassword}
                      onChange={(e) => setAuthPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full mt-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2.5 rounded-lg transition"
                  >
                    {isRegisterMode ? 'Register Account' : 'Sign In'}
                  </button>
                </form>

                <div className="mt-6 text-center text-xs text-slate-400">
                  {isRegisterMode ? (
                    <>
                      Already have an account?{' '}
                      <button
                        onClick={() => setIsRegisterMode(false)}
                        className="text-indigo-400 hover:underline font-semibold"
                      >
                        Sign In
                      </button>
                    </>
                  ) : (
                    <>
                      New to TalentLens?{' '}
                      <button
                        onClick={() => setIsRegisterMode(true)}
                        className="text-indigo-400 hover:underline font-semibold"
                      >
                        Register
                      </button>
                    </>
                  )}
                </div>
              </div>
            ) : (
              /* CANDIDATE PORTAL CONTENT */
              <div className="flex flex-col gap-6">
                {/* Candidate Subtabs */}
                <div className="bg-slate-950/60 border border-slate-800 rounded-2xl p-4 flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Candidate Portal:</span>
                    <span className="text-sm font-bold text-slate-200">{profile?.full_name || profile?.email || 'Candidate'}</span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setCandidateSubTab('profile-resumes')}
                      className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
                        candidateSubTab === 'profile-resumes'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      Profile & Resumes
                    </button>
                    <button
                      onClick={() => {
                        setCandidateSubTab('career-guidance');
                        if (!selectedAnalysisResumeId && resumes.length > 0) {
                          const activeRes = resumes.find((r) => r.is_active) || resumes[0];
                          setSelectedAnalysisResumeId(activeRes.id);
                          fetchResumeAnalyses(activeRes.id);
                        }
                      }}
                      className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
                        candidateSubTab === 'career-guidance'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      💡 Career Guidance
                    </button>
                    <button
                      onClick={() => {
                        setCandidateSubTab('career-assistant');
                        fetchConversations();
                        if (!newConvResumeId && resumes.length > 0) {
                          const activeRes = resumes.find((r) => r.is_active) || resumes[0];
                          setNewConvResumeId(activeRes.id);
                        }
                      }}
                      className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
                        candidateSubTab === 'career-assistant'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      🤖 Career Assistant
                    </button>
                    <button
                      onClick={() => setCandidateSubTab('my-applications')}
                      className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
                        candidateSubTab === 'my-applications'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      My Applications ({myApplications.length})
                    </button>
                  </div>
                </div>

                {candidateSubTab === 'profile-resumes' ? (
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Profile Management */}
                <div className="bg-slate-950/40 border border-slate-800 rounded-2xl p-6 h-fit">
                  <h2 className="text-lg font-bold text-slate-200 mb-1 flex items-center gap-2">
                    <span>👤</span> Candidate Profile
                  </h2>
                  <p className="text-xs text-slate-400 mb-6">
                    Your independent candidate identity. Accessible only by you.
                  </p>

                  {profileLoading && (
                    <div className="mb-4 text-xs text-indigo-400 animate-pulse">
                      Loading profile data...
                    </div>
                  )}

                  {profileMessage && (
                    <div
                      className={`mb-4 p-3 text-xs rounded-lg ${
                        profileMessage.startsWith('Error')
                          ? 'bg-red-950/50 border border-red-800 text-red-300'
                          : 'bg-emerald-950/50 border border-emerald-800 text-emerald-300'
                      }`}
                    >
                      {profileMessage}
                    </div>
                  )}

                  <form onSubmit={handleSaveProfile} className="flex flex-col gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1">Headline</label>
                      <input
                        type="text"
                        value={profileForm.headline}
                        onChange={(e) => setProfileForm({ ...profileForm, headline: e.target.value })}
                        placeholder="e.g. Senior Full Stack Engineer"
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1">Location</label>
                      <input
                        type="text"
                        value={profileForm.location}
                        onChange={(e) => setProfileForm({ ...profileForm, location: e.target.value })}
                        placeholder="e.g. San Francisco, CA"
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1">Phone</label>
                      <input
                        type="text"
                        value={profileForm.phone}
                        onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                        placeholder="e.g. +1-555-0199"
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1">Professional Summary</label>
                      <textarea
                        rows={4}
                        value={profileForm.professional_summary}
                        onChange={(e) => setProfileForm({ ...profileForm, professional_summary: e.target.value })}
                        placeholder="Summary of experience, technical focus, and achievements..."
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 resize-none"
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={profileSaving}
                      className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium py-2 rounded-lg text-sm transition"
                    >
                      {profileSaving ? 'Saving...' : profile ? 'Update Profile' : 'Create Profile'}
                    </button>
                  </form>
                </div>

                {/* Middle & Right: Resume Upload, Versions & Parsed Inspector */}
                <div className="lg:col-span-2 flex flex-col gap-6">
                  {/* Resume Upload Box */}
                  <div className="bg-slate-950/40 border border-slate-800 rounded-2xl p-6">
                    <div className="flex justify-between items-center mb-4">
                      <div>
                        <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                          <span>📄</span> Resume Upload & AI Parsing
                        </h2>
                        <p className="text-xs text-slate-400">
                          Upload your PDF resume. PyMuPDF extracts text and Ollama extracts structured skills.
                        </p>
                      </div>
                    </div>

                    {uploadError && (
                      <div className="mb-4 p-3 bg-red-950/50 border border-red-800 text-red-300 text-xs rounded-lg">
                        {uploadError}
                      </div>
                    )}

                    <div className="flex items-center gap-4">
                      <input
                        type="file"
                        ref={fileInputRef}
                        accept=".pdf,application/pdf"
                        onChange={handleUploadResume}
                        disabled={uploading}
                        className="block w-full text-xs text-slate-400 file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 file:cursor-pointer cursor-pointer border border-slate-700 rounded-lg bg-slate-900/60 p-1"
                      />
                      {uploading && (
                        <div className="flex items-center gap-2 text-xs text-indigo-400 font-medium whitespace-nowrap">
                          <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
                          Parsing PDF & AI...
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Resume Versions List */}
                  <div className="bg-slate-950/40 border border-slate-800 rounded-2xl p-6">
                    <h3 className="text-md font-bold text-slate-200 mb-4 flex items-center justify-between">
                      <span>Resume Versions ({resumes.length})</span>
                      <button
                        onClick={fetchResumes}
                        className="text-xs text-indigo-400 hover:text-indigo-300"
                      >
                        Refresh
                      </button>
                    </h3>

                    {resumesLoading ? (
                      <p className="text-xs text-slate-500">Loading versions...</p>
                    ) : resumes.length === 0 ? (
                      <div className="text-center py-8 text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
                        No resumes uploaded yet. Upload a PDF above to get started.
                      </div>
                    ) : (
                      <div className="flex flex-col gap-3">
                        {resumes.map((res) => (
                          <div
                            key={res.id}
                            className={`p-4 rounded-xl border transition flex flex-wrap justify-between items-center gap-4 ${
                              selectedResume?.id === res.id
                                ? 'bg-indigo-950/30 border-indigo-600'
                                : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                            }`}
                          >
                            <div className="flex flex-col gap-1">
                              <div className="flex items-center gap-2">
                                <span className="font-semibold text-sm text-slate-200">
                                  {res.original_filename}
                                </span>
                                {res.is_active && (
                                  <span className="px-2 py-0.5 text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800 rounded-full font-bold">
                                    ACTIVE RESUME
                                  </span>
                                )}
                                <span
                                  className={`px-2 py-0.5 text-[10px] rounded-full font-semibold ${
                                    res.parsing_status === 'COMPLETED'
                                      ? 'bg-indigo-950 text-indigo-400 border border-indigo-800'
                                      : res.parsing_status === 'PROCESSING'
                                      ? 'bg-amber-950 text-amber-400 border border-amber-800'
                                      : 'bg-red-950 text-red-400 border border-red-800'
                                  }`}
                                >
                                  {res.parsing_status}
                                </span>
                              </div>
                              <div className="text-xs text-slate-400 flex gap-4">
                                <span>Uploaded: {new Date(res.created_at).toLocaleDateString()}</span>
                                <span>Size: {(res.file_size / 1024).toFixed(1)} KB</span>
                              </div>
                            </div>

                            {/* Action Buttons */}
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleViewResume(res.id)}
                                className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-700"
                              >
                                Inspect AI Data
                              </button>
                              {!res.is_active && (
                                <button
                                  onClick={() => handleSetActive(res.id)}
                                  className="px-3 py-1.5 text-xs bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-300 border border-indigo-500/50 rounded-lg"
                                >
                                  Make Active
                                </button>
                              )}
                              <button
                                onClick={() => handleDownload(res.id)}
                                className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-700"
                              >
                                Download
                              </button>
                              <button
                                onClick={() => {
                                  setSelectedAnalysisResumeId(res.id);
                                  fetchResumeAnalyses(res.id);
                                  setCandidateSubTab('career-guidance');
                                }}
                                className="px-3 py-1.5 text-xs bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-lg shadow-sm"
                              >
                                💡 Analyze Resume
                              </button>
                              <button
                                onClick={() => handleDeleteResume(res.id, res.original_filename)}
                                className="px-3 py-1.5 text-xs bg-red-950/40 hover:bg-red-900/60 text-red-300 border border-red-800/50 rounded-lg"
                              >
                                Delete
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Selected Resume Details & AI Structured Data Inspector */}
                  {selectedResume && (
                    <div className="bg-slate-950/60 border border-indigo-900/50 rounded-2xl p-6 shadow-xl">
                      <div className="flex justify-between items-start mb-4 border-b border-slate-800 pb-3">
                        <div>
                          <h3 className="text-md font-bold text-indigo-300">
                            Inspecting: {selectedResume.original_filename}
                          </h3>
                          <p className="text-xs text-slate-400 font-mono mt-0.5">
                            SHA-256: {selectedResume.sha256}
                          </p>
                        </div>
                        <button
                          onClick={() => setSelectedResume(null)}
                          className="text-slate-400 hover:text-slate-200 text-sm"
                        >
                          ✕ Close
                        </button>
                      </div>

                      {selectedResume.parsing_status === 'FAILED' && (
                        <div className="mb-4 p-3 bg-red-950/60 border border-red-800 text-red-300 text-xs rounded-lg">
                          <strong>Parsing Error:</strong> {selectedResume.parsing_error || 'Unknown failure'}
                        </div>
                      )}

                      {selectedResume.parsed_data ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
                          {/* Left: General & Skills */}
                          <div className="flex flex-col gap-4">
                            <div className="bg-slate-900/70 p-4 rounded-xl border border-slate-800">
                              <h4 className="font-semibold text-slate-200 mb-2">Identified Candidate</h4>
                              <p><strong className="text-slate-400">Name:</strong> {selectedResume.parsed_data.full_name || 'N/A'}</p>
                              <p><strong className="text-slate-400">Email:</strong> {selectedResume.parsed_data.email || 'N/A'}</p>
                              <p><strong className="text-slate-400">Phone:</strong> {selectedResume.parsed_data.phone || 'N/A'}</p>
                              {selectedResume.parsed_data.professional_summary && (
                                <p className="mt-2 text-slate-300 italic border-l-2 border-indigo-500 pl-2">
                                  "{selectedResume.parsed_data.professional_summary}"
                                </p>
                              )}
                            </div>

                            <div className="bg-slate-900/70 p-4 rounded-xl border border-slate-800">
                              <h4 className="font-semibold text-slate-200 mb-2">Extracted Skills</h4>
                              <div className="flex flex-wrap gap-1.5">
                                {(selectedResume.parsed_data.skills || []).map((skill, idx) => (
                                  <span
                                    key={idx}
                                    className="px-2 py-0.5 bg-indigo-950 text-indigo-300 border border-indigo-800/80 rounded font-medium"
                                  >
                                    {skill}
                                  </span>
                                ))}
                                {(!selectedResume.parsed_data.skills || selectedResume.parsed_data.skills.length === 0) && (
                                  <span className="text-slate-500">None detected</span>
                                )}
                              </div>
                            </div>

                            {selectedResume.parsed_data.certifications && selectedResume.parsed_data.certifications.length > 0 && (
                              <div className="bg-slate-900/70 p-4 rounded-xl border border-slate-800">
                                <h4 className="font-semibold text-slate-200 mb-2">Certifications</h4>
                                <ul className="list-disc list-inside text-slate-300 space-y-1">
                                  {selectedResume.parsed_data.certifications.map((cert, idx) => (
                                    <li key={idx}>{cert}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>

                          {/* Right: Experience & Education */}
                          <div className="flex flex-col gap-4">
                            <div className="bg-slate-900/70 p-4 rounded-xl border border-slate-800">
                              <h4 className="font-semibold text-slate-200 mb-2">Experience History</h4>
                              <div className="space-y-3">
                                {(selectedResume.parsed_data.experience || []).map((exp, idx) => (
                                  <div key={idx} className="border-b border-slate-800 pb-2 last:border-0 last:pb-0">
                                    <div className="font-bold text-slate-200">{exp.job_title || 'Position'}</div>
                                    <div className="text-indigo-400">{exp.company || 'Company'} ({exp.start_date || '?'} - {exp.end_date || '?'})</div>
                                    {exp.description && <p className="text-slate-400 mt-1">{exp.description}</p>}
                                  </div>
                                ))}
                                {(!selectedResume.parsed_data.experience || selectedResume.parsed_data.experience.length === 0) && (
                                  <span className="text-slate-500">No experience records detected</span>
                                )}
                              </div>
                            </div>

                            <div className="bg-slate-900/70 p-4 rounded-xl border border-slate-800">
                              <h4 className="font-semibold text-slate-200 mb-2">Education</h4>
                              <div className="space-y-2">
                                {(selectedResume.parsed_data.education || []).map((edu, idx) => (
                                  <div key={idx} className="border-b border-slate-800 pb-2 last:border-0 last:pb-0">
                                    <div className="font-semibold text-slate-200">{edu.degree || 'Degree'} {edu.field_of_study ? `in ${edu.field_of_study}` : ''}</div>
                                    <div className="text-slate-400">{edu.institution || 'Institution'} ({edu.start_date || '?'} - {edu.end_date || '?'})</div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="text-xs text-slate-400">
                          {selectedResume.extracted_text ? (
                            <div>
                              <p className="font-semibold mb-1 text-slate-300">Raw PyMuPDF Extracted Text:</p>
                              <pre className="bg-slate-900 p-3 rounded-lg overflow-x-auto whitespace-pre-wrap max-h-48 text-slate-400">
                                {selectedResume.extracted_text}
                              </pre>
                            </div>
                          ) : (
                            <p className="text-slate-500 italic">No structured or raw text available for this file.</p>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
                ) : candidateSubTab === 'career-guidance' ? (
                  /* SUBTAB: CAREER GUIDANCE & RESUME INTELLIGENCE */
                  <div className="flex flex-col gap-6">
                    {/* Header Banner */}
                    <div className="bg-gradient-to-r from-indigo-950/60 via-slate-900/60 to-purple-950/40 border border-indigo-900/40 rounded-2xl p-6">
                      <div className="flex flex-wrap justify-between items-start gap-4">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xl">💡</span>
                            <h2 className="text-lg font-bold text-slate-100">Resume Intelligence & Career Guidance</h2>
                            <span className="text-[10px] bg-indigo-900/60 text-indigo-300 border border-indigo-700/50 px-2 py-0.5 rounded-full font-semibold">
                              ADVISORY ONLY
                            </span>
                          </div>
                          <p className="text-xs text-slate-400 max-w-2xl leading-relaxed">
                            Get evidence-grounded insights on how recruiters perceive your resume, what technical strengths you demonstrate,
                            and high-impact areas to improve. Purely advisory — never modifies your resume or affects M6 screening scores.
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Setup & Configuration Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                      {/* Left 2 Cols: Setup Request */}
                      <div className="lg:col-span-2 bg-slate-950/40 border border-slate-800 rounded-2xl p-6 flex flex-col gap-4">
                        <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                          <span>⚙️</span> Configure Analysis
                        </h3>

                        {/* Resume Selector */}
                        <div>
                          <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                            Select Resume Version to Analyze:
                          </label>
                          {resumes.length === 0 ? (
                            <p className="text-xs text-amber-400 italic">No resumes uploaded yet. Upload a PDF in the 'Profile & Resumes' tab first.</p>
                          ) : (
                            <select
                              value={selectedAnalysisResumeId}
                              onChange={(e) => {
                                setSelectedAnalysisResumeId(e.target.value);
                                fetchResumeAnalyses(e.target.value);
                              }}
                              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                            >
                              <option value="">-- Choose a Resume Version --</option>
                              {resumes.map((r) => (
                                <option key={r.id} value={r.id}>
                                  {r.original_filename} ({new Date(r.created_at).toLocaleDateString()}) {r.is_active ? '★ ACTIVE' : ''} [{r.parsing_status}]
                                </option>
                              ))}
                            </select>
                          )}
                        </div>

                        {/* Target Role Input with quick chips */}
                        <div>
                          <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                            Target Role (Optional):
                          </label>
                          <input
                            type="text"
                            value={targetRoleInput}
                            onChange={(e) => setTargetRoleInput(e.target.value)}
                            placeholder="e.g. Backend Developer, Data Scientist, Full Stack Engineer..."
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                          />
                          <div className="flex flex-wrap gap-1.5 mt-2">
                            <span className="text-[10px] text-slate-500 mr-1 self-center">Quick Suggestions:</span>
                            {['Backend Developer', 'Frontend Developer', 'Full Stack Developer', 'Data Scientist', 'DevOps Engineer'].map((role) => (
                              <button
                                key={role}
                                type="button"
                                onClick={() => setTargetRoleInput(role)}
                                className={`text-[10px] px-2 py-0.5 rounded-md border transition ${
                                  targetRoleInput === role
                                    ? 'bg-indigo-900 text-indigo-200 border-indigo-600 font-semibold'
                                    : 'bg-slate-900 text-slate-400 border-slate-700 hover:text-slate-200'
                                }`}
                              >
                                + {role}
                              </button>
                            ))}
                            {targetRoleInput && (
                              <button
                                type="button"
                                onClick={() => setTargetRoleInput('')}
                                className="text-[10px] text-slate-400 hover:text-slate-200 underline ml-1"
                              >
                                Clear
                              </button>
                            )}
                          </div>
                        </div>

                        {/* Error Alert */}
                        {analysisError && (
                          <div className="p-3 bg-red-950/60 border border-red-800 rounded-lg text-xs text-red-300">
                            {analysisError}
                          </div>
                        )}

                        {/* Action Button */}
                        <div className="pt-2">
                          <button
                            onClick={handleStartAnalysis}
                            disabled={!selectedAnalysisResumeId || analysisInProgress}
                            className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold transition flex items-center justify-center gap-2 ${
                              !selectedAnalysisResumeId || analysisInProgress
                                ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                                : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30'
                            }`}
                          >
                            {analysisInProgress ? (
                              <>
                                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                <span>Evaluating Resume & Running AI Guidance...</span>
                              </>
                            ) : (
                              <>
                                <span>🚀 Run Career Guidance Analysis</span>
                              </>
                            )}
                          </button>
                        </div>
                      </div>

                      {/* Right 1 Col: Analysis History */}
                      <div className="bg-slate-950/40 border border-slate-800 rounded-2xl p-6 flex flex-col gap-3">
                        <div className="flex justify-between items-center mb-1">
                          <h3 className="text-sm font-bold text-slate-200">
                            Analysis History ({analysesList.length})
                          </h3>
                          {selectedAnalysisResumeId && (
                            <button
                              onClick={() => fetchResumeAnalyses(selectedAnalysisResumeId)}
                              className="text-[10px] text-indigo-400 hover:underline"
                            >
                              Refresh
                            </button>
                          )}
                        </div>

                        {analysesLoading ? (
                          <p className="text-xs text-slate-500 animate-pulse">Loading history...</p>
                        ) : !selectedAnalysisResumeId ? (
                          <p className="text-xs text-slate-500 italic">Select a resume version to see historical analyses.</p>
                        ) : analysesList.length === 0 ? (
                          <div className="text-center py-6 border border-dashed border-slate-800 rounded-xl text-slate-500 text-xs">
                            No analyses yet for this version. Run your first analysis!
                          </div>
                        ) : (
                          <div className="flex flex-col gap-2 max-h-64 overflow-y-auto pr-1">
                            {analysesList.map((a) => (
                              <button
                                key={a.id}
                                onClick={() => fetchAnalysisDetail(a.id)}
                                className={`text-left p-2.5 rounded-lg border transition flex flex-col gap-1 ${
                                  currentAnalysis?.id === a.id
                                    ? 'bg-indigo-950/50 border-indigo-600'
                                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                                }`}
                              >
                                <div className="flex justify-between items-center text-[10px]">
                                  <span className="font-semibold text-slate-300">
                                    {a.target_role || 'General Review'}
                                  </span>
                                  <span
                                    className={`px-1.5 py-0.5 rounded font-bold uppercase text-[9px] ${
                                      a.status === 'COMPLETED'
                                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                                        : a.status === 'PROCESSING'
                                        ? 'bg-amber-950 text-amber-400 border border-amber-800'
                                        : 'bg-rose-950 text-rose-400 border border-rose-800'
                                    }`}
                                  >
                                    {a.status}
                                  </span>
                                </div>
                                <span className="text-[10px] text-slate-500">
                                  {new Date(a.created_at).toLocaleString()}
                                </span>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Report View */}
                    {currentAnalysis && (
                      <div className="flex flex-col gap-6">
                        {/* Report Header Card */}
                        <div className="bg-slate-950/60 border border-indigo-900/50 rounded-2xl p-6 shadow-xl flex flex-col gap-4">
                          <div className="flex flex-wrap justify-between items-start gap-4 border-b border-slate-800 pb-4">
                            <div>
                              <div className="flex items-center gap-2">
                                <h3 className="text-base font-bold text-slate-100">
                                  Report for: {currentAnalysis.target_role ? `Role Target — ${currentAnalysis.target_role}` : 'General Technical Evaluation'}
                                </h3>
                                <span
                                  className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                                    currentAnalysis.status === 'COMPLETED'
                                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                                      : currentAnalysis.status === 'PROCESSING'
                                      ? 'bg-amber-950 text-amber-400 border border-amber-800'
                                      : 'bg-rose-950 text-rose-400 border border-rose-800'
                                  }`}
                                >
                                  {currentAnalysis.status}
                                </span>
                              </div>
                              <p className="text-xs text-slate-400 mt-1">
                                Generated on {new Date(currentAnalysis.created_at).toLocaleString()} • Model: {currentAnalysis.model_name || 'qwen3:4b'}
                              </p>
                            </div>

                            {currentAnalysis.status === 'FAILED' && (
                              <button
                                onClick={() => handleRetryAnalysis(currentAnalysis.id)}
                                disabled={retryingAnalysisId === currentAnalysis.id}
                                className="px-3.5 py-1.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold rounded-lg transition flex items-center gap-2"
                              >
                                {retryingAnalysisId === currentAnalysis.id ? (
                                  <>
                                    <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                    <span>Retrying...</span>
                                  </>
                                ) : (
                                  <>
                                    <span>🔄 Retry Analysis</span>
                                  </>
                                )}
                              </button>
                            )}
                          </div>

                          {currentAnalysis.status === 'FAILED' && (
                            <div className="p-3 bg-amber-950/40 border border-amber-800 rounded-xl text-xs text-amber-300">
                              <p className="font-semibold mb-0.5">Notice: AI inference encountered an issue.</p>
                              <p>{currentAnalysis.error_message || 'A deterministic advisory fallback report has been supplied below.'}</p>
                            </div>
                          )}

                          {/* Advisory Overall Summary */}
                          {currentAnalysis.analysis_data?.overall_summary && (
                            <div className="bg-indigo-950/20 border border-indigo-900/40 rounded-xl p-4">
                              <h4 className="text-xs font-bold text-indigo-300 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                                <span>📋</span> Overall Advisory Summary
                              </h4>
                              <p className="text-xs text-slate-300 leading-relaxed">
                                {currentAnalysis.analysis_data.overall_summary}
                              </p>
                            </div>
                          )}

                          {/* Target Role Alignment (if provided) */}
                          {currentAnalysis.analysis_data?.target_role_alignment && (
                            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                              <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                                <span>🎯</span> Target Role Alignment: {currentAnalysis.analysis_data.target_role_alignment.target_role || currentAnalysis.target_role}
                              </h4>
                              <p className="text-xs text-slate-300 mb-3 leading-relaxed">
                                {currentAnalysis.analysis_data.target_role_alignment.alignment_summary}
                              </p>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {currentAnalysis.analysis_data.target_role_alignment.relevant_strengths.length > 0 && (
                                  <div className="bg-emerald-950/20 border border-emerald-900/30 rounded-lg p-3">
                                    <span className="text-[11px] font-bold text-emerald-400 block mb-1">Evidenced Strengths for Role:</span>
                                    <ul className="text-xs text-slate-300 space-y-1">
                                      {currentAnalysis.analysis_data.target_role_alignment.relevant_strengths.map((str, idx) => (
                                        <li key={idx} className="flex items-start gap-1.5">
                                          <span className="text-emerald-400">✓</span>
                                          <span>{str}</span>
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                                {currentAnalysis.analysis_data.target_role_alignment.missing_relevant_evidence.length > 0 && (
                                  <div className="bg-amber-950/20 border border-amber-900/30 rounded-lg p-3">
                                    <span className="text-[11px] font-bold text-amber-400 block mb-1">Common Role Skills Not Evident:</span>
                                    <ul className="text-xs text-slate-300 space-y-1">
                                      {currentAnalysis.analysis_data.target_role_alignment.missing_relevant_evidence.map((gap, idx) => (
                                        <li key={idx} className="flex items-start gap-1.5">
                                          <span className="text-amber-400">!</span>
                                          <span>{gap}</span>
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>

                        {/* PART 1: DETERMINISTIC CHECKS (RULE-BASED, NON-LLM) */}
                        {currentAnalysis.deterministic_checks && (
                          <div className="bg-slate-950/60 border border-teal-900/40 rounded-2xl p-6 shadow-xl flex flex-col gap-5">
                            <div className="flex flex-wrap justify-between items-center gap-2 border-b border-slate-800 pb-3">
                              <div>
                                <h3 className="text-sm font-bold text-teal-300 flex items-center gap-2">
                                  <span>⚙️</span> Deterministic Text Quality Checks (Rule-Based, Non-LLM)
                                </h3>
                                <p className="text-[11px] text-slate-400 mt-0.5">
                                  Algorithmic text analysis verifying structure, presence of metrics, and completeness.
                                </p>
                              </div>
                              <span className="text-[10px] bg-teal-950 text-teal-300 border border-teal-800 px-2 py-0.5 rounded font-mono font-semibold">
                                STATIC VERIFICATION
                              </span>
                            </div>

                            {/* Stat Badges */}
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                              <div className="bg-slate-900/70 border border-slate-800 p-3 rounded-xl">
                                <span className="text-[10px] text-slate-400 uppercase font-semibold block">Word Count</span>
                                <span className="text-lg font-bold text-slate-200">{currentAnalysis.deterministic_checks.word_count}</span>
                                <span className="text-[10px] text-slate-500 block">words detected</span>
                              </div>
                              <div className="bg-slate-900/70 border border-slate-800 p-3 rounded-xl">
                                <span className="text-[10px] text-slate-400 uppercase font-semibold block">Measurable Metrics</span>
                                <span className={`text-lg font-bold ${currentAnalysis.deterministic_checks.measurable_outcomes?.has_metrics ? 'text-emerald-400' : 'text-amber-400'}`}>
                                  {currentAnalysis.deterministic_checks.measurable_outcomes?.metrics_count || 0}
                                </span>
                                <span className="text-[10px] text-slate-500 block">quantitative points</span>
                              </div>
                              <div className="bg-slate-900/70 border border-slate-800 p-3 rounded-xl">
                                <span className="text-[10px] text-slate-400 uppercase font-semibold block">Detected Sections</span>
                                <span className="text-lg font-bold text-indigo-300">
                                  {currentAnalysis.deterministic_checks.sections_detected?.length || 0}
                                </span>
                                <span className="text-[10px] text-slate-500 block">standard sections</span>
                              </div>
                              <div className="bg-slate-900/70 border border-slate-800 p-3 rounded-xl">
                                <span className="text-[10px] text-slate-400 uppercase font-semibold block">Contact Presence</span>
                                <div className="flex gap-2 mt-1">
                                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${currentAnalysis.deterministic_checks.contact_info?.has_email ? 'bg-emerald-950 text-emerald-400' : 'bg-red-950 text-red-400'}`}>
                                    Email: {currentAnalysis.deterministic_checks.contact_info?.has_email ? '✓' : '✗'}
                                  </span>
                                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${currentAnalysis.deterministic_checks.contact_info?.has_phone ? 'bg-emerald-950 text-emerald-400' : 'bg-slate-800 text-slate-500'}`}>
                                    Phone: {currentAnalysis.deterministic_checks.contact_info?.has_phone ? '✓' : '✗'}
                                  </span>
                                </div>
                              </div>
                            </div>

                            {/* Section breakdown pills */}
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="text-xs text-slate-400 font-semibold">Standard Sections:</span>
                              {currentAnalysis.deterministic_checks.sections_detected?.map((s) => (
                                <span key={s} className="px-2 py-0.5 rounded bg-emerald-950/40 text-emerald-300 border border-emerald-800/40 text-[11px] font-medium">
                                  ✓ {s}
                                </span>
                              ))}
                              {currentAnalysis.deterministic_checks.missing_sections?.map((s) => (
                                <span key={s} className="px-2 py-0.5 rounded bg-amber-950/40 text-amber-300 border border-amber-800/40 text-[11px] font-medium">
                                  ⚠ Missing: {s}
                                </span>
                              ))}
                            </div>

                            {/* Findings List */}
                            {currentAnalysis.deterministic_checks.findings?.length > 0 && (
                              <div className="flex flex-col gap-2">
                                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">Quality Findings & Actionable Advice:</span>
                                {currentAnalysis.deterministic_checks.findings.map((f, idx) => (
                                  <div
                                    key={idx}
                                    className={`p-3 rounded-xl border text-xs flex items-start gap-3 ${
                                      f.level === 'WARNING'
                                        ? 'bg-rose-950/30 border-rose-900/50 text-rose-200'
                                        : f.level === 'ADVISORY'
                                        ? 'bg-amber-950/30 border-amber-900/50 text-amber-200'
                                        : 'bg-teal-950/30 border-teal-900/50 text-teal-200'
                                    }`}
                                  >
                                    <span className="font-bold font-mono uppercase text-[10px] px-1.5 py-0.5 rounded bg-slate-900/80">
                                      {f.level}
                                    </span>
                                    <span className="flex-1 leading-relaxed">{f.message}</span>
                                  </div>
                                ))}
                              </div>
                            )}

                            {/* Layout Notice */}
                            <div className="text-[11px] text-slate-500 italic border-t border-slate-900 pt-3">
                              {currentAnalysis.deterministic_checks.layout_notice ||
                                'Deterministic checks inspect extracted text and data only. Visual styling, margins, fonts, and page layouts cannot be evaluated from plain text.'}
                            </div>
                          </div>
                        )}

                        {/* PART 2: AI QUALITATIVE CAREER GUIDANCE */}
                        {currentAnalysis.analysis_data && (
                          <div className="flex flex-col gap-6">
                            {/* Key Strengths & Skills */}
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                              {/* Key Strengths */}
                              <div className="bg-slate-950/50 border border-slate-800 rounded-2xl p-5 flex flex-col gap-3">
                                <h4 className="text-sm font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                                  <span>💪</span> Key Demonstrated Strengths
                                </h4>
                                {currentAnalysis.analysis_data.strengths.length === 0 ? (
                                  <p className="text-xs text-slate-500 italic">No specific strengths isolated.</p>
                                ) : (
                                  <div className="flex flex-col gap-3">
                                    {currentAnalysis.analysis_data.strengths.map((str, idx) => (
                                      <div key={idx} className="bg-slate-900/70 border border-slate-800 rounded-xl p-3">
                                        <h5 className="font-semibold text-xs text-slate-200 mb-1">{str.title}</h5>
                                        <p className="text-xs text-slate-400 mb-2 leading-relaxed">{str.description}</p>
                                        {str.supporting_evidence?.length > 0 && (
                                          <div className="flex flex-wrap gap-1">
                                            {str.supporting_evidence.map((ev, eIdx) => (
                                              <span key={eIdx} className="text-[10px] bg-indigo-950/50 text-indigo-300 border border-indigo-800/40 px-2 py-0.5 rounded font-mono">
                                                "{ev}"
                                              </span>
                                            ))}
                                          </div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>

                              {/* Skills Breakdown */}
                              <div className="bg-slate-950/50 border border-slate-800 rounded-2xl p-5 flex flex-col gap-4">
                                <h4 className="text-sm font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                                  <span>⚡</span> Contextual Skills Analysis
                                </h4>
                                <div>
                                  <span className="text-[11px] font-bold text-emerald-400 block mb-1.5">
                                    Evidenced & Demonstrated in Context:
                                  </span>
                                  {currentAnalysis.analysis_data.skills_analysis.demonstrated_skills.length === 0 ? (
                                    <p className="text-xs text-slate-500 italic">No skills contextually evidenced in projects.</p>
                                  ) : (
                                    <div className="flex flex-wrap gap-1.5">
                                      {currentAnalysis.analysis_data.skills_analysis.demonstrated_skills.map((s) => (
                                        <span key={s} className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-xs font-semibold">
                                          {s}
                                        </span>
                                      ))}
                                    </div>
                                  )}
                                </div>
                                <div className="border-t border-slate-900 pt-3">
                                  <span className="text-[11px] font-bold text-amber-400 block mb-1.5">
                                    Isolated Keywords (Limited Evidentiary Context):
                                  </span>
                                  {currentAnalysis.analysis_data.skills_analysis.skills_with_limited_evidence.length === 0 ? (
                                    <p className="text-xs text-slate-500 italic">None. All listed skills have contextual mentions.</p>
                                  ) : (
                                    <div className="flex flex-wrap gap-1.5">
                                      {currentAnalysis.analysis_data.skills_analysis.skills_with_limited_evidence.map((s) => (
                                        <span key={s} className="px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 text-xs">
                                          {s}
                                        </span>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>

                            {/* Project Analysis */}
                            {currentAnalysis.analysis_data.project_analysis.length > 0 && (
                              <div className="bg-slate-950/50 border border-slate-800 rounded-2xl p-5 flex flex-col gap-3">
                                <h4 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                                  <span>🚀</span> Project Technical Evaluation
                                </h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                  {currentAnalysis.analysis_data.project_analysis.map((p, idx) => (
                                    <div key={idx} className="bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex flex-col justify-between gap-3">
                                      <div>
                                        <h5 className="font-bold text-sm text-indigo-300">{p.project_name}</h5>
                                        <div className="mt-2 text-xs space-y-2">
                                          <div>
                                            <span className="font-semibold text-slate-300">What is Demonstrated: </span>
                                            <span className="text-slate-400">{p.what_is_demonstrated}</span>
                                          </div>
                                          <div>
                                            <span className="font-semibold text-amber-400">What is Missing: </span>
                                            <span className="text-slate-400">{p.what_is_missing}</span>
                                          </div>
                                        </div>
                                      </div>
                                      <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 text-xs">
                                        <span className="text-teal-400 font-semibold block mb-0.5">Actionable Suggestion:</span>
                                        <span className="text-slate-300">{p.suggested_improvement}</span>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Experience Analysis */}
                            {currentAnalysis.analysis_data.experience_analysis.length > 0 && (
                              <div className="bg-slate-950/50 border border-slate-800 rounded-2xl p-5 flex flex-col gap-3">
                                <h4 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                                  <span>💼</span> Experience & Role Impact Analysis
                                </h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                  {currentAnalysis.analysis_data.experience_analysis.map((exp, idx) => (
                                    <div key={idx} className="bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex flex-col justify-between gap-3">
                                      <div>
                                        <h5 className="font-bold text-sm text-slate-200">{exp.role_or_experience}</h5>
                                        <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                                          <strong className="text-slate-300">Demonstrated Contributions: </strong>
                                          {exp.demonstrated_contributions}
                                        </p>
                                      </div>
                                      <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 text-xs">
                                        <span className="text-indigo-400 font-semibold block mb-0.5">Communication Improvement:</span>
                                        <span className="text-slate-300">{exp.improvement_suggestions}</span>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Prioritized Improvement Checklist */}
                            {currentAnalysis.analysis_data.improvement_priorities.length > 0 && (
                              <div className="bg-slate-950/50 border border-slate-800 rounded-2xl p-5 flex flex-col gap-3">
                                <h4 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                                  <span>🎯</span> Prioritized Action Items
                                </h4>
                                <div className="flex flex-col gap-3">
                                  {currentAnalysis.analysis_data.improvement_priorities.map((item, idx) => (
                                    <div
                                      key={idx}
                                      className="bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4"
                                    >
                                      <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                          <span
                                            className={`text-[9px] px-2 py-0.5 rounded font-bold uppercase ${
                                              item.priority === 'HIGH'
                                                ? 'bg-rose-950 text-rose-300 border border-rose-800'
                                                : item.priority === 'MEDIUM'
                                                ? 'bg-amber-950 text-amber-300 border border-amber-800'
                                                : 'bg-blue-950 text-blue-300 border border-blue-800'
                                            }`}
                                          >
                                            {item.priority} PRIORITY
                                          </span>
                                          <span className="font-bold text-sm text-slate-200">{item.issue}</span>
                                        </div>
                                        <p className="text-xs text-slate-400 leading-relaxed">
                                          <strong className="text-slate-300">Why it matters: </strong>
                                          {item.why_it_matters}
                                        </p>
                                      </div>
                                      <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 md:max-w-md text-xs">
                                        <span className="text-teal-400 font-semibold block mb-0.5">Suggested Action:</span>
                                        <span className="text-slate-300">{item.suggested_action}</span>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Limitations & Uncertainties Banner */}
                            {currentAnalysis.analysis_data.limitations_and_uncertainties?.length > 0 && (
                              <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-4 text-xs text-slate-500 space-y-1">
                                <span className="font-bold uppercase text-[10px] text-slate-400 block mb-1">
                                  Advisory Limitations & Uncertainties:
                                </span>
                                {currentAnalysis.analysis_data.limitations_and_uncertainties.map((lim, idx) => (
                                  <p key={idx}>• {lim}</p>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ) : candidateSubTab === 'career-assistant' ? (
                  /* SUBTAB: CAREER ASSISTANT */
                  <div className="flex flex-col gap-6">
                    {/* Header Banner */}
                    <div className="bg-gradient-to-r from-indigo-950/60 via-slate-900/60 to-purple-950/40 border border-indigo-900/40 rounded-2xl p-6">
                      <div className="flex flex-wrap justify-between items-start gap-4">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xl">🤖</span>
                            <h2 className="text-lg font-bold text-slate-100">Candidate AI Career Assistant</h2>
                            <span className="text-[10px] bg-indigo-900/60 text-indigo-300 border border-indigo-700/50 px-2 py-0.5 rounded-full font-semibold">
                              CONFIDENTIAL
                            </span>
                            <span className="text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded-full font-semibold">
                              ZERO IMPACT ON RECRUITER SCORES
                            </span>
                          </div>
                          <p className="text-xs text-slate-400 max-w-3xl leading-relaxed">
                            Your private conversational career mentor. Explore target career paths, dissect skill gaps, design 30/60/90-day learning roadmaps, and practice technical interview questions grounded in your actual uploaded resume experience and verified achievements.
                          </p>
                        </div>
                        <button
                          onClick={() => {
                            if (!newConvResumeId && resumes.length > 0) {
                              const activeRes = resumes.find((r) => r.is_active) || resumes[0];
                              setNewConvResumeId(activeRes.id);
                            }
                            setIsNewConvModalOpen(true);
                          }}
                          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-600/20 transition flex items-center gap-2"
                        >
                          <span>💬</span>
                          <span>New Conversation</span>
                        </button>
                      </div>
                    </div>

                    {/* Main Chat Layout: 2 Columns */}
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[640px]">
                      {/* Left: Conversations Sidebar (4 cols) */}
                      <div className="lg:col-span-4 bg-slate-950/50 border border-slate-800 rounded-2xl p-4 flex flex-col gap-3">
                        <div className="flex justify-between items-center pb-3 border-b border-slate-800">
                          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                            <span>🗂️</span> Saved Conversations
                          </h3>
                          <span className="text-[10px] text-slate-500 font-mono">
                            {conversationsList.length} thread{conversationsList.length === 1 ? '' : 's'}
                          </span>
                        </div>

                        {/* Conversation List */}
                        <div className="flex-1 overflow-y-auto space-y-2 pr-1 max-h-[560px]">
                          {conversationsLoading && conversationsList.length === 0 ? (
                            <div className="text-center py-8 text-indigo-400 animate-pulse text-xs">
                              Loading conversations...
                            </div>
                          ) : conversationsList.length === 0 ? (
                            <div className="text-center py-12 px-4 border border-dashed border-slate-800 rounded-xl text-slate-500 text-xs">
                              <span className="text-2xl block mb-2">💬</span>
                              <p className="font-semibold text-slate-400">No conversations yet</p>
                              <p className="text-[11px] text-slate-600 mt-1">Start your first career advisory or interview prep thread.</p>
                              <button
                                onClick={() => setIsNewConvModalOpen(true)}
                                className="mt-3 px-3 py-1.5 bg-indigo-600/80 hover:bg-indigo-600 text-white text-xs font-semibold rounded-lg transition"
                              >
                                + Start Chat
                              </button>
                            </div>
                          ) : (
                            conversationsList.map((conv) => {
                              const isSelected = activeConversation?.id === conv.id;
                              return (
                                <div
                                  key={conv.id}
                                  onClick={() => fetchConversationDetail(conv.id)}
                                  className={`p-3 rounded-xl border cursor-pointer transition flex flex-col gap-1.5 group ${
                                    isSelected
                                      ? 'bg-indigo-950/40 border-indigo-700 shadow-md'
                                      : 'bg-slate-900/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900'
                                  }`}
                                >
                                  <div className="flex justify-between items-start gap-2">
                                    <h4 className="text-xs font-semibold text-slate-200 line-clamp-1 group-hover:text-indigo-300 transition">
                                      {conv.conversation_title}
                                    </h4>
                                    <button
                                      title="Delete conversation"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleDeleteConversation(conv.id, conv.conversation_title);
                                      }}
                                      className="text-slate-600 hover:text-rose-400 text-xs p-0.5 rounded transition opacity-0 group-hover:opacity-100"
                                    >
                                      🗑️
                                    </button>
                                  </div>

                                  <div className="flex flex-wrap items-center gap-1.5">
                                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800/60 font-medium">
                                      {conv.conversation_type.replace('_', ' ')}
                                    </span>
                                    {conv.target_role && (
                                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-medium line-clamp-1">
                                        🎯 {conv.target_role}
                                      </span>
                                    )}
                                    {conv.resume_id && (
                                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800/40">
                                        📄 Resume Pinned
                                      </span>
                                    )}
                                  </div>

                                  <div className="flex justify-between items-center text-[10px] text-slate-500 pt-1">
                                    <span>{conv.message_count} message{conv.message_count === 1 ? '' : 's'}</span>
                                    <span>{new Date(conv.updated_at).toLocaleDateString()}</span>
                                  </div>
                                </div>
                              );
                            })
                          )}
                        </div>
                      </div>

                      {/* Right: Active Chat Pane (8 cols) */}
                      <div className="lg:col-span-8 bg-slate-950/50 border border-slate-800 rounded-2xl flex flex-col overflow-hidden">
                        {activeConvLoading ? (
                          <div className="flex-1 flex items-center justify-center text-indigo-400 animate-pulse text-xs py-24">
                            Loading conversation messages...
                          </div>
                        ) : !activeConversation ? (
                          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
                            <div className="w-16 h-16 rounded-2xl bg-indigo-950/60 border border-indigo-800/50 flex items-center justify-center text-3xl mb-4">
                              🤖
                            </div>
                            <h3 className="text-base font-bold text-slate-200 mb-1">TalentLens Career Assistant</h3>
                            <p className="text-xs text-slate-400 max-w-md mb-6 leading-relaxed">
                              Select an existing conversation from the left sidebar or start a new focused chat to explore career paths, analyze skill gaps, and prepare for interviews.
                            </p>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full text-left">
                              <button
                                onClick={() => {
                                  setNewConvPurpose('CAREER_GUIDANCE');
                                  setNewConvTitle('General Career Guidance & Strengths');
                                  setIsNewConvModalOpen(true);
                                }}
                                className="p-3 bg-slate-900/80 hover:bg-slate-900 border border-slate-800 hover:border-indigo-600 rounded-xl transition flex flex-col gap-1 text-left"
                              >
                                <span className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                                  <span>🌟</span> Career Guidance
                                </span>
                                <span className="text-[11px] text-slate-500">
                                  Review your resume strengths and demonstrated skills.
                                </span>
                              </button>
                              <button
                                onClick={() => {
                                  setNewConvPurpose('ROLE_TRANSITION');
                                  setNewConvTitle('Target Role Transition Plan');
                                  setIsNewConvModalOpen(true);
                                }}
                                className="p-3 bg-slate-900/80 hover:bg-slate-900 border border-slate-800 hover:border-indigo-600 rounded-xl transition flex flex-col gap-1 text-left"
                              >
                                <span className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                                  <span>🎯</span> Role Transition
                                </span>
                                <span className="text-[11px] text-slate-500">
                                  Identify skill gaps and bridge into your desired role.
                                </span>
                              </button>
                              <button
                                onClick={() => {
                                  setNewConvPurpose('INTERVIEW_PREP');
                                  setNewConvTitle('Technical Interview Preparation');
                                  setIsNewConvModalOpen(true);
                                }}
                                className="p-3 bg-slate-900/80 hover:bg-slate-900 border border-slate-800 hover:border-indigo-600 rounded-xl transition flex flex-col gap-1 text-left"
                              >
                                <span className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                                  <span>💼</span> Interview Practice
                                </span>
                                <span className="text-[11px] text-slate-500">
                                  Generate realistic technical questions based on your projects.
                                </span>
                              </button>
                              <button
                                onClick={() => {
                                  setNewConvPurpose('SKILL_DEVELOPMENT');
                                  setNewConvTitle('30/60/90-Day Learning Roadmap');
                                  setIsNewConvModalOpen(true);
                                }}
                                className="p-3 bg-slate-900/80 hover:bg-slate-900 border border-slate-800 hover:border-indigo-600 rounded-xl transition flex flex-col gap-1 text-left"
                              >
                                <span className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                                  <span>📈</span> Learning Roadmap
                                </span>
                                <span className="text-[11px] text-slate-500">
                                  Structured technical milestones to level up your career.
                                </span>
                              </button>
                            </div>
                          </div>
                        ) : (
                          <>
                            {/* Chat Header */}
                            <div className="p-4 bg-slate-900/70 border-b border-slate-800 flex flex-wrap justify-between items-center gap-3">
                              <div>
                                <div className="flex items-center gap-2">
                                  <h3 className="text-sm font-bold text-slate-100">{activeConversation.conversation_title}</h3>
                                  <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 font-semibold">
                                    {activeConversation.conversation_type.replace('_', ' ')}
                                  </span>
                                </div>
                                <div className="flex flex-wrap items-center gap-2 mt-1 text-[11px] text-slate-400">
                                  {activeConversation.target_role && (
                                    <span>🎯 Target: <strong className="text-slate-300">{activeConversation.target_role}</strong></span>
                                  )}
                                  {activeConversation.target_role && activeConversation.resume_id && <span>•</span>}
                                  {activeConversation.resume_id ? (
                                    <span className="text-purple-400 font-medium flex items-center gap-1">
                                      📄 Resume Grounded
                                    </span>
                                  ) : (
                                    <span className="text-slate-500 italic">No resume pinned</span>
                                  )}
                                </div>
                              </div>
                            </div>

                            {/* Chat Messages Body */}
                            <div className="flex-1 p-4 overflow-y-auto space-y-4 max-h-[500px] min-h-[380px]">
                              {activeConversation.messages.length === 0 ? (
                                <div className="text-center py-12 text-slate-500 text-xs">
                                  No messages yet. Send a message below to start your conversation!
                                </div>
                              ) : (
                                activeConversation.messages.map((msg) => {
                                  const isUser = msg.role === 'USER';
                                  const isFallback = msg.context_metadata?.is_fallback;
                                  const snippets = msg.context_metadata?.evidence_snippets || [];
                                  return (
                                    <div
                                      key={msg.id}
                                      className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} gap-1.5`}
                                    >
                                      <div className="flex items-center gap-2 text-[10px] text-slate-500">
                                        <span>{isUser ? 'You' : 'Career Assistant'}</span>
                                        <span>•</span>
                                        <span>{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                        {isFallback && (
                                          <span className="text-amber-400 font-medium">⚡ Advisory Fallback</span>
                                        )}
                                      </div>

                                      <div
                                        className={`max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed ${
                                          isUser
                                            ? 'bg-indigo-600 text-white rounded-br-sm'
                                            : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-bl-sm shadow-md'
                                        }`}
                                      >
                                        <div className="whitespace-pre-wrap">{msg.content}</div>

                                        {/* Evidence Grounding Box */}
                                        {!isUser && snippets.length > 0 && (
                                          <div className="mt-3 pt-3 border-t border-slate-800/80">
                                            <details className="cursor-pointer group">
                                              <summary className="text-[10px] text-indigo-400 hover:text-indigo-300 font-semibold list-none flex items-center gap-1">
                                                <span>📌 Grounded in your resume ({snippets.length} references)</span>
                                                <span className="group-open:rotate-180 transition-transform">▾</span>
                                              </summary>
                                              <div className="mt-2 space-y-1.5 pl-2 border-l-2 border-indigo-900/60 text-[10px] text-slate-400 font-mono">
                                                {snippets.map((snip, sIdx) => (
                                                  <div key={sIdx} className="bg-slate-950/60 p-1.5 rounded">
                                                    {snip}
                                                  </div>
                                                ))}
                                              </div>
                                            </details>
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  );
                                })
                              )}

                              {/* Assistant Typing Indicator */}
                              {sendingMessage && (
                                <div className="flex items-center gap-3 text-xs text-indigo-400 bg-indigo-950/20 border border-indigo-900/30 rounded-xl p-3 max-w-xs animate-pulse">
                                  <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
                                  <span>Formulating career guidance...</span>
                                </div>
                              )}

                              {chatError && (
                                <div className="p-3 bg-rose-950/40 border border-rose-800 rounded-xl text-xs text-rose-300">
                                  <span className="font-semibold block mb-0.5">Error:</span>
                                  {chatError}
                                </div>
                              )}
                            </div>

                            {/* Prompt Suggestions Bar */}
                            <div className="px-4 py-2 bg-slate-900/40 border-t border-slate-800 flex items-center gap-2 overflow-x-auto text-[11px] whitespace-nowrap">
                              <span className="text-slate-500 font-semibold text-[10px] uppercase tracking-wider">
                                Suggestions:
                              </span>
                              <button
                                onClick={() => setMessageInput('What are my strongest demonstrated technical skills?')}
                                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                              >
                                💪 Strongest Skills
                              </button>
                              <button
                                onClick={() => setMessageInput('What skills am I missing for my target role, and how can I bridge them?')}
                                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                              >
                                🎯 Skill Gap Analysis
                              </button>
                              <button
                                onClick={() => setMessageInput('Generate 5 technical interview questions based on my projects and experience.')}
                                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                              >
                                💼 Interview Questions
                              </button>
                              <button
                                onClick={() => setMessageInput('Create a 30-day learning roadmap to advance to senior level.')}
                                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                              >
                                📅 30-Day Roadmap
                              </button>
                            </div>

                            {/* Message Input Form */}
                            <form onSubmit={handleSendMessage} className="p-4 bg-slate-900/80 border-t border-slate-800 flex gap-2">
                              <input
                                type="text"
                                value={messageInput}
                                onChange={(e) => setMessageInput(e.target.value)}
                                placeholder="Ask about career direction, interview questions, resume impact, or skill roadmaps..."
                                disabled={sendingMessage}
                                className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
                              />
                              <button
                                type="submit"
                                disabled={sendingMessage || !messageInput.trim()}
                                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-600/20 transition flex items-center gap-1.5"
                              >
                                {sendingMessage ? (
                                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                ) : (
                                  <>
                                    <span>Send</span>
                                    <span>➤</span>
                                  </>
                                )}
                              </button>
                            </form>
                          </>
                        )}
                      </div>
                    </div>

                    {/* New Conversation Modal */}
                    {isNewConvModalOpen && (
                      <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
                        <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 max-w-lg w-full shadow-2xl flex flex-col gap-4">
                          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                              <span>🤖</span> Start New Career Conversation
                            </h3>
                            <button
                              onClick={() => setIsNewConvModalOpen(false)}
                              className="text-slate-500 hover:text-slate-300 text-sm font-bold"
                            >
                              ✕
                            </button>
                          </div>

                          <div className="space-y-4 text-xs">
                            {/* Purpose */}
                            <div>
                              <label className="block text-slate-300 font-semibold mb-1">
                                Conversation Purpose:
                              </label>
                              <select
                                value={newConvPurpose}
                                onChange={(e) => setNewConvPurpose(e.target.value)}
                                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500"
                              >
                                <option value="CAREER_GUIDANCE">Career Guidance & Strengths</option>
                                <option value="ROLE_TRANSITION">Target Role Transition & Gaps</option>
                                <option value="SKILL_DEVELOPMENT">Skill Development & Learning Roadmap</option>
                                <option value="INTERVIEW_PREP">Technical Interview Preparation</option>
                                <option value="RESUME_FEEDBACK">Resume Feedback & Framing</option>
                                <option value="GENERAL">General Discussion</option>
                              </select>
                            </div>

                            {/* Resume Version */}
                            <div>
                              <label className="block text-slate-300 font-semibold mb-1">
                                Pinned Resume Version:
                              </label>
                              <select
                                value={newConvResumeId}
                                onChange={(e) => setNewConvResumeId(e.target.value)}
                                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500"
                              >
                                <option value="">None (General advice without resume grounding)</option>
                                {resumes.map((r) => (
                                  <option key={r.id} value={r.id}>
                                    {r.original_filename} ({new Date(r.created_at).toLocaleDateString()}) {r.is_active ? '★ ACTIVE' : ''}
                                  </option>
                                ))}
                              </select>
                              <p className="text-[11px] text-slate-500 mt-1">
                                Pinning a resume grounds the assistant in your actual experience, skills, and M7 qualitative insights.
                              </p>
                            </div>

                            {/* Target Role */}
                            <div>
                              <label className="block text-slate-300 font-semibold mb-1">
                                Target Role (Optional):
                              </label>
                              <input
                                type="text"
                                value={newConvTargetRole}
                                onChange={(e) => setNewConvTargetRole(e.target.value)}
                                placeholder="e.g. Senior Backend Engineer, Data Architect"
                                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500"
                              />
                            </div>

                            {/* Title */}
                            <div>
                              <label className="block text-slate-300 font-semibold mb-1">
                                Conversation Title (Optional):
                              </label>
                              <input
                                type="text"
                                value={newConvTitle}
                                onChange={(e) => setNewConvTitle(e.target.value)}
                                placeholder="e.g. Backend Transition Plan"
                                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500"
                              />
                            </div>

                            {/* Initial Question */}
                            <div>
                              <label className="block text-slate-300 font-semibold mb-1">
                                Initial Question (Optional):
                              </label>
                              <textarea
                                value={newConvInitialMsg}
                                onChange={(e) => setNewConvInitialMsg(e.target.value)}
                                placeholder="e.g. Based on my resume, what are my strongest skills and what should I focus on next?"
                                rows={3}
                                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500 resize-none"
                              />
                            </div>
                          </div>

                          <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                            <button
                              type="button"
                              onClick={() => setIsNewConvModalOpen(false)}
                              disabled={creatingConv}
                              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition"
                            >
                              Cancel
                            </button>
                            <button
                              type="button"
                              onClick={handleCreateConversation}
                              disabled={creatingConv}
                              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition flex items-center gap-2"
                            >
                              {creatingConv ? (
                                <>
                                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                  <span>Creating...</span>
                                </>
                              ) : (
                                <span>Start Conversation</span>
                              )}
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  /* SUBTAB: MY APPLICATIONS */
                  <div className="flex flex-col gap-6">
                    {/* Filters Bar */}
                    <div className="bg-slate-950/40 border border-slate-800 rounded-2xl p-4 flex flex-wrap gap-4 items-center justify-between">
                      <div className="flex flex-wrap gap-3 items-center flex-1">
                        <div className="relative min-w-[220px]">
                          <input
                            type="text"
                            value={myAppKeyword}
                            onChange={(e) => setMyAppKeyword(e.target.value)}
                            placeholder="Search by job title..."
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                          />
                        </div>
                        <select
                          value={myAppStatusFilter}
                          onChange={(e) => setMyAppStatusFilter(e.target.value)}
                          className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                        >
                          <option value="">All Statuses</option>
                          <option value="SUBMITTED">Submitted</option>
                          <option value="UNDER_REVIEW">Under Review</option>
                          <option value="SHORTLISTED">Shortlisted</option>
                          <option value="HIRED">Hired</option>
                          <option value="REJECTED">Rejected</option>
                          <option value="WITHDRAWN">Withdrawn</option>
                        </select>
                      </div>
                      <div className="text-xs text-slate-400">
                        Total Applications: <strong className="text-slate-200">{myApplications.length}</strong>
                      </div>
                    </div>

                    {/* Applications List */}
                    {myApplicationsLoading ? (
                      <div className="text-center py-12 text-indigo-400 animate-pulse text-xs">
                        Loading your applications...
                      </div>
                    ) : myApplications.length === 0 ? (
                      <div className="text-center py-12 text-slate-500 border border-dashed border-slate-800 rounded-2xl">
                        <p className="text-sm font-medium">No applications found.</p>
                        <p className="text-xs text-slate-600 mt-1">Browse published jobs and apply using your active resume.</p>
                        <button
                          onClick={() => setActiveTab('public-jobs')}
                          className="mt-3 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition"
                        >
                          Browse Available Jobs
                        </button>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {myApplications.map((app) => (
                          <div
                            key={app.id}
                            className="bg-slate-950/60 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition flex flex-col justify-between gap-4"
                          >
                            <div className="flex flex-col gap-2">
                              <div className="flex justify-between items-start gap-2">
                                <div>
                                  <h3 className="font-bold text-slate-100 text-base">{app.job_title}</h3>
                                  <p className="text-xs text-indigo-400 font-medium">{app.organization_name}</p>
                                </div>
                                <span
                                  className={`text-[10px] px-2.5 py-1 rounded-full font-bold uppercase tracking-wider ${
                                    app.status === 'SUBMITTED'
                                      ? 'bg-blue-950 text-blue-400 border border-blue-800'
                                      : app.status === 'UNDER_REVIEW'
                                      ? 'bg-amber-950 text-amber-400 border border-amber-800'
                                      : app.status === 'SHORTLISTED'
                                      ? 'bg-purple-950 text-purple-400 border border-purple-800'
                                      : app.status === 'HIRED'
                                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                                      : app.status === 'REJECTED'
                                      ? 'bg-rose-950 text-rose-400 border border-rose-800'
                                      : 'bg-slate-800 text-slate-400 border border-slate-700'
                                  }`}
                                >
                                  {app.status}
                                </span>
                              </div>

                              <div className="text-xs text-slate-400 space-y-1">
                                {app.job_location && <div>📍 Location: {app.job_location}</div>}
                                {app.workplace_type && <div>💼 {app.workplace_type} · {app.employment_type?.replace('_', ' ')}</div>}
                                <div className="p-2 bg-slate-900/80 rounded-lg border border-slate-800/80 text-[11px] text-slate-300">
                                  📄 Pinned Resume: <strong className="text-indigo-300">{app.resume_filename}</strong>
                                </div>
                              </div>
                            </div>

                            <div className="border-t border-slate-800/80 pt-3 flex justify-between items-center text-xs">
                              <span className="text-[11px] text-slate-500">
                                Applied: {new Date(app.submitted_at).toLocaleDateString()}
                              </span>
                              <div className="flex gap-2">
                                <button
                                  onClick={() => setSelectedCandidateApp(app)}
                                  className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition"
                                >
                                  Details
                                </button>
                                {['SUBMITTED', 'UNDER_REVIEW', 'SHORTLISTED'].includes(app.status) && (
                                  <button
                                    onClick={() => handleWithdrawApplication(app.id)}
                                    className="px-3 py-1 bg-rose-950/60 hover:bg-rose-900 text-rose-300 border border-rose-800/60 rounded-lg transition"
                                  >
                                    Withdraw
                                  </button>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: RECRUITER WORKSPACE */}
        {activeTab === 'recruiter' && (
          <div>
            {!token ? (
              /* Recruiter Authentication Request */
              <div className="max-w-md mx-auto bg-slate-950/80 border border-slate-800 rounded-2xl p-8 shadow-xl mt-8">
                <h2 className="text-2xl font-bold text-slate-100 mb-2">Recruiter Access</h2>
                <p className="text-sm text-slate-400 mb-6">
                  Sign in with your organization account to create, publish, and manage job listings.
                </p>

                {authError && (
                  <div className="mb-4 p-3 bg-red-950/50 border border-red-800 text-red-300 text-sm rounded-lg">
                    {authError}
                  </div>
                )}

                <form onSubmit={handleAuth} className="flex flex-col gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">Email Address</label>
                    <input
                      type="email"
                      required
                      value={authEmail}
                      onChange={(e) => setAuthEmail(e.target.value)}
                      placeholder="recruiter@acme.com"
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">Password</label>
                    <input
                      type="password"
                      required
                      value={authPassword}
                      onChange={(e) => setAuthPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full mt-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2.5 rounded-lg transition"
                  >
                    Sign In
                  </button>
                </form>
              </div>
            ) : (
              /* RECRUITER LOGGED IN VIEW */
              <div className="flex flex-col gap-6">
                {/* Organization Switcher & Context Bar */}
                <div className="bg-slate-950/60 border border-slate-800 rounded-2xl p-4 flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Organization:</span>
                    {userOrgs.length > 0 ? (
                      <select
                        value={selectedOrgId}
                        onChange={(e) => setSelectedOrgId(e.target.value)}
                        className="bg-slate-900 border border-slate-700 text-sm text-slate-100 rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500 font-medium"
                      >
                        {userOrgs.map((org) => (
                          <option key={org.id} value={org.id}>
                            {org.name} ({org.role || 'MEMBER'})
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span className="text-xs text-amber-400 bg-amber-950/40 border border-amber-800/40 px-2.5 py-1 rounded">
                        No Organization Membership
                      </span>
                    )}

                    {activeOrg && (
                      <span className="px-2.5 py-1 text-xs rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800 font-semibold">
                        Role: {activeOrg.role}
                      </span>
                    )}

                    <button
                      onClick={() => setIsOrgModalOpen(true)}
                      className="text-xs text-indigo-400 hover:text-indigo-300 font-medium ml-2"
                    >
                      + Create Organization
                    </button>
                  </div>

                  {/* Subtabs: Jobs vs Applications vs Matcher */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => setRecruiterSubTab('jobs')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                        recruiterSubTab === 'jobs'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      Job Management
                    </button>
                    <button
                      onClick={() => setRecruiterSubTab('applications')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                        recruiterSubTab === 'applications'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      Applications ({recruiterApplications.length})
                    </button>
                    <button
                      onClick={() => setRecruiterSubTab('screening')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 ${
                        recruiterSubTab === 'screening'
                          ? 'bg-purple-600 text-white'
                          : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      <span>⚡</span> AI Screening
                    </button>
                    <button
                      onClick={() => setRecruiterSubTab('matcher')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                        recruiterSubTab === 'matcher'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      AI Matcher Pipeline
                    </button>
                  </div>
                </div>

                {recruiterActionMessage && (
                  <div className="p-3 bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-xs rounded-xl font-medium animate-fadeIn">
                    ✓ {recruiterActionMessage}
                  </div>
                )}

                {/* SUBTAB 1: JOB MANAGEMENT */}
                {recruiterSubTab === 'jobs' && (
                  <div className="flex flex-col gap-6">
                    {/* Header with Post Job Button */}
                    <div className="flex flex-wrap justify-between items-center gap-4">
                      <div>
                        <h2 className="text-xl font-bold text-slate-100">
                          {activeOrg ? `Jobs at ${activeOrg.name}` : 'Organization Jobs'}
                        </h2>
                        <p className="text-xs text-slate-400">
                          Manage job lifecycle: DRAFT → PUBLISHED → CLOSED → ARCHIVED.
                        </p>
                      </div>

                      {isRecruiterOrAbove && (
                        <button
                          onClick={openCreateJobModal}
                          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-xl shadow-lg transition flex items-center gap-2"
                        >
                          <span>+</span> Post New Job
                        </button>
                      )}
                    </div>

                    {/* Recruiter Filters */}
                    <div className="flex flex-wrap items-center gap-3 bg-slate-950/40 p-3 rounded-xl border border-slate-800">
                      <input
                        type="text"
                        placeholder="Filter by keyword..."
                        value={recruiterJobKeywordFilter}
                        onChange={(e) => setRecruiterJobKeywordFilter(e.target.value)}
                        className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 min-w-[200px]"
                      />
                      <select
                        value={recruiterJobStatusFilter}
                        onChange={(e) => setRecruiterJobStatusFilter(e.target.value)}
                        className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                      >
                        <option value="">All Statuses</option>
                        <option value="DRAFT">Draft</option>
                        <option value="PUBLISHED">Published</option>
                        <option value="CLOSED">Closed</option>
                        <option value="ARCHIVED">Archived</option>
                      </select>
                      <button
                        onClick={fetchRecruiterJobs}
                        className="text-xs text-indigo-400 hover:text-indigo-300 ml-auto"
                      >
                        Refresh List
                      </button>
                    </div>

                    {/* Jobs List */}
                    {recruiterJobsLoading ? (
                      <div className="text-center py-12 text-indigo-400 animate-pulse text-xs">
                        Loading organization jobs...
                      </div>
                    ) : recruiterJobs.length === 0 ? (
                      <div className="text-center py-12 text-slate-500 border border-dashed border-slate-800 rounded-2xl">
                        <p className="text-sm font-medium">No jobs found for this organization.</p>
                        {isRecruiterOrAbove ? (
                          <button
                            onClick={openCreateJobModal}
                            className="mt-3 text-xs text-indigo-400 hover:underline font-semibold"
                          >
                            Create the first job posting
                          </button>
                        ) : (
                          <p className="text-xs text-slate-600 mt-1">Viewers cannot create job postings.</p>
                        )}
                      </div>
                    ) : (
                      <div className="flex flex-col gap-3">
                        {recruiterJobs.map((job) => (
                          <div
                            key={job.id}
                            className="bg-slate-950/60 border border-slate-800 hover:border-slate-700 rounded-xl p-5 transition flex flex-wrap justify-between items-center gap-4"
                          >
                            <div className="flex flex-col gap-1.5 max-w-xl">
                              <div className="flex items-center gap-2.5">
                                <h3 className="font-bold text-slate-100 text-base">{job.title}</h3>
                                {/* Status Badge */}
                                <span
                                  className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                                    job.status === 'DRAFT'
                                      ? 'bg-amber-950 text-amber-400 border border-amber-800'
                                      : job.status === 'PUBLISHED'
                                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                                      : job.status === 'CLOSED'
                                      ? 'bg-rose-950 text-rose-400 border border-rose-800'
                                      : 'bg-slate-800 text-slate-400 border border-slate-700'
                                  }`}
                                >
                                  {job.status}
                                </span>
                              </div>

                              <div className="text-xs text-slate-400 flex flex-wrap gap-x-4 gap-y-1">
                                {job.department && <span>Department: <strong>{job.department}</strong></span>}
                                {job.location && <span>Location: <strong>{job.location}</strong></span>}
                                <span>Type: <strong>{job.workplace_type} · {job.employment_type.replace('_', ' ')}</strong></span>
                                {(job.salary_min !== null || job.salary_max !== null) && (
                                  <span className="text-emerald-400 font-mono">
                                    Salary: {job.salary_min?.toLocaleString()} - {job.salary_max?.toLocaleString()} {job.salary_currency}
                                  </span>
                                )}
                              </div>

                              <div className="flex flex-wrap gap-1 mt-1">
                                {job.required_skills.map((s, idx) => (
                                  <span
                                    key={idx}
                                    className="px-1.5 py-0.2 text-[10px] bg-slate-900 text-slate-300 border border-slate-700 rounded"
                                  >
                                    {s}
                                  </span>
                                ))}
                              </div>
                            </div>

                            {/* Lifecycle Action Buttons */}
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => {
                                  setRecruiterAppJobFilter(job.id);
                                  setRecruiterSubTab('applications');
                                }}
                                className="px-3 py-1.5 text-xs bg-indigo-950/80 hover:bg-indigo-900 text-indigo-300 rounded-lg border border-indigo-800 transition"
                              >
                                Applicants
                              </button>

                              <button
                                onClick={() => openScreeningForJob(job)}
                                className="px-3 py-1.5 text-xs bg-purple-950/80 hover:bg-purple-900 text-purple-300 rounded-lg border border-purple-800 transition flex items-center gap-1"
                              >
                                <span>⚡</span> Screen
                              </button>

                              {isRecruiterOrAbove && job.status !== 'ARCHIVED' && (
                                <button
                                  onClick={() => openEditJobModal(job)}
                                  className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-700 transition"
                                >
                                  Edit
                                </button>
                              )}

                              {isRecruiterOrAbove && job.status === 'DRAFT' && (
                                <button
                                  onClick={() => handleJobLifecycleAction(job.id, 'publish')}
                                  className="px-3 py-1.5 text-xs bg-emerald-700 hover:bg-emerald-600 text-white font-medium rounded-lg shadow transition"
                                >
                                  Publish
                                </button>
                              )}

                              {isRecruiterOrAbove && job.status === 'PUBLISHED' && (
                                <>
                                  <button
                                    onClick={() => handleJobLifecycleAction(job.id, 'close')}
                                    className="px-3 py-1.5 text-xs bg-amber-800 hover:bg-amber-700 text-white font-medium rounded-lg transition"
                                  >
                                    Close
                                  </button>
                                  <button
                                    onClick={() => handleJobLifecycleAction(job.id, 'archive')}
                                    className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition"
                                  >
                                    Archive
                                  </button>
                                </>
                              )}

                              {isRecruiterOrAbove && job.status === 'CLOSED' && (
                                <button
                                  onClick={() => handleJobLifecycleAction(job.id, 'archive')}
                                  className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition"
                                >
                                  Archive
                                </button>
                              )}

                              {job.status === 'ARCHIVED' && (
                                <span className="text-xs text-slate-500 italic">Archived (Read Only)</span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* SUBTAB 2: APPLICATIONS MANAGEMENT */}
                {recruiterSubTab === 'applications' && (
                  <div className="flex flex-col gap-6">
                    {/* Header and Filters Bar */}
                    <div className="bg-slate-950/40 border border-slate-800 rounded-2xl p-4 flex flex-wrap gap-4 items-center justify-between">
                      <div className="flex flex-wrap gap-3 items-center flex-1">
                        <div className="relative min-w-[200px]">
                          <input
                            type="text"
                            value={recruiterAppKeyword}
                            onChange={(e) => setRecruiterAppKeyword(e.target.value)}
                            placeholder="Search name, email, headline..."
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                          />
                        </div>

                        {/* Filter by Job */}
                        <select
                          value={recruiterAppJobFilter}
                          onChange={(e) => setRecruiterAppJobFilter(e.target.value)}
                          className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                        >
                          <option value="">All Jobs</option>
                          {recruiterJobs.map((j) => (
                            <option key={j.id} value={j.id}>
                              {j.title} ({j.status})
                            </option>
                          ))}
                        </select>

                        {/* Filter by Status */}
                        <select
                          value={recruiterAppStatusFilter}
                          onChange={(e) => setRecruiterAppStatusFilter(e.target.value)}
                          className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                        >
                          <option value="">All Statuses</option>
                          <option value="SUBMITTED">Submitted</option>
                          <option value="UNDER_REVIEW">Under Review</option>
                          <option value="SHORTLISTED">Shortlisted</option>
                          <option value="HIRED">Hired</option>
                          <option value="REJECTED">Rejected</option>
                          <option value="WITHDRAWN">Withdrawn</option>
                        </select>
                      </div>

                      <div className="text-xs text-slate-400">
                        Total Applicants: <strong className="text-slate-200">{recruiterApplications.length}</strong>
                      </div>
                    </div>

                    {/* Applications List */}
                    {recruiterAppsLoading ? (
                      <div className="text-center py-12 text-indigo-400 animate-pulse text-xs">
                        Loading applicant applications...
                      </div>
                    ) : recruiterApplications.length === 0 ? (
                      <div className="text-center py-12 text-slate-500 border border-dashed border-slate-800 rounded-2xl">
                        <p className="text-sm font-medium">No applications found.</p>
                        <p className="text-xs text-slate-600 mt-1">Applications submitted to your published jobs will appear here.</p>
                      </div>
                    ) : (
                      <div className="flex flex-col gap-3">
                        {recruiterApplications.map((app) => (
                          <div
                            key={app.id}
                            className="bg-slate-950/60 border border-slate-800 hover:border-slate-700 rounded-xl p-5 transition flex flex-wrap justify-between items-center gap-4"
                          >
                            <div className="flex flex-col gap-1 max-w-xl">
                              <div className="flex items-center gap-2.5">
                                <h3 className="font-bold text-slate-100 text-base">
                                  {app.candidate_name || 'Anonymous Candidate'}
                                </h3>
                                <span
                                  className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                                    app.status === 'SUBMITTED'
                                      ? 'bg-blue-950 text-blue-400 border border-blue-800'
                                      : app.status === 'UNDER_REVIEW'
                                      ? 'bg-amber-950 text-amber-400 border border-amber-800'
                                      : app.status === 'SHORTLISTED'
                                      ? 'bg-purple-950 text-purple-400 border border-purple-800'
                                      : app.status === 'HIRED'
                                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                                      : app.status === 'REJECTED'
                                      ? 'bg-rose-950 text-rose-400 border border-rose-800'
                                      : 'bg-slate-800 text-slate-400 border border-slate-700'
                                  }`}
                                >
                                  {app.status}
                                </span>
                              </div>

                              <div className="text-xs text-slate-400 flex flex-wrap gap-x-4 gap-y-1">
                                <span>Applied For: <strong className="text-indigo-400">{app.job_title}</strong></span>
                                {app.candidate_email && <span>Email: <strong>{app.candidate_email}</strong></span>}
                                {app.candidate_headline && <span>Headline: <em>{app.candidate_headline}</em></span>}
                              </div>

                              <div className="text-[11px] text-slate-500 flex items-center gap-2 mt-1">
                                <span>Applied: {new Date(app.submitted_at).toLocaleString()}</span>
                                <span>·</span>
                                <span>Pinned Resume: <strong className="text-slate-300">{app.resume_filename}</strong></span>
                              </div>
                            </div>

                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleDownloadSubmittedResume(app.id, app.resume_filename)}
                                className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-700 transition flex items-center gap-1.5"
                              >
                                <span>⬇️</span> Resume
                              </button>
                              <button
                                onClick={() => openRecruiterAppDetail(app)}
                                className="px-3 py-1.5 text-xs bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-semibold shadow transition"
                              >
                                Manage Status & Details
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* SUBTAB 3: AI CANDIDATE SCREENING ENGINE */}
                {recruiterSubTab === 'screening' && (
                  <div className="flex flex-col gap-6">
                    {/* Header Controls & Job Selector */}
                    <div className="bg-slate-950/40 border border-slate-800 rounded-2xl p-4 flex flex-wrap gap-4 items-center justify-between">
                      <div className="flex flex-wrap gap-3 items-center flex-1">
                        <div>
                          <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                            Target Job
                          </label>
                          <select
                            value={screeningJobId}
                            onChange={(e) => {
                              setScreeningJobId(e.target.value);
                              fetchScreeningRuns(e.target.value);
                            }}
                            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-purple-500"
                          >
                            {recruiterJobs.map((j) => (
                              <option key={j.id} value={j.id}>
                                {j.title} ({j.status})
                              </option>
                            ))}
                          </select>
                        </div>

                        {screeningRuns.length > 0 && (
                          <div>
                            <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                              Screening Run
                            </label>
                            <select
                              value={selectedRunId}
                              onChange={(e) => setSelectedRunId(e.target.value)}
                              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-purple-500"
                            >
                              {screeningRuns.map((r, idx) => (
                                <option key={r.id} value={r.id}>
                                  Run #{screeningRuns.length - idx}: {new Date(r.created_at).toLocaleString()} ({r.status} - {r.total_applications} apps)
                                </option>
                              ))}
                            </select>
                          </div>
                        )}
                      </div>

                      {isRecruiterOrAbove && (
                        <button
                          onClick={() => handleOpenTriggerModal()}
                          className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-xs font-semibold shadow-lg shadow-purple-900/30 transition flex items-center gap-2"
                        >
                          <span>⚡</span> Trigger New Screening Run
                        </button>
                      )}
                    </div>

                    {/* Decision-Support Regulatory & Fairness Notice */}
                    <div className="p-4 bg-purple-950/30 border border-purple-800/60 rounded-xl text-xs text-purple-200 flex flex-col md:flex-row gap-3 items-start md:items-center justify-between">
                      <div className="space-y-1">
                        <div className="font-semibold text-purple-100 flex items-center gap-1.5">
                          <span>🛡️</span> Decision-Support Notice: Explainable AI Evaluation
                        </div>
                        <p className="text-[11px] text-purple-300/90 leading-relaxed max-w-4xl">
                          Candidate scores are calculated deterministically using extracted resume evidence: <strong>60% Required Skills</strong>, <strong>15% Preferred Skills</strong>, and <strong>25% Experience</strong>. Missing resume evidence does not establish that a candidate lacks a capability. All shortlisting and hiring decisions remain strictly human-driven.
                        </p>
                      </div>
                      <div className="text-[10px] bg-purple-900/40 border border-purple-700/50 px-2.5 py-1 rounded-md text-purple-300 shrink-0">
                        Formula: Deterministic v1.0.0
                      </div>
                    </div>

                    {/* Historical Runs Strip */}
                    {screeningRuns.length > 0 && (
                      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
                        <span className="text-[11px] text-slate-400 font-semibold uppercase tracking-wider shrink-0">
                          Runs:
                        </span>
                        {screeningRuns.map((r) => {
                          const isSelected = r.id === selectedRunId;
                          return (
                            <button
                              key={r.id}
                              onClick={() => setSelectedRunId(r.id)}
                              className={`px-3 py-1.5 rounded-lg border transition shrink-0 flex items-center gap-2 text-xs ${
                                isSelected
                                  ? 'bg-purple-900/80 border-purple-500 text-purple-100 font-semibold'
                                  : 'bg-slate-900/80 border-slate-800 text-slate-400 hover:text-slate-200'
                              }`}
                            >
                              <span>{new Date(r.created_at).toLocaleDateString()}</span>
                              <span
                                className={`text-[10px] px-1.5 py-0.2 rounded font-medium ${
                                  r.status === 'COMPLETED'
                                    ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                                    : r.status === 'PROCESSING'
                                    ? 'bg-blue-950 text-blue-400 border border-blue-800 animate-pulse'
                                    : 'bg-red-950 text-red-400 border border-red-800'
                                }`}
                              >
                                {r.status}
                              </span>
                              <span className="text-[10px] text-slate-400">
                                ({r.processed_applications}/{r.total_applications})
                              </span>
                            </button>
                          );
                        })}
                      </div>
                    )}

                    {/* Filter and Search Bar for Current Run */}
                    {selectedRunId && (
                      <div className="bg-slate-950/40 border border-slate-800 rounded-xl p-3 flex flex-wrap gap-3 items-center justify-between text-xs">
                        <div className="flex flex-wrap gap-3 items-center flex-1">
                          <input
                            type="text"
                            placeholder="Filter by candidate name or email..."
                            value={screeningKeyword}
                            onChange={(e) => setScreeningKeyword(e.target.value)}
                            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-slate-100 focus:outline-none focus:border-purple-500 min-w-[220px]"
                          />
                          <select
                            value={screeningScoreFilter}
                            onChange={(e) => setScreeningScoreFilter(e.target.value)}
                            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-slate-100 focus:outline-none focus:border-purple-500"
                          >
                            <option value="">All Scores</option>
                            <option value="75">Strong Match (≥ 75%)</option>
                            <option value="50">Moderate Match (≥ 50%)</option>
                            <option value="25">Low Match (≥ 25%)</option>
                          </select>
                        </div>
                        <div className="text-slate-400 text-[11px]">
                          Ranked Leaderboard ({screeningResults.length} candidates)
                        </div>
                      </div>
                    )}

                    {/* Results Table / Leaderboard */}
                    {screeningRunsLoading || screeningResultsLoading ? (
                      <div className="p-12 text-center text-slate-500 text-xs">
                        Loading candidate screening evaluations...
                      </div>
                    ) : screeningRuns.length === 0 ? (
                      <div className="p-12 text-center bg-slate-950/30 border border-dashed border-slate-800 rounded-2xl flex flex-col items-center gap-3">
                        <span className="text-3xl">🎯</span>
                        <div className="font-semibold text-slate-300 text-sm">
                          No Screening Runs Found for this Job
                        </div>
                        <p className="text-xs text-slate-500 max-w-md">
                          Trigger an AI screening run to evaluate all submitted candidate applications against job requirements using grounded evidence and deterministic scoring.
                        </p>
                        {isRecruiterOrAbove && (
                          <button
                            onClick={() => handleOpenTriggerModal()}
                            className="mt-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-xs font-semibold shadow transition"
                          >
                            Start Candidate Screening
                          </button>
                        )}
                      </div>
                    ) : (
                      <div className="border border-slate-800 rounded-2xl overflow-hidden bg-slate-900/60 shadow-xl">
                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-xs text-slate-300">
                            <thead className="bg-slate-950/80 text-slate-400 text-[11px] uppercase tracking-wider border-b border-slate-800">
                              <tr>
                                <th className="py-3 px-4 w-12 text-center">Rank</th>
                                <th className="py-3 px-4">Candidate</th>
                                <th className="py-3 px-4">Submitted Resume</th>
                                <th className="py-3 px-4">Required Skills (60%)</th>
                                <th className="py-3 px-4">Exp Score (25%)</th>
                                <th className="py-3 px-4 text-center">Overall Score</th>
                                <th className="py-3 px-4 text-center">Confidence</th>
                                <th className="py-3 px-4 text-right">Actions</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/60">
                              {screeningResults
                                .filter((item) => {
                                  if (!screeningKeyword.trim()) return true;
                                  const kw = screeningKeyword.toLowerCase();
                                  return (
                                    (item.candidate_name || '').toLowerCase().includes(kw) ||
                                    (item.candidate_email || '').toLowerCase().includes(kw)
                                  );
                                })
                                .map((item, idx) => {
                                  const score = item.total_score ?? 0;
                                  const scoreColor =
                                    score >= 75
                                      ? 'bg-emerald-950 text-emerald-300 border-emerald-700'
                                      : score >= 50
                                      ? 'bg-amber-950 text-amber-300 border-amber-700'
                                      : 'bg-slate-800 text-slate-300 border-slate-700';

                                  return (
                                    <React.Fragment key={item.id}>
                                      <tr className="hover:bg-slate-800/40 transition">
                                        <td className="py-3 px-4 text-center font-bold text-slate-400">
                                          #{idx + 1}
                                        </td>
                                      <td className="py-3 px-4">
                                        <div className="font-semibold text-slate-100">
                                          {item.candidate_name || 'Anonymous Candidate'}
                                        </div>
                                        <div className="text-[11px] text-slate-400">
                                          {item.candidate_email || 'No email provided'}
                                        </div>
                                        {item.candidate_headline && (
                                          <div className="text-[10px] text-indigo-400 truncate max-w-[200px]">
                                            {item.candidate_headline}
                                          </div>
                                        )}
                                        <button
                                          onClick={() => toggleExpandResult(item.id)}
                                          className="text-[10px] text-purple-400 hover:text-purple-300 font-semibold flex items-center gap-1 mt-1 transition"
                                        >
                                          <span>💡</span> Why this score? {expandedResultIds[item.id] ? '▲' : '▼'}
                                        </button>
                                      </td>
                                      <td className="py-3 px-4">
                                        <button
                                          onClick={() =>
                                            handleDownloadSubmittedResume(
                                              item.application_id,
                                              item.resume_filename || 'submitted_resume.pdf'
                                            )
                                          }
                                          className="text-xs text-indigo-400 hover:text-indigo-300 underline font-mono flex items-center gap-1"
                                          title="Download exactly pinned submitted resume"
                                        >
                                          <span>📄</span> {item.resume_filename || 'resume.pdf'}
                                        </button>
                                      </td>
                                      <td className="py-3 px-4">
                                        <div className="flex items-center gap-2">
                                          <div className="w-20 bg-slate-800 rounded-full h-2 overflow-hidden border border-slate-700">
                                            <div
                                              className="bg-purple-500 h-full rounded-full"
                                              style={{ width: `${item.required_skill_score || 0}%` }}
                                            />
                                          </div>
                                          <span className="font-mono text-[11px] text-slate-200">
                                            {item.required_skill_score?.toFixed(0) || 0}%
                                          </span>
                                        </div>
                                        <div className="text-[10px] text-slate-400 mt-0.5">
                                          {item.matched_skills_count} matched · {item.missing_evidence_count} missing
                                        </div>
                                      </td>
                                      <td className="py-3 px-4 font-mono text-slate-300">
                                        {item.experience_score !== null && item.experience_score !== undefined
                                          ? `${item.experience_score.toFixed(0)}%`
                                          : 'N/A'}
                                      </td>
                                      <td className="py-3 px-4 text-center">
                                        <span
                                          className={`inline-block px-2.5 py-1 rounded-full text-xs font-mono font-bold border ${scoreColor}`}
                                        >
                                          {item.total_score !== null && item.total_score !== undefined
                                            ? `${item.total_score.toFixed(1)}/100`
                                            : 'PENDING'}
                                        </span>
                                      </td>
                                      <td className="py-3 px-4 text-center">
                                        <span
                                          className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                                            item.confidence_level === 'HIGH'
                                              ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800'
                                              : item.confidence_level === 'MEDIUM'
                                              ? 'bg-amber-950/80 text-amber-400 border border-amber-800'
                                              : 'bg-slate-800 text-slate-400 border border-slate-700'
                                          }`}
                                        >
                                          {item.confidence_level || 'UNKNOWN'}
                                        </span>
                                      </td>
                                      <td className="py-3 px-4 text-right">
                                        <button
                                          onClick={() => openResultDetailModal(item.id)}
                                          className="px-3 py-1.5 bg-purple-950 hover:bg-purple-900 text-purple-300 border border-purple-800 rounded-lg transition font-medium text-xs flex items-center gap-1.5 ml-auto"
                                        >
                                          <span>🔍</span> View Evidence
                                        </button>
                                      </td>
                                    </tr>

                                    {/* Expandable "Why this score?" compact section */}
                                    {expandedResultIds[item.id] && (
                                      <tr key={`${item.id}-insight`} className="bg-purple-950/20 border-b border-purple-900/30 animate-fadeIn">
                                        <td colSpan={8} className="py-3 px-6">
                                          <div className="flex flex-col gap-2 text-xs">
                                            <div className="flex items-center justify-between">
                                              <div className="font-semibold text-purple-300 flex items-center gap-1.5">
                                                <span>💡</span> Candidate Insight: Why this score?
                                                <span className="text-[10px] bg-purple-900/40 border border-purple-700/50 px-2 py-0.2 rounded text-purple-200">
                                                  Decision-Support AI
                                                </span>
                                              </div>
                                              <button
                                                onClick={() => openResultDetailModal(item.id)}
                                                className="text-[11px] text-purple-400 hover:text-purple-200 underline font-medium"
                                              >
                                                View Complete Breakdown & Evidence Quotes →
                                              </button>
                                            </div>
                                            <p className="text-slate-300 leading-relaxed text-[11px] max-w-4xl">
                                              {item.insight_summary || 'Evidence evaluated against job requirements. Click below for complete breakdown.'}
                                            </p>
                                          </div>
                                        </td>
                                      </tr>
                                    )}
                                  </React.Fragment>
                                );
                              })}
                              {screeningResults.length === 0 && (
                                <tr>
                                  <td colSpan={8} className="py-8 text-center text-slate-500">
                                    No candidate applications evaluated in this run.
                                  </td>
                                </tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* SUBTAB 4: CANDIDATE MATCHER PIPELINE */}
                {recruiterSubTab === 'matcher' && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <section className="flex flex-col gap-4 bg-slate-950/40 p-6 rounded-xl border border-slate-800">
                      <h2 className="text-lg font-semibold text-slate-200">Parse Requirements</h2>
                      <p className="text-sm text-slate-400 -mt-2">
                        Paste target technical skills or job descriptions to cross-match candidate profiles.
                      </p>
                      <textarea
                        className="w-full h-48 bg-slate-900 border border-slate-700 rounded-lg p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition resize-none"
                        placeholder="e.g. Seeking Full Stack Developer with 4+ years of React, Node.js, TypeScript, PostgreSQL..."
                        value={jdText}
                        onChange={(e) => setJdText(e.target.value)}
                      />
                      <button
                        onClick={handleMatch}
                        disabled={matchLoading || !jdText.trim()}
                        className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 text-white font-medium py-2 rounded-lg transition"
                      >
                        {matchLoading ? 'Matching Candidates...' : 'Run Match Pipeline'}
                      </button>
                      {matchError && <div className="text-red-400 text-sm mt-2">{matchError}</div>}
                    </section>

                    <section className="flex flex-col gap-4 bg-slate-950/40 p-6 rounded-xl border border-slate-800">
                      <h2 className="text-lg font-semibold text-slate-200">Ranked Matches ({matchCandidates.length})</h2>
                      <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
                        {matchCandidates.map((cand) => (
                          <div key={cand.id} className="bg-slate-900 border border-slate-800 rounded-lg p-4">
                            <div className="flex justify-between items-center mb-2">
                              <h3 className="font-bold text-slate-200">{cand.name}</h3>
                              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                                Score: {Math.round(cand.score * 100)}%
                              </span>
                            </div>
                            <p className="text-xs text-slate-400 mb-2">YOE: {cand.yoe_status}</p>
                            <div className="text-xs text-slate-300 mb-2">{cand.reasoning}</div>
                            <div className="flex flex-wrap gap-1">
                              {cand.matched_skills.map((s, idx) => (
                                <span key={idx} className="bg-emerald-950 text-emerald-400 text-[10px] px-1.5 py-0.5 rounded border border-emerald-800">
                                  ✓ {s}
                                </span>
                              ))}
                              {cand.missing_skills.map((s, idx) => (
                                <span key={idx} className="bg-rose-950 text-rose-400 text-[10px] px-1.5 py-0.5 rounded border border-rose-800">
                                  ✗ {s}
                                </span>
                              ))}
                            </div>
                          </div>
                        ))}
                        {matchCandidates.length === 0 && !matchLoading && (
                          <div className="text-slate-500 text-sm italic">Run match to view ranked candidate profiles.</div>
                        )}
                      </div>
                    </section>
                  </div>
                )}

                {/* CREATE / EDIT JOB MODAL */}
                {isJobModalOpen && (
                  <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                    <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 shadow-2xl flex flex-col gap-4">
                      <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                        <h2 className="text-lg font-bold text-slate-100">
                          {editingJob ? 'Edit Job Posting' : 'Create New Job (Draft)'}
                        </h2>
                        <button
                          onClick={() => setIsJobModalOpen(false)}
                          className="text-slate-400 hover:text-slate-100 text-sm font-bold"
                        >
                          ✕
                        </button>
                      </div>

                      {jobFormError && (
                        <div className="p-3 bg-red-950/60 border border-red-800 text-red-300 text-xs rounded-lg">
                          {jobFormError}
                        </div>
                      )}

                      <form onSubmit={handleSaveJob} className="flex flex-col gap-4 text-xs">
                        {/* Title & Department */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="block font-semibold text-slate-300 mb-1">
                              Job Title <span className="text-red-400">*</span>
                            </label>
                            <input
                              type="text"
                              required
                              value={jobFormData.title}
                              onChange={(e) => setJobFormData({ ...jobFormData, title: e.target.value })}
                              placeholder="e.g. Senior Backend Engineer"
                              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                            />
                          </div>
                          <div>
                            <label className="block font-semibold text-slate-300 mb-1">Department</label>
                            <input
                              type="text"
                              value={jobFormData.department}
                              onChange={(e) => setJobFormData({ ...jobFormData, department: e.target.value })}
                              placeholder="e.g. Platform Infrastructure"
                              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                            />
                          </div>
                        </div>

                        {/* Location, Workplace, Employment */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div>
                            <label className="block font-semibold text-slate-300 mb-1">Location</label>
                            <input
                              type="text"
                              value={jobFormData.location}
                              onChange={(e) => setJobFormData({ ...jobFormData, location: e.target.value })}
                              placeholder="e.g. Bengaluru, India"
                              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                            />
                          </div>
                          <div>
                            <label className="block font-semibold text-slate-300 mb-1">Workplace Type</label>
                            <select
                              value={jobFormData.workplace_type}
                              onChange={(e) => setJobFormData({ ...jobFormData, workplace_type: e.target.value })}
                              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                            >
                              <option value="ONSITE">Onsite</option>
                              <option value="REMOTE">Remote</option>
                              <option value="HYBRID">Hybrid</option>
                            </select>
                          </div>
                          <div>
                            <label className="block font-semibold text-slate-300 mb-1">Employment Type</label>
                            <select
                              value={jobFormData.employment_type}
                              onChange={(e) => setJobFormData({ ...jobFormData, employment_type: e.target.value })}
                              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                            >
                              <option value="FULL_TIME">Full Time</option>
                              <option value="PART_TIME">Part Time</option>
                              <option value="CONTRACT">Contract</option>
                              <option value="INTERNSHIP">Internship</option>
                            </select>
                          </div>
                        </div>

                        {/* Experience Range & Salary */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div>
                            <label className="block font-semibold text-slate-300 mb-1">Min Exp (Yrs)</label>
                            <input
                              type="number"
                              min="0"
                              value={jobFormData.experience_min}
                              onChange={(e) => setJobFormData({ ...jobFormData, experience_min: e.target.value })}
                              placeholder="e.g. 3"
                              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                            />
                          </div>
                          <div>
                            <label className="block font-semibold text-slate-300 mb-1">Max Exp (Yrs)</label>
                            <input
                              type="number"
                              min="0"
                              value={jobFormData.experience_max}
                              onChange={(e) => setJobFormData({ ...jobFormData, experience_max: e.target.value })}
                              placeholder="e.g. 7"
                              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                            />
                          </div>
                          <div>
                            <label className="block font-semibold text-slate-300 mb-1">Min Salary</label>
                            <input
                              type="number"
                              min="0"
                              value={jobFormData.salary_min}
                              onChange={(e) => setJobFormData({ ...jobFormData, salary_min: e.target.value })}
                              placeholder="e.g. 1500000"
                              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                            />
                          </div>
                          <div>
                            <label className="block font-semibold text-slate-300 mb-1">Max Salary</label>
                            <input
                              type="number"
                              min="0"
                              value={jobFormData.salary_max}
                              onChange={(e) => setJobFormData({ ...jobFormData, salary_max: e.target.value })}
                              placeholder="e.g. 2500000"
                              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                            />
                          </div>
                        </div>

                        {/* Description */}
                        <div>
                          <label className="block font-semibold text-slate-300 mb-1">
                            Description <span className="text-red-400">*</span>
                          </label>
                          <textarea
                            required
                            rows={3}
                            value={jobFormData.description}
                            onChange={(e) => setJobFormData({ ...jobFormData, description: e.target.value })}
                            placeholder="Detailed overview of the role..."
                            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 resize-none"
                          />
                        </div>

                        {/* Responsibilities & Qualifications */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="block font-semibold text-slate-300 mb-1">Responsibilities</label>
                            <textarea
                              rows={2}
                              value={jobFormData.responsibilities}
                              onChange={(e) => setJobFormData({ ...jobFormData, responsibilities: e.target.value })}
                              placeholder="Key duties..."
                              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 resize-none"
                            />
                          </div>
                          <div>
                            <label className="block font-semibold text-slate-300 mb-1">Qualifications</label>
                            <textarea
                              rows={2}
                              value={jobFormData.qualifications}
                              onChange={(e) => setJobFormData({ ...jobFormData, qualifications: e.target.value })}
                              placeholder="Required background..."
                              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 resize-none"
                            />
                          </div>
                        </div>

                        {/* Skills */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="block font-semibold text-slate-300 mb-1">
                              Required Skills (comma-separated)
                            </label>
                            <input
                              type="text"
                              value={jobFormData.required_skills}
                              onChange={(e) => setJobFormData({ ...jobFormData, required_skills: e.target.value })}
                              placeholder="e.g. Python, FastAPI, PostgreSQL"
                              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                            />
                          </div>
                          <div>
                            <label className="block font-semibold text-slate-300 mb-1">
                              Preferred Skills (comma-separated)
                            </label>
                            <input
                              type="text"
                              value={jobFormData.preferred_skills}
                              onChange={(e) => setJobFormData({ ...jobFormData, preferred_skills: e.target.value })}
                              placeholder="e.g. Docker, Kubernetes, AWS"
                              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                            />
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="border-t border-slate-800 pt-3 flex justify-end gap-3 mt-2">
                          <button
                            type="button"
                            onClick={() => setIsJobModalOpen(false)}
                            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                          >
                            Cancel
                          </button>
                          <button
                            type="submit"
                            disabled={jobFormSaving}
                            className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg shadow transition disabled:opacity-50"
                          >
                            {jobFormSaving ? 'Saving...' : editingJob ? 'Update Job' : 'Save as Draft'}
                          </button>
                        </div>
                      </form>
                    </div>
                  </div>
                )}

                {/* CREATE ORGANIZATION MODAL */}
                {isOrgModalOpen && (
                  <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                    <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 shadow-2xl flex flex-col gap-4">
                      <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                        <h2 className="text-md font-bold text-slate-100">Create New Organization</h2>
                        <button
                          onClick={() => setIsOrgModalOpen(false)}
                          className="text-slate-400 hover:text-slate-100 text-sm font-bold"
                        >
                          ✕
                        </button>
                      </div>

                      {orgError && (
                        <div className="p-3 bg-red-950/60 border border-red-800 text-red-300 text-xs rounded-lg">
                          {orgError}
                        </div>
                      )}

                      <form onSubmit={handleCreateOrganization} className="flex flex-col gap-4 text-xs">
                        <div>
                          <label className="block font-semibold text-slate-300 mb-1">Organization Name *</label>
                          <input
                            type="text"
                            required
                            value={newOrgName}
                            onChange={(e) => setNewOrgName(e.target.value)}
                            placeholder="e.g. Acme Corporation"
                            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="block font-semibold text-slate-300 mb-1">Slug (optional)</label>
                          <input
                            type="text"
                            value={newOrgSlug}
                            onChange={(e) => setNewOrgSlug(e.target.value)}
                            placeholder="e.g. acme-corp"
                            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                          />
                        </div>
                        <div className="border-t border-slate-800 pt-3 flex justify-end gap-3">
                          <button
                            type="button"
                            onClick={() => setIsOrgModalOpen(false)}
                            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                          >
                            Cancel
                          </button>
                          <button
                            type="submit"
                            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg shadow transition"
                          >
                            Create
                          </button>
                        </div>
                      </form>
                    </div>
                  </div>
                )}

                {/* 1. APPLY TO JOB MODAL */}
                {isApplyModalOpen && applyJob && (
                  <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                    <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto p-6 shadow-2xl flex flex-col gap-4">
                      <div className="flex justify-between items-start border-b border-slate-800 pb-3">
                        <div>
                          <h2 className="text-lg font-bold text-slate-100">Apply for Job</h2>
                          <div className="text-xs text-indigo-400 font-medium mt-0.5">
                            {applyJob.title} · {applyJob.organization_name}
                          </div>
                        </div>
                        <button
                          onClick={() => setIsApplyModalOpen(false)}
                          className="text-slate-400 hover:text-slate-100 text-sm font-bold"
                        >
                          ✕
                        </button>
                      </div>

                      {applyError && (
                        <div className="p-3 bg-red-950/60 border border-red-800 text-red-300 text-xs rounded-lg">
                          {applyError}
                        </div>
                      )}

                      {applySuccess && (
                        <div className="p-3 bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-xs rounded-lg">
                          ✓ {applySuccess}
                        </div>
                      )}

                      <form onSubmit={handleApplySubmit} className="flex flex-col gap-4 text-xs">
                        {/* Resume Selector */}
                        <div>
                          <label className="block font-semibold text-slate-300 mb-1">
                            Select Resume Version to Pin *
                          </label>
                          {resumes.length === 0 ? (
                            <div className="p-3 bg-amber-950/40 border border-amber-800/60 rounded-lg text-amber-300">
                              No uploaded resumes found. Please go to the{' '}
                              <button
                                type="button"
                                onClick={() => {
                                  setIsApplyModalOpen(false);
                                  setActiveTab('candidate');
                                  setCandidateSubTab('profile-resumes');
                                }}
                                className="underline font-bold"
                              >
                                Candidate Portal
                              </button>{' '}
                              to upload a resume before applying.
                            </div>
                          ) : (
                            <div className="flex flex-col gap-2">
                              {resumes.map((r) => {
                                const isEligible = r.parsing_status !== 'FAILED';
                                return (
                                  <label
                                    key={r.id}
                                    className={`flex items-center justify-between p-3 rounded-xl border transition cursor-pointer ${
                                      selectedResumeId === r.id
                                        ? 'bg-indigo-950/60 border-indigo-500'
                                        : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                                    } ${!isEligible ? 'opacity-50 cursor-not-allowed' : ''}`}
                                  >
                                    <div className="flex items-center gap-3">
                                      <input
                                        type="radio"
                                        name="selectedResume"
                                        value={r.id}
                                        disabled={!isEligible}
                                        checked={selectedResumeId === r.id}
                                        onChange={() => setSelectedResumeId(r.id)}
                                        className="accent-indigo-600"
                                      />
                                      <div className="flex flex-col">
                                        <span className="font-semibold text-slate-200">{r.original_filename}</span>
                                        <span className="text-[10px] text-slate-500">
                                          Uploaded: {new Date(r.created_at).toLocaleDateString()}
                                        </span>
                                      </div>
                                    </div>

                                    <div className="flex items-center gap-2">
                                      {r.is_active && (
                                        <span className="px-2 py-0.5 text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800 rounded font-bold uppercase">
                                          Active
                                        </span>
                                      )}
                                      {!isEligible && (
                                        <span className="px-2 py-0.5 text-[10px] bg-red-950 text-red-400 border border-red-800 rounded font-bold">
                                          Parse Failed
                                        </span>
                                      )}
                                    </div>
                                  </label>
                                );
                              })}
                            </div>
                          )}
                          <p className="text-[11px] text-slate-500 mt-1">
                            Note: The chosen resume file will be strictly pinned to this application and cannot be deleted while the application exists.
                          </p>
                        </div>

                        {/* Cover Letter */}
                        <div>
                          <label className="block font-semibold text-slate-300 mb-1">
                            Cover Letter (Optional)
                          </label>
                          <textarea
                            rows={4}
                            value={coverLetter}
                            onChange={(e) => setCoverLetter(e.target.value)}
                            placeholder="Introduce yourself and explain why you're a great fit for this position..."
                            className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 resize-none"
                          />
                        </div>

                        {/* Modal Footer */}
                        <div className="border-t border-slate-800 pt-3 flex justify-end gap-3 mt-1">
                          <button
                            type="button"
                            onClick={() => setIsApplyModalOpen(false)}
                            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                          >
                            Cancel
                          </button>
                          <button
                            type="submit"
                            disabled={applyLoading || !selectedResumeId}
                            className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg shadow transition disabled:opacity-50"
                          >
                            {applyLoading ? 'Submitting Application...' : 'Confirm & Submit Application'}
                          </button>
                        </div>
                      </form>
                    </div>
                  </div>
                )}

                {/* 2. CANDIDATE APPLICATION DETAILS MODAL */}
                {selectedCandidateApp && (
                  <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                    <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto p-6 shadow-2xl flex flex-col gap-4">
                      <div className="flex justify-between items-start border-b border-slate-800 pb-3">
                        <div>
                          <h2 className="text-lg font-bold text-slate-100">{selectedCandidateApp.job_title}</h2>
                          <div className="text-xs text-indigo-400 font-medium">
                            {selectedCandidateApp.organization_name}
                          </div>
                        </div>
                        <button
                          onClick={() => setSelectedCandidateApp(null)}
                          className="text-slate-400 hover:text-slate-100 text-sm font-bold"
                        >
                          ✕
                        </button>
                      </div>

                      <div className="space-y-3 text-xs text-slate-300">
                        <div className="flex justify-between items-center p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                          <span className="text-slate-400 font-semibold">Application Status</span>
                          <span className="text-xs px-2.5 py-1 rounded-full font-bold uppercase tracking-wider bg-indigo-950 text-indigo-300 border border-indigo-800">
                            {selectedCandidateApp.status}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400">
                          <div>Submitted: <strong className="text-slate-200">{new Date(selectedCandidateApp.submitted_at).toLocaleString()}</strong></div>
                          <div>Updated: <strong className="text-slate-200">{new Date(selectedCandidateApp.status_updated_at).toLocaleString()}</strong></div>
                          {selectedCandidateApp.withdrawn_at && (
                            <div className="col-span-2 text-rose-400">Withdrawn on: <strong>{new Date(selectedCandidateApp.withdrawn_at).toLocaleString()}</strong></div>
                          )}
                        </div>

                        <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                          <span className="text-slate-400 font-semibold block mb-1">Pinned Resume</span>
                          <span className="text-indigo-300 font-medium">📄 {selectedCandidateApp.resume_filename}</span>
                        </div>

                        {selectedCandidateApp.cover_letter && (
                          <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                            <span className="text-slate-400 font-semibold block mb-1">Submitted Cover Letter</span>
                            <p className="whitespace-pre-line text-slate-300 leading-relaxed text-xs">
                              {selectedCandidateApp.cover_letter}
                            </p>
                          </div>
                        )}
                      </div>

                      <div className="border-t border-slate-800 pt-3 flex justify-between items-center text-xs">
                        {['SUBMITTED', 'UNDER_REVIEW', 'SHORTLISTED'].includes(selectedCandidateApp.status) ? (
                          <button
                            onClick={() => handleWithdrawApplication(selectedCandidateApp.id)}
                            className="px-3 py-1.5 bg-rose-950/60 hover:bg-rose-900 text-rose-300 border border-rose-800/60 rounded-lg transition"
                          >
                            Withdraw Application
                          </button>
                        ) : <div />}
                        <button
                          onClick={() => setSelectedCandidateApp(null)}
                          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition"
                        >
                          Close
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* 3. RECRUITER APPLICATION DETAIL & STATUS HISTORY MODAL */}
                {isRecruiterAppModalOpen && selectedRecruiterAppDetail && (
                  <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                    <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 shadow-2xl flex flex-col gap-4">
                      <div className="flex justify-between items-start border-b border-slate-800 pb-3">
                        <div>
                          <h2 className="text-lg font-bold text-slate-100">
                            {selectedRecruiterAppDetail.candidate_name || 'Candidate Application'}
                          </h2>
                          <div className="text-xs text-indigo-400 font-medium mt-0.5">
                            Position: {selectedRecruiterAppDetail.job_title}
                          </div>
                        </div>
                        <button
                          onClick={() => setIsRecruiterAppModalOpen(false)}
                          className="text-slate-400 hover:text-slate-100 text-sm font-bold"
                        >
                          ✕
                        </button>
                      </div>

                      {/* Candidate Snapshot & Resume Download */}
                      <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 flex flex-wrap justify-between items-center gap-4 text-xs">
                        <div className="space-y-1">
                          <div>Email: <strong className="text-slate-200">{selectedRecruiterAppDetail.candidate_email}</strong></div>
                          {selectedRecruiterAppDetail.candidate_headline && (
                            <div>Headline: <strong className="text-slate-200">{selectedRecruiterAppDetail.candidate_headline}</strong></div>
                          )}
                          <div className="text-[11px] text-slate-500">
                            Pinned Resume: <strong className="text-slate-300">{selectedRecruiterAppDetail.resume_filename}</strong>
                          </div>
                        </div>

                        <button
                          onClick={() => handleDownloadSubmittedResume(selectedRecruiterAppDetail.id, selectedRecruiterAppDetail.resume_filename)}
                          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-semibold shadow transition flex items-center gap-1.5"
                        >
                          <span>⬇️</span> Download Submitted PDF
                        </button>
                      </div>

                      {/* Cover Letter */}
                      {selectedRecruiterAppDetail.cover_letter && (
                        <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-xs">
                          <span className="font-semibold text-slate-400 block mb-1">Cover Letter</span>
                          <p className="whitespace-pre-line text-slate-300 leading-relaxed">
                            {selectedRecruiterAppDetail.cover_letter}
                          </p>
                        </div>
                      )}

                      {/* Status Update Form (Only for Recruiter / Admin / Owner) */}
                      {isRecruiterOrAbove ? (
                        <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800 flex flex-col gap-3">
                          <h4 className="font-semibold text-slate-200 text-xs">Update Application Status</h4>

                          {statusUpdateError && (
                            <div className="p-2.5 bg-red-950/60 border border-red-800 text-red-300 text-xs rounded-lg">
                              {statusUpdateError}
                            </div>
                          )}

                          <form onSubmit={handleUpdateAppStatus} className="flex flex-col gap-3 text-xs">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                              <div>
                                <label className="block text-slate-400 mb-1">Select Next Status *</label>
                                <select
                                  value={statusUpdateVal}
                                  onChange={(e) => setStatusUpdateVal(e.target.value)}
                                  required
                                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                                >
                                  <option value="">Choose transition...</option>
                                  {selectedRecruiterAppDetail.status === 'SUBMITTED' && (
                                    <>
                                      <option value="UNDER_REVIEW">Move to Under Review</option>
                                      <option value="SHORTLISTED">Shortlist Candidate</option>
                                      <option value="REJECTED">Reject Application</option>
                                    </>
                                  )}
                                  {selectedRecruiterAppDetail.status === 'UNDER_REVIEW' && (
                                    <>
                                      <option value="SHORTLISTED">Shortlist Candidate</option>
                                      <option value="REJECTED">Reject Application</option>
                                    </>
                                  )}
                                  {selectedRecruiterAppDetail.status === 'SHORTLISTED' && (
                                    <>
                                      <option value="HIRED">Mark as Hired</option>
                                      <option value="REJECTED">Reject Application</option>
                                    </>
                                  )}
                                </select>
                              </div>

                              <div>
                                <label className="block text-slate-400 mb-1">Internal Note (Private to Recruiters)</label>
                                <input
                                  type="text"
                                  value={statusUpdateNote}
                                  onChange={(e) => setStatusUpdateNote(e.target.value)}
                                  placeholder="e.g. Cleared technical interview"
                                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                                />
                              </div>
                            </div>

                            <div className="flex justify-end">
                              <button
                                type="submit"
                                disabled={statusUpdating || !statusUpdateVal}
                                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-semibold shadow transition disabled:opacity-50"
                              >
                                {statusUpdating ? 'Updating Status...' : 'Apply Status Transition'}
                              </button>
                            </div>
                          </form>
                        </div>
                      ) : (
                        <div className="p-3 bg-slate-950/40 border border-slate-800 rounded-xl text-xs text-slate-400">
                          Read-only access: Organization Viewers cannot change application statuses.
                        </div>
                      )}

                      {/* Status History Timeline */}
                      <div className="space-y-2">
                        <h4 className="font-semibold text-slate-300 text-xs">Application Status Audit Timeline</h4>
                        <div className="space-y-2 max-h-48 overflow-y-auto">
                          {selectedRecruiterAppDetail.status_history.map((h) => (
                            <div
                              key={h.id}
                              className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-xs flex justify-between items-start gap-3"
                            >
                              <div>
                                <div className="font-semibold text-slate-200">
                                  {h.previous_status ? `${h.previous_status} → ${h.new_status}` : `Initial Status: ${h.new_status}`}
                                </div>
                                {h.internal_note && (
                                  <div className="text-slate-400 mt-0.5 italic">Note: "{h.internal_note}"</div>
                                )}
                              </div>
                              <span className="text-[10px] text-slate-500 whitespace-nowrap">
                                {new Date(h.changed_at).toLocaleString()}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="border-t border-slate-800 pt-3 flex justify-end">
                        <button
                          onClick={() => setIsRecruiterAppModalOpen(false)}
                          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition text-xs"
                        >
                          Close
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* 4. TRIGGER SCREENING CONFIRMATION MODAL */}
                {isTriggerModalOpen && triggerJob && (
                  <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fadeIn">
                    <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-lg w-full p-6 shadow-2xl flex flex-col gap-4 text-xs">
                      <div className="flex justify-between items-start border-b border-slate-800 pb-3">
                        <div>
                          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                            <span>⚡</span> Trigger Candidate Screening
                          </h2>
                          <div className="text-slate-400 text-xs mt-0.5">
                            Job: <strong className="text-purple-300">{triggerJob.title}</strong>
                          </div>
                        </div>
                        <button
                          onClick={() => setIsTriggerModalOpen(false)}
                          className="text-slate-400 hover:text-slate-100 text-sm font-bold"
                        >
                          ✕
                        </button>
                      </div>

                      {triggerError && (
                        <div className="p-3 bg-red-950/60 border border-red-800 text-red-300 rounded-lg">
                          {triggerError}
                        </div>
                      )}

                      <div className="space-y-3">
                        <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 space-y-2">
                          <div className="font-semibold text-slate-300">Target Requirements Evaluated:</div>
                          <div className="flex flex-wrap gap-1">
                            {triggerJob.required_skills.map((s, idx) => (
                              <span key={idx} className="px-2 py-0.5 bg-purple-950 text-purple-300 border border-purple-800 rounded font-medium text-[11px]">
                                {s} (Required)
                              </span>
                            ))}
                            {triggerJob.preferred_skills.map((s, idx) => (
                              <span key={idx} className="px-2 py-0.5 bg-slate-800 text-slate-300 border border-slate-700 rounded text-[11px]">
                                {s} (Preferred)
                              </span>
                            ))}
                          </div>
                          {(triggerJob.experience_min !== null || triggerJob.experience_max !== null) && (
                            <div className="text-[11px] text-slate-400">
                              Experience: {triggerJob.experience_min ?? 0} to {triggerJob.experience_max ?? '+'} years
                            </div>
                          )}
                        </div>

                        <div className="p-3 bg-amber-950/30 border border-amber-800/50 rounded-xl text-amber-200 space-y-1">
                          <div className="font-semibold flex items-center gap-1.5">
                            <span>⚙️</span> Sequential Inference & Resource Guardrails
                          </div>
                          <p className="text-[11px] text-amber-300/90 leading-relaxed">
                            Screening executes sequentially via local Ollama models (qwen3:4b primary, llama3.2:1b fallback) to protect host memory. Only one screening run can be active at a time for this job.
                          </p>
                        </div>

                        <div className="p-3 bg-slate-950/50 border border-slate-800 rounded-xl text-slate-400 leading-relaxed text-[11px]">
                          <strong>Decision-Support Notice:</strong> Generated scores and evidence citations assist recruiters in review. TalentLens never makes automatic hiring or rejection decisions.
                        </div>
                      </div>

                      <div className="border-t border-slate-800 pt-3 flex justify-end gap-3 mt-2">
                        <button
                          type="button"
                          onClick={() => setIsTriggerModalOpen(false)}
                          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          disabled={triggerLoading}
                          onClick={handleTriggerScreening}
                          className="px-5 py-2 bg-purple-600 hover:bg-purple-500 text-white font-semibold rounded-lg shadow-lg shadow-purple-900/30 transition disabled:opacity-50 flex items-center gap-1.5"
                        >
                          {triggerLoading ? (
                            <>
                              <span className="animate-spin">⏳</span>
                              <span>Starting Sequential Screening...</span>
                            </>
                          ) : (
                            <>
                              <span>⚡</span>
                              <span>Confirm & Run Screening</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* 5. SCREENING RESULT DETAIL & GROUNDED EVIDENCE MODAL */}
                {isResultDetailModalOpen && (
                  <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fadeIn">
                    <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-3xl w-full max-h-[92vh] overflow-y-auto p-6 shadow-2xl flex flex-col gap-5 text-xs">
                      {resultDetailLoading || !selectedResultDetail ? (
                        <div className="py-12 text-center text-slate-400">
                          Loading candidate evidence and scoring breakdown...
                        </div>
                      ) : (
                        <>
                          {/* Modal Header */}
                          <div className="flex justify-between items-start border-b border-slate-800 pb-4">
                            <div>
                              <div className="flex items-center gap-3">
                                <h2 className="text-lg font-bold text-slate-100">
                                  {selectedResultDetail.candidate_name || 'Candidate Evaluation'}
                                </h2>
                                <span
                                  className={`px-3 py-1 rounded-full text-xs font-mono font-bold border ${
                                    (selectedResultDetail.total_score ?? 0) >= 75
                                      ? 'bg-emerald-950 text-emerald-300 border-emerald-700'
                                      : (selectedResultDetail.total_score ?? 0) >= 50
                                      ? 'bg-amber-950 text-amber-300 border-amber-700'
                                      : 'bg-slate-800 text-slate-300 border-slate-700'
                                  }`}
                                >
                                  {selectedResultDetail.total_score != null
                                    ? `${selectedResultDetail.total_score.toFixed(1)} / 100`
                                    : 'PENDING'}
                                </span>
                                <span
                                  className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                                    selectedResultDetail.confidence_level === 'HIGH'
                                      ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800'
                                      : 'bg-amber-950/80 text-amber-400 border border-amber-800'
                                  }`}
                                >
                                  Confidence: {selectedResultDetail.confidence_level || 'UNKNOWN'}
                                </span>
                              </div>
                              <div className="text-slate-400 text-xs mt-1">
                                {selectedResultDetail.candidate_email} · {selectedResultDetail.candidate_headline || 'Candidate'}
                              </div>
                            </div>
                            <button
                              onClick={() => setIsResultDetailModalOpen(false)}
                              className="text-slate-400 hover:text-slate-100 text-base font-bold p-1"
                            >
                              ✕
                            </button>
                          </div>

                          {/* Pinned Resume Banner */}
                          <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 flex justify-between items-center text-xs">
                            <div>
                              <span className="text-slate-400">Evaluated Submitted Resume: </span>
                              <strong className="text-slate-200 font-mono">{selectedResultDetail.resume_filename || 'submitted_resume.pdf'}</strong>
                              <span className="text-[11px] text-slate-500 block">
                                Immutable pinned resume submitted by candidate at time of application
                              </span>
                            </div>
                            <button
                              onClick={() =>
                                handleDownloadSubmittedResume(
                                  selectedResultDetail.application_id,
                                  selectedResultDetail.resume_filename || 'resume.pdf'
                                )
                              }
                              className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-semibold transition flex items-center gap-1.5"
                            >
                              <span>⬇️</span> Download PDF
                            </button>
                          </div>

                          {/* Component Score Cards */}
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            <div className="p-3.5 bg-purple-950/30 border border-purple-800/50 rounded-xl">
                              <div className="text-[11px] text-purple-400 font-semibold uppercase tracking-wider">
                                Required Skills (60%)
                              </div>
                              <div className="text-xl font-bold font-mono text-purple-200 mt-1">
                                {selectedResultDetail.required_skill_score != null
                                  ? `${selectedResultDetail.required_skill_score.toFixed(0)}%`
                                  : 'N/A'}
                              </div>
                              <div className="text-[10px] text-purple-400/80 mt-1">
                                {selectedResultDetail.matched_skills.length} matched / {selectedResultDetail.missing_evidence.length} missing
                              </div>
                            </div>

                            <div className="p-3.5 bg-indigo-950/30 border border-indigo-800/50 rounded-xl">
                              <div className="text-[11px] text-indigo-400 font-semibold uppercase tracking-wider">
                                Preferred Skills (15%)
                              </div>
                              <div className="text-xl font-bold font-mono text-indigo-200 mt-1">
                                {selectedResultDetail.preferred_skill_score != null
                                  ? `${selectedResultDetail.preferred_skill_score.toFixed(0)}%`
                                  : 'N/A'}
                              </div>
                              <div className="text-[10px] text-indigo-400/80 mt-1">
                                {selectedResultDetail.preferred_skill_matches.length} matched
                              </div>
                            </div>

                            <div className="p-3.5 bg-slate-950/50 border border-slate-800 rounded-xl">
                              <div className="text-[11px] text-slate-400 font-semibold uppercase tracking-wider">
                                Experience Assessment (25%)
                              </div>
                              <div className="text-xl font-bold font-mono text-slate-200 mt-1">
                                {selectedResultDetail.experience_score != null
                                  ? `${selectedResultDetail.experience_score.toFixed(0)}%`
                                  : 'N/A'}
                              </div>
                              <div className="text-[10px] text-slate-400 mt-1 truncate">
                                Status: {selectedResultDetail.experience_assessment?.status || 'Assessed'}
                              </div>
                            </div>
                          </div>

                          {/* AI Candidate Insight Generator: "Why this score?" */}
                          {selectedResultDetail.insight && (
                            <div className="p-4 bg-gradient-to-br from-purple-950/40 via-slate-900 to-indigo-950/30 border border-purple-800/60 rounded-xl space-y-4">
                              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-purple-800/40 pb-2.5">
                                <div className="flex items-center gap-2">
                                  <span className="text-base">💡</span>
                                  <div>
                                    <h3 className="font-bold text-purple-200 text-sm">
                                      Candidate Insight: Why this score?
                                    </h3>
                                    <span className="text-[10px] text-purple-300/80">
                                      Decision-Support AI · Model: {selectedResultDetail.insight.model_id} · Schema: {selectedResultDetail.insight.prompt_version}
                                    </span>
                                  </div>
                                </div>
                                <div className="flex items-center gap-2">
                                  {selectedResultDetail.insight.status === 'FAILED' ? (
                                    <div className="flex items-center gap-2">
                                      <span className="text-[10px] px-2 py-0.5 rounded bg-red-950 text-red-300 border border-red-800 font-medium">
                                        Fallback Insight
                                      </span>
                                      <button
                                        disabled={retryingInsight}
                                        onClick={() => handleRetryInsight(selectedResultDetail.id)}
                                        className="px-2.5 py-1 bg-purple-700 hover:bg-purple-600 text-white rounded text-[11px] font-semibold transition disabled:opacity-50"
                                      >
                                        {retryingInsight ? 'Retrying...' : 'Retry AI Generation'}
                                      </button>
                                    </div>
                                  ) : (
                                    <span className="text-[10px] px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800 font-medium">
                                      ✓ Validated Insight
                                    </span>
                                  )}
                                </div>
                              </div>

                              {/* Summary */}
                              <div className="p-3 bg-slate-950/70 rounded-lg border border-purple-900/30 text-xs">
                                <span className="font-semibold text-purple-300 block mb-1">Summary Alignment</span>
                                <p className="text-slate-200 leading-relaxed">
                                  {selectedResultDetail.insight.insight_data.summary}
                                </p>
                              </div>

                              {/* Key Strengths */}
                              {selectedResultDetail.insight.insight_data.key_strengths && selectedResultDetail.insight.insight_data.key_strengths.length > 0 && (
                                <div className="space-y-2">
                                  <h4 className="font-semibold text-purple-200 text-xs flex items-center gap-1.5">
                                    <span>🌟</span> Demonstrated Key Strengths
                                  </h4>
                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                    {selectedResultDetail.insight.insight_data.key_strengths.map((str, idx) => (
                                      <div key={idx} className="p-3 bg-purple-950/20 border border-purple-900/40 rounded-lg text-xs space-y-1">
                                        <div className="flex items-center justify-between">
                                          <strong className="text-purple-300">{str.title}</strong>
                                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-purple-900/50 text-purple-200 border border-purple-700/50">
                                            {str.category}
                                          </span>
                                        </div>
                                        <p className="text-slate-300 text-[11px] leading-relaxed">{str.description}</p>
                                        {str.supporting_evidence && str.supporting_evidence.length > 0 && (
                                          <div className="text-[10px] text-slate-400 italic border-l border-purple-700 pl-2 mt-1">
                                            "{str.supporting_evidence[0]}"
                                          </div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Relevant Projects */}
                              {selectedResultDetail.insight.insight_data.relevant_projects && selectedResultDetail.insight.insight_data.relevant_projects.length > 0 && (
                                <div className="space-y-2">
                                  <h4 className="font-semibold text-purple-200 text-xs flex items-center gap-1.5">
                                    <span>🚀</span> Relevant Demonstrated Projects
                                  </h4>
                                  <div className="grid grid-cols-1 gap-2">
                                    {selectedResultDetail.insight.insight_data.relevant_projects.map((proj, idx) => (
                                      <div key={idx} className="p-3 bg-indigo-950/20 border border-indigo-900/40 rounded-lg text-xs space-y-1">
                                        <div className="flex flex-wrap items-center justify-between gap-1">
                                          <strong className="text-indigo-300">{proj.project_name}</strong>
                                          <div className="flex flex-wrap gap-1">
                                            {(proj.relevant_requirements || []).map((req, rIdx) => (
                                              <span key={rIdx} className="text-[9px] px-1.5 py-0.2 rounded bg-indigo-900/60 text-indigo-200 border border-indigo-700/50">
                                                {req}
                                              </span>
                                            ))}
                                          </div>
                                        </div>
                                        <p className="text-slate-300 text-[11px] leading-relaxed">{proj.description}</p>
                                        {proj.supporting_evidence && proj.supporting_evidence.length > 0 && (
                                          <div className="text-[10px] text-slate-400 italic border-l border-indigo-700 pl-2 mt-1">
                                            "{proj.supporting_evidence[0]}"
                                          </div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Uncertainties (if any) */}
                              {selectedResultDetail.insight.insight_data.uncertainties && selectedResultDetail.insight.insight_data.uncertainties.length > 0 && (
                                <div className="p-3 bg-amber-950/30 border border-amber-900/50 rounded-lg text-xs space-y-1">
                                  <div className="font-semibold text-amber-300 flex items-center gap-1">
                                    <span>⚠️</span> Information Uncertainties
                                  </div>
                                  <ul className="list-disc list-inside text-amber-200/90 text-[11px] space-y-0.5">
                                    {selectedResultDetail.insight.insight_data.uncertainties.map((u, idx) => (
                                      <li key={idx}>{u}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {/* Score Explanation Narrative */}
                              {selectedResultDetail.insight.insight_data.score_explanation && (
                                <div className="text-[11px] text-slate-400 leading-relaxed italic border-t border-purple-900/40 pt-2">
                                  <strong>Scoring Rationale:</strong> {selectedResultDetail.insight.insight_data.score_explanation}
                                </div>
                              )}
                            </div>
                          )}

                          {/* Grounded Explanation Narrative */}
                          <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1.5">
                            <div className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                              <span>📝</span> Deterministic Scoring Narrative
                            </div>
                            <p className="text-slate-300 leading-relaxed text-xs">
                              {selectedResultDetail.explanation}
                            </p>
                          </div>

                          {/* Matched Required Skills with Verbatim Evidence Quotes */}
                          <div className="space-y-2">
                            <h4 className="font-semibold text-slate-200 text-xs flex items-center gap-1.5">
                              <span className="text-emerald-400">✓</span> Evidenced Required Skills ({selectedResultDetail.matched_skills.length})
                            </h4>
                            {selectedResultDetail.matched_skills.length > 0 ? (
                              <div className="grid grid-cols-1 gap-2">
                                {selectedResultDetail.matched_skills.map((item, idx) => (
                                  <div
                                    key={idx}
                                    className="p-3 bg-emerald-950/20 border border-emerald-900/40 rounded-xl text-xs space-y-1"
                                  >
                                    <div className="flex items-center justify-between">
                                      <span className="font-bold text-emerald-300">
                                        {item.skill} {item.canonical_skill && `(${item.canonical_skill})`}
                                      </span>
                                      <span className="text-[10px] text-emerald-400 font-mono">
                                        Confidence: {((item.confidence || 1.0) * 100).toFixed(0)}%
                                      </span>
                                    </div>
                                    <div className="text-slate-300 italic text-[11px] pl-2 border-l border-emerald-800">
                                      "{item.evidence}"
                                    </div>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="p-3 bg-slate-950/40 border border-slate-800 rounded-xl text-slate-500 italic">
                                No required skills were evidenced in the submitted resume.
                              </div>
                            )}
                          </div>

                          {/* Missing Evidence Section */}
                          {selectedResultDetail.missing_evidence.length > 0 && (
                            <div className="space-y-2">
                              <h4 className="font-semibold text-slate-200 text-xs flex items-center gap-1.5">
                                <span className="text-amber-400">⚠️</span> Required Skills Not Evidenced ({selectedResultDetail.missing_evidence.length})
                              </h4>
                              <div className="grid grid-cols-1 gap-2">
                                {selectedResultDetail.missing_evidence.map((item, idx) => (
                                  <div
                                    key={idx}
                                    className="p-3 bg-amber-950/20 border border-amber-900/40 rounded-xl text-xs flex justify-between items-center"
                                  >
                                    <span className="font-semibold text-amber-300">{item.skill}</span>
                                    <span className="text-[11px] text-slate-400 italic">
                                      Not evidenced in submitted resume — does not establish lack of capability
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Preferred Skills Matches */}
                          {selectedResultDetail.preferred_skill_matches.length > 0 && (
                            <div className="space-y-2">
                              <h4 className="font-semibold text-slate-200 text-xs flex items-center gap-1.5">
                                <span className="text-indigo-400">★</span> Evidenced Preferred Skills ({selectedResultDetail.preferred_skill_matches.length})
                              </h4>
                              <div className="grid grid-cols-1 gap-2">
                                {selectedResultDetail.preferred_skill_matches.map((item, idx) => (
                                  <div
                                    key={idx}
                                    className="p-3 bg-indigo-950/20 border border-indigo-900/40 rounded-xl text-xs space-y-1"
                                  >
                                    <span className="font-semibold text-indigo-300">{item.skill}</span>
                                    <div className="text-slate-300 italic text-[11px] pl-2 border-l border-indigo-800">
                                      "{item.evidence}"
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Experience Details */}
                          {selectedResultDetail.experience_assessment && (
                            <div className="p-3.5 bg-slate-950/60 border border-slate-800 rounded-xl space-y-1.5 text-xs">
                              <div className="font-semibold text-slate-200">
                                Experience Assessment Details
                              </div>
                              <div className="text-slate-300 text-[11px]">
                                {selectedResultDetail.experience_assessment.note || 'Experience assessed against job requirements.'}
                              </div>
                              {selectedResultDetail.experience_assessment.verified_years !== null &&
                                selectedResultDetail.experience_assessment.verified_years !== undefined && (
                                  <div className="text-slate-400 text-[11px]">
                                    Verified Years: <strong className="text-slate-200">{selectedResultDetail.experience_assessment.verified_years}</strong> (Required: {selectedResultDetail.experience_assessment.required_min_years ?? 0} years)
                                  </div>
                                )}
                            </div>
                          )}

                          {/* Regulatory Human Decision Footer */}
                          <div className="p-3 bg-purple-950/20 border border-purple-900/40 rounded-xl text-[11px] text-purple-300/80 leading-relaxed">
                            <strong>Compliance & Decision-Support Notice:</strong> This score represents an automated recommendation calculated strictly from submitted resume text evidence. Missing evidence indicates absence of mention, not necessarily absence of candidate capability. Human recruiters retain full discretion and ownership over interview and hiring decisions.
                          </div>

                          {/* Modal Footer */}
                          <div className="border-t border-slate-800 pt-3 flex justify-end">
                            <button
                              onClick={() => setIsResultDetailModalOpen(false)}
                              className="px-5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition text-xs font-semibold"
                            >
                              Close Report
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
