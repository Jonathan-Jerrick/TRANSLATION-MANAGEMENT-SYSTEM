import React, { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import {
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  Users,
  MessageSquare,
  Zap,
  Target,
} from 'lucide-react';
import { apiService } from '../services/api';
import { useStore, TranslationSegment as SegmentType } from '../store/useStore';
import { wsService } from '../services/websocket';
import { usePageState } from '../hooks/usePageState';

const DEFAULT_STUDIO_STATE = {
  targetLocale: 'en',
  selectedSegmentId: null as string | null,
};

const TranslateStudio: React.FC = () => {
  const { currentProject, collaborators, typingUsers } = useStore();
  const setCurrentSegmentStore = useStore((state) => state.setCurrentSegment);
  const [studioState, setStudioState] = usePageState('studio:view', DEFAULT_STUDIO_STATE);
  const { targetLocale, selectedSegmentId } = studioState;
  const [isTranslating, setIsTranslating] = useState(false);
  const [isEstimatingQuality, setIsEstimatingQuality] = useState(false);
  const queryClient = useQueryClient();

  const activeTargetLocale = useMemo(() => {
    if (!currentProject) {
      return targetLocale;
    }
    const availableTargets = currentProject.target_locales;
    if (availableTargets && availableTargets.length > 0) {
      return availableTargets.includes(targetLocale)
        ? targetLocale
        : availableTargets[0];
    }
    return currentProject.source_locale || targetLocale;
  }, [currentProject, targetLocale]);

  useEffect(() => {
    if (!currentProject) {
      setStudioState({ targetLocale: 'en', selectedSegmentId: null });
      return;
    }
    if (activeTargetLocale !== targetLocale) {
      setStudioState({ targetLocale: activeTargetLocale });
    }
  }, [activeTargetLocale, currentProject, setStudioState, targetLocale]);

  const { data: segments = [], isLoading } = useQuery<SegmentType[]>({
    queryKey: ['project-segments', currentProject?.id, activeTargetLocale],
    queryFn: () => apiService.getProjectSegments(currentProject?.id || ''),
    enabled: !!currentProject?.id,
  });

  const { data: studioData } = useQuery({
    queryKey: ['studio-snapshot', currentProject?.id, activeTargetLocale],
    queryFn: () => apiService.getStudioSnapshot(currentProject?.id || '', activeTargetLocale),
    enabled: !!currentProject?.id,
  });

  const selectedSegment = useMemo(() => {
    if (!segments || !selectedSegmentId) {
      return null;
    }
    return segments.find((segment) => segment.id === selectedSegmentId) || null;
  }, [segments, selectedSegmentId]);

  useEffect(() => {
    if (!currentProject?.id) {
      return;
    }
    wsService.joinProject(currentProject.id);
    return () => {
      wsService.leaveProject(currentProject.id);
    };
  }, [currentProject?.id]);

  useEffect(() => {
    if (!segments || segments.length === 0) {
      if (selectedSegmentId) {
        setStudioState({ selectedSegmentId: null });
      }
      setCurrentSegmentStore(null);
      return;
    }

    const existing = segments.find((segment) => segment.id === selectedSegmentId);
    if (!existing) {
      setStudioState({ selectedSegmentId: segments[0].id });
      setCurrentSegmentStore(segments[0]);
    } else {
      setCurrentSegmentStore(existing);
    }
  }, [segments, selectedSegmentId, setCurrentSegmentStore, setStudioState]);

  const updateSegmentMutation = useMutation({
    mutationFn: ({ segmentId, updates }: { segmentId: string; updates: Partial<SegmentType> }) =>
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
          updates: { nmt_suggestion: result.translation },
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
            risk_level: result.risk_level,
          },
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

  const handleSegmentSelect = (segment: SegmentType) => {
    setStudioState({ selectedSegmentId: segment.id });
    setCurrentSegmentStore(segment);
  };

  const handleTranslation = () => {
    if (!selectedSegment) return;

    setIsTranslating(true);
    translateMutation.mutate({
      source_text: selectedSegment.source_text,
      source_lang: 'auto',
      target_lang: activeTargetLocale,
      provider: 'openai',
    });
  };

  const handleQualityEstimate = () => {
    if (!selectedSegment || !selectedSegment.post_edit) return;

    setIsEstimatingQuality(true);
    qualityEstimateMutation.mutate({
      source_text: selectedSegment.source_text,
      translated_text: selectedSegment.post_edit,
      source_lang: 'auto',
      target_lang: activeTargetLocale,
    });
  };

  const handleSegmentUpdate = (updates: Partial<SegmentType>) => {
    if (!selectedSegment) return;

    updateSegmentMutation.mutate({
      segmentId: selectedSegment.id,
      updates,
    });

    if (updates.post_edit !== undefined) {
      wsService.updateSegment(
        currentProject?.id || '',
        selectedSegment.id,
        updates.post_edit || '',
      );
    }
  };

  const getRiskColor = (risk?: string) => {
    switch (risk) {
      case 'high':
        return 'text-red-600';
      case 'medium':
        return 'text-yellow-600';
      case 'low':
        return 'text-green-600';
      default:
        return 'text-gray-600';
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
        <p className="text-gray-600">Please select a project to start translating.</p>
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

  const availableTargetLocales =
    currentProject.target_locales && currentProject.target_locales.length > 0
      ? currentProject.target_locales
      : [currentProject.source_locale];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Translation Studio</h1>
          <p className="text-gray-600 mt-1">
            {currentProject.name} • {currentProject.source_locale} → {activeTargetLocale}
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="collaboration-indicator">
            <Users className="h-4 w-4" />
            <span>{collaborators.length} online</span>
          </div>
          <select
            value={activeTargetLocale}
            onChange={(event) => setStudioState({ targetLocale: event.target.value })}
            className="form-select"
          >
            {availableTargetLocales.map((locale) => (
              <option key={locale} value={locale}>
                {locale.toUpperCase()}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="translation-studio">
        <div className="segment-editor">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Segments</h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {segments.map((segment) => (
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
                    <p className="text-sm text-gray-900 mb-2">{segment.source_text}</p>
                    {segment.post_edit && (
                      <p className="text-sm text-gray-600 italic">{segment.post_edit}</p>
                    )}
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    {segment.quality_estimate && (
                      <span
                        className={`text-xs font-medium ${getQualityColor(
                          segment.quality_estimate,
                        )}`}
                      >
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
                <div>
                  <label className="form-label">Source Text</label>
                  <div className="segment-source p-3 rounded-lg">
                    <p className="text-gray-900">{selectedSegment.source_text}</p>
                  </div>
                </div>

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

                {selectedSegment.nmt_suggestion && (
                  <div>
                    <label className="form-label">AI Translation</label>
                    <div className="segment-target p-3 rounded-lg">
                      <p className="text-gray-900">{selectedSegment.nmt_suggestion}</p>
                    </div>
                  </div>
                )}

                <div>
                  <label className="form-label">Your Translation</label>
                  <textarea
                    value={selectedSegment.post_edit || ''}
                    onChange={(event) => handleSegmentUpdate({ post_edit: event.target.value })}
                    className="segment-textarea"
                    rows={4}
                    placeholder="Enter your translation here..."
                    onFocus={() => {
                      wsService.sendTyping(currentProject.id, selectedSegment.id, true);
                    }}
                    onBlur={() => {
                      wsService.sendTyping(currentProject.id, selectedSegment.id, false);
                    }}
                  />
                </div>

                {(selectedSegment.quality_estimate || selectedSegment.risk_level) && (
                  <div className="grid grid-cols-2 gap-4">
                    {selectedSegment.quality_estimate && (
                      <div>
                        <label className="form-label">Quality Score</label>
                        <div
                          className={`text-2xl font-bold ${getQualityColor(
                            selectedSegment.quality_estimate,
                          )}`}
                        >
                          {Math.round(selectedSegment.quality_estimate)}%
                        </div>
                      </div>
                    )}
                    {selectedSegment.risk_level && (
                      <div>
                        <label className="form-label">Risk Level</label>
                        <div
                          className={`text-lg font-semibold ${getRiskColor(
                            selectedSegment.risk_level,
                          )}`}
                        >
                          {selectedSegment.risk_level.toUpperCase()}
                        </div>
                      </div>
                    )}
                  </div>
                )}

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

                <div>
                  <label className="form-label">Reviewer Notes</label>
                  <textarea
                    value={selectedSegment.reviewer_notes || ''}
                    onChange={(event) =>
                      handleSegmentUpdate({ reviewer_notes: event.target.value })
                    }
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
              <p className="text-gray-600">Choose a segment from the list to start translating.</p>
            </div>
          )}
        </div>
      </div>

      {studioData && (
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="activity-feed">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Translation Memory</h3>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {studioData.translation_memory?.map((entry: any) => (
                <div key={entry.id} className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm font-medium text-gray-900">{entry.source_text}</p>
                  <p className="text-sm text-gray-600 mt-1">{entry.translated_text}</p>
                  <p className="text-xs text-gray-500 mt-1">Usage: {entry.usage_count} times</p>
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
                  {term.notes && <p className="text-xs text-gray-500 mt-1">{term.notes}</p>}
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
