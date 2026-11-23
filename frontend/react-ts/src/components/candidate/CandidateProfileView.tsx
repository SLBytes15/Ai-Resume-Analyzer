import React, { useState } from 'react';
import { User, Phone, MapPin, Briefcase, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import { CandidateProfile } from '../../types';
import { Card, CardHeader, CardBody, CardFooter } from '../common/Card';
import { Button } from '../common/Button';

interface CandidateProfileViewProps {
  profile: CandidateProfile | null;
  onSaveProfile: (data: {
    phone: string;
    location: string;
    headline: string;
    professional_summary: string;
  }) => Promise<void>;
  saving: boolean;
  message: string;
}

export function CandidateProfileView({
  profile,
  onSaveProfile,
  saving,
  message,
}: CandidateProfileViewProps) {
  const [phone, setPhone] = useState(profile?.phone || '');
  const [location, setLocation] = useState(profile?.location || '');
  const [headline, setHeadline] = useState(profile?.headline || '');
  const [summary, setSummary] = useState(profile?.professional_summary || '');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSaveProfile({
      phone: phone.trim(),
      location: location.trim(),
      headline: headline.trim(),
      professional_summary: summary.trim(),
    });
  };

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h2 className="text-xl font-bold text-[#21152F] tracking-tight">Candidate Profile</h2>
        <p className="text-xs text-[#766A87]">
          Manage your personal details, contact coordinates, and professional headline.
        </p>
      </div>

      {message && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{message}</span>
        </div>
      )}

      <Card>
        <form onSubmit={handleSubmit}>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-[#F3EEFF] text-[#7950D9] flex items-center justify-center font-bold text-lg">
                {profile?.full_name ? profile.full_name.charAt(0).toUpperCase() : 'U'}
              </div>
              <div>
                <h3 className="text-sm font-bold text-[#21152F]">{profile?.full_name || 'Candidate Name'}</h3>
                <p className="text-xs text-[#766A87]">{profile?.email || 'Email address'}</p>
              </div>
            </div>
          </CardHeader>

          <CardBody className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Phone */}
              <div>
                <label className="block text-xs font-semibold text-[#21152F] mb-1.5">
                  Phone Number
                </label>
                <div className="relative">
                  <Phone className="w-4 h-4 text-[#766A87] absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="+91 98765 43210"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
                  />
                </div>
              </div>

              {/* Location */}
              <div>
                <label className="block text-xs font-semibold text-[#21152F] mb-1.5">
                  Current Location
                </label>
                <div className="relative">
                  <MapPin className="w-4 h-4 text-[#766A87] absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="e.g. Bengaluru, India"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
                  />
                </div>
              </div>
            </div>

            {/* Headline */}
            <div>
              <label className="block text-xs font-semibold text-[#21152F] mb-1.5">
                Professional Headline
              </label>
              <div className="relative">
                <Briefcase className="w-4 h-4 text-[#766A87] absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="e.g. Senior Backend Architect | Python, FastAPI, Distributed Systems"
                  value={headline}
                  onChange={(e) => setHeadline(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
                />
              </div>
            </div>

            {/* Professional Summary */}
            <div>
              <label className="block text-xs font-semibold text-[#21152F] mb-1.5">
                Professional Summary
              </label>
              <textarea
                rows={4}
                placeholder="Brief summary of your background, core strengths, and engineering accomplishments..."
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                className="w-full p-3 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white leading-relaxed resize-none"
              />
            </div>
          </CardBody>

          <CardFooter className="flex items-center justify-end gap-3">
            <Button type="submit" variant="primary" size="sm" isLoading={saving}>
              Save Profile Changes
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
