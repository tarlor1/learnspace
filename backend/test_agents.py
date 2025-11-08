"""
NeuralSeek Agent Configuration Test Script

This script tests your NeuralSeek agent configuration to ensure
all agents are properly set up and responding correctly.

Run this BEFORE starting the FastAPI server to verify your setup.
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import utilities (make sure utils.py is in the same directory)
try:
    from utils import (
        call_neuralseek_agent,
        QUESTION_GENERATOR_AGENT,
        ANSWER_VALIDATOR_AGENT,
        CONTENT_ANALYZER_AGENT,
        NEURALSEEK_API_URL,
        NEURALSEEK_API_KEY
    )
except ImportError:
    print("❌ Error: Could not import utils.py. Make sure you're in the backend directory.")
    sys.exit(1)


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_config():
    """Print current configuration"""
    print_header("📋 Current Configuration")
    print(f"API URL: {NEURALSEEK_API_URL}")
    print(f"API Key: {'*' * 20}{NEURALSEEK_API_KEY[-4:] if len(NEURALSEEK_API_KEY) > 4 else '****'}")
    print(f"\nConfigured Agents:")
    print(f"  1. Question Generator: {QUESTION_GENERATOR_AGENT}")
    print(f"  2. Answer Validator:   {ANSWER_VALIDATOR_AGENT}")
    print(f"  3. Content Analyzer:   {CONTENT_ANALYZER_AGENT}")


async def test_question_generator():
    """Test the Question Generator Agent"""
    print_header("🧪 Testing Question Generator Agent")
    
    test_text = """
    Chapter 1: Introduction to Python
    Python is a high-level programming language known for its simplicity and readability.
    It supports multiple programming paradigms including procedural, object-oriented, and functional programming.
    Python was created by Guido van Rossum and first released in 1991.
    """
    
    try:
        print(f"🤖 Calling agent: {QUESTION_GENERATOR_AGENT}")
        print(f"📝 Test context: {len(test_text)} characters")
        
        response = await call_neuralseek_agent(
            agent_name=QUESTION_GENERATOR_AGENT,
            query="Generate 3 study questions from this text: 1 short response, 1 MCQ with 4 options, and 1 index card.",
            context=test_text,
            parameters={"num_questions": 3, "temperature": 0.7, "format": "json"}
        )
        
        print("✅ Agent responded successfully!")
        print(f"📦 Response keys: {list(response.keys())}")
        
        # Try to display a preview of the response
        if 'output' in response:
            print(f"📄 Output preview: {str(response['output'])[:200]}...")
        elif 'result' in response:
            print(f"📄 Result preview: {str(response['result'])[:200]}...")
        else:
            print(f"📄 Response preview: {str(response)[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n💡 Troubleshooting tips:")
        print(f"   • Verify agent '{QUESTION_GENERATOR_AGENT}' exists in NeuralSeek")
        print(f"   • Check agent is configured to return JSON format")
        print(f"   • Ensure API key has permissions to invoke this agent")
        return False


async def test_answer_validator():
    """Test the Answer Validator Agent"""
    print_header("🧪 Testing Answer Validator Agent")
    
    test_question = "What is Python?"
    test_answer = "Python is a high-level programming language."
    
    try:
        print(f"🤖 Calling agent: {ANSWER_VALIDATOR_AGENT}")
        print(f"❓ Test question: {test_question}")
        print(f"✍️  Test answer: {test_answer}")
        
        query = f"""Evaluate this answer:
Question: {test_question}
Answer: {test_answer}

Return JSON with score (0-1), feedback, and is_correct (true/false)."""
        
        response = await call_neuralseek_agent(
            agent_name=ANSWER_VALIDATOR_AGENT,
            query=query,
            context="Python is a programming language created by Guido van Rossum.",
            parameters={"temperature": 0.3, "format": "json"}
        )
        
        print("✅ Agent responded successfully!")
        print(f"📦 Response keys: {list(response.keys())}")
        
        # Try to display validation result
        if 'output' in response:
            print(f"📄 Output preview: {str(response['output'])[:200]}...")
        elif 'result' in response:
            print(f"📄 Result preview: {str(response['result'])[:200]}...")
        else:
            print(f"📄 Response preview: {str(response)[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n💡 Troubleshooting tips:")
        print(f"   • Verify agent '{ANSWER_VALIDATOR_AGENT}' exists in NeuralSeek")
        print(f"   • Check agent is configured to return JSON format")
        print(f"   • Ensure API key has permissions to invoke this agent")
        return False


async def test_content_analyzer():
    """Test the Content Analyzer Agent"""
    print_header("🧪 Testing Content Analyzer Agent")
    
    test_text = """
    Chapter 1: Variables and Data Types
    Variables store data. Python has int, float, str, and bool types.
    
    Chapter 2: Control Flow
    Use if, elif, else for conditions. Use for and while for loops.
    """
    
    try:
        print(f"🤖 Calling agent: {CONTENT_ANALYZER_AGENT}")
        print(f"📝 Test context: {len(test_text)} characters")
        
        query = """Analyze this content and return JSON with:
- chapters (list)
- difficulty_level (beginner/intermediate/advanced)
- recommended_questions (number)"""
        
        response = await call_neuralseek_agent(
            agent_name=CONTENT_ANALYZER_AGENT,
            query=query,
            context=test_text,
            parameters={"temperature": 0.5, "format": "json"}
        )
        
        print("✅ Agent responded successfully!")
        print(f"📦 Response keys: {list(response.keys())}")
        
        # Try to display analysis result
        if 'output' in response:
            print(f"📄 Output preview: {str(response['output'])[:200]}...")
        elif 'result' in response:
            print(f"📄 Result preview: {str(response['result'])[:200]}...")
        else:
            print(f"📄 Response preview: {str(response)[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n💡 Troubleshooting tips:")
        print(f"   • Verify agent '{CONTENT_ANALYZER_AGENT}' exists in NeuralSeek")
        print(f"   • Check agent is configured to return JSON format")
        print(f"   • Ensure API key has permissions to invoke this agent")
        return False


async def main():
    """Run all agent tests"""
    print("\n" + "🚀" * 35)
    print("  NeuralSeek Agent Configuration Test")
    print("🚀" * 35)
    
    # Check environment variables
    if NEURALSEEK_API_KEY == "your-api-key-here":
        print("\n❌ ERROR: Please configure your NEURALSEEK_API_KEY in .env file")
        print("\nSteps:")
        print("  1. Copy .env.example to .env")
        print("  2. Edit .env and add your actual API key")
        print("  3. Run this script again")
        return
    
    # Print current configuration
    print_config()
    
    # Run tests
    results = {
        "Question Generator": await test_question_generator(),
        "Answer Validator": await test_answer_validator(),
        "Content Analyzer": await test_content_analyzer()
    }
    
    # Summary
    print_header("📊 Test Summary")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)
    
    for agent_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {agent_name}")
    
    print(f"\n{passed_tests}/{total_tests} agents configured correctly")
    
    if passed_tests == total_tests:
        print("\n🎉 SUCCESS! All agents are working correctly.")
        print("\nYou can now start the FastAPI server:")
        print("  uvicorn main:app --reload")
    else:
        print("\n⚠️  Some agents failed. Please review the errors above.")
        print("\n📖 See AGENTS.md for detailed configuration instructions.")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        print("\n📖 Check AGENTS.md for troubleshooting help")
