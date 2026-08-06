from model_config import client,model
# from main import app
import json

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

    response = client.chat.completions.create(model=model,messages=messages,stream=True)

    for chunk in response:
        content = chunk.choices[0].delta.content
        if content :
            yield content
        