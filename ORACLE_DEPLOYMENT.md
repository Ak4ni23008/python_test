# 🚀 Oracle Cloud Deployment Guide - CloudTrade

## Overview

This guide will help you deploy **CloudTrade** on **Oracle Cloud Infrastructure (OCI)** using Docker and Docker Compose.

**What will be deployed:**
- FastAPI Backend (with continuous live trading worker)
- Next.js Frontend
- PostgreSQL Database
- Nginx Reverse Proxy
- SSL/HTTPS support

---

## 📋 Prerequisites

### Local Machine
- Git installed
- GitHub repo cloned

### Oracle Cloud Account
- Active OCI account
- VM instance created (Ubuntu 22.04 recommended)
- Public IP address assigned
- SSH key pair generated

---

## 🔧 Step 1: Create Oracle VM Instance

### 1.1 Launch VM
1. Go to [OCI Console](https://www.oracle.com/cloud/sign-in/)
2. **Compute** → **Instances** → **Create Instance**

### 1.2 Instance Configuration
```
Name:              cloudtrade-server
Image:             Ubuntu 22.04 LTS
Shape:             VM.Standard.E4.Flex (minimum 2 OCPUs, 4 GB RAM)
Boot Volume:       50 GB
Public IP:         Assign (auto)
SSH Key:           Add your public key
```

### 1.3 Network Security
1. **Virtual Cloud Network**: Default VCN
2. **Subnet**: Default Public Subnet
3. **Security List**: Add rules:
   - Port 80 (HTTP)
   - Port 443 (HTTPS)
   - Port 22 (SSH)

### 1.4 Note Your Details
```
Public IP:         xxx.xxx.xxx.xxx
Username:          ubuntu
SSH Key:           /path/to/key.pem
```

---

## 💻 Step 2: SSH into Oracle VM

```bash
# Set permissions
chmod 600 /path/to/key.pem

# SSH in
ssh -i /path/to/key.pem ubuntu@YOUR_ORACLE_IP

# Update system
sudo apt update && sudo apt upgrade -y
```

---

## 🐳 Step 3: Install Docker & Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add ubuntu user to docker group
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Log out and back in to apply group changes
logout
ssh -i /path/to/key.pem ubuntu@YOUR_ORACLE_IP
```

---

## 📥 Step 4: Clone Repository

```bash
# Clone the repo
git clone https://github.com/Ak4ni23008/python_test.git cloudtrade
cd cloudtrade

# Optional: checkout main branch
git checkout main
```

---

## 🔑 Step 5: Configure Environment Variables

### 5.1 Create .env.prod
```bash
# Copy example
cp .env.example .env.prod

# Edit with your values
nano .env.prod
```

### 5.2 Add Your Configuration
```bash
# Database (generate random password)
DB_PASSWORD=$(openssl rand -base64 32)

# Your Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# Frontend API URL
NEXT_PUBLIC_API_URL=http://YOUR_ORACLE_IP

# Domain (if you have one)
CORS_ORIGINS=http://YOUR_ORACLE_IP,https://your-domain.com

# Environment
ENVIRONMENT=production
```

---

## 🚀 Step 6: Deploy with Docker Compose

### 6.1 Make deployment script executable
```bash
chmod +x deploy.sh
chmod +x health-check.sh
chmod +x deploy-auto.sh
```

### 6.2 Run deployment
```bash
./deploy.sh
```

### 6.3 Verify services are running
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f

# Test API
curl http://localhost:8000/health
curl http://localhost:3000
```

---

## 🌐 Step 7: Setup Domain & SSL (Optional but Recommended)

### 7.1 Update DNS (if you have a domain)
```
A Record: @ → YOUR_ORACLE_IP
A Record: www → YOUR_ORACLE_IP
```

### 7.2 Generate SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Note the certificate paths
# Cert:  /etc/letsencrypt/live/your-domain.com/fullchain.pem
# Key:   /etc/letsencrypt/live/your-domain.com/privkey.pem
```

### 7.3 Configure Nginx with SSL

```bash
# Create ssl directory
mkdir -p ssl

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem
sudo chown ubuntu:ubuntu ssl/*
```

### 7.4 Uncomment SSL in nginx.conf
```nginx
# Edit nginx.conf and uncomment SSL sections

# Restart nginx
docker-compose restart nginx
```

### 7.5 Auto-renew SSL Certificate
```bash
# Add to crontab
sudo crontab -e

# Add this line
0 3 1 * * certbot renew --quiet && docker-compose restart nginx > /dev/null 2>&1
```

---

## 📊 Step 8: Verify Deployment

### 8.1 Check All Services
```bash
docker-compose ps

# Expected output:
# cloudtrade-db       ✓ Up (healthy)
# cloudtrade-backend  ✓ Up (healthy)
# cloudtrade-frontend ✓ Up (healthy)
# cloudtrade-worker   ✓ Up
# cloudtrade-nginx    ✓ Up (healthy)
```

### 8.2 Test Endpoints
```bash
# Health check
curl http://YOUR_ORACLE_IP/health

# API Status
curl http://YOUR_ORACLE_IP/api/cloud/status

# Frontend
curl http://YOUR_ORACLE_IP
```

### 8.3 Access Dashboard
```
Frontend:  http://YOUR_ORACLE_IP:3000
API Docs:  http://YOUR_ORACLE_IP:8000/docs
Backend:   http://YOUR_ORACLE_IP:8000
```

---

## 🔄 Step 9: Enable Auto-Updates

### 9.1 Setup Automatic Deployment
```bash
# Create log directory
mkdir -p /var/log/cloudtrade
sudo chown ubuntu:ubuntu /var/log/cloudtrade

# Edit crontab
crontab -e

# Add this line for auto-pull updates every hour
0 * * * * cd /opt/cloudtrade && git pull origin main && docker-compose up -d > /var/log/cloudtrade/cron.log 2>&1
```

### 9.2 Enable Health Checks
```bash
# Add health check cron (every 5 minutes)
crontab -e

# Add this line
*/5 * * * * /opt/cloudtrade/health-check.sh
```

---

## 🛠️ Maintenance Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f worker

# Last 100 lines
docker-compose logs --tail 100
```

### Stop Services
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart
docker-compose restart backend
docker-compose restart worker
```

### Update Code
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose up -d --build
```

### View Database
```bash
# Connect to PostgreSQL
docker exec -it cloudtrade-db psql -U cloudtrade -d cloudtrade

# Common queries
\dt                    # List tables
SELECT * FROM users;   # View users
\q                     # Quit
```

### Backup Database
```bash
# Backup
docker exec cloudtrade-db pg_dump -U cloudtrade -d cloudtrade > backup.sql

# Restore (if needed)
cat backup.sql | docker exec -i cloudtrade-db psql -U cloudtrade -d cloudtrade
```

---

## 📈 Performance Optimization

### 1. Scale Backend (Multiple Instances)
```yaml
# In docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
```

### 2. Database Connection Pooling
```env
# Add to .env.prod
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

### 3. Cache Settings
```nginx
# In nginx.conf
proxy_cache_valid 200 302 10m;
proxy_cache_valid 404 1m;
```

### 4. Worker Scaling
```yaml
# In docker-compose.yml - create multiple workers
worker1:
  # config...
worker2:
  # config...
worker3:
  # config...
```

---

## 🔒 Security Checklist

- [ ] Change database password
- [ ] Enable firewall rules (only needed ports)
- [ ] Setup SSH key authentication (no passwords)
- [ ] Enable SSL/HTTPS
- [ ] Set strong Gemini API key
- [ ] Disable unnecessary SSH ports
- [ ] Enable audit logging
- [ ] Regular backups
- [ ] Monitor disk usage
- [ ] Update system regularly

---

## 🐛 Troubleshooting

### Services Won't Start
```bash
# Check logs
docker-compose logs

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Error
```bash
# Check if database is healthy
docker-compose ps db

# Check logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Port Already in Use
```bash
# Find process using port
sudo lsof -i :80
sudo lsof -i :3000
sudo lsof -i :8000

# Kill process
sudo kill -9 PID
```

### Out of Disk Space
```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a

# Remove old images
docker image prune -a
```

---

## 📱 Accessing Your App

### From Browser
```
Frontend:  http://YOUR_ORACLE_IP:3000
Backend:   http://YOUR_ORACLE_IP:8000
API Docs:  http://YOUR_ORACLE_IP:8000/docs
```

### From Mobile
1. Get your Oracle public IP
2. Access: `http://YOUR_ORACLE_IP:3000`
3. Use chat interface to create strategies
4. Deploy and monitor live trading

---

## 🆘 Support & Monitoring

### Real-time Monitoring
```bash
# CPU, Memory, Network
docker stats

# Disk usage
df -h

# System load
top
```

### Automated Alerts
Set up monitoring with:
- Oracle Cloud Notifications
- Uptime Robot (http://uptimerobot.com)
- DataDog / New Relic

---

## 🎉 You're Live!

Your **CloudTrade** platform is now running on Oracle Cloud!

**Key Points:**
- ✅ Frontend accessible from browser
- ✅ Backend API running
- ✅ Live trading worker continuous
- ✅ Database persistent
- ✅ SSL/HTTPS enabled (optional)
- ✅ Auto-restart on failure
- ✅ Auto-updates enabled

**Next Steps:**
1. Create a user account
2. Connect broker credentials
3. Create first strategy via chat
4. Run backtest
5. Deploy live trading

---

## 📞 Quick Reference

```bash
# Essential commands
docker-compose ps              # View status
docker-compose logs -f         # View logs
docker-compose restart         # Restart all
docker-compose down            # Stop all
git pull && docker-compose up -d --build  # Update

# SSH into containers
docker exec -it cloudtrade-backend bash
docker exec -it cloudtrade-db psql -U cloudtrade
```

---

**Happy Trading! 🚀**

For questions or issues, check logs:
```bash
docker-compose logs -f
```
