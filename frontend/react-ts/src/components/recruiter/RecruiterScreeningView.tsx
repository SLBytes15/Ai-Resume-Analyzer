import React, { useState } from 'react';
import {
  Sparkles,
  Target,
  Brain,
  CheckCircle2,
  AlertCircle,
  RotateCw,
  ChevronDown,
  ChevronUp,
  FileText,
  Award,
  Layers,
  ArrowRight,
} from 'lucide-react';
import {
  ScreeningRun,
  ScreeningResultItem,
  ScreeningResultDetail,
  RecruiterJob,
  Organization,
} from '../../types';
import { Card, CardHeader, CardBody } from '../common/Card';
import { Button } from '../common/Button';
import { Badge, StatusBadge } from '../common/Badge';
import { Modal } from '../common/Modal';

interface RecruiterScreeningViewProps {
  jobs: RecruiterJob[];
  selectedJobId: string;
  setSelectedJobId: (id: string) => void;
  screeningRuns: ScreeningRun[];
  runsLoading: boolean;
  selectedRunId: string;
  setSelectedRunId: (id: string) => void;
  results: ScreeningResultItem[];
  resultsLoading: boolean;
  scoreFilter: string;
  setScoreFilter: (val: string) => void;
  keyword: string;
  setKeyword: (val: string) => void;
  onTriggerScreening: (jobId: string) => Promise<void>;
  triggerLoading: boolean;
  triggerError: string;
  onViewResultDetail: (resultId: string) => Promise<void>;
  selectedResultDetail: ScreeningResultDetail | null;
  isResultModalOpen: boolean;
  setIsResultModalOpen: (open: boolean) => void;
  onRetryInsight: (resultId: string) => Promise<void>;
  retryingInsight: boolean;
  activeOrg?: Organization;
}

export function RecruiterScreeningView({
  jobs,
  selectedJobId,
  setSelectedJobId,
  screeningRuns,
  runsLoading,
  selectedRunId,
  setSelectedRunId,
  results,
  resultsLoading,
  scoreFilter,
  setScoreFilter,
  keyword,
  setKeyword,
  onTriggerScreening,
  triggerLoading,
  triggerError,
  onViewResultDetail,
  selectedResultDetail,
  isResultModalOpen,
  setIsResultModalOpen,
  onRetryInsight,
  retryingInsight,
  activeOrg,
}: RecruiterScreeningViewProps) {
  const isRecruiterOrAbove = activeOrg?.role && ['OWNER', 'ADMIN', 'RECRUITER'].includes(activeOrg.role);

  const selectedJob = jobs.find((j) => j.id === selectedJobId);
  const selectedRun = screeningRuns.find((r) => r.id === selectedRunId);

  const filteredResults = results.filter((res) => {
    const matchName =
      !keyword ||
      (res.candidate_name && res.candidate_name.toLowerCase().includes(keyword.toLowerCase())) ||
      (res.candidate_headline && res.candidate_headline.toLowerCase().includes(keyword.toLowerCase()));

    let matchScore = true;
    if (scoreFilter === '80+') matchScore = (res.total_score || 0) >= 80;
    else if (scoreFilter === '60-79') matchScore = (res.total_score || 0) >= 60 && (res.total_score || 0) < 80;
    else if (scoreFilter === '<60') matchScore = (res.total_score || 0) < 60;

    return matchName && matchScore;
  });

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Title & Trigger Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-5 h-5 text-[#7950D9]" />
            <h2 className="text-xl font-bold text-[#21152F] tracking-tight">
              AI Candidate Screening Engine (M6)
            </h2>
          </div>
          <p className="text-xs text-[#766A87]">
            Deterministic scoring (60% Req Skills / 15% Pref Skills / 25% Experience) with explainable Candidate Insights.
          </p>
        </div>

        {isRecruiterOrAbove && selectedJobId && (
          <Button
            variant="primary"
            size="sm"
            onClick={() => onTriggerScreening(selectedJobId)}
            isLoading={triggerLoading}
            icon={<Sparkles className="w-4 h-4" />}
          >
            Run Screening on {selectedJob?.title || 'Job'}
          </Button>
        )}
      </div>

      {triggerError && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs">
          {triggerError}
        </div>
      )}

      {/* Select Job & Screening Run Controls */}
      <Card>
        <CardBody className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Job Requisition */}
          <div>
            <label className="block text-[11px] font-semibold text-[#21152F] mb-1">
              Select Position to Screen
            </label>
            <select
              value={selectedJobId}
              onChange={(e) => {
                setSelectedJobId(e.target.value);
                setSelectedRunId('');
              }}
              className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
            >
              <option value="">-- Choose Position --</option>
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title} ({j.status})
                </option>
              ))}
            </select>
          </div>

          {/* Screening Run */}
          <div>
            <label className="block text-[11px] font-semibold text-[#21152F] mb-1">
              Screening Run History
            </label>
            <select
              value={selectedRunId}
              onChange={(e) => setSelectedRunId(e.target.value)}
              disabled={screeningRuns.length === 0}
              className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white disabled:opacity-50"
            >
              <option value="">
                {screeningRuns.length === 0
                  ? 'No runs found'
                  : '-- Select Screening Run --'}
              </option>
              {screeningRuns.map((r, idx) => (
                <option key={r.id} value={r.id}>
                  Run #{screeningRuns.length - idx}: {new Date(r.created_at).toLocaleDateString()} ({r.status})
                </option>
              ))}
            </select>
          </div>

          {/* Search Candidate */}
          <div>
            <label className="block text-[11px] font-semibold text-[#21152F] mb-1">
              Search Candidate
            </label>
            <input
              type="text"
              placeholder="Candidate name or headline..."
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
            />
          </div>

          {/* Score Filter */}
          <div>
            <label className="block text-[11px] font-semibold text-[#21152F] mb-1">
              Score Filter
            </label>
            <select
              value={scoreFilter}
              onChange={(e) => setScoreFilter(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
            >
              <option value="">All Scores</option>
              <option value="80+">Top Matches (80%+)</option>
              <option value="60-79">Qualified (60% - 79%)</option>
              <option value="<60">Below 60%</option>
            </select>
          </div>
        </CardBody>
      </Card>

      {/* Run Summary Card if selected */}
      {selectedRun && (
        <Card className="bg-gradient-to-r from-white to-[#F3EEFF]/40">
          <CardBody className="p-5 flex flex-wrap items-center justify-between gap-4 text-xs">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="font-bold text-[#21152F]">
                  Screening Run for {selectedJob?.title}
                </span>
                <StatusBadge status={selectedRun.status} />
              </div>
              <p className="text-[#766A87]">
                Evaluated on {new Date(selectedRun.created_at).toLocaleString()}
              </p>
            </div>

            <div className="flex items-center gap-6 text-[#766A87]">
              <div>Total Evaluated: <strong className="text-[#21152F]">{selectedRun.total_applications}</strong></div>
              <div>Processed: <strong className="text-emerald-700">{selectedRun.processed_applications}</strong></div>
              <div>Failed: <strong className="text-rose-600">{selectedRun.failed_applications}</strong></div>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Screening Results Cards Grid */}
      <div className="space-y-4">
        {!selectedJobId ? (
          <Card>
            <CardBody className="p-12 text-center text-xs text-[#766A87]">
              Select a position above to view or run AI candidate screenings.
            </CardBody>
          </Card>
        ) : filteredResults.length === 0 ? (
          <Card>
            <CardBody className="p-12 text-center text-xs text-[#766A87]">
              {results.length === 0 ? (
                <div>
                  <p className="mb-3">No candidate screening results for this run.</p>
                  {isRecruiterOrAbove && (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => onTriggerScreening(selectedJobId)}
                      isLoading={triggerLoading}
                    >
                      Trigger New Screening Run
                    </Button>
                  )}
                </div>
              ) : (
                'No candidates match the score or keyword filters.'
              )}
            </CardBody>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredResults.map((item, idx) => (
              <Card key={item.id} hoverEffect className="flex flex-col justify-between overflow-hidden">
                <CardBody className="p-5">
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div>
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="w-5 h-5 rounded-full bg-[#FAF9FD] text-[#7950D9] border border-[#EAE5F2] font-bold text-[10px] flex items-center justify-center">
                          #{idx + 1}
                        </span>
                        <h4 className="text-sm font-bold text-[#21152F]">
                          {item.candidate_name || 'Candidate'}
                        </h4>
                      </div>
                      <p className="text-xs text-[#766A87] line-clamp-1">
                        {item.candidate_headline || item.candidate_email}
                      </p>
                    </div>

                    <div className="text-right">
                      <div className="text-xl font-extrabold text-[#7950D9]">
                        {item.total_score !== null && item.total_score !== undefined
                          ? item.total_score.toFixed(1)
                          : '—'}
                        <span className="text-xs font-normal text-[#766A87]">/100</span>
                      </div>
                      <span className="text-[10px] text-[#766A87]">
                        Confidence: {item.confidence_level || 'N/A'}
                      </span>
                    </div>
                  </div>

                  {/* Score Breakdown Bars */}
                  <div className="space-y-1.5 p-3 rounded-xl bg-[#FAF9FD] border border-[#EAE5F2] text-[11px] mb-3">
                    <div className="flex justify-between text-[#766A87]">
                      <span>Required Skills (60%):</span>
                      <strong className="text-[#21152F]">{item.required_skill_score || 0}%</strong>
                    </div>
                    <div className="flex justify-between text-[#766A87]">
                      <span>Preferred Skills (15%):</span>
                      <strong className="text-[#21152F]">{item.preferred_skill_score || 0}%</strong>
                    </div>
                    <div className="flex justify-between text-[#766A87]">
                      <span>Experience (25%):</span>
                      <strong className="text-[#21152F]">{item.experience_score || 0}%</strong>
                    </div>
                  </div>

                  {/* Insight Summary Pill */}
                  {item.insight_summary && (
                    <div className="p-2.5 rounded-lg bg-[#F3EEFF]/50 border border-[#E7DCFF] text-[11px] text-[#21152F] mb-3 leading-relaxed">
                      <span className="font-semibold text-[#7950D9] block mb-0.5">AI Recruiter Insight:</span>
                      "{item.insight_summary}"
                    </div>
                  )}

                  {/* Actions */}
                  <div className="pt-2 border-t border-[#EAE5F2] flex items-center justify-between">
                    <span className="text-[11px] text-[#766A87]">
                      {item.matched_skills_count} skills matched
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onViewResultDetail(item.id)}
                      icon={<Brain className="w-3.5 h-3.5 text-[#7950D9]" />}
                    >
                      Inspect Evidence & Insight
                    </Button>
                  </div>
                </CardBody>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Screening Result & Insight Detail Modal */}
      {selectedResultDetail && (
        <Modal
          isOpen={isResultModalOpen}
          onClose={() => setIsResultModalOpen(false)}
          title={`Screening Assessment: ${selectedResultDetail.candidate_name || 'Candidate'}`}
          description={`Comprehensive evidence extraction and explainability breakdown`}
          maxWidth="3xl"
        >
          <div className="space-y-6 text-xs">
            {/* Score Banner */}
            <div className="p-4 bg-gradient-to-r from-[#FAF9FD] to-[#F3EEFF] rounded-2xl border border-[#EAE5F2] flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="text-[11px] font-semibold text-[#766A87]">Total Screening Score</span>
                <div className="text-3xl font-extrabold text-[#7950D9]">
                  {selectedResultDetail.total_score != null ? selectedResultDetail.total_score.toFixed(1) : '—'}{' '}
                  <span className="text-xs font-normal text-[#766A87]">/ 100</span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <span className="text-[#766A87] block">Required Skills</span>
                  <strong className="text-[#21152F] text-sm">{selectedResultDetail.required_skill_score || 0}%</strong>
                </div>
                <div>
                  <span className="text-[#766A87] block">Preferred Skills</span>
                  <strong className="text-[#21152F] text-sm">{selectedResultDetail.preferred_skill_score || 0}%</strong>
                </div>
                <div>
                  <span className="text-[#766A87] block">Experience</span>
                  <strong className="text-[#21152F] text-sm">{selectedResultDetail.experience_score || 0}%</strong>
                </div>
              </div>
            </div>

            {/* Explanation */}
            <div>
              <h4 className="font-bold text-[#21152F] mb-1">Deterministic Formula Explanation:</h4>
              <p className="p-3 bg-[#FAF9FD] rounded-xl border border-[#EAE5F2] text-[#21152F] leading-relaxed">
                {selectedResultDetail.explanation}
              </p>
            </div>

            {/* Matched Required Skills */}
            <div>
              <h4 className="font-bold text-[#21152F] mb-2">Matched Required Skills:</h4>
              {selectedResultDetail.matched_skills && selectedResultDetail.matched_skills.length > 0 ? (
                <div className="space-y-2">
                  {selectedResultDetail.matched_skills.map((skill, sIdx) => (
                    <div key={sIdx} className="p-3 bg-white rounded-xl border border-[#EAE5F2]">
                      <div className="flex items-center justify-between mb-1">
                        <strong className="text-[#7950D9]">{skill.skill}</strong>
                        <span className="text-[10px] text-emerald-600 font-semibold">Confidence: {(skill.confidence || 1) * 100}%</span>
                      </div>
                      <p className="text-[#766A87] italic">Evidence: "{skill.evidence}"</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[#766A87]">No required skills evidenced.</p>
              )}
            </div>

            {/* Missing Evidence */}
            {selectedResultDetail.missing_evidence && selectedResultDetail.missing_evidence.length > 0 && (
              <div>
                <h4 className="font-bold text-amber-800 mb-2">Missing or Unverified Requirements:</h4>
                <div className="space-y-1.5">
                  {selectedResultDetail.missing_evidence.map((m, mIdx) => (
                    <div key={mIdx} className="p-2.5 bg-amber-50 rounded-xl border border-amber-200 text-amber-900 flex items-center justify-between">
                      <strong>{m.skill}</strong>
                      <span className="text-[10px] text-amber-700">{m.reason}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Candidate Insight Generator Section */}
            {selectedResultDetail.insight?.insight_data ? (
              <div className="p-4 bg-[#F3EEFF]/40 rounded-2xl border border-[#E7DCFF] space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-[#7950D9] flex items-center gap-1.5">
                    <Brain className="w-4 h-4" />
                    <span>Candidate Insight Generator (Why this score?)</span>
                  </h4>
                  <Badge variant="purple" size="sm">Evidence Grounded</Badge>
                </div>

                <p className="text-[#21152F] font-medium leading-relaxed bg-white p-3 rounded-xl border border-[#EAE5F2]">
                  {selectedResultDetail.insight.insight_data.summary}
                </p>

                {/* Key Strengths */}
                {selectedResultDetail.insight.insight_data.key_strengths && selectedResultDetail.insight.insight_data.key_strengths.length > 0 && (
                  <div>
                    <span className="font-bold text-[#21152F] block mb-2">Validated Strengths:</span>
                    <div className="space-y-2">
                      {selectedResultDetail.insight.insight_data.key_strengths.map((str, strIdx) => (
                        <div key={strIdx} className="p-3 bg-white rounded-xl border border-[#EAE5F2]">
                          <strong className="text-[#21152F] block mb-0.5">{str.title}</strong>
                          <p className="text-[#766A87] mb-1.5">{str.description}</p>
                          {str.supporting_evidence && str.supporting_evidence.length > 0 && (
                            <span className="text-[10px] text-[#7950D9] bg-[#F3EEFF] px-2 py-0.5 rounded">
                              Citation: "{str.supporting_evidence[0]}"
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-4 bg-[#FAF9FD] rounded-xl border border-[#EAE5F2] text-center">
                <p className="text-[#766A87] mb-2">No AI candidate insight generated for this record.</p>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => onRetryInsight(selectedResultDetail.id)}
                  isLoading={retryingInsight}
                  icon={<RotateCw className="w-3.5 h-3.5" />}
                >
                  Generate Candidate Insight
                </Button>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
