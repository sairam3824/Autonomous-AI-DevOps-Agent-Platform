'use client';
import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { pipelinesApi } from '@/lib/api';
import YAMLEditor from '@/components/YAMLEditor';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import type { PipelineAnalyzeResponse } from '@/types';

const SAMPLE_YAML = `name: CI/CD Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install
      - run: npm test
      - run: npm run build
`;

export default function PipelinesPage() {
  useAuth();
  const [yaml, setYaml] = useState(SAMPLE_YAML);
  const [analysis, setAnalysis] = useState<PipelineAnalyzeResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generateReqs, setGenerateReqs] = useState('');

  const analyze = async () => {
    setIsAnalyzing(true);
    try {
      const { data } = await pipelinesApi.analyze({ yaml_content: yaml, platform: 'github_actions' });
      setAnalysis(data);
    } catch {
      // ignore
    }
    setIsAnalyzing(false);
  };

  const validate = async () => {
    try {
      const { data } = await pipelinesApi.validate({ yaml_content: yaml });
      alert(data.valid ? 'Pipeline syntax looks valid.' : `Validation issues: ${data.errors.join(', ')}`);
    } catch {
      // ignore
    }
  };

  const generate = async () => {
    if (!generateReqs.trim()) return;
    setIsGenerating(true);
    try {
      const { data } = await pipelinesApi.generate({ requirements: generateReqs, platform: 'github_actions' });
      setYaml(data.yaml_content);
    } catch {
      // ignore
    }
    setIsGenerating(false);
  };

  const severityVariant = (sev: string) => (sev === 'critical' ? 'error' : sev === 'warning' ? 'warning' : 'info');

  return (
    <div className="space-y-8">
      <Card className="rounded-[38px] px-7 py-8 md:px-10">
        <div className="space-y-5">
          <div>
            <p className="premium-label">Pipeline atelier</p>
            <h2 className="premium-title">Inspect delivery logic with more focus and less interface noise.</h2>
          </div>
          <p className="max-w-3xl text-sm leading-7 text-[var(--ink-soft)]">
            Analyze existing YAML, validate structure, or generate a new baseline from plain-language requirements.
          </p>
          <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_auto_auto_auto]">
            <Input
              value={generateReqs}
              onChange={(e) => setGenerateReqs(e.target.value)}
              placeholder="Describe the pipeline you want generated."
            />
            <Button onClick={analyze} isLoading={isAnalyzing}>
              Analyze
            </Button>
            <Button variant="secondary" onClick={validate}>
              Validate
            </Button>
            <Button variant="secondary" onClick={generate} isLoading={isGenerating}>
              Generate
            </Button>
          </div>
        </div>
      </Card>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,0.95fr)]">
        <YAMLEditor value={yaml} onChange={setYaml} height="560px" />

        <div className="space-y-6">
          <Card className="rounded-[38px]">
            <p className="premium-label">Assessment</p>
            <h3 className="mt-1 text-3xl text-[var(--ink)]">{analysis ? `${analysis.score}/100` : 'Waiting for review'}</h3>
            <p className="mt-4 text-sm leading-7 text-[var(--ink-soft)]">
              {analysis ? analysis.summary : 'Run an analysis to surface anti-patterns, recommendations, and readiness scoring.'}
            </p>
          </Card>

          <Card className="rounded-[38px]">
            <p className="premium-label">Recommendations</p>
            <div className="mt-4 space-y-3">
              {analysis?.suggestions?.length ? (
                analysis.suggestions.map((suggestion, index) => (
                  <div key={index} className="rounded-[24px] bg-white/46 px-4 py-4">
                    <div className="flex items-center justify-between gap-4">
                      <p className="text-sm font-semibold text-[var(--ink)]">{String(suggestion.title || 'Suggestion')}</p>
                      <Badge variant={severityVariant(String(suggestion.severity || 'info'))}>{String(suggestion.severity || 'info')}</Badge>
                    </div>
                    <p className="mt-2 text-sm leading-7 text-[var(--ink-soft)]">{String(suggestion.description || '')}</p>
                    {typeof suggestion.fix_example === 'string' && suggestion.fix_example.length > 0 && (
                      <pre className="mt-3 whitespace-pre-wrap rounded-[20px] bg-white/52 p-4 text-xs leading-6 text-[var(--ink-soft)]">
                        {suggestion.fix_example}
                      </pre>
                    )}
                  </div>
                ))
              ) : (
                <p className="text-sm text-[var(--ink-soft)]">No recommendations yet. Analyze or generate a pipeline to begin.</p>
              )}
            </div>
          </Card>
        </div>
      </section>
    </div>
  );
}
