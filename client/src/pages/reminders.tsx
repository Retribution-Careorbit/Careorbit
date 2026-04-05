import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { queryClient, apiRequest } from "@/lib/queryClient";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Layout } from "@/components/layout";
import { useToast } from "@/hooks/use-toast";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/animations";
import { Bell, Plus, Trash2, Clock, Loader2, Calendar } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { useActivePatientStore } from "@/lib/patient-context";
import { useAuthStore } from "@/lib/auth";

interface Reminder {
  reminder_id: string;
  medication_node_id: string;
  reminder_time: string;
  days_of_week?: number[];
  status?: string;
  adherence_streak?: number;
  total_taken?: number;
  total_missed?: number;
  last_status?: string | null;
  last_reason?: string | null;
}

interface DueReminder {
  reminder_id: string;
  medication_node_id: string;
  reminder_time: string;
  status: "pending" | "taken" | "missed";
  reason?: string | null;
}

const DAYS = [
  { value: 1, label: "Mon" },
  { value: 2, label: "Tue" },
  { value: 3, label: "Wed" },
  { value: 4, label: "Thu" },
  { value: 5, label: "Fri" },
  { value: 6, label: "Sat" },
  { value: 7, label: "Sun" },
];

export default function RemindersPage() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [nodeId, setNodeId] = useState("");
  const [time, setTime] = useState("08:00");
  const [selectedDays, setSelectedDays] = useState<number[]>([1, 2, 3, 4, 5, 6, 7]);
  const { toast } = useToast();
  const activePatientId = useActivePatientStore((s) => s.activePatientId);
  const user = useAuthStore((s) => s.user);
  const { data: profileData } = useQuery<{ preferred_language?: string }>({
    queryKey: ["/api/patients/profile", activePatientId],
    enabled: Boolean(activePatientId),
  });
  const isHindi = ((profileData?.preferred_language || user?.preferredLanguage || "en").toLowerCase().startsWith("hi"));
  const tx = (en: string, hi: string) => (isHindi ? hi : en);

  const { data: reminders = [], isLoading } = useQuery<Reminder[]>({
    queryKey: ["/api/reminders/list", activePatientId],
  });

  const { data: dueData } = useQuery<{ due: DueReminder[] }>({
    queryKey: ["/api/reminders/due", activePatientId],
  });

  const { data: appointments = [] } = useQuery<any[]>({
    queryKey: ["/api/orbit/appointments", activePatientId],
  });

  const { data: adherence } = useQuery<any>({
    queryKey: ["/api/reminders/adherence/summary", activePatientId],
  });

  const reminderList = Array.isArray(reminders) ? reminders : [];

  const createMutation = useMutation({
    mutationFn: async (body: { medication_node_id: string; reminder_time: string; days_of_week: number[] }) => {
      const res = await apiRequest("POST", "/api/reminders/create", body);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/reminders/list"] });
      toast({ title: tx("Reminder Created", "रिमाइंडर बनाया गया") });
      setDialogOpen(false);
      setNodeId("");
      setTime("08:00");
      setSelectedDays([1, 2, 3, 4, 5, 6, 7]);
    },
    onError: (err: Error) => {
      toast({ title: tx("Error", "त्रुटि"), description: err.message, variant: "destructive" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (reminderId: string) => {
      await apiRequest("DELETE", `/api/reminders/${reminderId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/reminders/list"] });
      toast({ title: tx("Reminder Deleted", "रिमाइंडर हटाया गया") });
    },
    onError: (err: Error) => {
      toast({ title: tx("Error", "त्रुटि"), description: err.message, variant: "destructive" });
    },
  });

  const markMutation = useMutation({
    mutationFn: async (body: { reminderId: string; status: "taken" | "missed"; reason?: string }) => {
      const res = await apiRequest("POST", `/api/reminders/${body.reminderId}/mark`, {
        status: body.status,
        reason: body.reason,
      });
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/reminders/list"] });
      queryClient.invalidateQueries({ queryKey: ["/api/reminders/due"] });
      queryClient.invalidateQueries({ queryKey: ["/api/reminders/adherence/summary"] });
      queryClient.invalidateQueries({ queryKey: ["/api/orbit/score"] });
      toast({ title: tx("Reminder updated", "रिमाइंडर अपडेट हुआ") });
    },
    onError: (err: Error) => {
      toast({ title: tx("Error", "त्रुटि"), description: err.message, variant: "destructive" });
    },
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!nodeId.trim()) return;
    createMutation.mutate({
      medication_node_id: nodeId,
      reminder_time: time,
      days_of_week: selectedDays,
    });
  };

  const toggleDay = (day: number) => {
    setSelectedDays((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day]
    );
  };

  const dueList = dueData?.due || [];
  const upcomingAppts = Array.isArray(appointments)
    ? appointments.filter((a: any) => a.status === "upcoming").slice(0, 2)
    : [];

  const handleMarkMissed = (reminderId: string) => {
    const reason = window.prompt(tx("Why did you miss this dose? (required)", "आपने यह डोज़ क्यों मिस की? (ज़रूरी)"));
    if (!reason || !reason.trim()) {
      toast({ title: tx("Missed reason is required", "मिस करने का कारण ज़रूरी है"), variant: "destructive" });
      return;
    }
    markMutation.mutate({ reminderId, status: "missed", reason: reason.trim() });
  };

  return (
    <Layout>
      <div className="space-y-6">
        <FadeIn>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="page-card p-3">
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>{tx("Adherence Rate", "अनुपालन दर")}</p>
              <p className="font-mono text-xl font-bold" data-testid="text-adherence-rate">{Math.round((adherence?.adherence_rate || 0) * 100)}%</p>
            </div>
            <div className="page-card p-3">
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>{tx("Current Streak", "वर्तमान स्ट्रीक")}</p>
              <p className="font-mono text-xl font-bold" data-testid="text-adherence-streak">{adherence?.streak_days || 0}d</p>
            </div>
            <div className="page-card p-3">
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>{tx("Taken", "लिया")}</p>
              <p className="font-mono text-xl font-bold" data-testid="text-total-taken">{adherence?.total_taken || 0}</p>
            </div>
            <div className="page-card p-3">
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>{tx("Missed", "मिस")}</p>
              <p className="font-mono text-xl font-bold" data-testid="text-total-missed">{adherence?.total_missed || 0}</p>
            </div>
          </div>
        </FadeIn>

        {dueList.length > 0 && (
          <FadeIn delay={0.05}>
            <div className="page-card p-4">
              <p className="section-header mb-2">{tx("Due Now", "अभी देय")}</p>
              <div className="space-y-2">
                {dueList.map((item, i) => (
                  <div key={item.reminder_id} className="flex items-center justify-between p-3 rounded-xl" style={{ border: "1px solid var(--border-subtle)" }} data-testid={`card-due-reminder-${i}`}>
                    <div>
                      <p className="font-medium" style={{ color: "var(--text-primary)" }}>{item.medication_node_id}</p>
                      <p className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>{item.reminder_time}</p>
                    </div>
                    {item.status === "pending" ? (
                      <div className="flex gap-2">
                        <Button size="sm" onClick={() => markMutation.mutate({ reminderId: item.reminder_id, status: "taken" })} disabled={markMutation.isPending} data-testid={`button-mark-taken-${i}`}>
                          {tx("Taken", "लिया")}
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => handleMarkMissed(item.reminder_id)} disabled={markMutation.isPending} data-testid={`button-mark-missed-${i}`}>
                          {tx("Missed", "मिस")}
                        </Button>
                      </div>
                    ) : (
                      <Badge variant="outline" className="capitalize">{item.status}</Badge>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </FadeIn>
        )}

        {upcomingAppts.length > 0 && (
          <FadeIn delay={0.08}>
            <div className="page-card p-4" data-testid="card-upcoming-appointments">
              <div className="flex items-center gap-2 mb-2">
                <Calendar className="h-4 w-4" style={{ color: "var(--accent-cyan)" }} />
                <p className="section-header">{tx("Upcoming Appointments", "आगामी अपॉइंटमेंट्स")}</p>
              </div>
              <div className="space-y-2">
                {upcomingAppts.map((appt: any, i: number) => (
                  <div key={appt.appointment_id || i} className="flex items-center justify-between p-3 rounded-xl" style={{ border: "1px solid var(--border-subtle)" }}>
                    <div>
                      <p className="font-medium" style={{ color: "var(--text-primary)" }}>{appt.doctor_name}</p>
                      <p className="text-xs" style={{ color: "var(--text-muted)" }}>{appt.specialization || tx("General", "सामान्य")}</p>
                    </div>
                    <Badge variant="outline" className="text-xs font-mono">
                      {new Date(appt.appointment_datetime).toLocaleDateString("en-IN", { month: "short", day: "numeric" })}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          </FadeIn>
        )}

        <FadeIn>
          <div className="page-title-bar">
            <div>
              <h1 data-testid="text-reminders-title">
                {tx("Reminders", "रिमाइंडर्स")}
              </h1>
              <p>
                {tx("Manage your medication reminder schedule", "अपनी दवा रिमाइंडर समय-सारणी प्रबंधित करें")}
              </p>
            </div>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button data-testid="button-create-reminder">
                  <Plus className="h-4 w-4 mr-2" />
                  {tx("New Reminder", "नया रिमाइंडर")}
                </Button>
              </DialogTrigger>
              <DialogContent style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)" }}>
                <DialogHeader>
                  <DialogTitle>{tx("Create Medication Reminder", "दवा रिमाइंडर बनाएं")}</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleCreate} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="nodeId">{tx("Medication Node ID", "दवा नोड आईडी")}</Label>
                    <Input id="nodeId" value={nodeId} onChange={(e) => setNodeId(e.target.value)} placeholder={tx("e.g., med_metformin_001", "उदा., med_metformin_001")} data-testid="input-node-id" required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="time">{tx("Reminder Time", "रिमाइंडर समय")}</Label>
                    <Input id="time" type="time" value={time} onChange={(e) => setTime(e.target.value)} data-testid="input-time" required />
                  </div>
                  <div className="space-y-2">
                    <Label>{tx("Days of Week", "सप्ताह के दिन")}</Label>
                    <div className="flex gap-2 flex-wrap">
                      {DAYS.map((day) => (
                        <label
                          key={day.value}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full cursor-pointer text-sm font-medium"
                          style={{
                            border: selectedDays.includes(day.value)
                              ? "1px solid var(--accent-cyan)"
                              : "1px solid var(--border-default)",
                            background: selectedDays.includes(day.value) ? "var(--accent-cyan-dim)" : "transparent",
                            color: selectedDays.includes(day.value) ? "var(--accent-cyan)" : "var(--text-secondary)",
                          }}
                        >
                          <Checkbox
                            checked={selectedDays.includes(day.value)}
                            onCheckedChange={() => toggleDay(day.value)}
                            data-testid={`checkbox-day-${day.value}`}
                            className="sr-only"
                            aria-label={tx(`Select ${day.label}`, `${day.label} चुनें`)}
                          />
                          <span>{day.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                  <Button type="submit" className="w-full" disabled={createMutation.isPending} data-testid="button-submit-reminder">
                    {createMutation.isPending && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                    {tx("Create Reminder", "रिमाइंडर बनाएं")}
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </FadeIn>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="page-card p-5 h-16 animate-pulse" />
            ))}
          </div>
        ) : reminderList.length === 0 ? (
          <FadeIn delay={0.1}>
            <div className="page-card p-12 text-center">
              <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3" style={{ background: "var(--accent-amber-dim)" }}>
                <Bell className="h-8 w-8" strokeWidth={1} style={{ color: "var(--accent-amber)", opacity: 0.5 }} />
              </div>
              <p className="font-medium" style={{ color: "var(--text-primary)" }} data-testid="text-no-reminders">{tx("No reminders set", "कोई रिमाइंडर सेट नहीं है")}</p>
              <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
                {tx("Create a reminder to stay on track with your medications", "दवाइयों के साथ नियमित रहने के लिए रिमाइंडर बनाएं")}
              </p>
            </div>
          </FadeIn>
        ) : (
          <StaggerContainer className="space-y-3">
            {reminderList.map((reminder, i) => (
              <StaggerItem key={reminder.reminder_id || i}>
                <div
                  className="page-card p-4"
                  data-testid={`card-reminder-${i}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "var(--accent-amber-dim)" }}>
                        <Clock className="h-5 w-5" style={{ color: "var(--accent-amber)" }} />
                      </div>
                      <div>
                        <p className="font-medium" style={{ color: "var(--text-primary)" }} data-testid={`text-reminder-med-${i}`}>
                          {reminder.medication_node_id}
                        </p>
                        <div className="flex items-center gap-2 text-sm" style={{ color: "var(--text-muted)" }}>
                          <span className="font-mono text-xs">{reminder.reminder_time}</span>
                          {reminder.last_status && (
                            <Badge variant="outline" className="text-xs capitalize">{reminder.last_status}</Badge>
                          )}
                          {typeof reminder.adherence_streak === "number" && (
                            <Badge variant="outline" className="text-xs">{tx("Streak", "स्ट्रीक")} {reminder.adherence_streak}d</Badge>
                          )}
                          {reminder.days_of_week && (
                            <div className="flex gap-1">
                              {DAYS.filter((d) => reminder.days_of_week!.includes(d.value)).map((d) => (
                                <Badge key={d.value} variant="outline" className="text-xs px-1.5 py-0">{d.label}</Badge>
                              ))}
                            </div>
                          )}
                        </div>
                        {reminder.last_reason && (
                          <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                            {tx("Last missed reason", "पिछला मिस कारण")}: {reminder.last_reason}
                          </p>
                        )}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => deleteMutation.mutate(reminder.reminder_id)}
                      disabled={deleteMutation.isPending}
                      className="h-9 w-9 rounded-full hover:text-destructive"
                      aria-label={tx(`Delete reminder for ${reminder.medication_node_id}`, `${reminder.medication_node_id} के लिए रिमाइंडर हटाएं`)}
                      data-testid={`button-delete-reminder-${i}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </StaggerItem>
            ))}
          </StaggerContainer>
        )}
      </div>
    </Layout>
  );
}
