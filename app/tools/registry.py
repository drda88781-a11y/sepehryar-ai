"""
Extensible Tool Registry for orchestrating agent tools with Pydantic contracts and auditing.
"""
import time
from typing import Callable, Any, Optional
from pydantic import BaseModel
from app.core.audit import record_audit
from app.core.logger import get_logger
from app.storage.repository import storage_repo

logger = get_logger("tool_registry")


class ToolDefinition(BaseModel):
    name: str
    description: str
    category: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]


class ToolRegistry:
    """Registry maintaining available tools, their parameter schemas, and execution wrappers."""

    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., Any]] = {}
        self._metadata: dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        category: str = "general",
        input_model: Optional[type[BaseModel]] = None,
        output_model: Optional[type[BaseModel]] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to register a tool with input/output validation models."""
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            in_schema = input_model.model_json_schema() if input_model else {}
            out_schema = output_model.model_json_schema() if output_model else {}

            self._tools[name] = func
            self._metadata[name] = ToolDefinition(
                name=name,
                description=description,
                category=category,
                input_schema=in_schema,
                output_schema=out_schema
            )
            logger.debug(f"Registered tool '{name}' [{category}]")
            return func
        return decorator

    def get_tool(self, name: str) -> Optional[Callable[..., Any]]:
        """Fetch tool function by name."""
        return self._tools.get(name)

    def list_tools(self, category: Optional[str] = None) -> list[ToolDefinition]:
        """List metadata for registered tools, optionally filtered by category."""
        if category:
            return [m for m in self._metadata.values() if m.category == category]
        return list(self._metadata.values())

    def execute(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool with timer, audit logging, and error recovery."""
        func = self._tools.get(tool_name)
        if not func:
            raise ValueError(f"Tool '{tool_name}' is not registered in the system.")

        start_time = time.perf_counter()
        success = True
        err_msg = None
        result = None

        try:
            result = func(**kwargs)
            return result
        except Exception as e:
            success = False
            err_msg = str(e)
            logger.error(f"Error executing tool '{tool_name}': {e}")
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            # Record audit
            record_audit(
                action="TOOL_EXECUTION",
                tool=tool_name,
                success=success,
                duration_ms=duration_ms,
                error_message=err_msg,
                metadata={"inputs": kwargs}
            )
            # Record in SQLite tool history
            try:
                storage_repo.record_tool_execution(
                    tool_name=tool_name,
                    input_data=kwargs,
                    output_data=result.model_dump() if hasattr(result, "model_dump") else str(result),
                    success=success,
                    duration_ms=duration_ms
                )
            except Exception as e:
                logger.debug(f"Could not persist tool execution history: {e}")


tool_registry = ToolRegistry()
register_tool = tool_registry.register
