import React, { useState } from 'react';
import {
  Bot,
  Send,
  Plus,
  Sparkles,
  FileText,
  User,
  Clock,
  Layers,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
} from 'lucide-react';
import {
  CareerConversationItem,
  CareerConversationDetail,
  ResumeItem,
} from '../../types';
import { Card, CardHeader, CardBody } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Modal } from '../common/Modal';

interface CandidateCareerAssistantViewProps {
  conversations: CareerConversationItem[];
  activeConversation: CareerConversationDetail | null;
  conversationsLoading: boolean;
  activeConvLoading: boolean;
  messageInput: string;
  setMessageInput: (val: string) => void;
  onSendMessage: () => Promise<void>;
  sendingMessage: boolean;
  chatError: string;
  onSelectConversation: (id: string) => Promise<void>;
  resumes: ResumeItem[];
  onCreateConversation: (data: {
    resume_id?: string;
    target_role?: string;
    conversation_purpose: string;
    title?: string;
    initial_message?: string;
  }) => Promise<void>;
  creatingConv: boolean;
}

export function CandidateCareerAssistantView({
  conversations,
  activeConversation,
  conversationsLoading,
  activeConvLoading,
  messageInput,
  setMessageInput,
  onSendMessage,
  sendingMessage,
  chatError,
  onSelectConversation,
  resumes,
  onCreateConversation,
  creatingConv,
}: CandidateCareerAssistantViewProps) {
  const [isNewModalOpen, setIsNewModalOpen] = useState(false);
  const [selectedResumeId, setSelectedResumeId] = useState('');
  const [targetRole, setTargetRole] = useState('');
  const [purpose, setPurpose] = useState('CAREER_GUIDANCE');
  const [title, setTitle] = useState('');
  const [initialMsg, setInitialMsg] = useState('');

  const suggestedPrompts = [
    'What system design topics should I prepare for based on my projects?',
    'How does my resume compare against Staff Engineer requirements?',
    'What skills should I highlight to strengthen my backend profile?',
    'Can you conduct a practice behavioural interview with me?',
  ];

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onCreateConversation({
      resume_id: selectedResumeId || undefined,
      target_role: targetRole.trim() || undefined,
      conversation_purpose: purpose,
      title: title.trim() || undefined,
      initial_message: initialMsg.trim() || undefined,
    });
    setIsNewModalOpen(false);
    setTitle('');
    setInitialMsg('');
  };

  return (
    <div className="h-[calc(100vh-140px)] flex flex-col lg:flex-row gap-4 max-w-6xl">
      {/* LEFT: Conversation Threads Sidebar */}
      <div className="w-full lg:w-72 bg-white border border-[#EAE5F2] rounded-2xl flex flex-col p-4 shrink-0">
        <div className="flex items-center justify-between pb-3 border-b border-[#EAE5F2] mb-3">
          <div className="flex items-center gap-2">
            <Bot className="w-4 h-4 text-[#7950D9]" />
            <h3 className="text-xs font-bold text-[#21152F]">Career Threads</h3>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setIsNewModalOpen(true)}
            icon={<Plus className="w-3.5 h-3.5" />}
          >
            New
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
          {conversations.length === 0 ? (
            <div className="text-center py-8 text-xs text-[#766A87]">
              No conversations yet. Start a new career planning thread!
            </div>
          ) : (
            conversations.map((conv) => {
              const isActive = activeConversation?.id === conv.id;
              return (
                <button
                  key={conv.id}
                  onClick={() => onSelectConversation(conv.id)}
                  className={`w-full text-left p-3 rounded-xl text-xs transition-all ${
                    isActive
                      ? 'bg-[#F3EEFF] text-[#7950D9] font-bold border border-[#E7DCFF]'
                      : 'text-[#21152F] hover:bg-[#FAF9FD] border border-transparent'
                  }`}
                >
                  <p className="truncate font-semibold mb-1">{conv.conversation_title}</p>
                  <div className="flex items-center justify-between text-[10px] text-[#766A87]">
                    <span className="truncate max-w-[120px]">{conv.conversation_type}</span>
                    <span>{new Date(conv.created_at).toLocaleDateString()}</span>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* RIGHT: Chat Area */}
      <div className="flex-1 bg-white border border-[#EAE5F2] rounded-2xl flex flex-col overflow-hidden shadow-xs">
        {activeConversation ? (
          <>
            {/* Chat Header */}
            <div className="px-6 py-4 border-b border-[#EAE5F2] bg-[#FAF9FD] flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-[#21152F]">
                    {activeConversation.conversation_title}
                  </h3>
                  <Badge variant="purple" size="sm">
                    {activeConversation.conversation_type}
                  </Badge>
                </div>
                {activeConversation.target_role && (
                  <p className="text-xs text-[#766A87] mt-0.5">
                    Target: {activeConversation.target_role}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-1.5 text-xs text-[#7950D9] bg-[#F3EEFF] px-3 py-1 rounded-full border border-[#E7DCFF]">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Grounded Resume Context</span>
              </div>
            </div>

            {/* Chat Messages Scrollable */}
            <div className="flex-1 p-6 overflow-y-auto space-y-4">
              {activeConversation.messages.map((msg) => {
                const isAssistant = msg.role === 'ASSISTANT';
                return (
                  <div
                    key={msg.id}
                    className={`flex gap-3 max-w-2xl ${
                      isAssistant ? 'mr-auto' : 'ml-auto flex-row-reverse'
                    }`}
                  >
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs font-bold ${
                        isAssistant
                          ? 'bg-[#7950D9] text-white shadow-sm'
                          : 'bg-[#21152F] text-white'
                      }`}
                    >
                      {isAssistant ? <Sparkles className="w-4 h-4" /> : <User className="w-4 h-4" />}
                    </div>

                    <div
                      className={`p-4 rounded-2xl text-xs leading-relaxed ${
                        isAssistant
                          ? 'bg-[#FAF9FD] text-[#21152F] border border-[#EAE5F2]'
                          : 'bg-[#7950D9] text-white shadow-xs'
                      }`}
                    >
                      <div className="whitespace-pre-wrap">{msg.content}</div>

                      {/* Evidence Citations if assistant */}
                      {isAssistant && msg.context_metadata?.evidence_snippets && msg.context_metadata.evidence_snippets.length > 0 && (
                        <div className="mt-3 pt-2 border-t border-[#EAE5F2] text-[11px] text-[#7950D9] space-y-1">
                          <span className="font-semibold block">Resume Evidence References:</span>
                          {msg.context_metadata.evidence_snippets.slice(0, 2).map((snip, sIdx) => (
                            <p key={sIdx} className="italic bg-[#F3EEFF] p-1.5 rounded">
                              "{snip}"
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              {sendingMessage && (
                <div className="flex gap-3 max-w-2xl mr-auto animate-pulse">
                  <div className="w-8 h-8 rounded-full bg-[#7950D9] text-white flex items-center justify-center text-xs">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <div className="p-4 rounded-2xl bg-[#FAF9FD] border border-[#EAE5F2] text-xs text-[#766A87]">
                    Analyzing resume context and composing grounded advice...
                  </div>
                </div>
              )}
            </div>

            {/* Suggested Prompts Pill Row */}
            <div className="px-6 py-2 border-t border-[#EAE5F2] bg-[#FAF9FD] flex items-center gap-2 overflow-x-auto">
              <span className="text-[11px] font-semibold text-[#766A87] shrink-0">Prompts:</span>
              {suggestedPrompts.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => setMessageInput(p)}
                  className="px-2.5 py-1 rounded-full text-[11px] bg-white border border-[#EAE5F2] hover:border-[#7950D9] hover:text-[#7950D9] text-[#21152F] shrink-0 transition-colors"
                >
                  {p}
                </button>
              ))}
            </div>

            {/* Input Box */}
            <div className="p-4 border-t border-[#EAE5F2] bg-white">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (messageInput.trim() && !sendingMessage) onSendMessage();
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  placeholder="Ask your career assistant about your resume, skills, or interview prep..."
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  className="flex-1 px-4 py-2.5 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
                />
                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  isLoading={sendingMessage}
                  disabled={!messageInput.trim()}
                  icon={<Send className="w-4 h-4" />}
                >
                  Send
                </Button>
              </form>
              {chatError && (
                <p className="text-rose-600 text-xs mt-1.5">{chatError}</p>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
            <div className="w-14 h-14 rounded-2xl bg-[#F3EEFF] text-[#7950D9] flex items-center justify-center mb-4">
              <Bot className="w-7 h-7" />
            </div>
            <h3 className="text-base font-bold text-[#21152F] mb-1">Candidate AI Career Assistant</h3>
            <p className="text-xs text-[#766A87] max-w-sm mb-6 leading-relaxed">
              Select an existing thread from the left, or launch a new conversation to get evidence-backed interview coaching.
            </p>
            <Button
              variant="primary"
              size="md"
              onClick={() => setIsNewModalOpen(true)}
              icon={<Plus className="w-4 h-4" />}
            >
              Start New Career Thread
            </Button>
          </div>
        )}
      </div>

      {/* New Conversation Modal */}
      <Modal
        isOpen={isNewModalOpen}
        onClose={() => setIsNewModalOpen(false)}
        title="Start New Career Assistant Conversation"
        description="Ground the conversation with your active resume and target career role."
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[#21152F] mb-1">
              Resume Version to Ground With
            </label>
            <select
              value={selectedResumeId}
              onChange={(e) => setSelectedResumeId(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
            >
              <option value="">No Resume (General Advice)</option>
              {resumes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.original_filename} {r.is_active ? '(Active Default)' : ''}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-[#21152F] mb-1">
                Target Role
              </label>
              <input
                type="text"
                placeholder="e.g. Senior Backend Engineer"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#21152F] mb-1">
                Conversation Purpose
              </label>
              <select
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
              >
                <option value="CAREER_GUIDANCE">Career Guidance</option>
                <option value="SKILL_DEVELOPMENT">Skill Development</option>
                <option value="INTERVIEW_PREP">Interview Preparation</option>
                <option value="RESUME_IMPROVEMENT">Resume Improvement</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#21152F] mb-1">
              Conversation Title
            </label>
            <input
              type="text"
              placeholder="e.g. System Design Prep for FinTech Role"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#21152F] mb-1">
              Initial Question or Query (Optional)
            </label>
            <textarea
              rows={3}
              placeholder="What questions or goals do you want to explore?"
              value={initialMsg}
              onChange={(e) => setInitialMsg(e.target.value)}
              className="w-full p-3 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white resize-none"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="ghost" size="sm" type="button" onClick={() => setIsNewModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={creatingConv}>
              Initialize Thread
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
