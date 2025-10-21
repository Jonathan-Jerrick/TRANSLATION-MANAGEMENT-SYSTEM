import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../services/api';
import { useStore } from '../store/useStore';
import { wsService } from '../services/websocket';
import { toast } from 'react-hot-toast';
import { 
  Save, 
  RefreshCw, 
  CheckCircle, 
  AlertTriangle,
  Users,
  MessageSquare,
  Zap,
  Target
} from 'lucide-react';

interface TranslationSegment {
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
  created_at: string;
  updated_at?: string;
}

const TranslateStudio: React.FC = () => {
  const { currentProject, collaborators, typingUsers } = useStore();
  const [selectedSegment, setSelectedSegment] = useState<TranslationSegment | null>(null);
  const [targetLocale, setTargetLocale] = useState('en');
  const [isTranslating, setIsTranslating] = useState(false);
  const [isEstimatingQuality, setIsEstimatingQuality] = useState(false);
  const queryClient = useQueryClient();

  const { data: segments, isLoading } = useQuery({
    queryKey: ['project-segments', currentProject?.id, targetLocale],
    queryFn: () => apiService.getProjectSegments(currentProject?.id || ''),
    enabled: !!currentProject?.id,
  });

  const { data: studioData } = useQuery({
    queryKey: ['studio-snapshot', currentProject?.id, targetLocale],
    queryFn: () => apiService.getStudioSnapshot(currentProject?.id || '', targetLocale),
    enabled: !!currentProject?.id,
  });

  const updateSegmentMutation = useMutation({
    mutationFn: ({ segmentId, updates }: { segmentId: string; updates: any }) =>
      apiService.updateSegment(currentProject?.id || '', segmentId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-segments'] });
      toast.success('Segment updated successfully!');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update segment');
    },
  });

  const translateMutation = useMutation({
    mutationFn: apiService.translateText,
    onSuccess: (result) => {
      if (selectedSegment) {
        updateSegmentMutation.mutate({
          segmentId: selectedSegment.id,
          updates: { nmt_suggestion: result.translation }
        });
      }
      setIsTranslating(false);
      toast.success('Translation completed!');
    },
    onError: (error: any) => {
      setIsTranslating(false);
      toast.error(error.response?.data?.detail || 'Translation failed');
    },
  });

  const qualityEstimateMutation = useMutation({
    mutationFn: apiService.estimateQuality,
    onSuccess: (result) => {
      if (selectedSegment) {
        updateSegmentMutation.mutate({
          segmentId: selectedSegment.id,
          updates: { 
            quality_estimate: result.quality_score,
            risk_level: result.risk_level
          }
        });
      }
      setIsEstimatingQuality(false);
      toast.success('Quality estimation completed!');
    },
    onError: (error: any) => {
      setIsEstimatingQuality(false);
      toast.error(error.response?.data?.detail || 'Quality estimation failed');
    },
  });

  useEffect(() => {
    if (currentProject?.id) {
      wsService.joinProject(currentProject.id);
    }
    return () => {
      if (currentProject?.id) {
        wsService.leaveProject(currentProject.id);
      }
    };
  }, [currentProject?.id]);

  const handleSegmentSelect = (segment: TranslationSegment) => {
    setSelectedSegment(segment);
  };

  const handleTranslation = async () => {
    if (!selectedSegment) return;
    
    setIsTranslating(true);
    translateMutation.mutate({
      source_text: selectedSegment.source_text,
      source_lang: 'auto',
      target_lang: targetLocale,
      provider: 'openai'
    });
  };

  const handleQualityEstimate = async () => {
    if (!selectedSegment || !selectedSegment.post_edit) return;
    
    setIsEstimatingQuality(true);
    qualityEstimateMutation.mutate({
      source_text: selectedSegment.source_text,
      translated_text: selectedSegment.post_edit,
      source_lang: 'auto',
      target_lang: targetLocale
    });
  };

  const handleSegmentUpdate = (updates: Partial<TranslationSegment>) => {
    if (!selectedSegment) return;
    
    updateSegmentMutation.mutate({
      segmentId: selectedSegment.id,
      updates
    });
    
    // Send real-time update
    wsService.updateSegment(
      currentProject?.id || '', 
      selectedSegment.id, 
      updates.post_edit || ''
    );
  };

  const getRiskColor = (risk?: string) => {
    switch (risk) {
      case 'high': return 'text-red-600';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const getQualityColor = (quality?: number) => {
    if (!quality) return 'text-gray-600';
    if (quality >= 80) return 'text-green-600';
    if (quality >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (!currentProject) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 mb-4">
          <Target className="h-12 w-12 mx-auto" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No project selected</h3>
        <p className="text-gray-600">
          Please select a project to start translating.
        </p>
      </div>
    );
  }

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
          <h1 className="text-3xl font-bold text-gray-900">Translation Studio</h1>
          <p className="text-gray-600 mt-1">
            {currentProject.name} • {currentProject.source_locale} → {targetLocale}
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="collaboration-indicator">
            <Users className="h-4 w-4" />
            <span>{collaborators.length} online</span>
          </div>
          <select
            value={targetLocale}
            onChange={(e) => setTargetLocale(e.target.value)}
            className="form-select"
          >
            {currentProject.target_locales.map(locale => (
              <option key={locale} value={locale}>{locale.toUpperCase()}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="translation-studio">
        {/* Segments List */}
        <div className="segment-editor">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Segments</h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {segments?.map((segment: TranslationSegment) => (
              <div
                key={segment.id}
                onClick={() => handleSegmentSelect(segment)}
                className={`segment cursor-pointer transition-colors ${
                  selectedSegment?.id === segment.id 
                    ? 'ring-2 ring-primary-500 bg-primary-50' 
                    : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm text-gray-900 mb-2">
                      {segment.source_text}
                    </p>
                    {segment.post_edit && (
                      <p className="text-sm text-gray-600 italic">
                        {segment.post_edit}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    {segment.quality_estimate && (
                      <span className={`text-xs font-medium ${getQualityColor(segment.quality_estimate)}`}>
                        {Math.round(segment.quality_estimate)}%
                      </span>
                    )}
                    {segment.risk_level && (
                      <span className={`text-xs ${getRiskColor(segment.risk_level)}`}>
                        {segment.risk_level.toUpperCase()}
                      </span>
                    )}
                    {segment.qa_flags.length > 0 && (
                      <AlertTriangle className="h-4 w-4 text-yellow-500" />
                    )}
                  </div>
                </div>
                
                {typingUsers[segment.id] && typingUsers[segment.id].length > 0 && (
                  <div className="typing-indicator">
                    {typingUsers[segment.id].join(', ')} typing...
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Translation Editor */}
        <div className="segment-editor">
          {selectedSegment ? (
            <>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Translation Editor</h3>
                <div className="flex space-x-2">
                  <button
                    onClick={handleTranslation}
                    disabled={isTranslating}
                    className="button button-primary text-sm"
                  >
                    {isTranslating ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <Zap className="h-4 w-4" />
                    )}
                    {isTranslating ? 'Translating...' : 'AI Translate'}
                  </button>
                  <button
                    onClick={handleQualityEstimate}
                    disabled={isEstimatingQuality || !selectedSegment.post_edit}
                    className="button button-secondary text-sm"
                  >
                    {isEstimatingQuality ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <CheckCircle className="h-4 w-4" />
                    )}
                    {isEstimatingQuality ? 'Analyzing...' : 'Check Quality'}
                  </button>
                </div>
              </div>

              <div className="space-y-4">
                {/* Source Text */}
                <div>
                  <label className="form-label">Source Text</label>
                  <div className="segment-source p-3 rounded-lg">
                    <p className="text-gray-900">{selectedSegment.source_text}</p>
                  </div>
                </div>

                {/* TM Suggestion */}
                {selectedSegment.tm_suggestion && (
                  <div>
                    <label className="form-label">Translation Memory Match</label>
                    <div className="segment-target p-3 rounded-lg">
                      <p className="text-gray-900">{selectedSegment.tm_suggestion}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        Match: {Math.round((selectedSegment.tm_score || 0) * 100)}%
                      </p>
                    </div>
                  </div>
                )}

                {/* NMT Suggestion */}
                {selectedSegment.nmt_suggestion && (
                  <div>
                    <label className="form-label">AI Translation</label>
                    <div className="segment-target p-3 rounded-lg">
                      <p className="text-gray-900">{selectedSegment.nmt_suggestion}</p>
                    </div>
                  </div>
                )}

                {/* Translation Editor */}
                <div>
                  <label className="form-label">Your Translation</label>
                  <textarea
                    value={selectedSegment.post_edit || ''}
                    onChange={(e) => handleSegmentUpdate({ post_edit: e.target.value })}
                    className="segment-textarea"
                    rows={4}
                    placeholder="Enter your translation here..."
                    onFocus={() => {
                      wsService.sendTyping(
                        currentProject.id, 
                        selectedSegment.id, 
                        true
                      );
                    }}
                    onBlur={() => {
                      wsService.sendTyping(
                        currentProject.id, 
                        selectedSegment.id, 
                        false
                      );
                    }}
                  />
                </div>

                {/* Quality Metrics */}
                {(selectedSegment.quality_estimate || selectedSegment.risk_level) && (
                  <div className="grid grid-cols-2 gap-4">
                    {selectedSegment.quality_estimate && (
                      <div>
                        <label className="form-label">Quality Score</label>
                        <div className={`text-2xl font-bold ${getQualityColor(selectedSegment.quality_estimate)}`}>
                          {Math.round(selectedSegment.quality_estimate)}%
                        </div>
                      </div>
                    )}
                    {selectedSegment.risk_level && (
                      <div>
                        <label className="form-label">Risk Level</label>
                        <div className={`text-lg font-semibold ${getRiskColor(selectedSegment.risk_level)}`}>
                          {selectedSegment.risk_level.toUpperCase()}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* QA Flags */}
                {selectedSegment.qa_flags.length > 0 && (
                  <div>
                    <label className="form-label">Quality Issues</label>
                    <div className="space-y-1">
                      {selectedSegment.qa_flags.map((flag, index) => (
                        <div key={index} className="text-sm text-yellow-600 flex items-center">
                          <AlertTriangle className="h-4 w-4 mr-2" />
                          {flag}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Term Hits */}
                {selectedSegment.term_hits.length > 0 && (
                  <div>
                    <label className="form-label">Terminology Matches</label>
                    <div className="flex flex-wrap gap-2">
                      {selectedSegment.term_hits.map((term, index) => (
                        <span key={index} className="tag">
                          {term}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Reviewer Notes */}
                <div>
                  <label className="form-label">Reviewer Notes</label>
                  <textarea
                    value={selectedSegment.reviewer_notes || ''}
                    onChange={(e) => handleSegmentUpdate({ reviewer_notes: e.target.value })}
                    className="form-textarea"
                    rows={2}
                    placeholder="Add notes for reviewers..."
                  />
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-12">
              <div className="text-gray-400 mb-4">
                <MessageSquare className="h-12 w-12 mx-auto" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Select a segment</h3>
              <p className="text-gray-600">
                Choose a segment from the list to start translating.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Translation Memory & Terms Sidebar */}
      {studioData && (
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="activity-feed">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Translation Memory</h3>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {studioData.translation_memory?.map((entry: any) => (
                <div key={entry.id} className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm font-medium text-gray-900">{entry.source_text}</p>
                  <p className="text-sm text-gray-600 mt-1">{entry.translated_text}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Usage: {entry.usage_count} times
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div className="activity-feed">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Terminology Base</h3>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {studioData.term_base?.map((term: any) => (
                <div key={term.id} className="p-3 bg-green-50 rounded-lg">
                  <p className="text-sm font-medium text-gray-900">{term.term}</p>
                  <p className="text-sm text-gray-600 mt-1">{term.translation}</p>
                  {term.notes && (
                    <p className="text-xs text-gray-500 mt-1">{term.notes}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TranslateStudio;