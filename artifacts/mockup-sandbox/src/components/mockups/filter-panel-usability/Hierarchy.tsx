import React, { useState, useMemo } from 'react';
import { X, Search, RotateCcw, Type, ListFilter, ToggleLeft } from 'lucide-react';
import './_group.css';

const CATEGORIES = ["unit", "functional", "integration", "e2e", "security", "business_logic", "regression", "other"];
const FEATURE_AREAS = ["Authentication", "Dashboard", "Medications", "Appointments", "Orbit Score", "Vitals", "Reminders", "Settings", "Notifications", "Reports"];

export function Hierarchy() {
  // String Filters
  const [searchAll, setSearchAll] = useState('');
  const [testName, setTestName] = useState('');
  const [filePath, setFilePath] = useState('');

  // Dropdown Filters
  const [category, setCategory] = useState('');
  const [featureArea, setFeatureArea] = useState('');

  // Toggle Filters
  const [testAge, setTestAge] = useState<'all' | 'new' | 'existing'>('all');

  const activeStringFiltersCount = [searchAll, testName, filePath].filter(Boolean).length;
  const activeDropdownFiltersCount = [category, featureArea].filter(Boolean).length;
  const activeToggleFiltersCount = testAge !== 'all' ? 1 : 0;

  const totalActive = activeStringFiltersCount + activeDropdownFiltersCount + activeToggleFiltersCount;

  // Mock calculation for test count
  const baseCount = 429;
  const currentCount = useMemo(() => {
    let count = baseCount;
    if (activeStringFiltersCount > 0) count -= activeStringFiltersCount * 45;
    if (activeDropdownFiltersCount > 0) count -= activeDropdownFiltersCount * 80;
    if (testAge !== 'all') count -= 150;
    return Math.max(12, count);
  }, [activeStringFiltersCount, activeDropdownFiltersCount, testAge]);

  const handleReset = () => {
    setSearchAll('');
    setTestName('');
    setFilePath('');
    setCategory('');
    setFeatureArea('');
    setTestAge('all');
  };

  return (
    <div className="w-[480px] h-[100vh] flex flex-col bg-[var(--bg-surface)] text-[var(--text-primary)] font-sans border-l border-[var(--border-default)]">
      {/* Header */}
      <div className="px-6 py-5 border-b border-[var(--border-default)] flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-medium">Filters</h2>
            {totalActive > 0 && (
              <span className="bg-[var(--accent-cyan-dim)] text-[var(--accent-cyan)] text-xs font-bold px-2 py-0.5 rounded-full">
                {totalActive}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button 
              onClick={handleReset}
              className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors p-2 flex items-center gap-1.5 text-sm"
            >
              <RotateCcw className="w-4 h-4" />
              Reset
            </button>
            <button className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors p-2">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
        
        {/* Breadcrumb style path */}
        <div className="text-xs font-mono text-[var(--text-secondary)] flex items-center gap-2">
          <span>Filters</span>
          <span className="text-[var(--text-muted)]">&gt;</span>
          <span className={totalActive > 0 ? 'text-[var(--accent-cyan)]' : ''}>{totalActive} active</span>
          <span className="text-[var(--text-muted)]">&gt;</span>
          <span>showing {currentCount} of {baseCount}</span>
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="flex flex-col">
          
          {/* Section 01: STRING FILTERS */}
          <div className="relative pt-8 pb-10 px-6">
            <div className="absolute left-0 top-8 bottom-10 w-1 bg-[var(--accent-cyan)] rounded-r-md"></div>
            
            <div className="flex items-center gap-3 mb-2">
              <Type className="w-5 h-5 text-[var(--accent-cyan)]" />
              <h3 className="text-sm font-bold tracking-wider text-[var(--text-primary)] uppercase">01 String Filters</h3>
            </div>
            <p className="text-xs text-[var(--text-muted)] mb-6 ml-8 font-mono">{activeStringFiltersCount} of 3 active</p>

            <div className="flex flex-col gap-5 ml-8">
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-[var(--text-secondary)]">Search All Fields</label>
                <div className={`relative flex items-center overflow-hidden rounded-md border bg-[var(--bg-base)] transition-colors ${searchAll ? 'border-[var(--accent-cyan)]' : 'border-[var(--border-strong)]'}`}>
                  {searchAll && <div className="absolute left-0 top-0 bottom-0 w-1 bg-[var(--accent-cyan)]"></div>}
                  <Search className="absolute left-3 w-4 h-4 text-[var(--text-muted)]" />
                  <input 
                    type="text" 
                    value={searchAll}
                    onChange={(e) => setSearchAll(e.target.value)}
                    placeholder="Search query..."
                    className="w-full bg-transparent border-none outline-none py-2.5 pl-9 pr-3 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-[var(--text-secondary)]">Test Name Contains</label>
                <div className={`relative flex items-center overflow-hidden rounded-md border bg-[var(--bg-base)] transition-colors ${testName ? 'border-[var(--accent-cyan)]' : 'border-[var(--border-strong)]'}`}>
                  {testName && <div className="absolute left-0 top-0 bottom-0 w-1 bg-[var(--accent-cyan)]"></div>}
                  <input 
                    type="text" 
                    value={testName}
                    onChange={(e) => setTestName(e.target.value)}
                    placeholder="e.g. auth_flow"
                    className="w-full bg-transparent border-none outline-none py-2.5 px-3 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] font-mono"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-[var(--text-secondary)]">File Path Contains</label>
                <div className={`relative flex items-center overflow-hidden rounded-md border bg-[var(--bg-base)] transition-colors ${filePath ? 'border-[var(--accent-cyan)]' : 'border-[var(--border-strong)]'}`}>
                  {filePath && <div className="absolute left-0 top-0 bottom-0 w-1 bg-[var(--accent-cyan)]"></div>}
                  <input 
                    type="text" 
                    value={filePath}
                    onChange={(e) => setFilePath(e.target.value)}
                    placeholder="e.g. src/tests/integration"
                    className="w-full bg-transparent border-none outline-none py-2.5 px-3 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] font-mono"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="h-px bg-[var(--border-subtle)] mx-6"></div>

          {/* Section 02: DROPDOWN FILTERS */}
          <div className="relative pt-8 pb-10 px-6">
            <div className="absolute left-0 top-8 bottom-10 w-1 bg-[var(--accent-violet)] rounded-r-md"></div>
            
            <div className="flex items-center gap-3 mb-2">
              <ListFilter className="w-5 h-5 text-[var(--accent-violet)]" />
              <h3 className="text-sm font-bold tracking-wider text-[var(--text-primary)] uppercase">02 Dropdown Filters</h3>
            </div>
            <p className="text-xs text-[var(--text-muted)] mb-6 ml-8 font-mono">{activeDropdownFiltersCount} of 2 active</p>

            <div className="flex flex-col gap-5 ml-8">
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-[var(--text-secondary)]">Category</label>
                <div className={`relative flex items-center overflow-hidden rounded-md border bg-[var(--bg-base)] transition-colors ${category ? 'border-[var(--accent-violet)]' : 'border-[var(--border-strong)]'}`}>
                  {category && <div className="absolute left-0 top-0 bottom-0 w-1 bg-[var(--accent-violet)]"></div>}
                  <select 
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full bg-transparent border-none outline-none py-2.5 px-3 text-sm text-[var(--text-primary)] appearance-none cursor-pointer"
                  >
                    <option value="" className="bg-[var(--bg-elevated)]">Any Category</option>
                    {CATEGORIES.map(c => (
                      <option key={c} value={c} className="bg-[var(--bg-elevated)]">{c}</option>
                    ))}
                  </select>
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-[var(--text-muted)]">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
                  </div>
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-[var(--text-secondary)]">Feature Area</label>
                <div className={`relative flex items-center overflow-hidden rounded-md border bg-[var(--bg-base)] transition-colors ${featureArea ? 'border-[var(--accent-violet)]' : 'border-[var(--border-strong)]'}`}>
                  {featureArea && <div className="absolute left-0 top-0 bottom-0 w-1 bg-[var(--accent-violet)]"></div>}
                  <select 
                    value={featureArea}
                    onChange={(e) => setFeatureArea(e.target.value)}
                    className="w-full bg-transparent border-none outline-none py-2.5 px-3 text-sm text-[var(--text-primary)] appearance-none cursor-pointer"
                  >
                    <option value="" className="bg-[var(--bg-elevated)]">Any Feature Area</option>
                    {FEATURE_AREAS.map(f => (
                      <option key={f} value={f} className="bg-[var(--bg-elevated)]">{f}</option>
                    ))}
                  </select>
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-[var(--text-muted)]">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="h-px bg-[var(--border-subtle)] mx-6"></div>

          {/* Section 03: TOGGLE FILTERS */}
          <div className="relative pt-8 pb-10 px-6">
            <div className="absolute left-0 top-8 bottom-10 w-1 bg-[var(--accent-emerald)] rounded-r-md"></div>
            
            <div className="flex items-center gap-3 mb-2">
              <ToggleLeft className="w-5 h-5 text-[var(--accent-emerald)]" />
              <h3 className="text-sm font-bold tracking-wider text-[var(--text-primary)] uppercase">03 Toggle Filters</h3>
            </div>
            <p className="text-xs text-[var(--text-muted)] mb-6 ml-8 font-mono">{activeToggleFiltersCount} of 1 active</p>

            <div className="flex flex-col gap-4 ml-8">
              <label 
                className={`relative flex items-center justify-between p-3 rounded-md border cursor-pointer transition-colors ${testAge === 'new' ? 'border-[var(--accent-emerald)] bg-[var(--bg-hover)]' : 'border-[var(--border-strong)] bg-[var(--bg-base)] hover:border-[var(--text-muted)]'}`}
              >
                {testAge === 'new' && <div className="absolute left-0 top-0 bottom-0 w-1 bg-[var(--accent-emerald)] rounded-l-md"></div>}
                <span className="text-sm font-medium">New Tests Only</span>
                <div className={`w-10 h-5 rounded-full p-0.5 transition-colors ${testAge === 'new' ? 'bg-[var(--accent-emerald)]' : 'bg-[var(--bg-elevated)]'}`}>
                  <div className={`w-4 h-4 bg-white rounded-full transition-transform ${testAge === 'new' ? 'translate-x-5' : 'translate-x-0'}`} />
                </div>
                <input 
                  type="checkbox" 
                  className="hidden" 
                  checked={testAge === 'new'} 
                  onChange={() => setTestAge(prev => prev === 'new' ? 'all' : 'new')}
                />
              </label>

              <label 
                className={`relative flex items-center justify-between p-3 rounded-md border cursor-pointer transition-colors ${testAge === 'existing' ? 'border-[var(--accent-emerald)] bg-[var(--bg-hover)]' : 'border-[var(--border-strong)] bg-[var(--bg-base)] hover:border-[var(--text-muted)]'}`}
              >
                {testAge === 'existing' && <div className="absolute left-0 top-0 bottom-0 w-1 bg-[var(--accent-emerald)] rounded-l-md"></div>}
                <span className="text-sm font-medium">Existing Tests Only</span>
                <div className={`w-10 h-5 rounded-full p-0.5 transition-colors ${testAge === 'existing' ? 'bg-[var(--accent-emerald)]' : 'bg-[var(--bg-elevated)]'}`}>
                  <div className={`w-4 h-4 bg-white rounded-full transition-transform ${testAge === 'existing' ? 'translate-x-5' : 'translate-x-0'}`} />
                </div>
                <input 
                  type="checkbox" 
                  className="hidden" 
                  checked={testAge === 'existing'} 
                  onChange={() => setTestAge(prev => prev === 'existing' ? 'all' : 'existing')}
                />
              </label>
            </div>
          </div>

        </div>
      </div>

      {/* Footer */}
      <div className="p-6 border-t border-[var(--border-default)] bg-[var(--bg-card)] mt-auto flex flex-col gap-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-[var(--text-muted)]">Results Preview</span>
          <span className="font-mono text-[var(--accent-cyan)] font-bold">Will show ~{currentCount} tests</span>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={handleReset}
            className="flex-1 py-2.5 px-4 rounded-md border border-[var(--border-strong)] text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors text-sm font-medium"
          >
            Clear All
          </button>
          <button className="flex-[2] py-2.5 px-4 rounded-md bg-[var(--accent-cyan)] text-[var(--bg-base)] hover:opacity-90 transition-opacity text-sm font-bold shadow-[0_0_15px_var(--accent-cyan-dim)]">
            Apply Filters
          </button>
        </div>
      </div>
    </div>
  );
}
