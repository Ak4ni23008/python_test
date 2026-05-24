# ⚡ Quick Start Guide - CloudTrade on Oracle

## 🚀 5-Minute Deployment

### Prerequisites
- Oracle VM running (Ubuntu 22.04)
- SSH access to VM
- Gemini API key

---

## Step 1: SSH into VM (2 mins)

```bash
ssh -i /path/to/key.pem ubuntu@YOUR_ORACLE_IP

# Update system
sudo apt update && sudo apt upgrade -y
```

---

## Step 2: Install Docker (2 mins)

```bash
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo usermod -aG docker ubuntu

# Logout and back in
logout
ssh -i /path/to/key.pem ubuntu@YOUR_ORACLE_IP
```

---

## Step 3: Clone & Deploy (1 min)

```bash
# Clone repo
git clone https://github.com/Ak4ni23008/python_test.git cloudtrade
cd cloudtrade

# Create environment file
cat > .env.prod << EOF
DB_PASSWORD=$(openssl rand -base64 32)
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.0-flash
NEXT_PUBLIC_API_URL=http://YOUR_ORACLE_IP
CORS_ORIGINS=http://YOUR_ORACLE_IP
ENVIRONMENT=production
EOF

# Deploy
chmod +x deploy.sh
./deploy.sh
```

---

## ✅ Done!

**Access your app:**
- Frontend: `http://YOUR_ORACLE_IP:3000`
- Backend: `http://YOUR_ORACLE_IP:8000`
- API Docs: `http://YOUR_ORACLE_IP:8000/docs`

---

## 📱 Start Using

1. Open `http://YOUR_ORACLE_IP:3000` in browser
2. Click **💬 Chat Builder**
3. Describe strategy: _"Buy RSI below 30, sell above 70"_
4. AI generates code
5. Click **Backtest** or **Deploy**
6. 🎉 Live trading running in cloud!

---

## 🔧 Common Commands

```bash
cd cloudtrade

# View status
docker-compose ps

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Update code
git pull && docker-compose up -d --build

# Backup database
docker exec cloudtrade-db pg_dump -U cloudtrade -d cloudtrade > backup.sql
```

---

## 🆘 Troubleshooting

**Services not starting?**
```bash
docker-compose logs
```

**Can't access frontend?**
```bash
# Check if running
docker-compose ps

# Check if ports open
curl http://localhost:3000
```

**Database issues?**
```bash
docker-compose restart db
sleep 10
docker-compose up -d
```

---

## 📞 Need Help?

Full guide: `cat ORACLE_DEPLOYMENT.md`

Logs: `docker-compose logs -f`

---

**That's it! Your cloud trading platform is LIVE! 🚀**
