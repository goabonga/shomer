# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for Celery cleanup tasks."""

from __future__ import annotations

from shomer.tasks.cleanup import DEFAULT_BATCH_SIZE


class TestCleanupTaskRegistration:
    """Tests that all cleanup tasks are registered."""

    def test_access_tokens_task_exists(self) -> None:
        """Access tokens cleanup task is registered."""
        from shomer.tasks.cleanup import clean_expired_access_tokens

        assert clean_expired_access_tokens.name == "shomer.cleanup.access_tokens"

    def test_refresh_tokens_task_exists(self) -> None:
        """Refresh tokens cleanup task is registered."""
        from shomer.tasks.cleanup import clean_expired_refresh_tokens

        assert clean_expired_refresh_tokens.name == "shomer.cleanup.refresh_tokens"

    def test_authorization_codes_task_exists(self) -> None:
        """Authorization codes cleanup task is registered."""
        from shomer.tasks.cleanup import clean_expired_authorization_codes

        assert (
            clean_expired_authorization_codes.name
            == "shomer.cleanup.authorization_codes"
        )

    def test_device_codes_task_exists(self) -> None:
        """Device codes cleanup task is registered."""
        from shomer.tasks.cleanup import clean_expired_device_codes

        assert clean_expired_device_codes.name == "shomer.cleanup.device_codes"

    def test_par_requests_task_exists(self) -> None:
        """PAR requests cleanup task is registered."""
        from shomer.tasks.cleanup import clean_expired_par_requests

        assert clean_expired_par_requests.name == "shomer.cleanup.par_requests"

    def test_verification_codes_task_exists(self) -> None:
        """Verification codes cleanup task is registered."""
        from shomer.tasks.cleanup import clean_expired_verification_codes

        assert (
            clean_expired_verification_codes.name == "shomer.cleanup.verification_codes"
        )

    def test_sessions_task_exists(self) -> None:
        """Sessions cleanup task is registered."""
        from shomer.tasks.cleanup import clean_expired_sessions

        assert clean_expired_sessions.name == "shomer.cleanup.sessions"

    def test_mfa_codes_task_exists(self) -> None:
        """MFA codes cleanup task is registered."""
        from shomer.tasks.cleanup import clean_expired_mfa_codes

        assert clean_expired_mfa_codes.name == "shomer.cleanup.mfa_codes"

    def test_revoked_pats_task_exists(self) -> None:
        """Revoked PATs cleanup task is registered."""
        from shomer.tasks.cleanup import clean_revoked_pats

        assert clean_revoked_pats.name == "shomer.cleanup.revoked_pats"


class TestDefaultBatchSize:
    """Tests for default batch size constant."""

    def test_default_batch_size(self) -> None:
        """Default batch size is 1000."""
        assert DEFAULT_BATCH_SIZE == 1000


class TestHelperImports:
    """Tests that helper functions are importable."""

    def test_run_sync_cleanup_importable(self) -> None:
        """_run_sync_cleanup is importable."""
        from shomer.tasks.cleanup import _run_sync_cleanup

        assert callable(_run_sync_cleanup)

    def test_run_sync_cleanup_revoked_importable(self) -> None:
        """_run_sync_cleanup_revoked is importable."""
        from shomer.tasks.cleanup import _run_sync_cleanup_revoked

        assert callable(_run_sync_cleanup_revoked)
