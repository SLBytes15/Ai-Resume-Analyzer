import React, { useRef, useState } from 'react';
import {
  FileText,
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  Download,
  Trash2,
  Sparkles,
  Eye,
  Clock,
  Layers,
} from 'lucide-react';
import { ResumeItem } from '../../types';
import { Card, CardHeader, CardBody } from '../common/Card';
import { Button } from '../common/Button';
import { Badge, StatusBadge } from '../common/Badge';
import { Modal } from '../common/Modal';

interface CandidateResumesViewProps {
  resumes: ResumeItem[];
  uploading: boolean;
  uploadError: string;
  onUpload: (file: File) => Promise<void>;
  onDeleteResume: (resumeId: string) => Promise<void>;
  onDownloadResume: (resumeId: string, filename: string) => void;
  onAnalyzeResume: (resumeId: string) => void;
}

export function CandidateResumesView({
  resumes,
  uploading,
  uploadError,
  onUpload,
  onDeleteResume,
  onDownloadResume,
  onAnalyzeResume,
}: CandidateResumesViewProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedResumeForView, setSelectedResumeForView] = useState<ResumeItem | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      await onUpload(file);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this resume version? (Pinned resumes cannot be deleted)')) {
      setDeletingId(id);
      try {
        await onDeleteResume(id);
      } finally {
        setDeletingId(null);
      }
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#21152F] tracking-tight">Resume Management</h2>
          <p className="text-xs text-[#766A87]">
            Upload and manage your CV versions. New applications pin the active version permanently.
          </p>
        </div>

        <div>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf,application/pdf"
            className="hidden"
          />
          <Button
            variant="primary"
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            isLoading={uploading}
            icon={<UploadCloud className="w-4 h-4" />}
          >
            Upload New Resume (PDF)
          </Button>
        </div>
      </div>

      {uploadError && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{uploadError}</span>
        </div>
      )}

      {/* Upload Dropzone Guide */}
      <div
        onClick={() => fileInputRef.current?.click()}
        className="p-8 border-2 border-dashed border-[#EAE5F2] hover:border-[#7950D9] bg-white rounded-2xl text-center cursor-pointer transition-all hover:bg-[#F3EEFF]/20 group"
      >
        <div className="w-12 h-12 rounded-2xl bg-[#F3EEFF] text-[#7950D9] flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
          <UploadCloud className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-bold text-[#21152F] mb-1">
          Upload your resume in PDF format
        </h3>
        <p className="text-xs text-[#766A87] max-w-sm mx-auto mb-3">
          Text-based PDFs with digital text layer only. Max upload size is 5MB.
        </p>
        <span className="text-xs font-semibold text-[#7950D9] group-hover:underline">
          Click to browse or drag and drop
        </span>
      </div>

      {/* Resumes List */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-[#21152F] flex items-center gap-2">
          <span>Uploaded Versions</span>
          <span className="text-xs font-normal text-[#766A87]">({resumes.length})</span>
        </h3>

        {resumes.length === 0 ? (
          <Card>
            <CardBody className="p-8 text-center text-xs text-[#766A87]">
              No resumes uploaded yet. Upload your first PDF to enable job applications and AI career guidance.
            </CardBody>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {resumes.map((resume, idx) => (
              <Card key={resume.id} hoverEffect className="relative overflow-hidden flex flex-col justify-between">
                <CardBody className="p-5">
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-[#F3EEFF] text-[#7950D9] flex items-center justify-center shrink-0">
                        <FileText className="w-5 h-5" />
                      </div>
                      <div className="min-w-0">
                        <h4 className="text-sm font-bold text-[#21152F] truncate">
                          {resume.original_filename}
                        </h4>
                        <div className="flex items-center gap-2 text-[11px] text-[#766A87] mt-0.5">
                          <span>{(resume.file_size / 1024).toFixed(1)} KB</span>
                          <span>·</span>
                          <span>{new Date(resume.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col items-end gap-1.5 shrink-0">
                      {resume.is_active && (
                        <Badge variant="purple" size="sm" dot>Active</Badge>
                      )}
                      <StatusBadge status={resume.parsing_status} />
                    </div>
                  </div>

                  {/* Skills preview if parsed */}
                  {resume.parsed_data?.skills && resume.parsed_data.skills.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-[#EAE5F2]">
                      <span className="text-[11px] font-semibold text-[#766A87] block mb-1.5">
                        Extracted Skills:
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {resume.parsed_data.skills.slice(0, 5).map((skill, sIdx) => (
                          <span
                            key={sIdx}
                            className="px-2 py-0.5 rounded text-[10px] font-medium bg-[#FAF9FD] text-[#43216F] border border-[#EAE5F2]"
                          >
                            {skill}
                          </span>
                        ))}
                        {resume.parsed_data.skills.length > 5 && (
                          <span className="text-[10px] text-[#766A87] self-center">
                            +{resume.parsed_data.skills.length - 5} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Actions Footer */}
                  <div className="mt-4 pt-3 border-t border-[#EAE5F2] flex items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedResumeForView(resume)}
                        icon={<Eye className="w-3.5 h-3.5" />}
                      >
                        Inspect
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDownloadResume(resume.id, resume.original_filename)}
                        icon={<Download className="w-3.5 h-3.5" />}
                      >
                        PDF
                      </Button>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => onAnalyzeResume(resume.id)}
                        icon={<Sparkles className="w-3.5 h-3.5" />}
                      >
                        Analyze
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(resume.id)}
                        isLoading={deletingId === resume.id}
                        className="text-rose-600 hover:text-rose-700 hover:bg-rose-50"
                        icon={<Trash2 className="w-3.5 h-3.5" />}
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                </CardBody>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Inspect Resume Modal */}
      {selectedResumeForView && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedResumeForView(null)}
          title={`Resume Details: ${selectedResumeForView.original_filename}`}
          description={`SHA-256: ${selectedResumeForView.sha256.substring(0, 16)}...`}
          maxWidth="2xl"
        >
          <div className="space-y-4 text-xs">
            <div className="p-3 bg-[#FAF9FD] rounded-xl border border-[#EAE5F2] grid grid-cols-2 gap-2 text-[#766A87]">
              <div>Parsing Status: <strong className="text-[#21152F]">{selectedResumeForView.parsing_status}</strong></div>
              <div>Active Version: <strong className="text-[#21152F]">{selectedResumeForView.is_active ? 'Yes' : 'No'}</strong></div>
              <div>File Size: <strong className="text-[#21152F]">{(selectedResumeForView.file_size / 1024).toFixed(1)} KB</strong></div>
              <div>Created: <strong className="text-[#21152F]">{new Date(selectedResumeForView.created_at).toLocaleString()}</strong></div>
            </div>

            <div>
              <h4 className="font-bold text-[#21152F] mb-1">Extracted Text Content</h4>
              <div className="p-4 bg-[#FAF9FD] rounded-xl border border-[#EAE5F2] font-mono text-[11px] max-h-60 overflow-y-auto whitespace-pre-wrap text-[#21152F]">
                {selectedResumeForView.extracted_text || 'No text extracted.'}
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
