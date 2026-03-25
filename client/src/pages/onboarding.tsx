import { useState } from "react";
import { useLocation } from "wouter";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { useAuthStore } from "@/lib/auth";
import { authFetch } from "@/lib/auth";
import { FadeIn, ScaleIn } from "@/components/animations";
import { motion, AnimatePresence } from "framer-motion";
import { Heart, ChevronDown, ChevronUp, UserCheck, Sparkles } from "lucide-react";

const GENDER_OPTIONS = [
  { value: "male", label: "Male" },
  { value: "female", label: "Female" },
  { value: "other", label: "Other" },
  { value: "prefer_not_to_say", label: "Prefer not to say" },
];

const LANGUAGE_OPTIONS = [
  { value: "en", label: "English" },
  { value: "hi", label: "Hindi" },
  { value: "bn", label: "Bengali" },
  { value: "ta", label: "Tamil" },
  { value: "te", label: "Telugu" },
  { value: "mr", label: "Marathi" },
  { value: "gu", label: "Gujarati" },
  { value: "kn", label: "Kannada" },
  { value: "ml", label: "Malayalam" },
];

const LITERACY_OPTIONS = [
  { value: "basic", label: "Basic", description: "Simple everyday language" },
  { value: "intermediate", label: "Intermediate", description: "Some medical terms with explanations" },
  { value: "advanced", label: "Advanced", description: "Full clinical terminology" },
];

const BLOOD_TYPE_OPTIONS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];

export default function OnboardingPage() {
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [gender, setGender] = useState("");
  const [preferredLanguage, setPreferredLanguage] = useState("");
  const [medicalLiteracyLevel, setMedicalLiteracyLevel] = useState("");
  const [bloodType, setBloodType] = useState("");
  const [heightCm, setHeightCm] = useState("");
  const [weightKg, setWeightKg] = useState("");
  const [city, setCity] = useState("");
  const [showOptional, setShowOptional] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const [, navigate] = useLocation();
  const { toast } = useToast();
  const user = useAuthStore((s) => s.user);
  const setAuth = useAuthStore((s) => s.setAuth);
  const token = useAuthStore((s) => s.token);
  const refreshToken = useAuthStore((s) => s.refreshToken);

  const filledCount = [dateOfBirth, gender, preferredLanguage, medicalLiteracyLevel].filter(Boolean).length;
  const progressPct = (filledCount / 4) * 100;

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    if (!dateOfBirth) newErrors.dateOfBirth = "Date of birth is required";
    if (!gender) newErrors.gender = "Gender is required";
    if (!preferredLanguage) newErrors.preferredLanguage = "Preferred language is required";
    if (!medicalLiteracyLevel) newErrors.medicalLiteracyLevel = "Medical literacy level is required";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    try {
      const body: Record<string, unknown> = {
        date_of_birth: dateOfBirth,
        gender,
        preferred_language: preferredLanguage,
        medical_literacy_level: medicalLiteracyLevel,
      };
      if (bloodType) body.blood_type = bloodType;
      if (heightCm) body.height_cm = parseFloat(heightCm);
      if (weightKg) body.weight_kg = parseFloat(weightKg);
      if (city) body.city = city;

      const res = await authFetch("/api/patients/profile", {
        method: "PUT",
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to update profile");

      if (user && token && refreshToken) {
        setAuth(token, refreshToken, {
          ...user,
          onboardingComplete: true,
          preferredLanguage,
        });
      }

      toast({ title: "Profile completed!", description: "Your health reports will now be personalized." });
      navigate("/");
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = () => {
    navigate("/");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-secondary/5 p-4">
      <ScaleIn>
        <Card className="w-full max-w-lg shadow-xl border-border/50">
          <CardHeader className="text-center pb-2">
            <FadeIn delay={0.1}>
              <div className="flex items-center justify-center gap-2.5 mb-3">
                <div className="w-11 h-11 rounded-xl bg-primary flex items-center justify-center shadow-lg">
                  <Heart className="h-6 w-6 text-primary-foreground" />
                </div>
                <CardTitle className="text-2xl font-heading font-bold tracking-tight">CareOrbit</CardTitle>
              </div>
            </FadeIn>
            <CardDescription className="text-base">
              Complete your profile to get personalized health reports tailored to your age, gender, and language preference.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mb-5">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-heading font-semibold flex items-center gap-2" data-testid="text-onboarding-title">
                  <Sparkles className="h-4 w-4 text-primary" />
                  Complete Your Profile
                </h3>
                <span className="text-xs text-muted-foreground font-medium">{filledCount}/4</span>
              </div>
              <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-primary rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${progressPct}%` }}
                  transition={{ duration: 0.4, ease: "easeOut" }}
                />
              </div>
            </div>

            <FadeIn delay={0.15}>
              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="dob">Date of Birth *</Label>
                  <Input
                    id="dob"
                    type="date"
                    data-testid="input-date-of-birth"
                    value={dateOfBirth}
                    onChange={(e) => { setDateOfBirth(e.target.value); setErrors((p) => ({ ...p, dateOfBirth: "" })); }}
                    max={new Date().toISOString().split("T")[0]}
                    className="h-11"
                  />
                  {errors.dateOfBirth && <p className="text-sm text-destructive" data-testid="error-date-of-birth">{errors.dateOfBirth}</p>}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="gender">Gender *</Label>
                  <Select value={gender} onValueChange={(v) => { setGender(v); setErrors((p) => ({ ...p, gender: "" })); }}>
                    <SelectTrigger data-testid="select-gender" className="h-11">
                      <SelectValue placeholder="Select gender" />
                    </SelectTrigger>
                    <SelectContent>
                      {GENDER_OPTIONS.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value} data-testid={`option-gender-${opt.value}`}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.gender && <p className="text-sm text-destructive" data-testid="error-gender">{errors.gender}</p>}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="language">Preferred Language *</Label>
                  <Select value={preferredLanguage} onValueChange={(v) => { setPreferredLanguage(v); setErrors((p) => ({ ...p, preferredLanguage: "" })); }}>
                    <SelectTrigger data-testid="select-language" className="h-11">
                      <SelectValue placeholder="Select language" />
                    </SelectTrigger>
                    <SelectContent>
                      {LANGUAGE_OPTIONS.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value} data-testid={`option-language-${opt.value}`}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.preferredLanguage && <p className="text-sm text-destructive" data-testid="error-language">{errors.preferredLanguage}</p>}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="literacy">Medical Literacy Level *</Label>
                  <Select value={medicalLiteracyLevel} onValueChange={(v) => { setMedicalLiteracyLevel(v); setErrors((p) => ({ ...p, medicalLiteracyLevel: "" })); }}>
                    <SelectTrigger data-testid="select-literacy" className="h-11">
                      <SelectValue placeholder="Select level" />
                    </SelectTrigger>
                    <SelectContent>
                      {LITERACY_OPTIONS.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value} data-testid={`option-literacy-${opt.value}`}>
                          {opt.label} — {opt.description}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.medicalLiteracyLevel && <p className="text-sm text-destructive" data-testid="error-literacy">{errors.medicalLiteracyLevel}</p>}
                </div>

                <div className="border-t pt-4">
                  <Button
                    type="button"
                    variant="ghost"
                    className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground w-full justify-start px-0"
                    onClick={() => setShowOptional(!showOptional)}
                    data-testid="button-toggle-optional"
                  >
                    {showOptional ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    Additional Details (optional)
                  </Button>

                  <AnimatePresence>
                    {showOptional && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25, ease: "easeInOut" }}
                        className="overflow-hidden"
                      >
                        <div className="space-y-4 mt-4">
                          <div className="space-y-2">
                            <Label htmlFor="bloodType">Blood Type</Label>
                            <Select value={bloodType} onValueChange={setBloodType}>
                              <SelectTrigger data-testid="select-blood-type" className="h-11">
                                <SelectValue placeholder="Select blood type" />
                              </SelectTrigger>
                              <SelectContent>
                                {BLOOD_TYPE_OPTIONS.map((bt) => (
                                  <SelectItem key={bt} value={bt} data-testid={`option-blood-${bt}`}>
                                    {bt}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>

                          <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                              <Label htmlFor="height">Height (cm)</Label>
                              <Input
                                id="height"
                                type="number"
                                data-testid="input-height"
                                placeholder="e.g. 170"
                                value={heightCm}
                                onChange={(e) => setHeightCm(e.target.value)}
                                min="30"
                                max="300"
                                className="h-11"
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor="weight">Weight (kg)</Label>
                              <Input
                                id="weight"
                                type="number"
                                data-testid="input-weight"
                                placeholder="e.g. 70"
                                value={weightKg}
                                onChange={(e) => setWeightKg(e.target.value)}
                                min="1"
                                max="500"
                                className="h-11"
                              />
                            </div>
                          </div>

                          <div className="space-y-2">
                            <Label htmlFor="city">City</Label>
                            <Input
                              id="city"
                              data-testid="input-city"
                              placeholder="e.g. Mumbai"
                              value={city}
                              onChange={(e) => setCity(e.target.value)}
                              className="h-11"
                            />
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                <Button
                  type="submit"
                  className="w-full h-11 shadow-sm"
                  disabled={loading}
                  data-testid="button-submit-profile"
                >
                  <UserCheck className="h-4 w-4 mr-2" />
                  {loading ? "Saving..." : "Complete Profile"}
                </Button>
              </form>
            </FadeIn>

            <Button
              variant="ghost"
              onClick={handleSkip}
              className="w-full text-center text-sm text-muted-foreground hover:text-foreground mt-4"
              data-testid="button-skip-onboarding"
            >
              Skip for now
            </Button>
          </CardContent>
        </Card>
      </ScaleIn>
    </div>
  );
}
