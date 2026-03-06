import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { PageTransition } from "@/components/animations";

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full">
        <AppSidebar />
        <main className="flex-1 overflow-auto">
          <div className="flex items-center gap-2 p-4 border-b border-border/50 bg-background/80 backdrop-blur-sm sticky top-0 z-10">
            <SidebarTrigger data-testid="button-sidebar-toggle" />
          </div>
          <div className="p-6 lg:p-8">
            <PageTransition>
              {children}
            </PageTransition>
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
}
