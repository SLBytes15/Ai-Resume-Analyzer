import React from 'react';

export type BadgeVariant =
  | 'default'
  | 'purple'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'neutral';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  className?: string;
  dot?: boolean;
}

export function Badge({
  children,
  variant = 'default',
  size = 'md',
  className = '',
  dot = false,
}: BadgeProps) {
  const variantStyles: Record<BadgeVariant, string> = {
    default: 'bg-[#F3EEFF] text-[#7950D9] border-[#E7DCFF]',
    purple: 'bg-[#7950D9]/10 text-[#7950D9] border-[#7950D9]/20',
    success: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    warning: 'bg-amber-50 text-amber-700 border-amber-200',
    danger: 'bg-rose-50 text-rose-700 border-rose-200',
    info: 'bg-blue-50 text-blue-700 border-blue-200',
    neutral: 'bg-slate-100 text-slate-700 border-slate-200',
  };

  const dotColors: Record<BadgeVariant, string> = {
    default: 'bg-[#7950D9]',
    purple: 'bg-[#7950D9]',
    success: 'bg-emerald-500',
    warning: 'bg-amber-500',
    danger: 'bg-rose-500',
    info: 'bg-blue-500',
    neutral: 'bg-slate-400',
  };

  const sizeStyles = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1 font-medium',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border transition-colors ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]}`} />}
      {children}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const norm = (status || '').toUpperCase();
  switch (norm) {
    case 'PUBLISHED':
    case 'HIRED':
    case 'COMPLETED':
      return <Badge variant="success" dot>{status}</Badge>;
    case 'SHORTLISTED':
    case 'INTERVIEWING':
      return <Badge variant="purple" dot>{status}</Badge>;
    case 'SUBMITTED':
    case 'PROCESSING':
    case 'PENDING':
      return <Badge variant="info" dot>{status}</Badge>;
    case 'UNDER_REVIEW':
      return <Badge variant="warning" dot>{status}</Badge>;
    case 'REJECTED':
    case 'FAILED':
    case 'CLOSED':
      return <Badge variant="danger" dot>{status}</Badge>;
    case 'WITHDRAWN':
    case 'DRAFT':
    case 'ARCHIVED':
    default:
      return <Badge variant="neutral" dot>{status}</Badge>;
  }
}
