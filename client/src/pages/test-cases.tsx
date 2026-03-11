import { useState, useMemo, useEffect, useRef } from "react";
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
  Filter, X, SlidersHorizontal, Type, Layers, FolderOpen, ToggleLeft, ChevronRight,
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

const CATEGORY_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  unit: { bg: "var(--accent-cyan-dim)", text: "var(--accent-cyan)", border: "var(--accent-cyan)" },
  functional: { bg: "var(--accent-emerald-dim)", text: "var(--accent-emerald)", border: "var(--accent-emerald)" },
  integration: { bg: "var(--accent-violet-dim)", text: "var(--accent-violet)", border: "var(--accent-violet)" },
  e2e: { bg: "var(--accent-amber-dim)", text: "var(--accent-amber)", border: "var(--accent-amber)" },
  security: { bg: "var(--accent-rose-dim)", text: "var(--accent-rose)", border: "var(--accent-rose)" },
  business_logic: { bg: "var(--accent-amber-dim)", text: "var(--accent-amber)", border: "var(--accent-amber)" },
  regression: { bg: "var(--border-subtle)", text: "var(--text-secondary)", border: "var(--border-default)" },
  false_positive_negative: { bg: "var(--accent-rose-dim)", text: "var(--accent-rose)", border: "var(--accent-rose)" },
  other: { bg: "var(--border-subtle)", text: "var(--text-muted)", border: "var(--border-default)" },
};

function formatTestName(name: string): string {
  return name.replace(/^test_/, "").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatCategory(cat: string): string {
  return cat.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function FilterPanel({
  open,
  onClose,
  search, setSearch,
  nameFilter, setNameFilter,
  filePathFilter, setFilePathFilter,
  selectedCategory, setSelectedCategory,
  selectedFeature, setSelectedFeature,
  showNewOnly, setShowNewOnly,
  showExistingOnly, setShowExistingOnly,
  categories,
  featureAreas,
  summary,
  activeFilterCount,
  clearAllFilters,
}: {
  open: boolean;
  onClose: () => void;
  search: string; setSearch: (v: string) => void;
  nameFilter: string; setNameFilter: (v: string) => void;
  filePathFilter: string; setFilePathFilter: (v: string) => void;
  selectedCategory: string; setSelectedCategory: (v: string) => void;
  selectedFeature: string; setSelectedFeature: (v: string) => void;
  showNewOnly: boolean; setShowNewOnly: (v: boolean) => void;
  showExistingOnly: boolean; setShowExistingOnly: (v: boolean) => void;
  categories: string[];
  featureAreas: string[];
  summary: TestSummary | undefined;
  activeFilterCount: number;
  clearAllFilters: () => void;
}) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open, onClose]);

  return (
    <>
      <div
        className="fixed inset-0 z-40 transition-opacity duration-300"
        style={{
          background: "rgba(0,0,0,0.4)",
          backdropFilter: "blur(4px)",
          opacity: open ? 1 : 0,
          pointerEvents: open ? "auto" : "none",
        }}
        onClick={onClose}
        data-testid="filter-overlay"
      />

      <div
        ref={panelRef}
        className="fixed top-0 right-0 z-50 h-full flex flex-col transition-transform duration-300 ease-out"
        style={{
          width: "min(480px, 50vw)",
          transform: open ? "translateX(0)" : "translateX(100%)",
          background: "var(--bg-surface)",
          borderLeft: "1px solid var(--border-subtle)",
          boxShadow: open ? "-8px 0 40px rgba(0,0,0,0.3)" : "none",
        }}
        data-testid="filter-panel"
      >
        <div
          className="flex items-center justify-between px-6 h-[64px] shrink-0"
          style={{ borderBottom: "1px solid var(--border-subtle)" }}
        >
          <div className="flex items-center gap-3">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: "var(--accent-cyan-dim)" }}
            >
              <SlidersHorizontal className="h-4 w-4" style={{ color: "var(--accent-cyan)" }} />
            </div>
            <span className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>Filters</span>
            {activeFilterCount > 0 && (
              <span
                className="text-[10px] font-bold px-1.5 py-0.5 rounded-full"
                style={{ background: "var(--accent-cyan)", color: "#fff" }}
                data-testid="badge-active-filters"
              >
                {activeFilterCount}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {activeFilterCount > 0 && (
              <button
                onClick={clearAllFilters}
                className="flex items-center gap-1 text-xs font-medium rounded-lg px-3 py-1.5 transition-colors"
                style={{ color: "var(--accent-rose)", background: "var(--accent-rose-dim)" }}
                data-testid="button-clear-filters"
              >
                <X className="h-3 w-3" />
                Reset
              </button>
            )}
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors hover:opacity-80"
              style={{ background: "var(--bg-elevated)", color: "var(--text-muted)" }}
              data-testid="button-close-filters"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">
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
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-9 h-9 text-sm"
                    style={{
                      background: "var(--bg-elevated)",
                      border: `1px solid ${search ? "var(--accent-cyan)" : "var(--border-default)"}`,
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
                  value={nameFilter}
                  onChange={(e) => setNameFilter(e.target.value)}
                  className="h-9 text-sm"
                  style={{
                    background: "var(--bg-elevated)",
                    border: `1px solid ${nameFilter ? "var(--accent-cyan)" : "var(--border-default)"}`,
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
                  value={filePathFilter}
                  onChange={(e) => setFilePathFilter(e.target.value)}
                  className="h-9 text-sm"
                  style={{
                    background: "var(--bg-elevated)",
                    border: `1px solid ${filePathFilter ? "var(--accent-cyan)" : "var(--border-default)"}`,
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
                <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                  <SelectTrigger
                    className="h-9 text-sm w-full"
                    style={{
                      background: "var(--bg-elevated)",
                      border: `1px solid ${selectedCategory !== "all" ? "var(--accent-violet)" : "var(--border-default)"}`,
                      color: "var(--text-primary)",
                    }}
                    data-testid="select-category"
                  >
                    <SelectValue placeholder="All Categories" />
                  </SelectTrigger>
                  <SelectContent
                    style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)" }}
                  >
                    <SelectItem value="all">All Categories</SelectItem>
                    {categories.map((cat) => (
                      <SelectItem key={cat} value={cat}>
                        <span className="flex items-center gap-2">
                          <span
                            className="w-2 h-2 rounded-full shrink-0"
                            style={{ background: CATEGORY_COLORS[cat]?.text || "var(--text-muted)" }}
                          />
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
                <Select value={selectedFeature} onValueChange={setSelectedFeature}>
                  <SelectTrigger
                    className="h-9 text-sm w-full"
                    style={{
                      background: "var(--bg-elevated)",
                      border: `1px solid ${selectedFeature !== "all" ? "var(--accent-cyan)" : "var(--border-default)"}`,
                      color: "var(--text-primary)",
                    }}
                    data-testid="select-feature"
                  >
                    <SelectValue placeholder="All Features" />
                  </SelectTrigger>
                  <SelectContent
                    className="max-h-[280px]"
                    style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)" }}
                  >
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
                onClick={() => { setShowNewOnly(!showNewOnly); if (!showNewOnly) setShowExistingOnly(false); }}
                className="w-full flex items-center justify-between p-3 rounded-xl transition-all duration-200"
                style={{
                  background: showNewOnly ? "var(--accent-emerald-dim)" : "var(--bg-elevated)",
                  border: `1px solid ${showNewOnly ? "var(--accent-emerald)" : "var(--border-default)"}`,
                }}
                data-testid="toggle-new-only"
              >
                <div className="flex items-center gap-3">
                  <Sparkles className="h-4 w-4" style={{ color: showNewOnly ? "var(--accent-emerald)" : "var(--text-muted)" }} />
                  <div className="text-left">
                    <span className="text-sm font-medium block" style={{ color: showNewOnly ? "var(--accent-emerald)" : "var(--text-primary)" }}>
                      New Tests Only
                    </span>
                    <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>
                      Show only recently added tests
                    </span>
                  </div>
                </div>
                <div
                  className="w-10 h-5 rounded-full relative transition-colors duration-200"
                  style={{ background: showNewOnly ? "var(--accent-emerald)" : "var(--border-default)" }}
                >
                  <div
                    className="absolute top-0.5 w-4 h-4 rounded-full transition-all duration-200"
                    style={{
                      background: "#fff",
                      left: showNewOnly ? 22 : 2,
                    }}
                  />
                </div>
              </button>

              <button
                onClick={() => { setShowExistingOnly(!showExistingOnly); if (!showExistingOnly) setShowNewOnly(false); }}
                className="w-full flex items-center justify-between p-3 rounded-xl transition-all duration-200"
                style={{
                  background: showExistingOnly ? "var(--accent-amber-dim)" : "var(--bg-elevated)",
                  border: `1px solid ${showExistingOnly ? "var(--accent-amber)" : "var(--border-default)"}`,
                }}
                data-testid="toggle-existing-only"
              >
                <div className="flex items-center gap-3">
                  <Archive className="h-4 w-4" style={{ color: showExistingOnly ? "var(--accent-amber)" : "var(--text-muted)" }} />
                  <div className="text-left">
                    <span className="text-sm font-medium block" style={{ color: showExistingOnly ? "var(--accent-amber)" : "var(--text-primary)" }}>
                      Existing Tests Only
                    </span>
                    <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>
                      Show only phase 1 & 2 tests
                    </span>
                  </div>
                </div>
                <div
                  className="w-10 h-5 rounded-full relative transition-colors duration-200"
                  style={{ background: showExistingOnly ? "var(--accent-amber)" : "var(--border-default)" }}
                >
                  <div
                    className="absolute top-0.5 w-4 h-4 rounded-full transition-all duration-200"
                    style={{
                      background: "#fff",
                      left: showExistingOnly ? 22 : 2,
                    }}
                  />
                </div>
              </button>
            </div>
          </div>
        </div>

        <div
          className="shrink-0 px-6 py-4 flex items-center justify-between"
          style={{ borderTop: "1px solid var(--border-subtle)", background: "var(--bg-elevated)" }}
        >
          <button
            onClick={clearAllFilters}
            className="text-xs font-medium px-3 py-2 rounded-lg transition-colors"
            style={{ color: "var(--text-secondary)", background: "var(--bg-surface)" }}
            data-testid="button-clear-filters-bottom"
          >
            Clear All
          </button>
          <button
            onClick={onClose}
            className="text-xs font-semibold px-5 py-2 rounded-lg transition-colors"
            style={{ background: "var(--accent-cyan)", color: "#fff" }}
            data-testid="button-apply-filters"
          >
            Apply Filters
          </button>
        </div>
      </div>
    </>
  );
}

export default function TestCasesPage() {
  const [search, setSearch] = useState("");
  const [nameFilter, setNameFilter] = useState("");
  const [filePathFilter, setFilePathFilter] = useState("");
  const [showNewOnly, setShowNewOnly] = useState(false);
  const [showExistingOnly, setShowExistingOnly] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedFeature, setSelectedFeature] = useState("all");
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
    return data.tests.filter((t) => {
      if (showNewOnly && !t.is_new) return false;
      if (showExistingOnly && t.is_new) return false;
      if (selectedCategory !== "all" && t.category !== selectedCategory) return false;
      if (selectedFeature !== "all" && t.feature_area !== selectedFeature) return false;
      if (search) {
        const s = search.toLowerCase();
        if (!t.name.toLowerCase().includes(s) &&
            !t.feature_area.toLowerCase().includes(s) &&
            !t.file_path.toLowerCase().includes(s)) return false;
      }
      if (nameFilter && !t.name.toLowerCase().includes(nameFilter.toLowerCase())) return false;
      if (filePathFilter && !t.file_path.toLowerCase().includes(filePathFilter.toLowerCase())) return false;
      return true;
    });
  }, [data, showNewOnly, showExistingOnly, search, nameFilter, filePathFilter, selectedCategory, selectedFeature]);

  const activeFilterCount = [
    showNewOnly,
    showExistingOnly,
    selectedCategory !== "all",
    selectedFeature !== "all",
    search.length > 0,
    nameFilter.length > 0,
    filePathFilter.length > 0,
  ].filter(Boolean).length;

  const clearAllFilters = () => {
    setSearch("");
    setNameFilter("");
    setFilePathFilter("");
    setShowNewOnly(false);
    setShowExistingOnly(false);
    setSelectedCategory("all");
    setSelectedFeature("all");
  };

  const summary = data?.summary;

  const activeChips = useMemo(() => {
    const chips: { label: string; clear: () => void }[] = [];
    if (search) chips.push({ label: `Search: "${search}"`, clear: () => setSearch("") });
    if (nameFilter) chips.push({ label: `Name: "${nameFilter}"`, clear: () => setNameFilter("") });
    if (filePathFilter) chips.push({ label: `Path: "${filePathFilter}"`, clear: () => setFilePathFilter("") });
    if (selectedCategory !== "all") chips.push({ label: formatCategory(selectedCategory), clear: () => setSelectedCategory("all") });
    if (selectedFeature !== "all") chips.push({ label: selectedFeature, clear: () => setSelectedFeature("all") });
    if (showNewOnly) chips.push({ label: "New Only", clear: () => setShowNewOnly(false) });
    if (showExistingOnly) chips.push({ label: "Existing Only", clear: () => setShowExistingOnly(false) });
    return chips;
  }, [search, nameFilter, filePathFilter, selectedCategory, selectedFeature, showNewOnly, showExistingOnly]);

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
            onClick={() => setFilterOpen(true)}
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
              <span
                className="text-[10px] font-bold w-5 h-5 rounded-full flex items-center justify-center"
                style={{ background: "var(--accent-cyan)", color: "#fff" }}
              >
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
                onClick={chip.clear}
                className="flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-full transition-colors group"
                style={{
                  background: "var(--accent-cyan-dim)",
                  color: "var(--accent-cyan)",
                  border: "1px solid transparent",
                }}
                data-testid={`chip-filter-${i}`}
              >
                {chip.label}
                <X className="h-3 w-3 opacity-60 group-hover:opacity-100" />
              </button>
            ))}
            <button
              onClick={clearAllFilters}
              className="text-xs underline ml-1"
              style={{ color: "var(--accent-rose)" }}
              data-testid="button-clear-all-chips"
            >
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
                  style={{
                    background: "var(--bg-card)",
                    border: "1px solid var(--border-subtle)",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = "var(--border-default)";
                    e.currentTarget.style.boxShadow = "0 2px 12px rgba(0,0,0,0.08)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = "var(--border-subtle)";
                    e.currentTarget.style.boxShadow = "none";
                  }}
                  data-testid={`row-test-${idx}`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-sm" style={{ color: "var(--text-primary)" }} data-testid={`text-test-name-${idx}`}>
                        {formatTestName(tc.name)}
                      </span>
                      {tc.is_new && (
                        <span
                          className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded"
                          style={{ background: "var(--accent-emerald-dim)", color: "var(--accent-emerald)" }}
                          data-testid={`badge-new-${idx}`}
                        >
                          NEW
                        </span>
                      )}
                    </div>
                    <p className="text-xs mt-0.5 truncate font-mono" style={{ color: "var(--text-muted)" }} data-testid={`text-file-path-${idx}`}>
                      {tc.file_path}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Badge
                      variant="outline"
                      className="text-xs"
                      style={{ borderColor: "var(--border-default)", color: "var(--text-secondary)" }}
                      data-testid={`badge-feature-${idx}`}
                    >
                      {tc.feature_area}
                    </Badge>
                    <span
                      className="text-[10px] font-medium uppercase tracking-wider px-2 py-1 rounded-md"
                      style={{ background: catColor.bg, color: catColor.text }}
                      data-testid={`badge-category-${idx}`}
                    >
                      {formatCategory(tc.category)}
                    </span>
                  </div>
                </div>
              );
            })}
            {filtered.length === 0 && (
              <div className="text-center py-12 rounded-xl" style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}>
                <FlaskConical className="h-10 w-10 mx-auto mb-3" style={{ color: "var(--text-muted)", opacity: 0.4 }} />
                <p className="text-sm font-medium" style={{ color: "var(--text-secondary)" }} data-testid="text-no-results">
                  No tests match your filters
                </p>
                <button
                  onClick={clearAllFilters}
                  className="text-xs mt-2 underline"
                  style={{ color: "var(--accent-cyan)" }}
                  data-testid="button-clear-filters-empty"
                >
                  Clear all filters
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      <FilterPanel
        open={filterOpen}
        onClose={() => setFilterOpen(false)}
        search={search} setSearch={setSearch}
        nameFilter={nameFilter} setNameFilter={setNameFilter}
        filePathFilter={filePathFilter} setFilePathFilter={setFilePathFilter}
        selectedCategory={selectedCategory} setSelectedCategory={setSelectedCategory}
        selectedFeature={selectedFeature} setSelectedFeature={setSelectedFeature}
        showNewOnly={showNewOnly} setShowNewOnly={setShowNewOnly}
        showExistingOnly={showExistingOnly} setShowExistingOnly={setShowExistingOnly}
        categories={categories}
        featureAreas={featureAreas}
        summary={summary}
        activeFilterCount={activeFilterCount}
        clearAllFilters={clearAllFilters}
      />
    </Layout>
  );
}
