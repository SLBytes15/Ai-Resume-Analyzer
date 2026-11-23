import React, { useState } from 'react';
import {
  Bot,
  Send,
  Plus,
  Sparkles,
  Building2,
  ShieldCheck,
  CheckCircle2,
  FileText,
  User,
  Search,
} from 'lucide-react';
import {
  RecruiterAiConversationItem,
  RecruiterAiConversationDetail,
  RecruiterJob,
  Organization,
} from '../../types';
import { Card, CardBody } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Modal } from '../common/Modal';

interface RecruiterAssistantViewProps {
  conversations: RecruiterAiConversationItem[];
  activeConversation: RecruiterAiConversationDetail | null;
  loading: boolean;
  activeLoading: boolean;
  input: string;
  setInput: (val: string) => void;
  onSendMessage: () => Promise<void>;
  sending: boolean;
  error: string;
  onSelectConversation: (id: string) => Promise<void>;
  jobs: RecruiterJob[];
  selectedJobId: string;
  setSelectedJobId: (id: string) => void;
  onCreateConversation: (data: {
    conversation_title?: string;
    conversation_type: string;
    initial_message?: string;
  }) => Promise<void>;
  creating: boolean;
  activeOrg?: Organization;
}

export function RecruiterAssistantView({
  conversations,
  activeConversation,
  loading,
  activeLoading,
  input,
  setInput,
  onSendMessage,
  sending,
  error,
  onSelectConversation,
  jobs,
  selectedJobId,
  setSelectedJobId,
  onCreateConversation,
  creating,
  activeOrg,
}: RecruiterAssistantViewProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [convType, setConvType] = useState('GENERAL_HIRING');
  const [initialMsg, setInitialMsg] = useState('');

  const suggestedQueries = [
    'Compare the top candidates for Senior API Developer.',
    'Summarize our current recruitment pipeline and bottlenecks.',
    'What are the most commonly demonstrated skills across applicants?',
    'Which candidates demonstrate 3+ years of FastAPI and PostgreSQL?',
  ];

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onCreateConversation({
      conversation_title: title.trim() || undefined,
      conversation_type: convType,
      initial_message: initialMsg.trim() || undefined,
    });
    setIsModalOpen(false);
    setTitle('');
    setInitialMsg('');
  };

  return (
    <div className="h-[calc(100vh-140px)] flex flex-col lg:flex-row gap-4 max-w-6xl">
      {/* LEFT: Conversation History */}
      <div className="w-full lg:w-72 bg-white border border-[#EAE5F2] rounded-2xl flex flex-col p-4 shrink-0">
        <div className="flex items-center justify-between pb-3 border-b border-[#EAE5F2] mb-3">
          <div className="flex items-center gap-2">
            <Bot className="w-4 h-4 text-[#7950D9]" />
            <h3 className="text-xs font-bold text-[#21152F]">Hiring Assistant</h3>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setIsModalOpen(true)}
            icon={<Plus className="w-3.5 h-3.5" />}
          >
            New
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
          {conversations.length === 0 ? (
            <div className="text-center py-8 text-xs text-[#766A87]">
              No conversations yet. Start an inquiry thread.
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

      {/* RIGHT: Chat Thread Area */}
      <div className="flex-1 bg-white border border-[#EAE5F2] rounded-2xl flex flex-col overflow-hidden shadow-xs">
        {activeConversation ? (
          <>
            {/* Header */}
            <div className="px-6 py-4 border-b border-[#EAE5F2] bg-[#FAF9FD] flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-[#21152F]">
                    {activeConversation.conversation_title}
                  </h3>
                  <Badge variant="purple" size="sm">
                    {activeConversation.conversation_type}
                  </Badge>
                </div>
                <p className="text-xs text-[#766A87] mt-0.5">
                  Scoped to: {activeOrg?.name || 'Organization'}
                </p>
              </div>

              {/* Optional Job Focus Selector */}
              <div className="flex items-center gap-2 text-xs">
                <span className="text-[#766A87]">Job Focus:</span>
                <select
                  value={selectedJobId}
                  onChange={(e) => setSelectedJobId(e.target.value)}
                  className="px-2.5 py-1 text-xs rounded-lg border border-[#EAE5F2] bg-white text-[#21152F]"
                >
                  <option value="">All Requisitions</option>
                  {jobs.map((j) => (
                    <option key={j.id} value={j.id}>
                      {j.title}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Messages Scrollable */}
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
                      {isAssistant ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
                    </div>

                    <div
                      className={`p-4 rounded-2xl text-xs leading-relaxed ${
                        isAssistant
                          ? 'bg-[#FAF9FD] text-[#21152F] border border-[#EAE5F2]'
                          : 'bg-[#7950D9] text-white shadow-xs'
                      }`}
                    >
                      <div className="whitespace-pre-wrap">{msg.content}</div>

                      {/* Grounded SQL Evidence Citations */}
                      {isAssistant && msg.context_metadata?.sources_used && msg.context_metadata.sources_used.length > 0 && (
                        <div className="mt-3 pt-2 border-t border-[#EAE5F2] text-[11px] text-[#7950D9] space-y-1">
                          <span className="font-semibold block flex items-center gap-1">
                            <ShieldCheck className="w-3.5 h-3.5" />
                            Grounded Database Sources:
                          </span>
                          <div className="flex flex-wrap gap-1">
                            {msg.context_metadata.sources_used.map((src, sIdx) => (
                              <span key={sIdx} className="px-2 py-0.5 rounded bg-[#F3EEFF] text-[10px]">
                                {src}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              {sending && (
                <div className="flex gap-3 max-w-2xl mr-auto animate-pulse">
                  <div className="w-8 h-8 rounded-full bg-[#7950D9] text-white flex items-center justify-center text-xs">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="p-4 rounded-2xl bg-[#FAF9FD] border border-[#EAE5F2] text-xs text-[#766A87]">
                    Executing safe SQL retrieval and composing hiring intelligence response...
                  </div>
                </div>
              )}
            </div>

            {/* Suggested Queries */}
            <div className="px-6 py-2 border-t border-[#EAE5F2] bg-[#FAF9FD] flex items-center gap-2 overflow-x-auto">
              <span className="text-[11px] font-semibold text-[#766A87] shrink-0">Inquiries:</span>
              {suggestedQueries.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => setInput(q)}
                  className="px-2.5 py-1 rounded-full text-[11px] bg-white border border-[#EAE5F2] hover:border-[#7950D9] hover:text-[#7950D9] text-[#21152F] shrink-0 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>

            {/* Input Box */}
            <div className="p-4 border-t border-[#EAE5F2] bg-white">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (input.trim() && !sending) onSendMessage();
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  placeholder="Ask a hiring intelligence question about applicants, screening scores, or pipeline stats..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  className="flex-1 px-4 py-2.5 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
                />
                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  isLoading={sending}
                  disabled={!input.trim()}
                  icon={<Send className="w-4 h-4" />}
                >
                  Send
                </Button>
              </form>
              {error && <p className="text-rose-600 text-xs mt-1.5">{error}</p>}
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
            <div className="w-14 h-14 rounded-2xl bg-[#F3EEFF] text-[#7950D9] flex items-center justify-center mb-4">
              <Bot className="w-7 h-7" />
            </div>
            <h3 className="text-base font-bold text-[#21152F] mb-1">M9 Recruiter AI Assistant</h3>
            <p className="text-xs text-[#766A87] max-w-sm mb-6 leading-relaxed">
              Query applicant databases safely with organization-isolated SQL retrieval, compare finalists, and analyze recruitment metrics.
            </p>
            <Button
              variant="primary"
              size="md"
              onClick={() => setIsModalOpen(true)}
              icon={<Plus className="w-4 h-4" />}
            >
              Start New Hiring Thread
            </Button>
          </div>
        )}
      </div>

      {/* New Conversation Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Start Recruiter AI Discussion"
        description="Select the focus of your hiring intelligence inquiry."
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[#21152F] mb-1">
              Discussion Title
            </label>
            <input
              type="text"
              placeholder="e.g. Lead API Developer Candidate Review"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#21152F] mb-1">
              Conversation Type
            </label>
            <select
              value={convType}
              onChange={(e) => setConvType(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white"
            >
              <option value="GENERAL_HIRING">General Hiring Inquiries</option>
              <option value="CANDIDATE_COMPARISON">Candidate Comparison</option>
              <option value="SKILL_DISTRIBUTION">Skill Distribution & Insights</option>
              <option value="PIPELINE_STATUS">Recruitment Pipeline Status</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#21152F] mb-1">
              Initial Question (Optional)
            </label>
            <textarea
              rows={3}
              placeholder="Compare candidates and summarize our hiring progress..."
              value={initialMsg}
              onChange={(e) => setInitialMsg(e.target.value)}
              className="w-full p-3 text-xs rounded-xl border border-[#EAE5F2] bg-[#FAF9FD] text-[#21152F] focus:outline-none focus:border-[#7950D9] focus:bg-white resize-none"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="ghost" size="sm" type="button" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={creating}>
              Create Discussion Thread
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
