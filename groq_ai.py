from model_config import client,model
# from main import app
import json

from tools_for_groq import only_text,list_public_projects,get_project_details

tool_defs =[
    {
        "type":"function",
        "function":{
            "name":"list_public_projects",
            "description":"list all public github projects of the user.",
            "parameters":{
                "type":"object",
                "properties":{},
                "required":[]
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"get_project_details",
            "description":"get detailed information for the project given by name ONLY ONE",
            "parameters":{
                "type":"object",
                "properties":{"project_name:":{"type":"string","description":"exact name of the project which is same as github_repo name"}},
                "required":["project_name"]
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"only_text",
            "description":"full resume parsed as text i.e string use ONLY if provided schema has missing details",
                "parameters":{
                    "type":"object",
                    "properties":{},
                    "required":[]
            }
        }
    }
]
def _run_tool(name:str,args:dict):
    if name == "list_public_projects":
        return list_public_projects()
    if name == "get_project_details":
        return get_project_details(args["project_name"])
    if name == "only_text":
        return only_text()
    return {"error":f"unknown tool {name}"}
    

import time
async def chat_with_me(user_message:str,resume_json):
    system_prompt =f"""
    your Pratyush's persnoal assistant your job is to read resume 
    details from the content given to you:
    {resume_json}
    the given schema consist of key points of resume you can use it to answer user's question 
    important:
    1. give infromation related to resume only dont provide false facts
    2. if given question doesnt have any answer in resume 
        eg. if resume shows owner is software engineer and question is related to electronics 
        response = sorry but pratyush is not well wersed in electronics infact he is a good sofwtare engineer
        format the response accordingly dont repeat same response

        eg. if resume have missing skills but it is related to owners field 
        response = pratyush has not yet worked with it yet but he is always eager to learn and explore

        
    your also handed the tools for neccessary queries use tools appropriatley with reasoning 
    note for tool calling:
    if tool calling returns error the tool name is wrong check for matching tools then call again
    if no tool for that only then exit tool loop

    your provided with tool name 'only_text' which returns resume as a text
    if resume_schema doesnt hav query's answer like hobbies or anything only then use this
    if that is not found in the resume as a text then answer accordingly eg. sorry hobbies are not mentioned in resume

    IMPORTANT:
    if query is unrelated to proffessniol things eg can you buy me food
    return sorry i cant help you with that 

    """

    messages = [
        {
            "role":"system",
            "content":system_prompt
        },
        {
            "role":"user",
            "content":user_message
        }
    ]

    while True:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tool_defs,
            tool_choice="auto"
        )
        msg = resp.choices[0].message
        tool_calls = getattr(msg,"tool_calls",None)
        time.sleep(1)
        if not tool_calls:
            # since tool call is not needed query is not asking for tools so return normal answer
            final_stream = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True
            )

            for chunk in final_stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
            return 
        messages.append({
            "role":"assistant",
            "content":msg.content or "",
            "tool_calls":[
                tc.model_dump() if hasattr(tc, "model_dump") else tc
                for tc in tool_calls
            ]
        })

        for tc in tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments or "{}")
            result = _run_tool(fn_name, fn_args)

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": fn_name,
                "content": json.dumps(result),
        })