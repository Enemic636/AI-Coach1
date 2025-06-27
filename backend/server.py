from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import json
import random
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

# Fitness AI Knowledge Base
class FitnessAI:
    def __init__(self):
        self.workouts = {
            "beginner": {
                "strength": [
                    {"name": "Push-ups", "sets": 3, "reps": "8-12", "rest": "60s"},
                    {"name": "Squats", "sets": 3, "reps": "10-15", "rest": "60s"},
                    {"name": "Lunges", "sets": 3, "reps": "8-10 each leg", "rest": "60s"},
                    {"name": "Plank", "sets": 3, "reps": "20-30s", "rest": "45s"}
                ],
                "cardio": [
                    {"name": "Walking", "duration": "20-30 min", "intensity": "moderate"},
                    {"name": "Stationary bike", "duration": "15-20 min", "intensity": "light"},
                    {"name": "Swimming", "duration": "15-20 min", "intensity": "light"}
                ]
            },
            "intermediate": {
                "strength": [
                    {"name": "Push-ups", "sets": 4, "reps": "12-15", "rest": "45s"},
                    {"name": "Squats", "sets": 4, "reps": "15-20", "rest": "45s"},
                    {"name": "Burpees", "sets": 3, "reps": "8-12", "rest": "60s"},
                    {"name": "Mountain climbers", "sets": 3, "reps": "30s", "rest": "45s"},
                    {"name": "Deadlifts", "sets": 4, "reps": "10-12", "rest": "60s"}
                ],
                "cardio": [
                    {"name": "Running", "duration": "25-35 min", "intensity": "moderate"},
                    {"name": "HIIT", "duration": "20-25 min", "intensity": "high"},
                    {"name": "Cycling", "duration": "30-40 min", "intensity": "moderate"}
                ]
            },
            "advanced": {
                "strength": [
                    {"name": "Weighted squats", "sets": 5, "reps": "8-12", "rest": "90s"},
                    {"name": "Pull-ups", "sets": 4, "reps": "8-15", "rest": "60s"},
                    {"name": "Deadlifts", "sets": 5, "reps": "6-10", "rest": "90s"},
                    {"name": "Bench press", "sets": 4, "reps": "8-12", "rest": "90s"},
                    {"name": "Overhead press", "sets": 4, "reps": "8-10", "rest": "90s"}
                ],
                "cardio": [
                    {"name": "Running", "duration": "45-60 min", "intensity": "moderate-high"},
                    {"name": "HIIT", "duration": "30-40 min", "intensity": "high"},
                    {"name": "Boxing", "duration": "45-60 min", "intensity": "high"}
                ]
            }
        }
        
        self.nutrition_tips = [
            "שתה לפחות 8 כוסות מים ביום",
            "כלול חלבון בכל ארוחה",
            "אכל 5-6 פעמים ביום במנות קטנות",
            "הימנע מסוכר מעובד",
            "אכל ירקות בכל ארוחה",
            "אל תדלג על ארוחת בוקר",
            "אכל פחמימות מורכבות",
            "הוסף אומגה 3 לתזונה"
        ]
        
        self.motivational_quotes = [
            "כל יום הוא הזדמנות להיות חזק יותר! 💪",
            "אתה חזק יותר ממה שאתה חושב! 🔥",
            "ההתקדמות הטובה ביותר היא התקדמות עקבית! ⭐",
            "הדרך היחידה לכישלון היא להפסיק לנסות! 🎯",
            "הגוף שלך יכול לעשות הכל - הראש שלך הוא שצריך לשכנע! 🧠",
            "כל אימון מקרב אותך ליעד! 🏆"
        ]

    def get_workout_plan(self, level: str, workout_type: str) -> List[Dict]:
        return self.workouts.get(level, {}).get(workout_type, [])
    
    def get_nutrition_tip(self) -> str:
        return random.choice(self.nutrition_tips)
    
    def get_motivation(self) -> str:
        return random.choice(self.motivational_quotes)
    
    def analyze_message(self, message: str) -> Dict[str, Any]:
        message_lower = message.lower()
        
        # Intent detection
        if any(word in message_lower for word in ["תרגיל", "אימון", "workout", "exercise"]):
            return {"intent": "workout", "confidence": 0.9}
        elif any(word in message_lower for word in ["תזונה", "דיאטה", "nutrition", "diet", "אוכל"]):
            return {"intent": "nutrition", "confidence": 0.9}
        elif any(word in message_lower for word in ["מוטיבציה", "עצוב", "motivation", "tired", "עייף"]):
            return {"intent": "motivation", "confidence": 0.9}
        elif any(word in message_lower for word in ["שלום", "היי", "hello", "hi"]):
            return {"intent": "greeting", "confidence": 0.9}
        elif any(word in message_lower for word in ["עזרה", "help", "מה אתה יכול"]):
            return {"intent": "help", "confidence": 0.9}
        else:
            return {"intent": "general", "confidence": 0.5}

    def generate_response(self, message: str, user_profile: Dict = None) -> str:
        analysis = self.analyze_message(message)
        intent = analysis["intent"]
        
        if intent == "greeting":
            return "שלום! 👋 אני המאמן הכושר הדיגיטלי שלך! איך אני יכול לעזור לך היום? אני יכול לתת לך תוכניות אימון, עצות תזונה, או פשוט לעודד אותך! 💪"
        
        elif intent == "workout":
            level = user_profile.get("fitness_level", "beginner") if user_profile else "beginner"
            workout_type = "strength" if any(word in message.lower() for word in ["כוח", "strength", "משקולות"]) else "cardio"
            
            workout_plan = self.get_workout_plan(level, workout_type)
            if workout_plan:
                response = f"הנה תוכנית אימון {workout_type} ברמה {level}:\n\n"
                for i, exercise in enumerate(workout_plan, 1):
                    if workout_type == "strength":
                        response += f"{i}. {exercise['name']}\n"
                        response += f"   סטים: {exercise['sets']} | חזרות: {exercise['reps']} | מנוחה: {exercise['rest']}\n\n"
                    else:
                        response += f"{i}. {exercise['name']}\n"
                        response += f"   משך: {exercise['duration']} | עצימות: {exercise['intensity']}\n\n"
                response += "בהצלחה! 🔥 אם תרצה עוד עזרה, אני כאן!"
                return response
            else:
                return "אני יכול לעזור לך עם תוכניות אימון! ספר לי איזה סוג אימון אתה מחפש - כוח או קרדיו?"
        
        elif intent == "nutrition":
            tip = self.get_nutrition_tip()
            return f"💡 עצה תזונתית:\n{tip}\n\nזכור, תזונה נכונה היא 70% מההצלחה בכושר! האם יש שאלה ספציפית על תזונה?"
        
        elif intent == "motivation":
            motivation = self.get_motivation()
            return f"{motivation}\n\nאני מאמין בך! כל צעד קטן מוביל לשינוי גדול. איך אני יכול לעזור לך להמשיך?"
        
        elif intent == "help":
            return """🤖 אני המאמן הדיגיטלי שלך! אני יכול לעזור לך עם:

💪 תוכניות אימון מותאמות אישית
🥗 עצות תזונה
🔥 מוטיבציה ועידוד
📊 מעקב אחר התקדמות
🎯 קביעת יעדים

פשוט ספר לי מה אתה רוצה לעשות או איך אתה מרגיש, ואני אעזור לך!"""
        
        else:
            return "אני כאן לעזור לך עם כושר ותזונה! ספר לי איך אני יכול לעזור - אימון, תזונה, או סתם עידוד? 😊"

fitness_ai = FitnessAI()

# Pydantic Models
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    message: str
    response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_type: str = "user"  # user or ai

class ChatMessageCreate(BaseModel):
    user_id: str
    message: str

class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    age: Optional[int] = None
    fitness_level: str = "beginner"  # beginner, intermediate, advanced
    goals: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserProfileCreate(BaseModel):
    user_id: str
    name: str
    age: Optional[int] = None
    fitness_level: str = "beginner"
    goals: List[str] = []

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Fitness AI Trainer API"}

@api_router.post("/chat", response_model=ChatMessage)
async def send_message(input: ChatMessageCreate):
    # Get user profile
    user_profile_doc = await db.user_profiles.find_one({"user_id": input.user_id})
    user_profile = user_profile_doc if user_profile_doc else {}
    
    # Generate AI response
    ai_response = fitness_ai.generate_response(input.message, user_profile)
    
    # Create chat message
    chat_message = ChatMessage(
        user_id=input.user_id,
        message=input.message,
        response=ai_response
    )
    
    # Save to database
    await db.chat_messages.insert_one(chat_message.dict())
    
    return chat_message

@api_router.get("/chat/{user_id}", response_model=List[ChatMessage])
async def get_chat_history(user_id: str):
    messages = await db.chat_messages.find({"user_id": user_id}).sort("timestamp", -1).limit(50).to_list(50)
    return [ChatMessage(**msg) for msg in messages]

@api_router.post("/profile", response_model=UserProfile)
async def create_user_profile(input: UserProfileCreate):
    # Check if profile exists
    existing_profile = await db.user_profiles.find_one({"user_id": input.user_id})
    if existing_profile:
        return UserProfile(**existing_profile)
    
    profile = UserProfile(**input.dict())
    await db.user_profiles.insert_one(profile.dict())
    return profile

@api_router.get("/profile/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: str):
    profile = await db.user_profiles.find_one({"user_id": user_id})
    if profile:
        return UserProfile(**profile)
    else:
        # Create default profile
        default_profile = UserProfile(user_id=user_id, name="משתמש")
        await db.user_profiles.insert_one(default_profile.dict())
        return default_profile

@api_router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Get user profile
            user_profile_doc = await db.user_profiles.find_one({"user_id": user_id})
            user_profile = user_profile_doc if user_profile_doc else {}
            
            # Generate AI response
            ai_response = fitness_ai.generate_response(message_data["message"], user_profile)
            
            # Create chat message
            chat_message = ChatMessage(
                user_id=user_id,
                message=message_data["message"],
                response=ai_response
            )
            
            # Save to database
            await db.chat_messages.insert_one(chat_message.dict())
            
            # Send response back
            await manager.send_personal_message(
                json.dumps({
                    "type": "ai_response",
                    "message": ai_response,
                    "timestamp": chat_message.timestamp.isoformat()
                }),
                websocket
            )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()