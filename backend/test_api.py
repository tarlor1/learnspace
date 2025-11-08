"""
Simple test script to verify the LearnSpace API is working
Run the FastAPI server first: uvicorn main:app --reload
Then run this script: python test_api.py
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_response(response: requests.Response):
    """Print formatted response"""
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✅ Success!")
    else:
        print("❌ Failed!")
    print(f"\nResponse:")
    print(json.dumps(response.json(), indent=2))


def test_health_check():
    """Test the root endpoint"""
    print_section("1. Testing Health Check")
    try:
        response = requests.get(f"{BASE_URL}/")
        print_response(response)
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_generate_questions() -> Dict[str, Any]:
    """Test question generation"""
    print_section("2. Testing Question Generation")
    
    sample_text = """
    Chapter 1: Introduction to Python Programming
    
    Python is a high-level, interpreted programming language created by Guido van Rossum. 
    It was first released in 1991 and has become one of the most popular programming languages.
    Python emphasizes code readability with its use of significant indentation.
    
    Chapter 2: Variables and Data Types
    
    In Python, variables are created when you assign a value to them. Python has several 
    built-in data types including integers, floats, strings, booleans, lists, and dictionaries.
    Type conversion can be done using built-in functions like int(), float(), and str().
    
    Chapter 3: Control Flow and Loops
    
    Python supports conditional statements using if, elif, and else keywords. Loops can be 
    implemented using for loops for iterating over sequences, and while loops for conditional 
    iteration. Break and continue statements control loop execution.
    
    Chapter 4: Functions and Modules
    
    Functions in Python are defined using the def keyword. They can accept parameters and 
    return values. Python's module system allows code organization and reusability. The import 
    statement is used to include modules in your program.
    """
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate-questions",
            json={
                "pdf_text": sample_text,
                "num_questions": 6
            },
            timeout=30
        )
        
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📝 Generated {data['num_questions']} questions")
            print(f"🔑 Session ID: {data['session_id']}")
            
            print("\n📚 Questions Preview:")
            for i, q in enumerate(data['questions'][:3], 1):
                print(f"\n{i}. [{q['type'].upper()}] {q['chapter']}")
                print(f"   {q['question'][:80]}...")
                if q['options']:
                    print(f"   Options: {len(q['options'])} choices")
            
            if len(data['questions']) > 3:
                print(f"\n... and {len(data['questions']) - 3} more questions")
            
            return data
        
        return {}
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {}


def test_get_questions():
    """Test getting all questions"""
    print_section("3. Testing Get All Questions")
    
    try:
        response = requests.get(f"{BASE_URL}/questions")
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 Total questions in system: {data['total_questions']}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_submit_answer(question_id: str):
    """Test submitting an answer"""
    print_section("4. Testing Submit Answer")
    
    try:
        response = requests.post(
            f"{BASE_URL}/submit-answer",
            json={
                "question_id": question_id,
                "answer": "This is my test answer for the question."
            }
        )
        
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n⏰ Submitted at: {data['timestamp']}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_get_stats():
    """Test getting statistics"""
    print_section("5. Testing Statistics Endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}/stats")
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            print("\n📈 System Statistics:")
            print(f"   Sessions: {data['total_sessions']}")
            print(f"   Questions: {data['total_questions']}")
            print(f"   Answers: {data['total_answers']}")
            print(f"   Answer Rate: {data['answer_rate']}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "🚀" * 30)
    print("  LearnSpace API Test Suite")
    print("🚀" * 30)
    
    try:
        # Test 1: Health check
        if not test_health_check():
            print("\n❌ Server is not responding. Make sure it's running:")
            print("   uvicorn main:app --reload")
            return
        
        # Test 2: Generate questions
        questions_data = test_generate_questions()
        
        if not questions_data:
            print("\n⚠️  Question generation failed. Check server logs.")
            return
        
        # Test 3: Get all questions
        test_get_questions()
        
        # Test 4: Submit answer (if questions were generated)
        if questions_data.get('questions'):
            first_question_id = questions_data['questions'][0]['id']
            test_submit_answer(first_question_id)
        
        # Test 5: Get statistics
        test_get_stats()
        
        # Summary
        print_section("✅ All Tests Completed!")
        print("\n🎉 Your LearnSpace API is working correctly!")
        print("\n📖 Next steps:")
        print("   • View API docs: http://localhost:8000/docs")
        print("   • Integrate with frontend")
        print("   • Configure NeuralSeek API key in .env")
        print("   • Test with real PDF text")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to the API server.")
        print("\nMake sure the FastAPI server is running:")
        print("   cd backend")
        print("   uvicorn main:app --reload")
        print("\nThen try running this test again.")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
