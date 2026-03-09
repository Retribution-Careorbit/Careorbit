import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuthStore } from "@/lib/auth";
import { Phone, AlertTriangle, CreditCard, User, Heart, Pill, QrCode } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";

export function SOSButton() {
  const [open, setOpen] = useState(false);
  const prefersReducedMotion = useReducedMotion();

  return (
    <>
      <motion.button
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-red-600 hover:bg-red-700 text-white shadow-lg flex items-center justify-center transition-colors"
        whileHover={prefersReducedMotion ? {} : { scale: 1.1 }}
        whileTap={prefersReducedMotion ? {} : { scale: 0.95 }}
        onClick={() => setOpen(true)}
        aria-label="Emergency SOS"
        data-testid="button-sos"
      >
        <AlertTriangle className="h-6 w-6" />
      </motion.button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="glass-strong max-w-md">
          <DialogHeader>
            <DialogTitle className="font-heading flex items-center gap-2 text-red-500">
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

  const contacts = data?.contacts || [];

  return (
    <div className="space-y-3 mt-3">
      {isLoading ? (
        <p className="text-sm text-muted-foreground text-center py-4">Loading...</p>
      ) : contacts.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-4" data-testid="text-no-emergency-contacts">
          No emergency contacts set. Add them in your profile settings.
        </p>
      ) : (
        contacts.map((contact: any, i: number) => (
          <Card key={i} className="border-red-500/20">
            <CardContent className="p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center">
                  <User className="h-5 w-5 text-red-500" />
                </div>
                <div>
                  <p className="font-medium text-sm" data-testid={`text-contact-name-${i}`}>{contact.name}</p>
                  <p className="text-xs text-muted-foreground">{contact.relation}</p>
                </div>
              </div>
              <a href={`tel:${contact.phone}`}>
                <Button variant="destructive" size="sm" className="shadow-sm" data-testid={`button-call-${i}`}>
                  <Phone className="h-4 w-4 mr-1" />
                  Call
                </Button>
              </a>
            </CardContent>
          </Card>
        ))
      )}

      <a href="tel:108" className="block">
        <Button variant="destructive" className="w-full h-12 text-base shadow-lg" data-testid="button-call-ambulance">
          <Phone className="h-5 w-5 mr-2" />
          Call Ambulance (108)
        </Button>
      </a>
    </div>
  );
}

function MedicalIDCard() {
  const user = useAuthStore((s) => s.user);

  const { data: profileData } = useQuery<any>({
    queryKey: ["/api/patients/profile"],
  });

  const { data: medsData } = useQuery<any>({
    queryKey: ["/api/patients/medications"],
  });

  const profile = profileData?.profile || {};
  const medications = medsData?.medications || [];

  return (
    <div className="mt-3">
      <Card className="border-primary/30 bg-gradient-to-br from-primary/5 to-secondary/5" data-testid="card-medical-id">
        <CardContent className="p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                <Heart className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="font-heading font-bold text-lg">{user?.name || "Patient"}</p>
                <p className="text-sm text-muted-foreground">CareOrbit Medical ID</p>
              </div>
            </div>
            <div className="w-16 h-16 rounded-lg bg-white dark:bg-white/10 flex items-center justify-center">
              <QrCode className="h-10 w-10 text-foreground dark:text-white/70" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-muted-foreground text-xs">Age</p>
              <p className="font-medium" data-testid="text-medical-id-age">{profile.age || "—"}</p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs">Gender</p>
              <p className="font-medium capitalize" data-testid="text-medical-id-gender">{profile.gender || "—"}</p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs">Blood Type</p>
              <p className="font-medium" data-testid="text-medical-id-blood-type">{profile.blood_type || "—"}</p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs">City</p>
              <p className="font-medium" data-testid="text-medical-id-city">{profile.city || "—"}</p>
            </div>
          </div>

          {medications.length > 0 && (
            <div>
              <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
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
        </CardContent>
      </Card>
    </div>
  );
}
