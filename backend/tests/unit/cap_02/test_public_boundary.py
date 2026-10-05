from apistra.modules.catalog import public


def test_public_boundary_exports_endpoint_contracts() -> None:
    assert public.EndpointService
    assert public.ModelEndpoint
    assert public.ProbeOutcome.CONNECTION_VERIFIED == "CONNECTION_VERIFIED"


def test_public_boundary_exports_governed_tool_contracts() -> None:
    assert public.ToolService
    assert public.ToolVersionStatus.PUBLISHED == "PUBLISHED"
