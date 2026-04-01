import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuthStore } from "@/lib/auth";
import { useActivePatientStore } from "@/lib/patient-context";
import { Phone, AlertTriangle, CreditCard, User, Heart, Pill, QrCode } from "lucide-react";

export function SOSButton() {
  const [open, setOpen] = useState(false);

  return (
    <>
      {!open && (
        <button
          className="w-12 h-12 rounded-full text-white flex items-center justify-center sos-pulse-ring"
          style={{
            position: "fixed",
            bottom: 80,
            right: 20,
            zIndex: 9999,
            background: "linear-gradient(135deg, #F43F5E, #E11D48)",
            boxShadow: "0 4px 16px rgba(244, 63, 94, 0.40)",
          }}
          onClick={() => setOpen(true)}
          aria-label="Emergency SOS"
          data-testid="button-sos"
        >
          <AlertTriangle className="h-5 w-5" strokeWidth={2} />
        </button>
      )}

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-md" style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)" }}>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ color: "var(--accent-rose)" }}>
              <AlertTriangle className="h-5 w-5" />
              Emergency
            </DialogTitle>
          </DialogHeader>
          <Tabs defaultValue="contacts">
            <TabsList className="w-full">
              <TabsTrigger value="contacts" className="flex-1" data-testid="tab-emergency-contacts">
                <Phone className="h-4 w-4 mr-1" />
                Contacts
              </TabsTrigger>
              <TabsTrigger value="medical-id" className="flex-1" data-testid="tab-medical-id">
                <CreditCard className="h-4 w-4 mr-1" />
                Medical ID
              </TabsTrigger>
            </TabsList>
            <TabsContent value="contacts">
              <EmergencyContacts />
            </TabsContent>
            <TabsContent value="medical-id">
              <MedicalIDCard />
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>
    </>
  );
}

function EmergencyContacts() {
  const { data, isLoading } = useQuery<any>({
    queryKey: ["/api/patients/emergency-contacts"],
  });

  const { data: emergencyPass } = useQuery<any>({
    queryKey: ["/api/patients/emergency-pass"],
  });

  const contacts = data?.contacts || [];
  const dispatchPhone = emergencyPass?.dispatch_phone || "108";

  return (
    <div className="space-y-3 mt-3">
      {isLoading ? (
        <p className="text-sm text-center py-4" style={{ color: "var(--text-muted)" }}>Loading...</p>
      ) : contacts.length === 0 ? (
        <p className="text-sm text-center py-4" style={{ color: "var(--text-muted)" }} data-testid="text-no-emergency-contacts">
          No emergency contacts set. Add them in your profile settings.
        </p>
      ) : (
        contacts.map((contact: any, i: number) => (
          <div
            key={i}
            className="flex items-center justify-between p-4 rounded-xl"
            style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ background: "rgba(244, 63, 94, 0.10)" }}>
                <User className="h-5 w-5" style={{ color: "var(--accent-rose)" }} />
              </div>
              <div>
                <p className="font-medium text-sm" style={{ color: "var(--text-primary)" }} data-testid={`text-contact-name-${i}`}>{contact.name}</p>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>{contact.relation}</p>
              </div>
            </div>
            <a href={`tel:${contact.phone}`}>
              <Button variant="destructive" size="sm" data-testid={`button-call-${i}`}>
                <Phone className="h-4 w-4 mr-1" />
                Call
              </Button>
            </a>
          </div>
        ))
      )}

      <a href={`tel:${dispatchPhone}`} className="block">
        <Button
          variant="destructive"
          className="w-full h-12 text-base"
          style={{ boxShadow: "0 4px 16px rgba(244, 63, 94, 0.30)" }}
          data-testid="button-call-ambulance"
        >
          <Phone className="h-5 w-5 mr-2" />
          Call Emergency ({dispatchPhone})
        </Button>
      </a>
    </div>
  );
}

function MedicalIDCard() {
  const user = useAuthStore((s) => s.user);
  const members = useActivePatientStore((s) => s.members);
  const activePatientId = useActivePatientStore((s) => s.activePatientId);

  const activeMemberName = members.find((m) => m.id === activePatientId)?.name || user?.name || "Patient";

  const { data: profileData } = useQuery<any>({
    queryKey: ["/api/patients/profile"],
  });

  const { data: medsData } = useQuery<any>({
    queryKey: ["/api/patients/medications"],
  });

  const { data: emergencyPass } = useQuery<any>({
    queryKey: ["/api/patients/emergency-pass"],
  });

  const profile = profileData?.profile || {};
  const medications = medsData?.medications || [];
  const qrPath = emergencyPass?.qr_path;
  const qrUrl = qrPath ? `${window.location.origin}${qrPath}` : "";
  const qrImageUrl = qrUrl
    ? `https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=${encodeURIComponent(qrUrl)}`
    : "";

  return (
    <div className="mt-3">
      <div
        className="rounded-xl p-5 space-y-4"
        style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}
        data-testid="card-medical-id"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ background: "var(--accent-cyan-dim)" }}>
              <Heart className="h-6 w-6" style={{ color: "var(--accent-cyan)" }} />
            </div>
            <div>
              <p className="font-bold text-lg" style={{ color: "var(--text-primary)" }}>{activeMemberName}</p>
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>CareOrbit Medical ID</p>
            </div>
          </div>
          <a
            href={qrUrl || "#"}
            target="_blank"
            rel="noreferrer"
            className="w-16 h-16 rounded-lg flex items-center justify-center"
            style={{
              background: "var(--bg-elevated)",
              border: "1px solid var(--border-subtle)",
              pointerEvents: qrUrl ? "auto" : "none",
            }}
            title={qrUrl ? "Open emergency read-only profile" : "Generating emergency QR"}
            data-testid="link-emergency-qr"
          >
            {qrImageUrl ? (
              <img
                src={qrImageUrl}
                alt="Emergency QR"
                className="w-14 h-14 rounded"
              />
            ) : (
              <QrCode className="h-10 w-10" style={{ color: "var(--text-muted)" }} />
            )}
          </a>
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>Age</p>
            <p className="font-medium" style={{ color: "var(--text-primary)" }} data-testid="text-medical-id-age">{profile.age || "—"}</p>
          </div>
          <div>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>Gender</p>
            <p className="font-medium capitalize" style={{ color: "var(--text-primary)" }} data-testid="text-medical-id-gender">{profile.gender || "—"}</p>
          </div>
          <div>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>Blood Type</p>
            <p className="font-medium" style={{ color: "var(--text-primary)" }} data-testid="text-medical-id-blood-type">{profile.blood_type || "—"}</p>
          </div>
          <div>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>City</p>
            <p className="font-medium" style={{ color: "var(--text-primary)" }} data-testid="text-medical-id-city">{profile.city || "—"}</p>
          </div>
        </div>

        {medications.length > 0 && (
          <div>
            <p className="text-xs mb-2 flex items-center gap-1" style={{ color: "var(--text-muted)" }}>
              <Pill className="h-3 w-3" />
              Current Medications
            </p>
            <div className="flex flex-wrap gap-1.5">
              {medications.slice(0, 6).map((med: any, i: number) => (
                <Badge key={i} variant="outline" className="text-xs">
                  {med.name} {med.dosage && `(${med.dosage})`}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {qrUrl && (
          <p className="text-[11px] break-all" style={{ color: "var(--text-muted)" }} data-testid="text-emergency-qr-url">
            QR read-only URL: {qrUrl}
          </p>
        )}
      </div>
    </div>
  );
}
