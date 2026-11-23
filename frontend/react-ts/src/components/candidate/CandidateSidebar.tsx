import React from 'react';
import {
  LayoutDashboard,
  User,
  FileText,
  Sparkles,
  Compass,
  FileCheck2,
  Bot,
  LogOut,
  ExternalLink,
} from 'lucide-react';
import { CandidateProfile } from '../../types';

export type CandidateTab =
  | 'overview'
  | 'profile'
  | 'resumes'
  | 'intelligence'
  | 'jobs'
  | 'applications'
  | 'career-assistant';

interface CandidateSidebarProps {
  activeTab: CandidateTab;
  onTabChange: (tab: CandidateTab) => void;
  profile: CandidateProfile | null;
  onLogout: () => void;
  onExploreJobs: () => void;
}

export function CandidateSidebar({
  activeTab,
  onTabChange,
  profile,
  onLogout,
  onExploreJobs,
}: CandidateSidebarProps) {
  const navItems: Array<{ id: CandidateTab; label: string; icon: React.ReactNode }> = [
    { id: 'overview', label: 'Overview', icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: 'profile', label: 'My Profile', icon: <User className="w-4 h-4" /> },
    { id: 'resumes', label: 'My Resumes', icon: <FileText className="w-4 h-4" /> },
    { id: 'intelligence', label: 'Resume Intelligence', icon: <Sparkles className="w-4 h-4 text-[#7950D9]" /> },
    { id: 'jobs', label: 'Explore Jobs', icon: <Compass className="w-4 h-4" /> },
    { id: 'applications', label: 'My Applications', icon: <FileCheck2 className="w-4 h-4" /> },
    { id: 'career-assistant', label: 'Career Assistant', icon: <Bot className="w-4 h-4 text-[#7950D9]" /> },
  ];

  return (
    <aside className="w-full lg:w-64 bg-white border-b lg:border-b-0 lg:border-r border-[#EAE5F2] flex flex-col justify-between shrink-0 p-4">
      <div>
        {/* Section title */}
        <div className="px-3 py-2 mb-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-[#766A87]">
            Candidate Portal
          </span>
        </div>

        {/* Nav Items List */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 text-left ${
                  isActive
                    ? 'bg-[#F3EEFF] text-[#7950D9] shadow-xs'
                    : 'text-[#766A87] hover:text-[#21152F] hover:bg-[#FAF9FD]'
                }`}
              >
                <span className={isActive ? 'text-[#7950D9]' : 'text-[#766A87]'}>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* User Card at Bottom */}
      <div className="mt-8 pt-4 border-t border-[#EAE5F2]">
        <div className="p-3 bg-[#FAF9FD] rounded-xl border border-[#EAE5F2] mb-3">
          <div className="flex items-center gap-2.5 mb-1">
            <div className="w-8 h-8 rounded-full bg-[#7950D9] text-white flex items-center justify-center font-bold text-xs shrink-0">
              {profile?.full_name ? profile.full_name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-bold text-[#21152F] truncate">
                {profile?.full_name || 'Candidate User'}
              </p>
              <p className="text-[11px] text-[#766A87] truncate">{profile?.email || 'Authenticated'}</p>
            </div>
          </div>
        </div>

        <button
          onClick={onLogout}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium text-[#766A87] hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors border border-transparent hover:border-rose-200"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
