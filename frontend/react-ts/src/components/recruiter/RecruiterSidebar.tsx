import React from 'react';
import {
  LayoutDashboard,
  Briefcase,
  Users,
  Sparkles,
  GitPullRequest,
  Bot,
  Building2,
  Plus,
  Layers,
  Search,
} from 'lucide-react';
import { Organization } from '../../types';
import { Button } from '../common/Button';

export type RecruiterTab =
  | 'overview'
  | 'jobs'
  | 'applicants'
  | 'screening'
  | 'pipeline'
  | 'hiring-assistant'
  | 'matcher'
  | 'organizations';

interface RecruiterSidebarProps {
  activeTab: RecruiterTab;
  onTabChange: (tab: RecruiterTab) => void;
  activeOrg?: Organization;
  userOrgs: Organization[];
  onSelectOrg: (id: string) => void;
  onOpenNewJobModal: () => void;
  onOpenNewOrgModal: () => void;
}

export function RecruiterSidebar({
  activeTab,
  onTabChange,
  activeOrg,
  userOrgs,
  onSelectOrg,
  onOpenNewJobModal,
  onOpenNewOrgModal,
}: RecruiterSidebarProps) {
  const navItems: Array<{ id: RecruiterTab; label: string; icon: React.ReactNode }> = [
    { id: 'overview', label: 'Overview', icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: 'jobs', label: 'Job Requisitions', icon: <Briefcase className="w-4 h-4" /> },
    { id: 'applicants', label: 'Applicants', icon: <Users className="w-4 h-4" /> },
    { id: 'screening', label: 'AI Screening (M6)', icon: <Sparkles className="w-4 h-4 text-[#7950D9]" /> },
    { id: 'pipeline', label: 'Hiring Pipeline', icon: <GitPullRequest className="w-4 h-4 text-emerald-600" /> },
    { id: 'hiring-assistant', label: 'Hiring Assistant (M9)', icon: <Bot className="w-4 h-4 text-[#7950D9]" /> },
    { id: 'matcher', label: 'Instant Matcher', icon: <Search className="w-4 h-4" /> },
  ];

  const isRecruiterOrAbove = activeOrg?.role && ['OWNER', 'ADMIN', 'RECRUITER'].includes(activeOrg.role);

  return (
    <aside className="w-full lg:w-64 bg-white border-b lg:border-b-0 lg:border-r border-[#EAE5F2] flex flex-col justify-between shrink-0 p-4">
      <div>
        {/* Active Organization Chip */}
        <div className="p-3 bg-[#FAF9FD] rounded-2xl border border-[#EAE5F2] mb-4">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#766A87]">
              Active Organization
            </span>
            <button
              onClick={onOpenNewOrgModal}
              title="Create new organization"
              className="text-[10px] font-bold text-[#7950D9] hover:underline"
            >
              + New Org
            </button>
          </div>

          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[#F3EEFF] text-[#7950D9] flex items-center justify-center font-bold text-xs shrink-0">
              <Building2 className="w-4 h-4" />
            </div>
            <div className="min-w-0 flex-1">
              <select
                value={activeOrg?.id || ''}
                onChange={(e) => onSelectOrg(e.target.value)}
                className="w-full bg-transparent font-bold text-xs text-[#21152F] focus:outline-none cursor-pointer truncate"
              >
                {userOrgs.map((org) => (
                  <option key={org.id} value={org.id}>
                    {org.name}
                  </option>
                ))}
              </select>
              <div className="text-[10px] text-[#766A87] font-medium">
                Role: <span className="text-[#7950D9] font-bold">{activeOrg?.role || 'MEMBER'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Action: New Job */}
        {isRecruiterOrAbove && (
          <div className="mb-4">
            <Button
              variant="primary"
              size="sm"
              onClick={onOpenNewJobModal}
              icon={<Plus className="w-4 h-4" />}
              className="w-full justify-center shadow-xs"
            >
              Create Job Requisition
            </Button>
          </div>
        )}

        {/* Navigation Links */}
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

      <div className="mt-8 pt-4 border-t border-[#EAE5F2] text-[11px] text-[#766A87] text-center">
        <span>TalentLens Recruiter Workspace</span>
      </div>
    </aside>
  );
}
