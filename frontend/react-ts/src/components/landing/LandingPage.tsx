import React from 'react';
import {
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Zap,
  Target,
  FileText,
  Users,
  Brain,
  CheckCircle2,
  TrendingUp,
  Search,
  MessageSquare,
  BarChart3,
  Compass,
  Briefcase,
} from 'lucide-react';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';

interface LandingPageProps {
  onExploreJobs: () => void;
  onOpenRecruiter: () => void;
  onOpenCandidate: () => void;
  onGetStarted: () => void;
}

export function LandingPage({
  onExploreJobs,
  onOpenRecruiter,
  onOpenCandidate,
  onGetStarted,
}: LandingPageProps) {
  return (
    <div className="flex flex-col min-h-screen bg-[#FAF9FD]">
      {/* HERO SECTION */}
      <section className="relative pt-16 pb-24 px-4 sm:px-6 lg:px-8 overflow-hidden">
        {/* Subtle background glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[450px] bg-gradient-to-b from-[#F3EEFF]/80 via-[#F3EEFF]/40 to-transparent blur-3xl pointer-events-none -z-10" />

        <div className="max-w-5xl mx-auto text-center">
          {/* Eyebrow Pill */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#F3EEFF] border border-[#E7DCFF] text-[#7950D9] text-xs font-semibold mb-6 shadow-xs animate-in fade-in duration-300">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Next-Generation AI Recruitment & Career Intelligence</span>
          </div>

          {/* Headline */}
          <h1 className="text-4xl sm:text-6xl font-extrabold text-[#21152F] tracking-tight leading-[1.12] mb-6">
            Where Talent Meets{' '}
            <span className="bg-gradient-to-r from-[#7950D9] via-[#935EF8] to-[#43216F] bg-clip-text text-transparent">
              Intelligent Hiring.
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-lg sm:text-xl text-[#766A87] max-w-2xl mx-auto leading-relaxed mb-10">
            Discover opportunities, understand your potential, and make smarter hiring decisions
            with AI-powered recruitment intelligence.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
            <Button
              variant="primary"
              size="lg"
              onClick={onExploreJobs}
              icon={<Compass className="w-5 h-5" />}
              className="w-full sm:w-auto shadow-md shadow-[#7950D9]/25 hover:shadow-lg"
            >
              Explore Opportunities
            </Button>
            <Button
              variant="secondary"
              size="lg"
              onClick={onOpenRecruiter}
              icon={<ArrowRight className="w-5 h-5 text-[#7950D9]" />}
              className="w-full sm:w-auto"
            >
              Explore Recruiter Workspace
            </Button>
          </div>

          {/* Hero Visual: SaaS Interactive Dashboard Preview */}
          <div className="relative mx-auto max-w-4xl rounded-2xl p-2 sm:p-3 bg-gradient-to-b from-[#E7DCFF] via-white to-[#FAF9FD] border border-[#EAE5F2] shadow-2xl shadow-[#7950D9]/10">
            <div className="rounded-xl bg-white border border-[#EAE5F2] p-5 sm:p-7 text-left overflow-hidden">
              {/* Fake Window Controls */}
              <div className="flex items-center justify-between pb-4 mb-6 border-b border-[#EAE5F2]">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-rose-400" />
                  <div className="w-3 h-3 rounded-full bg-amber-400" />
                  <div className="w-3 h-3 rounded-full bg-emerald-400" />
                  <span className="ml-2 text-xs font-medium text-[#766A87]">
                    TalentLens Screening & Evidence Engine
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="purple" size="sm" dot>Live Evaluation</Badge>
                </div>
              </div>

              {/* Mock Dashboard Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                {/* Card 1: Score & Match */}
                <div className="p-4 rounded-xl bg-[#FAF9FD] border border-[#EAE5F2]">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-[#766A87]">Deterministic Score</span>
                    <Badge variant="success" size="sm">92% Match</Badge>
                  </div>
                  <div className="text-3xl font-extrabold text-[#21152F] mb-1">92.0 <span className="text-xs text-[#766A87] font-normal">/ 100</span></div>
                  <p className="text-xs text-[#766A87]">
                    60% Req Skills (100%) + 15% Pref Skills (100%) + 25% Experience (68%)
                  </p>
                  <div className="w-full bg-[#EAE5F2] rounded-full h-2 mt-3 overflow-hidden">
                    <div className="bg-[#7950D9] h-2 rounded-full w-[92%]" />
                  </div>
                </div>

                {/* Card 2: Grounded Skills Evidenced */}
                <div className="p-4 rounded-xl bg-[#FAF9FD] border border-[#EAE5F2]">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-[#766A87]">Matched Skills</span>
                    <span className="text-xs text-emerald-600 font-semibold">4 Verified</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                      Python (4 yrs)
                    </span>
                    <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                      FastAPI (3 yrs)
                    </span>
                    <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                      PostgreSQL
                    </span>
                    <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                      Docker
                    </span>
                  </div>
                  <p className="text-[11px] text-[#766A87] mt-3">
                    Verified through project and employment evidence snippets.
                  </p>
                </div>

                {/* Card 3: AI Recruiter Insight */}
                <div className="p-4 rounded-xl bg-[#FAF9FD] border border-[#EAE5F2]">
                  <div className="flex items-center gap-1.5 mb-2">
                    <Sparkles className="w-3.5 h-3.5 text-[#7950D9]" />
                    <span className="text-xs font-semibold text-[#21152F]">Candidate Insight</span>
                  </div>
                  <p className="text-xs text-[#21152F] leading-snug line-clamp-3">
                    "Candidate demonstrates strong backend microservice design with extensive FastAPI experience. Documented 4 years at CloudTech building high-throughput APIs."
                  </p>
                  <div className="mt-3 pt-2 border-t border-[#EAE5F2] flex items-center justify-between text-[11px]">
                    <span className="text-[#766A87]">Explainability</span>
                    <span className="text-[#7950D9] font-medium">100% Grounded</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* PLATFORM CAPABILITIES */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 border-y border-[#EAE5F2] bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <Badge variant="purple" className="mb-3">Core Platform Capabilities</Badge>
            <h2 className="text-3xl font-extrabold text-[#21152F] tracking-tight">
              Built for precision, transparency, and trust.
            </h2>
            <p className="text-[#766A87] mt-3">
              TalentLens removes recruitment guesswork with verifiable evidence extraction, deterministic scoring, and grounded AI decision support.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="p-6 rounded-2xl bg-[#FAF9FD] border border-[#EAE5F2] hover:border-[#D4BEFF] transition-all duration-200">
              <div className="w-12 h-12 rounded-xl bg-[#F3EEFF] text-[#7950D9] flex items-center justify-center mb-5">
                <Target className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#21152F] mb-2">Deterministic Scoring Engine</h3>
              <p className="text-sm text-[#766A87] leading-relaxed">
                Objective scoring formulas evaluate required skills (60%), preferred skills (15%), and experience (25%). No black-box score hallucinations.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="p-6 rounded-2xl bg-[#FAF9FD] border border-[#EAE5F2] hover:border-[#D4BEFF] transition-all duration-200">
              <div className="w-12 h-12 rounded-xl bg-[#F3EEFF] text-[#7950D9] flex items-center justify-center mb-5">
                <Brain className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#21152F] mb-2">Evidence-Backed Candidate Insights</h3>
              <p className="text-sm text-[#766A87] leading-relaxed">
                Explainable summaries cite verbatim resume excerpts and verified projects, highlighting exact strengths and specific evidence gaps.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="p-6 rounded-2xl bg-[#FAF9FD] border border-[#EAE5F2] hover:border-[#D4BEFF] transition-all duration-200">
              <div className="w-12 h-12 rounded-xl bg-[#F3EEFF] text-[#7950D9] flex items-center justify-center mb-5">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#21152F] mb-2">Resume Version Pinning</h3>
              <p className="text-sm text-[#766A87] leading-relaxed">
                Applications pin the exact resume version submitted. Candidates can upload new versions for future roles without modifying active application records.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* DUAL WORKSPACE SHOWCASE: CANDIDATES VS RECRUITERS */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto space-y-20">
          {/* Candidates Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold mb-4">
                <Users className="w-3.5 h-3.5" />
                For Candidates
              </div>
              <h2 className="text-3xl font-extrabold text-[#21152F] tracking-tight mb-4">
                Supercharge your career with personalized AI guidance.
              </h2>
              <p className="text-[#766A87] text-base leading-relaxed mb-6">
                Understand how your resume aligns with target roles. Get deterministic text quality feedback, discover skill gaps, and chat with an AI career mentor grounded in your actual experience.
              </p>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-3 text-sm text-[#21152F]">
                  <CheckCircle2 className="w-5 h-5 text-[#7950D9] shrink-0 mt-0.5" />
                  <span><strong>M7 Resume Intelligence:</strong> Structural checks, measurable outcome audits, and role-tailored guidance.</span>
                </li>
                <li className="flex items-start gap-3 text-sm text-[#21152F]">
                  <CheckCircle2 className="w-5 h-5 text-[#7950D9] shrink-0 mt-0.5" />
                  <span><strong>M8 AI Career Assistant:</strong> Interview preparation and targeted skill enhancement grounded in your resume.</span>
                </li>
                <li className="flex items-start gap-3 text-sm text-[#21152F]">
                  <CheckCircle2 className="w-5 h-5 text-[#7950D9] shrink-0 mt-0.5" />
                  <span><strong>Transparent Tracking:</strong> Real-time application lifecycle tracking with self-service withdrawal.</span>
                </li>
              </ul>
              <Button variant="primary" onClick={onOpenCandidate} icon={<ArrowRight className="w-4 h-4" />}>
                Enter Candidate Portal
              </Button>
            </div>

            {/* Candidate Card Graphic */}
            <div className="rounded-2xl bg-white border border-[#EAE5F2] p-6 shadow-sm">
              <div className="flex items-center justify-between pb-4 border-b border-[#EAE5F2] mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-[#F3EEFF] text-[#7950D9] flex items-center justify-center font-bold">
                    SC
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-[#21152F]">Sarah Candidate</h4>
                    <p className="text-xs text-[#766A87]">Target Role: Staff Backend Engineer</p>
                  </div>
                </div>
                <Badge variant="purple">Analysis Ready</Badge>
              </div>
              <div className="space-y-3 text-xs">
                <div className="p-3 bg-[#FAF9FD] rounded-xl border border-[#EAE5F2]">
                  <span className="font-semibold text-[#21152F] block mb-1">Resume Quality Checks:</span>
                  <div className="grid grid-cols-2 gap-2 text-[#766A87]">
                    <div>Word Count: <strong className="text-[#21152F]">482 words</strong></div>
                    <div>Sections: <strong className="text-[#21152F]">5 detected</strong></div>
                    <div>Metrics & Outcomes: <strong className="text-emerald-600">3 verified</strong></div>
                    <div>Contact Info: <strong className="text-emerald-600">Complete</strong></div>
                  </div>
                </div>
                <div className="p-3 bg-[#F3EEFF]/40 rounded-xl border border-[#E7DCFF]">
                  <span className="font-semibold text-[#7950D9] block mb-1">High-Priority Recommendation:</span>
                  <p className="text-[#21152F]">
                    Elaborate on database sharding & caching strategies in project "E-Commerce API" to strengthen evidence for Staff-level scope.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Recruiters Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            {/* Recruiter Card Graphic */}
            <div className="order-2 lg:order-1 rounded-2xl bg-white border border-[#EAE5F2] p-6 shadow-sm">
              <div className="flex items-center justify-between pb-4 border-b border-[#EAE5F2] mb-4">
                <div>
                  <h4 className="text-sm font-bold text-[#21152F]">Senior API Architect Requisition</h4>
                  <p className="text-xs text-[#766A87]">Core Tech Department · 12 Applicants Screened</p>
                </div>
                <Badge variant="success">Active Job</Badge>
              </div>

              {/* Mini Pipeline Preview */}
              <div className="grid grid-cols-4 gap-2 mb-4 text-center">
                <div className="p-2 rounded-lg bg-[#FAF9FD] border border-[#EAE5F2]">
                  <div className="text-sm font-bold text-[#21152F]">12</div>
                  <div className="text-[10px] text-[#766A87]">Submitted</div>
                </div>
                <div className="p-2 rounded-lg bg-amber-50 border border-amber-200">
                  <div className="text-sm font-bold text-amber-700">5</div>
                  <div className="text-[10px] text-amber-700">Review</div>
                </div>
                <div className="p-2 rounded-lg bg-[#F3EEFF] border border-[#E7DCFF]">
                  <div className="text-sm font-bold text-[#7950D9]">3</div>
                  <div className="text-[10px] text-[#7950D9]">Shortlisted</div>
                </div>
                <div className="p-2 rounded-lg bg-emerald-50 border border-emerald-200">
                  <div className="text-sm font-bold text-emerald-700">2</div>
                  <div className="text-[10px] text-emerald-700">Interview</div>
                </div>
              </div>

              <div className="p-3 bg-[#FAF9FD] rounded-xl border border-[#EAE5F2] text-xs">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-[#21152F]">M9 Hiring Intelligence:</span>
                  <span className="text-[10px] text-[#7950D9]">SQL Retrieval Grounded</span>
                </div>
                <p className="text-[#766A87]">
                  "Ranked #1 candidate demonstrates 4 verified years of FastAPI and PostgreSQL architecture. Ready for technical round."
                </p>
              </div>
            </div>

            <div className="order-1 lg:order-2">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#F3EEFF] text-[#7950D9] text-xs font-semibold mb-4">
                <Briefcase className="w-3.5 h-3.5" />
                For Recruiters & Hiring Teams
              </div>
              <h2 className="text-3xl font-extrabold text-[#21152F] tracking-tight mb-4">
                Cut screening time by 80% without losing human touch.
              </h2>
              <p className="text-[#766A87] text-base leading-relaxed mb-6">
                Publish positions, screen high-volume candidate pools deterministically, inspect pinned resume PDFs, and query organization hiring data through conversational intelligence.
              </p>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-3 text-sm text-[#21152F]">
                  <CheckCircle2 className="w-5 h-5 text-[#7950D9] shrink-0 mt-0.5" />
                  <span><strong>Automated Screening Batches:</strong> Run screening across all applicants with reproducible scoring weights.</span>
                </li>
                <li className="flex items-start gap-3 text-sm text-[#21152F]">
                  <CheckCircle2 className="w-5 h-5 text-[#7950D9] shrink-0 mt-0.5" />
                  <span><strong>M9 Recruiter AI Assistant:</strong> Query candidate pipelines, compare finalists, and review source citations safely.</span>
                </li>
                <li className="flex items-start gap-3 text-sm text-[#21152F]">
                  <CheckCircle2 className="w-5 h-5 text-[#7950D9] shrink-0 mt-0.5" />
                  <span><strong>Multi-Tenant Isolation:</strong> Strict organizational boundary protection, RBAC, and auditor-ready history logs.</span>
                </li>
              </ul>
              <Button variant="secondary" onClick={onOpenRecruiter} icon={<ArrowRight className="w-4 h-4 text-[#7950D9]" />}>
                Open Recruiter Workspace
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* TRUST & PRIVACY */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-white border-t border-[#EAE5F2]">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-center">
            <div className="p-6">
              <ShieldCheck className="w-8 h-8 text-[#7950D9] mx-auto mb-3" />
              <h4 className="text-base font-bold text-[#21152F] mb-1">Strict Tenant Isolation</h4>
              <p className="text-xs text-[#766A87]">
                Cross-organization barriers prevent data leakage. Recruiters cannot access another tenant's jobs or applicants.
              </p>
            </div>
            <div className="p-6">
              <FileText className="w-8 h-8 text-[#7950D9] mx-auto mb-3" />
              <h4 className="text-base font-bold text-[#21152F] mb-1">Tamper-Proof Resume Pinning</h4>
              <p className="text-xs text-[#766A87]">
                Submitted resumes are permanently pinned to applications. Editing your profile never alters historical submissions.
              </p>
            </div>
            <div className="p-6">
              <Zap className="w-8 h-8 text-[#7950D9] mx-auto mb-3" />
              <h4 className="text-base font-bold text-[#21152F] mb-1">Resilient Local AI Architecture</h4>
              <p className="text-xs text-[#766A87]">
                Multi-model fallbacks ensure platform availability even during inference outages with deterministic fallback logic.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FINAL CALL TO ACTION */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-[#FAF9FD] to-[#F3EEFF]/80 text-center">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[#21152F] mb-4">
            Ready to experience intelligent recruitment?
          </h2>
          <p className="text-[#766A87] text-base mb-8">
            Join candidates and forward-thinking recruitment teams using TalentLens today.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button variant="primary" size="lg" onClick={onGetStarted}>
              Get Started Free
            </Button>
            <Button variant="outline" size="lg" onClick={onExploreJobs}>
              Browse Open Jobs
            </Button>
          </div>
        </div>
      </section>

      {/* PROFESSIONAL FOOTER */}
      <footer className="mt-auto border-t border-[#EAE5F2] bg-white py-12 px-4 sm:px-8 text-xs text-[#766A87]">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-[#7950D9] flex items-center justify-center text-white">
              <Sparkles className="w-3.5 h-3.5" />
            </div>
            <span className="font-bold text-sm text-[#21152F]">TalentLens</span>
            <span className="text-[#766A87]">© 2026 TalentLens Inc. All rights reserved.</span>
          </div>
          <div className="flex items-center gap-6">
            <button onClick={onExploreJobs} className="hover:text-[#7950D9] transition-colors">
              Explore Jobs
            </button>
            <button onClick={onOpenCandidate} className="hover:text-[#7950D9] transition-colors">
              Candidate Portal
            </button>
            <button onClick={onOpenRecruiter} className="hover:text-[#7950D9] transition-colors">
              Recruiter Workspace
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}
