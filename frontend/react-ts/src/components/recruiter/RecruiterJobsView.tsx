import React, { useState } from 'react';
import {
  Briefcase,
  Plus,
  Search,
  MapPin,
  Clock,
  DollarSign,
  Send,
  Lock,
  Archive,
  Edit2,
  CheckCircle2,
  AlertCircle,
  Building2,
} from 'lucide-react';
import { RecruiterJob, Organization } from '../../types';
import { Card, CardBody, CardHeader } from '../common/Card';
import { Button } from '../common/Button';
import { Badge, StatusBadge } from '../common/Badge';
import { Modal } from '../common/Modal';

interface RecruiterJobsViewProps {
  jobs: RecruiterJob[];
  loading: boolean;
  activeOrg?: Organization;
  keywordFilter: string;
  setKeywordFilter: (val: string) => void;
  statusFilter: string;
  setStatusFilter: (val: string) => void;
  onPublishJob: (jobId: string) => Promise<void>;
  onCloseJob: (jobId: string) => Promise<void>;
  onArchiveJob: (jobId: string) => Promise<void>;
  onSaveJob: (formData: any, jobId?: string) => Promise<void>;
  actionMessage: string;
}

export function RecruiterJobsView({
  jobs,
  loading,
  activeOrg,
  keywordFilter,
  setKeywordFilter,
  statusFilter,
  setStatusFilter,
  onPublishJob,
  onCloseJob,
  onArchiveJob,
  onSaveJob,
  actionMessage,
}: RecruiterJobsViewProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingJob, setEditingJob] = useState<RecruiterJob | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [formError, setFormError] = useState('');

  const [formData, setFormData] = useState({
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

  const isRecruiterOrAbove = activeOrg?.role && ['OWNER', 'ADMIN', 'RECRUITER'].includes(activeOrg.role);

  const handleOpenCreate = () => {
    setEditingJob(null);
    setFormData({
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
    setFormError('');
    setIsModalOpen(true);
  };

  const handleOpenEdit = (job: RecruiterJob) => {
    setEditingJob(job);
    setFormData({
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
      required_skills: (job.required_skills || []).join(', '),
      preferred_skills: (job.preferred_skills || []).join(', '),
    });
    setFormError('');
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');

    if (!formData.title.trim() || !formData.description.trim()) {
      setFormError('Job title and detailed description are required.');
      return;
    }

    setIsSaving(true);
    try {
      const payload: any = {
        title: formData.title.trim(),
        description: formData.description.trim(),
        department: formData.department.trim() || undefined,
        responsibilities: formData.responsibilities.trim() || undefined,
        qualifications: formData.qualifications.trim() || undefined,
        location: formData.location.trim() || undefined,
        workplace_type: formData.workplace_type,
        employment_type: formData.employment_type,
        salary_currency: formData.salary_currency,
        required_skills: formData.required_skills
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
        preferred_skills: formData.preferred_skills
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
      };

      if (formData.experience_min) payload.experience_min = parseInt(formData.experience_min, 10);
      if (formData.experience_max) payload.experience_max = parseInt(formData.experience_max, 10);
      if (formData.salary_min) payload.salary_min = parseFloat(formData.salary_min);
      if (formData.salary_max) payload.salary_max = parseFloat(formData.salary_max);

      await onSaveJob(payload, editingJob?.id);
      setIsModalOpen(false);
    } catch (err: any) {
      setFormError(err.message || 'Error saving job requisition');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#21152F] tracking-tight">Job Requisitions</h2>
          <p className="text-xs text-[#766A87]">
            Create, manage, and publish positions for {activeOrg?.name || 'your organization'}.
          </p>
        </div>

        {isRecruiterOrAbove && (
          <Button
            variant="primary"
            size="sm"
            onClick={handleOpenCreate}
            icon={<Plus className="w-4 h-4" />}
          >
            Create Job Requisition
          </Button>
        )}
      </div>

      {actionMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* Filter Bar */}
      <Card>
        <CardBody className="p-4 flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-[#766A87] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by title, department, or description..."
              value={keywordFilter}
              onChange={(e) => setKeywordFilter(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
            />
          </div>

          <div className="w-full sm:w-48">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
            >
              <option value="">All Job Statuses</option>
              <option value="DRAFT">Draft</option>
              <option value="PUBLISHED">Published</option>
              <option value="CLOSED">Closed</option>
              <option value="ARCHIVED">Archived</option>
            </select>
          </div>
        </CardBody>
      </Card>

      {/* Jobs List */}
      {jobs.length === 0 ? (
        <Card>
          <CardBody className="p-12 text-center text-xs text-[#766A87]">
            No job requisitions found in this organization.
            {isRecruiterOrAbove && (
              <div className="mt-3">
                <Button variant="primary" size="sm" onClick={handleOpenCreate}>
                  Create First Job Requisition
                </Button>
              </div>
            )}
          </CardBody>
        </Card>
      ) : (
        <div className="space-y-4">
          {jobs.map((job) => (
            <Card key={job.id} hoverEffect className="overflow-hidden">
              <CardBody className="p-6">
                <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
                  <div className="space-y-2 flex-1">
                    <div className="flex items-center gap-2.5">
                      <h3 className="text-base font-bold text-[#21152F]">{job.title}</h3>
                      <StatusBadge status={job.status} />
                    </div>

                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-[#766A87]">
                      {job.department && (
                        <span className="flex items-center gap-1">
                          <Building2 className="w-3.5 h-3.5 text-[#7950D9]" />
                          {job.department}
                        </span>
                      )}
                      {job.location && (
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5" />
                          {job.location} ({job.workplace_type})
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        {job.employment_type}
                      </span>
                      {job.salary_min && (
                        <span className="flex items-center gap-1 text-emerald-700 font-semibold">
                          <DollarSign className="w-3.5 h-3.5" />
                          {job.salary_currency} {job.salary_min.toLocaleString()}
                          {job.salary_max ? ` - ${job.salary_max.toLocaleString()}` : '+'}
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-[#766A87] line-clamp-2 leading-relaxed">
                      {job.description}
                    </p>

                    {/* Required Skills */}
                    {job.required_skills && job.required_skills.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5 pt-1">
                        <span className="text-[11px] font-semibold text-[#766A87]">Required:</span>
                        {job.required_skills.map((skill, sIdx) => (
                          <span
                            key={sIdx}
                            className="px-2 py-0.5 rounded text-[10px] font-medium bg-[#F3EEFF] text-[#7950D9] border border-[#E7DCFF]"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Actions Column */}
                  {isRecruiterOrAbove && (
                    <div className="flex flex-wrap lg:flex-col items-end gap-2 shrink-0 pt-2 lg:pt-0 border-t lg:border-t-0 border-[#EAE5F2]">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleOpenEdit(job)}
                        icon={<Edit2 className="w-3.5 h-3.5 text-[#766A87]" />}
                      >
                        Edit
                      </Button>

                      {job.status === 'DRAFT' && (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => onPublishJob(job.id)}
                          icon={<Send className="w-3.5 h-3.5" />}
                        >
                          Publish
                        </Button>
                      )}

                      {job.status === 'PUBLISHED' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onCloseJob(job.id)}
                          icon={<Lock className="w-3.5 h-3.5 text-amber-600" />}
                          className="text-amber-700 hover:bg-amber-50"
                        >
                          Close Job
                        </Button>
                      )}

                      {job.status !== 'DRAFT' && job.status !== 'ARCHIVED' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onArchiveJob(job.id)}
                          icon={<Archive className="w-3.5 h-3.5" />}
                        >
                          Archive
                        </Button>
                      )}
                    </div>
                  )}
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      {/* Create / Edit Job Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingJob ? `Edit Job: ${editingJob.title}` : 'Create Job Requisition'}
        description="Specify job requirements, qualifications, and deterministic screening skills."
        maxWidth="3xl"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {formError && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs">
              {formError}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[#21152F] mb-1">
                Job Title *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Lead API Developer"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#21152F] mb-1">
                Department
              </label>
              <input
                type="text"
                placeholder="e.g. Platform Engineering"
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#21152F] mb-1">
              Job Description *
            </label>
            <textarea
              rows={4}
              required
              placeholder="Detailed overview of the role, challenges, and core mission..."
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full p-3 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white leading-relaxed resize-none"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-[#21152F] mb-1">
                Workplace Type
              </label>
              <select
                value={formData.workplace_type}
                onChange={(e) => setFormData({ ...formData, workplace_type: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
              >
                <option value="ONSITE">Onsite</option>
                <option value="REMOTE">Remote</option>
                <option value="HYBRID">Hybrid</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#21152F] mb-1">
                Employment Type
              </label>
              <select
                value={formData.employment_type}
                onChange={(e) => setFormData({ ...formData, employment_type: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
              >
                <option value="FULL_TIME">Full Time</option>
                <option value="PART_TIME">Part Time</option>
                <option value="CONTRACT">Contract</option>
                <option value="INTERNSHIP">Internship</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#21152F] mb-1">
                Location
              </label>
              <input
                type="text"
                placeholder="e.g. Bengaluru, India"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div>
              <label className="block text-xs font-semibold text-[#21152F] mb-1">
                Min Exp (Yrs)
              </label>
              <input
                type="number"
                min="0"
                placeholder="0"
                value={formData.experience_min}
                onChange={(e) => setFormData({ ...formData, experience_min: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#21152F] mb-1">
                Max Exp (Yrs)
              </label>
              <input
                type="number"
                min="0"
                placeholder="10"
                value={formData.experience_max}
                onChange={(e) => setFormData({ ...formData, experience_max: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#21152F] mb-1">
                Min Salary
              </label>
              <input
                type="number"
                min="0"
                placeholder="1000000"
                value={formData.salary_min}
                onChange={(e) => setFormData({ ...formData, salary_min: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#21152F] mb-1">
                Currency
              </label>
              <input
                type="text"
                value={formData.salary_currency}
                onChange={(e) => setFormData({ ...formData, salary_currency: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white uppercase"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#21152F] mb-1">
              Required Skills (comma-separated, 60% of screening score)
            </label>
            <input
              type="text"
              placeholder="e.g. Python, FastAPI, PostgreSQL"
              value={formData.required_skills}
              onChange={(e) => setFormData({ ...formData, required_skills: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white font-medium text-[#7950D9]"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#21152F] mb-1">
              Preferred Skills (comma-separated, 15% of screening score)
            </label>
            <input
              type="text"
              placeholder="e.g. Docker, Redis, Kubernetes, Kafka"
              value={formData.preferred_skills}
              onChange={(e) => setFormData({ ...formData, preferred_skills: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#EAE5F2]">
            <Button variant="ghost" size="sm" type="button" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isSaving}>
              {editingJob ? 'Save Requisition' : 'Create Draft Requisition'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
