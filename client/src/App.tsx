import { Switch, Route } from "wouter";
import { Suspense, lazy } from "react";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/theme-provider";
import { useAuthStore } from "@/lib/auth";
import { SOSButton } from "@/components/emergency";

const NotFound = lazy(() => import("@/pages/not-found"));
const LoginPage = lazy(() => import("@/pages/login"));
const RegisterPage = lazy(() => import("@/pages/register"));
const AuthCallbackPage = lazy(() => import("@/pages/auth-callback"));
const DashboardPage = lazy(() => import("@/pages/dashboard"));
const MedicationsPage = lazy(() => import("@/pages/medications"));
const DocumentsPage = lazy(() => import("@/pages/documents"));
const ChatPage = lazy(() => import("@/pages/chat"));
const RemindersPage = lazy(() => import("@/pages/reminders"));
const SettingsPage = lazy(() => import("@/pages/settings"));
const TestCasesPage = lazy(() => import("@/pages/test-cases"));
const OnboardingPage = lazy(() => import("@/pages/onboarding"));
const OrbitScorePage = lazy(() => import("@/pages/orbit-score"));
const AppointmentsPage = lazy(() => import("@/pages/appointments"));
const HealthInsightsPage = lazy(() => import("@/pages/health-insights"));

function RouteLoader() {
  return (
    <div className="min-h-screen w-full flex items-center justify-center text-sm" style={{ color: "var(--text-muted)" }}>
      Loading...
    </div>
  );
}

function AuthenticatedRoutes() {
  return (
    <Switch>
      <Route path="/"><DashboardPage /></Route>
      <Route path="/onboarding"><OnboardingPage /></Route>
      <Route path="/medications"><MedicationsPage /></Route>
      <Route path="/documents"><DocumentsPage /></Route>
      <Route path="/chat"><ChatPage /></Route>
      <Route path="/reminders"><RemindersPage /></Route>
      <Route path="/settings"><SettingsPage /></Route>
      <Route path="/test-cases"><TestCasesPage /></Route>
      <Route path="/orbit-score"><OrbitScorePage /></Route>
      <Route path="/appointments"><AppointmentsPage /></Route>
      <Route path="/health-insights"><HealthInsightsPage /></Route>
      <Route><NotFound /></Route>
    </Switch>
  );
}

function UnauthenticatedRoutes() {
  return (
    <Switch>
      <Route path="/auth/callback"><AuthCallbackPage /></Route>
      <Route path="/register"><RegisterPage /></Route>
      <Route path="/"><LoginPage /></Route>
      <Route><LoginPage /></Route>
    </Switch>
  );
}

function Router() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return (
    <Suspense fallback={<RouteLoader />}>
      {isAuthenticated ? (
        <>
          <AuthenticatedRoutes />
          <SOSButton />
        </>
      ) : (
        <UnauthenticatedRoutes />
      )}
    </Suspense>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <TooltipProvider>
          <Toaster />
          <Router />
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
