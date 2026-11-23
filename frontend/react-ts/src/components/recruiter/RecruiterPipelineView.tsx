import React from 'react';
import {
  GitPullRequest,
  CheckCircle2,
  Clock,
  Sparkles,
  User,
  ArrowRight,
  Filter,
} from 'lucide-react';
import { RecruiterApplication, RecruiterJob, Organization } from '../../types';
import { Card, CardBody, CardHeader } from '../common/Card';
import { Button } from '../common/Button';
import { Badge, StatusBadge } from '../common/Badge';

interface RecruiterPipelineViewProps {
  applications: RecruiterApplication[];
  jobs: RecruiterJob[];
  onViewApplicant: (app: RecruiterApplication) => void;
  activeOrg?: Organization;
}

export function RecruiterPipelineView({
  applications,
  jobs,
  onViewApplicant,
  activeOrg,
}: RecruiterPipelineViewProps) {
  const [selectedJobFilter, setSelectedJobFilter] = React.useState('');

  const filteredApps = selectedJobFilter
    ? applications.filter((a) => a.job_id === selectedJobFilter)
    : applications;

  const stages: Array<{
    id: string;
    title: string;
    color: string;
    apps: RecruiterApplication[];
  }> = [
    {
      id: 'SUBMITTED',
      title: 'Submitted',
      color: 'border-blue-300 bg-blue-50/50',
      apps: filteredApps.filter((a) => a.status === 'SUBMITTED'),
    },
    {
      id: 'UNDER_REVIEW',
      title: 'Under Review',
      color: 'border-amber-300 bg-amber-50/50',
      apps: filteredApps.filter((a) => a.status === 'UNDER_REVIEW'),
    },
    {
      id: 'SHORTLISTED',
      title: 'Shortlisted',
      color: 'border-[#7950D9]/30 bg-[#F3EEFF]/50',
      apps: filteredApps.filter((a) => a.status === 'SHORTLISTED'),
    },
    {
      id: 'INTERVIEWING',
      title: 'Interviewing',
      color: 'border-purple-300 bg-purple-50/50',
      apps: filteredApps.filter((a) => a.status === 'INTERVIEWING'),
    },
    {
      id: 'HIRED',
      title: 'Hired',
      color: 'border-emerald-300 bg-emerald-50/50',
      apps: filteredApps.filter((a) => a.status === 'HIRED'),
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#21152F] tracking-tight">Hiring Pipeline</h2>
          <p className="text-xs text-[#766A87]">
            Visual stage-by-stage progression of candidate applications for {activeOrg?.name || 'organization'}.
          </p>
        </div>

        <div className="w-full sm:w-64">
          <select
            value={selectedJobFilter}
            onChange={(e) => setSelectedJobFilter(e.target.value)}
            className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-white text-[#21152F] focus:outline-none focus:border-[#7950D9]"
          >
            <option value="">All Requisitions ({applications.length})</option>
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                {j.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Visual Kanban Columns */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 overflow-x-auto pb-4">
        {stages.map((stage) => (
          <div key={stage.id} className="flex flex-col min-w-[220px]">
            {/* Column Header */}
            <div className={`p-3 rounded-xl border mb-3 flex items-center justify-between ${stage.color}`}>
              <h3 className="text-xs font-bold text-[#21152F]">{stage.title}</h3>
              <span className="w-5 h-5 rounded-full bg-white text-[#21152F] font-extrabold text-[10px] flex items-center justify-center shadow-xs">
                {stage.apps.length}
              </span>
            </div>

            {/* Column Cards */}
            <div className="space-y-3 flex-1">
              {stage.apps.length === 0 ? (
                <div className="p-4 rounded-xl border border-dashed border-[#EAE5F2] text-center text-[11px] text-[#766A87]">
                  No candidates
                </div>
              ) : (
                stage.apps.map((app) => (
                  <Card
                    key={app.id}
                    hoverEffect
                    onClick={() => onViewApplicant(app)}
                    className="cursor-pointer"
                  >
                    <CardBody className="p-3.5 space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <strong className="text-[#21152F] truncate block">
                          {app.candidate_name || 'Candidate'}
                        </strong>
                      </div>
                      <p className="text-[11px] text-[#766A87] line-clamp-1">{app.job_title}</p>
                      <div className="flex items-center justify-between text-[10px] text-[#766A87] pt-2 border-t border-[#EAE5F2]">
                        <span>{new Date(app.submitted_at).toLocaleDateString()}</span>
                        <span className="text-[#7950D9] font-medium hover:underline">Review →</span>
                      </div>
                    </CardBody>
                  </Card>
                ))
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
