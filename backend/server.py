from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import json
import asyncio
import time
from collections import defaultdict
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Production Configuration
PRODUCTION_MODE = os.environ.get('PRODUCTION_MODE', 'False').lower() == 'true'
MAX_MESSAGE_LENGTH = 2000
MAX_MESSAGES_PER_MINUTE = 10
MAX_DAILY_MESSAGES = 200
SESSION_TIMEOUT_HOURS = 24

# MongoDB connection with production settings
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(
    mongo_url,
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=45000,
    waitQueueTimeoutMS=5000,
    serverSelectionTimeoutMS=5000
)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(
    title="AI Fitness Trainer",
    description="Professional AI Fitness Trainer powered by Gemini",
    version="1.0.0",
    docs_url="/docs" if not PRODUCTION_MODE else None,
    redoc_url="/redoc" if not PRODUCTION_MODE else None
)

# Security middleware
if PRODUCTION_MODE:
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["*"]
    )

# Rate limiting
rate_limiter = defaultdict(lambda: defaultdict(list))

def check_rate_limit(client_ip: str, user_id: str) -> bool:
    """Check if user has exceeded rate limits"""
    now = time.time()
    minute_ago = now - 60
    day_ago = now - (24 * 60 * 60)
    
    # Clean old entries
    rate_limiter[user_id]['minute'] = [t for t in rate_limiter[user_id]['minute'] if t > minute_ago]
    rate_limiter[user_id]['day'] = [t for t in rate_limiter[user_id]['day'] if t > day_ago]
    
    # Check limits
    if len(rate_limiter[user_id]['minute']) >= MAX_MESSAGES_PER_MINUTE:
        return False
    if len(rate_limiter[user_id]['day']) >= MAX_DAILY_MESSAGES:
        return False
    
    # Add current request
    rate_limiter[user_id]['minute'].append(now)
    rate_limiter[user_id]['day'].append(now)
    
    return True

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# WebSocket connection manager with production features
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_times: Dict[str, datetime] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.connection_times[user_id] = datetime.utcnow()

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.connection_times:
            del self.connection_times[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(message)
            except:
                self.disconnect(user_id)

    def cleanup_old_connections(self):
        """Remove connections older than session timeout"""
        cutoff_time = datetime.utcnow() - timedelta(hours=SESSION_TIMEOUT_HOURS)
        to_remove = []
        
        for user_id, connect_time in self.connection_times.items():
            if connect_time < cutoff_time:
                to_remove.append(user_id)
        
        for user_id in to_remove:
            self.disconnect(user_id)

manager = ConnectionManager()

# Production-Ready Gemini Fitness Trainer
class ProductionFitnessTrainer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.system_message = """אתה מאמן כושר מקצועי ומומחה ברמה גבוהה ביותר, עם ניסיון של 20 שנה בתחום הכושר, התזונה והמוטיבציה. אתה דובר עברית באופן מושלם ומתמחה במתן עצות מותאמות אישית.

## התפקיד שלך:
🏋️‍♂️ **מאמן כושר מקצועי** - מנתח כל בקשה בעומק ונותן תוכניות מותאמות אישית
🥗 **יועץ תזונה מוסמך** - מספק עצות תזונה מקצועיות ומותאמות אישית  
🧠 **מוטיבטור מקצועי** - מעניק מוטיבציה אישית והנחיה רגשית
📊 **אנליסט כושר** - מנתח את המצב הנוכחי ומתכנן את הדרך קדימה

## דרישות המקצועיות שלך:
1. **ניתוח מעמיק** - בכל שאלה, תנתח:
   - המטרות של השואל
   - רמת הכושר המשוערת  
   - הקונטקסט המלא
   - דרכי התאמה אישית

2. **תשובות מקצועיות** - כל תשובה תכלול:
   - ניתוח מפורט של הבקשה
   - עצות ספציפיות ומפורטות
   - תוכנית פעולה ברורה
   - שאלות המעמיקות

3. **בטיחות מקצועית**:
   - תמיד תדגיש בטיחות באימונים
   - תמליץ להתייעץ עם רופא במקרים רפואיים
   - תתן עצות מבוססות מחקר מדעי

## סגנון מקצועי:
- עברית מושלמת עם אימוג'ים רלוונטיים 💪🔥🏋️‍♂️🥗🎯
- מבנה ברור עם כותרות
- דוגמאות מעשיות וספציפיות
- תמיד עם המלצה למעקב

זכור: אתה מאמן אמיתי שמקדיש זמן, מנתח לעומק, ובאמת אכפת לו מההצלחה של המשתמש!"""

        self.session_cache = {}
        self.last_cleanup = time.time()

    def _cleanup_sessions(self):
        """Clean old sessions to prevent memory leaks"""
        if time.time() - self.last_cleanup > 3600:  # Cleanup every hour
            cutoff_time = time.time() - (SESSION_TIMEOUT_HOURS * 3600)
            self.session_cache = {
                k: v for k, v in self.session_cache.items() 
                if v.get('last_used', 0) > cutoff_time
            }
            self.last_cleanup = time.time()

    async def get_response(self, user_message: str, user_id: str, user_profile: Dict = None) -> str:
        try:
            self._cleanup_sessions()
            
            # Input validation and sanitization
            if not user_message or len(user_message.strip()) == 0:
                return "שלום! 👋 לא קיבלתי הודעה ברורה. איך אני יכול לעזור לך היום?"
            
            if len(user_message) > MAX_MESSAGE_LENGTH:
                return f"ההודעה ארוכה מדי. אנא שלח הודעה עד {MAX_MESSAGE_LENGTH} תווים. 📝"

            # Create enhanced context
            enhanced_message = user_message.strip()
            if user_profile and any(user_profile.get(key) for key in ['name', 'age', 'fitness_level', 'goals']):
                profile_context = "\n\n--- פרופיל המשתמש ---\n"
                if user_profile.get('name'):
                    profile_context += f"שם: {user_profile['name']}\n"
                if user_profile.get('age'):
                    profile_context += f"גיל: {user_profile['age']}\n"
                if user_profile.get('fitness_level'):
                    profile_context += f"רמת כושר: {user_profile['fitness_level']}\n"
                if user_profile.get('goals'):
                    profile_context += f"יעדים: {', '.join(user_profile['goals'])}\n"
                
                enhanced_message = user_message + profile_context

            # Create chat instance with error handling
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"prod_fitness_{user_id}",
                system_message=self.system_message
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(4000)
            
            # Create and send message
            message = UserMessage(text=enhanced_message)
            response = await chat.send_message(message)
            
            # Update session cache
            self.session_cache[user_id] = {
                'last_used': time.time(),
                'message_count': self.session_cache.get(user_id, {}).get('message_count', 0) + 1
            }
            
            # Validate response
            if not response or len(response.strip()) == 0:
                return "מצטער, נתקלתי בבעיה ביצירת תשובה. נסה שוב בעוד רגע! 🔄"
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error in ProductionFitnessTrainer.get_response: {str(e)}", exc_info=True)
            return """שלום! 👋 נתקלתי בבעיה טכנית זמנית.

🔧 **אנא נסה שוב בעוד רגע**

בינתיים, אני כאן לעזור לך עם:
💪 תוכניות אימון מותאמות אישית
🥗 עצות תזונה מקצועיות  
🔥 מוטיבציה והנחיה אישית
📊 ניתוח והגדרת יעדים

ספר לי איך אני יכול לעזור לך! 😊"""

# Initialize trainer
gemini_api_key = os.environ.get('GEMINI_API_KEY')
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY environment variable is required")

fitness_trainer = ProductionFitnessTrainer(gemini_api_key)

# Enhanced Pydantic Models with validation
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH)
    response: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_type: str = Field(default="user", regex="^(user|ai)$")

    @validator('message', 'response')
    def sanitize_text(cls, v):
        return v.strip()

class ChatMessageCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH)

    @validator('message')
    def sanitize_message(cls, v):
        return v.strip()

class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=13, le=120)
    fitness_level: str = Field(default="beginner", regex="^(beginner|intermediate|advanced)$")
    goals: List[str] = Field(default=[], max_items=10)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserProfileCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=13, le=120)
    fitness_level: str = Field(default="beginner", regex="^(beginner|intermediate|advanced)$")
    goals: List[str] = Field(default=[], max_items=10)

class UserProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=13, le=120)
    fitness_level: Optional[str] = Field(None, regex="^(beginner|intermediate|advanced)$")
    goals: Optional[List[str]] = Field(None, max_items=10)

# Dependency for rate limiting
async def rate_limit_check(request: Request, input: ChatMessageCreate = None):
    client_ip = request.client.host
    user_id = input.user_id if input else "unknown"
    
    if not check_rate_limit(client_ip, user_id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before sending more messages."
        )
    return input

# Production API Routes
@api_router.get("/")
async def root():
    return {
        "message": "AI Fitness Trainer - Production Ready",
        "version": "1.0.0",
        "status": "healthy",
        "powered_by": "Gemini AI"
    }

@api_router.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        await db.admin.command('ping')
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "ai_service": "operational"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail="Service unhealthy")

@api_router.post("/chat", response_model=ChatMessage)
async def send_message(
    request: Request,
    input: ChatMessageCreate = Depends(rate_limit_check)
):
    try:
        # Get user profile for context
        user_profile_doc = await db.user_profiles.find_one({"user_id": input.user_id})
        user_profile = user_profile_doc if user_profile_doc else {}
        
        # Generate AI response
        ai_response = await fitness_trainer.get_response(
            input.message, 
            input.user_id, 
            user_profile
        )
        
        # Create chat message
        chat_message = ChatMessage(
            user_id=input.user_id,
            message=input.message,
            response=ai_response
        )
        
        # Save to database with error handling
        try:
            await db.chat_messages.insert_one(chat_message.dict())
        except Exception as db_error:
            logger.error(f"Database error: {str(db_error)}")
            # Continue even if database save fails
        
        return chat_message
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.get("/chat/{user_id}", response_model=List[ChatMessage])
async def get_chat_history(user_id: str, limit: int = Field(default=50, le=200, ge=1)):
    try:
        # Validate user_id
        if not user_id or len(user_id) > 100:
            raise HTTPException(status_code=400, detail="Invalid user_id")
            
        messages = await db.chat_messages.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return [ChatMessage(**msg) for msg in messages]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_chat_history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.post("/profile", response_model=UserProfile)
async def create_user_profile(input: UserProfileCreate):
    try:
        # Check if profile exists
        existing_profile = await db.user_profiles.find_one({"user_id": input.user_id})
        if existing_profile:
            return UserProfile(**existing_profile)
        
        # Create new profile
        profile_data = input.dict()
        profile_data['created_at'] = datetime.utcnow()
        profile_data['updated_at'] = datetime.utcnow()
        
        profile = UserProfile(**profile_data)
        await db.user_profiles.insert_one(profile.dict())
        return profile
        
    except Exception as e:
        logger.error(f"Error in create_user_profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.get("/profile/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: str):
    try:
        if not user_id or len(user_id) > 100:
            raise HTTPException(status_code=400, detail="Invalid user_id")
            
        profile = await db.user_profiles.find_one({"user_id": user_id})
        if profile:
            return UserProfile(**profile)
        else:
            # Create default profile
            default_profile = UserProfile(
                user_id=user_id, 
                name="משתמש",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await db.user_profiles.insert_one(default_profile.dict())
            return default_profile
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_user_profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.put("/profile/{user_id}", response_model=UserProfile)
async def update_user_profile(user_id: str, input: UserProfileUpdate):
    try:
        if not user_id or len(user_id) > 100:
            raise HTTPException(status_code=400, detail="Invalid user_id")
            
        # Get existing profile
        existing_profile = await db.user_profiles.find_one({"user_id": user_id})
        if not existing_profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Update only provided fields
        update_data = {k: v for k, v in input.dict().items() if v is not None}
        if update_data:
            update_data['updated_at'] = datetime.utcnow()
            await db.user_profiles.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
        
        # Return updated profile
        updated_profile = await db.user_profiles.find_one({"user_id": user_id})
        return UserProfile(**updated_profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_user_profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    if not user_id or len(user_id) > 100:
        await websocket.close(code=1008, reason="Invalid user_id")
        return
        
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Check rate limit for WebSocket
            if not check_rate_limit("websocket", user_id):
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Rate limit exceeded. Please wait before sending more messages."
                }))
                continue
                
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                user_message = message_data.get("message", "").strip()
                
                if not user_message or len(user_message) > MAX_MESSAGE_LENGTH:
                    await websocket.send_text(json.dumps({
                        "type": "error", 
                        "message": "Invalid message"
                    }))
                    continue
                
                # Get user profile
                user_profile_doc = await db.user_profiles.find_one({"user_id": user_id})
                user_profile = user_profile_doc if user_profile_doc else {}
                
                # Generate AI response
                ai_response = await fitness_trainer.get_response(user_message, user_id, user_profile)
                
                # Create and save chat message
                chat_message = ChatMessage(
                    user_id=user_id,
                    message=user_message,
                    response=ai_response
                )
                
                try:
                    await db.chat_messages.insert_one(chat_message.dict())
                except:
                    pass  # Continue even if database save fails
                
                # Send response
                await manager.send_personal_message(
                    json.dumps({
                        "type": "ai_response",
                        "message": ai_response,
                        "timestamp": chat_message.timestamp.isoformat()
                    }),
                    user_id
                )
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Internal error occurred"
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        manager.disconnect(user_id)

# Include router
app.include_router(api_router)

# CORS with production settings
allowed_origins = ["*"] if not PRODUCTION_MODE else [
    "https://227f84f8-8e50-4282-ad85-bd314b6e4bc5.preview.emergentagent.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Production logging
logging.basicConfig(
    level=logging.INFO if not PRODUCTION_MODE else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cleanup task
async def periodic_cleanup():
    """Periodic cleanup of old connections and sessions"""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            manager.cleanup_old_connections()
            if hasattr(fitness_trainer, '_cleanup_sessions'):
                fitness_trainer._cleanup_sessions()
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")

# Start cleanup task
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_cleanup())
    logger.info("AI Fitness Trainer started successfully")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("AI Fitness Trainer shutdown completed")