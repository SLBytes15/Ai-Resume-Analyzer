import React, { useState } from 'react';
import {
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Info,
  RotateCw,
  Target,
  FileText,
  Layers,
  Award,
  ChevronRight,
  TrendingUp,
} from 'lucide-react';
import { ResumeItem, ResumeAnalysis, ResumeAnalysisListItem } from '../../types';
import { Card, CardHeader, CardBody } from '../common/Card';
import { Button } from '../common/Button';
import { Badge, StatusBadge } from '../common/Badge';

interface CandidateIntelligenceViewProps {
  resumes: ResumeItem[];
  selectedResumeId: string;
  setSelectedResumeId: (id: string) => void;
  targetRole: string;
  setTargetRole: (role: string) => void;
  currentAnalysis: ResumeAnalysis | null;
  analysesList: ResumeAnalysisListItem[];
  analysisLoading: boolean;
  analysesListLoading: boolean;
  analysisError: string;
  onTriggerAnalysis: () => Promise<void>;
  onSelectAnalysis: (analysisId: string) => Promise<void>;
  onRetryAnalysis: (analysisId: string) => Promise<void>;
  retryingId: string | null;
}

export function CandidateIntelligenceView({
  resumes,
  selectedResumeId,
  setSelectedResumeId,
  targetRole,
  setTargetRole,
  currentAnalysis,
  analysesList,
  analysisLoading,
  analysesListLoading,
  analysisError,
  onTriggerAnalysis,
  onSelectAnalysis,
  onRetryAnalysis,
  retryingId,
}: CandidateIntelligenceViewProps) {
  const activeResume = resumes.find((r) => r.is_active);

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Sparkles className="w-5 h-5 text-[#7950D9]" />
          <h2 className="text-xl font-bold text-[#21152F] tracking-tight">
            Resume Intelligence & Career Guidance
          </h2>
        </div>
        <p className="text-xs text-[#766A87]">
          Deterministic structure audit combined with grounded AI career guidance to help you stand out.
        </p>
      </div>

      {/* Trigger Analysis Form Card */}
      <Card>
        <CardBody className="p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Select Resume */}
            <div>
              <label className="block text-xs font-semibold text-[#21152F] mb-1.5">
                Select Resume Version
              </label>
              <select
                value={selectedResumeId}
                onChange={(e) => setSelectedResumeId(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
              >
                <option value="">-- Choose a resume to analyze --</option>
                {resumes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.original_filename} {r.is_active ? '(Active Default)' : ''}
                  </option>
                ))}
              </select>
            </div>

            {/* Target Role Input */}
            <div>
              <label className="block text-xs font-semibold text-[#21152F] mb-1.5">
                Target Role (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. Staff Backend Engineer, ML Platform Lead"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            <span className="text-[11px] text-[#766A87]">
              Combines deterministic text quality checks with LLM qualitative advisory evaluation.
            </span>
            <Button
              variant="primary"
              size="sm"
              onClick={onTriggerAnalysis}
              isLoading={analysisLoading}
              disabled={!selectedResumeId}
              icon={<Sparkles className="w-4 h-4" />}
            >
              Analyze Resume
            </Button>
          </div>

          {analysisError && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs">
              {analysisError}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Main Analysis Display */}
      {currentAnalysis && (
        <div className="space-y-6 animate-in fade-in duration-200">
          {/* Status & Overview Bar */}
          <Card className="bg-gradient-to-r from-white to-[#F3EEFF]/40">
            <CardBody className="p-6">
              <div className="flex flex-wrap items-center justify-between gap-4 mb-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-base font-bold text-[#21152F]">
                      Analysis Report {currentAnalysis.target_role ? `for ${currentAnalysis.target_role}` : ''}
                    </h3>
                    <StatusBadge status={currentAnalysis.status} />
                  </div>
                  <p className="text-xs text-[#766A87]">
                    Generated on {new Date(currentAnalysis.created_at).toLocaleString()}
                  </p>
                </div>

                {currentAnalysis.status === 'FAILED' && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onRetryAnalysis(currentAnalysis.id)}
                    isLoading={retryingId === currentAnalysis.id}
                    icon={<RotateCw className="w-3.5 h-3.5" />}
                  >
                    Retry Analysis
                  </Button>
                )}
              </div>

              {currentAnalysis.analysis_data?.overall_summary && (
                <div className="p-4 bg-white rounded-xl border border-[#EAE5F2] text-xs text-[#21152F] leading-relaxed">
                  <span className="font-bold text-[#7950D9] block mb-1">Advisory Summary:</span>
                  {currentAnalysis.analysis_data.overall_summary}
                </div>
              )}
            </CardBody>
          </Card>

          {/* Deterministic Quality Checks Grid */}
          {currentAnalysis.deterministic_checks && (
            <div>
              <h4 className="text-sm font-bold text-[#21152F] mb-3 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Deterministic Structure & Quality Audit</span>
              </h4>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                <div className="p-3 bg-white rounded-xl border border-[#EAE5F2] text-center">
                  <div className="text-xs text-[#766A87]">Word Count</div>
                  <div className="text-lg font-extrabold text-[#21152F]">
                    {currentAnalysis.deterministic_checks.word_count}
                  </div>
                </div>
                <div className="p-3 bg-white rounded-xl border border-[#EAE5F2] text-center">
                  <div className="text-xs text-[#766A87]">Sections Found</div>
                  <div className="text-lg font-extrabold text-[#7950D9]">
                    {currentAnalysis.deterministic_checks.sections_detected.length}
                  </div>
                </div>
                <div className="p-3 bg-white rounded-xl border border-[#EAE5F2] text-center">
                  <div className="text-xs text-[#766A87]">Missing Sections</div>
                  <div className="text-lg font-extrabold text-amber-600">
                    {currentAnalysis.deterministic_checks.missing_sections.length}
                  </div>
                </div>
                <div className="p-3 bg-white rounded-xl border border-[#EAE5F2] text-center">
                  <div className="text-xs text-[#766A87]">Quantified Metrics</div>
                  <div className="text-lg font-extrabold text-emerald-600">
                    {currentAnalysis.deterministic_checks.measurable_outcomes?.metrics_count || 0}
                  </div>
                </div>
              </div>

              {/* Findings */}
              {currentAnalysis.deterministic_checks.findings && currentAnalysis.deterministic_checks.findings.length > 0 && (
                <Card>
                  <CardBody className="p-4 space-y-2">
                    <span className="text-xs font-bold text-[#21152F] block">Findings & Feedback:</span>
                    {currentAnalysis.deterministic_checks.findings.map((finding, fIdx) => (
                      <div
                        key={fIdx}
                        className={`p-2.5 rounded-lg text-xs flex items-start gap-2.5 ${
                          finding.level === 'WARNING'
                            ? 'bg-amber-50 text-amber-900 border border-amber-200'
                            : 'bg-[#FAF9FD] text-[#21152F] border border-[#EAE5F2]'
                        }`}
                      >
                        {finding.level === 'WARNING' ? (
                          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                        ) : (
                          <Info className="w-4 h-4 text-[#7950D9] shrink-0 mt-0.5" />
                        )}
                        <span>{finding.message}</span>
                      </div>
                    ))}
                  </CardBody>
                </Card>
              )}
            </div>
          )}

          {/* Qualitative LLM Insights (Strengths, Priorities, Alignment) */}
          {currentAnalysis.analysis_data && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Strengths */}
              <Card>
                <CardHeader>
                  <h4 className="text-xs font-bold text-[#21152F] flex items-center gap-2">
                    <Award className="w-4 h-4 text-emerald-600" />
                    <span>Demonstrated Strengths</span>
                  </h4>
                </CardHeader>
                <CardBody className="p-5 space-y-3">
                  {currentAnalysis.analysis_data.strengths.length === 0 ? (
                    <p className="text-xs text-[#766A87]">No specific strengths extracted.</p>
                  ) : (
                    currentAnalysis.analysis_data.strengths.map((s, idx) => (
                      <div key={idx} className="p-3 rounded-xl bg-[#FAF9FD] border border-[#EAE5F2] text-xs">
                        <strong className="text-[#21152F] block mb-1">{s.title}</strong>
                        <p className="text-[#766A87] leading-relaxed mb-2">{s.description}</p>
                        {s.supporting_evidence && s.supporting_evidence.length > 0 && (
                          <div className="text-[11px] text-[#7950D9] bg-[#F3EEFF] p-2 rounded-lg">
                            Evidence: "{s.supporting_evidence[0]}"
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </CardBody>
              </Card>

              {/* Improvement Priorities */}
              <Card>
                <CardHeader>
                  <h4 className="text-xs font-bold text-[#21152F] flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-[#7950D9]" />
                    <span>Improvement Priorities</span>
                  </h4>
                </CardHeader>
                <CardBody className="p-5 space-y-3">
                  {currentAnalysis.analysis_data.improvement_priorities.length === 0 ? (
                    <p className="text-xs text-[#766A87]">No high-priority improvements identified.</p>
                  ) : (
                    currentAnalysis.analysis_data.improvement_priorities.map((item, idx) => (
                      <div key={idx} className="p-3 rounded-xl bg-[#FAF9FD] border border-[#EAE5F2] text-xs">
                        <div className="flex items-center justify-between mb-1">
                          <strong className="text-[#21152F]">{item.issue}</strong>
                          <Badge variant={item.priority === 'HIGH' ? 'danger' : 'warning'} size="sm">
                            {item.priority}
                          </Badge>
                        </div>
                        <p className="text-[#766A87] mb-2">{item.why_it_matters}</p>
                        <div className="p-2 bg-white rounded-lg border border-[#EAE5F2] text-[11px] text-[#21152F]">
                          Action: {item.suggested_action}
                        </div>
                      </div>
                    ))
                  )}
                </CardBody>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* Historical Analyses List */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-[#21152F]">Previous Analysis Reports</h3>
        {analysesList.length === 0 ? (
          <p className="text-xs text-[#766A87]">No previous analysis history recorded for this resume.</p>
        ) : (
          <div className="space-y-2">
            {analysesList.map((item) => (
              <div
                key={item.id}
                onClick={() => onSelectAnalysis(item.id)}
                className="p-3.5 bg-white border border-[#EAE5F2] hover:border-[#7950D9] rounded-xl flex items-center justify-between cursor-pointer transition-all hover:shadow-xs"
              >
                <div>
                  <span className="text-xs font-bold text-[#21152F]">
                    {item.target_role ? `Target: ${item.target_role}` : 'General Career Audit'}
                  </span>
                  <span className="text-[11px] text-[#766A87] ml-3">
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={item.status} />
                  <ChevronRight className="w-4 h-4 text-[#766A87]" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
