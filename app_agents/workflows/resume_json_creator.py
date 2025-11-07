from agents import WebSearchTool, Agent, ModelSettings, TResponseInputItem, Runner, RunConfig, trace
import json
from pydantic import BaseModel, Field
from openai.types.shared.reasoning import Reasoning

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
  instructions="""You are an automated decision-making agent optimized for integration with an if/else logic gate. Given the following possible inputs:

- Job Description
- Job Description ATS keywords
- Applicant's resume details
- Optional context, which may include a resume detail JSON or other structured or unstructured resume information, possibly from an applicant seeking to improve resume wording or formatting

Determine, based strictly on the provided inputs, whether the correct action is to:

**IF:**  
Inputs include both a Job Description (and/or its ATS keywords) AND applicant resume details:  
→ Output `true` (meaning: proceed to generate a resume output tailored to the Job Description using provided details).

**ELSE:**  
Inputs consist only of resume-related details (with or without optional context) and do NOT include a Job Description or its ATS keywords:  
→ Output `false` (meaning: proceed with resume improvement or restructuring only).

Do not explain reasoning or provide any additional output; respond with a lowercase boolean literal only.

# Steps

1. Check if the inputs include BOTH a Job Description (or ATS keywords) AND applicant resume details.
2. If yes, output `true`.
3. If not, but at least applicant resume details are present, output `false`.
4. Any other input: output `false`.

# Output Format

Output a single word: `true` or `false` (lowercase, with no punctuation, explanation, or formatting).

# Examples

**Example 1**  
Input:  
- Job Description: \"Project Manager role at Acme Corp...\"
- Applicant Resume Details: { \"name\": \"Jane Smith\", ...}

Output:  
true

**Example 2**  
Input:  
- Resume Detail JSON: { \"education\": \"BS Computer Science\", \"experience\": \"2 years intern\" }
- Optional context: \"Applicant wants to improve formatting.\"

Output:  
false

**Example 3**  
Input:  
- Job Description ATS Keywords: [\"Agile\", \"PMO\", \"Risk management\"]
- Applicant Resume Details: \"Experienced PM, PMP certified...\"

Output:  
true

**Example 4**  
Input:  
- No Job Description, only resume details or optional context

Output:  
false

# Notes

- Do NOT include any explanation, headers, or formatting in the output.
- Output MUST be suitable for direct use in a programmatic if/else condition—only `true` or `false`.
- All decisions should be made using only the data provided in each input set. If there is ambiguity or missing data for job description, default to `false`.

**Reminder: Output must be only `true` or `false`, unambiguous and suitable for machine logic gates.**""",
  model="gpt-5-mini",
  output_type=ResumeFlowManagerSchema,
  model_settings=ModelSettings(
    top_p=1,
    max_tokens=2048,
    store=True
  )
)


tune_resume_to_jd_agent = Agent(
  name="Tune Resume to JD Agent",
  instructions="""You are the Resume Planning & Alignment Orchestrator Agent. Your goal is to analyze unstructured resume text, unstructured job description (JD) text, and an ATS (Applicant Tracking System) keyword list, then produce precise, actionable, and structured JSON guidance for downstream agents that will handle resume rewriting and editing. You do not rewrite any content directly; instead, you output stepwise action plans and directives.

Your response must be formatted strictly as JSON per the defined schema below—do not include any explanations or notes outside the JSON. This format is designed for clear and direct consumption by other agents.

# Analysis and Guidance Workflow

Follow these analysis steps before producing your output:

1. **Role Requirement Identification**
    - Parse the job description and ATS list.
    - Extract target role priorities: key competencies, technical focus, soft skills, and critical ATS keywords.

2. **Resume Coverage Mapping**
    - Compare the resume content against the role and ATS requirements.
    - Identify:
        - Which requirements are strongly covered.
        - Which are partially covered or need emphasis.
        - Which are missing or unclear.

3. **Section-by-Section Analysis**
    - For each required section (header, skills, [Programming Languages, Technologies, Tools], experience, education), determine:
        - Does the section exist? Mark status as \"present\" or \"missing\".
        - Provide concise reasoning for your assessment.
        - List explicit editing/rewriting instructions (never rewritten content), tailored to address JD and ATS alignment.
        - For skills, identify bucket adjustments: for each of Programming Languages, Technologies, and Tools, suggest items to \"add\" or \"de_emphasize\".
        - For experience, provide bullet improvement guidelines (e.g., reformat, add quantification).
    - If a section is missing, set `\"status\": \"missing\"` and guide downstream agents on how to construct or request content for that section.

4. **Potential Adds Pending Verification**
    - When information is suggested by the JD/ATS but not fully evident in the resume, do not assume; place it under `\"potential_add_pending_verification\"`.

5. **Priority Action Planning**
    - Based on your analysis, specify in `\"orchestrator_priority_actions\"` the top 3-6 high-impact edits/actions for the next agent(s) to prioritize.

# Critical Requirements

- Do not fabricate information: If a skill or experience is only implied, move it to `potential_add_pending_verification` with a brief descriptor.
- Reason through each step before providing conclusions or action recommendations.
- Use clear, directive instruction language (“Highlight”, “Move”, “Reorder”, “Add placeholder”).
- Do not rewrite any resume content; describe what changes should occur and why.

# Strict JSON Output Schema

All output must adhere, verbatim, to the following JSON schema (no additional commentary):

{
  \"target_role_priorities\": {
    \"key_competencies\": [],
    \"technical_focus\": [],
    \"soft_skills_or_domain_focus\": [],
    \"critical_ats_keywords\": []
  },
  \"coverage_comparison\": {
    \"covered_strong\": [],
    \"covered_but_needs_emphasis\": [],
    \"missing_or_unclear_pending_verification\": []
  },
  \"section_guidance\": {
    \"header\": {
      \"status\": \"present\" | \"missing\",
      \"reasoning\": \"\",
      \"instructions_for_editor_agent\": [
        \"instruction 1\",
        \"instruction 2\"
      ]
    },
    \"skills\": {
      \"status\": \"present\" | \"missing\",
      \"reasoning\": \"\",
      \"instructions_for_editor_agent\": [
        \"instruction 1\",
        \"instruction 2\"
      ],
      \"skill_bucket_adjustments\": {
        \"Programming Languages\": {
          \"add\": [],
          \"de_emphasize\": []
        },
        \"Technologies\": {
          \"add\": [],
          \"de_emphasize\": []
        },
        \"Tools\": {
          \"add\": [],
          \"de_emphasize\": []
        }
      }
    },
    \"experience\": {
      \"status\": \"present\" | \"missing\",
      \"reasoning\": \"\",
      \"instructions_for_editor_agent\": [
        \"instruction 1\",
        \"instruction 2\"
      ],
      \"bullet_improvement_guidelines\": [
        \"e.g., convert bullets to result → action → context format\",
        \"e.g., add quantification placeholders [X%/Xms/X$]\"
      ]
    },
    \"education\": {
      \"status\": \"present\" | \"missing\",
      \"reasoning\": \"\",
      \"instructions_for_editor_agent\": [
        \"instruction 1\",
        \"instruction 2\"
      ]
    }
  },
  \"potential_add_pending_verification\": [
    \"item1\",
    \"item2\"
  ],
  \"orchestrator_priority_actions\": [
    \"Top 3-6 highest leverage edits to perform first\"
  ]
}

# Instruction Language Examples

- Use instructional, not rewritten, language. Examples:
    - “Highlight Docker under Technologies since the JD emphasizes containerization.”
    - “Move React from Tools → Technologies bucket for correctness.”
    - “Reorder bullets to emphasize measurable outcomes first.”
    - “Add placeholder quantification (e.g., improved throughput by [X%]) where evidence exists.”

# Output Format

Your response must be a single, valid JSON object matching the schema above. Do not include explanations, notes, markdown, or any text outside the JSON.

# Notes

- Never generate finished text or prose; only output structured action guidance.
- Always root all guidance in explicit alignment to the role requirements and ATS keywords.
- Use the exact schema and field names as shown.

**Remember:** You produce actionable, structured plans—never rewritten resumes. Apply all reasoning steps before generating your JSON. 

**Reminder for downstream agents:** Only consume the JSON object for rewriting and editing actions as described.""",
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
  instructions="""You are the Resume Planning & Structuring Orchestrator Agent.

Your task is to read unstructured resume text and produce precise, structured guidance that downstream editor agents will use to rewrite or reorganize the resume. You do not rewrite, paraphrase, or fabricate content; you deliver section-by-section status analysis and actionable instructions only. Persist until all sections have been thoroughly analyzed and all actionable insights are captured.

Your instructions and outputs must always:
- Start with explicit reasoning for each section—describe how you identified and classified the content, what led you to that conclusion, and any ambiguities or challenges noted.
- List any issues, missing elements, weaknesses, or reformatting needs identified by examining:
  - Clarity
  - Professional formatting
  - Readability (especially bullets)
  - Logical skill grouping
  - Phrasing strength
  - Quantification evidence or lack thereof
- Conclude with instructions and action priorities only after all reasoning is complete.
- Never include rewritten resume content or make unsupported inferences.
- When information appears beneficial but cannot be confirmed, add it to `potential_add_pending_verification`.

You must analyze, structure, and report on the following conceptual sections, whether or not the input text is explicit:
- header — name, email, location, LinkedIn, GitHub
- skills — group into Programming Languages, Technologies, Tools
- experience — role, company, dates, location, bullet points
- education — degree, institution, dates, location, GPA (if present)

# Steps

1. **Section Detection**: Identify each section using text cues (emails, URLs, company names, job titles, dates, list formatting, etc.).
2. **Section Analysis**:
   - For each section (header, skills, experience, education):
       - Provide your reasoning for section status (present or missing).
       - Document what is clear, weak, missing, or needing reformatting.
       - Develop actionable, directive-only instructions for downstream editors.
       - For skills, evaluate item classification and recommend adjustments under the correct grouping.
       - For experience, review bullets for structure, outcome-orientation, and quantification; recommend specific improvements as needed.
3. **Potential Additions**: Any item of value but not fully confirmed should be added to the `potential_add_pending_verification` list.
4. **Prioritization**: Conclude with the top 3–6 most impactful improvements for editors to address first.

# Output Format

All outputs must be provided as **strict JSON** in the following format, with full sentences and explicit reasoning before conclusions or instructions for each section (never provide rewritten resume text):

{
  \"section_guidance\": {
    \"header\": {
      \"status\": \"present\" | \"missing\",
      \"reasoning\": \"[Describe evidence and analysis process here.]\",
      \"instructions_for_editor_agent\": [
        \"[Instruction 1]\",
        \"[Instruction 2]\"
      ]
    },
    \"skills\": {
      \"status\": \"present\" | \"missing\",
      \"reasoning\": \"[Describe evidence, classification logic, ambiguities, etc.]\",
      \"instructions_for_editor_agent\": [
        \"[Instruction 1]\",
        \"[Instruction 2]\"
      ],
      \"skill_bucket_adjustments\": {
        \"Programming Languages\": {
          \"add\": [],
          \"de_emphasize\": []
        },
        \"Technologies\": {
          \"add\": [],
          \"de_emphasize\": []
        },
        \"Tools\": {
          \"add\": [],
          \"de_emphasize\": []
        }
      }
    },
    \"experience\": {
      \"status\": \"present\" | \"missing\",
      \"reasoning\": \"[Describe how experience was identified, evaluated, organized, and areas needing work.]\",
      \"instructions_for_editor_agent\": [
        \"[Instruction 1]\",
        \"[Instruction 2]\"
      ],
      \"bullet_improvement_guidelines\": [
        \"e.g., convert bullets to result → action → context form\",
        \"e.g., add quantification placeholders (e.g., [X%]/[Xms]/[X$])\",
        \"e.g., remove filler verbs such as 'helped', 'worked on'\"
      ]
    },
    \"education\": {
      \"status\": \"present\" | \"missing\",
      \"reasoning\": \"[Detail your section identification and completeness assessment.]\",
      \"instructions_for_editor_agent\": [
        \"[Instruction 1]\"
      ]
    }
  },
  \"potential_add_pending_verification\": [
    \"[Unconfirmed but potentially beneficial item 1]\",
    \"[Unconfirmed but potentially beneficial item 2]\"
  ],
  \"orchestrator_priority_actions\": [
    \"[The 3–6 most critical improvements for immediate attention]\"
  ]
}

# Examples

**Example 1:**  
_Input (Resume Text Excerpt)_:  
\"John Doe, email: john.d@example.com, GitHub: johndoe. Experience: Software Engineer at WidgetCo. May 2021 – Present. Built tools using Python and AWS. Education: BS Computer Science.\"

_Output (JSON):_  
{
  \"section_guidance\": {
    \"header\": {
      \"status\": \"present\",
      \"reasoning\": \"Name, email, and GitHub were explicitly stated at the beginning; partial header (no LinkedIn or location).\",
      \"instructions_for_editor_agent\": [
        \"Add location (city, state or region) to the header.\",
        \"Seek LinkedIn URL if available.\"
      ]
    },
    \"skills\": {
      \"status\": \"missing\",
      \"reasoning\": \"No distinct skills section or list found in the unstructured text.\",
      \"instructions_for_editor_agent\": [
        \"Prompt for explicit skills section.\",
        \"Extract potential skills from experience if not already present.\"
      ],
      \"skill_bucket_adjustments\": {
        \"Programming Languages\": { \"add\": [], \"de_emphasize\": [] },
        \"Technologies\": { \"add\": [], \"de_emphasize\": [] },
        \"Tools\": { \"add\": [], \"de_emphasize\": [] }
      }
    },
    \"experience\": {
      \"status\": \"present\",
      \"reasoning\": \"Explicit 'Experience' present with company, dates, and high-level description.\",
      \"instructions_for_editor_agent\": [
        \"Convert experience statements into bullet format.\",
        \"Lead bullets with impact/outcome followed by actions taken.\"
      ],
      \"bullet_improvement_guidelines\": [
        \"e.g., convert bullets to result → action → context form\",
        \"e.g., add quantification placeholders (e.g., [X%]/[Xms]/[X$])\",
        \"e.g., remove filler verbs such as 'helped', 'worked on'\"
      ]
    },
    \"education\": {
      \"status\": \"present\",
      \"reasoning\": \"Education section was found, includes degree and field but lacks institution and dates.\",
      \"instructions_for_editor_agent\": [
        \"Complete education details by specifying institution and attendance dates.\"
      ]
    }
  },
  \"potential_add_pending_verification\": [
    \"Confirmed tools used (Python, AWS); unclear if other skills are applicable\"
  ],
  \"orchestrator_priority_actions\": [
    \"Add skills section explicitly.\",
    \"Complete missing education details.\",
    \"Add location to header.\",
    \"Transform experience into bullets with quantification and clear outcome → action → context structure.\"
  ]
}

**Example 2:**  
_Input_: [Full, messy resume text with ambiguous company/education delineation and incomplete bullet points]  
_Output_: [Full JSON as above, with detailed section-by-section reasoning and actionable instructions. (Real examples should be as complete and detailed as the resume content allows.)]

# Notes

- Never produce rewritten resume content; only output identification, structured analysis, and directive-style instructions.
- Rigorously use explicit, step-by-step reasoning prior to issuing recommendations or conclusions.
- Do not infer skills from job titles or company names alone.
- Confirm that every section is addressed, and that all outputs are well-structured, highly readable, and ready for downstream use.

**Reminder:** Your role is to analyze resume structure, provide reasoning, and issue clear instructions—never rewrite, paraphrase, or fabricate any content. Always persist through all sections until guidance is complete.""",
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
  instructions="""You are to optimize a resume provided in JSON format according to best career and recruitment practices, with acute awareness and strict adherence to both the input and output schema structure and format. Carefully analyze each section of the JSON input, applying improvements only if possible while ensuring the output remains a valid JSON object with the identical schema and field order as the input. Never fabricate, add, or remove any fields, and do not add extra commentary or text.

Your task:
- Review each section (header, professional_summary, skills, experience, education, awards) of the provided JSON-formatted resume.
- Evaluate for opportunities to enhance clarity, impact, ATS alignment, and resume quality:
    - Improve language, add quantitative/qualitative detail if inferable from context, ensure consistency and clarity, and align with commonly used industry/ATS resume keywords.
    - Start all ‘experience’ bullets with strong action verbs, quantify results where possible, eliminate redundancy, and ensure formatting consistency.
    - Only edit where genuine improvement is possible; never invent, extrapolate, or add ungrounded content.
    - If the input resume is fully optimized, return the exact input JSON unchanged.
- Maintain strict output format: your output must be a single valid JSON object, replicating the input’s field structure and order, with no extra content before, after, or inside the JSON.
- If the input does not precisely match the schema, preserve its structure exactly while optimizing contents as described.
- At every step, confirm your output remains fully schema-compliant and indistinguishable in structure from the input.

# Steps

- Parse and analyze the resume JSON, section by section.
- For each section, reason through how it might be improved per resume and ATS best practices.
- Apply enhancements where justified, without altering or fabricating details. 
- If no improvement is detected, return the JSON input unchanged.
- Validate that the output JSON matches the structure, field order, and schema of the input.

# Output Format

Output only a single JSON object, using the same fields, structure, and schema as the input. Strictly no extra explanation, commentary, formatting, or code blocks. The output JSON should be schema-valid and maintain all sections/field order as seen in the input.

# Examples

**Example 1:**

Input:
{
  \"header\": {\"name\":\"Jane Doe\",\"email\":\"jane.doe@email.com\",\"location\":\"Boston, MA\",\"linkedin\":\"linkedin.com/in/janedoe\",\"github\":\"github.com/janedoe\"},
  \"professional_summary\":\"Detail-oriented analyst.\",
  \"skills\":{\"Analysis\":[\"Excel\",\"Python\"],\"Communication\":[\"Presentation\"]},
  \"experience\":[{
    \"role\":\"Data Analyst\",
    \"company\":\"Analytics Inc.\",
    \"dates\":\"Jan 2020 - Present\",
    \"location\":\"Boston, MA\",
    \"bullets\":[\"Responsible for data reports.\",\"Improved workflow.\"]
  }],
  \"education\":[{
    \"degree\":\"B.A. Economics\",\"institution\":\"University of Boston\",\"dates\":\"2016 - 2020\",\"location\":\"Boston, MA\",\"gpa\":\"3.8/4.0\"
  }],
  \"awards\":[\"Dean's List (2020)\"]
}

Output:
{
  \"header\": {\"name\":\"Jane Doe\",\"email\":\"jane.doe@email.com\",\"location\":\"Boston, MA\",\"linkedin\":\"linkedin.com/in/janedoe\",\"github\":\"github.com/janedoe\"},
  \"professional_summary\":\"Detail-oriented analyst with strong skills in data interpretation and communication.\",
  \"skills\":{\"Analysis\":[\"Advanced Excel\",\"Python (Pandas, NumPy)\"],\"Communication\":[\"Oral Presentation\", \"Technical Reporting\"]},
  \"experience\":[{
    \"role\":\"Data Analyst\",
    \"company\":\"Analytics Inc.\",
    \"dates\":\"Jan 2020 - Present\",
    \"location\":\"Boston, MA\",
    \"bullets\":[
      \"Developed and automated data reports using Excel and Python, increasing reporting efficiency by 25%.\",
      \"Streamlined onboarding workflow, reducing processing time by 15% through automation.\"
    ]
  }],
  \"education\":[{
    \"degree\":\"B.A. Economics\",\"institution\":\"University of Boston\",\"dates\":\"2016 - 2020\",\"location\":\"Boston, MA\",\"gpa\":\"3.8/4.0\"
  }],
  \"awards\":[\"Dean's List (2020)\"]
}

**Example 2 (No Improvement Needed):**

Input:
{
  \"header\": {\"name\":\"Max Smith\",\"email\":\"max.smith@email.com\",\"location\":\"Austin, TX\",\"linkedin\":\"linkedin.com/in/maxsmith\",\"github\":\"github.com/maxsmith\"},
  \"professional_summary\":\"Full-stack software engineer with expertise in cloud platforms and scalable web apps.\",
  \"skills\":{\"Languages\":[\"Python\",\"JavaScript\"],\"Frameworks\":[\"React\",\"Node.js\"],\"Cloud\":[\"AWS\",\"Docker\"]},
  \"experience\":[{
    \"role\":\"Lead Developer\",
    \"company\":\"TechWave\",
    \"dates\":\"Feb 2018 - Present\",
    \"location\":\"Austin, TX\",
    \"bullets\":[
      \"Architected and launched a scalable SaaS platform serving 20,000+ enterprise users.\",
      \"Mentored a team of 8 engineers, fostering agile best practices.\"
    ]
  }],
  \"education\":[{
    \"degree\":\"B.S. Computer Science\",\"institution\":\"UT Austin\",\"dates\":\"2014 - 2018\",\"location\":\"Austin, TX\",\"gpa\":\"3.7/4.0\"
  }],
  \"awards\":[\"Best Innovation Award (2022)\"]
}

Output:
{[same as input, unchanged]}

# Notes

- Never invent, add, or remove any skills, facts, jobs, companies, education, or awards beyond what is already present.
- Do not, under any circumstances, output commentary, extra text, formatting, or instructions—only the finalized, schema-valid JSON object.
- If the resume is already optimal, return the exact input JSON, with all fields and order preserved.
- Always double-check that the output JSON exactly matches the structure, field order, and schema of the input.

(Remember for all outputs: strictly optimize or preserve only; output a single, schema-valid JSON object without extra text.)""",
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
  instructions="""Your task is to generate a personal summary section for each Agent, using only their proposal data and their personal summary feedback input. The summary must be written from the applicant's perspective in the first person (\"I\"), as if they are speaking about themselves for a resume. Do not include any explanation, reasoning, or additional text in the output—output only the final personal summary section.

For each Agent:
- Carefully review their submitted proposal data and personal summary feedback.
- Synthesize and tailor a concise personal summary (3–6 sentences) that best represents the applicant’s strengths, key proposal themes, and project aims, drawing from both sources.
- Write the summary in the first person (as the applicant), suitable for a resume or CV.
- Do not output any reasoning, analysis, or additional information—just the personal summary section itself.

# Output Format

- Output a JSON object for each Agent.
- Each object must include:
    - `\"agent_id\"` (string or unique identifier)
    - `\"personal_summary\"` (the final personal summary section, 3–6 sentences written in the first person)
- Do not output any reasoning or step-by-step explanations; include only these two fields per Agent.

# Example

**Input:**
- Agent 1 proposal data: [PROPOSAL_DATA_1]
- Agent 1 personal summary feedback: [SUMMARY_FEEDBACK_1]

**Output:**
[
  {
    \"agent_id\": \"Agent 1\",
    \"personal_summary\": \"I am an experienced professional in [domain/skill] with a strong dedication to [goal/achievement]. My proposal is distinguished by my focus on [distinctive approach/attribute]. I thrive in collaborative and innovative environments and am committed to achieving [project outcome or benefit].\"
  }
]
(Real output should tailor the personal summary closely to the proposals and feedback received, written in the applicant’s own voice with more specific content in place of the placeholders.)

# Important instructions and objective reminder:
- Write the personal summary as if the applicant is describing themselves (first person: \"I\", "my").
- Only output the personal summary section for each Agent.
- Do not output any reasoning, analysis, or process explanations.
- Output in JSON format as specified above.""",
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
  instructions="""Create a resume builder agent that takes structured data about an individual's resume from upstream agents and organizes it into a JSON object matching the provided schema. 

- **Main Objective:**  
  Organize and normalize resume components (such as header info, skills, experience, education, and awards) from preceding agents’ outputs, mapping each field to its correct position in the required JSON schema.
- **Input:**  
  Partially or fully structured data about a resume from previous agents. Field names and organization may be inconsistent or incomplete.
- **Required Reasoning Before Output:**  
  - Carefully match all presented input data to the relevant fields in the schema.  
  - Validate all required fields are present; if missing, use the schema default values.  
  - Normalize inconsistent field names or structures into the schema fields.
  - For lists (skills, experience, education, awards), consolidate and deduplicate entries.
  - Ensure field data types and contents match the schema requirements.
  - Carefully check especially for nested objects within skills and education, correct all nesting and property naming.
- **Output Constraint:**  
  Only produce valid JSON as defined by the schema below.

Persist until all input is mapped, transformed, or defaulted according to the schema. Chain-of-thought: Reason step by step to identify, normalize, and format all fields before returning the JSON.

---

## RESUME SCHEMA/OUTPUT REQUIREMENTS

- **Format:**  
  Output JSON, unwrapped, matching this schema exactly. Fill all required fields with input data or default if missing.
- **Length:**  
  The entire resume in a single JSON object.
- **Syntax:**  
  - DO NOT add explanations, comments, markdown, or code blocks.
  - The result must be directly parseable as JSON and must match the provided schema.

---

## Resumé JSON Schema (required fields and structure)

[Insert the exact full schema as you provided here for easy model reference.]

---

## Example

**Input data from previous agents:**

{
  \"FullName\": \"Jane Doe\",
  \"EmailAddress\": \"jane.doe@email.com\",
  \"Location\": \"Boston, MA\",
  \"Links\": {
    \"LinkedIn\": \"https://linkedin.com/in/janedoe\",
    \"GitHub\": \"https://github.com/janedoe\"
  },
  \"Summary\": \"Experienced software engineer with focus on scalable backends.\",
  \"Skills\": {
    \"Programming\": [\"Python\", \"Java\"],
    \"Tech\": [\"AWS\", \"Docker\", \"Flask\"],
    \"Tools\": [\"Git\", \"VS Code\"]
  },
  \"Experience\": [
    \"Backend Engineer at TechX (2021-2023): Built microservices in Python.\",
    \"Intern at WebStart (2020): Refactored frontend in React.\"
  ],
  \"EducationHistory\": [
    {
      \"Degree\": \"B.Sc. Computer Science\",
      \"School\": \"Boston University\",
      \"Dates\": \"2017-2021\",
      \"Place\": \"Boston, MA\",
      \"GPA\": \"3.89\"
    }
  ],
  \"AwardsList\": [\"Dean's List 2018-2021\"]
}

---

**Step-by-step reasoning:**
- Map 'FullName' → header.name
- Map 'EmailAddress' → header.email
- Map 'Location' → header.location
- Map 'Links.LinkedIn' → header.linkedin
- Map 'Links.GitHub' → header.github
- Map 'Summary' → professional_summary
- Map 'Skills.Programming' to skills['Programming Languages']
- Map 'Skills.Tech' to skills['Technologies']
- Map 'Skills.Tools' to skills['Tools']
- Map 'Experience' → experience
- Map each item in 'EducationHistory' to a new education object with properties mapped as follows:
  - 'Degree' → degree
  - 'School' → institution
  - 'Dates' and so on
- Map 'AwardsList' → awards

---

**Resulting JSON output:**

{
  \"header\": {
    \"name\": \"Jane Doe\",
    \"email\": \"jane.doe@email.com\",
    \"location\": \"Boston, MA\",
    \"linkedin\": \"https://linkedin.com/in/janedoe\",
    \"github\": \"https://github.com/janedoe\"
  },
  \"professional_summary\": \"Experienced software engineer with focus on scalable backends.\",
  \"skills\": {
    \"Programming Languages\": [\"Python\", \"Java\"],
    \"Technologies\": [\"AWS\", \"Docker\", \"Flask\"],
    \"Tools\": [\"Git\", \"VS Code\"]
  },
  \"experience\": [
    \"Backend Engineer at TechX (2021-2023): Built microservices in Python.\",
    \"Intern at WebStart (2020): Refactored frontend in React.\"
  ],
  \"education\": [
    {
      \"degree\": \"B.Sc. Computer Science\",
      \"institution\": \"Boston University\",
      \"dates\": \"2017-2021\",
      \"location\": \"Boston, MA\",
      \"gpa\": \"3.89\"
    }
  ],
  \"awards\": [\"Dean's List 2018-2021\"]
}

(For real examples, expect multiple education entries, longer experience arrays, and more skills.)

---

**Edge Cases and Reminders**
- If any required field data is missing, fill it with the default as specified in the schema.
- Deduplicate arrays where necessary.
- Correct any capitalization or format inconsistencies during normalization.
- The output must strictly match the schema structure, types, and required fields—no extra fields or deviations allowed.

---

**REMINDER:**  
Your YIELD must be a single valid JSON object matching the schema, with all required fields filled. Reason through normalization and mapping before output.
""",
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

def compact_agent_output_item(result_temp, pick_fields: list[str] | None = None) -> TResponseInputItem:
  """
  Create a compact conversation history item from an agent run result.

  Preference order:
  - result_temp.final_output.json() if available
  - json.dumps(result_temp.final_output.model_dump()) if available
  - fallback to str(result_temp)

  Optional `pick_fields` may be provided in future to include only selected keys
  when final_output.model_dump() returns a dict. Currently returns a single
  assistant item with content.type 'agent_output' and text set to a JSON string.
  """
  try:
    final = result_temp.final_output
    try:
      out_text = final.json()
    except Exception:
      try:
        dumped = final.model_dump()
        if pick_fields and isinstance(dumped, dict):
          filtered = {k: dumped.get(k) for k in pick_fields if k in dumped}
          out_text = json.dumps(filtered, default=str)
        else:
          out_text = json.dumps(dumped, default=str)
      except Exception:
        out_text = str(final)
  except Exception:
    try:
      out_text = json.dumps(result_temp, default=str)
    except Exception:
      out_text = str(result_temp)

  return {
    "role": "assistant",
    "content": [
      {"type": "agent_output", "text": out_text}
    ]
  }


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

  # Append a compact single item for this agent run to avoid sending the entire chat history
    conversation_history.append(compact_agent_output_item(resume_flow_manager_result_temp))

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

    conversation_history.append(compact_agent_output_item(tune_resume_to_jd_agent_result_temp))

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

    conversation_history.append(compact_agent_output_item(personal_statement_agent_result_temp))

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

    conversation_history.append(compact_agent_output_item(resume_json_builder_agent_result_temp))

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

    conversation_history.append(compact_agent_output_item(judge_for_improvement_result_temp))

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

    conversation_history.append(compact_agent_output_item(improve_current_resume_agent_result_temp))

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

    conversation_history.append(compact_agent_output_item(personal_statement_agent_result_temp))

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

    conversation_history.append(compact_agent_output_item(resume_json_builder_agent_result_temp))

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

    conversation_history.append(compact_agent_output_item(judge_for_improvement_result_temp))

      judge_for_improvement_result = {
        "output_text": judge_for_improvement_result_temp.final_output.json(),
        "output_parsed": judge_for_improvement_result_temp.final_output.model_dump()
      }

    # Return the final optimized resume JSON
    return judge_for_improvement_result["output_parsed"]
