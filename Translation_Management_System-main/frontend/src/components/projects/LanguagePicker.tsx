import React, { useMemo, useState } from 'react';

export interface LocaleOption {
  code: string;
  label: string;
}

interface LanguagePickerProps {
  locales: LocaleOption[];
  sourceLocale: string;
  targetLocales: string[];
  onChange: (next: { source: string; targets: string[] }) => void;
  disabled?: boolean;
}

const normalize = (value: string) => value.trim().toLowerCase();

const LanguagePicker: React.FC<LanguagePickerProps> = ({
  locales,
  sourceLocale,
  targetLocales,
  onChange,
  disabled = false,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const sortedLocales = useMemo(
    () =>
      [...locales].sort((a, b) => {
        const labelCompare = a.label.localeCompare(b.label);
        return labelCompare !== 0 ? labelCompare : a.code.localeCompare(b.code);
      }),
    [locales],
  );

  const filteredTargets = useMemo(() => {
    const query = normalize(searchTerm);
    return sortedLocales.filter((locale) => {
      if (locale.code === sourceLocale) {
        return false;
      }
      if (!query) {
        return true;
      }
      return (
        normalize(locale.label).includes(query) ||
        normalize(locale.code).includes(query)
      );
    });
  }, [searchTerm, sortedLocales, sourceLocale]);

  const selectedTargets = useMemo(
    () =>
      sortedLocales.filter((locale) => targetLocales.includes(locale.code)),
    [sortedLocales, targetLocales],
  );

  const handleSourceChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const nextSource = event.target.value;
    const sanitizedTargets = targetLocales.filter((code) => code !== nextSource);
    onChange({ source: nextSource, targets: sanitizedTargets });
  };

  const toggleTarget = (code: string) => {
    if (disabled) return;
    const nextTargets = targetLocales.includes(code)
      ? targetLocales.filter((target) => target !== code)
      : [...targetLocales, code];
    onChange({
      source: sourceLocale,
      targets: nextTargets,
    });
  };

  const clearTargets = () => {
    if (disabled) return;
    onChange({
      source: sourceLocale,
      targets: [],
    });
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="form-label block mb-1 text-sm font-medium text-gray-700">
          Source Language
        </label>
        <select
          value={sourceLocale}
          onChange={handleSourceChange}
          disabled={disabled}
          className="form-select w-full"
        >
          <option value="">Select language</option>
          {sortedLocales.map((locale) => (
            <option key={locale.code} value={locale.code}>
              {locale.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="form-label block text-sm font-medium text-gray-700">
            Target Languages
          </label>
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <span>{selectedTargets.length} selected</span>
            <button
              type="button"
              onClick={clearTargets}
              disabled={disabled || selectedTargets.length === 0}
              className="text-primary-600 hover:text-primary-500 disabled:text-gray-300 disabled:cursor-not-allowed"
            >
              Clear
            </button>
          </div>
        </div>
        <input
          type="search"
          value={searchTerm}
          onChange={(event) => setSearchTerm(event.target.value)}
          placeholder="Search languages..."
          disabled={disabled}
          className="form-input w-full mb-3"
        />
        {selectedTargets.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {selectedTargets.map((locale) => (
              <span
                key={locale.code}
                className="inline-flex items-center bg-primary-100 text-primary-700 text-xs font-medium px-2.5 py-1 rounded-full"
              >
                {locale.label}
                {!disabled && (
                  <button
                    type="button"
                    onClick={() => toggleTarget(locale.code)}
                    className="ml-2 text-primary-600 hover:text-primary-800"
                    aria-label={`Remove ${locale.label}`}
                  >
                    ×
                  </button>
                )}
              </span>
            ))}
          </div>
        )}
        <div className="max-h-48 overflow-y-auto rounded-md border border-gray-200">
          {filteredTargets.map((locale) => {
            const isSelected = targetLocales.includes(locale.code);
            return (
              <label
                key={locale.code}
                className={`flex items-center justify-between px-3 py-2 border-b border-gray-100 last:border-b-0 cursor-pointer ${
                  isSelected ? 'bg-primary-50' : 'bg-white'
                } ${disabled ? 'cursor-not-allowed opacity-60' : ''}`}
              >
                <div>
                  <p className="text-sm font-medium text-gray-800">{locale.label}</p>
                  <p className="text-xs text-gray-500 uppercase tracking-wide">
                    {locale.code}
                  </p>
                </div>
                <input
                  type="checkbox"
                  className="h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  checked={isSelected}
                  onChange={() => toggleTarget(locale.code)}
                  disabled={disabled}
                />
              </label>
            );
          })}
          {filteredTargets.length === 0 && (
            <div className="px-3 py-4 text-sm text-gray-500">
              No languages match your search.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LanguagePicker;
