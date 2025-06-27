import requests
import sys
import uuid
from datetime import datetime

class FitnessAITesterAPI:
    def __init__(self, base_url="https://227f84f8-8e50-4282-ad85-bd314b6e4bc5.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = f"test_user_{uuid.uuid4()}"

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.text}")
                    return False, response.json()
                except:
                    return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )

    def test_create_profile(self):
        """Test creating a user profile"""
        return self.run_test(
            "Create User Profile",
            "POST",
            "profile",
            200,
            data={
                "user_id": self.user_id,
                "name": "Test User",
                "fitness_level": "intermediate",
                "goals": ["strength", "endurance"]
            }
        )

    def test_get_profile(self):
        """Test getting a user profile"""
        return self.run_test(
            "Get User Profile",
            "GET",
            f"profile/{self.user_id}",
            200
        )

    def test_send_message(self, message, description=None):
        """Test sending a message to the AI trainer"""
        test_name = f"Send Message: '{message}'"
        if description:
            test_name += f" ({description})"
            
        success, response = self.run_test(
            test_name,
            "POST",
            "chat",
            200,
            data={
                "user_id": self.user_id,
                "message": message
            }
        )
        
        if success:
            # Analyze response quality
            ai_response = response.get('response', '')
            print(f"\n📝 AI Response Preview (first 150 chars): {ai_response[:150]}...")
            
            # Check if response is in Hebrew
            has_hebrew = any('\u0590' <= c <= '\u05FF' for c in ai_response)
            if has_hebrew:
                print("✅ Response is in Hebrew")
            else:
                print("❌ Response is NOT in Hebrew")
                success = False
            
            # Check response length (detailed responses should be substantial)
            if len(ai_response) > 300:
                print(f"✅ Response is detailed ({len(ai_response)} characters)")
            else:
                print(f"❌ Response is too short ({len(ai_response)} characters)")
                success = False
                
            # Check for analysis indicators
            analysis_indicators = ["ניתוח", "אני מבין", "לפי מה שאתה אומר", "בהתבסס על"]
            has_analysis = any(indicator in ai_response for indicator in analysis_indicators)
            if has_analysis:
                print("✅ Response includes analysis")
            else:
                print("❌ Response lacks analysis")
                success = False
                
            # Check for specific advice
            specific_indicators = ["לדוגמה", "ספציפית", "מומלץ", "כדאי", "תוכנית", "תרגיל"]
            has_specific_advice = any(indicator in ai_response for indicator in specific_indicators)
            if has_specific_advice:
                print("✅ Response includes specific advice")
            else:
                print("❌ Response lacks specific advice")
                success = False
                
            # Check for follow-up questions
            question_indicators = ["?", "האם", "מה", "איך", "כמה"]
            has_questions = any(indicator in ai_response for indicator in question_indicators)
            if has_questions:
                print("✅ Response includes follow-up questions")
            else:
                print("❌ Response lacks follow-up questions")
                success = False
                
            if success:
                print("✅ Overall response quality is good")
            else:
                print("❌ Response quality needs improvement")
                self.tests_passed -= 1  # Decrement because we initially incremented on HTTP success
                
        return success, response

    def test_get_chat_history(self):
        """Test getting chat history"""
        return self.run_test(
            "Get Chat History",
            "GET",
            f"chat/{self.user_id}",
            200
        )

def main():
    print("=" * 70)
    print("FITNESS AI TRAINER API TEST - ENHANCED QUALITY CHECK")
    print("=" * 70)
    
    tester = FitnessAITesterAPI()
    
    # Test root endpoint
    tester.test_root_endpoint()
    
    # Test user profile
    tester.test_create_profile()
    tester.test_get_profile()
    
    # Test specific scenarios from the review request
    print("\n" + "=" * 70)
    print("TESTING SPECIFIC SCENARIOS")
    print("=" * 70)
    
    # 1. Greeting message
    tester.test_send_message("שלום! אני רוצה להתחיל להתאמן", "Greeting")
    
    # 2. Professional advice request
    tester.test_send_message(
        "אני רוצה לרדת במשקל ולבנות שריר. בן 25, משקל 80 ק\"ג, גובה 175, עובד בישיבה", 
        "Professional advice"
    )
    
    # 3. Workout plan request
    tester.test_send_message(
        "תן לי תוכנית אימון של 3 פעמים בשבוע לחדר כושר", 
        "Workout plan"
    )
    
    # 4. Nutrition advice request
    tester.test_send_message(
        "איך אני צריך לאכול כדי לרדת במשקל אבל לשמור על שריר?", 
        "Nutrition advice"
    )
    
    # Test chat history
    success, chat_history = tester.test_get_chat_history()
    if success:
        print(f"Retrieved {len(chat_history)} chat messages")
    
    # Print results
    print("\n" + "=" * 70)
    print(f"RESULTS: {tester.tests_passed}/{tester.tests_run} tests passed")
    print("=" * 70)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())