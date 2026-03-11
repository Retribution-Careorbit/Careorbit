import { useState, useMemo, useEffect, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Layout } from "@/components/layout";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  FlaskConical, Search, ListChecks, Sparkles, Archive,
  Filter, X, SlidersHorizontal, Type, Layers, FolderOpen, ToggleLeft, ChevronRight, Check,
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

function FilterPanelContent({
  draft,
  setDraft,
  categories,
  featureAreas,
  summary,
}: {
  draft: FilterState;
  setDraft: (fn: (prev: FilterState) => FilterState) => void;
  categories: string[];
  featureAreas: string[];
  summary: TestSummary | undefined;
}) {
  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Type className="h-3.5 w-3.5" style={{ color: "var(--accent-cyan)" }} />
          <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
            String Filters
          </span>
        </div>
        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--text-secondary)" }}>
              Search All Fields
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5" style={{ color: "var(--text-muted)" }} />
              <Input
                placeholder="Search by name, feature, path..."
                value={draft.search}
                onChange={(e) => setDraft((p) => ({ ...p, search: e.target.value }))}
                className="pl-9 h-9 text-sm"
                style={{
                  background: "var(--bg-elevated)",
                  border: `1px solid ${draft.search ? "var(--accent-cyan)" : "var(--border-default)"}`,
                  color: "var(--text-primary)",
                }}
                data-testid="input-search-tests"
              />
            </div>
          </div>
          <div>
            <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--text-secondary)" }}>
              Test Name Contains
            </label>
            <Input
              placeholder="e.g. login, validation, orbit..."
              value={draft.nameFilter}
              onChange={(e) => setDraft((p) => ({ ...p, nameFilter: e.target.value }))}
              className="h-9 text-sm"
              style={{
                background: "var(--bg-elevated)",
                border: `1px solid ${draft.nameFilter ? "var(--accent-cyan)" : "var(--border-default)"}`,
                color: "var(--text-primary)",
              }}
              data-testid="input-name-filter"
            />
          </div>
          <div>
            <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--text-secondary)" }}>
              File Path Contains
            </label>
            <Input
              placeholder="e.g. unit, integration, api..."
              value={draft.filePathFilter}
              onChange={(e) => setDraft((p) => ({ ...p, filePathFilter: e.target.value }))}
              className="h-9 text-sm"
              style={{
                background: "var(--bg-elevated)",
                border: `1px solid ${draft.filePathFilter ? "var(--accent-cyan)" : "var(--border-default)"}`,
                color: "var(--text-primary)",
              }}
              data-testid="input-filepath-filter"
            />
          </div>
        </div>
      </div>

      <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: 24 }}>
        <div className="flex items-center gap-2 mb-3">
          <Layers className="h-3.5 w-3.5" style={{ color: "var(--accent-violet)" }} />
          <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
            Dropdown Filters
          </span>
        </div>
        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--text-secondary)" }}>
              Category
            </label>
            <Select value={draft.selectedCategory} onValueChange={(v) => setDraft((p) => ({ ...p, selectedCategory: v }))}>
              <SelectTrigger
                className="h-9 text-sm w-full"
                style={{
                  background: "var(--bg-elevated)",
                  border: `1px solid ${draft.selectedCategory !== "all" ? "var(--accent-violet)" : "var(--border-default)"}`,
                  color: "var(--text-primary)",
                }}
                data-testid="select-category"
              >
                <SelectValue placeholder="All Categories" />
              </SelectTrigger>
              <SelectContent style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)" }}>
                <SelectItem value="all">All Categories</SelectItem>
                {categories.map((cat) => (
                  <SelectItem key={cat} value={cat}>
                    <span className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full shrink-0" style={{ background: CATEGORY_COLORS[cat]?.text || "var(--text-muted)" }} />
                      {formatCategory(cat)}
                      {summary?.by_category?.[cat] ? ` (${summary.by_category[cat]})` : ""}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-xs font-medium mb-1.5 block" style={{ color: "var(--text-secondary)" }}>
              Feature Area
            </label>
            <Select value={draft.selectedFeature} onValueChange={(v) => setDraft((p) => ({ ...p, selectedFeature: v }))}>
              <SelectTrigger
                className="h-9 text-sm w-full"
                style={{
                  background: "var(--bg-elevated)",
                  border: `1px solid ${draft.selectedFeature !== "all" ? "var(--accent-cyan)" : "var(--border-default)"}`,
                  color: "var(--text-primary)",
                }}
                data-testid="select-feature"
              >
                <SelectValue placeholder="All Features" />
              </SelectTrigger>
              <SelectContent className="max-h-[280px]" style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)" }}>
                <SelectItem value="all">All Features</SelectItem>
                {featureAreas.map((feat) => (
                  <SelectItem key={feat} value={feat}>
                    <span className="flex items-center gap-2">
                      <FolderOpen className="h-3 w-3 shrink-0" style={{ color: "var(--text-muted)" }} />
                      {feat}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: 24 }}>
        <div className="flex items-center gap-2 mb-3">
          <ToggleLeft className="h-3.5 w-3.5" style={{ color: "var(--accent-emerald)" }} />
          <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
            Toggle Filters
          </span>
        </div>
        <div className="space-y-2">
          <button
            onClick={() => setDraft((p) => ({ ...p, showNewOnly: !p.showNewOnly, showExistingOnly: !p.showNewOnly ? false : p.showExistingOnly }))}
            className="w-full flex items-center justify-between p-3 rounded-xl transition-all duration-200"
            style={{
              background: draft.showNewOnly ? "var(--accent-emerald-dim)" : "var(--bg-elevated)",
              border: `1px solid ${draft.showNewOnly ? "var(--accent-emerald)" : "var(--border-default)"}`,
            }}
            data-testid="toggle-new-only"
          >
            <div className="flex items-center gap-3">
              <Sparkles className="h-4 w-4" style={{ color: draft.showNewOnly ? "var(--accent-emerald)" : "var(--text-muted)" }} />
              <div className="text-left">
                <span className="text-sm font-medium block" style={{ color: draft.showNewOnly ? "var(--accent-emerald)" : "var(--text-primary)" }}>
                  New Tests Only
                </span>
                <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>Show only recently added tests</span>
              </div>
            </div>
            <div className="w-10 h-5 rounded-full relative transition-colors duration-200" style={{ background: draft.showNewOnly ? "var(--accent-emerald)" : "var(--border-default)" }}>
              <div className="absolute top-0.5 w-4 h-4 rounded-full transition-all duration-200" style={{ background: "#fff", left: draft.showNewOnly ? 22 : 2 }} />
            </div>
          </button>

          <button
            onClick={() => setDraft((p) => ({ ...p, showExistingOnly: !p.showExistingOnly, showNewOnly: !p.showExistingOnly ? false : p.showNewOnly }))}
            className="w-full flex items-center justify-between p-3 rounded-xl transition-all duration-200"
            style={{
              background: draft.showExistingOnly ? "var(--accent-amber-dim)" : "var(--bg-elevated)",
              border: `1px solid ${draft.showExistingOnly ? "var(--accent-amber)" : "var(--border-default)"}`,
            }}
            data-testid="toggle-existing-only"
          >
            <div className="flex items-center gap-3">
              <Archive className="h-4 w-4" style={{ color: draft.showExistingOnly ? "var(--accent-amber)" : "var(--text-muted)" }} />
              <div className="text-left">
                <span className="text-sm font-medium block" style={{ color: draft.showExistingOnly ? "var(--accent-amber)" : "var(--text-primary)" }}>
                  Existing Tests Only
                </span>
                <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>Show only phase 1 & 2 tests</span>
              </div>
            </div>
            <div className="w-10 h-5 rounded-full relative transition-colors duration-200" style={{ background: draft.showExistingOnly ? "var(--accent-amber)" : "var(--border-default)" }}>
              <div className="absolute top-0.5 w-4 h-4 rounded-full transition-all duration-200" style={{ background: "#fff", left: draft.showExistingOnly ? 22 : 2 }} />
            </div>
          </button>
        </div>
      </div>
    </div>
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

  useEffect(() => {
    if (!filterOpen) return;
    const handleKey = (e: KeyboardEvent) => { if (e.key === "Escape") setFilterOpen(false); };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [filterOpen]);

  const summary = data?.summary;

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

  const hasDraftChanges = JSON.stringify(draftFilters) !== JSON.stringify(appliedFilters);

  return (
    <Layout>
      <div className="flex relative">
        <div className={`space-y-6 transition-all duration-300 ${filterOpen ? "pr-4" : ""}`} style={{ flex: filterOpen ? "1 1 0" : "1 1 100%", minWidth: 0 }}>
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
              onClick={filterOpen ? () => setFilterOpen(false) : openFilters}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 shrink-0"
              style={{
                background: filterOpen ? "var(--accent-cyan)" : activeFilterCount > 0 ? "var(--accent-cyan-dim)" : "var(--bg-elevated)",
                border: `1px solid ${filterOpen ? "var(--accent-cyan)" : activeFilterCount > 0 ? "var(--accent-cyan)" : "var(--border-default)"}`,
                color: filterOpen ? "#fff" : activeFilterCount > 0 ? "var(--accent-cyan)" : "var(--text-secondary)",
              }}
              data-testid="button-open-filters"
            >
              <Filter className="h-4 w-4" />
              Filters
              {activeFilterCount > 0 && !filterOpen && (
                <span className="text-[10px] font-bold w-5 h-5 rounded-full flex items-center justify-center" style={{ background: "var(--accent-cyan)", color: "#fff" }}>
                  {activeFilterCount}
                </span>
              )}
              {filterOpen ? <X className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
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

        <div
          className="shrink-0 transition-all duration-300 overflow-hidden"
          style={{
            width: filterOpen ? "min(460px, 45vw)" : 0,
            opacity: filterOpen ? 1 : 0,
          }}
          data-testid="filter-panel"
        >
          <div
            className="rounded-2xl flex flex-col sticky top-2"
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border-subtle)",
              boxShadow: "0 4px 24px rgba(0,0,0,0.12)",
              maxHeight: "calc(100vh - 140px)",
            }}
          >
            <div className="flex items-center justify-between px-5 py-4 shrink-0" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: "var(--accent-cyan-dim)" }}>
                  <SlidersHorizontal className="h-3.5 w-3.5" style={{ color: "var(--accent-cyan)" }} />
                </div>
                <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Filters</span>
                {draftFilterCount > 0 && (
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full" style={{ background: "var(--accent-cyan)", color: "#fff" }} data-testid="badge-active-filters">
                    {draftFilterCount}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {draftFilterCount > 0 && (
                  <button onClick={clearDraft} className="flex items-center gap-1 text-[11px] font-medium rounded-lg px-2.5 py-1 transition-colors" style={{ color: "var(--accent-rose)", background: "var(--accent-rose-dim)" }} data-testid="button-clear-filters">
                    <X className="h-3 w-3" />
                    Reset
                  </button>
                )}
                <button onClick={() => setFilterOpen(false)} className="w-7 h-7 rounded-lg flex items-center justify-center transition-colors hover:opacity-80" style={{ background: "var(--bg-elevated)", color: "var(--text-muted)" }} data-testid="button-close-filters">
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto px-5 py-4">
              <FilterPanelContent
                draft={draftFilters}
                setDraft={setDraftFilters}
                categories={categories}
                featureAreas={featureAreas}
                summary={summary}
              />
            </div>

            <div className="shrink-0 px-5 py-3 flex items-center justify-between" style={{ borderTop: "1px solid var(--border-subtle)", background: "var(--bg-elevated)", borderRadius: "0 0 16px 16px" }}>
              <button onClick={clearDraft} className="text-xs font-medium px-3 py-2 rounded-lg transition-colors" style={{ color: "var(--text-secondary)", background: "var(--bg-surface)" }} data-testid="button-clear-filters-bottom">
                Clear All
              </button>
              <button
                onClick={applyFilters}
                className="flex items-center gap-1.5 text-xs font-semibold px-5 py-2.5 rounded-lg transition-all duration-200"
                style={{
                  background: hasDraftChanges ? "var(--accent-cyan)" : "var(--accent-cyan-dim)",
                  color: hasDraftChanges ? "#fff" : "var(--accent-cyan)",
                  boxShadow: hasDraftChanges ? "0 2px 8px rgba(0, 212, 255, 0.3)" : "none",
                }}
                data-testid="button-apply-filters"
              >
                <Check className="h-3.5 w-3.5" />
                Apply Filters
              </button>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
