import { useCallback, useEffect, useRef } from 'react';
import { useStore } from '../store/useStore';

type SetterValue<T> = Partial<T> | T | ((previous: T) => T);

export function usePageState<T>(key: string, initialState: T) {
  const state = useStore((store) => store.pageState[key] as T | undefined);
  const updatePageState = useStore((store) => store.updatePageState);
  const clearPageState = useStore((store) => store.clearPageState);
  const initialRef = useRef(initialState);

  useEffect(() => {
    initialRef.current = initialState;
  }, [initialState]);

  useEffect(() => {
    if (state === undefined) {
      updatePageState<T>(key, initialRef.current);
    }
  }, [key, state, updatePageState]);

  const setState = useCallback(
    (value: SetterValue<T>) => {
      updatePageState<T>(key, (prev) => {
        const castPrev = (prev ?? initialRef.current) as T;
        if (typeof value === 'function') {
          return (value as (previous: T) => T)(castPrev);
        }
        if (
          value &&
          typeof value === 'object' &&
          !Array.isArray(value) &&
          castPrev &&
          typeof castPrev === 'object' &&
          !Array.isArray(castPrev)
        ) {
          return { ...(castPrev as Record<string, unknown>), ...(value as Record<string, unknown>) } as T;
        }
        return value as T;
      });
    },
    [key, updatePageState],
  );

  const resetState = useCallback(() => {
    updatePageState<T>(key, initialRef.current);
  }, [key, updatePageState]);

  const removeState = useCallback(() => {
    clearPageState(key);
  }, [clearPageState, key]);

  return [state ?? initialRef.current, setState, resetState, removeState] as const;
}
