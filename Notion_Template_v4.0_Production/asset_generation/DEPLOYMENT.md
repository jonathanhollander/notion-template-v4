# Estate Planning Concierge v4.0 - Production Deployment Guide

## Overview

This document provides comprehensive instructions for deploying the Estate Planning Concierge v4.0 Review Dashboard to production environments.

## Prerequisites

### System Requirements
- Python 3.8+ 
- 2GB+ RAM (4GB+ recommended)
- 50GB+ disk space for asset generation
- Ubuntu 20.04+ / CentOS 8+ / RHEL 8+

### Dependencies
```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx supervisor

# Or for CentOS/RHEL:
sudo dnf install -y python3 python3-pip nginx supervisor
```

## Installation

### 1. Create Application User
```bash
sudo useradd --system --home /opt/estate-planning --shell /bin/bash estate-planning
sudo mkdir -p /opt/estate-planning
sudo chown estate-planning:estate-planning /opt/estate-planning
```

### 2. Application Setup
```bash
# Switch to application user
sudo -u estate-planning -s

# Navigate to application directory
cd /opt/estate-planning

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install flask flask-cors aiosqlite asyncio gunicorn
```

### 3. Application Files
Copy your application files to `/opt/estate-planning/`:
```
/opt/estate-planning/
├── venv/
├── review_dashboard.py
├── wsgi.py
├── utils/
│   ├── database_manager.py
│   ├── cache_manager.py
│   └── ...
├── services/
│   ├── prompt_competition_service.py
│   └── ...
├── templates/
│   └── dashboard.html
└── logs/
```

### 4. Directory Structure
```bash
# Create required directories
sudo mkdir -p /var/lib/estate-planning
sudo mkdir -p /var/log/estate-planning
sudo mkdir -p /etc/estate-planning

# Set permissions
sudo chown -R estate-planning:estate-planning /var/lib/estate-planning
sudo chown -R estate-planning:estate-planning /var/log/estate-planning
sudo chown -R estate-planning:estate-planning /etc/estate-planning
```

## Configuration

### 1. Environment Variables
Create `/etc/estate-planning/environment`:
```bash
# Database Configuration
ESTATE_DB_PATH=/var/lib/estate-planning/estate_planning_assets.db

# Security Configuration  
REVIEW_API_TOKEN=your-secure-api-token-here
FLASK_SECRET_KEY=your-flask-secret-key-here

# OpenRouter API (for AI services)
OPENROUTER_API_KEY=your-openrouter-api-key

# Optional: Other AI Service APIs
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key

# Application Configuration
FLASK_ENV=production
PYTHONPATH=/opt/estate-planning
```

### 2. Gunicorn Configuration
Create `/etc/estate-planning/gunicorn.conf.py`:
```python
import multiprocessing

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 5

# Restart workers after this many requests, to prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
loglevel = "info"
accesslog = "/var/log/estate-planning/access.log"
errorlog = "/var/log/estate-planning/error.log"
capture_output = True

# Process naming
proc_name = "estate-planning-dashboard"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Preload app for better memory usage
preload_app = True
```

### 3. Systemd Service
Create `/etc/systemd/system/estate-planning.service`:
```ini
[Unit]
Description=Estate Planning Concierge v4.0 Review Dashboard
After=network.target

[Service]
Type=forking
User=estate-planning
Group=estate-planning
WorkingDirectory=/opt/estate-planning
Environment=PATH=/opt/estate-planning/venv/bin
EnvironmentFile=/etc/estate-planning/environment
ExecStart=/opt/estate-planning/venv/bin/gunicorn \
    --config /etc/estate-planning/gunicorn.conf.py \
    --daemon \
    wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s QUIT $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 4. Nginx Configuration
Create `/etc/nginx/sites-available/estate-planning`:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/estate-planning.crt;
    ssl_certificate_key /etc/ssl/private/estate-planning.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA256;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=dashboard:10m rate=10r/s;
    limit_req zone=dashboard burst=20 nodelay;
    
    # Client upload limits
    client_max_body_size 16M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    
    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files (if any)
    location /static/ {
        alias /opt/estate-planning/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

## Deployment Steps

### 1. Deploy Application
```bash
# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable estate-planning
sudo systemctl start estate-planning

# Check service status
sudo systemctl status estate-planning
```

### 2. Configure Web Server
```bash
# Enable nginx site
sudo ln -s /etc/nginx/sites-available/estate-planning /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. SSL Certificate Setup
```bash
# Option 1: Let's Encrypt (recommended)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# Option 2: Self-signed certificate (development only)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/estate-planning.key \
    -out /etc/ssl/certs/estate-planning.crt
```

## Monitoring & Maintenance

### 1. Log Monitoring
```bash
# Application logs
sudo journalctl -u estate-planning -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Application error logs
sudo tail -f /var/log/estate-planning/error.log
```

### 2. Database Maintenance
```bash
# Backup database
sudo -u estate-planning sqlite3 /var/lib/estate-planning/estate_planning_assets.db ".backup /var/backups/estate_planning_$(date +%Y%m%d_%H%M%S).db"

# Database vacuum (monthly)
sudo -u estate-planning sqlite3 /var/lib/estate-planning/estate_planning_assets.db "VACUUM;"
```

### 3. Log Rotation
Create `/etc/logrotate.d/estate-planning`:
```
/var/log/estate-planning/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0644 estate-planning estate-planning
    postrotate
        systemctl reload estate-planning
    endscript
}
```

## Security Considerations

### 1. Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp  
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. API Token Security
- Use strong, randomly generated API tokens
- Rotate tokens regularly
- Store tokens in environment variables, never in code
- Monitor access logs for unauthorized attempts

### 3. Database Security
- Database files should have restrictive permissions (600)
- Regular backups stored securely
- Consider database encryption for sensitive data

## Performance Optimization

### 1. Database Optimization
```sql
-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_competitions_status ON prompt_competitions(competition_status);
CREATE INDEX IF NOT EXISTS idx_competitions_category ON prompt_competitions(page_category);
CREATE INDEX IF NOT EXISTS idx_evaluations_competition ON quality_evaluations(competition_id);
```

### 2. Caching
- Enable nginx gzip compression
- Use browser caching for static assets
- Consider Redis for session storage (future enhancement)

### 3. Monitoring
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Monitor resource usage
htop
sudo iotop
sudo nethogs
```

## Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   sudo systemctl status estate-planning
   sudo journalctl -u estate-planning --no-pager
   ```

2. **Database permission errors**
   ```bash
   sudo chown estate-planning:estate-planning /var/lib/estate-planning/*.db
   sudo chmod 644 /var/lib/estate-planning/*.db
   ```

3. **Nginx 502 errors**
   ```bash
   # Check if Gunicorn is running
   sudo netstat -tlnp | grep :5000
   # Check nginx error logs
   sudo tail -f /var/log/nginx/error.log
   ```

4. **High memory usage**
   ```bash
   # Adjust worker count in gunicorn.conf.py
   workers = 2  # Reduce if memory constrained
   ```

### Health Checks
```bash
# Application health
curl -H "X-API-TOKEN: your-token" https://your-domain.com/api/get-progress

# Service status
sudo systemctl is-active estate-planning

# Database connectivity
sudo -u estate-planning sqlite3 /var/lib/estate-planning/estate_planning_assets.db "SELECT COUNT(*) FROM prompt_competitions;"
```

## Backup & Recovery

### 1. Automated Backups
Create `/opt/estate-planning/backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/estate-planning"
DB_PATH="/var/lib/estate-planning/estate_planning_assets.db"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
sqlite3 $DB_PATH ".backup $BACKUP_DIR/database_$DATE.db"

# Keep only last 30 days of backups
find $BACKUP_DIR -name "database_*.db" -mtime +30 -delete
```

### 2. Restore Procedure
```bash
# Stop the service
sudo systemctl stop estate-planning

# Restore database
sudo -u estate-planning cp /var/backups/estate-planning/database_YYYYMMDD_HHMMSS.db /var/lib/estate-planning/estate_planning_assets.db

# Start the service
sudo systemctl start estate-planning
```

## Scaling Considerations

### Horizontal Scaling
- Use load balancer (nginx upstream)
- Shared database (PostgreSQL recommended)
- Distributed session storage (Redis)

### Vertical Scaling  
- Increase worker processes in Gunicorn
- Add more CPU/RAM to server
- Use SSD storage for database

---

*This deployment guide ensures a secure, scalable, and maintainable production environment for the Estate Planning Concierge v4.0 Review Dashboard.*