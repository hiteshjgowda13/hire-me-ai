# Hire Me AI

An AI-powered personal assistant that answers questions about Hitesh — his background, skills, and GitHub projects — using a resume-grounded LLM agent with live tool-calling and streamed responses.

## Overview

Hire Me AI is a conversational agent designed to sit on a personal portfolio site and answer recruiter/visitor questions on Hitesh's behalf. It parses a resume PDF into structured data at startup, and augments that with live tool calls to GitHub for project details, so answers about "what has Hitesh built" stay accurate without manual upkeep.

## Features

- Resume parsing: extracts structured data (skills, experience, education, projects) from a PDF resume using an LLM, validated against a Pydantic schema.
- Tool-calling agent: the assistant decides when to pull live GitHub data (project listings, repo details, README summaries) versus answering directly from resume context.
- Streaming responses: replies are streamed token-by-token over HTTP for a responsive chat experience.
- Guardrails: the system prompt constrains the assistant to stay on-topic (professional/technical queries about Hitesh), avoid fabricating information, and handle missing data gracefully.

## Architecture

```
frontend (static HTML/CSS/JS)
        |
        v
FastAPI backend (main.py)
        |
        +-- startup: parse resume PDF -> text -> structured JSON (Groq LLM)
        |
        +-- POST /chat: streaming agent loop (groq_ai.py)
                |
                +-- tool calls (tools_for_groq.py)
                        |
                        +-- GitHub REST API (public repos, README content)
```

The chat endpoint runs an agent loop against a Groq-hosted LLM: on each turn, the model either calls a tool (list projects, get project details, fetch raw resume text) or produces a final answer, which is streamed back to the client as plain text.

## Tech Stack

**Backend**
- Python, FastAPI, Uvicorn
- Groq API (LLM inference, tool calling, streaming)
- Pydantic (structured resume schema)
- pypdf (resume text extraction)
- GitHub REST API (project data)

**Frontend**
- Static HTML, CSS, and vanilla JavaScript
- No build step or framework — a lightweight streaming chat UI with a custom markdown/field renderer for structured responses (e.g. project listings)

## Project Structure

```
main.py              FastAPI app, CORS config, lifespan startup, /chat endpoint
groq_ai.py            Agent loop: system prompt, tool dispatch, streaming
tools_for_groq.py      Resume parsing, GitHub tool implementations
pdf_parser.py           Resume PDF -> text extraction
model_config.py          Groq client and model configuration
frontend/               Static chat UI (index.html, style.css, script.js)
```

## Live Demo

(link to be added after deployment)

## Attribution

The backend — API design, the resume-parsing pipeline, the agent/tool-calling logic, and integration with the Groq and GitHub APIs — was designed and built end to end by Hitesh.

The frontend (chat UI, styling, and client-side response rendering) was built using Claude Code, based on the existing backend API contract, without modifying any backend logic.
