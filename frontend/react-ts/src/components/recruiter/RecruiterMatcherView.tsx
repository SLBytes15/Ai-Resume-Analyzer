import React from 'react';
import { Search, Sparkles, AlertCircle, CheckCircle2, User } from 'lucide-react';
import { CandidateMatch } from '../../types';
import { Card, CardBody, CardHeader } from '../common/Card';
import { Button } from '../common/Button';

interface RecruiterMatcherViewProps {
  jdText: string;
  setJdText: (val: string) => void;
  onMatch: () => Promise<void>;
  matchLoading: boolean;
  matchError: string;
  matchCandidates: CandidateMatch[];
}

export function RecruiterMatcherView({
  jdText,
  setJdText,
  onMatch,
  matchLoading,
  matchError,
  matchCandidates,
}: RecruiterMatcherViewProps) {
  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h2 className="text-xl font-bold text-[#21152F] tracking-tight">Instant Semantic Candidate Matcher</h2>
        <p className="text-xs text-[#766A87]">
          Paste any job description or list of requirements to instantly rank candidates using RAG embeddings.
        </p>
      </div>

      <Card>
        <CardBody className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[#21152F] mb-1.5">
              Job Description / Requirements
            </label>
            <textarea
              rows={5}
              placeholder="Paste job description (e.g. Looking for a Senior Python Developer with 4+ years experience in FastAPI, PostgreSQL, Docker, and Microservices)..."
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              className="w-full p-3 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white leading-relaxed resize-none"
            />
          </div>

          <div className="flex items-center justify-between">
            <span className="text-[11px] text-[#766A87]">
              Compares vector embeddings against all uploaded candidate resumes.
            </span>
            <Button
              variant="primary"
              size="sm"
              onClick={onMatch}
              isLoading={matchLoading}
              disabled={!jdText.trim()}
              icon={<Sparkles className="w-4 h-4" />}
            >
              Match Candidates
            </Button>
          </div>

          {matchError && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs">
              {matchError}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Results */}
      {matchCandidates.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-sm font-bold text-[#21152F]">
            Ranked Candidate Matches ({matchCandidates.length})
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {matchCandidates.map((c, idx) => (
              <Card key={c.id} hoverEffect className="overflow-hidden">
                <CardBody className="p-5">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-full bg-[#F3EEFF] text-[#7950D9] font-bold text-xs flex items-center justify-center">
                        #{idx + 1}
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-[#21152F]">{c.name}</h4>
                        <span className="text-[11px] text-[#766A87]">{c.yoe_status}</span>
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="text-lg font-extrabold text-[#7950D9]">
                        {c.score}%
                      </div>
                      <span className="text-[10px] text-[#766A87]">Match Score</span>
                    </div>
                  </div>

                  {c.reasoning && (
                    <p className="text-xs text-[#21152F] bg-[#FAF9FD] p-3 rounded-xl border border-[#EAE5F2] mb-3">
                      "{c.reasoning}"
                    </p>
                  )}

                  <div className="space-y-1.5 text-xs">
                    {c.matched_skills && c.matched_skills.length > 0 && (
                      <div>
                        <span className="font-semibold text-emerald-700 block mb-1">Matched Skills:</span>
                        <div className="flex flex-wrap gap-1">
                          {c.matched_skills.map((s, sIdx) => (
                            <span key={sIdx} className="px-2 py-0.5 rounded text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-200">
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {c.missing_skills && c.missing_skills.length > 0 && (
                      <div className="pt-1">
                        <span className="font-semibold text-amber-700 block mb-1">Missing Skills:</span>
                        <div className="flex flex-wrap gap-1">
                          {c.missing_skills.map((s, sIdx) => (
                            <span key={sIdx} className="px-2 py-0.5 rounded text-[10px] bg-amber-50 text-amber-700 border border-amber-200">
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </CardBody>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
