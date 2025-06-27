# Production Deployment Guide 🚀

## מדריך פריסה לפרודקשן - מאמן הכושר הדיגיטלי

### 📋 דרישות מערכת

**חומרה מומלצת:**
- CPU: 2+ cores
- RAM: 4GB+ 
- Storage: 20GB+ SSD
- Network: Stable internet connection

**תוכנה נדרשת:**
- Python 3.11+
- Node.js 18+
- MongoDB 7.0+
- Nginx (מומלץ)
- SSL Certificate

### 🔧 הגדרת סביבת פרודקשן

#### 1. הכנת השרת

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv nodejs npm mongodb nginx certbot

# Install yarn
npm install -g yarn

# Create application user
sudo useradd -m -s /bin/bash fitnessai
sudo usermod -aG sudo fitnessai
```

#### 2. הגדרת MongoDB

```bash
# Start MongoDB service
sudo systemctl start mongod
sudo systemctl enable mongod

# Create database and user
mongo
> use fitness_trainer_production
> db.createUser({
  user: "fitnessai",
  pwd: "your_secure_password",
  roles: ["readWrite"]
})
> exit
```

#### 3. קלונינג ופריסת הקוד

```bash
# Switch to application user
sudo su - fitnessai

# Clone repository
git clone <your-repo-url> /home/fitnessai/fitness-trainer
cd /home/fitnessai/fitness-trainer

# Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup frontend
cd ../frontend
yarn install
yarn build
```

#### 4. הגדרת משתני סביבה

```bash
# Create production environment file
cat > /home/fitnessai/fitness-trainer/backend/.env << EOF
MONGO_URL="mongodb://fitnessai:your_secure_password@localhost:27017/fitness_trainer_production"
DB_NAME="fitness_trainer_production"
GEMINI_API_KEY="your_gemini_api_key"
PRODUCTION_MODE="true"
EOF

# Create frontend environment file
cat > /home/fitnessai/fitness-trainer/frontend/.env << EOF
REACT_APP_BACKEND_URL=https://your-domain.com
EOF
```

### 🔒 הגדרת אבטחה

#### 1. Firewall Configuration

```bash
# Configure UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

#### 2. SSL Certificate

```bash
# Install SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### 3. Nginx Configuration

```bash
# Create Nginx config
sudo tee /etc/nginx/sites-available/fitness-trainer << EOF
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/m;
    
    # Frontend
    location / {
        root /home/fitnessai/fitness-trainer/frontend/build;
        index index.html index.htm;
        try_files \$uri \$uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Backend API
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # WebSocket support
    location /api/ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/fitness-trainer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 🚀 הגדרת שירותי מערכת

#### 1. Backend Service

```bash
# Create systemd service
sudo tee /etc/systemd/system/fitness-trainer-backend.service << EOF
[Unit]
Description=Fitness Trainer Backend
After=network.target mongodb.service

[Service]
Type=simple
User=fitnessai
WorkingDirectory=/home/fitnessai/fitness-trainer/backend
Environment=PATH=/home/fitnessai/fitness-trainer/backend/venv/bin
ExecStart=/home/fitnessai/fitness-trainer/backend/venv/bin/uvicorn server:app --host 127.0.0.1 --port 8001 --workers 4
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/fitnessai/fitness-trainer
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable fitness-trainer-backend
sudo systemctl start fitness-trainer-backend
```

#### 2. MongoDB Backup Service

```bash
# Create backup script
sudo tee /home/fitnessai/backup-mongodb.sh << EOF
#!/bin/bash
BACKUP_DIR="/home/fitnessai/backups"
DATE=\$(date +%Y%m%d_%H%M%S)
mkdir -p \$BACKUP_DIR

mongodump --host localhost --db fitness_trainer_production --out \$BACKUP_DIR/mongodb_\$DATE

# Keep only last 7 days
find \$BACKUP_DIR -name "mongodb_*" -mtime +7 -exec rm -rf {} \;
EOF

sudo chmod +x /home/fitnessai/backup-mongodb.sh

# Add to crontab
sudo crontab -u fitnessai -e
# Add: 0 2 * * * /home/fitnessai/backup-mongodb.sh
```

### 📊 ניטור ולוגים

#### 1. Log Rotation

```bash
# Setup log rotation
sudo tee /etc/logrotate.d/fitness-trainer << EOF
/var/log/fitness-trainer/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 fitnessai fitnessai
    postrotate
        systemctl reload fitness-trainer-backend
    endscript
}
EOF
```

#### 2. Monitoring Script

```bash
# Create monitoring script
sudo tee /home/fitnessai/monitor.sh << EOF
#!/bin/bash
LOGFILE="/var/log/fitness-trainer/monitor.log"
mkdir -p /var/log/fitness-trainer

# Check backend health
curl -f http://localhost:8001/api/health > /dev/null 2>&1
if [ \$? -ne 0 ]; then
    echo "\$(date): Backend health check failed" >> \$LOGFILE
    systemctl restart fitness-trainer-backend
fi

# Check MongoDB
mongo --eval "db.adminCommand('ping')" > /dev/null 2>&1
if [ \$? -ne 0 ]; then
    echo "\$(date): MongoDB ping failed" >> \$LOGFILE
    systemctl restart mongod
fi

# Check disk space
DISK_USAGE=\$(df / | awk 'NR==2 {print \$5}' | sed 's/%//')
if [ \$DISK_USAGE -gt 85 ]; then
    echo "\$(date): Disk usage high: \$DISK_USAGE%" >> \$LOGFILE
fi
EOF

sudo chmod +x /home/fitnessai/monitor.sh

# Add to crontab (every 5 minutes)
sudo crontab -u fitnessai -e
# Add: */5 * * * * /home/fitnessai/monitor.sh
```

### 🔄 הליך עדכון

```bash
# 1. Backup current version
cp -r /home/fitnessai/fitness-trainer /home/fitnessai/fitness-trainer.backup

# 2. Pull latest changes
cd /home/fitnessai/fitness-trainer
git pull origin main

# 3. Update backend dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt

# 4. Update frontend
cd ../frontend
yarn install
yarn build

# 5. Restart services
sudo systemctl restart fitness-trainer-backend
sudo systemctl reload nginx
```

### 🚨 בעיות נפוצות ופתרונות

#### Backend לא מתחיל:
```bash
# Check logs
sudo journalctl -u fitness-trainer-backend -f

# Check port availability
sudo netstat -tulpn | grep :8001

# Restart service
sudo systemctl restart fitness-trainer-backend
```

#### בעיות MongoDB:
```bash
# Check MongoDB status
sudo systemctl status mongod

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log

# Restart MongoDB
sudo systemctl restart mongod
```

#### בעיות SSL:
```bash
# Test SSL certificate
openssl x509 -in /etc/letsencrypt/live/your-domain.com/fullchain.pem -text -noout

# Renew certificate manually
sudo certbot renew --force-renewal
```

### 📈 אופטימיזציה לביצועים

1. **MongoDB Indexing:**
```javascript
// Connect to MongoDB and create indexes
use fitness_trainer_production
db.chat_messages.createIndex({"user_id": 1, "timestamp": -1})
db.user_profiles.createIndex({"user_id": 1}, {unique: true})
```

2. **Nginx Caching:**
```nginx
# Add to server block
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

3. **Backend Optimization:**
- Use connection pooling for MongoDB
- Enable Gzip compression
- Set appropriate worker count for uvicorn

---

**📞 תמיכה טכנית:**
לבעיות פריסה או תמיכה טכנית, בדקו את הלוגים ותשתמשו בכלי הניטור המובנים.