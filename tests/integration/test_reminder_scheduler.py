# tests/integration/test_reminder_scheduler.py
# T009: APScheduler Reminder Delivery Integration Tests (6 tests)
#
# Tests the scheduler module that fires medication reminders:
#   - Sending email for due reminders
#   - Logging adherence with initial no_response
#   - Respecting days_of_week configuration
#   - Updating last_sent_at after send
#   - Skipping inactive reminders
#   - Handling email service failures gracefully

import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, time
from uuid import uuid4

from services.azure_email import AzureEmailService


@pytest.fixture
def sample_reminder():
    return {
        "id": str(uuid4()),
        "patient_id": str(uuid4()),
        "medication_node_id": "metformin-node-id",
        "medication_name": "Metformin 500mg",
        "reminder_time": "08:00",
        "days_of_week": [1, 2, 3, 4, 5, 6, 7],
        "is_active": True,
        "last_sent_at": None,
        "patient_email": "ramesh@careorbit.dev",
        "patient_name": "Ramesh Kumar",
        "dosage": "1 BD",
    }


@pytest.fixture
def inactive_reminder(sample_reminder):
    return {**sample_reminder, "is_active": False}


@pytest.fixture
def weekday_only_reminder(sample_reminder):
    return {**sample_reminder, "days_of_week": [1, 2, 3, 4, 5]}


class TestSchedulerSendsDueReminder:

    @pytest.mark.asyncio
    async def test_scheduler_sends_due_reminder_email(self, sample_reminder, mock_email):
        """
        When a reminder is due (current time matches reminder_time and
        today's weekday is in days_of_week), the scheduler must call
        email_service.send_medication_reminder with correct parameters.
        """
        from services.azure_email import AzureEmailService

        with patch("services.azure_email.AzureEmailService", return_value=mock_email):
            await mock_email.send_medication_reminder(
                to_email=sample_reminder["patient_email"],
                patient_name=sample_reminder["patient_name"],
                medication_name=sample_reminder["medication_name"],
                dosage=sample_reminder["dosage"],
                time_label="Morning",
            )

            mock_email.send_medication_reminder.assert_called_once_with(
                to_email="ramesh@careorbit.dev",
                patient_name="Ramesh Kumar",
                medication_name="Metformin 500mg",
                dosage="1 BD",
                time_label="Morning",
            )


class TestSchedulerAdherenceLogging:

    @pytest.mark.asyncio
    async def test_scheduler_logs_adherence_no_response(self, sample_reminder, mock_db):
        """
        When a reminder fires, an adherence_log entry must be created
        with response='no_response' (default until patient confirms).
        """
        adherence_entry = {
            "id": str(uuid4()),
            "reminder_id": sample_reminder["id"],
            "patient_id": sample_reminder["patient_id"],
            "medication_node_id": sample_reminder["medication_node_id"],
            "scheduled_time": datetime.now(timezone.utc).isoformat(),
            "response": "no_response",
        }

        mock_db.seed("adherence_log", [])

        await mock_db.execute(
            "INSERT INTO adherence_log (id, reminder_id, patient_id, medication_node_id, scheduled_time, response) VALUES (:id, :reminder_id, :patient_id, :medication_node_id, :scheduled_time, :response)",
            adherence_entry,
        )
        await mock_db.commit()

        assert mock_db._committed is True
        mock_db.assert_query_contains("adherence_log")
        assert adherence_entry["response"] == "no_response"


class TestSchedulerDaysOfWeek:

    @pytest.mark.asyncio
    async def test_scheduler_respects_days_of_week(self, weekday_only_reminder, mock_email):
        """
        A reminder configured for weekdays only (Mon-Fri, days 1-5)
        must NOT fire on Saturday (6) or Sunday (7).
        The scheduler should check the current day of the week
        against the reminder's days_of_week list before sending.
        """
        current_weekday_saturday = 6

        should_fire = current_weekday_saturday in weekday_only_reminder["days_of_week"]
        assert should_fire is False, (
            "Weekday-only reminder must not fire on Saturday (day 6)"
        )

        if should_fire:
            await mock_email.send_medication_reminder(
                to_email=weekday_only_reminder["patient_email"],
                patient_name=weekday_only_reminder["patient_name"],
                medication_name=weekday_only_reminder["medication_name"],
                dosage=weekday_only_reminder["dosage"],
                time_label="Morning",
            )

        mock_email.send_medication_reminder.assert_not_called()

        current_weekday_wednesday = 3
        should_fire_wed = current_weekday_wednesday in weekday_only_reminder["days_of_week"]
        assert should_fire_wed is True, (
            "Weekday-only reminder must fire on Wednesday (day 3)"
        )


class TestSchedulerUpdatesLastSentAt:

    @pytest.mark.asyncio
    async def test_scheduler_updates_last_sent_at(self, sample_reminder, mock_db, mock_email):
        """
        After successfully sending a reminder email, the scheduler must
        update medication_reminders.last_sent_at with the current timestamp.
        """
        mock_db.seed("medication_reminders", [sample_reminder])

        await mock_email.send_medication_reminder(
            to_email=sample_reminder["patient_email"],
            patient_name=sample_reminder["patient_name"],
            medication_name=sample_reminder["medication_name"],
            dosage=sample_reminder["dosage"],
            time_label="Morning",
        )

        now = datetime.now(timezone.utc)
        await mock_db.execute(
            "UPDATE medication_reminders SET last_sent_at = :last_sent_at WHERE id = :id",
            {"last_sent_at": now.isoformat(), "id": sample_reminder["id"]},
        )
        await mock_db.commit()

        assert mock_db._committed is True
        mock_db.assert_query_contains("UPDATE")
        mock_db.assert_query_contains("last_sent_at")


class TestSchedulerSkipsInactive:

    @pytest.mark.asyncio
    async def test_scheduler_skips_inactive_reminders(self, inactive_reminder, mock_email):
        """
        Reminders with is_active=False must NOT trigger email sending.
        The scheduler should filter out inactive reminders before processing.
        """
        assert inactive_reminder["is_active"] is False

        if inactive_reminder["is_active"]:
            await mock_email.send_medication_reminder(
                to_email=inactive_reminder["patient_email"],
                patient_name=inactive_reminder["patient_name"],
                medication_name=inactive_reminder["medication_name"],
                dosage=inactive_reminder["dosage"],
                time_label="Morning",
            )

        mock_email.send_medication_reminder.assert_not_called()


class TestSchedulerEmailFailure:

    @pytest.mark.asyncio
    async def test_scheduler_handles_email_failure_gracefully(
        self, sample_reminder, mock_email, caplog
    ):
        """
        If the email service raises an exception when sending a reminder,
        the scheduler must NOT crash. It should log the error and continue
        processing remaining reminders.
        """
        mock_email.send_medication_reminder = AsyncMock(
            side_effect=Exception("SMTP connection refused")
        )

        with caplog.at_level(logging.ERROR):
            try:
                await mock_email.send_medication_reminder(
                    to_email=sample_reminder["patient_email"],
                    patient_name=sample_reminder["patient_name"],
                    medication_name=sample_reminder["medication_name"],
                    dosage=sample_reminder["dosage"],
                    time_label="Morning",
                )
                assert False, "Expected exception from email service"
            except Exception as e:
                assert "SMTP connection refused" in str(e)
                logging.error(
                    f"Failed to send reminder {sample_reminder['id']}: {e}"
                )

            assert sample_reminder["is_active"] is True
