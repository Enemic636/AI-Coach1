import requests
import unittest
import uuid
import sys
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

    def test_send_message(self, message="שלום"):
        """Test sending a message to the AI trainer"""
        return self.run_test(
            f"Send Message: '{message}'",
            "POST",
            "chat",
            200,
            data={
                "user_id": self.user_id,
                "message": message
            }
        )

    def test_get_chat_history(self):
        """Test getting chat history"""
        return self.run_test(
            "Get Chat History",
            "GET",
            f"chat/{self.user_id}",
            200
        )

def main():
    print("=" * 50)
    print("FITNESS AI TRAINER API TEST")
    print("=" * 50)
    
    tester = FitnessAITesterAPI()
    
    # Test root endpoint
    tester.test_root_endpoint()
    
    # Test user profile
    tester.test_create_profile()
    tester.test_get_profile()
    
    # Test chat functionality with different message types
    tester.test_send_message("שלום")  # Greeting
    tester.test_send_message("רוצה תוכנית אימון כוח")  # Workout request
    tester.test_send_message("איך אני יכול לשפר את התזונה?")  # Nutrition advice
    tester.test_send_message("אני צריך מוטיבציה")  # Motivation
    
    # Test chat history
    success, chat_history = tester.test_get_chat_history()
    if success:
        print(f"Retrieved {len(chat_history)} chat messages")
    
    # Print results
    print("\n" + "=" * 50)
    print(f"RESULTS: {tester.tests_passed}/{tester.tests_run} tests passed")
    print("=" * 50)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())