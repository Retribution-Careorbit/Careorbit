import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Layout } from "@/components/layout";
import { useActivePatientStore } from "@/lib/patient-context";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/animations";
import { AdherenceDonut } from "@/components/charts";
import { Pill, AlertTriangle, Search, Shield, CheckCircle } from "lucide-react";

interface Medication {
  name: string;
  dosage?: string;
  frequency?: string;
  confidence?: number;
  confidence_label?: string;
  prescribed_by_doctor?: string;
  interactions?: any[];
}

const CONFIDENCE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  VERIFIED: { bg: "var(--accent-emerald-dim)", text: "var(--accent-emerald)", border: "var(--accent-emerald)" },
  HIGH: { bg: "var(--accent-cyan-dim)", text: "var(--accent-cyan)", border: "var(--accent-cyan)" },
  MODERATE: { bg: "var(--accent-amber-dim)", text: "var(--accent-amber)", border: "var(--accent-amber)" },
  LOW: { bg: "rgba(244, 63, 94, 0.12)", text: "var(--accent-rose)", border: "var(--accent-rose)" },
};

export default function MedicationsPage() {
  const [search, setSearch] = useState("");
  const [interactionOpen, setInteractionOpen] = useState(false);
  const activePatientId = useActivePatientStore((s) => s.activePatientId);

  const { data, isLoading } = useQuery<{ medications: Medication[] }>({
    queryKey: ["/api/patients/medications", activePatientId],
  });

  const { data: adherence } = useQuery<any>({
    queryKey: ["/api/reminders/adherence/summary", activePatientId],
  });

  const { data: profileData } = useQuery<any>({
    queryKey: ["/api/patients/profile", activePatientId],
  });

  const isHindi = String(profileData?.profile?.preferred_language || "en").toLowerCase() === "hi";
  const t = {
    title: isHindi ? "दवाइयाँ" : "Medications",
    subtitle: isHindi ? "आपकी वर्तमान दवाइयाँ, डेटा कॉन्फिडेंस और क्लिनिकल इंटरैक्शन जोखिम सहित" : "Your current medications with data confidence and clinical interaction risk",
    checkInteractions: isHindi ? "इंटरैक्शन जाँचें" : "Check Interactions",
    noInteractions: isHindi ? "कोई इंटरैक्शन नहीं मिला" : "No interactions detected",
    allSafe: isHindi ? "आपकी सभी दवाइयाँ साथ में सुरक्षित दिखती हैं" : "All your medications appear safe together",
    searchPlaceholder: isHindi ? "दवाइयाँ खोजें..." : "Search medications...",
    noMatch: isHindi ? "आपकी खोज से कोई दवा नहीं मिली" : "No medications match your search",
    noMeds: isHindi ? "कोई दवा नहीं मिली" : "No medications found",
    trySearch: isHindi ? "कोई दूसरा शब्द आज़माएँ" : "Try a different search term",
    uploadStart: isHindi ? "शुरू करने के लिए पर्चा अपलोड करें" : "Upload a prescription to get started",
    dosage: isHindi ? "खुराक" : "Dosage",
    frequency: isHindi ? "आवृत्ति" : "Frequency",
    prescribedBy: isHindi ? "डॉक्टर" : "Prescribed by",
    takenToday: isHindi ? "2/3 आज लिया गया" : "2/3 taken today",
    interactionAlerts: isHindi ? "इंटरैक्शन अलर्ट" : "Interaction Alerts",
    interactionSeverity: isHindi ? "इंटरैक्शन गंभीरता" : "Interaction Severity",
    medAdherence: isHindi ? "दवा अनुपालन" : "Medication Adherence",
    warning: isHindi ? "चेतावनी" : "Warning",
    potentialInteraction: isHindi ? "संभावित इंटरैक्शन मिला" : "Potential interaction detected",
    taken: isHindi ? "लिया गया" : "Taken",
    pending: isHindi ? "बाकी" : "Pending",
    verified: isHindi ? "सत्यापित" : "Verified",
    high: isHindi ? "उच्च" : "High",
    moderate: isHindi ? "मध्यम" : "Moderate",
    low: isHindi ? "निम्न" : "Low",
    unknown: isHindi ? "अज्ञात" : "Unknown",
    dataConfidence: isHindi ? "डेटा कॉन्फिडेंस" : "Data Confidence",
    severityNote: isHindi
      ? "नोट: कॉन्फिडेंस डेटा-निकर्षण गुणवत्ता दर्शाता है; जोखिम गंभीरता किडनी लैब (eGFR/Creatinine) के आधार पर अलग से बढ़ सकती है।"
      : "Note: Confidence reflects extraction reliability; risk severity can be escalated independently by kidney labs (eGFR/Creatinine).",
  };

  const confidenceLabelText = (label: string) => {
    const key = String(label || "").toUpperCase();
    if (key === "VERIFIED") return t.verified;
    if (key === "HIGH") return t.high;
    if (key === "MODERATE") return t.moderate;
    if (key === "LOW") return t.low;
    return t.unknown;
  };

  const severityText = (value: string) => {
    const key = String(value || "").toUpperCase();
    if (!isHindi) return key || t.warning;
    if (key === "LOW") return "निम्न";
    if (key === "MODERATE") return "मध्यम";
    if (key === "ELEVATED") return "उच्च";
    if (key === "HIGH") return "उच्च";
    if (key === "CRITICAL") return "गंभीर";
    if (key === "CONTRAINDICATED") return "वर्जित";
    return key || t.warning;
  };

  const doctorDisplay = (raw?: string) => {
    const text = String(raw || "").trim();
    if (!isHindi) return text;
    if (text.toUpperCase() === "DR SELF") return "डॉ स्वयं";
    return text;
  };

  const medications = data?.medications || [];
  const filteredMeds = medications.filter((m) =>
    m.name.toLowerCase().includes(search.toLowerCase())
  );

  const allInteractions = medications.flatMap((m) =>
    (m.interactions || []).map((ix: any) => ({ ...ix, medicationName: m.name }))
  );

  const adherenceScore = Math.round((adherence?.adherence_rate || 0) * 100);
  const clampedAdherence = Math.max(0, Math.min(adherenceScore, 100));

  return (
    <Layout>
      <div className="space-y-6">
        <FadeIn>
          <div className="page-title-bar">
            <div>
              <h1 data-testid="text-medications-title">
                {t.title}
              </h1>
              <p>
                {t.subtitle}
              </p>
            </div>
            <Dialog open={interactionOpen} onOpenChange={setInteractionOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="shrink-0" data-testid="button-check-interactions">
                  <Shield className="h-4 w-4 mr-2" />
                  {t.checkInteractions}
                </Button>
              </DialogTrigger>
              <DialogContent style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)" }}>
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5" style={{ color: "var(--accent-cyan)" }} />
                    {t.checkInteractions}
                  </DialogTitle>
                </DialogHeader>
                <div className="space-y-3 mt-2">
                  {allInteractions.length === 0 ? (
                    <div className="text-center py-6">
                      <CheckCircle className="h-10 w-10 mx-auto mb-2" style={{ color: "var(--accent-emerald)" }} />
                      <p className="font-medium" style={{ color: "var(--text-primary)" }} data-testid="text-no-interactions">{t.noInteractions}</p>
                      <p className="text-sm" style={{ color: "var(--text-muted)" }}>{t.allSafe}</p>
                    </div>
                  ) : (
                    allInteractions.map((ix: any, j: number) => (
                      <div
                        key={j}
                        className="p-4 rounded-xl"
                        style={{ background: "rgba(244, 63, 94, 0.05)", border: "1px solid rgba(244, 63, 94, 0.20)" }}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <AlertTriangle className="h-4 w-4" style={{ color: "var(--accent-rose)" }} />
                          <span className="font-medium text-sm" style={{ color: "var(--text-primary)" }}>{ix.drug_pair || ix.medicationName}</span>
                          <Badge className="text-xs ml-auto" style={{ background: "rgba(244,63,94,0.10)", color: "var(--accent-rose)", border: "1px solid rgba(244,63,94,0.30)" }}>
                            {severityText(ix.severity || t.warning)}
                          </Badge>
                        </div>
                        <p className="text-xs" style={{ color: "var(--text-muted)" }}>{ix.description || t.potentialInteraction}</p>
                        {ix.clinical_action && (
                          <p className="text-xs mt-1" style={{ color: "var(--accent-cyan)" }}>{ix.clinical_action}</p>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </FadeIn>

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-5">
          <div className="space-y-5">
            <FadeIn delay={0.05}>
              <div
                className="flex items-center gap-2 rounded-full px-4 h-11"
                style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)" }}
              >
                <Search className="h-4 w-4 shrink-0" style={{ color: "var(--text-muted)" }} />
                <input
                  type="search"
                  placeholder={t.searchPlaceholder}
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="flex-1 bg-transparent border-none outline-none text-sm"
                  style={{ color: "var(--text-primary)" }}
                  data-testid="input-search-medications"
                />
              </div>
            </FadeIn>

            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="page-card p-5">
                    <Skeleton className="h-6 w-32 mb-3" />
                    <Skeleton className="h-4 w-48" />
                  </div>
                ))}
              </div>
            ) : filteredMeds.length === 0 ? (
              <FadeIn delay={0.1}>
                <div className="page-card p-12 text-center">
                  <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3" style={{ background: "var(--accent-violet-dim)" }}>
                    <Pill className="h-8 w-8" strokeWidth={1} style={{ color: "var(--accent-violet)", opacity: 0.5 }} />
                  </div>
                  <p className="font-medium" style={{ color: "var(--text-primary)" }} data-testid="text-no-medications">
                    {search ? t.noMatch : t.noMeds}
                  </p>
                  <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
                    {search ? t.trySearch : t.uploadStart}
                  </p>
                </div>
              </FadeIn>
            ) : (
              <StaggerContainer className="space-y-3">
                {filteredMeds.map((med, i) => {
                  const conf = med.confidence_label ? CONFIDENCE_COLORS[med.confidence_label] : null;
                  return (
                    <StaggerItem key={i}>
                      <div
                        className="page-card overflow-hidden"
                        style={{
                          borderLeft: conf ? `3px solid ${conf.border}` : undefined,
                        }}
                        data-testid={`card-medication-${i}`}
                      >
                        <div className="p-5">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: "var(--accent-violet-dim)" }}>
                                <Pill className="h-4 w-4" style={{ color: "var(--accent-violet)" }} />
                              </div>
                              <span className="font-medium" style={{ color: "var(--text-primary)" }}>{med.name}</span>
                            </div>
                            {conf && (
                              <Badge
                                className="text-xs border font-medium"
                                style={{
                                  background: conf.bg,
                                  color: conf.text,
                                  borderColor: `color-mix(in srgb, ${conf.border} 30%, transparent)`,
                                }}
                                data-testid={`badge-confidence-${(med.confidence_label || "unknown").toLowerCase()}`}
                              >
                                {`${t.dataConfidence}: ${confidenceLabelText(med.confidence_label || "Unknown")}`}
                              </Badge>
                            )}
                          </div>
                          <div className="space-y-1 text-sm">
                            {med.dosage && (
                              <p>
                                <span style={{ color: "var(--text-muted)" }}>{t.dosage}:</span>{" "}
                                <span className="font-mono text-xs" style={{ color: "var(--text-secondary)" }}>{med.dosage}</span>
                              </p>
                            )}
                            {med.frequency && (
                              <p>
                                <span style={{ color: "var(--text-muted)" }}>{t.frequency}:</span>{" "}
                                <span className="font-medium" style={{ color: "var(--text-primary)" }}>{med.frequency}</span>
                              </p>
                            )}
                            {med.prescribed_by_doctor && (
                              <p>
                                <span style={{ color: "var(--text-muted)" }}>{t.prescribedBy}:</span>{" "}
                                <span className="font-medium" style={{ color: "var(--text-primary)" }}>{doctorDisplay(med.prescribed_by_doctor)}</span>
                              </p>
                            )}
                            <div className="flex items-center gap-2 mt-2">
                              {[1, 2, 3].map((pill) => (
                                <div
                                  key={pill}
                                  className="w-6 h-8 rounded-full"
                                  style={{
                                    background: pill <= 2 ? "var(--accent-cyan-dim)" : "var(--bg-elevated)",
                                    border: pill <= 2 ? "2px solid color-mix(in srgb, var(--accent-cyan) 40%, transparent)" : "2px solid var(--border-subtle)",
                                  }}
                                  title={pill <= 2 ? t.taken : t.pending}
                                />
                              ))}
                              <span className="text-xs" style={{ color: "var(--text-muted)" }}>{t.takenToday}</span>
                            </div>
                          </div>
                          {med.interactions && med.interactions.length > 0 && (
                            <div
                              className="mt-3 p-3 rounded-lg"
                              style={{ background: "rgba(244,63,94,0.05)", border: "1px solid rgba(244,63,94,0.20)" }}
                              data-testid={`alert-interaction-${i}`}
                            >
                              <div className="flex items-center gap-1.5 text-sm font-medium" style={{ color: "var(--accent-rose)" }}>
                                <AlertTriangle className="h-4 w-4" />
                                {t.interactionAlerts}
                              </div>
                              <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>
                                {t.interactionSeverity}: {severityText(String(med.interactions[0]?.severity || ""))}
                              </p>
                              {med.interactions.map((int: any, j: number) => (
                                <p key={j} className="text-xs mt-1.5" style={{ color: "var(--text-muted)" }}>{int.description || JSON.stringify(int)}</p>
                              ))}
                              <p className="text-[11px] mt-2" style={{ color: "var(--text-muted)" }}>
                                {t.severityNote}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    </StaggerItem>
                  );
                })}
              </StaggerContainer>
            )}
          </div>

          <FadeIn delay={0.05}>
            <div
              className="page-card p-5 flex flex-col items-center sticky top-24"
              data-testid="card-adherence"
            >
              <AdherenceDonut percentage={clampedAdherence} size={120} />
              <p className="text-xs mt-2 font-medium" style={{ color: "var(--text-muted)" }}>{t.medAdherence}</p>
            </div>
          </FadeIn>
        </div>
      </div>
    </Layout>
  );
}
