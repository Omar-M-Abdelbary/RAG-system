# rag_agent_server.py
from mcp.server.fastmcp import FastMCP
import json
from fastapi import FastAPI, APIRouter, status, Request, HTTPException
 # adjust this to your actual import paths
from routes.schemes.nlp import PushRequest, SearchRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from controllers import NLPController
from models import ResponseSignal

mcp = FastMCP("RAG")

from typing import Dict
import os, json
from datetime import datetime

user_sessions: Dict[str, dict] = {}

required_fields = {
    "name": {
        "question": "What is your name?",
        "validation": lambda x: len(x.strip()) >= 2 and x.replace(" ", "").isalpha(),
        "error": "Please enter a valid name (at least 2 letters)"
    },
    "age": {
        "question": "How old are you? (10-99)",
        "validation": lambda x: x.isdigit() and 10 <= int(x) <= 99,
        "error": "Please enter a valid age between 10-99"
    },
    "address": {
        "question": "What is your address?",
        "validation": lambda x: len(x.strip()) >= 5,
        "error": "Please enter a valid address (at least 5 characters)"
    },
    "profession": {
        "question": "What is your profession?",
        "validation": lambda x: len(x.strip()) >= 2,
        "error": "Please enter a valid profession"
    }
}

def get_session(project_id: str = "default_project") -> dict:
    if project_id not in user_sessions:
        user_sessions[project_id] = {
            'user_info': {},
            'current_field': next(iter(required_fields))
        }
    return user_sessions[project_id]

@mcp.tool()
def collect_user_info(text: str, project_id: str = "default_project") -> str:
    session = get_session(project_id)
    for field, rules in required_fields.items():
        if field not in session['user_info']:
            if rules['validation'](text):
                session['user_info'][field] = text.strip()
                session['current_field'] = None
                break
            else:
                return rules['error']
    return get_next_question_or_done(session)

def get_next_question_or_done(session: dict) -> str:
    missing_field = next((field for field in required_fields if field not in session['user_info']), None)
    if missing_field:
        session['current_field'] = missing_field
        return required_fields[missing_field]['question']
    return save_user_data(session['user_info'])

@mcp.tool()
def save_user_data(user_info: dict) -> str:
    os.makedirs("user_data", exist_ok=True)
    filename = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(f"user_data/{filename}", "w") as f:
        for k, v in user_info.items():
            f.write(f"{k}: {v}\n")
    return f"✅ Saved user data to {filename}"



mcp = FastMCP("RagAgent")

@mcp.tool()
async def answer_cat_question(search_request: SearchRequest) -> str:
    try:
        request = Request
        project_id = "2"
        

        project_model = await ProjectModel.create_instance(
            db_client=request.app.db_client
        )

        project = await project_model.get_project_or_create_one(
            project_id=project_id
        )

        nlp_controller = NLPController(
            vectordb_client=request.app.vectordb_client,
            generation_client=request.app.generation_client,
            embedding_client=request.app.embedding_client,
            template_parser=request.app.template_parser,
        )

        # 1. Get the RAG answer and context
        answer, full_prompt, chat_history = await nlp_controller.answer_rag_question(
            project=project,
            query=search_request.text,
            limit=search_request.limit,
        )
        if not answer:
            return "❌ RAG Error: No answer returned."

        return answer

    except Exception as e:
        import traceback
        return f"❌ RAG Tool Error:\n{traceback.format_exc()}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
