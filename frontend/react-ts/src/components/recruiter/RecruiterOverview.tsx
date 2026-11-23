import React from 'react';
import {
  Briefcase,
  Users,
  Sparkles,
  GitPullRequest,
  Bot,
  Plus,
  ArrowRight,
  TrendingUp,
  Clock,
  CheckCircle2,
} from 'lucide-react';
import { RecruiterJob, RecruiterApplication, Organization } from '../../types';
import { Card, CardBody, CardHeader } from '../common/Card';
import { Button } from '../common/Button';
import { Badge, StatusBadge } from '../common/Badge';

interface RecruiterOverviewProps {
  activeOrg?: Organization;
  jobs: RecruiterJob[];
  applications: RecruiterApplication[];
  onNavigate: (tab: any) => void;
  onOpenNewJobModal: () => void;
  onViewApplicant: (app: RecruiterApplication) => void;
}

export function RecruiterOverview({
  activeOrg,
  jobs,
  applications,
  onNavigate,
  onOpenNewJobModal,
  onViewApplicant,
}: RecruiterOverviewProps) {
  const publishedJobs = jobs.filter((j) => j.status === 'PUBLISHED');
  const draftJobs = jobs.filter((j) => j.status === 'DRAFT');

  const underReviewCount = applications.filter((a) => a.status === 'UNDER_REVIEW').length;
  const shortlistedCount = applications.filter((a) => a.status === 'SHORTLISTED').length;
  const interviewingCount = applications.filter((a) => a.status === 'INTERVIEWING').length;
  const hiredCount = applications.filter((a) => a.status === 'HIRED').length;
  const submittedCount = applications.filter((a) => a.status === 'SUBMITTED').length;

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-[#43216F] via-[#513296] to-[#7950D9] text-white shadow-lg shadow-[#7950D9]/15 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
        <div>
          <Badge variant="purple" className="bg-white/15 text-white border-white/20 mb-2">
            Hiring Intelligence Hub
          </Badge>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-2">
            {activeOrg?.name || 'Recruitment Organization'} Workspace
          </h2>
          <p className="text-purple-100 text-sm max-w-xl">
            Streamline candidate evaluation with reproducible deterministic scoring, explainable AI insights, and role-based applicant workflows.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={onOpenNewJobModal}
            className="bg-white text-[#7950D9] hover:bg-[#F3EEFF] border-white font-semibold"
            icon={<Plus className="w-4 h-4" />}
          >
            Create Job Requisition
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onNavigate('hiring-assistant')}
            className="text-white hover:bg-white/10"
            icon={<Bot className="w-4 h-4" />}
          >
            Ask Hiring Assistant
          </Button>
        </div>
      </div>

      {/* Stats Metric Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        {/* Open Positions */}
        <Card hoverEffect onClick={() => onNavigate('jobs')} className="cursor-pointer">
          <CardBody className="p-4">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-semibold text-[#766A87]">Open Roles</span>
              <Briefcase className="w-4 h-4 text-[#7950D9]" />
            </div>
            <div className="text-2xl font-extrabold text-[#21152F]">{publishedJobs.length}</div>
            <p className="text-[10px] text-[#766A87] mt-0.5">{draftJobs.length} drafts pending</p>
          </CardBody>
        </Card>

        {/* Total Applicants */}
        <Card hoverEffect onClick={() => onNavigate('applicants')} className="cursor-pointer">
          <CardBody className="p-4">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-semibold text-[#766A87]">Total Applicants</span>
              <Users className="w-4 h-4 text-blue-600" />
            </div>
            <div className="text-2xl font-extrabold text-[#21152F]">{applications.length}</div>
            <p className="text-[10px] text-[#766A87] mt-0.5">{submittedCount} awaiting review</p>
          </CardBody>
        </Card>

        {/* Under Review */}
        <Card hoverEffect onClick={() => onNavigate('pipeline')} className="cursor-pointer">
          <CardBody className="p-4">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-semibold text-[#766A87]">Under Review</span>
              <Clock className="w-4 h-4 text-amber-600" />
            </div>
            <div className="text-2xl font-extrabold text-[#21152F]">{underReviewCount}</div>
            <p className="text-[10px] text-amber-700 font-medium mt-0.5">In active evaluation</p>
          </CardBody>
        </Card>

        {/* Shortlisted */}
        <Card hoverEffect onClick={() => onNavigate('pipeline')} className="cursor-pointer">
          <CardBody className="p-4">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-semibold text-[#766A87]">Shortlisted</span>
              <Sparkles className="w-4 h-4 text-[#7950D9]" />
            </div>
            <div className="text-2xl font-extrabold text-[#7950D9]">{shortlistedCount}</div>
            <p className="text-[10px] text-[#766A87] mt-0.5">Top-scoring candidates</p>
          </CardBody>
        </Card>

        {/* Interviewing */}
        <Card hoverEffect onClick={() => onNavigate('pipeline')} className="cursor-pointer">
          <CardBody className="p-4">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-semibold text-[#766A87]">Interviewing</span>
              <GitPullRequest className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="text-2xl font-extrabold text-emerald-700">{interviewingCount}</div>
            <p className="text-[10px] text-emerald-600 font-medium mt-0.5">{hiredCount} hired to date</p>
          </CardBody>
        </Card>
      </div>

      {/* Visual Pipeline Bar */}
      <Card>
        <CardBody className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-[#21152F]">Active Hiring Pipeline Distribution</h3>
              <p className="text-xs text-[#766A87]">
                Visual progress of all {applications.length} candidate applications across stages.
              </p>
            </div>
            <Button variant="ghost" size="sm" onClick={() => onNavigate('pipeline')}>
              View Full Pipeline
            </Button>
          </div>

          {applications.length === 0 ? (
            <p className="text-xs text-[#766A87] text-center py-4">No applications received yet.</p>
          ) : (
            <div>
              <div className="w-full h-3 rounded-full bg-[#EAE5F2] flex overflow-hidden">
                <div style={{ width: `${(submittedCount / applications.length) * 100}%` }} className="bg-blue-500" title={`Submitted: ${submittedCount}`} />
                <div style={{ width: `${(underReviewCount / applications.length) * 100}%` }} className="bg-amber-500" title={`Under Review: ${underReviewCount}`} />
                <div style={{ width: `${(shortlistedCount / applications.length) * 100}%` }} className="bg-[#7950D9]" title={`Shortlisted: ${shortlistedCount}`} />
                <div style={{ width: `${(interviewingCount / applications.length) * 100}%` }} className="bg-purple-600" title={`Interviewing: ${interviewingCount}`} />
                <div style={{ width: `${(hiredCount / applications.length) * 100}%` }} className="bg-emerald-500" title={`Hired: ${hiredCount}`} />
              </div>

              <div className="flex flex-wrap items-center justify-between gap-2 mt-3 text-[11px] text-[#766A87]">
                <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-blue-500" /> Submitted ({submittedCount})</span>
                <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-amber-500" /> Under Review ({underReviewCount})</span>
                <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#7950D9]" /> Shortlisted ({shortlistedCount})</span>
                <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-purple-600" /> Interviewing ({interviewingCount})</span>
                <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-emerald-500" /> Hired ({hiredCount})</span>
              </div>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Two Column Section: Recent Applicants & Quick Links */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Applicants */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-[#21152F]">Recent Applications</h3>
            <button
              onClick={() => onNavigate('applicants')}
              className="text-xs font-semibold text-[#7950D9] hover:underline"
            >
              View All ({applications.length})
            </button>
          </div>

          {applications.length === 0 ? (
            <Card>
              <CardBody className="p-8 text-center text-xs text-[#766A87]">
                No applicants have submitted applications yet.
              </CardBody>
            </Card>
          ) : (
            <div className="space-y-3">
              {applications.slice(0, 5).map((app) => (
                <Card
                  key={app.id}
                  hoverEffect
                  onClick={() => onViewApplicant(app)}
                  className="cursor-pointer"
                >
                  <CardBody className="p-4 flex items-center justify-between gap-4">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="text-xs font-bold text-[#21152F] truncate">
                          {app.candidate_name || 'Applicant'}
                        </h4>
                        <StatusBadge status={app.status} />
                      </div>
                      <p className="text-[11px] text-[#766A87] truncate">
                        Applied for <strong>{app.job_title}</strong> on {new Date(app.submitted_at).toLocaleDateString()}
                      </p>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <Button variant="ghost" size="sm">
                        Review
                      </Button>
                    </div>
                  </CardBody>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions & AI Tools */}
        <div className="space-y-4">
          <h3 className="text-base font-bold text-[#21152F]">Intelligence Tools</h3>
          <div className="space-y-3">
            <Card hoverEffect onClick={() => onNavigate('screening')} className="cursor-pointer">
              <CardBody className="p-4 flex items-start gap-3">
                <div className="w-9 h-9 rounded-xl bg-[#F3EEFF] text-[#7950D9] flex items-center justify-center shrink-0">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-[#21152F] mb-0.5">Run Batch AI Screening</h4>
                  <p className="text-[11px] text-[#766A87]">
                    Screen candidates against job criteria with deterministic scoring and candidate insights.
                  </p>
                </div>
              </CardBody>
            </Card>

            <Card hoverEffect onClick={() => onNavigate('hiring-assistant')} className="cursor-pointer">
              <CardBody className="p-4 flex items-start gap-3">
                <div className="w-9 h-9 rounded-xl bg-[#F3EEFF] text-[#7950D9] flex items-center justify-center shrink-0">
                  <Bot className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-[#21152F] mb-0.5">M9 Recruiter AI Assistant</h4>
                  <p className="text-[11px] text-[#766A87]">
                    Ask natural language questions about applicants, compare finalists, and review pipeline statistics.
                  </p>
                </div>
              </CardBody>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
