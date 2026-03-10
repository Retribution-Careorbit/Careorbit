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
import { Calendar, Clock, Plus, MapPin, User, Video, Stethoscope } from "lucide-react";

export default function AppointmentsPage() {
  const { toast } = useToast();
  const [open, setOpen] = useState(false);
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

  return (
    <Layout>
      <div className="space-y-6">
        <FadeIn>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-[28px] font-semibold" style={{ color: "var(--text-primary)" }} data-testid="text-appointments-title">
                Appointments
              </h1>
              <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
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
              <div key={i} className="rounded-xl p-6" style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}>
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
                <div className="rounded-xl p-8 text-center" style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}>
                  <Calendar className="h-12 w-12 mx-auto mb-3" strokeWidth={1} style={{ color: "var(--text-muted)" }} />
                  <p style={{ color: "var(--text-secondary)" }} data-testid="text-no-upcoming">No upcoming appointments</p>
                </div>
              </FadeIn>
            ) : (
              <StaggerContainer className="space-y-3">
                {upcoming.map((appt: any, i: number) => (
                  <StaggerItem key={appt.appointment_id || i}>
                    <div
                      className="rounded-xl p-5"
                      style={{
                        background: "var(--bg-card)",
                        border: "1px solid var(--border-subtle)",
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
                      <div
                        className="rounded-xl p-5 opacity-70"
                        style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}
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
                          <Badge variant="secondary" className="text-xs">Completed</Badge>
                        </div>
                      </div>
                    </StaggerItem>
                  ))}
                </StaggerContainer>
              </>
            )}
          </>
        )}
      </div>
    </Layout>
  );
}
