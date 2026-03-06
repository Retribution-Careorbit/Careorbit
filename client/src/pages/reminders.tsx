import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { queryClient, apiRequest } from "@/lib/queryClient";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Layout } from "@/components/layout";
import { useToast } from "@/hooks/use-toast";
import { FadeIn, StaggerContainer, StaggerItem, HoverCard } from "@/components/animations";
import { Bell, Plus, Trash2, Clock, Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";

interface Reminder {
  reminder_id: string;
  medication_node_id: string;
  reminder_time: string;
  days_of_week?: number[];
  status?: string;
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

  const { data: reminders = [], isLoading } = useQuery<Reminder[]>({
    queryKey: ["/api/reminders/list"],
  });

  const reminderList = Array.isArray(reminders) ? reminders : [];

  const createMutation = useMutation({
    mutationFn: async (body: { medication_node_id: string; reminder_time: string; days_of_week: number[] }) => {
      const res = await apiRequest("POST", "/api/reminders/create", body);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/reminders/list"] });
      toast({ title: "Reminder Created" });
      setDialogOpen(false);
      setNodeId("");
      setTime("08:00");
      setSelectedDays([1, 2, 3, 4, 5, 6, 7]);
    },
    onError: (err: Error) => {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (reminderId: string) => {
      await apiRequest("DELETE", `/api/reminders/${reminderId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/reminders/list"] });
      toast({ title: "Reminder Deleted" });
    },
    onError: (err: Error) => {
      toast({ title: "Error", description: err.message, variant: "destructive" });
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

  return (
    <Layout>
      <div className="space-y-6">
        <FadeIn>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-heading font-bold tracking-tight" data-testid="text-reminders-title">Reminders</h1>
              <p className="text-muted-foreground mt-1.5">
                Manage your medication reminder schedule
              </p>
            </div>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button className="shadow-sm" data-testid="button-create-reminder">
                  <Plus className="h-4 w-4 mr-2" />
                  New Reminder
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle className="font-heading">Create Medication Reminder</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleCreate} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="nodeId">Medication Node ID</Label>
                    <Input
                      id="nodeId"
                      value={nodeId}
                      onChange={(e) => setNodeId(e.target.value)}
                      placeholder="e.g., med_metformin_001"
                      data-testid="input-node-id"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="time">Reminder Time</Label>
                    <Input
                      id="time"
                      type="time"
                      value={time}
                      onChange={(e) => setTime(e.target.value)}
                      data-testid="input-time"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Days of Week</Label>
                    <div className="flex gap-2 flex-wrap">
                      {DAYS.map((day) => (
                        <label
                          key={day.value}
                          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border cursor-pointer transition-all ${
                            selectedDays.includes(day.value)
                              ? "border-primary bg-primary/5 text-primary"
                              : "border-border hover:border-muted-foreground/50"
                          }`}
                        >
                          <Checkbox
                            checked={selectedDays.includes(day.value)}
                            onCheckedChange={() => toggleDay(day.value)}
                            data-testid={`checkbox-day-${day.value}`}
                            className="sr-only"
                            aria-label={`Select ${day.label}`}
                          />
                          <span className="text-sm font-medium">{day.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                  <Button
                    type="submit"
                    className="w-full"
                    disabled={createMutation.isPending}
                    data-testid="button-submit-reminder"
                  >
                    {createMutation.isPending && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                    Create Reminder
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </FadeIn>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Card key={i}>
                <CardContent className="p-5">
                  <div className="h-6 bg-muted rounded-md w-48 animate-pulse" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : reminderList.length === 0 ? (
          <FadeIn delay={0.1}>
            <Card>
              <CardContent className="p-12 text-center">
                <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
                  <Bell className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="text-lg font-heading font-medium" data-testid="text-no-reminders">No reminders set</p>
                <p className="text-muted-foreground mt-1">
                  Create a reminder to stay on track with your medications
                </p>
              </CardContent>
            </Card>
          </FadeIn>
        ) : (
          <StaggerContainer className="space-y-3">
            {reminderList.map((reminder, i) => (
              <StaggerItem key={reminder.reminder_id || i}>
                <HoverCard>
                  <Card data-testid={`card-reminder-${i}`}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                            <Clock className="h-5 w-5 text-primary" />
                          </div>
                          <div>
                            <p className="font-medium" data-testid={`text-reminder-med-${i}`}>
                              {reminder.medication_node_id}
                            </p>
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <span>{reminder.reminder_time}</span>
                              {reminder.days_of_week && (
                                <div className="flex gap-1">
                                  {DAYS.filter((d) => reminder.days_of_week!.includes(d.value)).map((d) => (
                                    <Badge key={d.value} variant="outline" className="text-xs px-1.5 py-0">
                                      {d.label}
                                    </Badge>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => deleteMutation.mutate(reminder.reminder_id)}
                          disabled={deleteMutation.isPending}
                          className="h-9 w-9 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                          aria-label={`Delete reminder for ${reminder.medication_node_id}`}
                          data-testid={`button-delete-reminder-${i}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
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
