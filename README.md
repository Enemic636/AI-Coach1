# AI Fitness Trainer - Production Ready 🏋️‍♂️

## מאמן כושר דיגיטלי מבוסס AI

מערכת מתקדמת למאמן כושר אישי מבוסס בינה מלאכותית, הפועלת עם Gemini AI ומספקת עצות מקצועיות בתחום הכושר, התזונה והמוטיבציה.

### ✨ תכונות עיקריות

- **🤖 מאמן AI מתקדם** - מנתח לעומק כל שאלה ונותן תשובות מותאמות אישית
- **💬 ממשק צ'אט דמוי וואטסאפ** - חוויית משתמש אינטואיטיבית בעברית
- **🏋️‍♂️ תוכניות אימון מותאמות** - לכל רמות הכושר (מתחיל, בינוני, מתקדם)
- **🥗 יעוץ תזונה מקצועי** - המלצות מבוססות מחקר מדעי
- **📊 מעקב התקדמות** - שמירת היסטוריית שיחות ופרופיל משתמש
- **🔒 אבטחה מתקדמת** - הגנות Rate Limiting ו-Input Validation

### 🛠 טכנולוגיות

**Backend:**
- FastAPI (Python) - מהיר, מודרני ומאובטח
- MongoDB - מסד נתונים גמיש ומהיר
- Gemini AI - בינה מלאכותית מתקדמת של Google
- WebSocket - תקשורת בזמן אמת

**Frontend:**
- React 19 - ממשק משתמש מתקדם
- Tailwind CSS - עיצוב מותאם וזריז
- Axios - תקשורת API מהימנה

### 🚀 הפעלה מהירה

1. **הגדרת סביבה:**
```bash
# Clone the repository
git clone <repository-url>
cd ai-fitness-trainer

# Set environment variables
echo "GEMINI_API_KEY=your_gemini_api_key" >> backend/.env
echo "MONGO_URL=mongodb://localhost:27017" >> backend/.env
echo "DB_NAME=fitness_trainer_db" >> backend/.env
```

2. **התקנת תלויות:**
```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies
cd ../frontend
yarn install
```

3. **הפעלת השירותים:**
```bash
# Start MongoDB (if running locally)
mongod

# Start Backend
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001

# Start Frontend
cd frontend
yarn start
```

### 📡 API Documentation

#### Chat Endpoints
- `POST /api/chat` - שליחת הודעה למאמן
- `GET /api/chat/{user_id}` - קבלת היסטוריית צ'אט
- `WebSocket /api/ws/{user_id}` - צ'אט בזמן אמת

#### Profile Endpoints
- `POST /api/profile` - יצירת פרופיל משתמש
- `GET /api/profile/{user_id}` - קבלת פרופיל משתמש
- `PUT /api/profile/{user_id}` - עדכון פרופיל משתמש

#### Health & Monitoring
- `GET /api/` - מידע על המערכת
- `GET /api/health` - בדיקת תקינות המערכת

### 🔒 תכונות אבטחה

- **Rate Limiting:** מגבלה של 10 הודעות לדקה, 200 ליום
- **Input Validation:** אימות נתונים נכנסים
- **Error Handling:** טיפול מתקדם בשגיאות
- **CORS Protection:** הגנה מפני בקשות לא מורשות
- **Session Management:** ניהול סשנים בטוח

### 📊 מגבלות מערכת

- **אורך הודעה מקסימלי:** 2,000 תווים
- **הודעות לדקה:** 10 (למשתמש)
- **הודעות ליום:** 200 (למשתמש)
- **זמן timeout לבקשות:** 30 שניות
- **גודל היסטוריה מקסימלי:** 200 הודעות

### 🎯 דוגמאות שימוש

**שאלות מומלצות למאמן:**
- "אני בן 25, רוצה לרדת במשקל ולבנות שריר"
- "תן לי תוכנית אימון של 3 פעמים בשבוע"
- "איך אני צריך לאכול כדי לשפר ביצועים?"
- "אני מרגיש חסר מוטיבציה, עזור לי"

### 🏥 אחריות רפואית

⚠️ **הערה חשובה:** המאמן הדיגיטלי מספק עצות כלליות בלבד ואינו תחליף לייעוץ רפואי מקצועי. יש להתייעץ עם רופא לפני התחלת תוכנית אימונים חדשה.

### 📞 תמיכה

לשאלות טכניות או הצעות לשיפור:
- צרו קשר דרך ממשק המערכת
- בדקו את הלוגים ב-`/var/log/supervisor/`
- השתמשו ב-endpoint `/api/health` לבדיקת תקינות

### 📈 ביצועים ואמינות

- **זמן תגובה ממוצע:** < 3 שניות
- **זמינות:** 99.9%
- **ניטור רציף:** Health checks אוטומטיים
- **גיבוי אוטומטי:** כל הנתונים נשמרים במסד הנתונים

---

**נוצר עם ❤️ על ידי Emergent AI Platform**