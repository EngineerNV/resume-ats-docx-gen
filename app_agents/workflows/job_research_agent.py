from agents import WebSearchTool, RunContextWrapper, Agent, ModelSettings, TResponseInputItem, Runner, RunConfig, trace
from pydantic import BaseModel
from openai.types.shared.reasoning import Reasoning

from ..prompts import (
    ATS_RESEARCH_AGENT_INSTRUCTIONS,
    LEADERSHIP_VALUES_SUMMARY_INSTRUCTIONS,
    format_clean_output_prompt,
    format_judge_ats_research_prompt,
    format_restructure_input_prompt,
)

# Tool definitions
web_search_preview = WebSearchTool(
  search_context_size="medium",
  user_location={
    "type": "approximate"
  }
)
web_search_preview1 = WebSearchTool(
  search_context_size="medium",
  user_location={
    "country": "US",
    "type": "approximate"
  }
)
class JudgeAtsResearchAgentSchema(BaseModel):
  status: str
  failure_summary: str
  websearch_tries: float


class AtsResearchAgentSchema(BaseModel):
  job_title: str
  primary_keywords: list[str]
  secondary_keywords: list[str]
  soft_skills: list[str]
  certifications: list[str]
  recommended_resume_phrases: list[str]
  sources: list[str]


class JudgeAtsResearchAgentContext:
  def __init__(self, state_websearch_attempts: str):
    self.state_websearch_attempts = state_websearch_attempts
def judge_ats_research_agent_instructions(run_context: RunContextWrapper[JudgeAtsResearchAgentContext], _agent: Agent[JudgeAtsResearchAgentContext]):
  state_websearch_attempts = run_context.context.state_websearch_attempts
  return format_judge_ats_research_prompt(state_websearch_attempts)
judge_ats_research_agent = Agent(
  name="Judge ATS Research Agent",
  instructions=judge_ats_research_agent_instructions,
  model="gpt-5-nano",
  output_type=JudgeAtsResearchAgentSchema,
  model_settings=ModelSettings(
    store=True,
    reasoning=Reasoning(
      effort="low",
      summary="auto"
    )
  )
)


ats_research_agent = Agent(
  name="ATS research agent",
  instructions=ATS_RESEARCH_AGENT_INSTRUCTIONS,
  model="gpt-5-mini",
  tools=[
    web_search_preview
  ],
  output_type=AtsResearchAgentSchema,
  model_settings=ModelSettings(
    store=True,
    reasoning=Reasoning(
      effort="medium",
      summary="auto"
    )
  )
)


class RestructureInputContext:
  def __init__(self, workflow_input_as_text: str):
    self.workflow_input_as_text = workflow_input_as_text
    
def restructure_input_instructions(run_context: RunContextWrapper[RestructureInputContext], _agent: Agent[RestructureInputContext]):
  workflow_input_as_text = run_context.context.workflow_input_as_text
  return format_restructure_input_prompt(workflow_input_as_text)
restructure_input = Agent(
  name="Restructure Input",
  instructions=restructure_input_instructions,
  model="gpt-5-mini",
  model_settings=ModelSettings(
    store=True,
    reasoning=Reasoning(
      effort="low",
      summary="auto"
    )
  )
)


leadership_values_agent = Agent(
  name="Leadership Values Agent",
  instructions=LEADERSHIP_VALUES_SUMMARY_INSTRUCTIONS,
  model="gpt-4.1-mini",
  tools=[
    web_search_preview1
  ],
  model_settings=ModelSettings(
    temperature=0.68,
    top_p=1,
    max_tokens=15359,
    store=True
  )
)


class CleanOutputAgentContext:
  def __init__(self, state_leadership_values: str, state_webresearch_output: str):
    self.state_leadership_values = state_leadership_values
    self.state_webresearch_output = state_webresearch_output
def clean_output_agent_instructions(run_context: RunContextWrapper[CleanOutputAgentContext], _agent: Agent[CleanOutputAgentContext]):
  state_leadership_values = run_context.context.state_leadership_values
  state_webresearch_output = run_context.context.state_webresearch_output
  return format_clean_output_prompt(state_leadership_values, state_webresearch_output)
clean_output_agent = Agent(
  name="Clean Output Agent",
  instructions=clean_output_agent_instructions,
  model="gpt-4.1",
  model_settings=ModelSettings(
    temperature=0.82,
    top_p=1,
    max_tokens=32032,
    store=True
  )
)


class WorkflowInput(BaseModel):
  input_as_text: str


# Main code entrypoint
async def run_workflow(workflow_input: WorkflowInput):
  with trace("Job Research"):
    state = {
      "status": False,
      "judgement_output": "Failed",
      "websearch_attempts": 0,
      "leadership_values": None,
      "webresearch_output": None,
      "atsoutput": {
        "job_title": "",
        "primary_keywords": [

        ],
        "secondary_keywords": [

        ],
        "soft_skills": [

        ],
        "certifications": [

        ],
        "recommended_resume_phrases": [

        ],
        "sources": [

        ]
      }
    }
    workflow = workflow_input.model_dump()
    conversation_history: list[TResponseInputItem] = [
      {
        "role": "user",
        "content": [
          {
            "type": "input_text",
            "text": workflow["input_as_text"]
          }
        ]
      }
    ]
    restructure_input_result_temp = await Runner.run(
      restructure_input,
      input=[
        *conversation_history
      ],
      run_config=RunConfig(trace_metadata={
        "__trace_source__": "agent-builder",
        "workflow_id": "wf_69094b31b9208190aa343ff092246f2608c5cc4a89830252"
      }),
      context=RestructureInputContext(workflow_input_as_text=workflow["input_as_text"])
    )

    conversation_history.extend([item.to_input_item() for item in restructure_input_result_temp.new_items])

    restructure_input_result = {
      "output_text": restructure_input_result_temp.final_output_as(str)
    }
    state["judgement_output"] = "failed"
    state["websearch_attempts"] = 0
    while "failed" == state["judgement_output"] and state["websearch_attempts"] < 3:
      ats_research_agent_result_temp = await Runner.run(
        ats_research_agent,
        input=[
          *conversation_history
        ],
        run_config=RunConfig(trace_metadata={
          "__trace_source__": "agent-builder",
          "workflow_id": "wf_69094b31b9208190aa343ff092246f2608c5cc4a89830252"
        })
      )

      conversation_history.extend([item.to_input_item() for item in ats_research_agent_result_temp.new_items])

      ats_research_agent_result = {
        "output_text": ats_research_agent_result_temp.final_output.json(),
        "output_parsed": ats_research_agent_result_temp.final_output.model_dump()
      }
      state["webresearch_output"] = ats_research_agent_result["output_text"]
      judge_ats_research_agent_result_temp = await Runner.run(
        judge_ats_research_agent,
        input=[
          *conversation_history
        ],
        run_config=RunConfig(trace_metadata={
          "__trace_source__": "agent-builder",
          "workflow_id": "wf_69094b31b9208190aa343ff092246f2608c5cc4a89830252"
        }),
        context=JudgeAtsResearchAgentContext(state_websearch_attempts=state["websearch_attempts"])
      )

      conversation_history.extend([item.to_input_item() for item in judge_ats_research_agent_result_temp.new_items])

      judge_ats_research_agent_result = {
        "output_text": judge_ats_research_agent_result_temp.final_output.json(),
        "output_parsed": judge_ats_research_agent_result_temp.final_output.model_dump()
      }
      state["websearch_attempts"] = judge_ats_research_agent_result["output_parsed"]["websearch_tries"]
      state["judgement_output"] = judge_ats_research_agent_result["output_parsed"]["status"]
    leadership_values_agent_result_temp = await Runner.run(
      leadership_values_agent,
      input=[
        *conversation_history
      ],
      run_config=RunConfig(trace_metadata={
        "__trace_source__": "agent-builder",
        "workflow_id": "wf_69094b31b9208190aa343ff092246f2608c5cc4a89830252"
      })
    )

    conversation_history.extend([item.to_input_item() for item in leadership_values_agent_result_temp.new_items])

    leadership_values_agent_result = {
      "output_text": leadership_values_agent_result_temp.final_output_as(str)
    }
    state["leadership_values"] = leadership_values_agent_result["output_text"]
    clean_output_agent_result_temp = await Runner.run(
      clean_output_agent,
      input=[
        *conversation_history
      ],
      run_config=RunConfig(trace_metadata={
        "__trace_source__": "agent-builder",
        "workflow_id": "wf_69094b31b9208190aa343ff092246f2608c5cc4a89830252"
      }),
      context=CleanOutputAgentContext(state_leadership_values=state["leadership_values"], state_webresearch_output=state["webresearch_output"])
    )

    conversation_history.extend([item.to_input_item() for item in clean_output_agent_result_temp.new_items])

    clean_output_agent_result = {
      "output_text": clean_output_agent_result_temp.final_output_as(str)
    }
    
    # Return the final clean output text
    return clean_output_agent_result["output_text"]
