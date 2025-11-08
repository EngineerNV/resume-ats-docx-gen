from agents import WebSearchTool, Agent, ModelSettings, TResponseInputItem, Runner, RunConfig, trace
from pydantic import BaseModel, Field
from openai.types.shared.reasoning import Reasoning

from ..prompts import (
    IMPROVE_CURRENT_RESUME_INSTRUCTIONS,
    JUDGE_FOR_IMPROVEMENT_INSTRUCTIONS,
    PERSONAL_STATEMENT_INSTRUCTIONS,
    RESUME_FLOW_MANAGER_INSTRUCTIONS,
    RESUME_JSON_BUILDER_INSTRUCTIONS,
    TUNE_RESUME_TO_JD_INSTRUCTIONS,
)

# Tool definitions
web_search_preview = WebSearchTool(
  search_context_size="medium",
  user_location={
    "country": "US",
    "type": "approximate"
  }
)
class ResumeFlowManagerSchema(BaseModel):
  output: bool


class JudgeForImprovementSchema__Header(BaseModel):
  name: str
  email: str
  location: str
  linkedin: str
  github: str


class JudgeForImprovementSchema__Skills(BaseModel):
  programming_languages: list[str] = Field(alias="Programming Languages")
  technologies: list[str] = Field(alias="Technologies")
  tools: list[str] = Field(alias="Tools")
  
  class Config:
    populate_by_name = True


class JudgeForImprovementSchema__ExperienceItem(BaseModel):
  role: str
  company: str
  dates: str
  location: str
  bullets: list[str]


class JudgeForImprovementSchema__EducationItem(BaseModel):
  degree: str
  institution: str
  dates: str
  location: str
  gpa: str


class JudgeForImprovementSchema(BaseModel):
  header: JudgeForImprovementSchema__Header
  professional_summary: str
  skills: JudgeForImprovementSchema__Skills
  experience: list[JudgeForImprovementSchema__ExperienceItem]
  education: list[JudgeForImprovementSchema__EducationItem]
  awards: list[str]


class ResumeJsonBuilderAgentSchema__Header(BaseModel):
  name: str
  email: str
  location: str
  linkedin: str
  github: str


class ResumeJsonBuilderAgentSchema__Skills(BaseModel):
  programming_languages: list[str] = Field(alias="Programming Languages")
  technologies: list[str] = Field(alias="Technologies")
  tools: list[str] = Field(alias="Tools")
  
  class Config:
    populate_by_name = True


class ResumeJsonBuilderAgentSchema__ExperienceItem(BaseModel):
  role: str
  company: str
  dates: str
  location: str
  bullets: list[str]


class ResumeJsonBuilderAgentSchema__EducationItem(BaseModel):
  degree: str
  institution: str
  dates: str
  location: str
  gpa: str


class ResumeJsonBuilderAgentSchema(BaseModel):
  header: ResumeJsonBuilderAgentSchema__Header
  professional_summary: str
  skills: ResumeJsonBuilderAgentSchema__Skills
  experience: list[ResumeJsonBuilderAgentSchema__ExperienceItem]
  education: list[ResumeJsonBuilderAgentSchema__EducationItem]
  awards: list[str]


resume_flow_manager = Agent(
  name="Resume Flow Manager",
  instructions=RESUME_FLOW_MANAGER_INSTRUCTIONS,
  model="gpt-5-mini",
  output_type=ResumeFlowManagerSchema,
  model_settings=ModelSettings(
    top_p=1,
    max_tokens=50000,
    store=True
  )
)
# NOTE: This agent now exists mostly for backwards compatibility with the
# original Agent Builder workflow. The FastAPI layer + ResumeOrchestrator
# already decide whether we're in "job" vs "resume" mode before invoking this
# workflow, so the boolean output is effectively informational today.


tune_resume_to_jd_agent = Agent(
  name="Tune Resume to JD Agent",
  instructions=TUNE_RESUME_TO_JD_INSTRUCTIONS,
  model="o4-mini",
  tools=[
    web_search_preview
  ],
  model_settings=ModelSettings(
    store=True,
    reasoning=Reasoning(
      effort="medium",
      summary="detailed"
    )
  )
)


improve_current_resume_agent = Agent(
  name="Improve Current Resume Agent",
  instructions=IMPROVE_CURRENT_RESUME_INSTRUCTIONS,
  model="o4-mini",
  model_settings=ModelSettings(
    store=True,
    reasoning=Reasoning(
      effort="medium",
      summary="auto"
    )
  )
)


judge_for_improvement = Agent(
  name="Judge for Improvement",
  instructions=JUDGE_FOR_IMPROVEMENT_INSTRUCTIONS,
  model="gpt-4.1",
  output_type=JudgeForImprovementSchema,
  model_settings=ModelSettings(
    temperature=0.6,
    top_p=1,
    max_tokens=32768,
    store=True
  )
)


personal_statement_agent = Agent(
  name="Personal  Statement Agent",
  instructions=PERSONAL_STATEMENT_INSTRUCTIONS,
  model="gpt-4.1",
  model_settings=ModelSettings(
    temperature=0.7,
    top_p=1,
    max_tokens=9880,
    store=True
  )
)


resume_json_builder_agent = Agent(
  name="Resume JSON Builder Agent",
  instructions=RESUME_JSON_BUILDER_INSTRUCTIONS,
  model="gpt-4.1-mini",
  output_type=ResumeJsonBuilderAgentSchema,
  model_settings=ModelSettings(
    temperature=0.65,
    top_p=1,
    max_tokens=32768,
    store=True
  )
)


class WorkflowInput(BaseModel):
  input_as_text: str


# Main code entrypoint
async def run_workflow(workflow_input: WorkflowInput):
  with trace("Resume JSON Creator"):
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
    resume_flow_manager_result_temp = await Runner.run(
      resume_flow_manager,
      input=[
        *conversation_history
      ],
      run_config=RunConfig(trace_metadata={
        "__trace_source__": "agent-builder",
        "workflow_id": "wf_690a83b0b64481909665ac147c6b534904a7600661710e25"
      })
    )

    conversation_history.extend([item.to_input_item() for item in resume_flow_manager_result_temp.new_items])

    resume_flow_manager_result = resume_flow_manager_result_temp.final_output.model_dump()
    
    if resume_flow_manager_result["output"] == True:
      tune_resume_to_jd_agent_result_temp = await Runner.run(
        tune_resume_to_jd_agent,
        input=[
          *conversation_history
        ],
        run_config=RunConfig(trace_metadata={
          "__trace_source__": "agent-builder",
          "workflow_id": "wf_690a83b0b64481909665ac147c6b534904a7600661710e25"
        })
      )

      conversation_history.extend([item.to_input_item() for item in tune_resume_to_jd_agent_result_temp.new_items])

      personal_statement_agent_result_temp = await Runner.run(
        personal_statement_agent,
        input=[
          *conversation_history
        ],
        run_config=RunConfig(trace_metadata={
          "__trace_source__": "agent-builder",
          "workflow_id": "wf_690a83b0b64481909665ac147c6b534904a7600661710e25"
        })
      )

      conversation_history.extend([item.to_input_item() for item in personal_statement_agent_result_temp.new_items])

      resume_json_builder_agent_result_temp = await Runner.run(
        resume_json_builder_agent,
        input=[
          *conversation_history
        ],
        run_config=RunConfig(trace_metadata={
          "__trace_source__": "agent-builder",
          "workflow_id": "wf_690a83b0b64481909665ac147c6b534904a7600661710e25"
        })
      )

      conversation_history.extend([item.to_input_item() for item in resume_json_builder_agent_result_temp.new_items])

      judge_for_improvement_result_temp = await Runner.run(
        judge_for_improvement,
        input=[
          *conversation_history
        ],
        run_config=RunConfig(trace_metadata={
          "__trace_source__": "agent-builder",
          "workflow_id": "wf_690a83b0b64481909665ac147c6b534904a7600661710e25"
        })
      )

      conversation_history.extend([item.to_input_item() for item in judge_for_improvement_result_temp.new_items])

      judge_for_improvement_result = {
        "output_text": judge_for_improvement_result_temp.final_output.json(),
        "output_parsed": judge_for_improvement_result_temp.final_output.model_dump()
      }
    else:
      improve_current_resume_agent_result_temp = await Runner.run(
        improve_current_resume_agent,
        input=[
          *conversation_history
        ],
        run_config=RunConfig(trace_metadata={
          "__trace_source__": "agent-builder",
          "workflow_id": "wf_690a83b0b64481909665ac147c6b534904a7600661710e25"
        })
      )

      conversation_history.extend([item.to_input_item() for item in improve_current_resume_agent_result_temp.new_items])

      personal_statement_agent_result_temp = await Runner.run(
        personal_statement_agent,
        input=[
          *conversation_history
        ],
        run_config=RunConfig(trace_metadata={
          "__trace_source__": "agent-builder",
          "workflow_id": "wf_690a83b0b64481909665ac147c6b534904a7600661710e25"
        })
      )

      conversation_history.extend([item.to_input_item() for item in personal_statement_agent_result_temp.new_items])

      resume_json_builder_agent_result_temp = await Runner.run(
        resume_json_builder_agent,
        input=[
          *conversation_history
        ],
        run_config=RunConfig(trace_metadata={
          "__trace_source__": "agent-builder",
          "workflow_id": "wf_690a83b0b64481909665ac147c6b534904a7600661710e25"
        })
      )

      conversation_history.extend([item.to_input_item() for item in resume_json_builder_agent_result_temp.new_items])

      judge_for_improvement_result_temp = await Runner.run(
        judge_for_improvement,
        input=[
          *conversation_history
        ],
        run_config=RunConfig(trace_metadata={
          "__trace_source__": "agent-builder",
          "workflow_id": "wf_690a83b0b64481909665ac147c6b534904a7600661710e25"
        })
      )

      conversation_history.extend([item.to_input_item() for item in judge_for_improvement_result_temp.new_items])

      judge_for_improvement_result = {
        "output_text": judge_for_improvement_result_temp.final_output.json(),
        "output_parsed": judge_for_improvement_result_temp.final_output.model_dump()
      }

    # Return the final optimized resume JSON
    return judge_for_improvement_result["output_parsed"]
