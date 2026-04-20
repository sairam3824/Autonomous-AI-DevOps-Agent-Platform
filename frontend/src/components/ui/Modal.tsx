'use client';
import { useEffect } from 'react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export default function Modal({ isOpen, onClose, title, children }: ModalProps) {
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-[rgba(61,46,32,0.18)] backdrop-blur-sm" onClick={onClose} />
      <div className="premium-surface-strong relative z-10 w-full max-w-2xl rounded-[36px] p-7">
        <div className="mb-5 flex items-start justify-between">
          <div>
            <p className="premium-label">Workspace</p>
            <h2 className="mt-1 text-3xl text-[var(--ink)]">{title}</h2>
          </div>
          <button onClick={onClose} className="rounded-full bg-white/56 px-4 py-2 text-sm text-[var(--ink-soft)]">
            Close
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
