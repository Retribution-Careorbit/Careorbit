import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Layout } from "@/components/layout";
import { FadeIn, StaggerContainer, StaggerItem, HoverCard } from "@/components/animations";
import { Pill, AlertTriangle } from "lucide-react";

interface Medication {
  name: string;
  dosage?: string;
  frequency?: string;
  confidence?: number;
  confidence_label?: string;
  interactions?: any[];
}

const CONFIDENCE_STYLES: Record<string, { badge: string; border: string }> = {
  VERIFIED: {
    badge: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800",
    border: "border-l-emerald-500",
  },
  HIGH: {
    badge: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 border-blue-200 dark:border-blue-800",
    border: "border-l-blue-500",
  },
  MODERATE: {
    badge: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300 border-amber-200 dark:border-amber-800",
    border: "border-l-amber-500",
  },
  LOW: {
    badge: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300 border-red-200 dark:border-red-800",
    border: "border-l-red-500",
  },
};

export default function MedicationsPage() {
  const { data, isLoading } = useQuery<{ medications: Medication[] }>({
    queryKey: ["/api/patients/medications"],
  });

  const medications = data?.medications || [];

  const getConfidenceBadge = (label?: string) => {
    const style = label ? CONFIDENCE_STYLES[label] : undefined;
    const badgeClass = style?.badge || "border-muted";
    const displayLabel = label ? label.charAt(0) + label.slice(1).toLowerCase() : "Unknown";
    return <Badge className={`${badgeClass} border font-medium text-xs`} data-testid={`badge-confidence-${(label || "unknown").toLowerCase()}`}>{displayLabel}</Badge>;
  };

  const getBorderClass = (label?: string) => {
    return label ? (CONFIDENCE_STYLES[label]?.border || "") : "";
  };

  return (
    <Layout>
      <div className="space-y-6">
        <FadeIn>
          <div>
            <h1 className="text-3xl font-heading font-bold tracking-tight" data-testid="text-medications-title">Medications</h1>
            <p className="text-muted-foreground mt-1.5">
              Your current medications with confidence scores and interaction alerts
            </p>
          </div>
        </FadeIn>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <Card key={i}>
                <CardContent className="p-6">
                  <Skeleton className="h-6 w-32 mb-3" />
                  <Skeleton className="h-4 w-48 mb-2" />
                  <Skeleton className="h-4 w-36" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : medications.length === 0 ? (
          <FadeIn delay={0.1}>
            <Card>
              <CardContent className="p-12 text-center">
                <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
                  <Pill className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="text-lg font-heading font-medium" data-testid="text-no-medications">No medications found</p>
                <p className="text-muted-foreground mt-1">
                  Upload a prescription to get started
                </p>
              </CardContent>
            </Card>
          </FadeIn>
        ) : (
          <StaggerContainer className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {medications.map((med, i) => (
              <StaggerItem key={i}>
                <HoverCard>
                  <Card className={`border-l-4 ${getBorderClass(med.confidence_label)} overflow-hidden`} data-testid={`card-medication-${i}`}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg flex items-center gap-2 font-heading">
                          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                            <Pill className="h-4 w-4 text-primary" />
                          </div>
                          {med.name}
                        </CardTitle>
                        {getConfidenceBadge(med.confidence_label)}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-1.5 text-sm">
                        {med.dosage && (
                          <p><span className="text-muted-foreground">Dosage:</span> <span className="font-medium">{med.dosage}</span></p>
                        )}
                        {med.frequency && (
                          <p><span className="text-muted-foreground">Frequency:</span> <span className="font-medium">{med.frequency}</span></p>
                        )}
                        {med.confidence !== undefined && (
                          <p><span className="text-muted-foreground">Confidence:</span> <span className="font-medium">{(med.confidence * 100).toFixed(0)}%</span></p>
                        )}
                        {med.interactions && med.interactions.length > 0 && (
                          <div className="mt-3 p-3 rounded-lg bg-destructive/5 border border-destructive/20" data-testid={`alert-interaction-${i}`}>
                            <div className="flex items-center gap-1.5 text-destructive font-medium text-sm">
                              <AlertTriangle className="h-4 w-4" />
                              Interaction Alerts
                            </div>
                            {med.interactions.map((int: any, j: number) => (
                              <p key={j} className="text-xs mt-1.5 text-muted-foreground">{int.description || JSON.stringify(int)}</p>
                            ))}
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </HoverCard>
              </StaggerItem>
            ))}
          </StaggerContainer>
        )}
      </div>
    </Layout>
  );
}
