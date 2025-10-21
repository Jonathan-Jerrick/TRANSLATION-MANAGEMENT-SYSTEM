export interface ActivityEntry {
  id: string;
  message: string;
  created_at: string;
  category: string;
}

export interface DeadlineEntry {
  project_id: string;
  project_name: string;
  due_date: string;
  priority?: string;
}

export interface DashboardSummary {
  active_projects: number;
  pending_reviews: number;
  monthly_earnings: number;
  words_translated: number;
  recent_activity: ActivityEntry[];
  upcoming_deadlines: DeadlineEntry[];
}

export interface WorkflowStep {
  name: string;
  automated: boolean;
  assignee: string;
  status: 'pending' | 'in_progress' | 'completed';
}

export interface TranslationSegment {
  id: string;
  source_text: string;
  target_locale: string;
  tm_suggestion?: string;
  tm_score?: number;
  nmt_suggestion?: string;
  post_edit?: string;
  reviewer_notes?: string;
  risk_level?: 'low' | 'medium' | 'high';
  quality_estimate?: number;
  qa_flags: string[];
  term_hits: string[];
}

export interface Job {
  id: string;
  content_id?: string;
  connector_id?: string | null;
  name?: string;
  client?: string;
  sector: string;
  source_locale: string;
  target_locales: string[];
  progress: number;
  status: 'intake' | 'in_progress' | 'completed';
  due_date?: string;
  estimated_word_count?: number;
  budget?: number;
  priority?: string;
  workflow: WorkflowStep[];
  segments: TranslationSegment[];
  metadata: Record<string, string>;
}

export interface TranslationMemoryEntry {
  id: string;
  source_text: string;
  translated_text: string;
  usage_count: number;
}

export interface TermEntry {
  id: string;
  term: string;
  translation: string;
  notes?: string;
}

export interface QAInsight {
  title: string;
  message: string;
  severity: 'low' | 'medium' | 'high';
}

export interface StudioSnapshot {
  project_id: string;
  project_name: string;
  source_locale: string;
  target_locale: string;
  sector: string;
  segments: TranslationSegment[];
  translation_memory: TranslationMemoryEntry[];
  term_base: TermEntry[];
  qa_insights: QAInsight[];
  workflow: WorkflowStep[];
  progress: number;
}

export interface EarningsPoint {
  label: string;
  earnings: number;
  words: number;
  projects: number;
}

export interface LanguagePairPerformance {
  pair: string;
  value: number;
}

export interface TimeTrackingPoint {
  label: string;
  hours: number;
}

export interface TimeTrackingAnalysis {
  total_hours: number;
  breakdown: Record<string, number>;
  daily_average: number;
  trend: TimeTrackingPoint[];
}

export interface AnalyticsOverview {
  total_earnings: number;
  words_translated: number;
  projects_completed: number;
  average_rating: number;
  earnings_trend: EarningsPoint[];
  language_pair_performance: LanguagePairPerformance[];
  time_tracking: TimeTrackingAnalysis;
}

export interface Vendor {
  id: string;
  name: string;
  rating: number;
  sectors: string[];
  locales: string[];
  contact_email: string;
  active: boolean;
}
