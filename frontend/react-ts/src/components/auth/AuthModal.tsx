import React, { useState } from 'react';
import { Sparkles, Eye, EyeOff, Lock, Mail, User, ArrowRight, ShieldCheck, CheckCircle2, AlertCircle, X } from 'lucide-react';
import { Button } from '../common/Button';
import { handleApiResponse, parseApiError } from '../../utils/apiError';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  isRegisterDefault?: boolean;
  onSuccess: (token: string) => void;
}

export function AuthModal({
  isOpen,
  onClose,
  isRegisterDefault = false,
  onSuccess,
}: AuthModalProps) {
  const [isRegister, setIsRegister] = useState(isRegisterDefault);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');

    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      setErrorMessage('Email address is required.');
      return;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(trimmedEmail)) {
      setErrorMessage('Please enter a valid email address.');
      return;
    }

    if (isRegister) {
      const trimmedName = fullName.trim();
      if (!trimmedName) {
        setErrorMessage('Full name is required.');
        return;
      }
      if (password.length < 8) {
        setErrorMessage('Password must be at least 8 characters long.');
        return;
      }
    } else {
      if (!password) {
        setErrorMessage('Password is required.');
        return;
      }
    }

    setIsLoading(true);

    const API_BASE = (import.meta.env.VITE_API_URL as string) || 'http://127.0.0.1:8000';
    const endpoint = isRegister ? '/api/v1/auth/register' : '/api/v1/auth/login';
    const payload = isRegister
      ? { email: trimmedEmail, password, full_name: fullName.trim() }
      : { email: trimmedEmail, password };

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await handleApiResponse<{ access_token: string }>(
        res,
        isRegister ? 'Registration failed. Please check your details.' : 'Authentication failed. Please check your credentials.'
      );
      onSuccess(data.access_token);
      onClose();
    } catch (err: unknown) {
      setErrorMessage(parseApiError(err, 'Authentication error occurred'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-[#21152F]/50 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Split-Screen Modal Box */}
      <div className="relative w-full max-w-4xl bg-white rounded-3xl shadow-2xl border border-[#EAE5F2] overflow-hidden z-10 grid grid-cols-1 md:grid-cols-12 min-h-[580px] animate-in fade-in zoom-in-95 duration-200">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-20 p-2 text-[#766A87] hover:text-[#21152F] hover:bg-[#F3EEFF] rounded-full transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* LEFT COLUMN: Visual Branding & Value Proposition */}
        <div className="hidden md:flex md:col-span-5 bg-gradient-to-br from-[#43216F] via-[#513296] to-[#7950D9] p-8 text-white flex-col justify-between relative overflow-hidden">
          {/* Subtle glow circle */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-2xl pointer-events-none" />

          <div>
            {/* Brand Logo */}
            <div className="flex items-center gap-2.5 mb-10">
              <div className="w-9 h-9 rounded-xl bg-white/15 backdrop-blur-sm flex items-center justify-center text-white border border-white/20">
                <Sparkles className="w-5 h-5 text-purple-200" />
              </div>
              <span className="font-extrabold text-xl tracking-tight text-white">TalentLens</span>
            </div>

            <h3 className="text-2xl font-bold tracking-tight leading-snug mb-4">
              Intelligent Recruitment, Grounded in Evidence.
            </h3>
            <p className="text-purple-100/80 text-sm leading-relaxed mb-8">
              Join thousands of professionals and recruitment teams discovering precise career alignment.
            </p>

            <div className="space-y-3.5 text-xs text-purple-100/90">
              <div className="flex items-center gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-purple-300 shrink-0" />
                <span>Deterministic, explainable candidate scoring</span>
              </div>
              <div className="flex items-center gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-purple-300 shrink-0" />
                <span>Tamper-proof resume version pinning</span>
              </div>
              <div className="flex items-center gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-purple-300 shrink-0" />
                <span>Grounded AI candidate & recruiter assistants</span>
              </div>
            </div>
          </div>

          <div className="pt-6 border-t border-white/10 flex items-center gap-2 text-[11px] text-purple-200/70">
            <ShieldCheck className="w-4 h-4" />
            <span>Enterprise-grade tenant isolation & privacy</span>
          </div>
        </div>

        {/* RIGHT COLUMN: Elegant Authentication Form */}
        <div className="md:col-span-7 p-8 sm:p-10 flex flex-col justify-center">
          <div className="max-w-md w-full mx-auto">
            {/* Header / Tabs */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-2xl font-extrabold text-[#21152F] tracking-tight">
                  {isRegister ? 'Create your account' : 'Welcome back'}
                </h2>
              </div>
              <p className="text-sm text-[#766A87]">
                {isRegister
                  ? 'Start your journey with AI-powered career intelligence.'
                  : 'Enter your credentials to access your dashboard.'}
              </p>
            </div>

            {/* Error Message */}
            {errorMessage && (
              <div className="mb-5 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start gap-2.5 animate-in fade-in duration-150">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
                <span>{errorMessage}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Full Name Field (Register Mode Only) */}
              {isRegister && (
                <div>
                  <label className="block text-xs font-semibold text-[#21152F] mb-1.5">
                    Full Name
                  </label>
                  <div className="relative">
                    <User className="w-4 h-4 text-[#766A87] absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      required
                      placeholder="e.g. Sarah Jenkins"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-sm text-[#21152F] placeholder-[#9B91AA] focus:outline-none focus:border-[#7950D9] focus:bg-white focus:ring-2 focus:ring-[#7950D9]/15 transition-all"
                    />
                  </div>
                </div>
              )}

              {/* Email Field */}
              <div>
                <label className="block text-xs font-semibold text-[#21152F] mb-1.5">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-[#766A87] absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    required
                    placeholder="name@company.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-sm text-[#21152F] placeholder-[#9B91AA] focus:outline-none focus:border-[#7950D9] focus:bg-white focus:ring-2 focus:ring-[#7950D9]/15 transition-all"
                  />
                </div>
              </div>

              {/* Password Field */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-semibold text-[#21152F]">
                    Password
                  </label>
                </div>
                <div className="relative">
                  <Lock className="w-4 h-4 text-[#766A87] absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    minLength={isRegister ? 8 : 1}
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-sm text-[#21152F] placeholder-[#9B91AA] focus:outline-none focus:border-[#7950D9] focus:bg-white focus:ring-2 focus:ring-[#7950D9]/15 transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#766A87] hover:text-[#21152F]"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {isRegister && (
                  <p className="text-[11px] text-[#766A87] mt-1">
                    Must be at least 8 characters with letters, numbers, and symbols.
                  </p>
                )}
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                variant="primary"
                size="md"
                isLoading={isLoading}
                className="w-full mt-2"
                icon={<ArrowRight className="w-4 h-4" />}
              >
                {isRegister ? 'Create Account' : 'Sign In'}
              </Button>
            </form>

            {/* Toggle Mode Footer */}
            <div className="mt-6 pt-5 border-t border-[#EAE5F2] text-center text-xs text-[#766A87]">
              {isRegister ? (
                <p>
                  Already have an account?{' '}
                  <button
                    onClick={() => {
                      setIsRegister(false);
                      setErrorMessage('');
                    }}
                    className="font-bold text-[#7950D9] hover:underline"
                  >
                    Sign In
                  </button>
                </p>
              ) : (
                <p>
                  Don't have an account yet?{' '}
                  <button
                    onClick={() => {
                      setIsRegister(true);
                      setErrorMessage('');
                    }}
                    className="font-bold text-[#7950D9] hover:underline"
                  >
                    Create one for free
                  </button>
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
