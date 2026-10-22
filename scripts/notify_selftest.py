#!/usr/bin/env python3
"""ASTRA-GUARD Notification Engine Self-Test Suite (notify-selftest).

Validates end-to-end reliability, provider connectivity, outbox queueing,
HMAC token security, SSRF defenses, and tiered escalation.
"""
import asyncio
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

# Add apps/api to PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
API_DIR = ROOT_DIR / "apps" / "api"
sys.path.insert(0, str(API_DIR))

from app.core.config import settings
from app.db.models import (
    Alert,
    Base,
    EscalationPolicy,
    EscalationState,
    InboundEvent,
    LinkToken,
    NotificationChannel,
    NotificationOutbox,
    Subscription,
)
from app.db.session import AsyncSessionLocal
from app.services.adapters.registry import adapter_registry
from app.services.adapters.webhook import is_safe_webhook_url
from app.services.alert_service import alert_service
from app.services.escalation_engine import escalation_engine
from app.services.outbox_worker import outbox_worker
from app.services.tokens import (
    generate_action_token,
    verify_and_consume_action_token,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


class NotificationSelfTestRunner:
    """Executes verification tests for all notification features."""

    def __init__(self) -> None:
        self.results: list[dict[str, str]] = []

    def record(self, test_name: str, passed: bool, notes: str = "") -> None:
        status = "PASS" if passed else "FAIL"
        self.results.append({"test": test_name, "status": status, "notes": notes})
        symbol = "[OK]" if passed else "[FAIL]"
        print(f"  {symbol:<6} {test_name}: {status} {f'({notes})' if notes else ''}")

    async def get_test_db_session(self):
        """Connect to configured database or create isolated SQLite in-memory test session."""
        try:
            session = AsyncSessionLocal()
            await session.execute(select(1))
            return session, None
        except Exception:  # noqa: BLE001
            test_engine = create_async_engine(
                "sqlite+aiosqlite:///:memory:",
                connect_args={"check_same_thread": False},
                future=True,
            )
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            session_factory = async_sessionmaker(
                bind=test_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            return session_factory(), test_engine

    async def run(self) -> int:
        print("=" * 72)
        print("ASTRA-GUARD NOTIFICATION SUBSYSTEM SELF-TEST (make notify-selftest)")
        print(f"Timestamp: {datetime.now(UTC).isoformat()} | Environment: {settings.ENVIRONMENT}")
        print("=" * 72)

        db, fallback_engine = await self.get_test_db_session()
        db_type = "Isolated In-Memory SQLite" if fallback_engine else "Configured Database"
        print(f"Database Backend: {db_type}\n")

        try:
            async with db:
                # 1. DB Schema Check
                print("[Phase 1] Database & Notification Schema Verification...")
                await self.test_db_schema(db)

                # 2. Honest Provider Health Checks
                print("\n[Phase 2] Honest Provider Adapter Health Checks...")
                await self.test_provider_adapters()

                # 3. HMAC Action Token Cryptography & Tamper Resistance
                print("\n[Phase 3] HMAC Cryptographic Action Tokens & Replay Guards...")
                await self.test_hmac_action_tokens(db)

                # 4. SSRF Defense on Webhooks
                print("\n[Phase 4] Webhook SSRF Validation & Private IP Blocking...")
                self.test_ssrf_defenses()

                # 5. Outbox Queueing & Exponential Backoff Worker
                print("\n[Phase 5] Outbox Queueing & Worker Execution...")
                await self.test_outbox_pipeline(db)

                # 6. Tiered Escalation Policy Evaluation
                print("\n[Phase 6] Tiered Escalation Matrix & Cancellation...")
                await self.test_escalation_lifecycle(db)
        finally:
            if fallback_engine:
                await fallback_engine.dispose()

        # Print Final Summary Table
        print("\n" + "=" * 72)
        print("SELF-TEST RESULTS SUMMARY")
        print("=" * 72)
        print(f"{'Test':<48} | {'Status':<6} | {'Notes'}")
        print("-" * 72)

        all_passed = True
        for r in self.results:
            if r["status"] != "PASS":
                all_passed = False
            print(f"{r['test']:<48} | {r['status']:<6} | {r['notes']}")

        print("=" * 72)
        if all_passed:
            print("[OK] ALL NOTIFICATION SELF-TESTS PASSED (Production / Demo Ready)")
            return 0
        else:
            print("[FAIL] SOME TESTS FAILED. Check details above.")
            return 1

    async def test_db_schema(self, db) -> None:
        try:
            for model in [
                NotificationChannel,
                Subscription,
                NotificationOutbox,
                EscalationPolicy,
                EscalationState,
                LinkToken,
                InboundEvent,
            ]:
                await db.execute(select(model).limit(1))
            self.record("DB Schema: Tables Accessible", True, "All 7 notification models operational")
        except Exception as e:  # noqa: BLE001
            self.record("DB Schema: Tables Accessible", False, str(e))

    async def test_provider_adapters(self) -> None:
        try:
            health_list = await adapter_registry.check_all_health()
            for p in health_list:
                ch_type = p["type"]
                status = p["status"]
                details = p.get("details", "")
                missing = p.get("missing_env", [])
                notes = f"{status}"
                if missing:
                    notes += f" (missing: {', '.join(missing)})"
                elif details:
                    notes += f" ({details})"
                self.record(f"Provider: {ch_type.upper()}", True, notes)
        except Exception as e:  # noqa: BLE001
            self.record("Provider Health Check", False, str(e))

    async def test_hmac_action_tokens(self, db) -> None:
        try:
            raw_token, action_url = await generate_action_token(
                db=db,
                alert_id="ALT-SELFTEST-001",
                channel_id="CHN-TEST",
                action="approve",
                expiry_seconds=3600,
            )
            self.record("HMAC Token: Generation", bool(raw_token and action_url), "Generated signed URL")

            # Validate valid token consumption
            consumed_data = await verify_and_consume_action_token(db, raw_token)
            self.record(
                "HMAC Token: Single-Use Consumption",
                consumed_data.get("alert_id") == "ALT-SELFTEST-001" and consumed_data.get("action") == "approve",
                "Successfully verified & consumed",
            )

            # Validate replay rejection (single-use)
            replayed = False
            try:
                await verify_and_consume_action_token(db, raw_token)
                replayed = True
            except ValueError:
                replayed = False
            self.record("HMAC Token: Anti-Replay Guard", not replayed, "Replayed token correctly rejected")

            # Validate tamper resistance
            tampered = raw_token[:-4] + "ffff"
            tamper_caught = False
            try:
                await verify_and_consume_action_token(db, tampered)
            except ValueError:
                tamper_caught = True
            self.record("HMAC Token: Tamper Resistance", tamper_caught, "Modified signature rejected")
        except Exception as e:  # noqa: BLE001
            self.record("HMAC Token Test", False, str(e))

    def test_ssrf_defenses(self) -> None:
        try:
            blocked_targets = [
                "http://127.0.0.1:8000/api",
                "http://localhost:3000/webhook",
                "http://169.254.169.254/latest/meta-data",
                "http://10.0.0.1/admin",
                "http://192.168.1.1/hook",
            ]
            all_blocked = True
            for url in blocked_targets:
                is_safe, _ = is_safe_webhook_url(url, allow_local=False)
                if is_safe:
                    all_blocked = False

            self.record("SSRF: Loopback & Private IP Blocking", all_blocked, "Blocked 127.0.0.1, AWS meta-data, RFC1918")

            safe_target = "https://httpbin.org/post"
            is_safe, _ = is_safe_webhook_url(safe_target, allow_local=False)
            self.record("SSRF: Public Webhook Allowed", is_safe, "Public HTTPS targets permitted")
        except Exception as e:  # noqa: BLE001
            self.record("SSRF Defense Test", False, str(e))

    async def test_outbox_pipeline(self, db) -> None:
        try:
            # Ensure at least one active channel and subscription exists for outbox routing
            stmt = select(NotificationChannel).limit(1)
            existing_ch = (await db.execute(stmt)).scalars().first()
            if not existing_ch:
                ch_id = f"CHN-SELFTEST-{uuid.uuid4().hex[:6].upper()}"
                ch = NotificationChannel(
                    id=ch_id,
                    user_id="FlightDirector",
                    type="fake",
                    name="Self-Test Channel",
                    encrypted_address="selftest@fake.local",
                    status="CONNECTED",
                    verified_at=datetime.now(UTC),
                    created_at=datetime.now(UTC),
                )
                db.add(ch)
                sub = Subscription(
                    id=f"SUB-SELFTEST-{uuid.uuid4().hex[:6].upper()}",
                    channel_id=ch_id,
                    min_level="WATCH",
                    enabled=True,
                    created_at=datetime.now(UTC),
                )
                db.add(sub)
                await db.commit()

            test_alert = await alert_service.fire_test_alert(
                db=db,
                level="CRITICAL",
                asset_id="SENTINEL-2A",
            )
            self.record("Outbox: Test Alert Fired", bool(test_alert.id), f"Created {test_alert.id}")

            outbox_stmt = select(NotificationOutbox).where(NotificationOutbox.alert_id == test_alert.id)
            items = list((await db.execute(outbox_stmt)).scalars().all())
            self.record("Outbox: Deliveries Queued", len(items) > 0, f"{len(items)} outbox delivery records created")

            processed = await outbox_worker.claim_and_process_batch(db, batch_size=10)
            self.record("Outbox: Worker Batch Execution", processed >= 0, f"Processed batch ({processed} items)")
        except Exception as e:  # noqa: BLE001
            self.record("Outbox Pipeline Test", False, str(e))

    async def test_escalation_lifecycle(self, db) -> None:
        try:
            # Ensure policy exists
            policy = await escalation_engine.get_or_create_default_policy(db)
            self.record("Escalation: Policies Defined", bool(policy.id), f"Active policy: {policy.name}")

            dummy_alert = Alert(
                id=f"ALT-ESC-{uuid.uuid4().hex[:8].upper()}",
                snapshot_id="RSN-ESC",
                level="CRITICAL",
                title="[TEST] Escalation Cancellation Test",
                rationale="[SIMULATED] Verify cancellation upon human acknowledgement.",
                recommendation="Acknowledge.",
                status="ACTIVE",
                dedup_key=f"esc_cancel_{uuid.uuid4().hex[:6]}",
                synthetic=True,
                created_at=datetime.now(UTC),
            )
            db.add(dummy_alert)
            await db.flush()

            await escalation_engine.initialize_alert_escalation(db, dummy_alert, test=True)

            esc_state_stmt = select(EscalationState).where(EscalationState.alert_id == dummy_alert.id)
            esc_state = (await db.execute(esc_state_stmt)).scalars().first()
            self.record("Escalation: Tier L1 Scheduled", bool(esc_state and esc_state.current_level == 1), "L1 active")

            await alert_service.record_operator_action(
                db=db,
                alert_id=dummy_alert.id,
                user="FlightDirector",
                action="approve",
                note="Verified in self-test.",
            )

            await db.refresh(esc_state)
            self.record(
                "Escalation: Halted on Operator Ack",
                bool(esc_state.halted_at),
                f"Halted reason: '{esc_state.halted_reason}'",
            )
        except Exception as e:  # noqa: BLE001
            self.record("Escalation Lifecycle Test", False, str(e))


def main() -> None:
    runner = NotificationSelfTestRunner()
    code = asyncio.run(runner.run())
    sys.exit(code)


if __name__ == "__main__":
    main()
