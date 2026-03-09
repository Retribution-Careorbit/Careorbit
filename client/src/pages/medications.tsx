import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Layout } from "@/components/layout";
import { FadeIn, StaggerContainer, StaggerItem, HoverCard } from "@/components/animations";
import { AdherenceDonut } from "@/components/charts";
import { Pill, AlertTriangle, Search, Shield, CheckCircle, XCircle } from "lucide-react";

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
  const [search, setSearch] = useState("");
  const [interactionOpen, setInteractionOpen] = useState(false);

  const { data, isLoading } = useQuery<{ medications: Medication[] }>({
    queryKey: ["/api/patients/medications"],
  });

  const medications = data?.medications || [];
  const filteredMeds = medications.filter((m) =>
    m.name.toLowerCase().includes(search.toLowerCase())
  );

  const allInteractions = medications.flatMap((m) =>
    (m.interactions || []).map((ix: any) => ({ ...ix, medicationName: m.name }))
  );

  const verifiedCount = medications.filter((m) => m.confidence_label === "VERIFIED").length;
  const adherenceScore = medications.length > 0 ? Math.round((verifiedCount / medications.length) * 100 + 40) : 0;
  const clampedAdherence = Math.min(adherenceScore, 95);

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
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-heading font-bold tracking-tight" data-testid="text-medications-title">Medications</h1>
              <p className="text-muted-foreground mt-1.5">
                Your current medications with confidence scores and interaction alerts
              </p>
            </div>
            <Dialog open={interactionOpen} onOpenChange={setInteractionOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="shrink-0" data-testid="button-check-interactions">
                  <Shield className="h-4 w-4 mr-2" />
                  Check Interactions
                </Button>
              </DialogTrigger>
              <DialogContent className="glass-strong">
                <DialogHeader>
                  <DialogTitle className="font-heading flex items-center gap-2">
                    <Shield className="h-5 w-5 text-primary" />
                    Drug Interaction Checker
                  </DialogTitle>
                </DialogHeader>
                <div className="space-y-3 mt-2">
                  {allInteractions.length === 0 ? (
                    <div className="text-center py-6">
                      <CheckCircle className="h-10 w-10 text-green-500 mx-auto mb-2" />
                      <p className="font-medium" data-testid="text-no-interactions">No interactions detected</p>
                      <p className="text-sm text-muted-foreground">All your medications appear safe together</p>
                    </div>
                  ) : (
                    allInteractions.map((ix: any, j: number) => (
                      <div key={j} className="p-4 rounded-xl border border-destructive/20 bg-destructive/5">
                        <div className="flex items-center gap-2 mb-1">
                          <AlertTriangle className="h-4 w-4 text-destructive" />
                          <span className="font-medium text-sm">{ix.drug_pair || ix.medicationName}</span>
                          <Badge className="bg-red-500/10 text-red-500 border-red-500/30 text-xs ml-auto">
                            {ix.severity || "Warning"}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">{ix.description || "Potential interaction detected"}</p>
                        {ix.clinical_action && (
                          <p className="text-xs text-primary mt-1">{ix.clinical_action}</p>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </FadeIn>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <FadeIn delay={0.05} className="lg:col-span-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search medications..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
                data-testid="input-search-medications"
              />
            </div>
          </FadeIn>

          <FadeIn delay={0.05}>
            <Card className="glass" data-testid="card-adherence">
              <CardContent className="p-4 flex flex-col items-center">
                <AdherenceDonut percentage={clampedAdherence} size={120} />
                <p className="text-xs text-muted-foreground mt-1">Medication Adherence</p>
              </CardContent>
            </Card>
          </FadeIn>
        </div>

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
        ) : filteredMeds.length === 0 ? (
          <FadeIn delay={0.1}>
            <Card className="glass">
              <CardContent className="p-12 text-center">
                <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
                  <Pill className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="text-lg font-heading font-medium" data-testid="text-no-medications">
                  {search ? "No medications match your search" : "No medications found"}
                </p>
                <p className="text-muted-foreground mt-1">
                  {search ? "Try a different search term" : "Upload a prescription to get started"}
                </p>
              </CardContent>
            </Card>
          </FadeIn>
        ) : (
          <StaggerContainer className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredMeds.map((med, i) => (
              <StaggerItem key={i}>
                <HoverCard>
                  <Card className={`glass border-l-4 ${getBorderClass(med.confidence_label)} overflow-hidden`} data-testid={`card-medication-${i}`}>
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
                        <div className="flex items-center gap-2 mt-2">
                          {[1, 2, 3].map((pill) => (
                            <div
                              key={pill}
                              className={`w-6 h-8 rounded-full border-2 ${
                                pill <= 2
                                  ? "bg-primary/20 border-primary/40"
                                  : "bg-muted border-border"
                              }`}
                              title={pill <= 2 ? "Taken" : "Pending"}
                            />
                          ))}
                          <span className="text-xs text-muted-foreground ml-1">2/3 taken today</span>
                        </div>
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
