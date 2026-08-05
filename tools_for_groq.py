from main import app
from pydantic import BaseModel
from model_config import client,model


#tool for groq which stores only resume text fall back to this if question asked  cannot be asked from json format
def only_text() -> str:
    """this function is a tool use it for getting the text of resume it contains evrything about the user's resume"""
    return app.state.resume_text


class Expirence(BaseModel):
    company:str|None = None
    role:str|None= None
    duration:str|None = None
    description:str|None=None
    skill_used: list[str] =[]

# what to extract from resume not fully text but this is main key points of resume
class Resume(BaseModel):
    name:str |None = None
    email:str |None =None
    phone:str |None = None

    total_experience_years: float | None = None

    skills: list[str] =[]
    expirences : list[Expirence] =[]
    education:list[str] =[]
    projects:list[str] =[]
    certification:list[str]=[]

resume_schema = Resume.model_json_schema()

#we will use this once we could hav writtent this in main but it ll be lengthy
import json
def parse_resume_json_using_ai(resume_text):
    system_prompt = f"""
    You are an expert resume parser.

    Extract information from the resume based on its meaning,
    not only based on exact section headings.

    Different resumes may use different headings.

    For example:
    - Experience
    - Professional Experience
    - Work History
    - Employment
    - Internships

    These may all contain relevant experience.

    Skills may also appear in the skills section, work experience,
    internships or projects.

    Return ONLY valid JSON matching this schema:

    {resume_schema}

    Important rules:

    1. Do not invent information.
    2. If a value is not available, return null.
    3. If a list has no information, return an empty list.
    4. Include internships inside experiences.
    5. Extract skills mentioned across the entire resume.
    """

    user_prompt = f"""
    Parse the following resume:
    {resume_text}
    """

    system_message ={
        "role":"system",
        "content":system_prompt
    }
    user_message ={
        "role":"user",
        "content":user_prompt
    }
    messages =[system_message,user_message]
    response_format ={
        "type":"json_object"
    }
    response = client.chat.completions.create(model=model,messages=messages,temperature=0,response_format=response_format)

    raw_output = response.choices[0].message.content
    data = json.loads(raw_output)
    resume = Resume(**data)

    return resume