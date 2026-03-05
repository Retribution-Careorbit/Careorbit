class AzureEmailService:
    async def send_medication_reminder(self, to_email, patient_name, medication_name, dosage, time_label):
        raise NotImplementedError("Azure Email not configured")

    async def send_interaction_alert(self, **kwargs):
        raise NotImplementedError("Azure Email not configured")

    async def send_upload_result(self, **kwargs):
        raise NotImplementedError("Azure Email not configured")
