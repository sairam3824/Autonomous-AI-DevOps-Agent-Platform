'use client';
import { useEffect, useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useProjectStore } from '@/stores/projectStore';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import { Input, Textarea } from '@/components/ui/Input';

export default function ProjectsPage() {
  useAuth();
  const { projects, isLoading, fetchProjects, createProject, deleteProject } = useProjectStore();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [repoUrl, setRepoUrl] = useState('');

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handleCreate = async () => {
    if (!name.trim()) return;
    await createProject(name, description || undefined, repoUrl || undefined);
    setShowCreate(false);
    setName('');
    setDescription('');
    setRepoUrl('');
  };

  return (
    <div className="space-y-8">
      <Card className="rounded-[38px] px-7 py-8 md:px-10">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-3">
            <p className="premium-label">Portfolio</p>
            <h2 className="premium-title">Projects deserve the same calm, premium treatment as the tooling around them.</h2>
            <p className="max-w-3xl text-sm leading-7 text-[var(--ink-soft)]">
              Create and maintain project spaces that anchor logs, pipelines, and agent runs without the noise of a typical admin console.
            </p>
          </div>
          <Button size="lg" onClick={() => setShowCreate(true)}>
            New project
          </Button>
        </div>
      </Card>

      {isLoading && <p className="text-sm text-[var(--ink-soft)]">Loading projects.</p>}

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {projects.map((project) => (
          <Card key={project.id} className="rounded-[34px]">
            <div className="space-y-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="premium-label">Project</p>
                  <h3 className="mt-1 text-3xl text-[var(--ink)]">{project.name}</h3>
                </div>
                <button onClick={() => deleteProject(project.id)} className="text-sm text-[var(--ink-soft)] transition-colors hover:text-[var(--ink)]">
                  Remove
                </button>
              </div>
              <p className="text-sm leading-7 text-[var(--ink-soft)]">{project.description || 'No project description added yet.'}</p>
              <div className="space-y-2 text-sm text-[var(--ink-soft)]">
                <p>{project.repo_url || 'No repository linked'}</p>
                <p>Created {new Date(project.created_at).toLocaleDateString()}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {projects.length === 0 && !isLoading && (
        <Card className="rounded-[38px] text-center">
          <p className="premium-label">Portfolio</p>
          <h3 className="mt-2 text-3xl text-[var(--ink)]">No projects yet</h3>
          <p className="mx-auto mt-3 max-w-xl text-sm leading-7 text-[var(--ink-soft)]">
            Start by creating a project space. It will become the home for logs, pipelines, and agent runs.
          </p>
          <Button className="mt-6" onClick={() => setShowCreate(true)}>
            Create your first project
          </Button>
        </Card>
      )}

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Create Project">
        <div className="space-y-4">
          <Input label="Project name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Production platform" required />
          <Textarea label="Description" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="A concise summary of this environment or initiative." rows={4} />
          <Input label="Repository URL" value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} placeholder="https://github.com/your-org/repo" />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" onClick={() => setShowCreate(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate}>Create project</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
