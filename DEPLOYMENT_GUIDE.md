# FRIDAY AI - Production Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying FRIDAY AI in a production environment.

## Prerequisites
- Python 3.9+
- Node.js 18+
- Git
- ADB (Android Debug Bridge) for phone camera integration

## Backend Deployment

### 1. Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd Friday

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Create `.env` file in project root:
```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# LLM API Keys (at least one required)
FRIDAY_GEMINI_KEY=your_gemini_api_key_here
FRIDAY_GROQ_KEY=your_groq_api_key_here

# ADB Configuration
ADB_PATH=/usr/bin/adb  # Adjust to your ADB path

# Vision Settings
FRAME_WIDTH=640
FRAME_HEIGHT=480
FRAME_SKIP=2

# Logging
LOG_LEVEL=INFO
```

### 3. Production Server Setup
Install gunicorn for production:
```bash
pip install gunicorn
```

Create systemd service file (`/etc/systemd/system/friday.service`):
```ini
[Unit]
Description=FRIDAY AI Assistant
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/Friday
EnvironmentFile=/path/to/Friday/.env
ExecStart=/path/to/Friday/venv/bin/gunicorn src.friday.api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable friday
sudo systemctl start friday
```

## Frontend Deployment

### 1. Build Production
```bash
cd frontend
npm install
npm run build
```

### 2. Serve with Nginx
Install nginx:
```bash
sudo apt-get install nginx
```

Configure nginx site (`/etc/nginx/sites-available/friday`):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /path/to/Friday/frontend/out;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket connections
    location /api/v1/events {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable site and restart nginx:
```bash
sudo ln -s /etc/nginx/sites-available/friday /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Health Checks & Monitoring

### Health Endpoints
- `GET /health` - Overall system health
- `GET /api/v1/status` - Voice pipeline status
- `GET /api/v1/vision/status` - Vision system status
- `GET /api/v1/adb/status` - ADB connection status

### Monitoring Script
Create `monitor_friday.sh`:
```bash
#!/bin/bash

LOG_FILE="/var/log/friday_monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

check_service() {
    curl -s http://localhost:8000/health > /dev/null
    if [ $? -eq 0 ]; then
        echo "[$DATE] FRIDAY API: HEALTHY" >> $LOG_FILE
    else
        echo "[$DATE] FRIDAY API: DOWN - RESTARTING" >> $LOG_FILE
        systemctl restart friday
    fi
}

# Check every 5 minutes
while true; do
    check_service
    sleep 300
done
```

Make executable and run:
```bash
chmod +x monitor_friday.sh
nohup ./monitor_friday.sh &
```

## Database Initialization
The SQLite database will be created automatically at:
`./data/friday.db`

To backup:
```bash
cp ./data/friday.db ./backups/friday_$(date +%Y%m%d_%H%M%S).db
```

## Troubleshooting

### Common Issues
1. **ADB Connection Issues**
   - Ensure USB debugging is enabled on phone
   - Verify ADB path in .env
   - Test with: `adb devices`

2. **Audio Problems**
   - Check microphone permissions
   - Verify correct audio device in settings
   - Test with: `arecord -l` (Linux)

3. **Vision System**
   - Ensure proper lighting for face detection
   - Verify phone camera accessibility via ADB
   - Check OpenCV installation

4. **LLM API Failures**
   - Verify API keys in .env
   - Check rate limits with providers
   - Fallback to rule-based responses if needed

## Security Considerations
1. Change default API keys in production
2. Restrict API access to trusted IPs if needed
3. Enable HTTPS for production (Let's Encrypt recommended)
4. Regularly update dependencies
5. Monitor logs for suspicious activity

## Performance Optimization
1. Adjust gunicorn workers based on CPU cores
2. Tune vision FRAME_SKIP for performance/accuracy balance
3. Consider GPU acceleration for LLM if available
4. Enable browser caching for frontend assets
5. Use CDN for static assets in production

## Backup Strategy
1. Daily database backup
2. Weekly configuration backup
3. Version control for code changes
4. Offsite storage for critical data

## Update Procedure
1. Pull latest changes: `git pull`
2. Install new dependencies: `pip install -r requirements.txt`
3. Restart service: `systemctl restart friday`
4. Clear frontend cache if needed