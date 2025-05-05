from fastapi import FastAPI, APIRouter, status, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator, Field, EmailStr
from typing import Dict, Optional, List
import os, json
from datetime import datetime
import logging
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import openai
from openai import OpenAI
from routes.schemes.nlp import PushRequest, SearchRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from controllers import NLPController
from models import ResponseSignal
from smolagents import CodeAgent, tool, HfApiModel
from tools.agent import classify_user_intent

evaluate_router = APIRouter(
    prefix ="/api/evaluate",
    tags=["api", "evaluate"],
)

logger = logging.getLogger('uvicorn.error')

# Email configuration
EMAIL_ADDRESS = 
EMAIL_PASSWORD = 
SMTP_SERVER = 
SMTP_PORT = 587

# Branch information
BRANCHES = {
    "securities": {
        "name": "Investment Banking & Securities Brokerage",
        "full_name": "Cairo Capital Securities",
        "description": "Our securities brokerage services provide expert investment advice and trading capabilities"
    },
    "asset_management": {
        "name": "Asset Management",
        "full_name": "Cairo Capital Asset Management",
        "description": "Professional asset management services to help grow and protect your investments"
    },
    "private_equity": {
        "name": "Private Equity",
        "full_name": "Cairo Capital Private Equity",
        "description": "Strategic private equity investments in promising mid-cap companies"
    }
}

# Registration state tracking
registration_states = {}

# Registration field order
REGISTRATION_FIELDS = [
    "name",
    "email",
    "username",
    "password"
]

# Field prompts
FIELD_PROMPTS = {
    "name": "Please provide your full name:",
    "email": "Please provide your email address:",
    "username": "Please choose a username (4-20 characters, letters, numbers, and underscores only):",
    "password": "Please create a password (minimum 4 characters, letters and numbers only):"
}

class UserRegistration(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    username: str = Field(..., min_length=4, max_length=20)
    password: str = Field(..., min_length=4, max_length=20)
    branch: str

    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("Username can only contain letters, numbers, and underscores")
        return v

    @validator('password')
    def validate_password(cls, v):
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{4,}$', v):
            raise ValueError("Password must be at least 4 characters long and contain at least one letter and one number")
        return v

    @validator('branch')
    def validate_branch(cls, v):
        if v not in BRANCHES:
            raise ValueError(f"Invalid branch. Must be one of: {', '.join(BRANCHES.keys())}")
        return v

async def send_email(subject: str, body: str):
    """Send an email notification."""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = EMAIL_ADDRESS
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info("Email sent successfully")
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")

def get_greeting_response() -> str:
    """Get an appropriate greeting response."""
    return "Hello! I'm your assistant for Cairo Capital information and registration. How can I help you today?"

def get_identity_response() -> str:
    """Get a response for identity questions."""
    return "I am Cairo Capital's virtual assistant. I can help you with information about our services, assist with registration for our different branches (Investment Banking & Securities Brokerage, Asset Management, and Private Equity), and answer your questions about our company."

def get_branch_from_text(text: str) -> Optional[str]:
    """Extract branch from user's text."""
    text = text.lower().strip()
    
    # Define keywords for each branch
    branch_keywords = {
        "securities": [
            "securities", "investment banking", "brokerage", "trading",
            "investment", "banking", "securities brokerage"
        ],
        "asset_management": [
            "asset management", "wealth management", "portfolio",
            "investment management", "assets"
        ],
        "private_equity": [
            "private equity", "private", "equity", "capital",
            "private investment"
        ]
    }
    
    # Check for matches in keywords
    for branch_key, keywords in branch_keywords.items():
        if any(keyword in text for keyword in keywords):
            return branch_key
    
    return None



def save_user_info_locally(user_info: dict):
    """Save user information to a local file."""
    try:
        # Create user_data directory if it doesn't exist
        os.makedirs("user_data", exist_ok=True)
        
        # Format the information for the file
        info_text = f"""User Information:
Name: {user_info['name']}
Email: {user_info['email']}
Username: {user_info['username']}
Branch: {user_info['branch']}
Registration Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        
        filename = f"user_data/{user_info['username']}_info.txt"
        with open(filename, 'w') as f:
            f.write(info_text)
        logger.info(f"User information saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving user information: {str(e)}")
        raise


def classify_user_intent(text: str) -> Dict:
    
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """You are an AI assistant for Cairo Capital. Your task is to classify the user's intent and identify if it's related to any specific branch. Classify the user's message into one of the following categories:

1. greeting - User is greeting (e.g., "hi", "hello", "good morning", "how are you", "hey", "what's up", "how's it going")
2. identity - User is asking about who you are or what you can do (e.g., "who are you", "what are you", "introduce yourself", "tell me about yourself", "what can you do")
3. branch_registration - User wants to register for a specific branch
4. branch_info - User wants information about a specific branch or its divisions
5. general_question - User has a general question about Cairo Capital, its divisions, or services
6. other - User's query doesn't fit any of the above categories

If the user refers to a specific branch, identify which one. Valid branches are:
- securities
- asset_management
- private_equity

Guidelines for classification:
- Any form of greeting or polite conversation opener should be classified as 'greeting'
- Questions about your identity or capabilities should be classified as 'identity'
- Questions about registration, accounts, or wallets should be classified as 'branch_registration'
- Questions about specific services or divisions should be classified as 'branch_info'
- General questions about Cairo Capital should be classified as 'general_question'
- If unsure, classify as 'other'

Cairo Capital-related topics include:
- Cairo Capital 
- Investment banking and securities brokerage
- Asset management and wealth management
- Private equity investments
- Financial services
- Trading and brokerage
- Portfolio management
- Capital markets
- Team members
- Account registration and wallet services
- Financial products and services
- Company divisions and departments

Return the classification result as a JSON object in this format:
{
  "intent": "<one of: greeting | identity | branch_registration | branch_info | general_question | other>",
  "branch": "<securities | asset_management | private_equity | null>"
}"""},
                {"role": "user", "content": text}
            ],
            temperature=0
        )
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Intent classification result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in intent classification: {str(e)}")
        return {"intent": "general_question", "branch": None}


@evaluate_router.post("/evaluate")
async def evaluate(request: Request, user_input: SearchRequest):
    """Evaluate user input and provide appropriate response."""
    try:
        logger.info(f"Evaluating input: {user_input.text}")
        
        # Classify intent first
        intent = classify_user_intent(user_input.text)
        logger.info(f"Classified intent: {intent}")
        

        
        # Handle greetings through intent classification
        if intent["intent"] == "greeting":
            if "how are you" in user_input.text.lower():
                return {
                    "response": "I'm doing well, thank you! How can I help you with Cairo Capital today?",
                    "type": "greeting"
                }
            return {
                "response": get_greeting_response(),
                "type": "greeting"
            }
        
        # Handle identity questions through intent classification
        if intent["intent"] == "identity":
            return {
                "response": get_identity_response(),
                "type": "identity"
            }
        
        # Check if user is in registration process
        session_id = request.headers.get('X-Session-ID', 'default')
        if session_id in registration_states:
            current_state = registration_states[session_id]
            
            # Handle branch selection during registration
            if current_state == 'awaiting_branch':
                branch = get_branch_from_text(user_input.text)
                if branch:
                    registration_states[session_id] = 'collecting_info'
                    registration_states[session_id + '_branch'] = branch
                    registration_states[session_id + '_current_field'] = 0
                    registration_states[session_id + '_info'] = {}
                    
                    current_field = REGISTRATION_FIELDS[0]
                    return {
                        "response": FIELD_PROMPTS[current_field],
                        "type": "registration_prompt"
                    }
                else:
                    return {
                        "response": "Please select a valid branch: Investment Banking & Securities Brokerage, Asset Management, or Private Equity.",
                        "type": "branch_selection"
                    }
            
            # Handle registration information collection
            elif current_state == 'collecting_info':
                current_field_index = registration_states[session_id + '_current_field']
                current_field = REGISTRATION_FIELDS[current_field_index]
                user_info = registration_states[session_id + '_info']
                
                # Validate the input based on the current field
                try:
                    if current_field == 'name':
                        if len(user_input.text.strip()) < 2:
                            raise ValueError("Name must be at least 2 characters long")
                        user_info['name'] = user_input.text.strip()
                    
                    elif current_field == 'email':
                        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', user_input.text.strip()):
                            raise ValueError("Please provide a valid email address")
                        user_info['email'] = user_input.text.strip()
                    
                    elif current_field == 'username':
                        if not re.match(r'^[a-zA-Z0-9_]{4,20}$', user_input.text.strip()):
                            raise ValueError("Username must be 4-20 characters, letters, numbers, and underscores only")
                        user_info['username'] = user_input.text.strip()
                    
                    elif current_field == 'password':
                        if not re.match(r'^[a-zA-Z0-9]{4,}$', user_input.text.strip()):
                            raise ValueError("Password must be at least 4 characters long and contain only letters and numbers")
                        user_info['password'] = user_input.text.strip()
                    
                    # Move to next field
                    current_field_index += 1
                    registration_states[session_id + '_current_field'] = current_field_index
                    
                    # If all fields are collected, complete registration
                    if current_field_index >= len(REGISTRATION_FIELDS):
                        # Create registration object
                        registration = UserRegistration(
                            **user_info,
                            branch=registration_states[session_id + '_branch']
                        )
                        
                        # Save user information
                        save_user_info_locally(registration.dict())
                        
                        # Send confirmation email
                        branch_info = BRANCHES[registration.branch]
                        await send_email(
                            "New User Registration",
                            f"New registration for {branch_info['full_name']}:\n\n"
                            f"Name: {registration.name}\n"
                            f"Email: {registration.email}\n"
                            f"Username: {registration.username}\n"
                            f"Branch: {branch_info['name']}"
                        )
                        
                        # Clear registration state
                        del registration_states[session_id]
                        del registration_states[session_id + '_branch']
                        del registration_states[session_id + '_current_field']
                        del registration_states[session_id + '_info']
                        
                        return {
                            "response": f"Registration successful for {branch_info['full_name']}! We'll contact you shortly.",
                            "type": "registration_success"
                        }
                    
                    # Ask for next field
                    next_field = REGISTRATION_FIELDS[current_field_index]
                    return {
                        "response": FIELD_PROMPTS[next_field],
                        "type": "registration_prompt"
                    }
                    
                except ValueError as e:
                    return {
                        "response": f"Invalid input: {str(e)}\n\n{FIELD_PROMPTS[current_field]}",
                        "type": "registration_error"
                    }
        
        # Handle off-topic questions
        if intent["intent"] == "other":

            await send_email(
                "Off-Topic Question",
                f"User asked about a topic unrelated to Cairo Capital:\n\n"
                f"Question: {user_input.text}\n\n"
                f"Please review and provide appropriate guidance."
            )
            return {
                "response": "I apologize, but I can only provide information about Cairo Capital and its services. Our team has been notified about your question and will get back to you.",
                "type": "off_topic"
            }
        
        # Handle branch registration
        if intent["intent"] == "branch_registration" or "wallet" in user_input.text.lower() or "account" in user_input.text.lower():
            # Start registration process
            session_id = request.headers.get('X-Session-ID', 'default')
            registration_states[session_id] = 'awaiting_branch'
            
            return {
                "response": "Which branch would you like to register for? Please specify: Investment Banking & Securities Brokerage, Asset Management, or Private Equity.",
                "type": "branch_selection"
            }
        
        # Handle branch information requests and general questions
        elif intent["intent"] in ["branch_info", "general_question"]:
            try:
                project_id = 2
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
                
                # If it's a branch info request and we know which branch
                if intent["intent"] == "branch_info" and intent["branch"]:
                    branch_info = BRANCHES[intent["branch"]]
                    return {
                        "response": f"{branch_info['full_name']}:\n{branch_info['description']}",
                        "type": "branch_info"
                    }
                
                # For general questions or when branch is not specified
                answer, _, _ = await nlp_controller.answer_rag_question(
                    project=project,
                    query=user_input.text,
                    limit=user_input.limit
                )
                
                if answer:
                    return {
                        "response": answer,
                        "type": "rag_answer"
                    }
                
                # If no answer found, provide a fallback response about divisions
                if "division" in user_input.text.lower() or "main" in user_input.text.lower():
                    divisions_info = "\n".join([
                        f"1. {branch['full_name']}: {branch['description']}"
                        for branch in BRANCHES.values()
                    ])
                    return {
                        "response": f"Cairo Capital has three main divisions:\n\n{divisions_info}",
                        "type": "divisions_info"
                    }
                
                # If no answer found, send email notification
                await send_email(
                    "Unanswered Question",
                    f"User asked: {user_input.text}\n\nNo relevant information found in the knowledge base."
                )
                return {
                    "response": "I don't have specific information about that in my knowledge base. Our team has been notified and will get back to you.",
                    "type": "no_answer"
                }
                
            except Exception as e:
                logger.error(f"Error in RAG system: {str(e)}")
                return {
                    "response": "I'm having trouble accessing the information right now. Please try again later.",
                    "type": "error"
                }
        
        # Handle other queries
        else:
            await send_email(
                "Unhandled Query",
                f"User asked: {user_input.text}\n\nThis query doesn't match any of our predefined categories."
            )
            return {
                "response": "I'm not sure how to help with that. Our team has been notified and will get back to you.",
                "type": "other"
            }
                
    except Exception as e:
        logger.error(f"Error evaluating input: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@evaluate_router.post("/register")
async def register_user(registration: UserRegistration):
    try:
        # Save user information locally
        save_user_info_locally(registration.dict())
        
        # Send confirmation email
        branch_info = BRANCHES[registration.branch]
        await send_email(
            "New User Registration",
            f"New registration for {branch_info['full_name']}:\n\n"
            f"Name: {registration.name}\n"
            f"Email: {registration.email}\n"
            f"Username: {registration.username}\n"
            f"Branch: {branch_info['name']}"
        )
        
        return {
            "message": f"Registration successful for {branch_info['full_name']}! We'll contact you shortly.",
            "type": "registration_success"
        }
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

