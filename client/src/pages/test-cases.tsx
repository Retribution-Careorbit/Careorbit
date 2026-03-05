import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Layout } from "@/components/layout";
import { FlaskConical, Search, ListChecks, Sparkles, Archive } from "lucide-react";

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

const CATEGORY_COLORS: Record<string, string> = {
  unit: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  functional: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  integration: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
  e2e: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
  security: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  business_logic: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  regression: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200",
  false_positive_negative: "bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200",
  other: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
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

  const { data, isLoading } = useQuery<TestCasesResponse>({
    queryKey: ["/api/tests/cases"],
  });

  const filtered = useMemo(() => {
    if (!data) return [];
    return data.tests.filter((t) => {
      if (showNewOnly && !t.is_new) return false;
      if (search && !t.name.toLowerCase().includes(search.toLowerCase()) &&
          !t.feature_area.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [data, showNewOnly, search]);

  const summary = data?.summary;

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2" data-testid="text-testcases-title">
            <FlaskConical className="h-8 w-8 text-primary" />
            Test Cases
          </h1>
          <p className="text-muted-foreground mt-1">
            Complete test suite coverage for CareOrbit platform
          </p>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <Card key={i}>
                <CardHeader className="pb-2"><Skeleton className="h-4 w-24" /></CardHeader>
                <CardContent><Skeleton className="h-8 w-16" /></CardContent>
              </Card>
            ))}
          </div>
        ) : summary ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Total Tests</CardTitle>
                <ListChecks className="h-5 w-5 text-primary" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold" data-testid="text-total-tests">{summary.total}</div>
                <p className="text-xs text-muted-foreground mt-1">Across all categories</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">New Tests</CardTitle>
                <Sparkles className="h-5 w-5 text-chart-1" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-chart-1" data-testid="text-new-tests">{summary.new_count}</div>
                <p className="text-xs text-muted-foreground mt-1">Prompt 3 test cases</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Existing Tests</CardTitle>
                <Archive className="h-5 w-5 text-chart-2" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-chart-2" data-testid="text-existing-tests">{summary.existing_count}</div>
                <p className="text-xs text-muted-foreground mt-1">Phase 1 & 2 coverage</p>
              </CardContent>
            </Card>
          </div>
        ) : null}

        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search tests by name or feature..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
                data-testid="input-search-tests"
              />
            </div>
            <label className="flex items-center gap-2 cursor-pointer select-none" data-testid="toggle-new-only">
              <input
                type="checkbox"
                checked={showNewOnly}
                onChange={(e) => setShowNewOnly(e.target.checked)}
                className="rounded border-gray-300"
                data-testid="input-new-only"
              />
              <span className="text-sm font-medium">Show only new tests</span>
            </label>
          </div>
        </div>

        <div className="text-sm text-muted-foreground" data-testid="text-filtered-count">
          Showing {filtered.length} of {summary?.total || 0} tests
        </div>

        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-16 w-full rounded-lg" />
            ))}
          </div>
        ) : (
          <div className="space-y-2" data-testid="test-case-list">
            {filtered.map((tc, idx) => (
              <div
                key={`${tc.file_path}-${tc.name}`}
                className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                data-testid={`row-test-${idx}`}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-sm" data-testid={`text-test-name-${idx}`}>
                      {formatTestName(tc.name)}
                    </span>
                    {tc.is_new && (
                      <Badge className="bg-emerald-500 text-white text-xs px-1.5 py-0" data-testid={`badge-new-${idx}`}>
                        NEW
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5 truncate" data-testid={`text-file-path-${idx}`}>
                    {tc.file_path}
                  </p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <Badge variant="outline" className="text-xs" data-testid={`badge-feature-${idx}`}>
                    {tc.feature_area}
                  </Badge>
                  <Badge
                    className={`text-xs ${CATEGORY_COLORS[tc.category] || CATEGORY_COLORS.other}`}
                    data-testid={`badge-category-${idx}`}
                  >
                    {formatCategory(tc.category)}
                  </Badge>
                </div>
              </div>
            ))}
            {filtered.length === 0 && (
              <div className="text-center py-8 text-muted-foreground" data-testid="text-no-results">
                No tests match your filters
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
}
