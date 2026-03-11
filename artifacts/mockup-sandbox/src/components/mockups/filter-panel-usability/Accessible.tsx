import React, { useState, useEffect, useRef } from 'react';
import { X, Search, Filter, RotateCcw, AlertCircle, Check } from 'lucide-react';
import './_group.css';

const CATEGORIES = ["unit", "functional", "integration", "e2e", "security", "business_logic", "regression", "other"];
const FEATURE_AREAS = ["Authentication", "Dashboard", "Medications", "Appointments", "Orbit Score", "Vitals", "Reminders", "Settings", "Notifications", "Reports"];

export function Accessible() {
  const [searchAll, setSearchAll] = useState('');
  const [testName, setTestName] = useState('');
  const [filePath, setFilePath] = useState('');
  const [category, setCategory] = useState('');
  const [featureArea, setFeatureArea] = useState('');
  const [newTestsOnly, setNewTestsOnly] = useState(false);
  const [existingTestsOnly, setExistingTestsOnly] = useState(false);
  const [isPendingChanges, setIsPendingChanges] = useState(false);

  const applyButtonRef = useRef<HTMLButtonElement>(null);

  const activeFilterCount = [
    searchAll, testName, filePath, category, featureArea, newTestsOnly, existingTestsOnly
  ].filter(Boolean).length;

  useEffect(() => {
    // Determine if there are pending changes. For this mockup, if any filter is set, we consider it pending.
    setIsPendingChanges(activeFilterCount > 0);
  }, [searchAll, testName, filePath, category, featureArea, newTestsOnly, existingTestsOnly]);

  const handleReset = () => {
    setSearchAll('');
    setTestName('');
    setFilePath('');
    setCategory('');
    setFeatureArea('');
    setNewTestsOnly(false);
    setExistingTestsOnly(false);
  };

  const handleApply = () => {
    // Mock apply
    setIsPendingChanges(false);
    alert('Filters applied successfully.');
  };

  return (
    <div 
      className="fixed inset-y-0 right-0 w-[480px] h-screen flex flex-col shadow-2xl overflow-hidden"
      style={{ 
        backgroundColor: 'var(--bg-surface)', 
        borderLeft: '1px solid var(--border-strong)',
        color: 'var(--text-primary)',
        fontFamily: 'var(--font-sans)'
      }}
      role="dialog"
      aria-labelledby="panel-title"
    >
      {/* Skip to apply link for screen readers and keyboard users */}
      <button
        onClick={() => applyButtonRef.current?.focus()}
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 z-50 px-4 py-2 font-bold"
        style={{ backgroundColor: 'var(--accent-cyan)', color: '#000' }}
      >
        Skip to Apply Filters
      </button>

      {/* Header */}
      <header 
        className="flex items-center justify-between px-6 py-5 border-b"
        style={{ borderColor: 'var(--border-strong)', backgroundColor: 'var(--bg-elevated)' }}
      >
        <div className="flex items-center gap-3">
          <h2 id="panel-title" className="text-2xl font-bold m-0">Filters</h2>
          {activeFilterCount > 0 && (
            <span 
              className="inline-flex items-center justify-center px-3 py-1 text-sm font-bold rounded-full"
              style={{ backgroundColor: 'var(--accent-cyan-dim)', color: 'var(--accent-cyan)', border: '1px solid var(--accent-cyan)' }}
              aria-label={`${activeFilterCount} active filters`}
            >
              {activeFilterCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={handleReset}
            className="flex items-center gap-2 px-4 py-2 text-base font-bold rounded focus:outline-none transition-colors"
            style={{ 
              color: 'var(--text-primary)', 
              backgroundColor: 'transparent',
              border: '2px solid transparent'
            }}
            onFocus={(e) => { e.currentTarget.style.border = '3px solid var(--accent-cyan)'; }}
            onBlur={(e) => { e.currentTarget.style.border = '2px solid transparent'; }}
            aria-label="Reset all filters"
          >
            <RotateCcw className="w-5 h-5" aria-hidden="true" />
            Reset
          </button>
          <button 
            className="p-2 rounded focus:outline-none transition-colors"
            style={{ color: 'var(--text-primary)', border: '2px solid transparent' }}
            onFocus={(e) => { e.currentTarget.style.border = '3px solid var(--accent-cyan)'; }}
            onBlur={(e) => { e.currentTarget.style.border = '2px solid transparent'; }}
            aria-label="Close filters panel"
          >
            <X className="w-6 h-6" aria-hidden="true" />
          </button>
        </div>
      </header>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-10">
        
        {/* String Filters */}
        <section aria-labelledby="string-filters-title">
          <div className="mb-4 border-b pb-2" style={{ borderColor: 'var(--border-default)' }}>
            <h3 id="string-filters-title" className="text-xl font-bold">Text Search Filters</h3>
            <p className="text-base mt-1" style={{ color: 'var(--text-primary)' }}>
              Search for specific test cases using text matching.
            </p>
          </div>
          
          <div className="space-y-6">
            <div className="space-y-2">
              <div className="flex justify-between items-baseline">
                <label htmlFor="searchAll" className="text-lg font-bold">Search All Fields</label>
                <span className="text-sm font-bold" style={{ color: 'var(--text-muted)' }} aria-hidden="true">Optional</span>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Search className="w-5 h-5" style={{ color: 'var(--text-primary)' }} aria-hidden="true" />
                </div>
                <input
                  type="text"
                  id="searchAll"
                  value={searchAll}
                  onChange={(e) => setSearchAll(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 text-base rounded border-2 bg-transparent focus:outline-none transition-shadow"
                  style={{ 
                    borderColor: 'var(--border-strong)', 
                    color: 'var(--text-primary)' 
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = 'var(--accent-cyan)';
                    e.currentTarget.style.boxShadow = '0 0 0 1px var(--accent-cyan)';
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = 'var(--border-strong)';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                  placeholder="Enter keywords..."
                  aria-describedby="searchAll-error"
                />
                {searchAll.length > 0 && searchAll.length < 3 && (
                  <p id="searchAll-error" className="mt-2 text-base font-bold flex items-center gap-2" style={{ color: 'var(--accent-amber)' }}>
                    <AlertCircle className="w-5 h-5" aria-hidden="true" />
                    Please enter at least 3 characters for better results.
                  </p>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-baseline">
                <label htmlFor="testName" className="text-lg font-bold">Test Name Contains</label>
                <span className="text-sm font-bold" style={{ color: 'var(--text-muted)' }} aria-hidden="true">Optional</span>
              </div>
              <input
                type="text"
                id="testName"
                value={testName}
                onChange={(e) => setTestName(e.target.value)}
                className="w-full px-4 py-3 text-base rounded border-2 bg-transparent focus:outline-none transition-shadow"
                style={{ 
                  borderColor: 'var(--border-strong)', 
                  color: 'var(--text-primary)',
                  fontFamily: 'var(--font-mono)'
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = 'var(--accent-cyan)';
                  e.currentTarget.style.boxShadow = '0 0 0 1px var(--accent-cyan)';
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border-strong)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
                placeholder="e.g. test_login_flow"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-baseline">
                <label htmlFor="filePath" className="text-lg font-bold">File Path Contains</label>
                <span className="text-sm font-bold" style={{ color: 'var(--text-muted)' }} aria-hidden="true">Optional</span>
              </div>
              <input
                type="text"
                id="filePath"
                value={filePath}
                onChange={(e) => setFilePath(e.target.value)}
                className="w-full px-4 py-3 text-base rounded border-2 bg-transparent focus:outline-none transition-shadow"
                style={{ 
                  borderColor: 'var(--border-strong)', 
                  color: 'var(--text-primary)',
                  fontFamily: 'var(--font-mono)'
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = 'var(--accent-cyan)';
                  e.currentTarget.style.boxShadow = '0 0 0 1px var(--accent-cyan)';
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border-strong)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
                placeholder="e.g. src/auth/"
              />
            </div>
          </div>
        </section>

        {/* Dropdown Filters */}
        <section aria-labelledby="dropdown-filters-title">
          <div className="mb-4 border-b pb-2" style={{ borderColor: 'var(--border-default)' }}>
            <h3 id="dropdown-filters-title" className="text-xl font-bold">Categorization Filters</h3>
            <p className="text-base mt-1" style={{ color: 'var(--text-primary)' }}>
              Filter tests by their defined category or specific feature area.
            </p>
          </div>

          <div className="space-y-6">
            <div className="space-y-2">
              <div className="flex justify-between items-baseline">
                <label htmlFor="category" className="text-lg font-bold">Category</label>
                <span className="text-sm font-bold" style={{ color: 'var(--text-muted)' }} aria-hidden="true">Optional</span>
              </div>
              <div className="relative">
                <select
                  id="category"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-4 py-3 text-base rounded border-2 appearance-none focus:outline-none transition-shadow"
                  style={{ 
                    borderColor: 'var(--border-strong)', 
                    backgroundColor: 'var(--bg-card)',
                    color: 'var(--text-primary)'
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = 'var(--accent-cyan)';
                    e.currentTarget.style.boxShadow = '0 0 0 1px var(--accent-cyan)';
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = 'var(--border-strong)';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  <option value="">Any Category</option>
                  {CATEGORIES.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
                <div className="absolute inset-y-0 right-0 flex items-center px-4 pointer-events-none">
                  <svg className="w-5 h-5 fill-current" viewBox="0 0 20 20" style={{ color: 'var(--text-primary)' }} aria-hidden="true">
                    <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-baseline">
                <label htmlFor="featureArea" className="text-lg font-bold">Feature Area</label>
                <span className="text-sm font-bold" style={{ color: 'var(--text-muted)' }} aria-hidden="true">Optional</span>
              </div>
              <div className="relative">
                <select
                  id="featureArea"
                  value={featureArea}
                  onChange={(e) => setFeatureArea(e.target.value)}
                  className="w-full px-4 py-3 text-base rounded border-2 appearance-none focus:outline-none transition-shadow"
                  style={{ 
                    borderColor: 'var(--border-strong)', 
                    backgroundColor: 'var(--bg-card)',
                    color: 'var(--text-primary)'
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = 'var(--accent-cyan)';
                    e.currentTarget.style.boxShadow = '0 0 0 1px var(--accent-cyan)';
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = 'var(--border-strong)';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  <option value="">Any Feature Area</option>
                  {FEATURE_AREAS.map(area => (
                    <option key={area} value={area}>{area}</option>
                  ))}
                </select>
                <div className="absolute inset-y-0 right-0 flex items-center px-4 pointer-events-none">
                  <svg className="w-5 h-5 fill-current" viewBox="0 0 20 20" style={{ color: 'var(--text-primary)' }} aria-hidden="true">
                    <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Toggle Filters */}
        <section aria-labelledby="toggle-filters-title">
          <div className="mb-4 border-b pb-2" style={{ borderColor: 'var(--border-default)' }}>
            <h3 id="toggle-filters-title" className="text-xl font-bold">Status Filters</h3>
            <p className="text-base mt-1" style={{ color: 'var(--text-primary)' }}>
              Filter by test age. These options are mutually exclusive.
            </p>
          </div>

          <div className="space-y-6">
            <div className="flex items-center justify-between p-4 rounded border-2" style={{ borderColor: 'var(--border-strong)', backgroundColor: 'var(--bg-card)' }}>
              <div>
                <label htmlFor="newTests" className="text-lg font-bold block">New Tests Only</label>
                <span className="text-base mt-1 block" style={{ color: 'var(--text-primary)' }}>Created in the last 7 days</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-base font-bold" aria-hidden="true" style={{ color: newTestsOnly ? 'var(--accent-cyan)' : 'var(--text-primary)' }}>
                  {newTestsOnly ? 'ON' : 'OFF'}
                </span>
                <button
                  id="newTests"
                  role="switch"
                  aria-checked={newTestsOnly}
                  onClick={() => {
                    setNewTestsOnly(!newTestsOnly);
                    if (!newTestsOnly) setExistingTestsOnly(false);
                  }}
                  className="relative inline-flex h-8 w-14 items-center rounded-full transition-colors focus:outline-none"
                  style={{ 
                    backgroundColor: newTestsOnly ? 'var(--accent-cyan)' : 'var(--bg-hover)',
                    border: '2px solid transparent'
                  }}
                  onFocus={(e) => { e.currentTarget.style.border = '2px solid white'; e.currentTarget.style.boxShadow = '0 0 0 2px var(--accent-cyan)'; }}
                  onBlur={(e) => { e.currentTarget.style.border = '2px solid transparent'; e.currentTarget.style.boxShadow = 'none'; }}
                >
                  <span className="sr-only">Toggle New Tests Only</span>
                  <span
                    className={`${newTestsOnly ? 'translate-x-7' : 'translate-x-1'} inline-block h-6 w-6 transform rounded-full bg-white transition-transform`}
                  />
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 rounded border-2" style={{ borderColor: 'var(--border-strong)', backgroundColor: 'var(--bg-card)' }}>
              <div>
                <label htmlFor="existingTests" className="text-lg font-bold block">Existing Tests Only</label>
                <span className="text-base mt-1 block" style={{ color: 'var(--text-primary)' }}>Created more than 7 days ago</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-base font-bold" aria-hidden="true" style={{ color: existingTestsOnly ? 'var(--accent-cyan)' : 'var(--text-primary)' }}>
                  {existingTestsOnly ? 'ON' : 'OFF'}
                </span>
                <button
                  id="existingTests"
                  role="switch"
                  aria-checked={existingTestsOnly}
                  onClick={() => {
                    setExistingTestsOnly(!existingTestsOnly);
                    if (!existingTestsOnly) setNewTestsOnly(false);
                  }}
                  className="relative inline-flex h-8 w-14 items-center rounded-full transition-colors focus:outline-none"
                  style={{ 
                    backgroundColor: existingTestsOnly ? 'var(--accent-cyan)' : 'var(--bg-hover)',
                    border: '2px solid transparent'
                  }}
                  onFocus={(e) => { e.currentTarget.style.border = '2px solid white'; e.currentTarget.style.boxShadow = '0 0 0 2px var(--accent-cyan)'; }}
                  onBlur={(e) => { e.currentTarget.style.border = '2px solid transparent'; e.currentTarget.style.boxShadow = 'none'; }}
                >
                  <span className="sr-only">Toggle Existing Tests Only</span>
                  <span
                    className={`${existingTestsOnly ? 'translate-x-7' : 'translate-x-1'} inline-block h-6 w-6 transform rounded-full bg-white transition-transform`}
                  />
                </button>
              </div>
            </div>
          </div>
        </section>

      </div>

      {/* Footer */}
      <footer 
        className="p-6 border-t flex items-center justify-between gap-4 mt-auto"
        style={{ borderColor: 'var(--border-strong)', backgroundColor: 'var(--bg-elevated)' }}
      >
        <button
          onClick={handleReset}
          className="px-6 py-4 text-lg font-bold rounded focus:outline-none transition-colors border-2"
          style={{ 
            color: 'var(--text-primary)', 
            backgroundColor: 'transparent',
            borderColor: 'var(--border-strong)'
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = 'var(--accent-cyan)';
            e.currentTarget.style.boxShadow = '0 0 0 1px var(--accent-cyan)';
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = 'var(--border-strong)';
            e.currentTarget.style.boxShadow = 'none';
          }}
        >
          Clear All
        </button>
        <button
          ref={applyButtonRef}
          onClick={handleApply}
          disabled={!isPendingChanges}
          className="flex-1 flex items-center justify-center gap-3 px-6 py-4 text-lg font-bold rounded focus:outline-none transition-all disabled:opacity-50 disabled:cursor-not-allowed border-2"
          style={{ 
            backgroundColor: isPendingChanges ? 'var(--accent-cyan)' : 'var(--bg-hover)',
            color: isPendingChanges ? '#000000' : 'var(--text-muted)',
            borderColor: 'transparent'
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = 'white';
            e.currentTarget.style.boxShadow = '0 0 0 2px var(--accent-cyan)';
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = 'transparent';
            e.currentTarget.style.boxShadow = 'none';
          }}
          aria-disabled={!isPendingChanges}
        >
          <Filter className="w-6 h-6" aria-hidden="true" />
          Apply Filters
        </button>
      </footer>
    </div>
  );
}
