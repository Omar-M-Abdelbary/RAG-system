import openai
from typing import Dict, Optional, List
import os, json
import logging
from smolagents import CodeAgent, tool


logger = logging.getLogger('uvicorn.error')


@tool
def classify_user_intent(text: str) -> Dict:
    """
        Classifies the user's intent and identifies if it relates to a specific Cairo Capital branch.

        Args:
            text (str): The user's message to classify.

        Returns:
            Dict: A dictionary with the following structure:
                {
                "intent": "<one of: greeting | identity | branch_registration | branch_info | general_question | other>",
                "branch": "<securities | asset_management | private_equity | null>"
                }

        Example:
            classify_user_intent("I want to register with the asset management branch.")
            -> {"intent": "branch_registration", "branch": "asset_management"}
    """
    
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
