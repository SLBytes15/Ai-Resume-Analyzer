import  { useState } from 'react';

interface Candidate {
  id: string;
  name: string;
  score: number;
  yoe_status: string;
  matched_skills: string[];
  missing_skills: string[];
  reasoning: string;
}

export default function App() {
  const [jdText, setJdText] = useState('');
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleMatch = async () => {
    if (!jdText.trim()) return;
    setLoading(true);
    setError('');
    
    try {
      // 1. Basic parsing simulation to match your backend model structure requirements
      // Realistically you will map a proper textarea input payload to your FastAPI endpoint model schema
      const mockPayload = {
        jd_id: "UI_REQUEST_" + Date.now(),
        role: "Full Stack Developer", // In V2 you can add an explicit Role field
        skills: jdText.split(',').map(s => s.trim()).filter(Boolean),
        minimum_years: 4
      };

      const response = await fetch('http://127.0.0.1:8000/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockPayload)
      });

      if (!response.ok) throw new Error('API server calculation rejected the mapping schema.');
      const data = await response.json();
      setCandidates(data.candidate || []);
    } catch (err: any) {
      setError(err.message || 'Failed to reach backend engine endpoints.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 font-sans">
      {/* Top Banner Header */}
      <header className="border-b border-slate-800 bg-slate-950/50 backdrop-blur px-8 py-4">
        <h1 className="text-xl font-bold text-indigo-400 tracking-wide">💼 AI Recruiter Assistant</h1>
      </header>

      {/* Main Grid Workspace Dashboard Layout */}
      <main className="max-w-7xl mx-auto p-8 grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* LEFT PANEL: INPUT WORKSPACE */}
        <section className="flex flex-col gap-4 bg-slate-950/40 p-6 rounded-xl border border-slate-800">
          <h2 className="text-lg font-semibold text-slate-200">Parse Requirements</h2>
          <p className="text-sm text-slate-400 -mt-2">
            Paste target technical skills separated by commas to execute cross-matching calculations.
          </p>
          <textarea
            className="w-full h-80 bg-slate-900 border border-slate-700 rounded-lg p-4 text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm placeholder:text-slate-600"
            placeholder="React, Node.js, TypeScript, Express, PostgreSQL, Docker, AWS, REST APIs"
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
          />
          <button
            onClick={handleMatch}
            disabled={loading || !jdText.trim()}
            className="w-full bg-indigo-600 hover:bg-indigo-500 font-semibold py-3 px-4 rounded-lg shadow-lg shadow-indigo-600/20 active:scale-[0.98] transition disabled:opacity-50 disabled:pointer-events-none"
          >
            {loading ? 'Analyzing Vector Space...' : 'Match Candidates 🚀'}
          </button>
          {error && <p className="text-sm text-rose-400 bg-rose-950/30 border border-rose-900/50 p-3 rounded-lg text-center">{error}</p>}
        </section>

        {/* RIGHT PANEL: LIVE SCREENING RESULTS CONTAINER */}
        <section className="flex flex-col gap-4 overflow-y-auto max-h-[calc(100vh-12rem)]">
          <h2 className="text-lg font-semibold text-slate-200">Ranked Matching Pools ({candidates.length})</h2>
          
          {candidates.length === 0 && !loading && (
            <div className="flex flex-col items-center justify-center border-2 border-dashed border-slate-800 rounded-xl h-64 text-slate-500">
              <p>No query generated yet.</p>
              <p className="text-xs">Provide a JD payload sequence on the left to review talent.</p>
            </div>
          )}

          {candidates.map((cand) => (
            <div key={cand.id} className="bg-slate-950/60 border border-slate-800 p-6 rounded-xl hover:border-slate-700 transition flex flex-col gap-4">
              {/* Card Header Row */}
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-bold text-lg text-slate-100">{cand.name}</h3>
                  <span className={`inline-block mt-1 text-xs px-2 py-0.5 rounded font-medium border ${
                    cand.yoe_status.includes('✓') 
                      ? 'bg-emerald-950/50 text-emerald-400 border-emerald-800/60' 
                      : 'bg-amber-950/50 text-amber-400 border-amber-800/60'
                  }`}>
                    {cand.yoe_status}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-2xl font-black text-indigo-400">{cand.score}%</span>
                  <p className="text-[10px] text-slate-500 tracking-wider uppercase font-semibold">Match Confidence</p>
                </div>
              </div>

              {/* Skill Intersection Mapping Grid */}
              <div className="grid grid-cols-2 gap-4 text-sm pt-2 border-t border-slate-900">
                <div>
                  <h4 className="text-xs text-emerald-500 font-bold tracking-wider uppercase mb-1">✓ Matched Skills</h4>
                  <div className="flex flex-wrap gap-1">
                    {cand.matched_skills.map((s, i) => (
                      <span key={i} className="bg-emerald-950/30 text-emerald-300 px-2 py-0.5 rounded text-xs border border-emerald-900/30">{s}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-xs text-slate-500 font-bold tracking-wider uppercase mb-1">✗ Missing Skills</h4>
                  <div className="flex flex-wrap gap-1">
                    {cand.missing_skills.map((s, i) => (
                      <span key={i} className="bg-slate-900 text-slate-400 px-2 py-0.5 rounded text-xs border border-slate-800">{s}</span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Analytical Explanation Insight */}
              <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800/40">
                <h4 className="text-xs text-slate-400 font-semibold mb-1">AI Reasoning Assessment:</h4>
                <p className="text-xs text-slate-300 leading-relaxed italic">"{cand.reasoning}"</p>
              </div>
            </div>
          ))}
        </section>

      </main>
    </div>
  );
}