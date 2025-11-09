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


# --- NeuralSeek API Configuration ---
NEURALSEEK_API_URL = os.getenv("NEURALSEEK_API_URL")
NEURALSEEK_API_KEY = os.getenv("NEURALSEEK_API_KEY")
NEURALSEEK_INSTANCE_ID = os.getenv("NEURALSEEK_INSTANCE_ID")

# Agent Names
MAKE_QUESTION_AGENT = os.getenv("MAKE_QUESTION_AGENT", "question_maker")
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

# --- Neo4j Configuration ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

from neo4j import GraphDatabase
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
logger.info(f"✅ Neo4j connection established: {NEO4J_URI}")


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
    if params and "relevant_chunks" in params:
        logger.info(f"   Context length: {len(params['relevant_chunks'])} characters")
        logger.info(f"   Context preview: {params['relevant_chunks'][:200]}...")
    else:
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


def get_random_chunks_from_documents(document_ids: List[str], num_chunks: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch random chunks from Neo4j for the given document IDs.

    Args:
        document_ids: List of document UUIDs to query
        num_chunks: Number of random chunks to fetch

    Returns:
        List of chunk dictionaries with text, document_id, chunk_index, chapter_id
    """
    if not document_ids:
        logger.warning("No document IDs provided for chunk retrieval")
        return []

    logger.info(f"🔍 Fetching {num_chunks} random chunks from {len(document_ids)} documents")

    with neo4j_driver.session() as session:
        # Query random chunks from the specified documents
        result = session.run(
            """
            MATCH (c:Chunk)-[:PART_OF]->(d:Document)
            WHERE d.id IN $doc_ids
            WITH c, rand() AS random
            ORDER BY random
            LIMIT $limit
            RETURN c.text AS text,
                   c.document_id AS document_id,
                   c.chunk_index AS chunk_index,
                   c.chapter_id AS chapter_id
            """,
            doc_ids=document_ids,
            limit=num_chunks
        )

        chunks = []
        for record in result:
            chunks.append({
                "text": record["text"],
                "document_id": record["document_id"],
                "chunk_index": record["chunk_index"],
                "chapter_id": record["chapter_id"]
            })

        logger.info(f"✅ Retrieved {len(chunks)} random chunks")
        return chunks


async def generate_topics_from_context(context: str) -> List[str]:
    """
    Generates topics using the 'topic_generator' agent with provided context.

    Args:
        context: A string containing the relevant chunks of text.

    Returns:
        List of 5 topic strings generated from the context.
    """
    logger.info("Generating topics from context using 'topic_generator' agent.")

    # The 'topic_generator' agent expects the context in the 'relevant_chunks' parameter
    agent_params = {"relevant_chunks": context}

    # Call the generic agent function
    response = await call_maistro_agent(
        agent_name="topic_generator", params=agent_params
    )

    try:
        # Response format: {"topic": ["Topic 1", "Topic 2", "Topic 3", "Topic 4", "Topic 5"]}
        print(f"\n🔍 DEBUG: Full topic_generator response:")
        print(f"   Type: {type(response)}")
        print(f"   Keys: {response.keys() if isinstance(response, dict) else 'N/A'}")
        print(f"   Full response: {json.dumps(response, indent=2)}\n")

        answer = response.get("answer", {})

        print(f"🔍 DEBUG: Answer field:")
        print(f"   Type: {type(answer)}")
        print(f"   Content: {answer}\n")

        if isinstance(answer, str):
            # Parse JSON string if needed
            print(f"🔍 DEBUG: Parsing answer as JSON string...")
            answer = json.loads(answer)
            print(f"   Parsed result: {answer}\n")

        topics = answer.get("topic", [])

        print(f"🔍 DEBUG: Extracted topics:")
        print(f"   Type: {type(topics)}")
        print(f"   Count: {len(topics) if isinstance(topics, list) else 'N/A'}")
        print(f"   Content: {topics}\n")

        # Check if answer is empty dict or topics is empty
        if isinstance(answer, dict) and not answer:
            logger.error(f"❌ topic_generator returned empty response. This likely means the agent is not properly configured in NeuralSeek.")
            logger.error(f"   Please check the 'topic_generator' agent configuration in the NeuralSeek dashboard.")
            return []

        if not isinstance(topics, list) or len(topics) == 0:
            logger.warning(f"No topics returned from topic_generator. Response: {answer}")
            return []

        logger.info(f"✅ Generated {len(topics)} topics from context")
        for i, topic in enumerate(topics, 1):
            logger.info(f"   {i}. {topic}")

        return topics

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"❌ Failed to parse topics from response: {e}")
        logger.error(f"   Raw answer: {response.get('answer')}")
        return []
    except Exception as e:
        logger.error(f"❌ Unexpected error parsing topics: {e}")
        return []


async def generate_question_from_context(context: str, topic: Optional[str] = None) -> Dict[str, Any]:
    """
    Generates a question using the 'question_maker' agent with provided context.

    Args:
        context: A string containing the relevant chunks of text.
        topic: Optional specific topic to generate a question about.

    Returns:
        A dictionary representing the structured question from the agent's response.
    """
    logger.info("Generating question from context using 'question_maker' agent.")

    if topic:
        logger.info(f"   Using topic: {topic}")

    # The 'question_maker' agent expects the context in the 'relevant_chunks' parameter
    # According to the OpenAPI spec, it needs relevant_chunks
    agent_params = {
        "relevant_chunks": context,
    }

    # If topic is provided, add it to the context
    if topic:
        agent_params["relevant_chunks"] = f"Topic: {topic}\n\nContext:\n{context}"

    # Call the generic agent function
    response = await call_maistro_agent(
        agent_name=MAKE_QUESTION_AGENT, params=agent_params
    )

    # The actual question is in the 'answer' field
    try:
        print(f"\n🔍 DEBUG: Full question_maker response:")
        print(f"   Type: {type(response)}")
        print(f"   Keys: {response.keys() if isinstance(response, dict) else 'N/A'}")
        print(f"   Full response: {json.dumps(response, indent=2)}\n")

        answer = response.get("answer", {})

        print(f"🔍 DEBUG: Answer field:")
        print(f"   Type: {type(answer)}")
        print(f"   Content: {answer}\n")

        # The answer might be a JSON string or already a dict
        if isinstance(answer, str):
            # Strip any whitespace
            answer = answer.strip()

            # It might be wrapped in markdown ```json ... ``` or ```
            if answer.startswith("```json"):
                print(f"🔍 DEBUG: Stripping markdown ```json markers...")
                answer = answer[7:].strip()  # Remove ```json
                if answer.endswith("```"):
                    answer = answer[:-3].strip()
            elif answer.startswith("```"):
                print(f"🔍 DEBUG: Stripping markdown ``` markers...")
                answer = answer[3:].strip()  # Remove ```
                if answer.endswith("```"):
                    answer = answer[:-3].strip()

            print(f"🔍 DEBUG: Cleaned answer for parsing:")
            print(f"   First 200 chars: {answer[:200]}")
            print(f"   Last 200 chars: {answer[-200:]}\n")

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

            print(f"🔍 DEBUG: Parsing answer as JSON...")
            structured_question = json.loads(answer)
            print(f"   Parsed question: {json.dumps(structured_question, indent=2)}\n")
        elif isinstance(answer, dict):
            # It's already a dictionary
            print(f"🔍 DEBUG: Answer is already a dict")
            structured_question = answer
        else:
            raise ValueError(f"Unexpected answer type: {type(answer)}")

        # Check if the response is empty
        if not structured_question or structured_question == {}:
            logger.error("❌ question_maker agent returned empty response")
            logger.error("   This likely means the agent is not properly configured in NeuralSeek.")
            logger.error("   Please check the 'question_maker' agent in the NeuralSeek dashboard.")
            logger.error(f"   Full response was: {json.dumps(response, indent=2)}")
            return {
                "error": "question_maker agent returned empty response. Please check agent configuration in NeuralSeek.",
                "raw_response": response.get("answer"),
                "full_response": response,
            }

        # Validate the expected structure
        # Expected format: {"topic": "...", "correct_answer": "...", "content": {"type": "...", "text": "..."}}
        if "content" not in structured_question:
            logger.warning(f"⚠️  Response missing 'content' field. Got: {structured_question.keys()}")
        if "topic" not in structured_question:
            logger.warning(f"⚠️  Response missing 'topic' field. Got: {structured_question.keys()}")
        if "correct_answer" not in structured_question:
            logger.warning(f"⚠️  Response missing 'correct_answer' field. Got: {structured_question.keys()}")

        logger.info("Successfully parsed structured question from agent response.")
        logger.info(f"   Topic: {structured_question.get('topic', 'N/A')}")
        logger.info(f"   Has content: {bool(structured_question.get('content'))}")
        logger.info(f"   Has correct_answer: {bool(structured_question.get('correct_answer'))}")

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


async def generate_questions_from_user_documents(
    document_ids: List[str], num_questions: int = 10
) -> List[Dict[str, Any]]:
    """
    Generate questions based on random chunks from the user's documents.
    Uses NeuralSeek topic_generator to identify topics from chunks, then
    uses question_maker agent to generate questions about those topics.

    Args:
        document_ids: List of document UUIDs to generate questions from
        num_questions: Number of questions to generate

    Returns:
        List of question dictionaries with content and metadata
    """
    logger.info(f"🎯 Generating {num_questions} questions from user documents")

    if not document_ids:
        logger.warning("No documents provided for question generation")
        return []

    # Fetch random chunks from the user's documents
    # Get enough chunks to extract topics from
    num_chunk_groups = (num_questions + 4) // 5  # Each topic_generator call returns 5 topics
    chunks = get_random_chunks_from_documents(document_ids, num_chunks=num_chunk_groups * 5)

    if not chunks:
        logger.warning("No chunks found in user documents")
        return []

    questions = []

    # Process chunks in groups to generate topics
    for group_idx in range(num_chunk_groups):
        start_idx = group_idx * 5
        end_idx = min(start_idx + 5, len(chunks))
        context_chunks = chunks[start_idx:end_idx]

        if not context_chunks:
            continue

        # Combine chunks into context for topic generation
        context = "\n\n".join([chunk["text"] for chunk in context_chunks])

        logger.info(f"   � Generating topics from chunk group {group_idx + 1}")

        try:
            # Step 1: Generate topics from the context
            topics = await generate_topics_from_context(context)

            if not topics:
                logger.warning(f"   No topics generated for group {group_idx + 1}, skipping")
                continue

            # Step 2: Generate questions for each topic
            for topic_idx, topic in enumerate(topics):
                if len(questions) >= num_questions:
                    break

                logger.info(f"   📝 Generating question {len(questions)+1}/{num_questions} about: {topic}")

                try:
                    # Call question_maker agent with the context and topic
                    question_data = await generate_question_from_context(context, topic=topic)

                    # Add metadata about source
                    question_data["document_id"] = context_chunks[0]["document_id"]
                    question_data["chapter_id"] = context_chunks[0].get("chapter_id")
                    question_data["source_chunks"] = [c["chunk_index"] for c in context_chunks]
                    question_data["topic"] = topic  # Store the generated topic

                    questions.append(question_data)

                except Exception as e:
                    logger.error(f"   ❌ Failed to generate question for topic '{topic}': {e}")
                    continue

            if len(questions) >= num_questions:
                break

        except Exception as e:
            logger.error(f"   ❌ Failed to process chunk group {group_idx + 1}: {e}")
            continue

    logger.info(f"✅ Successfully generated {len(questions)} questions from documents")
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
