# tests/security/test_rate_limiting.py
# V3 FIXES:
#   C4: Redesigned — uses correct password on 6th attempt (falsifiable)
#   H3: Added X-Forwarded-For headers to simulate same-IP
# V4: Preserved all V3 fixes.

import pytest
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4

client = TestClient(app)

RATE_LIMIT_IP = "10.0.0.42"


class TestAuthRateLimiting:

    def test_login_rate_limited_after_5_failures(self):
        """
        V3 FIX C4: Falsifiable design.
        Steps:
          1. Register a real user (known password)
          2. Send 5 wrong-password attempts from same IP
          3. Send CORRECT password on 6th attempt
        If rate limiting works: 6th returns 429 (locked despite correct pwd)
        If rate limiting broken: 6th returns 200 → test fails correctly
        """
        email = f"ratelimit.{uuid4().hex[:8]}@test.com"
        password = "CorrectPass123!"

        # Step 1: Register real user
        reg = client.post("/api/auth/register", json={
            "name": "Rate Limit Test",
            "email": email,
            "password": password,
            "phone_number": "+919876500001"
        })
        assert reg.status_code in (200, 201, 202)

        # Step 2: 5 wrong-password attempts from same IP
        for i in range(5):
            client.post("/api/auth/login", json={
                "email": email,
                "password": f"wrong-password-{i}"
            }, headers={"X-Forwarded-For": RATE_LIMIT_IP})

        # Step 3: Correct password on 6th attempt
        response = client.post("/api/auth/login", json={
            "email": email,
            "password": password  # Correct!
        }, headers={"X-Forwarded-For": RATE_LIMIT_IP})

        # If rate limiting works → 429 (blocked despite correct password)
        # If rate limiting broken → 200 (test fails correctly)
        assert response.status_code == 429, \
            f"Expected 429 (rate limited), got {response.status_code}. " \
            f"Rate limiting may not be implemented or threshold not 5."

    def test_different_ip_not_rate_limited(self):
        """Rate limiting must be per-IP, not global."""
        email = f"ratelimit2.{uuid4().hex[:8]}@test.com"
        client.post("/api/auth/register", json={
            "name": "RL Test 2", "email": email,
            "password": "Pass123!", "phone_number": "+919876500002"
        })

        # 5 failures from IP-A
        for i in range(5):
            client.post("/api/auth/login", json={
                "email": email, "password": f"wrong-{i}"
            }, headers={"X-Forwarded-For": "10.0.0.1"})

        # Login from IP-B should succeed
        response = client.post("/api/auth/login", json={
            "email": email, "password": "Pass123!"
        }, headers={"X-Forwarded-For": "10.0.0.2"})
        assert response.status_code == 200, \
            "Rate limiting from IP-A must not block IP-B"
