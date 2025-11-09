"""
Test script to directly call the question_maker agent and see the raw response
"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils import call_maistro_agent


async def test_question_maker_agent():
    """Test the question_maker agent with sample context"""

    print("\n" + "=" * 80)
    print("🧪 TESTING QUESTION_MAKER AGENT DIRECTLY")
    print("=" * 80)

    # Sample context
    sample_context = """
    Python is a high-level, interpreted programming language known for its simplicity
    and readability. It uses indentation to define code blocks and supports multiple
    programming paradigms including procedural, object-oriented, and functional programming.

    Python was created by Guido van Rossum and first released in 1991. The language
    emphasizes code readability with its notable use of significant whitespace.
    """

    print("\n📝 Sample Context:")
    print("-" * 80)
    print(sample_context)
    print()

    print("🤖 Calling question_maker agent...")
    print("-" * 80)

    try:
        response = await call_maistro_agent(
            agent_name="question_maker", params={"relevant_chunks": sample_context}
        )

        print("\n✅ Response received!")
        print("=" * 80)
        print(json.dumps(response, indent=2))
        print("=" * 80)

        # Parse the answer
        answer = response.get("answer", {})
        if isinstance(answer, str):
            try:
                parsed = json.loads(answer)
                print("\n📋 Parsed Answer:")
                print(json.dumps(parsed, indent=2))
            except json.JSONDecodeError as e:
                print(f"\n⚠️  Could not parse answer as JSON: {e}")
                print(f"Raw answer: {answer}")
        else:
            print(f"\n⚠️  Answer is not a string, it's: {type(answer)}")
            print(f"Content: {answer}")

        # Check for empty response
        if answer == "{}" or answer == {}:
            print("\n❌ PROBLEM DETECTED: Agent returned empty response!")
            print("\nThis means the agent is NOT properly configured in NeuralSeek.")
            print("\nTO FIX:")
            print("1. Login to https://stagingapi.neuralseek.com")
            print("2. Go to mAIstro agents")
            print("3. Find 'question_maker' agent")
            print("4. Add NTL script with <<Explore>> command")
            print("5. Ensure it's connected to an LLM")
            print("6. Test it in the NeuralSeek interface first")

    except Exception as e:
        print(f"\n❌ Error calling agent: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_question_maker_agent())
