import asyncio
import sys
from pathlib import Path
from typing import cast

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from macwise.integration.models import Operation
from macwise.integration.server import SERVER_INSTRUCTIONS, create_server
from macwise.integration.service import CodexReadService
from macwise.models import AuditDocument

EXPECTED_TOOL_NAMES = {operation.value for operation in Operation}


def test_server_lists_exact_closed_read_only_tool_surface(sample_audit: AuditDocument) -> None:
    async def list_tools():
        server = create_server(CodexReadService(audit_provider=lambda: sample_audit))
        return await server.list_tools()

    tools = asyncio.run(list_tools())

    assert {tool.name for tool in tools} == EXPECTED_TOOL_NAMES
    for tool in tools:
        assert tool.annotations is not None
        assert tool.annotations.readOnlyHint is True
        assert tool.annotations.destructiveHint is False
        assert tool.annotations.idempotentHint is True
        assert tool.annotations.openWorldHint is False
        assert tool.outputSchema is not None
        definitions = tool.inputSchema.get("$defs")
        assert isinstance(definitions, dict)
        typed_definitions = cast(dict[str, object], definitions)
        for value in typed_definitions.values():
            assert isinstance(value, dict)
            schema = cast(dict[str, object], value)
            assert schema.get("type") != "object" or schema.get("additionalProperties") is False


def test_server_instructions_lead_with_static_untrusted_evidence_boundary() -> None:
    prefix = SERVER_INSTRUCTIONS[:512].casefold()

    assert "untrusted evidence" in prefix
    assert "read-only" in prefix
    assert "never" in prefix
    assert "apply" in prefix


def test_real_stdio_client_can_initialize_list_and_call(tmp_path: Path) -> None:
    script = """
from datetime import UTC, datetime
from macwise.integration.server import create_server
from macwise.integration.service import CodexReadService
from macwise.models import AuditDocument

audit = AuditDocument(audit_id="audit:stdio", collected_at=datetime(2026, 7, 18, tzinfo=UTC))
create_server(CodexReadService(audit_provider=lambda: audit)).run(transport="stdio")
"""

    async def exercise() -> tuple[set[str], bool, bool, str | None, str]:
        parameters = StdioServerParameters(command=sys.executable, args=["-c", script])
        stderr_path = tmp_path / "server.stderr"
        with stderr_path.open("w+", encoding="utf-8") as stderr:
            async with (
                stdio_client(parameters, errlog=stderr) as (read, write),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                listed = await session.list_tools()
                called = await session.call_tool(
                    "audit_mac", {"request": {"schema_version": 1, "refresh": False}}
                )
                rejected = await session.call_tool(
                    "audit_mac",
                    {
                        "request": {
                            "schema_version": 1,
                            "refresh": False,
                            "shell": "rm",
                        },
                    },
                )
            stderr.seek(0)
            error_text = stderr.read()
        structured = called.structuredContent
        audit_id = structured.get("audit_id") if structured is not None else None
        return (
            {tool.name for tool in listed.tools},
            bool(called.isError),
            bool(rejected.isError),
            audit_id,
            error_text,
        )

    names, is_error, extra_was_rejected, audit_id, stderr = asyncio.run(exercise())

    assert names == EXPECTED_TOOL_NAMES
    assert is_error is False
    assert extra_was_rejected is True
    assert audit_id == "audit:stdio"
    assert "traceback" not in stderr.casefold()
