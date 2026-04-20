'use client';
import { useEffect, useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { logsApi } from '@/lib/api';
import { useProjectStore } from '@/stores/projectStore';
import LogViewer from '@/components/LogViewer';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Select from '@/components/ui/Select';
import { Textarea } from '@/components/ui/Input';
import type { RAGQueryResponse, RAGStats } from '@/types';

export default function LogsPage() {
  useAuth();
  const { projects, fetchProjects, isLoading: isProjectsLoading } = useProjectStore();
  const [logContent, setLogContent] = useState('');
  const [question, setQuestion] = useState('');
  const [ragResult, setRagResult] = useState<RAGQueryResponse | null>(null);
  const [stats, setStats] = useState<RAGStats | null>(null);
  const [isQuerying, setIsQuerying] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [uploadMsg, setUploadMsg] = useState('');
  const [selectedProjectId, setSelectedProjectId] = useState('');

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  useEffect(() => {
    if (!selectedProjectId && projects.length > 0) {
      setSelectedProjectId(String(projects[0].id));
    }
  }, [projects, selectedProjectId]);

  useEffect(() => {
    if (selectedProjectId) {
      loadStats(Number(selectedProjectId));
    } else {
      setStats(null);
    }
  }, [selectedProjectId]);

  const uploadLogs = async () => {
    if (!logContent.trim() || !selectedProjectId) return;
    setIsUploading(true);
    try {
      await logsApi.upload({
        content: logContent,
        source: 'manual-upload',
        project_id: Number(selectedProjectId),
      });
      setUploadMsg('Logs uploaded and indexed successfully.');
      loadStats(Number(selectedProjectId));
    } catch {
      setUploadMsg('Upload failed.');
    }
    setIsUploading(false);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !selectedProjectId) return;
    setIsUploading(true);
    try {
      await logsApi.uploadFile(file, Number(selectedProjectId));
      setUploadMsg(`File "${file.name}" uploaded and indexed.`);
      loadStats(Number(selectedProjectId));
    } catch {
      setUploadMsg('File upload failed.');
    }
    setIsUploading(false);
  };

  const queryRAG = async () => {
    if (!question.trim()) return;
    if (!selectedProjectId) return;
    setIsQuerying(true);
    try {
      const { data } = await logsApi.ragQuery({ question, k: 5, project_id: Number(selectedProjectId) });
      setRagResult(data);
    } catch {
      // ignore
    }
    setIsQuerying(false);
  };

  const indexDocs = async () => {
    if (!selectedProjectId) return;
    setIsIndexing(true);
    try {
      await logsApi.indexDocs(Number(selectedProjectId));
      setUploadMsg('Knowledge base indexed.');
      loadStats(Number(selectedProjectId));
    } catch {
      setUploadMsg('Indexing failed.');
    }
    setIsIndexing(false);
  };

  const loadStats = async (projectId: number) => {
    try {
      const { data } = await logsApi.ragStats(projectId);
      setStats(data);
    } catch {
      // ignore
    }
  };

  return (
    <div className="space-y-8">
      <Card className="rounded-[38px] px-7 py-8 md:px-10">
        <div className="space-y-5">
          <div>
            <p className="premium-label">Operational memory</p>
            <h2 className="premium-title">Upload incident evidence, search for signal, and keep the interface quiet.</h2>
          </div>
          <p className="max-w-3xl text-sm leading-7 text-[var(--ink-soft)]">
            Attach logs to a project, index knowledge, and ask direct operational questions without leaving the workspace.
          </p>
        </div>
      </Card>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]">
        <div className="space-y-6">
          <Card className="rounded-[38px]">
            <div className="space-y-4">
              <Select
                label="Project"
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                options={
                  projects.length > 0
                    ? projects.map((project) => ({ value: String(project.id), label: project.name }))
                    : [{ value: '', label: isProjectsLoading ? 'Loading projects...' : 'No projects available' }]
                }
                disabled={projects.length === 0}
              />
              <Textarea value={logContent} onChange={(e) => setLogContent(e.target.value)} placeholder="Paste logs or incident transcript." rows={8} />
              <div className="flex flex-wrap gap-3">
                <Button onClick={uploadLogs} isLoading={isUploading} disabled={!selectedProjectId}>
                  Upload text
                </Button>
                <label className="inline-flex cursor-pointer rounded-full bg-white/60 px-4 py-2 text-sm text-[var(--ink)] transition-colors hover:bg-white/80">
                  Upload file
                  <input type="file" className="hidden" accept=".log,.txt,.json" onChange={handleFileUpload} disabled={!selectedProjectId} />
                </label>
                <Button variant="secondary" onClick={indexDocs} isLoading={isIndexing}>
                  Index knowledge base
                </Button>
              </div>
              {projects.length === 0 && <p className="text-sm text-[var(--ink-soft)]">Create a project first to attach logs.</p>}
              {uploadMsg && <p className="text-sm text-[var(--accent)]">{uploadMsg}</p>}
            </div>
          </Card>

          <Card className="rounded-[38px]">
            <p className="premium-label">Log review</p>
            <div className="mt-4">
              <LogViewer content={logContent || 'No logs loaded yet.'} />
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="rounded-[38px]">
            <div className="space-y-4">
              <Textarea value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask a question about your logs or DevOps context." rows={4} />
              <div className="flex flex-wrap gap-3">
                <Button onClick={queryRAG} isLoading={isQuerying}>
                  Search memory
                </Button>
                <Button variant="secondary" onClick={() => selectedProjectId && loadStats(Number(selectedProjectId))} disabled={!selectedProjectId}>
                  Refresh stats
                </Button>
              </div>
            </div>
          </Card>

          <Card className="rounded-[38px]">
            <p className="premium-label">Response</p>
            <div className="mt-4 space-y-4">
              {ragResult ? (
                <>
                  <p className="text-sm leading-7 text-[var(--ink-soft)]">{ragResult.answer}</p>
                  <p className="text-sm text-[var(--accent)]">Confidence {(ragResult.confidence * 100).toFixed(1)}%</p>
                  <div className="space-y-3">
                    {ragResult.sources.map((src, i) => (
                      <div key={i} className="rounded-[22px] bg-white/46 px-4 py-4">
                        <p className="text-xs uppercase tracking-[0.24em] text-[var(--ink-soft)]">{src.source}</p>
                        <p className="mt-2 text-sm leading-7 text-[var(--ink-soft)]">{src.text}</p>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p className="text-sm text-[var(--ink-soft)]">Query results will appear here.</p>
              )}
            </div>
          </Card>

          <Card className="rounded-[38px]">
            <p className="premium-label">Vector store</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <MiniStat label="Documents" value={String(stats?.total_documents ?? '-')} />
              <MiniStat label="Chunks" value={String(stats?.total_chunks ?? '-')} />
              <MiniStat label="Index size" value={stats ? `${(stats.index_size_bytes / 1024).toFixed(1)} KB` : '-'} />
              <MiniStat label="Model" value={stats?.embedding_model || '-'} />
            </div>
          </Card>
        </div>
      </section>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[22px] bg-white/46 px-4 py-4">
      <p className="premium-label">{label}</p>
      <p className="mt-2 text-base text-[var(--ink)]">{value}</p>
    </div>
  );
}
