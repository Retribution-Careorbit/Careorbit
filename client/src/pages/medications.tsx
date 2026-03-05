import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Layout } from "@/components/layout";
import { Pill, AlertTriangle } from "lucide-react";

interface Medication {
  name: string;
  dosage?: string;
  frequency?: string;
  confidence?: number;
  confidence_label?: string;
  interactions?: any[];
}

export default function MedicationsPage() {
  const { data, isLoading } = useQuery<{ medications: Medication[] }>({
    queryKey: ["/api/patients/medications"],
  });

  const medications = data?.medications || [];

  const getConfidenceBadge = (label?: string) => {
    switch (label) {
      case "VERIFIED":
        return <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">Verified</Badge>;
      case "HIGH":
        return <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">High</Badge>;
      case "MODERATE":
        return <Badge className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">Moderate</Badge>;
      case "LOW":
        return <Badge variant="destructive">Low</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold" data-testid="text-medications-title">Medications</h1>
          <p className="text-muted-foreground mt-1">
            Your current medications with confidence scores and interaction alerts
          </p>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <Card key={i}>
                <CardContent className="p-6">
                  <Skeleton className="h-6 w-32 mb-2" />
                  <Skeleton className="h-4 w-48" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : medications.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <Pill className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-lg font-medium" data-testid="text-no-medications">No medications found</p>
              <p className="text-muted-foreground mt-1">
                Upload a prescription to get started
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {medications.map((med, i) => (
              <Card key={i} data-testid={`card-medication-${i}`}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Pill className="h-5 w-5 text-primary" />
                      {med.name}
                    </CardTitle>
                    {getConfidenceBadge(med.confidence_label)}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-1 text-sm">
                    {med.dosage && (
                      <p><span className="text-muted-foreground">Dosage:</span> {med.dosage}</p>
                    )}
                    {med.frequency && (
                      <p><span className="text-muted-foreground">Frequency:</span> {med.frequency}</p>
                    )}
                    {med.confidence !== undefined && (
                      <p><span className="text-muted-foreground">Confidence:</span> {(med.confidence * 100).toFixed(0)}%</p>
                    )}
                    {med.interactions && med.interactions.length > 0 && (
                      <div className="mt-2 p-2 rounded bg-destructive/10 border border-destructive/20">
                        <div className="flex items-center gap-1 text-destructive font-medium">
                          <AlertTriangle className="h-4 w-4" />
                          Interaction Alerts
                        </div>
                        {med.interactions.map((int: any, j: number) => (
                          <p key={j} className="text-xs mt-1">{int.description || JSON.stringify(int)}</p>
                        ))}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
