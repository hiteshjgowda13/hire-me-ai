import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from groq_ai import chat_with_me


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("aagent booting up..")
    import json
    from tools_for_groq import parse_resume_json_using_ai, Resume

    resume_path = Path("my_resume.pdf")
    cache_path = Path("resume_cache.json")

    app.state.resume_text = parse_resume(resume_path)

    if cache_path.exists():
        print("loading cached resume_json (skip LLM call)")
        app.state.resume_json = Resume(**json.loads(cache_path.read_text(encoding="utf-8")))
    else:
        app.state.resume_json = parse_resume_json_using_ai(app.state.resume_text)
        cache_path.write_text(
            app.state.resume_json.model_dump_json(indent=2), encoding="utf-8"
        )

    yield

    print("agent closed")


app = FastAPI(lifespan=lifespan)

frontend_origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:5500,http://127.0.0.1:5500,https://your-vercel-app.vercel.app",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip() for origin in frontend_origins.split(",") if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# function on startup to call pdf_parser
# helper function too
from pdf_parser import read_resume


def parse_resume(file_path):
    resume_as_text = read_resume(file_path)
    if resume_as_text:
        return resume_as_text
    else:
        raise HTTPException(
            status_code=500, detail="internal server error likely resume missing"
        )


@app.get("/")
def home():
    return "welcome"


@app.post("/chat")
async def chat_stream(request: str = Body(..., media_type="text/plain")):
    return StreamingResponse(
        chat_with_me(user_message=request, resume_json=app.state.resume_json),
        media_type="text/plain",
    )
