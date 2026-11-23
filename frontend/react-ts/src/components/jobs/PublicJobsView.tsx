import React, { useState } from 'react';
import {
  Compass,
  Search,
  Building2,
  MapPin,
  Clock,
  DollarSign,
  Briefcase,
  CheckCircle2,
  AlertCircle,
  FileText,
  ArrowRight,
  Filter,
} from 'lucide-react';
import { PublicJob, ResumeItem } from '../../types';
import { Card, CardBody, CardHeader } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Modal } from '../common/Modal';

interface PublicJobsViewProps {
  jobs: PublicJob[];
  loading: boolean;
  keyword: string;
  setKeyword: (val: string) => void;
  location: string;
  setLocation: (val: string) => void;
  workplace: string;
  setWorkplace: (val: string) => void;
  employment: string;
  setEmployment: (val: string) => void;
  skill: string;
  setSkill: (val: string) => void;
  sort: 'newest' | 'oldest';
  setSort: (val: 'newest' | 'oldest') => void;
  onApplyClick: (job: PublicJob) => void;
  token: string;
  onOpenAuth: () => void;
}

export function PublicJobsView({
  jobs,
  loading,
  keyword,
  setKeyword,
  location,
  setLocation,
  workplace,
  setWorkplace,
  employment,
  setEmployment,
  skill,
  setSkill,
  sort,
  setSort,
  onApplyClick,
  token,
  onOpenAuth,
}: PublicJobsViewProps) {
  const [selectedJobForDetail, setSelectedJobForDetail] = useState<PublicJob | null>(null);

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Compass className="w-5 h-5 text-[#7950D9]" />
          <h2 className="text-2xl font-extrabold text-[#21152F] tracking-tight">
            Explore Open Positions
          </h2>
        </div>
        <p className="text-xs text-[#766A87]">
          Discover verified engineering roles across top teams. Applications permanently pin your submitted CV version.
        </p>
      </div>

      {/* Filter Bar */}
      <Card>
        <CardBody className="p-5 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 text-[#766A87] absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Title, department, keywords..."
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
              />
            </div>

            {/* Location Input */}
            <div className="relative">
              <MapPin className="w-4 h-4 text-[#766A87] absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Location (e.g. Bengaluru, Remote)..."
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
              />
            </div>

            {/* Skill Input */}
            <div className="relative">
              <Filter className="w-4 h-4 text-[#766A87] absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Required Skill (e.g. Python, FastAPI)..."
                value={skill}
                onChange={(e) => setSkill(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[#EAE5F2]">
            <div className="flex flex-wrap gap-2 text-xs">
              <select
                value={workplace}
                onChange={(e) => setWorkplace(e.target.value)}
                className="px-3 py-1.5 rounded-lg border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9]"
              >
                <option value="">All Workplaces</option>
                <option value="ONSITE">Onsite</option>
                <option value="REMOTE">Remote</option>
                <option value="HYBRID">Hybrid</option>
              </select>

              <select
                value={employment}
                onChange={(e) => setEmployment(e.target.value)}
                className="px-3 py-1.5 rounded-lg border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9]"
              >
                <option value="">All Employment Types</option>
                <option value="FULL_TIME">Full Time</option>
                <option value="PART_TIME">Part Time</option>
                <option value="CONTRACT">Contract</option>
                <option value="INTERNSHIP">Internship</option>
              </select>

              <select
                value={sort}
                onChange={(e) => setSort(e.target.value as any)}
                className="px-3 py-1.5 rounded-lg border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9]"
              >
                <option value="newest">Newest First</option>
                <option value="oldest">Oldest First</option>
              </select>
            </div>

            <span className="text-xs text-[#766A87]">
              Showing <strong className="text-[#21152F]">{jobs.length}</strong> open role(s)
            </span>
          </div>
        </CardBody>
      </Card>

      {/* Jobs Grid */}
      {jobs.length === 0 ? (
        <Card>
          <CardBody className="p-12 text-center text-xs text-[#766A87]">
            No published jobs match the specified criteria. Try clearing filters.
          </CardBody>
        </Card>
      ) : (
        <div className="space-y-4">
          {jobs.map((job) => (
            <Card key={job.id} hoverEffect className="overflow-hidden">
              <CardBody className="p-6">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div className="space-y-2 flex-1">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-base font-bold text-[#21152F]">{job.title}</h3>
                        <Badge variant="purple" size="sm">
                          {job.workplace_type}
                        </Badge>
                      </div>

                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-[#766A87]">
                        <span className="flex items-center gap-1 font-semibold text-[#21152F]">
                          <Building2 className="w-3.5 h-3.5 text-[#7950D9]" />
                          {job.organization_name}
                        </span>
                        {job.department && (
                          <span>Department: {job.department}</span>
                        )}
                        {job.location && (
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3.5 h-3.5" />
                            {job.location}
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
                    </div>

                    <p className="text-xs text-[#766A87] line-clamp-2 leading-relaxed">
                      {job.description}
                    </p>

                    {/* Required Skills */}
                    {job.required_skills && job.required_skills.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5 pt-1">
                        <span className="text-[11px] font-semibold text-[#766A87]">Required:</span>
                        {job.required_skills.map((s, sIdx) => (
                          <span
                            key={sIdx}
                            className="px-2 py-0.5 rounded text-[10px] font-medium bg-[#F3EEFF] text-[#7950D9] border border-[#E7DCFF]"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="flex flex-col sm:items-end justify-between gap-3 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-[#EAE5F2]">
                    <span className="text-[11px] text-[#766A87]">
                      Published on {new Date(job.published_at || job.created_at).toLocaleDateString()}
                    </span>

                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedJobForDetail(job)}
                      >
                        Details
                      </Button>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => {
                          if (!token) onOpenAuth();
                          else onApplyClick(job);
                        }}
                        icon={<ArrowRight className="w-3.5 h-3.5" />}
                      >
                        Apply Now
                      </Button>
                    </div>
                  </div>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      {/* Job Details Modal */}
      {selectedJobForDetail && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedJobForDetail(null)}
          title={selectedJobForDetail.title}
          description={`${selectedJobForDetail.organization_name} · ${selectedJobForDetail.workplace_type}`}
          maxWidth="2xl"
        >
          <div className="space-y-4 text-xs">
            <div className="p-3 bg-[#FAF9FD] rounded-xl border border-[#EAE5F2] grid grid-cols-2 gap-2 text-[#766A87]">
              <div>Location: <strong className="text-[#21152F]">{selectedJobForDetail.location || 'Remote'}</strong></div>
              <div>Type: <strong className="text-[#21152F]">{selectedJobForDetail.employment_type}</strong></div>
              <div>
                Experience: <strong className="text-[#21152F]">{selectedJobForDetail.experience_min || 0} - {selectedJobForDetail.experience_max || '+'} yrs</strong>
              </div>
              <div>
                Salary: <strong className="text-emerald-700">{selectedJobForDetail.salary_currency} {selectedJobForDetail.salary_min?.toLocaleString() || 'Competitive'}</strong>
              </div>
            </div>

            <div>
              <h4 className="font-bold text-[#21152F] mb-1">Description:</h4>
              <p className="text-[#766A87] leading-relaxed whitespace-pre-wrap">
                {selectedJobForDetail.description}
              </p>
            </div>

            {selectedJobForDetail.responsibilities && (
              <div>
                <h4 className="font-bold text-[#21152F] mb-1">Responsibilities:</h4>
                <p className="text-[#766A87] leading-relaxed whitespace-pre-wrap">
                  {selectedJobForDetail.responsibilities}
                </p>
              </div>
            )}

            {selectedJobForDetail.qualifications && (
              <div>
                <h4 className="font-bold text-[#21152F] mb-1">Qualifications:</h4>
                <p className="text-[#766A87] leading-relaxed whitespace-pre-wrap">
                  {selectedJobForDetail.qualifications}
                </p>
              </div>
            )}

            <div className="pt-3 border-t border-[#EAE5F2] flex items-center justify-end gap-2">
              <Button
                variant="primary"
                size="md"
                onClick={() => {
                  const targetJob = selectedJobForDetail;
                  setSelectedJobForDetail(null);
                  if (!token) onOpenAuth();
                  else onApplyClick(targetJob);
                }}
              >
                Apply to this Position
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
