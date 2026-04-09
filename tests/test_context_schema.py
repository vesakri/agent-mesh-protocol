"""Tests for context schema URN parsing and matching."""
import pytest


class TestParseSchemaUrn:
    def test_basic_urn(self):
        from ampro import parse_schema_urn
        info = parse_schema_urn("urn:schema:purchase-order:v1")
        assert info.namespace == "schema"
        assert info.name == "purchase-order"
        assert info.version == "v1"
        assert info.urn == "urn:schema:purchase-order:v1"

    def test_reverse_domain_name(self):
        from ampro import parse_schema_urn
        info = parse_schema_urn("urn:schema:com.example.purchase-order:v1")
        assert info.name == "com.example.purchase-order"

    def test_different_namespace(self):
        from ampro import parse_schema_urn
        info = parse_schema_urn("urn:domain:shipping-manifest:v2")
        assert info.namespace == "domain"
        assert info.name == "shipping-manifest"
        assert info.version == "v2"

    def test_empty_raises(self):
        from ampro import parse_schema_urn
        with pytest.raises(ValueError):
            parse_schema_urn("")

    def test_too_few_parts(self):
        from ampro import parse_schema_urn
        with pytest.raises(ValueError, match="4 colon-separated"):
            parse_schema_urn("urn:schema:name")

    def test_too_many_parts(self):
        from ampro import parse_schema_urn
        with pytest.raises(ValueError, match="4 colon-separated"):
            parse_schema_urn("urn:schema:name:v1:extra")

    def test_wrong_prefix(self):
        from ampro import parse_schema_urn
        with pytest.raises(ValueError, match="urn:"):
            parse_schema_urn("http:schema:name:v1")

    def test_empty_namespace(self):
        from ampro import parse_schema_urn
        with pytest.raises(ValueError, match="Namespace"):
            parse_schema_urn("urn::name:v1")

    def test_empty_name(self):
        from ampro import parse_schema_urn
        with pytest.raises(ValueError, match="Name"):
            parse_schema_urn("urn:schema::v1")

    def test_empty_version(self):
        from ampro import parse_schema_urn
        with pytest.raises(ValueError, match="Version"):
            parse_schema_urn("urn:schema:name:")


class TestCheckSchemaSupported:
    def test_supported(self):
        from ampro import check_schema_supported
        assert check_schema_supported(
            "urn:schema:purchase-order:v1",
            ["urn:schema:purchase-order:v1", "urn:schema:rfq:v2"],
        ) is True

    def test_not_supported(self):
        from ampro import check_schema_supported
        assert check_schema_supported(
            "urn:schema:invoice:v1",
            ["urn:schema:purchase-order:v1"],
        ) is False

    def test_case_insensitive(self):
        from ampro import check_schema_supported
        assert check_schema_supported(
            "URN:SCHEMA:PURCHASE-ORDER:V1",
            ["urn:schema:purchase-order:v1"],
        ) is True

    def test_empty_urn(self):
        from ampro import check_schema_supported
        assert check_schema_supported("", ["urn:schema:x:v1"]) is False

    def test_none_urn(self):
        from ampro import check_schema_supported
        assert check_schema_supported(None, ["urn:schema:x:v1"]) is False

    def test_empty_supported(self):
        from ampro import check_schema_supported
        assert check_schema_supported("urn:schema:x:v1", []) is False
