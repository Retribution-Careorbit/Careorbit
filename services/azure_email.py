import logging
from config import get_settings

logger = logging.getLogger("careorbit.services.email")


class AzureEmailService:
    def __init__(self):
        settings = get_settings()
        self._connection_string = settings.AZURE_COMM_CONNECTION_STRING
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self._connection_string:
            return None
        try:
            from azure.communication.email import EmailClient
            self._client = EmailClient.from_connection_string(self._connection_string)
            return self._client
        except Exception as e:
            logger.warning(f"Failed to initialize Email client: {e}")
            return None

    async def send_medication_reminder(self, to_email, patient_name, medication_name, dosage, time_label):
        client = self._get_client()
        if not client:
            raise NotImplementedError("Azure Email not configured")

        try:
            message = {
                "senderAddress": "noreply@careorbit.dev",
                "recipients": {"to": [{"address": to_email}]},
                "content": {
                    "subject": f"CareOrbit: {time_label} Medication Reminder",
                    "html": (
                        f"<h2>Hi {patient_name},</h2>"
                        f"<p>Time for your <strong>{time_label}</strong> medication:</p>"
                        f"<p><strong>{medication_name}</strong> — {dosage}</p>"
                        "<p>Stay healthy! — CareOrbit</p>"
                    ),
                },
            }
            poller = client.begin_send(message)
            poller.result()
            logger.info(f"Medication reminder sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send medication reminder: {e}")
            return False

    async def send_interaction_alert(self, **kwargs):
        client = self._get_client()
        if not client:
            raise NotImplementedError("Azure Email not configured")

        try:
            to_email = kwargs.get("to_email", "")
            patient_name = kwargs.get("patient_name", "")
            drug_pair = kwargs.get("drug_pair", "")
            severity = kwargs.get("severity", "")

            message = {
                "senderAddress": "noreply@careorbit.dev",
                "recipients": {"to": [{"address": to_email}]},
                "content": {
                    "subject": f"CareOrbit: Drug Interaction Alert ({severity})",
                    "html": (
                        f"<h2>Drug Interaction Alert</h2>"
                        f"<p>Patient: {patient_name}</p>"
                        f"<p>Interaction: <strong>{drug_pair}</strong></p>"
                        f"<p>Severity: <strong>{severity}</strong></p>"
                    ),
                },
            }
            poller = client.begin_send(message)
            poller.result()
            return True
        except Exception as e:
            logger.error(f"Failed to send interaction alert: {e}")
            return False

    async def send_upload_result(self, **kwargs):
        client = self._get_client()
        if not client:
            raise NotImplementedError("Azure Email not configured")

        try:
            to_email = kwargs.get("to_email", "")
            patient_name = kwargs.get("patient_name", "")
            doc_type = kwargs.get("doc_type", "document")
            status = kwargs.get("status", "processed")

            message = {
                "senderAddress": "noreply@careorbit.dev",
                "recipients": {"to": [{"address": to_email}]},
                "content": {
                    "subject": f"CareOrbit: Your {doc_type} has been {status}",
                    "html": (
                        f"<h2>Hi {patient_name},</h2>"
                        f"<p>Your {doc_type} has been {status}.</p>"
                        "<p>View results in your CareOrbit dashboard.</p>"
                    ),
                },
            }
            poller = client.begin_send(message)
            poller.result()
            return True
        except Exception as e:
            logger.error(f"Failed to send upload result: {e}")
            return False
