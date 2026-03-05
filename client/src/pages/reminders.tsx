import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { queryClient, apiRequest } from "@/lib/queryClient";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Layout } from "@/components/layout";
import { useToast } from "@/hooks/use-toast";
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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold" data-testid="text-reminders-title">Reminders</h1>
            <p className="text-muted-foreground mt-1">
              Manage your medication reminder schedule
            </p>
          </div>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button data-testid="button-create-reminder">
                <Plus className="h-4 w-4 mr-2" />
                New Reminder
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Medication Reminder</DialogTitle>
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
                        className="flex items-center gap-1 cursor-pointer"
                      >
                        <Checkbox
                          checked={selectedDays.includes(day.value)}
                          onCheckedChange={() => toggleDay(day.value)}
                          data-testid={`checkbox-day-${day.value}`}
                        />
                        <span className="text-sm">{day.label}</span>
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

        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <Card key={i}>
                <CardContent className="p-6">
                  <div className="h-6 bg-muted rounded w-48 animate-pulse" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : reminderList.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <Bell className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-lg font-medium" data-testid="text-no-reminders">No reminders set</p>
              <p className="text-muted-foreground mt-1">
                Create a reminder to stay on track with your medications
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {reminderList.map((reminder, i) => (
              <Card key={reminder.reminder_id || i} data-testid={`card-reminder-${i}`}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
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
                                <Badge key={d.value} variant="outline" className="text-xs px-1">
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
                      data-testid={`button-delete-reminder-${i}`}
                    >
                      <Trash2 className="h-4 w-4 text-muted-foreground hover:text-destructive" />
                    </Button>
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
