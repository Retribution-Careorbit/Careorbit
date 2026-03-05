import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/theme-provider";
import { useAuthStore } from "@/lib/auth";
import NotFound from "@/pages/not-found";
import LoginPage from "@/pages/login";
import RegisterPage from "@/pages/register";
import DashboardPage from "@/pages/dashboard";
import MedicationsPage from "@/pages/medications";
import DocumentsPage from "@/pages/documents";
import ChatPage from "@/pages/chat";
import RemindersPage from "@/pages/reminders";
import SettingsPage from "@/pages/settings";
import TestCasesPage from "@/pages/test-cases";

function AuthenticatedRoutes() {
  return (
    <Switch>
      <Route path="/" component={DashboardPage} />
      <Route path="/medications" component={MedicationsPage} />
      <Route path="/documents" component={DocumentsPage} />
      <Route path="/chat" component={ChatPage} />
      <Route path="/reminders" component={RemindersPage} />
      <Route path="/settings" component={SettingsPage} />
      <Route path="/test-cases" component={TestCasesPage} />
      <Route component={NotFound} />
    </Switch>
  );
}

function UnauthenticatedRoutes() {
  return (
    <Switch>
      <Route path="/register" component={RegisterPage} />
      <Route path="/" component={LoginPage} />
      <Route component={LoginPage} />
    </Switch>
  );
}

function Router() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return isAuthenticated ? <AuthenticatedRoutes /> : <UnauthenticatedRoutes />;
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
