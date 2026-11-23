import React from 'react';
import {
  Sparkles,
  FileText,
  Compass,
  FileCheck2,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  Briefcase,
} from 'lucide-react';
import { CandidateProfile, ResumeItem, CandidateApplication } from '../../types';
import { Card, CardBody } from '../common/Card';
import { Button } from '../common/Button';
import { Badge, StatusBadge } from '../common/Badge';

interface CandidateOverviewProps {
  profile: CandidateProfile | null;
  resumes: ResumeItem[];
  applications: CandidateApplication[];
  onNavigate: (tab: any) => void;
  onExploreJobs: () => void;
}

export function CandidateOverview({
  profile,
  resumes,
  applications,
  onNavigate,
  onExploreJobs,
}: CandidateOverviewProps) {
  const activeResume = resumes.find((r) => r.is_active);
  const completedResumes = resumes.filter((r) => r.parsing_status === 'COMPLETED');

  // Calculate profile completion percentage
  let completionPoints = 0;
  if (profile?.full_name) completionPoints += 25;
  if (profile?.headline) completionPoints += 25;
  if (profile?.phone && profile?.location) completionPoints += 25;
  if (activeResume) completionPoints += 25;

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="relative p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-[#43216F] via-[#513296] to-[#7950D9] text-white shadow-lg shadow-[#7950D9]/15 overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-96 bg-white/5 rounded-l-full blur-xl pointer-events-none" />
        <div className="relative z-10 max-w-2xl">
          <Badge variant="purple" className="bg-white/15 text-white border-white/20 mb-3">
            Candidate Workspace
          </Badge>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-2">
            Welcome back, {profile?.full_name || 'Candidate'}!
          </h2>
          <p className="text-purple-100 text-sm leading-relaxed mb-6">
            Track your job applications, analyze your resume against industry benchmarks, and explore
            new career possibilities with AI-driven insights.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={onExploreJobs}
              className="bg-white text-[#7950D9] hover:bg-[#F3EEFF] border-white font-semibold"
              icon={<Compass className="w-4 h-4" />}
            >
              Explore Opportunities
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onNavigate('intelligence')}
              className="text-white hover:bg-white/10"
              icon={<Sparkles className="w-4 h-4" />}
            >
              Run Resume Intelligence
            </Button>
          </div>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Profile Completion */}
        <Card hoverEffect onClick={() => onNavigate('profile')} className="cursor-pointer">
          <CardBody className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-[#766A87]">Profile Completion</span>
              <span className="text-xs font-bold text-[#7950D9]">{completionPoints}%</span>
            </div>
            <div className="w-full bg-[#EAE5F2] rounded-full h-2 mb-2 overflow-hidden">
              <div
                className="bg-[#7950D9] h-2 rounded-full transition-all duration-500"
                style={{ width: `${completionPoints}%` }}
              />
            </div>
            <p className="text-[11px] text-[#766A87]">
              {completionPoints === 100 ? 'Profile fully completed' : 'Complete profile to boost match rate'}
            </p>
          </CardBody>
        </Card>

        {/* Active Resume */}
        <Card hoverEffect onClick={() => onNavigate('resumes')} className="cursor-pointer">
          <CardBody className="p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-[#766A87]">Active Resume</span>
              <FileText className="w-4 h-4 text-[#7950D9]" />
            </div>
            <div className="text-sm font-bold text-[#21152F] truncate mb-1">
              {activeResume ? activeResume.original_filename : 'No resume uploaded'}
            </div>
            <p className="text-[11px] text-[#766A87]">
              {activeResume ? `${resumes.length} total version(s)` : 'Upload a PDF to apply to jobs'}
            </p>
          </CardBody>
        </Card>

        {/* Applications */}
        <Card hoverEffect onClick={() => onNavigate('applications')} className="cursor-pointer">
          <CardBody className="p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-[#766A87]">My Applications</span>
              <FileCheck2 className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="text-2xl font-extrabold text-[#21152F] mb-1">
              {applications.length}
            </div>
            <p className="text-[11px] text-[#766A87]">
              {applications.filter((a) => a.status === 'INTERVIEWING' || a.status === 'SHORTLISTED').length} active in pipeline
            </p>
          </CardBody>
        </Card>

        {/* Career Assistant */}
        <Card hoverEffect onClick={() => onNavigate('career-assistant')} className="cursor-pointer">
          <CardBody className="p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-[#766A87]">Career Assistant</span>
              <Sparkles className="w-4 h-4 text-[#7950D9]" />
            </div>
            <div className="text-sm font-bold text-[#21152F] mb-1">AI Career Guidance</div>
            <p className="text-[11px] text-[#7950D9] font-medium flex items-center gap-1">
              Chat with AI Mentor <ArrowRight className="w-3 h-3" />
            </p>
          </CardBody>
        </Card>
      </div>

      {/* Two Column Layout: Recent Applications & Recommended Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Recent Applications */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-[#21152F]">Recent Applications</h3>
            <button
              onClick={() => onNavigate('applications')}
              className="text-xs font-semibold text-[#7950D9] hover:underline"
            >
              View All ({applications.length})
            </button>
          </div>

          {applications.length === 0 ? (
            <Card>
              <CardBody className="p-8 text-center text-xs text-[#766A87]">
                You haven't submitted any applications yet.
                <div className="mt-3">
                  <Button variant="secondary" size="sm" onClick={onExploreJobs}>
                    Browse Open Jobs
                  </Button>
                </div>
              </CardBody>
            </Card>
          ) : (
            <div className="space-y-3">
              {applications.slice(0, 3).map((app) => (
                <Card key={app.id} hoverEffect className="overflow-hidden">
                  <CardBody className="p-4 flex items-center justify-between gap-4">
                    <div>
                      <h4 className="text-sm font-bold text-[#21152F]">{app.job_title}</h4>
                      <p className="text-xs text-[#766A87]">
                        {app.organization_name} · Applied on {new Date(app.submitted_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <StatusBadge status={app.status} />
                    </div>
                  </CardBody>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Career Acceleration Card */}
        <div className="space-y-4">
          <h3 className="text-base font-bold text-[#21152F]">Resume Quick Health</h3>
          <Card className="bg-[#FAF9FD] border-[#EAE5F2]">
            <CardBody className="p-5 space-y-3 text-xs">
              <div className="flex items-center gap-2 font-semibold text-[#21152F]">
                <Sparkles className="w-4 h-4 text-[#7950D9]" />
                <span>Resume Intelligence Checks</span>
              </div>
              <p className="text-[#766A87] leading-relaxed">
                Make sure your resume contains quantified achievements, clear employment dates, and standard section headings.
              </p>
              <div className="pt-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => onNavigate('intelligence')}
                  className="w-full justify-center"
                >
                  Analyze My Resume
                </Button>
              </div>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}
