from agents import Agent, ModelSettings, TResponseInputItem, Runner, RunConfig, trace
from pydantic import BaseModel

from ..prompts import RESUME_EXTRACTION_INSTRUCTIONS

resume_extraction_agent = Agent(
  name="Resume Extraction Agent",
  instructions=RESUME_EXTRACTION_INSTRUCTIONS,
  model="gpt-4.1",
  model_settings=ModelSettings(
    temperature=1,
    top_p=1,
    max_tokens=30027,
    store=True
  )
)


class WorkflowInput(BaseModel):
  input_as_text: str


# Main code entrypoint
async def run_workflow(workflow_input: WorkflowInput):
  with trace("Resume/Context Extractor"):
    state = {

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
    resume_extraction_agent_result_temp = await Runner.run(
      resume_extraction_agent,
      input=[
        *conversation_history
      ],
      run_config=RunConfig(trace_metadata={
        "__trace_source__": "agent-builder",
        "workflow_id": "wf_6909c4b9e4d481908f55276e5f3af0d600153d3685400f6a"
      })
    )

    conversation_history.extend([item.to_input_item() for item in resume_extraction_agent_result_temp.new_items])

    resume_extraction_agent_result = {
      "output_text": resume_extraction_agent_result_temp.final_output_as(str)
    }
    # Return the extracted resume text (string). The orchestrator will parse or include
    # this as needed. Use a plain string to avoid coupling to a specific schema here.
    return resume_extraction_agent_result["output_text"]