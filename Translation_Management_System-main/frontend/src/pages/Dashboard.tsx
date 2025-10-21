import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../services/api';
import { useStore } from '../store/useStore';
import { 
  Users, 
  FileText, 
  Clock, 
  TrendingUp,
  Activity,
  Calendar,
  DollarSign
} from 'lucide-react';

const Dashboard: React.FC = () => {
  const { user } = useStore();

  const { data: dashboardData, isLoading: dashboardLoading } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: apiService.getDashboardSummary,
  });

  const { data: analyticsData, isLoading: analyticsLoading } = useQuery({
    queryKey: ['analytics-summary'],
    queryFn: apiService.getAnalyticsSummary,
  });

  if (dashboardLoading || analyticsLoading) {
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
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.full_name || user?.username}!
          </h1>
          <p className="text-gray-600 mt-1">
            Here's what's happening with your translation projects.
          </p>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <Activity className="h-4 w-4" />
          <span>Last updated: {new Date().toLocaleTimeString()}</span>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="dashboard-grid">
        <div className="metric-card">
          <div className="metric-card-header">
            <div className="flex items-center">
              <FileText className="h-8 w-8 text-blue-600" />
              <div className="ml-3">
                <p className="metric-card-title">Active Projects</p>
                <p className="metric-card-value">{dashboardData?.active_projects || 0}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-card-header">
            <div className="flex items-center">
              <Clock className="h-8 w-8 text-yellow-600" />
              <div className="ml-3">
                <p className="metric-card-title">Pending Reviews</p>
                <p className="metric-card-value">{dashboardData?.pending_reviews || 0}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-card-header">
            <div className="flex items-center">
              <DollarSign className="h-8 w-8 text-green-600" />
              <div className="ml-3">
                <p className="metric-card-title">Monthly Earnings</p>
                <p className="metric-card-value">${dashboardData?.monthly_earnings || 0}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-card-header">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-purple-600" />
              <div className="ml-3">
                <p className="metric-card-title">Words Translated</p>
                <p className="metric-card-value">{dashboardData?.words_translated || 0}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="activity-feed">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
          <div className="space-y-4">
            {dashboardData?.recent_activity?.map((activity: any) => (
              <div key={activity.id} className="activity-item">
                <p className="activity-message">{activity.message}</p>
                <p className="activity-time">
                  {new Date(activity.created_at).toLocaleString()}
                </p>
              </div>
            )) || (
              <p className="text-gray-500 text-center py-4">No recent activity</p>
            )}
          </div>
        </div>

        {/* Upcoming Deadlines */}
        <div className="activity-feed">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Upcoming Deadlines</h3>
          <div className="space-y-4">
            {dashboardData?.upcoming_deadlines?.map((deadline: any) => (
              <div key={deadline.project_id} className="activity-item">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{deadline.project_name}</p>
                    <p className="text-sm text-gray-500">
                      Due: {new Date(deadline.due_date).toLocaleDateString()}
                    </p>
                  </div>
                  <span className={`badge ${
                    deadline.priority === 'high' ? 'danger' : 
                    deadline.priority === 'medium' ? 'warning' : 'success'
                  }`}>
                    {deadline.priority || 'normal'}
                  </span>
                </div>
              </div>
            )) || (
              <p className="text-gray-500 text-center py-4">No upcoming deadlines</p>
            )}
          </div>
        </div>
      </div>

      {/* Analytics Overview */}
      {analyticsData && (
        <div className="analytics-chart">
          <h3 className="analytics-chart-title">Analytics Overview</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">
                {analyticsData.total_connectors || 0}
              </p>
              <p className="text-sm text-gray-600">Total Connectors</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">
                {analyticsData.completed_jobs || 0}
              </p>
              <p className="text-sm text-gray-600">Completed Jobs</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">
                {analyticsData.average_mtqe ? `${analyticsData.average_mtqe.toFixed(1)}%` : 'N/A'}
              </p>
              <p className="text-sm text-gray-600">Average Quality</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;