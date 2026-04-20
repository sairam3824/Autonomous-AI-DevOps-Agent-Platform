'use client';
import { useEffect, useRef } from 'react';
import type { WebSocketMessage } from '@/types';

interface AgentStreamProps {
  messages: WebSocketMessage[];
  isActive?: boolean;
}

const labels: Record<string, string> = {
  started: 'Started',
  thinking: 'Processing',
  action: 'Action',
  result: 'Result',
  completed: 'Completed',
  error: 'Issue',
  final_result: 'Output',
};

export default function AgentStream({ messages, isActive }: AgentStreamProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="premium-surface rounded-[30px] p-6">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <p className="premium-label">Execution Feed</p>
          <h3 className="mt-1 text-2xl text-[var(--ink)]">Agent Transcript</h3>
        </div>
        <span className="rounded-full bg-white/55 px-3 py-1 text-xs text-[var(--ink-soft)]">
          {isActive ? 'Live' : 'Idle'}
        </span>
      </div>

      <div className="space-y-4">
        {messages.length === 0 && <p className="text-sm text-[var(--ink-soft)]">Agent activity will appear here once you run a task.</p>}

        {messages.map((msg, i) => {
          const content = msg.message || (msg.output ? JSON.stringify(msg.output, null, 2) : '');
          return (
            <div key={i} className="rounded-[24px] bg-white/46 px-4 py-4">
              <div className="mb-2 flex items-center justify-between gap-4">
                <p className="text-sm font-medium text-[var(--ink)]">{labels[msg.type] || msg.type}</p>
                <p className="text-xs text-[var(--ink-soft)]">
                  {msg.timestamp ? new Date(msg.timestamp * 1000).toLocaleTimeString() : ''}
                </p>
              </div>
              <p className="whitespace-pre-wrap text-sm leading-7 text-[var(--ink-soft)]">{content}</p>
            </div>
          );
        })}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
