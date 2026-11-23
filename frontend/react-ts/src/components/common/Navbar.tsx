import React from 'react';
import { Sparkles, Briefcase, User, Building2, LogOut, ChevronDown, Compass } from 'lucide-react';
import { Organization } from '../../types';
import { Button } from './Button';

interface NavbarProps {
  activeTab: 'landing' | 'public-jobs' | 'candidate' | 'recruiter';
  setActiveTab: (tab: 'landing' | 'public-jobs' | 'candidate' | 'recruiter') => void;
  token: string;
  userEmail?: string;
  onLogout: () => void;
  onOpenAuth: (isRegister?: boolean) => void;
  userOrgs: Organization[];
  selectedOrgId: string;
  onSelectOrg: (orgId: string) => void;
}

export function Navbar({
  activeTab,
  setActiveTab,
  token,
  userEmail,
  onLogout,
  onOpenAuth,
  userOrgs,
  selectedOrgId,
  onSelectOrg,
}: NavbarProps) {
  const activeOrg = userOrgs.find((o) => o.id === selectedOrgId);

  return (
    <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-[#EAE5F2] px-4 sm:px-8 py-3.5 transition-all">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        {/* Brand Logo */}
        <div className="flex items-center gap-8">
          <button
            onClick={() => setActiveTab('landing')}
            className="flex items-center gap-2.5 text-left group focus:outline-none"
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#43216F] to-[#7950D9] flex items-center justify-center text-white shadow-sm shadow-[#7950D9]/30 group-hover:scale-105 transition-transform">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-lg text-[#21152F] tracking-tight">TalentLens</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-[#F3EEFF] text-[#7950D9] tracking-wider uppercase">
                  AI
                </span>
              </div>
            </div>
          </button>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            <button
              onClick={() => setActiveTab('landing')}
              className={`px-3.5 py-2 rounded-xl text-sm font-medium transition-all ${
                activeTab === 'landing'
                  ? 'bg-[#F3EEFF] text-[#7950D9] font-semibold'
                  : 'text-[#766A87] hover:text-[#21152F] hover:bg-[#FAF9FD]'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('public-jobs')}
              className={`px-3.5 py-2 rounded-xl text-sm font-medium transition-all flex items-center gap-1.5 ${
                activeTab === 'public-jobs'
                  ? 'bg-[#F3EEFF] text-[#7950D9] font-semibold'
                  : 'text-[#766A87] hover:text-[#21152F] hover:bg-[#FAF9FD]'
              }`}
            >
              <Compass className="w-4 h-4" />
              Explore Jobs
            </button>
            <button
              onClick={() => {
                if (!token) onOpenAuth(false);
                else setActiveTab('candidate');
              }}
              className={`px-3.5 py-2 rounded-xl text-sm font-medium transition-all flex items-center gap-1.5 ${
                activeTab === 'candidate'
                  ? 'bg-[#F3EEFF] text-[#7950D9] font-semibold'
                  : 'text-[#766A87] hover:text-[#21152F] hover:bg-[#FAF9FD]'
              }`}
            >
              <User className="w-4 h-4" />
              Candidate Portal
            </button>
            <button
              onClick={() => {
                if (!token) onOpenAuth(false);
                else setActiveTab('recruiter');
              }}
              className={`px-3.5 py-2 rounded-xl text-sm font-medium transition-all flex items-center gap-1.5 ${
                activeTab === 'recruiter'
                  ? 'bg-[#F3EEFF] text-[#7950D9] font-semibold'
                  : 'text-[#766A87] hover:text-[#21152F] hover:bg-[#FAF9FD]'
              }`}
            >
              <Briefcase className="w-4 h-4" />
              Recruiter Workspace
            </button>
          </nav>
        </div>

        {/* Right Action Area */}
        <div className="flex items-center gap-3">
          {token ? (
            <div className="flex items-center gap-3">
              {/* Recruiter Active Org Switcher (if on recruiter tab or has orgs) */}
              {userOrgs.length > 0 && (
                <div className="relative hidden sm:block">
                  <div className="flex items-center gap-2 bg-[#FAF9FD] border border-[#EAE5F2] rounded-xl px-3 py-1.5 text-xs text-[#21152F]">
                    <Building2 className="w-3.5 h-3.5 text-[#7950D9]" />
                    <select
                      value={selectedOrgId}
                      onChange={(e) => onSelectOrg(e.target.value)}
                      className="bg-transparent font-medium text-xs text-[#21152F] focus:outline-none cursor-pointer pr-2"
                    >
                      {userOrgs.map((org) => (
                        <option key={org.id} value={org.id}>
                          {org.name} ({org.role || 'MEMBER'})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              )}

              {/* User Avatar Chip */}
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#F3EEFF]/80 border border-[#E7DCFF] text-xs">
                <div className="w-5 h-5 rounded-full bg-[#7950D9] text-white flex items-center justify-center font-bold text-[10px]">
                  {userEmail ? userEmail.charAt(0).toUpperCase() : 'U'}
                </div>
                <span className="font-medium text-[#43216F] max-w-[140px] truncate hidden sm:inline">
                  {userEmail || 'Account'}
                </span>
              </div>

              {/* Log out */}
              <Button
                variant="outline"
                size="sm"
                onClick={onLogout}
                icon={<LogOut className="w-3.5 h-3.5 text-[#766A87]" />}
                className="hidden sm:inline-flex"
              >
                Sign Out
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={() => onOpenAuth(false)}>
                Sign In
              </Button>
              <Button variant="primary" size="sm" onClick={() => onOpenAuth(true)}>
                Get Started
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
