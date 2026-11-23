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
  const [recruiterSubTab, setRecruiterSubTab] = useState<'jobs' | 'matcher'>('jobs');
  const [userOrgs, setUserOrgs] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [recruiterJobs, setRecruiterJobs] = useState<RecruiterJob[]>([]);
  const [recruiterJobsLoading, setRecruiterJobsLoading] = useState(false);
  const [recruiterJobStatusFilter, setRecruiterJobStatusFilter] = useState('');
  const [recruiterJobKeywordFilter, setRecruiterJobKeywordFilter] = useState('');
  const [recruiterActionMessage, setRecruiterActionMessage] = useState('');

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
      const res = await fetch(`${API_BASE}/api/v1/resumes/${resumeId}/set-active`, {
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
                    <button
                      onClick={() => setSelectedPublicJob(null)}
                      className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition"
                    >
                      Close
                    </button>
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

                  {/* Subtabs: Jobs vs Matcher */}
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

                {/* SUBTAB 2: LEGACY CANDIDATE MATCHER */}
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
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
