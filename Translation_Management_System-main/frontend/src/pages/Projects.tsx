import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../services/api';
import { toast } from 'react-hot-toast';
import { 
  Plus, 
  Search, 
  Filter, 
  Calendar,
  User,
  Clock,
  CheckCircle,
  AlertCircle,
  FileText
} from 'lucide-react';

interface Project {
  id: string;
  name: string;
  sector: string;
  source_locale: string;
  target_locales: string[];
  status: string;
  progress: number;
  created_at: string;
  due_date?: string;
  priority?: string;
  assigned_vendor_id?: string;
  assigned_user_id?: string;
}

const Projects: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [filterStatus, setFilterStatus] = useState('all');
  const queryClient = useQueryClient();

  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: apiService.getProjects,
  });

  const createProjectMutation = useMutation({
    mutationFn: apiService.createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      toast.success('Project created successfully!');
      setShowCreateModal(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create project');
    },
  });

  const filteredProjects = projects?.filter((project: Project) => {
    const matchesSearch = project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         project.sector.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || project.status === filterStatus;
    return matchesSearch && matchesFilter;
  }) || [];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="status-completed">Completed</span>;
      case 'in_progress':
        return <span className="status-active">In Progress</span>;
      case 'intake':
        return <span className="status-pending">Intake</span>;
      default:
        return <span className="status-pending">{status}</span>;
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
          <p className="text-gray-600 mt-1">
            Manage your translation projects and track progress.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="button button-primary flex items-center"
        >
          <Plus className="h-4 w-4 mr-2" />
          New Project
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <input
            type="text"
            placeholder="Search projects..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="form-input pl-10"
          />
        </div>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="form-select"
        >
          <option value="all">All Status</option>
          <option value="intake">Intake</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
        </select>
      </div>

      {/* Projects Grid */}
      <div className="projects-grid">
        {filteredProjects.map((project: Project) => (
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
                    style={{ width: `${project.progress * 100}%` }}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between pt-2">
                <span className="text-xs text-gray-500">
                  Created: {new Date(project.created_at).toLocaleDateString()}
                </span>
                <div className="flex space-x-2">
                  <button className="text-xs text-primary-600 hover:text-primary-500">
                    View Details
                  </button>
                  <button className="text-xs text-primary-600 hover:text-primary-500">
                    Edit
                  </button>
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
              : 'Get started by creating your first project.'
            }
          </p>
          {!searchTerm && filterStatus === 'all' && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="button button-primary"
            >
              Create Project
            </button>
          )}
        </div>
      )}

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="modal">
          <div className="modal-content">
            <div className="modal-header">
              <h2 className="modal-title">Create New Project</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="close-button"
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const formData = new FormData(e.target as HTMLFormElement);
                  const projectData = {
                    name: formData.get('name') as string,
                    sector: formData.get('sector') as string,
                    source_locale: formData.get('source_locale') as string,
                    target_locales: (formData.get('target_locales') as string).split(',').map(l => l.trim()),
                    content: formData.get('content') as string,
                    description: formData.get('description') as string,
                    priority: formData.get('priority') as string,
                    due_date: formData.get('due_date') as string,
                  };
                  createProjectMutation.mutate(projectData);
                }}
                className="space-y-4"
              >
                <div>
                  <label className="form-label">Project Name</label>
                  <input
                    name="name"
                    type="text"
                    required
                    className="form-input"
                    placeholder="Enter project name"
                  />
                </div>
                <div>
                  <label className="form-label">Sector</label>
                  <select name="sector" required className="form-select">
                    <option value="">Select sector</option>
                    <option value="government">Government</option>
                    <option value="legal">Legal</option>
                    <option value="bfsi">BFSI</option>
                    <option value="ecommerce">E-Commerce</option>
                    <option value="healthcare">Healthcare</option>
                    <option value="technology">Technology</option>
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="form-label">Source Language</label>
                    <select name="source_locale" required className="form-select">
                      <option value="">Select language</option>
                      <option value="en">English</option>
                      <option value="es">Spanish</option>
                      <option value="fr">French</option>
                      <option value="de">German</option>
                      <option value="it">Italian</option>
                      <option value="pt">Portuguese</option>
                      <option value="ru">Russian</option>
                      <option value="zh">Chinese</option>
                      <option value="ja">Japanese</option>
                      <option value="ko">Korean</option>
                    </select>
                  </div>
                  <div>
                    <label className="form-label">Target Languages</label>
                    <input
                      name="target_locales"
                      type="text"
                      required
                      className="form-input"
                      placeholder="en, es, fr (comma separated)"
                    />
                  </div>
                </div>
                <div>
                  <label className="form-label">Content</label>
                  <textarea
                    name="content"
                    required
                    className="form-textarea"
                    rows={4}
                    placeholder="Enter content to translate"
                  />
                </div>
                <div>
                  <label className="form-label">Description</label>
                  <textarea
                    name="description"
                    className="form-textarea"
                    rows={2}
                    placeholder="Project description (optional)"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="form-label">Priority</label>
                    <select name="priority" className="form-select">
                      <option value="low">Low</option>
                      <option value="medium" selected>Medium</option>
                      <option value="high">High</option>
                      <option value="critical">Critical</option>
                    </select>
                  </div>
                  <div>
                    <label className="form-label">Due Date</label>
                    <input
                      name="due_date"
                      type="date"
                      className="form-input"
                    />
                  </div>
                </div>
                <div className="modal-footer">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
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