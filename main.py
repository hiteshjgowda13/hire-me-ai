from fastapi import FastAPI,HTTPException
from contextlib import asynccontextmanager
from pathlib import Path


@asynccontextmanager
async def lifespan(app:FastAPI):
    print("aagent booting up..")
    from tools_for_groq import parse_resume_json_using_ai

    resume_path = Path("my_resume.pdf")
    app.state.resume_text = parse_resume(resume_path)
    app.state.resume_json = parse_resume_json_using_ai(app.state.resume_text)

    yield

    print("agent closed")

app = FastAPI(lifespan=lifespan)



# function on startup to call pdf_parser
#helper function too
from pdf_parser import read_resume

def parse_resume(file_path):
    resume_as_text = read_resume(file_path)
    if resume_as_text :
        return resume_as_text
    else:
        raise HTTPException(status_code=500,detail="internal server error likely resume missing")



@app.get("/")
def home():
    return app.state.resume_json