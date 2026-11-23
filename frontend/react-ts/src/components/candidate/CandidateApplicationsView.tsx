import React, { useState } from 'react';
import {
  FileCheck2,
  Search,
  Building2,
  Calendar,
  FileText,
  AlertCircle,
  ExternalLink,
  Ban,
  ArrowRight,
  Eye,
} from 'lucide-react';
import { CandidateApplication } from '../../types';
import { Card, CardBody } from '../common/Card';
import { Button } from '../common/Button';
import { Badge, StatusBadge } from '../common/Badge';
import { Modal } from '../common/Modal';

interface CandidateApplicationsViewProps {
  applications: CandidateApplication[];
  loading: boolean;
  onWithdrawApplication: (appId: string) => Promise<void>;
  onExploreJobs: () => void;
}

export function CandidateApplicationsView({
  applications,
  loading,
  onWithdrawApplication,
  onExploreJobs,
}: CandidateApplicationsViewProps) {
  const [keyword, setKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [withdrawingId, setWithdrawingId] = useState<string | null>(null);
  const [selectedApp, setSelectedApp] = useState<CandidateApplication | null>(null);

  const filtered = applications.filter((app) => {
    const matchKeyword =
      !keyword ||
      app.job_title.toLowerCase().includes(keyword.toLowerCase()) ||
      app.organization_name.toLowerCase().includes(keyword.toLowerCase());
    const matchStatus = !statusFilter || app.status === statusFilter;
    return matchKeyword && matchStatus;
  });

  const handleWithdraw = async (appId: string) => {
    if (window.confirm('Are you sure you want to withdraw this application? This action cannot be reversed.')) {
      setWithdrawingId(appId);
      try {
        await onWithdrawApplication(appId);
        if (selectedApp?.id === appId) {
          setSelectedApp(null);
        }
      } finally {
        setWithdrawingId(null);
      }
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Title & Stats */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#21152F] tracking-tight">My Applications</h2>
          <p className="text-xs text-[#766A87]">
            Track the status of your submitted job applications and pinned resume versions.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={onExploreJobs} icon={<Search className="w-3.5 h-3.5" />}>
          Browse More Jobs
        </Button>
      </div>

      {/* Filter Bar */}
      <Card>
        <CardBody className="p-4 flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-[#766A87] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by job title or organization..."
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
            />
          </div>

          <div className="w-full sm:w-48">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
            >
              <option value="">All Application Statuses</option>
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

      {/* Applications List */}
      {filtered.length === 0 ? (
        <Card>
          <CardBody className="p-12 text-center text-xs text-[#766A87]">
            {applications.length === 0 ? (
              <div>
                <p className="mb-3">You haven't submitted any applications yet.</p>
                <Button variant="primary" size="sm" onClick={onExploreJobs}>
                  Discover Jobs Now
                </Button>
              </div>
            ) : (
              'No applications match your search filters.'
            )}
          </CardBody>
        </Card>
      ) : (
        <div className="space-y-3">
          {filtered.map((app) => (
            <Card key={app.id} hoverEffect className="overflow-hidden">
              <CardBody className="p-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-base font-bold text-[#21152F]">{app.job_title}</h3>
                      <StatusBadge status={app.status} />
                    </div>

                    <div className="flex flex-wrap items-center gap-y-1 gap-x-4 text-xs text-[#766A87]">
                      <span className="flex items-center gap-1">
                        <Building2 className="w-3.5 h-3.5 text-[#7950D9]" />
                        <strong className="text-[#21152F]">{app.organization_name}</strong>
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5" />
                        Applied on {new Date(app.submitted_at).toLocaleDateString()}
                      </span>
                      <span className="flex items-center gap-1">
                        <FileText className="w-3.5 h-3.5 text-blue-600" />
                        Pinned CV: {app.resume_filename}
                      </span>
                    </div>

                    {app.cover_letter && (
                      <p className="mt-2 text-xs text-[#766A87] bg-[#FAF9FD] p-2.5 rounded-lg border border-[#EAE5F2] line-clamp-2">
                        Cover Note: "{app.cover_letter}"
                      </p>
                    )}
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedApp(app)}
                      icon={<Eye className="w-3.5 h-3.5" />}
                    >
                      View Details
                    </Button>
                    {app.status !== 'WITHDRAWN' && app.status !== 'REJECTED' && app.status !== 'HIRED' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleWithdraw(app.id)}
                        isLoading={withdrawingId === app.id}
                        className="text-rose-600 hover:text-rose-700 hover:bg-rose-50"
                        icon={<Ban className="w-3.5 h-3.5" />}
                      >
                        Withdraw
                      </Button>
                    )}
                  </div>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      {/* Application Detail Modal */}
      {selectedApp && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedApp(null)}
          title={selectedApp.job_title}
          subtitle={selectedApp.organization_name + " • Application Details"}
          size="md"
          footer={
            <div className="flex justify-between items-center w-full">
              {['SUBMITTED', 'UNDER_REVIEW', 'SHORTLISTED'].includes(selectedApp.status) ? (
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => handleWithdraw(selectedApp.id)}
                  isLoading={withdrawingId === selectedApp.id}
                  icon={<Ban className="w-3.5 h-3.5" />}
                >
                  Withdraw Application
                </Button>
              ) : <div />}
              <Button variant="outline" size="sm" onClick={() => setSelectedApp(null)}>
                Close
              </Button>
            </div>
          }
        >
          <div className="space-y-4 text-xs">
            <div className="flex justify-between items-center p-3 bg-[#FAF9FD] rounded-xl border border-[#EAE5F2]">
              <span className="text-[#766A87] font-semibold">Application Status</span>
              <StatusBadge status={selectedApp.status} />
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs bg-[#FAF9FD] p-3 rounded-xl border border-[#EAE5F2]">
              <div>
                <span className="text-[#766A87] block text-[11px]">Submitted At</span>
                <span className="font-semibold text-[#21152F]">{new Date(selectedApp.submitted_at).toLocaleString()}</span>
              </div>
              <div>
                <span className="text-[#766A87] block text-[11px]">Last Updated</span>
                <span className="font-semibold text-[#21152F]">{new Date(selectedApp.status_updated_at).toLocaleString()}</span>
              </div>
              {selectedApp.withdrawn_at && (
                <div className="col-span-2 text-rose-600 font-semibold">
                  Withdrawn on: {new Date(selectedApp.withdrawn_at).toLocaleString()}
                </div>
              )}
            </div>

            <div className="p-3 bg-[#FAF9FD] rounded-xl border border-[#EAE5F2]">
              <span className="text-[#766A87] font-semibold block mb-1 text-[11px]">Pinned Resume Version</span>
              <div className="flex items-center gap-2 text-[#7950D9] font-medium">
                <FileText className="w-4 h-4" />
                <span>{selectedApp.resume_filename}</span>
              </div>
            </div>

            {selectedApp.cover_letter && (
              <div className="p-3 bg-[#FAF9FD] rounded-xl border border-[#EAE5F2]">
                <span className="text-[#766A87] font-semibold block mb-1 text-[11px]">Cover Letter</span>
                <p className="whitespace-pre-line text-[#21152F] leading-relaxed">
                  {selectedApp.cover_letter}
                </p>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
