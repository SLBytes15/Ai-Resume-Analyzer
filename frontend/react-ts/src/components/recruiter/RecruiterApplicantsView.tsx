import React, { useState } from 'react';
import {
  Users,
  Search,
  Filter,
  Download,
  Eye,
  Calendar,
  Building2,
  FileText,
  Clock,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  MessageSquare,
} from 'lucide-react';
import {
  RecruiterApplication,
  RecruiterApplicationDetail,
  RecruiterJob,
  Organization,
} from '../../types';
import { Card, CardBody, CardHeader } from '../common/Card';
import { Button } from '../common/Button';
import { Badge, StatusBadge } from '../common/Badge';
import { Modal } from '../common/Modal';

interface RecruiterApplicantsViewProps {
  applications: RecruiterApplication[];
  loading: boolean;
  jobs: RecruiterJob[];
  activeOrg?: Organization;
  jobFilter: string;
  setJobFilter: (val: string) => void;
  statusFilter: string;
  setStatusFilter: (val: string) => void;
  keyword: string;
  setKeyword: (val: string) => void;
  selectedAppDetail: RecruiterApplicationDetail | null;
  isDetailModalOpen: boolean;
  setIsDetailModalOpen: (open: boolean) => void;
  onViewApplicantDetail: (appId: string) => Promise<void>;
  onDownloadResume: (appId: string, filename: string) => void;
  onUpdateStatus: (appId: string, newStatus: string, note: string) => Promise<void>;
  statusUpdating: boolean;
  statusUpdateError: string;
}

export function RecruiterApplicantsView({
  applications,
  loading,
  jobs,
  activeOrg,
  jobFilter,
  setJobFilter,
  statusFilter,
  setStatusFilter,
  keyword,
  setKeyword,
  selectedAppDetail,
  isDetailModalOpen,
  setIsDetailModalOpen,
  onViewApplicantDetail,
  onDownloadResume,
  onUpdateStatus,
  statusUpdating,
  statusUpdateError,
}: RecruiterApplicantsViewProps) {
  const [targetStatus, setTargetStatus] = useState('');
  const [internalNote, setInternalNote] = useState('');

  const isRecruiterOrAbove = activeOrg?.role && ['OWNER', 'ADMIN', 'RECRUITER'].includes(activeOrg.role);

  const filtered = applications.filter((app) => {
    const matchKeyword =
      !keyword ||
      (app.candidate_name && app.candidate_name.toLowerCase().includes(keyword.toLowerCase())) ||
      (app.candidate_email && app.candidate_email.toLowerCase().includes(keyword.toLowerCase())) ||
      app.job_title.toLowerCase().includes(keyword.toLowerCase());
    const matchJob = !jobFilter || app.job_id === jobFilter;
    const matchStatus = !statusFilter || app.status === statusFilter;
    return matchKeyword && matchJob && matchStatus;
  });

  const handleStatusSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAppDetail || !targetStatus) return;
    await onUpdateStatus(selectedAppDetail.id, targetStatus, internalNote.trim());
    setTargetStatus('');
    setInternalNote('');
  };

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-[#21152F] tracking-tight">Applicant Management</h2>
        <p className="text-xs text-[#766A87]">
          Review candidate profiles, download pinned resume versions, and update hiring lifecycle statuses.
        </p>
      </div>

      {/* Filter Bar */}
      <Card>
        <CardBody className="p-4 flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-[#766A87] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by candidate name, email, or role..."
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
            />
          </div>

          <div className="w-full sm:w-56">
            <select
              value={jobFilter}
              onChange={(e) => setJobFilter(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
            >
              <option value="">All Job Requisitions</option>
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title}
                </option>
              ))}
            </select>
          </div>

          <div className="w-full sm:w-44">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
            >
              <option value="">All Statuses</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="UNDER_REVIEW">Under Review</option>
              <option value="SHORTLISTED">Shortlisted</option>
              <option value="INTERVIEWING">Interviewing</option>
              <option value="HIRED">Hired</option>
              <option value="REJECTED">Rejected</option>
              <option value="WITHDRAWN">Withdrawn</option>
            </select>
          </div>
        </CardBody>
      </Card>

      {/* Applicants Table */}
      <Card className="overflow-hidden">
        {filtered.length === 0 ? (
          <CardBody className="p-12 text-center text-xs text-[#766A87]">
            No applicants found matching the selected criteria.
          </CardBody>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#FAF9FD] border-b border-[#EAE5F2] text-[#766A87] font-semibold">
                <tr>
                  <th className="px-6 py-3.5">Candidate</th>
                  <th className="px-6 py-3.5">Applied Position</th>
                  <th className="px-6 py-3.5">Submission Date</th>
                  <th className="px-6 py-3.5">Pinned Resume</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EAE5F2]">
                {filtered.map((app) => (
                  <tr key={app.id} className="hover:bg-[#FAF9FD]/70 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-bold text-[#21152F]">
                        {app.candidate_name || 'Applicant'}
                      </div>
                      <div className="text-[11px] text-[#766A87]">{app.candidate_email}</div>
                    </td>
                    <td className="px-6 py-4 font-medium text-[#21152F]">
                      {app.job_title}
                    </td>
                    <td className="px-6 py-4 text-[#766A87]">
                      {new Date(app.submitted_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-[#766A87]">
                      <button
                        onClick={() => onDownloadResume(app.id, app.resume_filename)}
                        className="inline-flex items-center gap-1.5 text-xs text-[#7950D9] hover:underline font-medium"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>{app.resume_filename}</span>
                      </button>
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={app.status} />
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onViewApplicantDetail(app.id)}
                        icon={<Eye className="w-3.5 h-3.5" />}
                      >
                        Review
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Applicant Detail & Status Lifecycle Modal */}
      {selectedAppDetail && (
        <Modal
          isOpen={isDetailModalOpen}
          onClose={() => setIsDetailModalOpen(false)}
          title={`Applicant: ${selectedAppDetail.candidate_name || 'Candidate'}`}
          description={`Application for ${selectedAppDetail.job_title}`}
          maxWidth="3xl"
        >
          <div className="space-y-6 text-xs">
            {/* Candidate Metadata Summary */}
            <div className="p-4 bg-[#FAF9FD] rounded-xl border border-[#EAE5F2] grid grid-cols-2 sm:grid-cols-4 gap-3 text-[#766A87]">
              <div>Email: <strong className="text-[#21152F] block">{selectedAppDetail.candidate_email}</strong></div>
              <div>Current Status: <div className="mt-0.5"><StatusBadge status={selectedAppDetail.status} /></div></div>
              <div>Submitted: <strong className="text-[#21152F] block">{new Date(selectedAppDetail.submitted_at).toLocaleDateString()}</strong></div>
              <div>
                Pinned PDF:
                <button
                  onClick={() => onDownloadResume(selectedAppDetail.id, selectedAppDetail.resume_filename)}
                  className="text-[#7950D9] hover:underline font-bold flex items-center gap-1 mt-0.5"
                >
                  <Download className="w-3 h-3" /> Download
                </button>
              </div>
            </div>

            {selectedAppDetail.candidate_headline && (
              <div>
                <span className="font-semibold text-[#766A87] block mb-1">Headline:</span>
                <p className="text-[#21152F] font-medium">{selectedAppDetail.candidate_headline}</p>
              </div>
            )}

            {selectedAppDetail.cover_letter && (
              <div>
                <span className="font-semibold text-[#766A87] block mb-1">Cover Note:</span>
                <div className="p-3 bg-[#FAF9FD] rounded-xl border border-[#EAE5F2] text-[#21152F] italic">
                  "{selectedAppDetail.cover_letter}"
                </div>
              </div>
            )}

            {/* Status Transition Form (Authorized Recruiters only) */}
            {isRecruiterOrAbove && selectedAppDetail.status !== 'WITHDRAWN' && (
              <div className="p-4 bg-[#F3EEFF]/40 rounded-xl border border-[#E7DCFF] space-y-3">
                <span className="font-bold text-[#7950D9] block text-xs">
                  Update Candidate Application Stage:
                </span>

                {statusUpdateError && (
                  <div className="p-2.5 rounded-lg bg-rose-50 text-rose-700 text-[11px]">
                    {statusUpdateError}
                  </div>
                )}

                <form onSubmit={handleStatusSubmit} className="space-y-3">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-semibold text-[#21152F] mb-1">
                        Select Target Status *
                      </label>
                      <select
                        required
                        value={targetStatus}
                        onChange={(e) => setTargetStatus(e.target.value)}
                        className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-white text-[#21152F] focus:outline-none focus:border-[#7950D9]"
                      >
                        <option value="">-- Choose target stage --</option>
                        <option value="UNDER_REVIEW">Under Review</option>
                        <option value="SHORTLISTED">Shortlisted</option>
                        <option value="INTERVIEWING">Interviewing</option>
                        <option value="HIRED">Hired</option>
                        <option value="REJECTED">Rejected</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-[#21152F] mb-1">
                        Internal Hiring Note (Optional)
                      </label>
                      <input
                        type="text"
                        placeholder="e.g. Cleared technical screening; schedule round 2"
                        value={internalNote}
                        onChange={(e) => setInternalNote(e.target.value)}
                        className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-white text-[#21152F] focus:outline-none focus:border-[#7950D9]"
                      />
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <Button
                      type="submit"
                      variant="primary"
                      size="sm"
                      isLoading={statusUpdating}
                      disabled={!targetStatus}
                    >
                      Update Application Stage
                    </Button>
                  </div>
                </form>
              </div>
            )}

            {/* Status History Audit Trail */}
            <div>
              <h4 className="font-bold text-[#21152F] mb-2 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-[#766A87]" />
                <span>Status Transition History</span>
              </h4>

              {selectedAppDetail.status_history && selectedAppDetail.status_history.length > 0 ? (
                <div className="space-y-2">
                  {selectedAppDetail.status_history.map((hist) => (
                    <div
                      key={hist.id}
                      className="p-3 bg-[#FAF9FD] rounded-xl border border-[#EAE5F2] flex items-center justify-between text-xs"
                    >
                      <div>
                        <span className="font-bold text-[#21152F]">{hist.new_status}</span>
                        {hist.previous_status && (
                          <span className="text-[#766A87] ml-2">from {hist.previous_status}</span>
                        )}
                        {hist.internal_note && (
                          <p className="text-[11px] text-[#766A87] mt-0.5 italic">
                            Note: "{hist.internal_note}"
                          </p>
                        )}
                      </div>
                      <span className="text-[11px] text-[#766A87]">
                        {new Date(hist.changed_at).toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[#766A87]">No status transitions recorded yet.</p>
              )}
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
