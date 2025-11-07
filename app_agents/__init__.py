"""Agent orchestration utilities for resume-ats-docx-gen.

This package also re-exports symbols from the `openai-agents` library to
avoid import-name collisions. That way, code can use:

	from agents import Agent, Runner, ModelSettings, WebSearchTool, RunConfig, trace

without shadowing the third-party module. If the third-party package is not
installed, imports will fail with a clear message.
"""

from __future__ import annotations

# Re-export selected symbols from the external `openai-agents` package.
try:  # pragma: no cover - import guard
	import openai_agents as _oa

	Agent = _oa.Agent
	Runner = _oa.Runner
	ModelSettings = _oa.ModelSettings
	WebSearchTool = _oa.WebSearchTool
	RunConfig = _oa.RunConfig
	trace = _oa.trace
	TResponseInputItem = getattr(_oa, "TResponseInputItem", object)
	RunContextWrapper = getattr(_oa, "RunContextWrapper", object)
except Exception as _e:  # pragma: no cover - library optional at runtime
	# Provide a friendly error if these are imported when the package is missing
	def _missing(*_, **__):  # type: ignore
		raise RuntimeError(
			"openai-agents package is required for agent-based workflows. Install it via 'pip install openai-agents'."
		)

	Agent = Runner = ModelSettings = WebSearchTool = RunConfig = trace = _missing  # type: ignore
	TResponseInputItem = RunContextWrapper = object  # harmless placeholders

