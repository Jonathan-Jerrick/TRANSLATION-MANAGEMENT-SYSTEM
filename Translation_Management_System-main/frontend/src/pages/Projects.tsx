import React, { useMemo } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import {
  Plus,
  Search,
  Calendar,
  FileText,
} from 'lucide-react';
import { apiService } from '../services/api';
import { useStore, Project as ProjectType, ProjectDraft } from '../store/useStore';
import LanguagePicker, { LocaleOption } from '../components/projects/LanguagePicker';
import { usePageState } from '../hooks/usePageState';

const DEFAULT_VIEW_STATE = {
  searchTerm: '',
  filterStatus: 'all',
  showCreateModal: false,
};

const statuses = ['intake', 'in_progress', 'completed'] as const;

const validateProjectDraft = (draft: ProjectDraft) => {
  if (!draft.name.trim()) {
    toast.error('Project name is required.');
    return false;
  }

  if (!draft.sector) {
    toast.error('Select a sector for the project.');
    return false;
  }

  if (!draft.source_locale) {
    toast.error('Select a source language.');
    return false;
  }

  if (!draft.target_locales.length) {
    toast.error('Select at least one target language.');
    return false;
  }

  if (draft.target_locales.includes(draft.source_locale)) {
    toast.error('Source and target languages must be different.');
    return false;
  }

  if (!draft.content.trim()) {
    toast.error('Add content to translate.');
    return false;
  }

  return true;
};

const buildProjectPayload = (draft: ProjectDraft) => ({
  name: draft.name.trim(),
  sector: draft.sector,
  source_locale: draft.source_locale,
  target_locales: draft.target_locales,
  content: draft.content.trim(),
  description: draft.description?.trim() || undefined,
  client: draft.client?.trim() || undefined,
  priority: draft.priority,
  due_date: draft.due_date || undefined,
  metadata: {
    workflow_mode: draft.workflow_mode,
  },
});

const Projects: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [viewState, setViewState] = usePageState('projects:view', DEFAULT_VIEW_STATE);
  const { searchTerm, filterStatus, showCreateModal } = viewState;

  const user = useStore((state) => state.user);
  const isAuthenticated = useStore((state) => state.isAuthenticated);
  const setCurrentProject = useStore((state) => state.setCurrentProject);
  const projectDraft = useStore((state) => state.projectDraft);
  const setProjectDraft = useStore((state) => state.setProjectDraft);
  const resetProjectDraft = useStore((state) => state.resetProjectDraft);

  const canManage = user?.role === 'manager' || user?.role === 'admin';

  const { data: projects = [], isLoading } = useQuery<ProjectType[]>({
    queryKey: ['projects'],
    queryFn: apiService.getProjects,
    enabled: isAuthenticated,
  });

  const { data: locales = [], isLoading: localesLoading } = useQuery<LocaleOption[]>({
    queryKey: ['locales'],
    queryFn: apiService.getLocales,
    staleTime: Infinity,
  });

  const createProjectMutation = useMutation({
    mutationFn: apiService.createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      toast.success('Project created successfully!');
      setViewState({ showCreateModal: false });
      resetProjectDraft();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create project');
    },
  });

  const normalizedSearch = searchTerm.trim().toLowerCase();

  const filteredProjects = useMemo(() => {
    if (!projects) return [];
    return projects.filter((project) => {
      const name = project.name ? project.name.toLowerCase() : '';
      const sector = project.sector ? project.sector.toLowerCase() : '';
      const managerName = project.metadata?.manager_name
        ? String(project.metadata.manager_name).toLowerCase()
        : '';
      const managerEmail = project.metadata?.manager_email
        ? String(project.metadata.manager_email).toLowerCase()
        : '';
      const matchesSearch =
        !normalizedSearch ||
        name.includes(normalizedSearch) ||
        sector.includes(normalizedSearch) ||
        managerName.includes(normalizedSearch) ||
        managerEmail.includes(normalizedSearch);
      const matchesFilter =
        filterStatus === 'all' || project.status === filterStatus;
      return matchesSearch && matchesFilter;
    });
  }, [projects, normalizedSearch, filterStatus]);

  const handleOpenCreateModal = () => {
    if (!localesLoading && locales.length === 0) {
      toast.error('No locales available. Please configure locales first.');
      return;
    }
    setViewState({ showCreateModal: true });
  };

  const handleCloseCreateModal = () => {
    setViewState({ showCreateModal: false });
  };

  const handleLanguageChange = (languages: { source: string; targets: string[] }) => {
    setProjectDraft((draft) => ({
      ...draft,
      source_locale: languages.source,
      target_locales: languages.targets.filter((code) => code !== languages.source),
    }));
  };

  const handleDraftFieldChange = (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>,
  ) => {
    const { name, value } = event.target;
    setProjectDraft((draft) => ({
      ...draft,
      [name]: value,
    }));
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!validateProjectDraft(projectDraft)) {
      return;
    }
    createProjectMutation.mutate(buildProjectPayload(projectDraft));
  };

  const handleNavigateToStudio = (project: ProjectType) => {
    setCurrentProject(project);
    navigate('/studio');
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="status-completed">Completed</span>;
      case 'in_progress':
        return <span className="status-active">In Progress</span>;
      case 'intake':
        return <span className="status-pending">Intake</span>;
      default:
        return <span className="status-pending capitalize">{status}</span>;
    }
  };

  const getPriorityColor = (priority?: string) => {
    switch (priority) {
      case 'critical':
        return 'text-red-600';
      case 'high':
        return 'text-orange-600';
      case 'medium':
        return 'text-yellow-600';
      case 'low':
        return 'text-green-600';
      default:
        return 'text-gray-600';
    }
  };

  if (isLoading || localesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
          <p className="text-gray-600 mt-1">
            Manage your translation projects and track progress.
          </p>
        </div>
        {canManage && (
          <button
            onClick={handleOpenCreateModal}
            className="button button-primary flex items-center"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Project
          </button>
        )}
      </div>

      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <input
            type="text"
            placeholder="Search projects..."
            value={searchTerm}
            onChange={(event) => setViewState({ searchTerm: event.target.value })}
            className="form-input pl-10"
          />
        </div>
        <select
          value={filterStatus}
          onChange={(event) => setViewState({ filterStatus: event.target.value })}
          className="form-select"
        >
          <option value="all">All Status</option>
          {statuses.map((status) => (
            <option key={status} value={status}>
              {status.replace(/_/g, ' ')}
            </option>
          ))}
        </select>
      </div>

      <div className="projects-grid">
        {filteredProjects.map((project) => (
          <div key={project.id} className="project-card">
            <div className="project-card-header">
              <h3 className="project-card-title">{project.name}</h3>
              {getStatusBadge(project.status)}
            </div>

            <div className="space-y-3">
              <div className="flex items-center text-sm text-gray-600">
                <span className="font-medium">Sector:</span>
                <span className="ml-2 capitalize">{project.sector}</span>
              </div>

              <div className="flex items-center text-sm text-gray-600">
                <span className="font-medium">Languages:</span>
                <span className="ml-2">
                  {project.source_locale} → {project.target_locales.join(', ')}
                </span>
              </div>

              {project.metadata?.workflow_mode && (
                <div className="flex items-center text-sm text-gray-600">
                  <span className="font-medium">Workflow:</span>
                  <span className="ml-2 capitalize">
                    {String(project.metadata.workflow_mode).replace(/_/g, ' ')}
                  </span>
                </div>
              )}

              {project.metadata?.manager_name && (
                <div className="flex items-center text-sm text-gray-600">
                  <span className="font-medium">Manager:</span>
                  <span className="ml-2">
                    {String(project.metadata.manager_name)}
                  </span>
                </div>
              )}
              {project.metadata?.manager_email && (
                <div className="flex items-center text-xs text-gray-500">
                  <span>{String(project.metadata.manager_email)}</span>
                </div>
              )}

              {project.priority && (
                <div className="flex items-center text-sm">
                  <span className="font-medium text-gray-600">Priority:</span>
                  <span className={`ml-2 font-medium ${getPriorityColor(project.priority)}`}>
                    {project.priority.toUpperCase()}
                  </span>
                </div>
              )}

              {project.due_date && (
                <div className="flex items-center text-sm text-gray-600">
                  <Calendar className="h-4 w-4 mr-1" />
                  <span>Due: {new Date(project.due_date).toLocaleDateString()}</span>
                </div>
              )}

              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Progress</span>
                  <span className="font-medium">{Math.round(project.progress * 100)}%</span>
                </div>
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${Math.min(project.progress * 100, 100)}%` }}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between pt-2">
                <span className="text-xs text-gray-500">
                  Created: {new Date(project.created_at).toLocaleDateString()}
                </span>
                <div className="flex space-x-2">
                  <button
                    type="button"
                    onClick={() => handleNavigateToStudio(project)}
                    className="text-xs text-primary-600 hover:text-primary-500"
                  >
                    Open in Studio
                  </button>
                  {canManage && (
                    <button
                      type="button"
                      onClick={() => {
                        setProjectDraft({
                          name: project.name ?? '',
                          sector: project.sector ?? '',
                          source_locale: project.source_locale ?? '',
                          target_locales: project.target_locales ?? [],
                          content: '',
                          description: project.metadata?.description ?? '',
                          client: project.metadata?.client ?? '',
                          priority: (project.priority as ProjectDraft['priority']) || 'medium',
                          due_date: project.due_date ?? '',
                          workflow_mode:
                            (project.metadata?.workflow_mode as ProjectDraft['workflow_mode']) ||
                            'human_post_edit',
                        });
                        setViewState({ showCreateModal: true });
                      }}
                      className="text-xs text-primary-600 hover:text-primary-500"
                    >
                      Duplicate
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredProjects.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            <FileText className="h-12 w-12 mx-auto" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No projects found</h3>
          <p className="text-gray-600 mb-4">
            {searchTerm || filterStatus !== 'all'
              ? 'Try adjusting your search or filter criteria.'
              : 'Get started by creating your first project.'}
          </p>
          {canManage && !searchTerm && filterStatus === 'all' && (
            <button
              onClick={handleOpenCreateModal}
              className="button button-primary"
            >
              Create Project
            </button>
          )}
        </div>
      )}

      {canManage && showCreateModal && (
        <div className="modal">
          <div className="modal-content max-w-3xl">
            <div className="modal-header">
              <h2 className="modal-title">Create New Project</h2>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={resetProjectDraft}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Reset form
                </button>
                <button
                  onClick={handleCloseCreateModal}
                  className="close-button"
                  aria-label="Close create project modal"
                >
                  ×
                </button>
              </div>
            </div>
            <div className="modal-body">
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="form-label">Project Name</label>
                    <input
                      name="name"
                      type="text"
                      required
                      value={projectDraft.name}
                      onChange={handleDraftFieldChange}
                      className="form-input"
                      placeholder="Enter project name"
                    />
                  </div>
                  <div>
                    <label className="form-label">Sector</label>
                    <select
                      name="sector"
                      required
                      value={projectDraft.sector}
                      onChange={handleDraftFieldChange}
                      className="form-select"
                    >
                      <option value="">Select sector</option>
                      <option value="government">Government</option>
                      <option value="legal">Legal</option>
                      <option value="bfsi">BFSI</option>
                      <option value="ecommerce">E-Commerce</option>
                      <option value="healthcare">Healthcare</option>
                      <option value="technology">Technology</option>
                    </select>
                  </div>
                </div>

                <LanguagePicker
                  locales={locales}
                  sourceLocale={projectDraft.source_locale}
                  targetLocales={projectDraft.target_locales}
                  onChange={handleLanguageChange}
                  disabled={localesLoading}
                />

                <div>
                  <label className="form-label">Content</label>
                  <textarea
                    name="content"
                    required
                    value={projectDraft.content}
                    onChange={handleDraftFieldChange}
                    className="form-textarea"
                    rows={4}
                    placeholder="Enter content to translate"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="form-label">Description</label>
                    <textarea
                      name="description"
                      value={projectDraft.description}
                      onChange={handleDraftFieldChange}
                      className="form-textarea"
                      rows={2}
                      placeholder="Project description (optional)"
                    />
                  </div>
                  <div>
                    <label className="form-label">Client</label>
                    <input
                      name="client"
                      type="text"
                      value={projectDraft.client}
                      onChange={handleDraftFieldChange}
                      className="form-input"
                      placeholder="Client name (optional)"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="form-label">Priority</label>
                    <select
                      name="priority"
                      value={projectDraft.priority}
                      onChange={handleDraftFieldChange}
                      className="form-select"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="critical">Critical</option>
                    </select>
                  </div>
                  <div>
                    <label className="form-label">Due Date</label>
                    <input
                      name="due_date"
                      type="date"
                      value={projectDraft.due_date}
                      onChange={handleDraftFieldChange}
                      className="form-input"
                    />
                  </div>
                </div>

                <div>
                  <label className="form-label">Workflow Mode</label>
                  <select
                    name="workflow_mode"
                    value={projectDraft.workflow_mode}
                    onChange={handleDraftFieldChange}
                    className="form-select"
                  >
                    <option value="human_post_edit">Human post-edit</option>
                    <option value="human_only">Human only</option>
                    <option value="nmt_first">Hybrid NMT + review</option>
                    <option value="full_llm">Fully automated (LLM)</option>
                  </select>
                </div>

                <div className="modal-footer">
                  <button
                    type="button"
                    onClick={handleCloseCreateModal}
                    className="button button-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createProjectMutation.isPending}
                    className="button button-primary"
                  >
                    {createProjectMutation.isPending ? 'Creating...' : 'Create Project'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Projects;
