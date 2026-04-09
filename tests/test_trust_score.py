"""Tests for trust score calculation and policy mapping."""
import pytest


class TestTrustScore:
    def test_brand_new_agent(self):
        from ampro import calculate_trust_score
        ts = calculate_trust_score(age_days=0, interactions=0, incidents=0, endorsements=0, identity_type="did:key")
        assert ts.score == 250  # 0 + 0 + 200 + 0 + 50
        assert ts.tier == "external"

    def test_established_agent(self):
        from ampro import calculate_trust_score
        ts = calculate_trust_score(age_days=365, interactions=1000, incidents=0, endorsements=5, identity_type="jwt")
        # age=200, track=200, clean=200, endorse=200, identity=150 -> 950
        assert ts.score == 950
        assert ts.tier == "internal"  # 800+

    def test_incident_penalty(self):
        from ampro import calculate_trust_score
        ts = calculate_trust_score(age_days=365, interactions=1000, incidents=4, endorsements=0, identity_type="did:key")
        assert ts.factors["clean_history"] == 0  # 200 - 4*50 = 0
        assert ts.factors["age"] == 200

    def test_incident_floor_at_zero(self):
        from ampro import calculate_trust_score
        ts = calculate_trust_score(age_days=0, interactions=0, incidents=100, endorsements=0, identity_type="did:key")
        assert ts.factors["clean_history"] == 0  # not negative

    def test_unknown_identity_type(self):
        from ampro import calculate_trust_score
        ts = calculate_trust_score(age_days=0, interactions=0, incidents=0, endorsements=0, identity_type="unknown")
        assert ts.factors["identity_strength"] == 25

    def test_mtls_identity(self):
        from ampro import calculate_trust_score
        ts = calculate_trust_score(age_days=0, interactions=0, incidents=0, endorsements=0, identity_type="mtls")
        assert ts.factors["identity_strength"] == 200

    def test_endorsement_cap(self):
        from ampro import calculate_trust_score
        ts = calculate_trust_score(age_days=0, interactions=0, incidents=0, endorsements=100, identity_type="did:key")
        assert ts.factors["endorsements"] == 200  # capped at 200

    def test_tier_boundary_800(self):
        from ampro import calculate_trust_score
        ts = calculate_trust_score(age_days=365, interactions=1000, incidents=0, endorsements=5, identity_type="mtls")
        assert ts.score == 1000
        assert ts.tier == "internal"

    def test_tier_boundary_400(self):
        from ampro import calculate_trust_score
        # age=200 + interactions=0 + clean=200 + endorse=0 + did:key=50 = 450 -> verified
        ts = calculate_trust_score(age_days=365, interactions=0, incidents=0, endorsements=0, identity_type="did:key")
        assert ts.score == 450
        assert ts.tier == "verified"

    def test_factor_dict_keys(self):
        from ampro import calculate_trust_score
        ts = calculate_trust_score(age_days=30, interactions=50, incidents=1, endorsements=2, identity_type="jwt")
        assert set(ts.factors.keys()) == {"age", "track_record", "clean_history", "endorsements", "identity_strength"}


class TestScoreToPolicy:
    def test_high_score(self):
        from ampro import score_to_policy
        p = score_to_policy(900)
        assert p.rate_limit_per_minute == 1000
        assert p.content_filter_enabled is False

    def test_medium_score(self):
        from ampro import score_to_policy
        p = score_to_policy(500)
        assert p.rate_limit_per_minute == 100
        assert p.content_filter_enabled is False

    def test_low_score(self):
        from ampro import score_to_policy
        p = score_to_policy(200)
        assert p.rate_limit_per_minute == 10
        assert p.content_filter_enabled is True

    def test_very_low_score(self):
        from ampro import score_to_policy
        p = score_to_policy(50)
        assert p.rate_limit_per_minute == 1
        assert p.content_filter_enabled is True

    def test_boundary_800(self):
        from ampro import score_to_policy
        p = score_to_policy(800)
        assert p.rate_limit_per_minute == 1000

    def test_boundary_799(self):
        from ampro import score_to_policy
        p = score_to_policy(799)
        assert p.rate_limit_per_minute == 100

    def test_boundary_400(self):
        from ampro import score_to_policy
        p = score_to_policy(400)
        assert p.rate_limit_per_minute == 100

    def test_boundary_100(self):
        from ampro import score_to_policy
        p = score_to_policy(100)
        assert p.rate_limit_per_minute == 10

    def test_boundary_0(self):
        from ampro import score_to_policy
        p = score_to_policy(0)
        assert p.rate_limit_per_minute == 1
