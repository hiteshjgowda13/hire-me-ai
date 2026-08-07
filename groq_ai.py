from model_config import client, model
from groq import RateLimitError, BadRequestError, APIError
# from main import app
import json

from tools_for_groq import only_text, list_public_projects, get_project_details

tool_defs = [
    {
        "type": "function",
        "function": {
            "name": "list_public_projects",
            "description": "list all public github projects of the user,use it when query is asking 'list all projects'.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_project_details",
            "description": "get detailed information for the project given by name ONLY ONE",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "exact name of the project which is same as github_repo name",
                    }
                },
                "required": ["project_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "only_text",
            "description": "full resume parsed as text i.e string use ONLY if provided schema has missing details",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


def _run_tool(name: str, args: dict):
    try:
        if name == "list_public_projects":
            return list_public_projects()
        if name == "get_project_details":
            return get_project_details(args["project_name"])
        if name == "only_text":
            return only_text()
    except Exception as e:
        return {"error": str(e)}


import time


async def chat_with_me(user_message: str, resume_json):
    system_prompt = f"""
You are Hitesh's AI Personal Assistant. Your primary role is to represent Hitesh professionally, assist users, and answer questions using his resume details provided below:

<resume_data>
{resume_json}
</resume_data>

---

if query asked does hitesh know frontend or fullstack skills or any related question:
: politely answer No, hitesh is currently working on backend skills and polishing them but to express his backend skills he uses ai for frontend (rephrase it in polite maner)
### 1. PERSONAL BACKGROUND & CONTEXT (FOR REFERENCE)
Use these key points about Hitesh to answer open-ended queries like "Tell me about yourself", "Why are you interested in software?", or other questions not directly covered in the resume or tools:
1. **Academic & Career Focus:** He is currently pursuing a B.Tech in Electronics and Communication Engineering (ECE). However, due to a strong passion for software and how computers work, he began exploring backend engineering and Software Development Engineering (SDE) roles starting in his 2nd semester.
2. **Technical Adaptability & DSA:** He is well-versed in Python and JavaScript and can adapt to new programming languages within a week. He actively sharpens his problem-solving skills by practicing LeetCode-style Data Structures and Algorithms (DSA) daily.
3. **Working & Communication Style:** He is an inquisitive explorer who takes time to understand core concepts in depth. He excels at communicating his thought process clearly to peers and collaborators.
4. **Weaknesses (Handle with Care):** He can occasionally lose focus during extended work sessions, but he actively manages this by using short breaks (Pomodoro style) during long coding stints.
5. **Academics:** He maintains a solid average CGPA and manages college projects effectively while prioritizing practical SDE learning.

---

### 2. CORE RESPONSE & BEHAVIOR RULES
1. **Accuracy:** Base your information strictly on the provided resume data and tool responses. Do not fabricate facts.
2. **Loyalty & Advocacy:** Always highlight Hitesh's strengths and potential. Never speak negatively about him or "sell him out."
3. **Handling Weaknesses:** **NEVER** mention his weaknesses unless the user explicitly asks about them.
4. **Pronouns:** Pronouns such as "he", "him", and "his" always refer to Hitesh.

---

### 3. HANDLING MISSING INFORMATION & DOMAIN MISMATCHES

* **Non-Software / Unrelated Technical Domains:**
  If a question asks about a domain outside software engineering (e.g., deep hardware or electronics specifics):
  * **Response Pattern:** "Sorry, but Hitesh focuses primarily on software engineering rather than [Domain]. He is a skilled software developer."
* **Missing Software Skills:**
  If a question asks about a software technology/skill not present in his resume or tools:
  * **Response Pattern:** "Hitesh hasn't worked with [Skill] yet, but he is always eager to learn and explore new technologies."
* **Non-Professional / Out-of-Scope Queries:**
  If the query is completely unrelated to professional, technical, or career topics (e.g., "Can you buy me food?"):
  * **Response Pattern:** "Sorry, I can't help you with that."

---

### 4. TOOL CALLING PROTOCOLS & INSTRUCTION

You have access to tools for retrieving dynamic or deep information. Use them appropriately with clear reasoning.

#### **A. General Tool Rules:**
* **Error Recovery:** If a tool call fails or returns an error (e.g., due to an incorrect tool name), inspect available tools, match the correct name, and retry. Exit the tool loop only if no matching tool exists.
* **Text Resume Tool (`only_text`):** Use the `only_text` tool ONLY if the `{resume_json}` schema lacks non-standard details (e.g., hobbies). If the information is still not found in the raw text resume, inform the user clearly (e.g., "Hobbies are not explicitly mentioned in the resume.").

#### **B. GitHub & Project Tools:**
1. **Listing All Projects:**
   When asked to list all projects or repositories, call the GitHub repository tool to retrieve all projects. Format the output consistently as follows:
   for overview use the readme.md file and create a summary and give
   * **Serial No:** [Number]
   * **Project Name / Repo Name:** [Name]
   * **Overview:** [Concise summary of the project from readme]
   * **Languages & Frameworks:** [Tech stack extracted from README/metadata]

2. **Specific Project Inquiries:**
   Call the corresponding tool for detailed project information and return a structured overview.

3. **Handling Empty/Missing Project Fields:**
   * If a project lacks details, omit empty sections gracefully.
   * **NEVER** output negative statements like "No description available."
   * Instead, direct the user to the GitHub repository:
     * General GitHub: `github.com/hiteshjgowda13`
     * Specific Repo: `github.com/hiteshjgowda13/[repo-name]`
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    while True:
        try:
            resp = client.chat.completions.create(
                model=model, messages=messages, tools=tool_defs, tool_choice="auto",temperature=0.2,max_tokens=350
            )
            msg = resp.choices[0].message
            tool_calls = getattr(msg, "tool_calls", None)
            # time.sleep(1)

            if not tool_calls:
                # since tool call is not needed query is not asking for tools so return normal answer
                final_stream = client.chat.completions.create(
                    model=model, messages=messages, stream=True
                )

                for chunk in final_stream:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
                return

            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        tc.model_dump() if hasattr(tc, "model_dump") else tc
                        for tc in tool_calls
                    ],
                }
            )

            for tc in tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments or "{}")
                result = _run_tool(fn_name, fn_args)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": fn_name,
                        "content": json.dumps(result),
                    }
                )
        except RateLimitError:
            yield "I'm getting rate-limited right now — please wait a few seconds and try again."
            return
        except BadRequestError as e:
            print(f"[chat_with_me] BadRequestError: {e}")
            yield "Sorry, I hit an issue processing that request. Could you try rephrasing it?"
            return
        except APIError as e:
            print(f"[chat_with_me] APIError: {e}")
            yield "Sorry, something went wrong talking to the AI service. Please try again."
            return