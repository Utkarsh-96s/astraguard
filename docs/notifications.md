# ASTRA-GUARD Mission Safety Notification Subsystem

The **ASTRA-GUARD Notification Subsystem** provides multi-channel alert delivery, tiered escalation policies, cryptographic operator action tokens, and tamper-evident audit logging for spacecraft operational safety.

---

## 1. Architectural Principles & Invariants

### 1.1 Human-in-the-Loop (HITL) Advisory Invariant
- **Advisory Only**: All alerts, recommendations, and notification action triggers are purely advisory.
- **Safety Lock**: Clicking "Acknowledge", "Approve", or tapping an inline notification button records an immutable entry into the `operator_actions` audit trail and halts ongoing escalation. It **never** autonomously commands thrusters or executes orbital maneuvers.

### 1.2 Honest Channel Status
- A channel is displayed as `CONNECTED` **only** after a genuine handshake or verified credentials.
- Channel states:
  - `NOT CONFIGURED`: Credentials or environment variables are absent. The UI and API explicitly display the required variable names. Success is never faked.
  - `PENDING VERIFICATION`: Credentials are configured, awaiting user linking handshake or verification ping.
  - `CONNECTED`: Active, verified connection confirmed.
  - `ERROR`: Delivery or authentication error, with the exact provider reason reported.

### 1.3 Transactional Outbox Pattern
- **At-Least-Once Delivery**: Alerts and outbox delivery records are created transactionally.
- **Worker Daemon**: `OutboxWorker` claims queued deliveries using database locks, evaluates quiet hours, enforces channel rate limits, and dispatches via provider adapters.
- **Exponential Backoff**: Transient errors trigger retries with exponential backoff (`delay = initial_delay * (2 ** attempts)`).
- **Dead-Letter Queue (DLQ)**: Deliveries exceeding max attempts (default 3) transition to `status: "dead"`. Operators can inspect the error details and trigger manual requeueing from the UI.
- **Deterministic Idempotency**: Each delivery has a deterministic idempotency key (`sha256(alert_id:channel_id:level:version)`), preventing duplicate external dispatches.

### 1.4 Tiered Escalation Matrix
- **Tier L1 (Immediate, 0s delay)**: Real-time interactive channels (Telegram, Web Push PWA, ntfy.sh).
- **Tier L2 (Secondary, default 300s / 5m delay)**: Asynchronous channels (SMTP Email, SMS). Dispatched if unacknowledged within the delay.
- **Tier L3 (Flight Director Escalation, default 900s / 15m delay)**: Emergency escalation (Mission Webhook, Flight Director SMS).
- **Cancellation**: Any operator action (Approve, Dismiss, Snooze) recorded by any user or channel immediately halts the escalation timer.

---

## 2. Notification Adapters & Configuration

### 2.1 Telegram Bot Adapter
- **Implementation**: `apps/api/app/services/adapters/telegram.py` & `apps/api/app/services/telegram_service.py`
- **Features**:
  - Secure deep-link and linking code generation (`/start <linking_code>`).
  - Interactive inline keyboards for one-tap **Acknowledge**, **Dismiss**, and **Snooze**.
  - Rate limiting (30 msg/sec global, 1 msg/sec per chat).
  - Handles HTTP 403 (bot blocked by user) and marks channel `UNSUBSCRIBED`.
  - Inbound webhook authentication via `X-Telegram-Bot-Api-Secret-Token`.
  - In-place message edits upon operator action to prevent stale clicks.
- **Environment Variables**:
  ```env
  TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"
  TELEGRAM_BOT_USERNAME="AstraGuardAlertsBot"
  TELEGRAM_WEBHOOK_SECRET="optional_random_hex_secret"
  ```

### 2.2 Phone Alerts: Web Push (PWA) & ntfy.sh
- **Implementation**:
  - Web Push: `apps/api/app/services/adapters/webpush.py`
  - ntfy: `apps/api/app/services/adapters/ntfy.py`
  - Service Worker: `apps/web/public/sw.js` & `apps/web/public/manifest.json`
  - UI Modal: `apps/web/src/components/PhoneAlertsModal.tsx`
- **Features**:
  - Standard P-256 Elliptic Curve VAPID keypair generation (`POST /api/v1/notifications/push/generate-vapid-keys`).
  - Native browser PushManager subscription with interactive action buttons (`Approve`, `Snooze`).
  - Topic-based publish to `ntfy.sh` (or self-hosted ntfy instance) with priority levels 1-5, tags (`rotating_light`, `warning`, `satellite`), and direct HTTP action buttons.
  - Automatic tag replacement (`tag: "alert-{alert_id}"`) so acknowledging replaces the push alert with an acknowledgment confirmation on the user's phone.
- **Environment Variables**:
  ```env
  VAPID_PUBLIC_KEY="BN...your_ec_public_key..."
  VAPID_PRIVATE_KEY="your_ec_private_key..."
  VAPID_CLAIM_EMAIL="mailto:ops@astra-guard.internal"
  NTFY_BASE_URL="https://ntfy.sh"
  NTFY_TOPIC="astraguard_alerts"
  ```

### 2.3 Email (SMTP) Adapter
- **Implementation**: `apps/api/app/services/adapters/email.py`
- **Features**:
  - Standard library `smtplib` executed in asynchronous threads via `asyncio.to_thread`.
  - Multipart MIME messages with both plain-text fallback and dark mission-critical HTML styling.
  - **Email Scanner / Pre-fetch Protection**: Action links lead to an intermediate confirmation landing page (`GET /api/v1/alerts/{id}/action-token/{token}`). Antivirus or enterprise spam link pre-fetchers cannot accidentally trigger state changes because confirmation requires an explicit human click submitting a POST form.
- **Environment Variables**:
  ```env
  SMTP_HOST="smtp.example.com"
  SMTP_PORT="587"
  SMTP_USER="apikey"
  SMTP_PASSWORD="your_smtp_password"
  SMTP_FROM="alerts@space.corp"
  SMTP_USE_TLS="true"
  ```

### 2.4 Generic Webhook Adapter (with SSRF Defense & HMAC Signatures)
- **Implementation**: `apps/api/app/services/adapters/webhook.py`
- **Features**:
  - **Strict SSRF Protection**: `is_safe_webhook_url` parses hostname, performs DNS resolution, and rejects loopback (`127.0.0.1`, `localhost`, `::1`), RFC 1918 private IPs (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local IPs (`169.254.0.0/16`), multicast, and cloud metadata targets (`metadata.google.internal`, AWS metadata IP).
  - Local URLs are permitted only when `ALLOW_LOCAL_WEBHOOKS=True` in config.
  - **Cryptographic Authentication**: Every outbound webhook request contains:
    - `X-AstraGuard-Signature`: `sha256=<hmac_hex>`
    - `X-AstraGuard-Timestamp`: ISO-8601 timestamp (protects receiver against replay attacks)
    - `X-AstraGuard-Event`: Event name (`alert.critical`, `alert.acknowledged`, `alert.test`)
  - Configurable custom headers and webhook secrets.
- **Environment Variables**:
  ```env
  ALLOW_LOCAL_WEBHOOKS="false"
  SECRET_KEY="your_secure_hmac_secret_key"
  ```

### 2.5 SMS Adapter (Twilio)
- **Implementation**: `apps/api/app/services/adapters/sms.py`
- **Features**:
  - International standard **E.164 phone number validation** via regex (`^\+[1-9]\d{1,14}$`).
  - Concise SMS formatting with shortened action URLs.
  - **Daily Cost Cap**: Operator credits protected by `TWILIO_DAILY_COST_LIMIT_USD`. Dispatches are throttled if daily spending exceeds the cap.
  - Contact masking (`+1 *** *** 4412`) ensures phone numbers are never logged in clear text.
- **Environment Variables**:
  ```env
  TWILIO_ACCOUNT_SID="ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
  TWILIO_AUTH_TOKEN="your_auth_token"
  TWILIO_FROM_NUMBER="+15551234567"
  TWILIO_DAILY_COST_LIMIT_USD="25.0"
  ```

---

## 3. Cryptographic Action Tokens

Action tokens allow secure, one-click acknowledgements from emails, SMS, and push notifications without requiring full session login.

- **Token Format**: `<payload_b64>.<sig_b64>`
- **Payload Contents**: `alert_id:channel_id:action:user_id:expiry_timestamp:nonce`
- **Signature**: `HMAC-SHA256(SECRET_KEY, payload_b64)`
- **Registry & Anti-Replay**: The SHA-256 hash of the token is recorded in `link_tokens`. Upon consumption, `used_at` is stamped. Any replay attempt is rejected immediately.
- **Tamper Resistance**: Any alteration of the payload or signature fails cryptographic constant-time comparison (`hmac.compare_digest`).

---

## 4. Web Dashboard UI Features

The operational Alerts page (`apps/web/src/app/dashboard/alerts/page.tsx`) provides complete visibility and control:

1. **Real-Time WebSocket Feed (`/ws/alerts`)**:
   - Connection status pill with pulsing indicators (`WS LIVE`, `CONNECTING`, `WS OFFLINE`).
   - Exponential backoff reconnection (1s &rarr; 15s).
   - Catch-up query using `since={last_seen_cursor}` so no alerts are dropped during disconnections.

2. **Search & Filter Toolbar**:
   - Real-time text search (`q=...`) across title, safety rationale, and recommendations.
   - Spacecraft asset selector (`asset_id=...`).
   - Severity filters (`ALL`, `CRITICAL`, `WARNING`, `WATCH`).
   - Status filters (`ALL`, `ACTIVE`, `ACKNOWLEDGED`, `DISMISSED`, `SNOOZED`).

3. **Delivery Chips Component (`DeliveryChips.tsx`)**:
   - Displayed on every alert card.
   - Live status badges for each delivery channel: Telegram, Web Push, ntfy, Email, Webhook, SMS.
   - Hover tooltip displays delivery timestamp, provider message ID, attempt count, and last error.

4. **Escalation Badges & Countdown Timers**:
   - Displays active escalation tier (`Tier L1`, `Tier L2`, `Tier L3`).
   - Real-time countdown timer to next tier escalation (`Escalating to L2 in 4m 12s`).
   - Reflects halted state immediately when an operator acknowledges.

5. **Notification Settings Console (`NotificationSettingsModal.tsx`)**:
   - **Provider Health Tab**: Honest status badges for all 6 providers, explicit lists of missing environment variables, and "Send Test Alert" button.
   - **Channels Tab**: Register new email, webhook, SMS, Telegram, or ntfy channels with verification and test dispatches.
   - **Escalation Tab**: Configure tiered escalation delays (L2 delay, L3 delay).
   - **Dead-Letter Queue Tab**: Inspect failed deliveries and retry outbox dispatches.

6. **Simulated Test Trigger (F9)**:
   - Header button fires a verified test alert (`[SIMULATED]`) through the outbox, exercising adapters with `test=true`.

---

## 5. Self-Test & Verification

To verify the complete notification subsystem end-to-end, run:

```bash
make notify-selftest
# Or directly via Python:
python scripts/notify_selftest.py
```

The self-test validates:
1. Database schema readiness (all 7 models accessible).
2. Honest status reporting for all 6 provider adapters.
3. Cryptographic HMAC token generation, valid verification, single-use consumption, anti-replay guards, and tamper resistance.
4. SSRF protection against loopback, private IP, and cloud metadata targets.
5. Outbox queuing and worker batch processing.
6. Tiered escalation matrix initialization and cancellation on operator action.

All test suites:
- Notification Core Tests: `pytest apps/api/tests/test_stage1_notification_core.py`
- Telegram Bot Tests: `pytest apps/api/tests/test_stage2_telegram_bot.py`
- Phone Push & ntfy Tests: `pytest apps/api/tests/test_stage3_phone_alerts.py`
- Email, Webhook, SMS Tests: `pytest apps/api/tests/test_stage4_email_webhook_sms.py`
- Demo Scenario Regression: `pytest apps/api/tests/test_demo_scenario.py`
- Full API Test Suite: `pytest apps/api/tests/` (114/114 passing)
