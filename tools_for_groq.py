from pydantic import BaseModel
from model_config import client,model
import os
import json
from urllib.request import Request,urlopen
from urllib.parse import urlencode


#tool for groq which stores only resume text fall back to this if question asked  cannot be asked from json format
def only_text() -> str:
    """this function is a tool use it for getting the text of resume it contains evrything about the user's resume"""
    from main import app
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

    Return ONLY a single valid JSON object (not a list/array) matching this schema:

    {resume_schema}

    Important rules:

    1. Do not invent information.
    2. If a value is not available, return null.
    3. If a list has no information, return an empty list.
    4. Include internships inside experiences.
    5. Extract skills mentioned across the entire resume.
    6. The top-level output must be a JSON object with these exact keys, never a bare array.
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
    attempts = 4
    for attempt in range(1, attempts + 1):
        response = client.chat.completions.create(model=model,messages=messages,temperature=0,response_format=response_format)
        raw_output = response.choices[0].message.content
        data = json.loads(raw_output)

        if isinstance(data, list) and len(data) == 1 and isinstance(data[0], dict):
            data = data[0]

        if isinstance(data, dict):
            return Resume(**data)

        if attempt == attempts:
            raise ValueError(f"resume parser returned {type(data).__name__} instead of a JSON object after {attempts} attempts")

        messages.append({"role": "assistant", "content": raw_output})
        messages.append({
            "role": "user",
            "content": "That was a JSON array, not an object. Re-send ONLY a single JSON object matching the schema — no array wrapper.",
        })


# simple webscrapper for getting acess of my repos
def _github_get(url:str):
    token = os.getenv("GITHUB_TOKEN")
# request headers sending for the scrapping to work
    headers ={
        "Accept":"application/vnd.github+json",
        "X-Github-Api-Version":"2022-11-28",
        "user-agent":"hire-me-ai"
    }

    if token:
        headers["Authorization"] =f"Bearer {token}"
    
    req= Request(url,headers=headers)
    with urlopen(req,timeout=20)as resp:
        return json.loads(resp.read().decode('utf-8'))


# function of getting public repos from abv func
def list_public_projects() -> list[dict]:
    """tool for llm: use this when you need to acess all projects of Hitesh's project 
        this project also include whatever is mentinoned in resume too
        therefore list all projects means get projects in github """
    username = os.getenv("GITHUB_USERNAME")

    if not username:
        raise ValueError("github username missing")

    all_projects =[]
    # simple pagination
    page =1 
    per_page=100
    # looping till end of page
    while True:
        query = urlencode({
            "per_page":per_page,
            "page":page,
            "type":"owner"
        })
        url = f"https://api.github.com/users/{username}/repos?{query}"
        repos = _github_get(url)

        #no more repos to get so empty repos ie none so break and exit
        if not repos:
            break

        for repo in repos:
            if not repo.get("private",False):
                all_projects.append({
                    "project_name":repo.get("name",""),
                    "description":repo.get("description")
                })
        if len(repos) <per_page:
            break
        page +=1

    return all_projects

def get_project_details(project_name:str) -> dict:
    """
    when query is asking about specific project use this tool
    and give a detail explanation using readme_excerpt,
    lamguages used give a overwiew
    """
    username = os.getenv("GITHUB_USERNAME")
    if not username:
        raise ValueError("github username_missing")

    repo = _github_get(f"https://api.github.com/repos/{username}/{project_name}")

    if repo.get("private",False):
        return {"error":"project is private not visible for public view"}


    langs = _github_get(repo["languages_url"])

    readme_text =""

    try:
        readme = _github_get(f"https://api.github.com/repos/{username}/{project_name}/readme")
        import base64
        if readme.get("encoding") == "base64" and readme.get("content"):
            readme_text = base64.b64decode(readme["content"]).decode("utf-8",errors="ignore")[:4000]
    except Exception:
        readme_text=""

    return {
        "project_name": repo.get("name", ""),
        "description": repo.get("description") or "No description",
        "homepage": repo.get("homepage") or "",
        "topics": repo.get("topics") or [],
        "languages": langs,
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "readme_excerpt": readme_text
    }
