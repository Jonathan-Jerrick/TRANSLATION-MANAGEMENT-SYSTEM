import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../services/api';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { 
  TrendingUp, 
  DollarSign, 
  Clock, 
  Target,
  Users,
  FileText,
  Award
} from 'lucide-react';

const Analytics: React.FC = () => {
  const { data: analyticsData, isLoading: analyticsLoading } = useQuery({
    queryKey: ['analytics-summary'],
    queryFn: apiService.getAnalyticsSummary,
  });

  const { data: overviewData, isLoading: overviewLoading } = useQuery({
    queryKey: ['analytics-overview'],
    queryFn: apiService.getAnalyticsOverview,
  });

  if (analyticsLoading || overviewLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner" />
      </div>
    );
  }

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600 mt-1">
            Track your translation performance and productivity metrics.
          </p>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <Clock className="h-4 w-4" />
          <span>Last updated: {new Date().toLocaleTimeString()}</span>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="dashboard-grid">
        <div className="metric-card">
          <div className="metric-card-header">
            <div className="flex items-center">
              <DollarSign className="h-8 w-8 text-green-600" />
              <div className="ml-3">
                <p className="metric-card-title">Total Earnings</p>
                <p className="metric-card-value">
                  ${overviewData?.total_earnings?.toLocaleString() || '0'}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-card-header">
            <div className="flex items-center">
              <FileText className="h-8 w-8 text-blue-600" />
              <div className="ml-3">
                <p className="metric-card-title">Words Translated</p>
                <p className="metric-card-value">
                  {overviewData?.words_translated?.toLocaleString() || '0'}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-card-header">
            <div className="flex items-center">
              <Target className="h-8 w-8 text-purple-600" />
              <div className="ml-3">
                <p className="metric-card-title">Projects Completed</p>
                <p className="metric-card-value">
                  {overviewData?.projects_completed || '0'}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-card-header">
            <div className="flex items-center">
              <Award className="h-8 w-8 text-yellow-600" />
              <div className="ml-3">
                <p className="metric-card-title">Average Rating</p>
                <p className="metric-card-value">
                  {overviewData?.average_rating?.toFixed(1) || '0.0'}/5.0
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Earnings Trend */}
        <div className="analytics-chart">
          <h3 className="analytics-chart-title">Earnings Trend</h3>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={overviewData?.earnings_trend || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" />
                <YAxis />
                <Tooltip 
                  formatter={(value: any) => [`$${value}`, 'Earnings']}
                  labelFormatter={(label) => `Week: ${label}`}
                />
                <Line 
                  type="monotone" 
                  dataKey="earnings" 
                  stroke="#3B82F6" 
                  strokeWidth={2}
                  dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Language Pair Performance */}
        <div className="analytics-chart">
          <h3 className="analytics-chart-title">Language Pair Performance</h3>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={overviewData?.language_pair_performance || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ pair, value }) => `${pair}: ${value}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {(overviewData?.language_pair_performance || []).map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Time Tracking Analysis */}
      {overviewData?.time_tracking && (
        <div className="analytics-chart">
          <h3 className="analytics-chart-title">Time Tracking Analysis</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="text-center">
              <p className="text-3xl font-bold text-gray-900">
                {overviewData.time_tracking.total_hours.toFixed(1)}h
              </p>
              <p className="text-sm text-gray-600">Total Hours</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-gray-900">
                {overviewData.time_tracking.daily_average.toFixed(1)}h
              </p>
              <p className="text-sm text-gray-600">Daily Average</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-gray-900">
                {Object.keys(overviewData.time_tracking.breakdown).length}
              </p>
              <p className="text-sm text-gray-600">Active Projects</p>
            </div>
          </div>
          
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={overviewData.time_tracking.trend || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" />
                <YAxis />
                <Tooltip 
                  formatter={(value: any) => [`${value}h`, 'Hours']}
                  labelFormatter={(label) => `Week: ${label}`}
                />
                <Bar dataKey="hours" fill="#10B981" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Sector Breakdown */}
      {analyticsData?.sector_breakdown && (
        <div className="analytics-chart">
          <h3 className="analytics-chart-title">Sector Breakdown</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(analyticsData.sector_breakdown).map(([sector, data]: [string, any]) => (
              <div key={sector} className="bg-white p-4 rounded-lg border border-gray-200">
                <h4 className="font-semibold text-gray-900 capitalize mb-2">{sector}</h4>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Projects:</span>
                    <span className="font-medium">{data.projects || 0}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Words:</span>
                    <span className="font-medium">{data.words?.toLocaleString() || 0}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Revenue:</span>
                    <span className="font-medium">${data.revenue?.toLocaleString() || 0}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Translator Productivity */}
      {analyticsData?.translator_productivity && (
        <div className="analytics-chart">
          <h3 className="analytics-chart-title">Translator Productivity</h3>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={Object.entries(analyticsData.translator_productivity).map(([name, productivity]) => ({
                name,
                productivity
              }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip 
                  formatter={(value: any) => [`${value} words/hour`, 'Productivity']}
                />
                <Bar dataKey="productivity" fill="#8B5CF6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Quality Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="analytics-chart">
          <h3 className="analytics-chart-title">Average Quality Score</h3>
          <div className="text-center">
            <p className="text-4xl font-bold text-green-600">
              {analyticsData?.average_mtqe?.toFixed(1) || '0.0'}%
            </p>
            <p className="text-sm text-gray-600 mt-2">Machine Translation Quality</p>
          </div>
        </div>

        <div className="analytics-chart">
          <h3 className="analytics-chart-title">Total Jobs</h3>
          <div className="text-center">
            <p className="text-4xl font-bold text-blue-600">
              {analyticsData?.total_jobs || '0'}
            </p>
            <p className="text-sm text-gray-600 mt-2">All Time</p>
          </div>
        </div>

        <div className="analytics-chart">
          <h3 className="analytics-chart-title">Completion Rate</h3>
          <div className="text-center">
            <p className="text-4xl font-bold text-purple-600">
              {analyticsData?.total_jobs > 0 
                ? Math.round((analyticsData.completed_jobs / analyticsData.total_jobs) * 100)
                : 0}%
            </p>
            <p className="text-sm text-gray-600 mt-2">Jobs Completed</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;