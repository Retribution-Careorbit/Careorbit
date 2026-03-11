import { useState, useMemo, useEffect, useCallback, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Layout } from "@/components/layout";
import {
  FlaskConical, Search, ListChecks, Sparkles, Archive,
  Filter, X, RotateCcw, ChevronRight, AlertCircle,
} from "lucide-react";

interface TestCase {
  name: string;
  file_path: string;
  category: string;
  feature_area: string;
  is_new: boolean;
}

interface TestSummary {
  total: number;
  new_count: number;
  existing_count: number;
  by_category: Record<string, number>;
}

interface TestCasesResponse {
  tests: TestCase[];
  summary: TestSummary;
}

interface FilterState {
  search: string;
  nameFilter: string;
  filePathFilter: string;
  selectedCategory: string;
  selectedFeature: string;
  showNewOnly: boolean;
  showExistingOnly: boolean;
}

const EMPTY_FILTERS: FilterState = {
  search: "",
  nameFilter: "",
  filePathFilter: "",
  selectedCategory: "all",
  selectedFeature: "all",
  showNewOnly: false,
  showExistingOnly: false,
};

const CATEGORY_COLORS: Record<string, { bg: string; text: string }> = {
  unit: { bg: "var(--accent-cyan-dim)", text: "var(--accent-cyan)" },
  functional: { bg: "var(--accent-emerald-dim)", text: "var(--accent-emerald)" },
  integration: { bg: "var(--accent-violet-dim)", text: "var(--accent-violet)" },
  e2e: { bg: "var(--accent-amber-dim)", text: "var(--accent-amber)" },
  security: { bg: "var(--accent-rose-dim)", text: "var(--accent-rose)" },
  business_logic: { bg: "var(--accent-amber-dim)", text: "var(--accent-amber)" },
  regression: { bg: "var(--border-subtle)", text: "var(--text-secondary)" },
  false_positive_negative: { bg: "var(--accent-rose-dim)", text: "var(--accent-rose)" },
  other: { bg: "var(--border-subtle)", text: "var(--text-muted)" },
};

function formatTestName(name: string): string {
  return name.replace(/^test_/, "").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatCategory(cat: string): string {
  return cat.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function countActiveFilters(f: FilterState): number {
  return [
    f.showNewOnly,
    f.showExistingOnly,
    f.selectedCategory !== "all",
    f.selectedFeature !== "all",
    f.search.length > 0,
    f.nameFilter.length > 0,
    f.filePathFilter.length > 0,
  ].filter(Boolean).length;
}

function AccessibleFilterPanel({
  open,
  onClose,
  draft,
  setDraft,
  onApply,
  onReset,
  hasDraftChanges,
  draftFilterCount,
  categories,
  featureAreas,
  summary,
}: {
  open: boolean;
  onClose: () => void;
  draft: FilterState;
  setDraft: (fn: (prev: FilterState) => FilterState) => void;
  onApply: () => void;
  onReset: () => void;
  hasDraftChanges: boolean;
  draftFilterCount: number;
  categories: string[];
  featureAreas: string[];
  summary: TestSummary | undefined;
}) {
  const applyButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open, onClose]);

  const inputFocusStyle = (el: HTMLElement) => {
    el.style.borderColor = "var(--accent-cyan)";
    el.style.boxShadow = "0 0 0 2px var(--accent-cyan)";
  };
  const inputBlurStyle = (el: HTMLElement) => {
    el.style.borderColor = "var(--border-strong)";
    el.style.boxShadow = "none";
  };

  return (
    <>
      <div
        className="fixed inset-0 z-40 transition-opacity duration-300"
        style={{
          background: "rgba(0,0,0,0.5)",
          backdropFilter: "blur(2px)",
          opacity: open ? 1 : 0,
          pointerEvents: open ? "auto" : "none",
        }}
        onClick={onClose}
        data-testid="filter-overlay"
        aria-hidden="true"
      />

      <div
        className="fixed top-0 right-0 z-50 h-full flex flex-col transition-transform duration-300 ease-out"
        style={{
          width: "min(480px, 50vw)",
          transform: open ? "translateX(0)" : "translateX(100%)",
          background: "var(--bg-surface)",
          borderLeft: "1px solid var(--border-strong)",
          boxShadow: open ? "-8px 0 40px rgba(0,0,0,0.3)" : "none",
        }}
        role="dialog"
        aria-labelledby="filter-panel-title"
        aria-modal="true"
        data-testid="filter-panel"
      >
        <button
          onClick={() => applyButtonRef.current?.focus()}
          className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:rounded focus:font-bold focus:text-sm"
          style={{ backgroundColor: "var(--accent-cyan)", color: "#000" }}
          data-testid="skip-to-apply"
        >
          Skip to Apply Filters
        </button>

        <header
          className="flex items-center justify-between px-6 py-5 shrink-0"
          style={{ borderBottom: "1px solid var(--border-strong)", background: "var(--bg-elevated)" }}
        >
          <div className="flex items-center gap-3">
            <h2 id="filter-panel-title" className="text-xl font-bold m-0" style={{ color: "var(--text-primary)" }}>
              Filters
            </h2>
            {draftFilterCount > 0 && (
              <span
                className="inline-flex items-center justify-center px-2.5 py-0.5 text-sm font-bold rounded-full"
                style={{ backgroundColor: "var(--accent-cyan-dim)", color: "var(--accent-cyan)", border: "1px solid var(--accent-cyan)" }}
                aria-label={`${draftFilterCount} active filters`}
                data-testid="badge-active-filters"
              >
                {draftFilterCount}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onReset}
              className="flex items-center gap-2 px-3 py-2 text-sm font-bold rounded-lg transition-colors"
              style={{ color: "var(--text-primary)", background: "transparent", border: "2px solid transparent" }}
              onFocus={(e) => { e.currentTarget.style.border = "2px solid var(--accent-cyan)"; }}
              onBlur={(e) => { e.currentTarget.style.border = "2px solid transparent"; }}
              aria-label="Reset all filters"
              data-testid="button-clear-filters"
            >
              <RotateCcw className="w-4 h-4" aria-hidden="true" />
              Reset
            </button>
            <button
              onClick={onClose}
              className="w-9 h-9 rounded-lg flex items-center justify-center transition-colors"
              style={{ color: "var(--text-primary)", background: "transparent", border: "2px solid transparent" }}
              onFocus={(e) => { e.currentTarget.style.border = "2px solid var(--accent-cyan)"; }}
              onBlur={(e) => { e.currentTarget.style.border = "2px solid transparent"; }}
              aria-label="Close filters panel"
              data-testid="button-close-filters"
            >
              <X className="w-5 h-5" aria-hidden="true" />
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-8">
          <section aria-labelledby="section-text-filters">
            <div className="mb-4 pb-2" style={{ borderBottom: "1px solid var(--border-default)" }}>
              <h3 id="section-text-filters" className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                Text Search Filters
              </h3>
              <p className="text-sm mt-1" style={{ color: "var(--text-primary)" }}>
                Search for specific test cases using text matching.
              </p>
            </div>
            <div className="space-y-5">
              <div className="space-y-2">
                <div className="flex justify-between items-baseline">
                  <label htmlFor="filter-search-all" className="text-base font-bold" style={{ color: "var(--text-primary)" }}>
                    Search All Fields
                  </label>
                  <span className="text-xs font-bold" style={{ color: "var(--text-muted)" }} aria-hidden="true">Optional</span>
                </div>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                    <Search className="w-4.5 h-4.5" style={{ color: "var(--text-primary)" }} aria-hidden="true" />
                  </div>
                  <input
                    type="text"
                    id="filter-search-all"
                    value={draft.search}
                    onChange={(e) => setDraft((p) => ({ ...p, search: e.target.value }))}
                    className="w-full pl-10 pr-4 py-3 text-sm rounded-lg bg-transparent transition-shadow"
                    style={{ border: "2px solid var(--border-strong)", color: "var(--text-primary)" }}
                    onFocus={(e) => inputFocusStyle(e.currentTarget)}
                    onBlur={(e) => inputBlurStyle(e.currentTarget)}
                    placeholder="Enter keywords..."
                    aria-describedby={draft.search.length > 0 && draft.search.length < 3 ? "search-hint" : undefined}
                    data-testid="input-search-tests"
                  />
                </div>
                {draft.search.length > 0 && draft.search.length < 3 && (
                  <p id="search-hint" className="mt-1.5 text-sm font-medium flex items-center gap-1.5" style={{ color: "var(--accent-amber)" }}>
                    <AlertCircle className="w-4 h-4 shrink-0" aria-hidden="true" />
                    Enter at least 3 characters for better results.
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-baseline">
                  <label htmlFor="filter-test-name" className="text-base font-bold" style={{ color: "var(--text-primary)" }}>
                    Test Name Contains
                  </label>
                  <span className="text-xs font-bold" style={{ color: "var(--text-muted)" }} aria-hidden="true">Optional</span>
                </div>
                <input
                  type="text"
                  id="filter-test-name"
                  value={draft.nameFilter}
                  onChange={(e) => setDraft((p) => ({ ...p, nameFilter: e.target.value }))}
                  className="w-full px-4 py-3 text-sm rounded-lg bg-transparent font-mono transition-shadow"
                  style={{ border: "2px solid var(--border-strong)", color: "var(--text-primary)" }}
                  onFocus={(e) => inputFocusStyle(e.currentTarget)}
                  onBlur={(e) => inputBlurStyle(e.currentTarget)}
                  placeholder="e.g. test_login_flow"
                  data-testid="input-name-filter"
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-baseline">
                  <label htmlFor="filter-file-path" className="text-base font-bold" style={{ color: "var(--text-primary)" }}>
                    File Path Contains
                  </label>
                  <span className="text-xs font-bold" style={{ color: "var(--text-muted)" }} aria-hidden="true">Optional</span>
                </div>
                <input
                  type="text"
                  id="filter-file-path"
                  value={draft.filePathFilter}
                  onChange={(e) => setDraft((p) => ({ ...p, filePathFilter: e.target.value }))}
                  className="w-full px-4 py-3 text-sm rounded-lg bg-transparent font-mono transition-shadow"
                  style={{ border: "2px solid var(--border-strong)", color: "var(--text-primary)" }}
                  onFocus={(e) => inputFocusStyle(e.currentTarget)}
                  onBlur={(e) => inputBlurStyle(e.currentTarget)}
                  placeholder="e.g. src/auth/"
                  data-testid="input-filepath-filter"
                />
              </div>
            </div>
          </section>

          <section aria-labelledby="section-categorization-filters">
            <div className="mb-4 pb-2" style={{ borderBottom: "1px solid var(--border-default)" }}>
              <h3 id="section-categorization-filters" className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                Categorization Filters
              </h3>
              <p className="text-sm mt-1" style={{ color: "var(--text-primary)" }}>
                Filter tests by their defined category or specific feature area.
              </p>
            </div>
            <div className="space-y-5">
              <div className="space-y-2">
                <div className="flex justify-between items-baseline">
                  <label htmlFor="filter-category" className="text-base font-bold" style={{ color: "var(--text-primary)" }}>
                    Category
                  </label>
                  <span className="text-xs font-bold" style={{ color: "var(--text-muted)" }} aria-hidden="true">Optional</span>
                </div>
                <div className="relative">
                  <select
                    id="filter-category"
                    value={draft.selectedCategory}
                    onChange={(e) => setDraft((p) => ({ ...p, selectedCategory: e.target.value }))}
                    className="w-full px-4 py-3 text-sm rounded-lg appearance-none transition-shadow"
                    style={{
                      border: `2px solid ${draft.selectedCategory !== "all" ? "var(--accent-violet)" : "var(--border-strong)"}`,
                      backgroundColor: "var(--bg-card)",
                      color: "var(--text-primary)",
                    }}
                    onFocus={(e) => inputFocusStyle(e.currentTarget)}
                    onBlur={(e) => { e.currentTarget.style.borderColor = draft.selectedCategory !== "all" ? "var(--accent-violet)" : "var(--border-strong)"; e.currentTarget.style.boxShadow = "none"; }}
                    data-testid="select-category"
                  >
                    <option value="all">All Categories</option>
                    {categories.map((cat) => (
                      <option key={cat} value={cat}>
                        {formatCategory(cat)} {summary?.by_category?.[cat] ? `(${summary.by_category[cat]})` : ""}
                      </option>
                    ))}
                  </select>
                  <div className="absolute inset-y-0 right-0 flex items-center px-3 pointer-events-none">
                    <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20" style={{ color: "var(--text-primary)" }} aria-hidden="true">
                      <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                    </svg>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-baseline">
                  <label htmlFor="filter-feature" className="text-base font-bold" style={{ color: "var(--text-primary)" }}>
                    Feature Area
                  </label>
                  <span className="text-xs font-bold" style={{ color: "var(--text-muted)" }} aria-hidden="true">Optional</span>
                </div>
                <div className="relative">
                  <select
                    id="filter-feature"
                    value={draft.selectedFeature}
                    onChange={(e) => setDraft((p) => ({ ...p, selectedFeature: e.target.value }))}
                    className="w-full px-4 py-3 text-sm rounded-lg appearance-none transition-shadow"
                    style={{
                      border: `2px solid ${draft.selectedFeature !== "all" ? "var(--accent-cyan)" : "var(--border-strong)"}`,
                      backgroundColor: "var(--bg-card)",
                      color: "var(--text-primary)",
                    }}
                    onFocus={(e) => inputFocusStyle(e.currentTarget)}
                    onBlur={(e) => { e.currentTarget.style.borderColor = draft.selectedFeature !== "all" ? "var(--accent-cyan)" : "var(--border-strong)"; e.currentTarget.style.boxShadow = "none"; }}
                    data-testid="select-feature"
                  >
                    <option value="all">All Feature Areas</option>
                    {featureAreas.map((feat) => (
                      <option key={feat} value={feat}>{feat}</option>
                    ))}
                  </select>
                  <div className="absolute inset-y-0 right-0 flex items-center px-3 pointer-events-none">
                    <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20" style={{ color: "var(--text-primary)" }} aria-hidden="true">
                      <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section aria-labelledby="section-status-filters">
            <div className="mb-4 pb-2" style={{ borderBottom: "1px solid var(--border-default)" }}>
              <h3 id="section-status-filters" className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                Status Filters
              </h3>
              <p className="text-sm mt-1" style={{ color: "var(--text-primary)" }}>
                Filter by test age. These options are mutually exclusive.
              </p>
            </div>
            <div className="space-y-4">
              <div
                className="flex items-center justify-between p-4 rounded-xl transition-colors"
                style={{
                  border: `2px solid ${draft.showNewOnly ? "var(--accent-emerald)" : "var(--border-strong)"}`,
                  background: draft.showNewOnly ? "var(--accent-emerald-dim)" : "var(--bg-card)",
                }}
              >
                <div>
                  <label htmlFor="toggle-new" className="text-base font-bold block cursor-pointer" style={{ color: "var(--text-primary)" }}>
                    New Tests Only
                  </label>
                  <span className="text-sm mt-0.5 block" style={{ color: "var(--text-secondary)" }}>
                    Show only recently added tests
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-bold" aria-hidden="true" style={{ color: draft.showNewOnly ? "var(--accent-emerald)" : "var(--text-muted)" }}>
                    {draft.showNewOnly ? "ON" : "OFF"}
                  </span>
                  <button
                    id="toggle-new"
                    role="switch"
                    aria-checked={draft.showNewOnly}
                    onClick={() => setDraft((p) => ({ ...p, showNewOnly: !p.showNewOnly, showExistingOnly: !p.showNewOnly ? false : p.showExistingOnly }))}
                    className="relative inline-flex h-7 w-12 items-center rounded-full transition-colors"
                    style={{
                      backgroundColor: draft.showNewOnly ? "var(--accent-emerald)" : "var(--border-default)",
                      border: "2px solid transparent",
                    }}
                    onFocus={(e) => { e.currentTarget.style.border = "2px solid white"; e.currentTarget.style.boxShadow = "0 0 0 2px var(--accent-cyan)"; }}
                    onBlur={(e) => { e.currentTarget.style.border = "2px solid transparent"; e.currentTarget.style.boxShadow = "none"; }}
                    data-testid="toggle-new-only"
                  >
                    <span className="sr-only">Toggle New Tests Only</span>
                    <span
                      className="inline-block h-5 w-5 rounded-full bg-white transition-transform duration-200"
                      style={{ transform: draft.showNewOnly ? "translateX(22px)" : "translateX(2px)" }}
                    />
                  </button>
                </div>
              </div>

              <div
                className="flex items-center justify-between p-4 rounded-xl transition-colors"
                style={{
                  border: `2px solid ${draft.showExistingOnly ? "var(--accent-amber)" : "var(--border-strong)"}`,
                  background: draft.showExistingOnly ? "var(--accent-amber-dim)" : "var(--bg-card)",
                }}
              >
                <div>
                  <label htmlFor="toggle-existing" className="text-base font-bold block cursor-pointer" style={{ color: "var(--text-primary)" }}>
                    Existing Tests Only
                  </label>
                  <span className="text-sm mt-0.5 block" style={{ color: "var(--text-secondary)" }}>
                    Show only phase 1 & 2 tests
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-bold" aria-hidden="true" style={{ color: draft.showExistingOnly ? "var(--accent-amber)" : "var(--text-muted)" }}>
                    {draft.showExistingOnly ? "ON" : "OFF"}
                  </span>
                  <button
                    id="toggle-existing"
                    role="switch"
                    aria-checked={draft.showExistingOnly}
                    onClick={() => setDraft((p) => ({ ...p, showExistingOnly: !p.showExistingOnly, showNewOnly: !p.showExistingOnly ? false : p.showNewOnly }))}
                    className="relative inline-flex h-7 w-12 items-center rounded-full transition-colors"
                    style={{
                      backgroundColor: draft.showExistingOnly ? "var(--accent-amber)" : "var(--border-default)",
                      border: "2px solid transparent",
                    }}
                    onFocus={(e) => { e.currentTarget.style.border = "2px solid white"; e.currentTarget.style.boxShadow = "0 0 0 2px var(--accent-cyan)"; }}
                    onBlur={(e) => { e.currentTarget.style.border = "2px solid transparent"; e.currentTarget.style.boxShadow = "none"; }}
                    data-testid="toggle-existing-only"
                  >
                    <span className="sr-only">Toggle Existing Tests Only</span>
                    <span
                      className="inline-block h-5 w-5 rounded-full bg-white transition-transform duration-200"
                      style={{ transform: draft.showExistingOnly ? "translateX(22px)" : "translateX(2px)" }}
                    />
                  </button>
                </div>
              </div>
            </div>
          </section>
        </div>

        <footer
          className="shrink-0 px-6 py-4 flex items-center justify-between gap-4"
          style={{ borderTop: "1px solid var(--border-strong)", background: "var(--bg-elevated)" }}
        >
          <button
            onClick={onReset}
            className="px-5 py-3 text-sm font-bold rounded-lg transition-colors"
            style={{
              color: "var(--text-primary)",
              background: "transparent",
              border: "2px solid var(--border-strong)",
            }}
            onFocus={(e) => inputFocusStyle(e.currentTarget)}
            onBlur={(e) => { e.currentTarget.style.borderColor = "var(--border-strong)"; e.currentTarget.style.boxShadow = "none"; }}
            data-testid="button-clear-filters-bottom"
          >
            Clear All
          </button>
          <button
            ref={applyButtonRef}
            onClick={onApply}
            disabled={!hasDraftChanges}
            className="flex-1 flex items-center justify-center gap-2 px-5 py-3 text-sm font-bold rounded-lg transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            style={{
              backgroundColor: hasDraftChanges ? "var(--accent-cyan)" : "var(--bg-hover, var(--bg-elevated))",
              color: hasDraftChanges ? "#000" : "var(--text-muted)",
              border: "2px solid transparent",
            }}
            onFocus={(e) => { e.currentTarget.style.border = "2px solid white"; e.currentTarget.style.boxShadow = "0 0 0 2px var(--accent-cyan)"; }}
            onBlur={(e) => { e.currentTarget.style.border = "2px solid transparent"; e.currentTarget.style.boxShadow = "none"; }}
            aria-disabled={!hasDraftChanges}
            data-testid="button-apply-filters"
          >
            <Filter className="w-4 h-4" aria-hidden="true" />
            Apply Filters
          </button>
        </footer>
      </div>
    </>
  );
}

export default function TestCasesPage() {
  const [appliedFilters, setAppliedFilters] = useState<FilterState>({ ...EMPTY_FILTERS });
  const [draftFilters, setDraftFilters] = useState<FilterState>({ ...EMPTY_FILTERS });
  const [filterOpen, setFilterOpen] = useState(false);

  const { data, isLoading } = useQuery<TestCasesResponse>({
    queryKey: ["/api/tests/cases"],
  });

  const categories = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.tests.map((t) => t.category))].sort();
  }, [data]);

  const featureAreas = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.tests.map((t) => t.feature_area))].sort();
  }, [data]);

  const filtered = useMemo(() => {
    if (!data) return [];
    const f = appliedFilters;
    return data.tests.filter((t) => {
      if (f.showNewOnly && !t.is_new) return false;
      if (f.showExistingOnly && t.is_new) return false;
      if (f.selectedCategory !== "all" && t.category !== f.selectedCategory) return false;
      if (f.selectedFeature !== "all" && t.feature_area !== f.selectedFeature) return false;
      if (f.search) {
        const s = f.search.toLowerCase();
        if (!t.name.toLowerCase().includes(s) && !t.feature_area.toLowerCase().includes(s) && !t.file_path.toLowerCase().includes(s)) return false;
      }
      if (f.nameFilter && !t.name.toLowerCase().includes(f.nameFilter.toLowerCase())) return false;
      if (f.filePathFilter && !t.file_path.toLowerCase().includes(f.filePathFilter.toLowerCase())) return false;
      return true;
    });
  }, [data, appliedFilters]);

  const activeFilterCount = countActiveFilters(appliedFilters);
  const draftFilterCount = countActiveFilters(draftFilters);

  const openFilters = useCallback(() => {
    setDraftFilters({ ...appliedFilters });
    setFilterOpen(true);
  }, [appliedFilters]);

  const applyFilters = useCallback(() => {
    setAppliedFilters({ ...draftFilters });
    setFilterOpen(false);
  }, [draftFilters]);

  const clearDraft = useCallback(() => {
    setDraftFilters({ ...EMPTY_FILTERS });
  }, []);

  const clearApplied = useCallback(() => {
    setAppliedFilters({ ...EMPTY_FILTERS });
    setDraftFilters({ ...EMPTY_FILTERS });
  }, []);

  const summary = data?.summary;
  const hasDraftChanges = JSON.stringify(draftFilters) !== JSON.stringify(appliedFilters);

  const activeChips = useMemo(() => {
    const f = appliedFilters;
    const chips: { label: string; key: keyof FilterState; resetValue: any }[] = [];
    if (f.search) chips.push({ label: `Search: "${f.search}"`, key: "search", resetValue: "" });
    if (f.nameFilter) chips.push({ label: `Name: "${f.nameFilter}"`, key: "nameFilter", resetValue: "" });
    if (f.filePathFilter) chips.push({ label: `Path: "${f.filePathFilter}"`, key: "filePathFilter", resetValue: "" });
    if (f.selectedCategory !== "all") chips.push({ label: formatCategory(f.selectedCategory), key: "selectedCategory", resetValue: "all" });
    if (f.selectedFeature !== "all") chips.push({ label: f.selectedFeature, key: "selectedFeature", resetValue: "all" });
    if (f.showNewOnly) chips.push({ label: "New Only", key: "showNewOnly", resetValue: false });
    if (f.showExistingOnly) chips.push({ label: "Existing Only", key: "showExistingOnly", resetValue: false });
    return chips;
  }, [appliedFilters]);

  const removeChip = useCallback((key: keyof FilterState, resetValue: any) => {
    setAppliedFilters((prev) => ({ ...prev, [key]: resetValue }));
    setDraftFilters((prev) => ({ ...prev, [key]: resetValue }));
  }, []);

  return (
    <Layout>
      <div className="space-y-6">
        <div className="page-title-bar">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2.5" style={{ color: "var(--text-primary)" }} data-testid="text-testcases-title">
              <FlaskConical className="h-6 w-6" style={{ color: "var(--accent-violet)" }} />
              Test Cases
            </h1>
            <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
              Complete test suite coverage for CareOrbit platform
            </p>
          </div>
          <button
            onClick={openFilters}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 shrink-0"
            style={{
              background: activeFilterCount > 0 ? "var(--accent-cyan-dim)" : "var(--bg-elevated)",
              border: `1px solid ${activeFilterCount > 0 ? "var(--accent-cyan)" : "var(--border-default)"}`,
              color: activeFilterCount > 0 ? "var(--accent-cyan)" : "var(--text-secondary)",
            }}
            data-testid="button-open-filters"
          >
            <Filter className="h-4 w-4" />
            Filters
            {activeFilterCount > 0 && (
              <span className="text-[10px] font-bold w-5 h-5 rounded-full flex items-center justify-center" style={{ background: "var(--accent-cyan)", color: "#fff" }}>
                {activeFilterCount}
              </span>
            )}
            <ChevronRight className="h-3.5 w-3.5" />
          </button>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="page-card p-5">
                <Skeleton className="h-4 w-24 mb-3" />
                <Skeleton className="h-8 w-16" />
              </div>
            ))}
          </div>
        ) : summary ? (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="page-card p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Total Tests</span>
                <ListChecks className="h-4 w-4" style={{ color: "var(--accent-cyan)" }} />
              </div>
              <div className="font-mono text-2xl font-bold" style={{ color: "var(--text-primary)" }} data-testid="text-total-tests">{summary.total}</div>
              <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>Across all categories</p>
            </div>
            <div className="page-card p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>New Tests</span>
                <Sparkles className="h-4 w-4" style={{ color: "var(--accent-emerald)" }} />
              </div>
              <div className="font-mono text-2xl font-bold" style={{ color: "var(--accent-emerald)" }} data-testid="text-new-tests">{summary.new_count}</div>
              <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>Prompt 3 test cases</p>
            </div>
            <div className="page-card p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Existing Tests</span>
                <Archive className="h-4 w-4" style={{ color: "var(--accent-amber)" }} />
              </div>
              <div className="font-mono text-2xl font-bold" style={{ color: "var(--accent-amber)" }} data-testid="text-existing-tests">{summary.existing_count}</div>
              <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>Phase 1 & 2 coverage</p>
            </div>
          </div>
        ) : null}

        {activeChips.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>Active:</span>
            {activeChips.map((chip, i) => (
              <button
                key={i}
                onClick={() => removeChip(chip.key, chip.resetValue)}
                className="flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-full transition-colors group"
                style={{ background: "var(--accent-cyan-dim)", color: "var(--accent-cyan)" }}
                data-testid={`chip-filter-${i}`}
              >
                {chip.label}
                <X className="h-3 w-3 opacity-60 group-hover:opacity-100" />
              </button>
            ))}
            <button onClick={clearApplied} className="text-xs underline ml-1" style={{ color: "var(--accent-rose)" }} data-testid="button-clear-all-chips">
              Clear all
            </button>
          </div>
        )}

        <div className="flex items-center justify-between">
          <span className="text-sm font-mono" style={{ color: "var(--text-muted)" }} data-testid="text-filtered-count">
            Showing {filtered.length} of {summary?.total || 0} tests
          </span>
        </div>

        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-16 w-full rounded-lg" />
            ))}
          </div>
        ) : (
          <div className="space-y-2" data-testid="test-case-list">
            {filtered.map((tc, idx) => {
              const catColor = CATEGORY_COLORS[tc.category] || CATEGORY_COLORS.other;
              return (
                <div
                  key={`${tc.file_path}-${tc.name}-${idx}`}
                  className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 p-3.5 rounded-xl transition-all duration-200"
                  style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--border-default)"; e.currentTarget.style.boxShadow = "0 2px 12px rgba(0,0,0,0.08)"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--border-subtle)"; e.currentTarget.style.boxShadow = "none"; }}
                  data-testid={`row-test-${idx}`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-sm" style={{ color: "var(--text-primary)" }} data-testid={`text-test-name-${idx}`}>
                        {formatTestName(tc.name)}
                      </span>
                      {tc.is_new && (
                        <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded" style={{ background: "var(--accent-emerald-dim)", color: "var(--accent-emerald)" }} data-testid={`badge-new-${idx}`}>
                          NEW
                        </span>
                      )}
                    </div>
                    <p className="text-xs mt-0.5 truncate font-mono" style={{ color: "var(--text-muted)" }} data-testid={`text-file-path-${idx}`}>
                      {tc.file_path}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Badge variant="outline" className="text-xs" style={{ borderColor: "var(--border-default)", color: "var(--text-secondary)" }} data-testid={`badge-feature-${idx}`}>
                      {tc.feature_area}
                    </Badge>
                    <span className="text-[10px] font-medium uppercase tracking-wider px-2 py-1 rounded-md" style={{ background: catColor.bg, color: catColor.text }} data-testid={`badge-category-${idx}`}>
                      {formatCategory(tc.category)}
                    </span>
                  </div>
                </div>
              );
            })}
            {filtered.length === 0 && (
              <div className="text-center py-12 rounded-xl" style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}>
                <FlaskConical className="h-10 w-10 mx-auto mb-3" style={{ color: "var(--text-muted)", opacity: 0.4 }} />
                <p className="text-sm font-medium" style={{ color: "var(--text-secondary)" }} data-testid="text-no-results">No tests match your filters</p>
                <button onClick={clearApplied} className="text-xs mt-2 underline" style={{ color: "var(--accent-cyan)" }} data-testid="button-clear-filters-empty">
                  Clear all filters
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      <AccessibleFilterPanel
        open={filterOpen}
        onClose={() => setFilterOpen(false)}
        draft={draftFilters}
        setDraft={setDraftFilters}
        onApply={applyFilters}
        onReset={clearDraft}
        hasDraftChanges={hasDraftChanges}
        draftFilterCount={draftFilterCount}
        categories={categories}
        featureAreas={featureAreas}
        summary={summary}
      />
    </Layout>
  );
}
