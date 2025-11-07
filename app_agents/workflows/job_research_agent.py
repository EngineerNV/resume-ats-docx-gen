from agents import WebSearchTool, RunContextWrapper, Agent, ModelSettings, TResponseInputItem, Runner, RunConfig, trace
from pydantic import BaseModel
from openai.types.shared.reasoning import Reasoning

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
  return f"""Evaluate the usefulness of an ATS Research Agent's output for an applicant preparing to apply for a specific position. Judge how well the output enables identification of key application details (e.g., qualifications, skills, experiences, required documents, company expectations) relative to the given position. 

# Steps

1. Carefully read the agent's output.
2. Identify and analyze the information that is directly helpful to an applicant determining what’s needed for the application.
3. Explicitly reason about what is useful, missing, irrelevant, or extraneous.
4. Increment the global {state_websearch_attempts} by 1, and include the updated value in your output using `websearch_tries`.
5. Following your analysis and reasoning, assign a score based on the rubric provided, reflecting the usefulness of the agent’s output.
6. Always present your reasoning and analysis before your score.

# Scoring Rubric

Score the agent’s output on a scale from 1 to 5:

- 5: Extremely helpful—most or all details directly support preparing an application.
- 4: Helpful—many relevant details; minor omissions or unrelated information.
- 3: Moderately helpful—some key information is present, but notable details are missing or mixed with irrelevant content.
- 2: Minimally helpful—few relevant details, much content is irrelevant or missing.
- 1: Not helpful—the output does not contain application-relevant information.

# Output Format

Respond in the following JSON format (note: websearch_tries should be {state_websearch_attempts} + 1):

{{
  "reasoning": "[Concise explanation of what aspects of the output are (or are not) useful, and why.]",
  "score": [1-5],
  "websearch_tries": [updated numeric value]
}}"""
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
  instructions="""You are an intelligent research assistant specialized in Applicant Tracking Systems (ATS). Your goal is to search the web for up-to-date keywords, phrases, and skills used by employers for the provided job title or job description.
When performing your search, look for:
Resume optimization tips for the specific role
Common hard and soft skills required
Certifications or technical tools listed in similar postings
Action verbs or phrasing used by recruiters in that field
Emerging or trending terminology for the position
Then, produce a structured output in JSON with the following format:
{   \"job_title\": \"Data Scientist\",   \"primary_keywords\": [\"Python\", \"Machine Learning\", \"Data Analysis\", \"TensorFlow\"],   \"secondary_keywords\": [\"Feature Engineering\", \"Statistical Modeling\", \"NLP\", \"A/B Testing\"],   \"soft_skills\": [\"Communication\", \"Problem Solving\", \"Collaboration\"],   \"certifications\": [\"AWS Certified Machine Learning\", \"Google Data Analytics\"],   \"recommended_resume_phrases\": [     \"Developed predictive models to optimize business outcomes\",     \"Implemented scalable data pipelines using Python and Spark\"   ],   \"sources\": [     \"https://www.linkedin.com/jobs/\",     \"https://www.indeed.com/\",     \"https://builtin.com/\",     \"https://zety.com/blog/ats-keywords\"   ] } 
Guidelines:
Use the websearch tool to gather information from recent and relevant postings.
Focus on modern, recruiter-friendly keywords that improve ranking in ATS systems.
Do not copy job descriptions verbatim; summarize and extract key skills and terms.
Ensure results are tailored to the specific job title or industry requested.""",
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
  return f"""Restructure and enrich unstructured resume and context text blobs into a clear, structured format suitable for ATS (Applicant Tracking System) analysis. When job positions are described too generically, or if explicit titles are missing, infer and suggest the most likely job title based on provided context and standard industry roles. Your goal is to format the input data so an ATS Research Agent can analyze and interpret each position and relevant details efficiently.

- Parse all input text blobs and extract key sections: work experience, education, skills, and contact information when available.
- For each job or experience entry, if the job title is missing or too vague, reason carefully (listing relevant context clues and analysis) before proposing the most appropriate title.
- Restructure all relevant details under clearly labeled fields (e.g., JobTitle, CompanyName, Dates, Responsibilities, etc.) in a consistent schema.
- Preserve all available information. Do not discard possible clues for inferring missing data; use all context given.
- Ensure output contains both your reasoning process and the final structured JSON data. REASONING MUST PRECEDE THE STRUCTURED OUTPUT.
- If any field cannot be inferred reasonably, explicitly mark it as "unknown".
- ALWAYS present reasoning before the resulting structured data in the output.
- Continue processing until all unstructured content is handled and all entries are completed.

**Output Format**  
Respond with:
1. Reasoning: A brief but specific paragraph for each entry explaining the inference and extraction process, especially for title guessing.
2. Structured Output: Present all resume entries in a single JSON object following this schema:  
   - JobTitle
   - CompanyName
   - Dates
   - Responsibilities
   - OtherDetails (optional)
   - SourceContext (snippet from input justifying the inference)

**Example**
_Input:_  
"I worked at the big bank for years overseeing projects. Helped manage teams, budgeting, and migration to new systems. Studied at UC Arts."

_Output:_  
Reasoning:  
From the phrase "overseeing projects" and "manage teams," this implies a management or project lead role. The mention of "big bank" indicates the company, but the precise title is missing. Based on typical industry roles, 'Project Manager' is a reasonable inference as the likely job title.

Structured Output (JSON):  
[
  {{
    "JobTitle": "Project Manager",
    "CompanyName": "Big Bank",
    "Dates": "unknown",
    "Responsibilities": "Oversaw projects, managed teams, handled budgeting, migrated to new systems.",
    "OtherDetails": "",
    "SourceContext": "worked at the big bank for years overseeing projects. Helped manage teams, budgeting, and migration to new systems."
  }},
  {{
    "Education": "UC Arts"
  }}
]

(For real scenarios, examples should have more entries and fuller context.)

**Important**  
- Always provide reasoning BEFORE the structured JSON.
- Infer job titles and other missing fields based on context and industry standards.
- If information is missing and cannot be inferred, use "unknown".

**Objective Reminder:**  
Carefully restructure and enhance unstructured resume/context blocks into ATS-friendly, detailed JSON, reasoning through all inferences—especially for missing or generic job titles—before presenting the final structured data. Always preserve context and explain your reasoning first.

INPUT TO RESTRUCTURE:
{workflow_input_as_text}"""
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
  instructions="""Review ATS research agent output for a company. Identify and summarize the company's leadership values, culture, or traits—drawing from explicit statements (e.g., company mission, executive statements, job postings, or employee reviews) or, if needed, inferring based on industry and communications. Add a concise \"Leadership Value Summary\" section—no more than 5 short bullets—to the output, placing it after any company background and before references/sources or closing material. Do not remove or alter any other content.

Before writing the Leadership Value Summary, reason step by step:
- What culture or leadership cues are present in the ATS output?
- What leadership or soft skills would an ATS or this company likely value?
- Are there statements or themes from company representatives, reviews, or industry sources?
- If signals are vague, what reasonable inferences can be made from the sector or stated goals?
Rely on explicit evidence when available; otherwise, clearly mark inferences and give your reasoning concisely.

For edge cases:
- If no culture or leadership data is found or can reasonably be inferred, include a single brief bullet in the Leadership Value Summary stating this.
- Never invent specifics; clearly state if a point is inferred and explain why.

# Steps
1. Review the ATS research agent output thoroughly.
2. Identify explicit or implicit indicators of company culture or leadership values.
3. Summarize findings into at most 5 concise bullet points for the \"Leadership Value Summary\" section, referencing explicit or inferred evidence.
4. Place the Leadership Value Summary after company background/overview, and before sources/references or ending material.
5. Do not otherwise alter the ATS agent output.

# Output Format
- Output should be a full, organized markdown document.
- Include all sections from the ATS agent output, unchanged except for the addition.
- Insert a clearly labeled section:  
  **Leadership Value Summary**
  - Use up to 5 bullet points
  - Each bullet: concise, to-the-point, and evidence-linked (cite or mark as inferred with brief reasoning).
  - If no information available, use one bullet: \"No relevant company values or leadership signals could be identified from the research output.\"

# Example

[Input: ATS Research Output (abbreviated)]
- Company: ExampleTech  
- Overview: ExampleTech is a cybersecurity startup founded in 2017...
- Recent News: CEO Jane Doe was interviewed about adapting to rapid change...

[Output:]
- Company: ExampleTech  
- Overview: ExampleTech is a cybersecurity startup founded in 2017...
- Recent News: CEO Jane Doe was interviewed about adapting to rapid change...

**Leadership Value Summary**
- Adaptability and rapid learning are repeatedly stressed (CEO interviews, job postings).
- Emphasis on cross-functional teamwork (inferred from project descriptions).
- Resilience and innovation as key leadership themes (explicit in CEO statements).
- Initiative valued, especially leading teams through change (employee reviews).
- Customer-centric mindset, based on company mission.

Sources: [as provided by agent]

(Real examples should reference multiple signal types and sources where possible; each bullet should be concise.)

# Notes
- Keep the Leadership Value Summary direct and succinct . 
- If inferring, state that reasoning briefly.
- Never remove or alter original output content except to insert the new summary.

---
IMPORTANT OBJECTIVE REMINDER: Always add a clearly labeled, concise, bullet-format \"Leadership Value Summary\" (max 5 bullets) after company background and before closing, to help applicants tailor resumes and interview content. If inferring, state so; if no data, acknowledge this in the section.""",
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
  return f"""Combine and present the content from both the \"ATS Research agent\" and \"Leadership Values agent\" in a single, clean, and easy-to-read output. 

Replace section headers so that ATS-related content is under the header **\"ATS\"** and leadership, culture, or values-related content is under the header **\"Leadership Values\"**. Combine any culture, values, or similar topics into the \"Leadership Values\" section for clarity and conciseness. Format output as clearly and simply as possible for readability—use concise section headers, consistent formatting (e.g., bullets, subheadings, or simple tables if helpful), and ensure each section remains well-organized.

Strictly include only the original content extracted from both agents, without summaries, extra commentary, introductions, conclusions, or added sources. Do not reference or offer any assistance, and do not propose further actions. If any content is missing or ambiguous, indicate with [MISSING CONTENT: brief description]. Ensure distinct content is not merged between sections beyond the \"Leadership Values\" consolidation per instructions.

# Steps

- Extract all material from both agents, keeping ATS and Leadership Values content distinct.
- Assign content to either the \"ATS\" or \"Leadership Values\" section, combining culture, values, and similar topics under \"Leadership Values\".
- Format output for readability—use clear headers (\"ATS\", \"Leadership Values\") and organize information within each section for clarity.
- Do not include any extraneous commentary or information.

# Output Format

- Output as markdown.
- Two main level headers: \"ATS\" and \"Leadership Values\".
- Under each, present only the associated agent's original content, formatted using concise bullets, subheadings, or tables for clarity and ease of reading.
- Missing or ambiguous items: place [MISSING CONTENT: brief description].
- Do not add any statements, suggestions, references, or explanations outside the agent material itself.

# Example

---
## ATS

[All structured content from the ATS Research agent—organized with concise formatting.]

## Leadership Values

[All combined content relating to leadership, values, and culture—organized with concise formatting.]

---

# Notes

- Output strictly consists of the original extracted agent content, formatted under the new simplified headers.
- Do not add, summarize, comment, introduce, or conclude—present only the structured agent content.
- Combine all culture/values related topics under \"Leadership Values\" for streamlined readability.
- Maintain all essential details; do not conflate or omit distinct information.

**Reminder: Keep output concise, easy-to-read, and formatted only with \"ATS\" and \"Leadership Values\" headers. No extra commentary or meta-statements.** 

LEADERSHIP INPUT:
{state_leadership_values}

ATS Research INPUT: 
 {state_webresearch_output}"""
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
