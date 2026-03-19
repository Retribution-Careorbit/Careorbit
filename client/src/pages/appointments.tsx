import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Layout } from "@/components/layout";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/animations";
import { useToast } from "@/hooks/use-toast";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { Calendar, Clock, Plus, MapPin, User, Video, Stethoscope, Download } from "lucide-react";

export default function AppointmentsPage() {
  const { toast } = useToast();
  const [open, setOpen] = useState(false);
  const [visitOpen, setVisitOpen] = useState(false);
  const [selectedVisit, setSelectedVisit] = useState<any | null>(null);
  const [doctorName, setDoctorName] = useState("");
  const [specialization, setSpecialization] = useState("");
  const [datetime, setDatetime] = useState("");
  const [clinicName, setClinicName] = useState("");

  const { data: appointments = [], isLoading } = useQuery<any[]>({
    queryKey: ["/api/orbit/appointments"],
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      return apiRequest("POST", "/api/orbit/appointments", {
        doctor_name: doctorName,
        specialization,
        appointment_datetime: datetime,
        clinic_name: clinicName,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/orbit/appointments"] });
      toast({ title: "Appointment Created", description: "Your appointment has been scheduled." });
      setOpen(false);
      setDoctorName("");
      setSpecialization("");
      setDatetime("");
      setClinicName("");
    },
    onError: (err: any) => {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    },
  });

  const upcoming = Array.isArray(appointments) ? appointments.filter((a: any) => a.status === "upcoming") : [];
  const past = Array.isArray(appointments) ? appointments.filter((a: any) => a.status === "completed") : [];

  const formatDate = (dt: string) => {
    try {
      return new Date(dt).toLocaleDateString("en-IN", {
        weekday: "short",
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dt;
    }
  };

  const handleOpenBrief = async (appointmentId: string) => {
    try {
      const res = await apiRequest("GET", `/api/summary/previsit-brief/${appointmentId}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank", "noopener,noreferrer");
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (err: any) {
      toast({ title: "Unable to open brief", description: err.message, variant: "destructive" });
    }
  };

  const openVisitSummary = (appt: any) => {
    setSelectedVisit(appt);
    setVisitOpen(true);
  };

  const visitHeader = selectedVisit
    ? `${selectedVisit.doctor_name || "Doctor"} • ${formatDate(selectedVisit.appointment_datetime || "")}`
    : "Past Visit Summary";

  return (
    <Layout>
      <div className="space-y-6">
        <FadeIn>
          <div className="page-title-bar">
            <div>
              <h1 data-testid="text-appointments-title">
                Appointments
              </h1>
              <p>
                Manage your doctor appointments
              </p>
            </div>
            <Dialog open={open} onOpenChange={setOpen}>
              <DialogTrigger asChild>
                <Button data-testid="button-new-appointment">
                  <Plus className="h-4 w-4 mr-2" />
                  New Appointment
                </Button>
              </DialogTrigger>
              <DialogContent style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)" }}>
                <DialogHeader>
                  <DialogTitle>Schedule Appointment</DialogTitle>
                </DialogHeader>
                <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(); }} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="doctor">Doctor Name</Label>
                    <Input id="doctor" data-testid="input-doctor-name" placeholder="Dr. Smith" value={doctorName} onChange={(e) => setDoctorName(e.target.value)} required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="spec">Specialization</Label>
                    <Input id="spec" data-testid="input-specialization" placeholder="Cardiologist, General Physician..." value={specialization} onChange={(e) => setSpecialization(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="datetime">Date & Time</Label>
                    <Input id="datetime" type="datetime-local" data-testid="input-appointment-datetime" value={datetime} onChange={(e) => setDatetime(e.target.value)} required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="clinic">Clinic Name</Label>
                    <Input id="clinic" data-testid="input-clinic-name" placeholder="Apollo Hospital..." value={clinicName} onChange={(e) => setClinicName(e.target.value)} />
                  </div>
                  <Button type="submit" className="w-full" disabled={createMutation.isPending} data-testid="button-submit-appointment">
                    {createMutation.isPending ? "Scheduling..." : "Schedule Appointment"}
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </FadeIn>

        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="page-card p-6">
                <Skeleton className="h-20 w-full" />
              </div>
            ))}
          </div>
        ) : (
          <>
            <FadeIn delay={0.1}>
              <p className="section-header flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Upcoming ({upcoming.length})
              </p>
            </FadeIn>

            {upcoming.length === 0 ? (
              <FadeIn delay={0.15}>
                <div className="page-card p-8 text-center">
                  <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3" style={{ background: "var(--accent-cyan-dim)" }}>
                    <Calendar className="h-8 w-8" strokeWidth={1} style={{ color: "var(--accent-cyan)", opacity: 0.5 }} />
                  </div>
                  <p className="font-medium" style={{ color: "var(--text-secondary)" }} data-testid="text-no-upcoming">No upcoming appointments</p>
                </div>
              </FadeIn>
            ) : (
              <StaggerContainer className="space-y-3">
                {upcoming.map((appt: any, i: number) => (
                  <StaggerItem key={appt.appointment_id || i}>
                    <div
                      className="page-card p-5"
                      style={{
                        borderLeft: "3px solid var(--accent-cyan)",
                      }}
                      data-testid={`card-appointment-${i}`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <User className="h-4 w-4" style={{ color: "var(--accent-cyan)" }} />
                            <span className="font-medium" style={{ color: "var(--text-primary)" }}>{appt.doctor_name}</span>
                            {appt.specialization && (
                              <Badge variant="outline" className="text-xs">{appt.specialization}</Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-4 text-sm" style={{ color: "var(--text-muted)" }}>
                            <span className="flex items-center gap-1 font-mono text-xs">
                              <Clock className="h-3.5 w-3.5" />
                              {formatDate(appt.appointment_datetime)}
                            </span>
                            {appt.clinic_name && (
                              <span className="flex items-center gap-1">
                                <MapPin className="h-3.5 w-3.5" />
                                {appt.clinic_name}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {appt.brief_scheduled && (
                            <Badge className="text-xs" style={{ background: "var(--accent-violet-dim)", color: "var(--accent-violet)", border: "1px solid color-mix(in srgb, var(--accent-violet) 30%, transparent)" }}>
                              Pre-visit Brief
                            </Badge>
                          )}
                          <Button variant="outline" size="sm" className="text-xs" data-testid={`button-video-${i}`}>
                            <Video className="h-3.5 w-3.5 mr-1" />
                            Video Call
                          </Button>
                          <Button variant="outline" size="sm" className="text-xs" asChild data-testid={`button-brief-${i}`}>
                            <button onClick={() => handleOpenBrief(appt.appointment_id)}>
                              <Download className="h-3.5 w-3.5 mr-1" />
                              Brief PDF
                            </button>
                          </Button>
                        </div>
                      </div>
                    </div>
                  </StaggerItem>
                ))}
              </StaggerContainer>
            )}

            {past.length > 0 && (
              <>
                <FadeIn delay={0.2}>
                  <p className="section-header flex items-center gap-2 mt-4">
                    <Stethoscope className="h-4 w-4" />
                    Past ({past.length})
                  </p>
                </FadeIn>
                <StaggerContainer className="space-y-3">
                  {past.map((appt: any, i: number) => (
                    <StaggerItem key={appt.appointment_id || `past-${i}`}>
                      <button
                        type="button"
                        className="page-card p-5 opacity-70 text-left w-full"
                        onClick={() => openVisitSummary(appt)}
                        data-testid={`card-past-appointment-${i}`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <User className="h-4 w-4" style={{ color: "var(--text-muted)" }} />
                              <span className="font-medium" style={{ color: "var(--text-primary)" }}>{appt.doctor_name}</span>
                              {appt.specialization && <Badge variant="outline" className="text-xs">{appt.specialization}</Badge>}
                            </div>
                            <p className="text-sm font-mono text-xs" style={{ color: "var(--text-muted)" }}>{formatDate(appt.appointment_datetime)}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary" className="text-xs">Completed</Badge>
                            {(appt.visit_summary || appt.visit_findings) && (
                              <span className="text-xs" style={{ color: "var(--accent-cyan)" }}>
                                View Visit
                              </span>
                            )}
                          </div>
                        </div>
                      </button>
                    </StaggerItem>
                  ))}
                </StaggerContainer>
              </>
            )}
          </>
        )}

        <Dialog open={visitOpen} onOpenChange={setVisitOpen}>
          <DialogContent style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)" }}>
            <DialogHeader>
              <DialogTitle>{visitHeader}</DialogTitle>
            </DialogHeader>
            {selectedVisit && (
              <div className="space-y-3">
                <p className="text-sm" style={{ color: "var(--text-primary)" }}>{selectedVisit.visit_summary}</p>
                {Array.isArray(selectedVisit.visit_findings) && selectedVisit.visit_findings.length > 0 && (
                  <div>
                    <p className="text-xs uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Findings</p>
                    <ul className="text-sm mt-1 space-y-1" style={{ color: "var(--text-secondary)" }}>
                      {selectedVisit.visit_findings.map((f: string, i: number) => (
                        <li key={i}>- {f}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {selectedVisit.doctor_notes && (
                  <div>
                    <p className="text-xs uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Doctor Notes</p>
                    <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>{selectedVisit.doctor_notes}</p>
                  </div>
                )}
                {Array.isArray(selectedVisit.visit_prescriptions) && selectedVisit.visit_prescriptions.length > 0 && (
                  <div>
                    <p className="text-xs uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Prescriptions</p>
                    <ul className="text-sm mt-1 space-y-1" style={{ color: "var(--text-secondary)" }}>
                      {selectedVisit.visit_prescriptions.map((p: any, i: number) => (
                        <li key={i}>- {p.name} {p.dosage}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
