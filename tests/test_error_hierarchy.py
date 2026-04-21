"""Tests for issue #47 — unified AmpError hierarchy."""
from __future__ import annotations

import pytest

from ampro.errors import (
    AmpError,
    CompliancePolicyError,
    CryptoError,
    MigrationChainTooLongError,
    NotImplementedInProtocol,
    RateLimitError,
    RedirectLoopError,
    SessionError,
    TransportError,
    TrustError,
    ValidationError as AmpValidationError,
)


class TestBaseHierarchy:
    def test_all_errors_inherit_from_amp_error(self):
        for cls in (
            AmpValidationError,
            TrustError,
            CryptoError,
            SessionError,
            CompliancePolicyError,
            RateLimitError,
            TransportError,
            NotImplementedInProtocol,
            RedirectLoopError,
            MigrationChainTooLongError,
        ):
            assert issubclass(cls, AmpError), f"{cls.__name__} must inherit from AmpError"
            assert issubclass(cls, Exception)

    def test_concrete_transport_errors_inherit_from_transport_error(self):
        assert issubclass(RedirectLoopError, TransportError)
        assert issubclass(MigrationChainTooLongError, TransportError)

    def test_cost_receipt_verification_error_is_crypto_error(self):
        from ampro.delegation.cost_receipt import CostReceiptVerificationError

        assert issubclass(CostReceiptVerificationError, CryptoError)
        assert issubclass(CostReceiptVerificationError, AmpError)

    def test_session_replay_error_is_session_error(self):
        from ampro.session.handshake import SessionReplayError

        assert issubclass(SessionReplayError, SessionError)
        assert issubclass(SessionReplayError, AmpError)

    def test_ampi_amp_error_is_amp_error(self):
        from ampro.ampi.errors import AMPError as AMPIError

        assert issubclass(AMPIError, AmpError)

    def test_errors_exported_from_top_level(self):
        from ampro import AmpError as ExportedAmpError
        from ampro import RedirectLoopError as ExportedRedirectLoopError
        from ampro import MigrationChainTooLongError as ExportedMigration

        assert ExportedAmpError is AmpError
        assert ExportedRedirectLoopError is RedirectLoopError
        assert ExportedMigration is MigrationChainTooLongError

    def test_amp_error_can_be_raised_and_caught(self):
        with pytest.raises(AmpError):
            raise RedirectLoopError("test")
        with pytest.raises(TransportError):
            raise RedirectLoopError("test")
        with pytest.raises(CryptoError):
            from ampro.delegation.cost_receipt import CostReceiptVerificationError

            raise CostReceiptVerificationError("bad sig")
