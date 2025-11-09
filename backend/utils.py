import os
import httpx
import json
import random
from typing import Dict, Any, Optional, List
import asyncio
from dotenv import load_dotenv
from models import Question
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Predefined Topics for Random Selection ---
TOPICS_LIST = [
    "Python programming",
    "JavaScript fundamentals",
    "Machine Learning basics",
    "Data Structures and Algorithms",
    "Web Development",
    "Database Design",
    "Cloud Computing",
    "Cybersecurity",
    "DevOps practices",
    "React framework",
    "Node.js",
    "API Design",
    "Software Testing",
    "Git and Version Control",
    "Docker and Containers",
    "Microservices Architecture",
    "Artificial Intelligence",
    "Computer Networks",
    "Operating Systems",
    "Object-Oriented Programming",
    "Functional Programming",
    "REST APIs",
    "GraphQL",
    "Agile Methodologies",
    "System Design"
]

def get_random_topic() -> str:
    """Select a random topic from the predefined list."""
    return random.choice(TOPICS_LIST)

# --- NeuralSeek API Configuration ---
NEURALSEEK_API_URL = os.getenv("NEURALSEEK_API_URL")
NEURALSEEK_API_KEY = os.getenv("NEURALSEEK_API_KEY")
NEURALSEEK_INSTANCE_ID = os.getenv("NEURALSEEK_INSTANCE_ID")

# Agent Names
MAKE_QUESTION_AGENT = os.getenv("MAKE_QUESTION_AGENT", "make_question")
QUESTION_GENERATOR_AGENT = os.getenv(
    "QUESTION_GENERATOR_AGENT", "question_generator_agent"
)
ANSWER_VALIDATOR_AGENT = os.getenv("ANSWER_VALIDATOR_AGENT", "answer_validator_agent")

# Validate configuration
if not all([NEURALSEEK_API_URL, NEURALSEEK_API_KEY, NEURALSEEK_INSTANCE_ID]):
    raise ValueError(
        "NEURALSEEK_API_URL, NEURALSEEK_API_KEY, and NEURALSEEK_INSTANCE_ID must be set in .env"
    )

logger.info("✅ NeuralSeek Config Loaded")
logger.info(f"   URL: {NEURALSEEK_API_URL}")
logger.info(f"   Instance ID: {NEURALSEEK_INSTANCE_ID}")


async def call_maistro_agent(
    agent_name: str, params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generic function to call a NeuralSeek mAIstro agent.

    Args:
        agent_name: The name of the agent to run.
        params: A dictionary of parameters to pass to the agent.

    Returns:
        The JSON response from the agent.

    Raises:
        httpx.HTTPStatusError: If the API call fails.
    """
    headers = {
        "Content-Type": "application/json",
        "apikey": NEURALSEEK_API_KEY,
    }

    if not NEURALSEEK_API_URL or not NEURALSEEK_INSTANCE_ID:
        raise ValueError("NeuralSeek API configuration is incomplete.")

    # The instance ID is part of the URL path
    api_url = f"{NEURALSEEK_API_URL.rstrip('/')}/{NEURALSEEK_INSTANCE_ID}/maistro"

    payload: Dict[str, Any] = {"agent": agent_name}
    if params:
        payload["params"] = params

    logger.info("🤖 Calling NeuralSeek mAIstro...")
    logger.info(f"   URL: {api_url}")
    logger.info(f"   Agent: {agent_name}")
    logger.info(f"   Params: {json.dumps(params, indent=2)}")

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            logger.info("✅ NeuralSeek call successful.")
            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP Error calling NeuralSeek: {e.response.status_code}")
            logger.error(f"   Response: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred during NeuralSeek call: {e}")
            raise


async def generate_question_from_context(context: str) -> Dict[str, Any]:
    """
    Generates a question using the 'make_question' agent with provided context.

    Args:
        context: A string containing the relevant chunks of text.

    Returns:
        A dictionary representing the structured question from the agent's response.
    """
    logger.info("Generating question from context using 'make_question' agent.")

    # The 'make_question' agent expects the context in the 'relevant_chunks' parameter
    agent_params = {"relevant_chunks": context}

    # Call the generic agent function
    response = await call_maistro_agent(
        agent_name=MAKE_QUESTION_AGENT, params=agent_params
    )

    # The actual question is in the 'answer' field
    try:
        answer = response.get("answer", {})

        logger.info(f"   Answer type: {type(answer)}")
        logger.info(f"   Full response keys: {response.keys()}")

        # The answer might be a JSON string or already a dict
        if isinstance(answer, str):
            # It might be wrapped in markdown ```json ... ```
            if answer.startswith("```json"):
                answer = answer.strip("```json").strip().strip("```")

            # Try to fix truncated JSON by adding missing closing characters
            if answer and not answer.rstrip().endswith("}"):
                logger.warning(
                    "   Detected potentially truncated JSON, attempting to fix..."
                )
                # Count opening and closing braces
                open_braces = answer.count("{")
                close_braces = answer.count("}")
                missing_braces = open_braces - close_braces

                # Add missing quotes if the string ends mid-value
                if answer.rstrip()[-1] not in ['"', "}", "]"]:
                    answer += '"'

                # Add missing braces
                answer += "}" * missing_braces

            structured_question = json.loads(answer)
        elif isinstance(answer, dict):
            # It's already a dictionary
            structured_question = answer
        else:
            raise ValueError(f"Unexpected answer type: {type(answer)}")

        logger.info("Successfully parsed structured question from agent response.")
        return structured_question
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(
            f"❌ Failed to parse JSON from NeuralSeek agent's 'answer' field: {e}"
        )
        logger.error(f"   Raw answer received: {response.get('answer')}")
        logger.error(f"   Full response: {json.dumps(response, indent=2)}")
        # Return a structured error response
        return {
            "error": "Failed to parse question from generation service.",
            "raw_response": response.get("answer"),
            "full_response": response,
        }
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while processing the agent response: {e}"
        )
        return {
            "error": "An unexpected error occurred.",
            "details": str(e),
        }


async def _fetch_one_question(
    client: httpx.AsyncClient, headers: Dict[str, str], topic: str
) -> Question:
    """Call NeuralSeek once and map the response to our Question model."""
    payload = {
        "agent": QUESTION_GENERATOR_AGENT,
        "params": [{"name": "chosenTopic", "value": topic}],
        "options": {"temperatureMod": 20, "maxTokens": 70},
    }
    response = await client.post(
        f"{NEURALSEEK_API_URL}/maistro", json=payload, headers=headers
    )
    print(response.json())
    response.raise_for_status()
    result = response.json()

    q_text = result.get("answer", "Could not generate a question.")
    return Question(topic=topic, question=q_text)


async def generate_questions_with_neuralseek(
    topic: Optional[str] = None, num_questions: int = 10
) -> List:
    """
    Generate multiple questions using NeuralSeek.
    If no topic is provided, randomly selects a topic for each question.

    Args:
        topic: Optional topic to generate questions about. If None, uses random topics.
        num_questions: Number of questions to generate

    Returns:
        List of Question objects
    """
    logger.info(f"🎯 Generating {num_questions} questions. Topic provided: {topic}")
    
    # Get legacy config values
    NEURALSEEK_EMBED_CODE = os.getenv("NEURALSEEK_EMBED_CODE")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {NEURALSEEK_API_KEY}",
        "embedcode": NEURALSEEK_EMBED_CODE,
        "apikey": NEURALSEEK_API_KEY,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        # Generate tasks with random topics if no topic specified
        tasks = []
        for _ in range(max(1, num_questions)):
            question_topic = topic if topic else get_random_topic()
            logger.info(f"   📚 Using topic: {question_topic}")
            tasks.append(_fetch_one_question(client, headers, question_topic))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return only Question objects
        questions = [res for res in results if isinstance(res, Question)]
        
        logger.info(f"✅ Successfully generated {len(questions)} questions")
        for q in questions:
            logger.info(f"   - {q.topic}: {q.question[:50]}...")

        return questions


async def validate_answer_with_neuralseek(
    topic: str, question_text: str, user_answer: str
) -> Dict[str, Any]:
    """
    Validate a user's answer using NeuralSeek's answer validator agent.
    This is the old topic-based approach.

    Args:
        topic: The topic of the question
        question_text: The question text
        user_answer: The user's submitted answer

    Returns:
        Dictionary with validation results (score, feedback, is_correct)
    """
    # Get legacy config values
    NEURALSEEK_EMBED_CODE = os.getenv("NEURALSEEK_EMBED_CODE")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {NEURALSEEK_API_KEY}",
        "embedcode": NEURALSEEK_EMBED_CODE or "",
    }

    try:
        parameters = {"topic": topic, "question": question_text, "answer": user_answer}
        payload = {
            "agent": ANSWER_VALIDATOR_AGENT,
            "topic": topic,
            "parameters": parameters,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{NEURALSEEK_API_URL}/maistro", json=payload, headers=headers
            )
            response.raise_for_status()
            return response.json()

    except Exception as e:
        logger.error(f"Error validating answer with NeuralSeek: {e}")
        return {
            "score": 0.5,
            "feedback": "Unable to automatically grade this answer.",
            "is_correct": None,
        }
