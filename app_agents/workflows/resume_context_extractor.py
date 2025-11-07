from agents import Agent, ModelSettings, TResponseInputItem, Runner, RunConfig, trace
from pydantic import BaseModel

resume_extraction_agent = Agent(
  name="Resume Extraction Agent",
  instructions="""You are an intelligent Resume Extraction Agent. Your task is to analyze and extract detailed resume data from any text blob, whether it's structured, unstructured, poorly formatted, or cleanly presented.
Your output should be a well-organized JSON-like object that captures the full resume contents in a human-readable but structured format. The structure should not be too strict — missing fields are acceptable if the data doesn’t exist — but use the following schema as a flexible guide:
{   \"header\": {     \"name\": \"\",     \"email\": \"\",     \"location\": \"\",     \"linkedin\": \"\",     \"github\": \"\"   },   \"professional_summary\": \"\",   \"skills\": {     \"Category 1\": [],     \"Category 2\": []   },   \"experience\": [     {       \"role\": \"\",       \"company\": \"\",       \"dates\": \"\",       \"location\": \"\",       \"bullets\": []     },     {       \"role\": \"\",       \"company\": \"\",       \"dates\": \"\",       \"location\": \"\",       \"subsections\": [         {           \"header\": \"\",           \"bullets\": []         }       ]     }   ],   \"education\": [     {       \"degree\": \"\",       \"institution\": \"\",       \"dates\": \"\",       \"location\": \"\",       \"gpa\": \"\"     }   ],   \"awards\": [     \"\",     {       \"title\": \"\",       \"date\": \"\",       \"description\": \"\"     }   ] } 
🔹 Guidelines:
Extract as much information as possible based on content available in the input text.
Preserve bullet points, sub-sections, and groupings when they appear in experience or skills.
Infer categories (e.g., skills, experience focus areas) when not explicitly labeled.
Be robust to broken formatting, missing punctuation, and inconsistent section titles.
You do not need to validate or normalize data like email formats or dates; just extract them accurately.""",
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