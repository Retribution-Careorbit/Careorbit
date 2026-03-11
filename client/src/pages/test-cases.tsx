import { useState, useMemo } from "react";
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
import { FlaskConical, Search, ListChecks, Sparkles, Archive, Filter, X } from "lucide-react";

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
  return name
    .replace(/^test_/, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatCategory(cat: string): string {
  return cat.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function TestCasesPage() {
  const [search, setSearch] = useState("");
  const [showNewOnly, setShowNewOnly] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedFeature, setSelectedFeature] = useState("all");

  const { data, isLoading } = useQuery<TestCasesResponse>({
    queryKey: ["/api/tests/cases"],
  });

  const categories = useMemo(() => {
    if (!data) return [];
    const cats = [...new Set(data.tests.map((t) => t.category))].sort();
    return cats;
  }, [data]);

  const featureAreas = useMemo(() => {
    if (!data) return [];
    const feats = [...new Set(data.tests.map((t) => t.feature_area))].sort();
    return feats;
  }, [data]);

  const filtered = useMemo(() => {
    if (!data) return [];
    return data.tests.filter((t) => {
      if (showNewOnly && !t.is_new) return false;
      if (selectedCategory !== "all" && t.category !== selectedCategory) return false;
      if (selectedFeature !== "all" && t.feature_area !== selectedFeature) return false;
      if (search && !t.name.toLowerCase().includes(search.toLowerCase()) &&
          !t.feature_area.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [data, showNewOnly, search, selectedCategory, selectedFeature]);

  const activeFilterCount = [
    showNewOnly,
    selectedCategory !== "all",
    selectedFeature !== "all",
    search.length > 0,
  ].filter(Boolean).length;

  const clearAllFilters = () => {
    setSearch("");
    setShowNewOnly(false);
    setSelectedCategory("all");
    setSelectedFeature("all");
  };

  const summary = data?.summary;

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

        <div className="page-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Filter className="h-4 w-4" style={{ color: "var(--accent-cyan)" }} />
            <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Filters</span>
            {activeFilterCount > 0 && (
              <Badge
                className="text-[10px] px-1.5 py-0 cursor-pointer"
                style={{ background: "var(--accent-cyan-dim)", color: "var(--accent-cyan)", border: "none" }}
                data-testid="badge-active-filters"
              >
                {activeFilterCount} active
              </Badge>
            )}
            {activeFilterCount > 0 && (
              <button
                onClick={clearAllFilters}
                className="ml-auto flex items-center gap-1 text-xs font-medium rounded-md px-2 py-1 hover:opacity-80 transition-opacity"
                style={{ color: "var(--accent-rose)", background: "var(--accent-rose-dim)" }}
                data-testid="button-clear-filters"
              >
                <X className="h-3 w-3" />
                Clear all
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4" style={{ color: "var(--text-muted)" }} />
              <Input
                placeholder="Search by name or feature..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 h-9 text-sm font-mono"
                style={{
                  background: "var(--bg-elevated)",
                  border: "1px solid var(--border-default)",
                  color: "var(--text-primary)",
                }}
                data-testid="input-search-tests"
              />
            </div>

            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger
                className="h-9 text-sm"
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
                style={{
                  background: "var(--bg-elevated)",
                  border: "1px solid var(--border-default)",
                }}
              >
                <SelectItem value="all">All Categories</SelectItem>
                {categories.map((cat) => (
                  <SelectItem key={cat} value={cat}>
                    {formatCategory(cat)} {summary?.by_category?.[cat] ? `(${summary.by_category[cat]})` : ""}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={selectedFeature} onValueChange={setSelectedFeature}>
              <SelectTrigger
                className="h-9 text-sm"
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
                className="max-h-[300px]"
                style={{
                  background: "var(--bg-elevated)",
                  border: "1px solid var(--border-default)",
                }}
              >
                <SelectItem value="all">All Features</SelectItem>
                {featureAreas.map((feat) => (
                  <SelectItem key={feat} value={feat}>
                    {feat}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <label
              className="flex items-center gap-2 cursor-pointer select-none h-9 px-3 rounded-md"
              style={{
                background: showNewOnly ? "var(--accent-emerald-dim)" : "var(--bg-elevated)",
                border: `1px solid ${showNewOnly ? "var(--accent-emerald)" : "var(--border-default)"}`,
              }}
              data-testid="toggle-new-only"
            >
              <input
                type="checkbox"
                checked={showNewOnly}
                onChange={(e) => setShowNewOnly(e.target.checked)}
                className="rounded"
                style={{ accentColor: "var(--accent-emerald)" }}
                data-testid="input-new-only"
              />
              <span className="text-sm font-medium" style={{ color: showNewOnly ? "var(--accent-emerald)" : "var(--text-secondary)" }}>
                New only
              </span>
            </label>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm font-mono" style={{ color: "var(--text-muted)" }} data-testid="text-filtered-count">
            Showing {filtered.length} of {summary?.total || 0} tests
          </span>
          {selectedCategory !== "all" && (
            <Badge
              className="text-xs"
              style={{
                background: CATEGORY_COLORS[selectedCategory]?.bg || "var(--border-subtle)",
                color: CATEGORY_COLORS[selectedCategory]?.text || "var(--text-muted)",
                border: "none",
              }}
            >
              {formatCategory(selectedCategory)}
            </Badge>
          )}
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
    </Layout>
  );
}
