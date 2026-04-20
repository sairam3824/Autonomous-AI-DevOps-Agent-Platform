'use client';
import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { agentsApi } from '@/lib/api';
import { AGENT_TYPES } from '@/lib/constants';
import AgentStream from '@/components/AgentStream';
import Button from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Input';
import Tabs from '@/components/ui/Tabs';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import type { AgentType, WebSocketMessage, AgentRun } from '@/types';

export default function AgentsPage() {
  useAuth();
  const [activeAgent, setActiveAgent] = useState<AgentType>('heal');
  const [input, setInput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [result, setResult] = useState<AgentRun | null>(null);
  const [history, setHistory] = useState<AgentRun[]>([]);

  const getInputData = (): Record<string, unknown> => {
    if (activeAgent === 'heal') return { logs: input, error_description: input };
    if (activeAgent === 'pipeline') return { action: 'analyze', yaml_content: input, platform: 'github_actions' };
    return { config_type: 'docker_compose', app_description: input };
  };

  const runAgent = async () => {
    if (!input.trim()) return;
    setIsRunning(true);
    setMessages([
      { type: 'started', message: `Running ${activeAgent} workflow`, timestamp: Date.now() / 1000 },
      { type: 'thinking', message: 'Preparing reasoning context', timestamp: Date.now() / 1000 },
    ]);
    setResult(null);

    try {
      const { data } = await agentsApi.run({ agent_type: activeAgent, input_data: getInputData() });
      setResult(data);
      setHistory((prev) => [data, ...prev]);
      setMessages((prev) => [
        ...prev,
        { type: 'result', message: `Completed in ${data.execution_time_ms}ms`, timestamp: Date.now() / 1000 },
        { type: 'completed', message: data.status === 'completed' ? 'Execution finished' : `Failed: ${data.error_message}`, timestamp: Date.now() / 1000 },
      ]);
    } catch (err: unknown) {
      setMessages((prev) => [...prev, { type: 'error', message: String(err), timestamp: Date.now() / 1000 }]);
    }
    setIsRunning(false);
  };

  const tabs = AGENT_TYPES.map((a) => ({ id: a.id, label: a.label.replace(' Agent', '') }));
  const placeholders: Record<AgentType, string> = {
    heal: 'Paste Kubernetes or Docker failures, incident notes, or error excerpts.',
    pipeline: 'Paste workflow YAML or CI/CD logic for review.',
    infra: 'Describe the system you want provisioned or generated.',
  };

  return (
    <div className="space-y-8">
      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(320px,0.85fr)]">
        <Card className="rounded-[38px]">
          <div className="space-y-5">
            <div>
              <p className="premium-label">Agent workspace</p>
              <h2 className="premium-title">Focused execution without control-panel noise.</h2>
            </div>
            <p className="max-w-3xl text-sm leading-7 text-[var(--ink-soft)]">
              Choose the agent discipline, provide context, and let the system respond with structured output and a clear execution transcript.
            </p>
            <Tabs tabs={tabs} activeTab={activeAgent} onChange={(id) => setActiveAgent(id as AgentType)} />
          </div>
        </Card>

        <Card className="rounded-[38px]">
          <p className="premium-label">Available disciplines</p>
          <div className="mt-4 space-y-3">
            {AGENT_TYPES.map((agent) => (
              <div key={agent.id} className="rounded-[24px] bg-white/48 px-4 py-4">
                <p className="text-base font-semibold text-[var(--ink)]">{agent.label}</p>
                <p className="mt-2 text-sm leading-7 text-[var(--ink-soft)]">{agent.description}</p>
              </div>
            ))}
          </div>
        </Card>
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,0.95fr)]">
        <div className="space-y-6">
          <Card className="rounded-[38px]">
            <div className="space-y-4">
              <Textarea label="Context" value={input} onChange={(e) => setInput(e.target.value)} placeholder={placeholders[activeAgent]} rows={9} />
              <div className="flex flex-wrap gap-3">
                <Button size="lg" onClick={runAgent} isLoading={isRunning}>
                  Run {AGENT_TYPES.find((a) => a.id === activeAgent)?.label}
                </Button>
                <Button
                  size="lg"
                  variant="secondary"
                  onClick={() => {
                    setInput('');
                    setMessages([]);
                    setResult(null);
                  }}
                >
                  Clear session
                </Button>
              </div>
            </div>
          </Card>

          <AgentStream messages={messages} isActive={isRunning} />
        </div>

        <div className="space-y-6">
          {result?.output_data && (
            <Card className="rounded-[38px]">
              <p className="premium-label">Structured output</p>
              <div className="mt-4 rounded-[26px] bg-white/44 p-4">
                <pre className="max-h-[28rem] overflow-x-auto whitespace-pre-wrap text-sm leading-7 text-[var(--ink-soft)]">
                  {JSON.stringify(result.output_data, null, 2)}
                </pre>
              </div>
            </Card>
          )}

          <Card className="rounded-[38px]">
            <p className="premium-label">Recent runs</p>
            <div className="mt-4 space-y-3">
              {history.length === 0 && <p className="text-sm text-[var(--ink-soft)]">No agent runs yet in this session.</p>}
              {history.map((run) => (
                <div key={run.id} className="flex items-center justify-between rounded-[24px] bg-white/46 px-4 py-4">
                  <div>
                    <p className="text-sm font-semibold capitalize text-[var(--ink)]">{run.agent_type}</p>
                    <p className="text-xs text-[var(--ink-soft)]">{run.execution_time_ms}ms</p>
                  </div>
                  <Badge variant={run.status === 'completed' ? 'success' : run.status === 'failed' ? 'error' : 'neutral'}>
                    {run.status}
                  </Badge>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </section>
    </div>
  );
}
