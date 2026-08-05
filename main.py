from fastapi import FastAPI,HTTPException
from contextlib import asynccontextmanager
from pathlib import Path
@asynccontextmanager
async def lifespan(app:FastAPI):
    print("aagent booting up..")
    resume_path = Path("my_resume.pdf")
    print(parse_resume(resume_path))
    yield
    print("agent closed")

app = FastAPI(lifespan=lifespan)


# function on startup to call pdf_parser
from pdf_parser import read_resume

def parse_resume(file_path):
    resume_as_text = read_resume(file_path)
    if resume_as_text :
        return resume_as_text
    else:
        raise HTTPException(status_code=500,detail="internal server error likely resume missing")
    