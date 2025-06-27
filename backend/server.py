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
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage

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

# Advanced Gemini Fitness Trainer
class AdvancedFitnessTrainer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.system_message = """אתה מאמן כושר מקצועי ומומחה ברמה גבוהה ביותר, עם ניסיון של 20 שנה בתחום הכושר, התזונה והמוטיवציה. אתה דובר עברית באופן מושלם ומתמחה במתן עצות מותאמות אישית.

## התפקיד שלך:
🏋️‍♂️ **מאמן כושר מקצועי** - מנתח כל בקשה בעומק ונותן תוכניות מותאמות אישית
🥗 **יועץ תזונה מוסמך** - מספק עצות תזונה מקצועיות ומותאמות אישית
🧠 **מוטיבטור מקצועי** - מעניק מוטיבציה אישית והנחיה רגשית
📊 **אנליסט כושר** - מנתח את המצב הנוכחי ומתכנן את הדרך קדימה

## דרישות המקצועיות שלך:
1. **ניתוח מעמיק** - בכל שאלה שמקבלת, תקדיש 5-10 שניות לחשיבה ותנתח:
   - מה המטרה של השואל?
   - מהי רמת הכושר המשוערת שלו?
   - מה הקונטקסט המלא של השאלה?
   - איך לתת תשובה מותאמת אישית?

2. **תשובות מקצועיות ומותאמות** - כל תשובה תכלול:
   - ניתוח של הבקשה
   - עצות ספציפיות ומפורטות
   - תוכנית פעולה ברורה
   - שאלות המעמיקות להבנה טובה יותר

3. **טון מקצועי אבל חברותי**:
   - שפה מקצועית אבל לא יבשה
   - עידוד אמיתי ומוטיבציה
   - אמפתיה והבנה
   - סבלנות ומוכנות לעזור

## דרכי העבודה שלך:
- **תמיד תשאל שאלות המעמיקות** כדי להבין את המשתמש יותר טוב
- **תתן דוגמאות קונקרטיות** ולא רק עצות כלליות
- **תתאים את התשובה** לרמת הכושר והיכולת של המשתמש
- **תציע מעקב והתקדמות** עם יעדים ברורים
- **תהיה זמין** לשאלות המשך ולהבהרות

## סגנון הכתיבה שלך:
- בעברית מושלמת עם אימוג'ים רלוונטיים 💪🔥🏋️‍♂️🥗🎯
- מבנה ברור עם כותרות וחלוקה לפסקאות
- דוגמאות מעשיות וספציפיות
- תמיד עם המלצה למעקב ולהמשך

זכור: אתה לא רק בוט שעונה על שאלות - אתה מאמן אמיתי שמקדיש זמן, מנתח לעומק, ובאמת אכפת לו מההצלחה של המשתמש!

בכל תשובה - התנהג כמו מאמן מקצועי שפוגש את הלקוח פנים אל פנים וצריך לתת לו בדיוק מה שהוא צריך."""

    async def get_response(self, user_message: str, user_id: str, user_profile: Dict = None) -> str:
        try:
            # Create enhanced context with user profile
            enhanced_message = user_message
            if user_profile and any(user_profile.get(key) for key in ['name', 'age', 'fitness_level', 'goals']):
                profile_context = "\n\n--- הקונטקסט שלי ---\n"
                if user_profile.get('name'):
                    profile_context += f"שם: {user_profile['name']}\n"
                if user_profile.get('age'):
                    profile_context += f"גיל: {user_profile['age']}\n"
                if user_profile.get('fitness_level'):
                    profile_context += f"רמת כושר: {user_profile['fitness_level']}\n"
                if user_profile.get('goals'):
                    profile_context += f"יעדים: {', '.join(user_profile['goals'])}\n"
                
                enhanced_message = user_message + profile_context

            # Create a new LLM chat instance for each conversation using Gemini
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"gemini_fitness_{user_id}",
                system_message=self.system_message
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(4000)
            
            # Create user message
            message = UserMessage(text=enhanced_message)
            
            # Get response from OpenAI
            response = await chat.send_message(message)
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting Gemini response: {str(e)}")
            return f"""שלום! 👋 נתקלתי בבעיה טכנית כרגע, אבל אני כאן בשביל לעזור לך!

🔧 **בעיה טכנית זמנית**
נסה שוב בעוד רגע, או בינתיים ספר לי:

🎯 **בואו נתחיל ידנית:**
- מה המטרה שלך בכושר (שרידת שומן, בניית שריר, שיפור כושר)?
- מה רמת הכושר הנוכחית שלך?
- כמה זמן אתה יכול להקדיש לאימונים?
- האם יש לך גישה לחדר כושר או אתה מתאמן בבית?

💪 ברגע שהבעיה תיפתר, אני אוכל לתת לך ניתוח מעמיק ותוכנית מותאמת!"""

# Initialize Gemini trainer
gemini_api_key = os.environ.get('GEMINI_API_KEY')
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY environment variable is required")

fitness_trainer = AdvancedFitnessTrainer(gemini_api_key)

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

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    fitness_level: Optional[str] = None
    goals: Optional[List[str]] = None

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Advanced Fitness AI Trainer API - Powered by Gemini"}

@api_router.post("/chat", response_model=ChatMessage)
async def send_message(input: ChatMessageCreate):
    # Get user profile for context
    user_profile_doc = await db.user_profiles.find_one({"user_id": input.user_id})
    user_profile = user_profile_doc if user_profile_doc else {}
    
    # Generate AI response with enhanced analysis
    ai_response = await fitness_trainer.get_response(input.message, input.user_id, user_profile)
    
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
async def get_chat_history(user_id: str, limit: int = 50):
    messages = await db.chat_messages.find({"user_id": user_id}).sort("timestamp", -1).limit(limit).to_list(limit)
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

@api_router.put("/profile/{user_id}", response_model=UserProfile)
async def update_user_profile(user_id: str, input: UserProfileUpdate):
    # Get existing profile
    existing_profile = await db.user_profiles.find_one({"user_id": user_id})
    if not existing_profile:
        # Create default profile if doesn't exist
        default_profile = UserProfile(user_id=user_id, name="משתמש")
        await db.user_profiles.insert_one(default_profile.dict())
        existing_profile = default_profile.dict()
    
    # Update only provided fields
    update_data = {k: v for k, v in input.dict().items() if v is not None}
    if update_data:
        await db.user_profiles.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
    
    # Return updated profile
    updated_profile = await db.user_profiles.find_one({"user_id": user_id})
    return UserProfile(**updated_profile)

@api_router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Get user profile for context
            user_profile_doc = await db.user_profiles.find_one({"user_id": user_id})
            user_profile = user_profile_doc if user_profile_doc else {}
            
            # Generate AI response with enhanced analysis
            ai_response = await fitness_trainer.get_response(message_data["message"], user_id, user_profile)
            
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