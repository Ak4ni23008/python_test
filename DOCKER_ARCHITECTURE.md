# 🐳 Docker Architecture - CloudTrade

## Overview

This document explains the Docker containerization strategy for CloudTrade on Oracle Cloud.

---

## Container Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ORACLE VM INSTANCE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           DOCKER NETWORK: cloudtrade-network       │  │
│  ├─────────────────────────────────────────────────────┤  │
│  │                                                     │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │  │
│  │  │   NGINX      │  │  PostgreSQL  │  │  Backend │ │  │
│  │  │ (Port 80/443)│  │ (Port 5432)  │  │ (8000)   │ │  │
│  │  └──────────────┘  └──────────────┘  └──────────┘ │  │
│  │         │                   │              │       │  │
│  │  ┌──────┴───────────────────┴──────┐     │       │  │
│  │  │     VOLUMES: postgres_data,      │     │       │  │
│  │  │     nginx_cache, code mounts     │     │       │  │
│  │  └────────────────────────────────┘     │       │  │
│  │                                           │       │  │
│  │  ┌──────────────┐  ┌──────────────┐    │       │  │
│  │  │  Frontend    │  │   Worker     │    │       │  │
│  │  │  (Port 3000) │  │ (Background) │    │       │  │
│  │  └──────────────┘  └──────────────┘    │       │  │
│  │                                           │       │  │
│  └─────────────────────────────────────────┼───────┘  │
│                                             │          │
│                       Traffic Flow ────────┘          │
│                                                       │
└─────────────────────────────────────────────────────────┘
```

---

## Container Specifications

### 1. **PostgreSQL (db)**
- **Image**: `postgres:15-alpine`
- **Port**: 5432 (internal)
- **Volume**: `postgres_data` (persistent)
- **Environment**:
  - User: `cloudtrade`
  - Database: `cloudtrade`
- **Health Check**: Every 10s
- **Restart Policy**: `unless-stopped`

### 2. **Backend (FastAPI)**
- **Image**: Custom (built from `Dockerfile.backend`)
- **Port**: 8000
- **Base**: Python 3.11 slim
- **Volumes**:
  - `./backend:/app` (code mount)
  - `/app/__pycache__` (ignore pycache)
- **Health Check**: HTTP `/health` endpoint
- **Dependencies**: PostgreSQL
- **Features**:
  - Non-root user (appuser:1000)
  - Automatic restart
  - Graceful shutdown

### 3. **Frontend (Next.js)**
- **Image**: Custom (built from `Dockerfile.frontend`)
- **Port**: 3000
- **Base**: Node 18 alpine
- **Build**: `npm run build` (production build)
- **Volumes**:
  - `./frontend:/app` (code mount)
  - `/app/node_modules` (cache)
  - `/app/.next` (build cache)
- **Health Check**: HTTP GET `/`
- **Features**:
  - Non-root user (appuser:1000)
  - Lightweight alpine base
  - Production optimized

### 4. **Worker (Live Trading)**
- **Image**: Custom (built from `Dockerfile.worker`)
- **No Port**: Internal only
- **Base**: Python 3.11 slim
- **Volumes**: Same as backend
- **Dependencies**: PostgreSQL, Backend
- **Features**:
  - Continuous background process
  - Auto-restart on failure
  - Resource limits (1 CPU, 1GB RAM)
  - Polling interval: 2 seconds
  - Logs to container stdout

### 5. **Nginx (Reverse Proxy)**
- **Image**: `nginx:alpine`
- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Volume**: `./nginx.conf:/etc/nginx/nginx.conf:ro`
- **Features**:
  - Rate limiting
  - Gzip compression
  - SSL/TLS support
  - Load balancing
  - Static asset caching
  - Health check endpoint

---

## Volume Management

### Persistent Volumes
```yaml
postgres_data:     # PostgreSQL database files
  - Location: /var/lib/postgresql/data
  - Persists: Between container restarts
  - Backup: Critical - backup regularly

nginx_cache:       # Nginx caching layer
  - Location: /var/cache/nginx
  - Persists: Cache between restarts
  - Cleanup: Safe to delete
```

### Bind Mounts (Code)
```yaml
./backend:/app     # Live code changes
./frontend:/app    # Live code changes
./nginx.conf       # Read-only config
./ssl/cert.pem     # SSL certificates
./ssl/key.pem      # SSL key
```

---

## Networking

### Network Type
```yaml
cloudtrade-network:
  Driver: bridge (default)
  Isolation: Containers only see each other
  Internal: No internet unless backend services require
```

### Service Discovery
Containers communicate by service name (internal DNS):
- `backend:8000` - FastAPI service
- `frontend:3000` - Next.js service
- `db:5432` - PostgreSQL service
- `nginx:80/443` - Reverse proxy

### Port Mapping
```
Host Port  →  Container Port  →  Service
80         →  80              →  nginx
443        →  443             →  nginx
3000       →  3000            →  frontend (optional)
8000       →  8000            →  backend (optional)
5432       →  5432            →  postgresql (optional)
```

---

## Build Process

### Dockerfile.backend
```dockerfile
1. Base: python:3.11-slim
2. Install: gcc, postgresql-client
3. Copy: requirements.txt
4. Run: pip install -r requirements.txt
5. Copy: backend code
6. User: appuser (non-root)
7. Expose: 8000
8. CMD: uvicorn app.main:app
```

### Dockerfile.frontend
```dockerfile
1. Base: node:18-alpine
2. Copy: package.json, package-lock.json
3. Run: npm ci (clean install)
4. Copy: frontend code
5. Run: npm run build (production build)
6. User: appuser (non-root)
7. Expose: 3000
8. CMD: npm start
```

### Dockerfile.worker
```dockerfile
1. Base: python:3.11-slim
2. Install: gcc, postgresql-client
3. Copy: requirements.txt + backend code
4. User: appuser (non-root)
5. No port exposure (background process)
6. CMD: python -m app.workers.live_worker
```

---

## Deployment Flow

### Initial Deployment
```
1. docker-compose build       # Build all images
2. docker-compose up -d       # Start all containers
3. Wait for health checks     # Verify all running
4. Run migrations (if needed) # Database setup
5. Access frontend            # http://localhost:3000
```

### Update Deployment
```
1. git pull origin main       # Get latest code
2. docker-compose up -d --build  # Rebuild changed images
3. Old containers: stop       # Graceful shutdown
4. New containers: start      # New code deployed
```

### Environment Variables
```
→ Loaded from: .env.prod file
→ Passed to: All containers at startup
→ Override: Can be set per container
→ Reload: Required to change (restart container)
```

---

## Resource Limits

### Worker Container (Live Trading)
```yaml
limits:
  cpus: '1'           # Max 1 CPU core
  memory: 1G          # Max 1GB RAM
reservations:
  cpus: '0.5'         # Request 0.5 CPU
  memory: 512M        # Request 512MB RAM
```

### Why Limits?
- Prevent runaway processes
- Ensure fair resource sharing
- Monitor performance
- Cost optimization
- Stability on shared hardware

---

## Health Checks

### Backend Health Check
```
Test: curl http://localhost:8000/health
Interval: 30s
Timeout: 10s
Start Period: 40s
Retries: 3
```

### Frontend Health Check
```
Test: wget --spider http://localhost:3000/
Interval: 30s
Timeout: 10s
Start Period: 40s
Retries: 3
```

### Database Health Check
```
Test: pg_isready -U cloudtrade
Interval: 10s
Timeout: 5s
Retries: 5
```

### Nginx Health Check
```
Test: wget --spider http://localhost/health
Interval: 30s
Timeout: 10s
Retries: 3
```

---

## Restart Policies

```yaml
restart: unless-stopped
```

**Behavior:**
- Automatic restart on crash
- Survives Docker daemon restart
- Manual stop: `docker-compose down`
- Prevents infinite restart loops

---

## Logging

### Container Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail 100

# With timestamps
docker-compose logs -f --timestamps
```

### Log Drivers
- Standard output: Captured by Docker
- Forwarding: Can be piped to:
  - File
  - Syslog
  - Splunk
  - DataDog

---

## Security Considerations

### 1. Non-root Users
- Containers run as `appuser:1000`
- Not as root (uid 0)
- Limited file system access
- Reduced attack surface

### 2. Read-only File System (Optional)
```yaml
read_only: true
tmpfs:
  - /tmp
  - /run
```

### 3. Network Isolation
- Containers can't reach external networks unless configured
- Internal communication only
- Firewall rules at host level

### 4. Secret Management
- API keys in environment variables
- Database passwords in `.env.prod`
- Never commit secrets
- Use Docker Secrets in swarm mode (advanced)

---

## Monitoring & Debugging

### View Running Containers
```bash
docker-compose ps
docker ps -a
```

### Check Container Stats
```bash
docker stats                    # All containers
docker stats cloudtrade-backend # Specific container
```

### Enter Container Shell
```bash
docker exec -it cloudtrade-backend bash
docker exec -it cloudtrade-db psql -U cloudtrade
```

### View Container Processes
```bash
docker top cloudtrade-backend
```

### Inspect Container
```bash
docker inspect cloudtrade-backend
docker inspect --format='{{json .NetworkSettings}}' cloudtrade-backend
```

---

## Troubleshooting

### Container Exiting Immediately
```bash
docker-compose logs backend
docker-compose restart backend
```

### Containers Can't Communicate
```bash
# Check network
docker network ls
docker network inspect cloudtrade-network

# Check DNS
docker exec -it cloudtrade-backend nslookup db
```

### Port Already in Use
```bash
lsof -i :80
lsof -i :3000
lsof -i :8000

kill -9 <PID>
```

### Disk Space Issues
```bash
df -h
docker system df
docker system prune -a
```

---

## Optimization Tips

### 1. Image Size
- Use alpine base images (smaller)
- Multi-stage builds (advanced)
- Clean up package managers
- Remove build dependencies

### 2. Build Speed
- Layer caching (stable layers first)
- .dockerignore file (exclude files)
- Use Docker BuildKit

### 3. Runtime Performance
- Volume mounts for development
- Bind mounts for code (hot reload)
- Resource limits (prevent runaway)

### 4. Storage
- Use named volumes for persistence
- Regular backups
- Monitor disk space

---

## Scaling Considerations

### Horizontal Scaling
```yaml
# Multiple backend instances
backend1:
  # config...
backend2:
  # config...
backend3:
  # config...
```

### Load Balancing
```nginx
upstream backend {
  least_conn;
  server backend1:8000;
  server backend2:8000;
  server backend3:8000;
}
```

### Database Scaling
- Connection pooling
- Read replicas
- Sharding (advanced)

---

## Production Checklist

- [ ] All images use non-root users
- [ ] Health checks configured
- [ ] Resource limits set
- [ ] Volumes are persistent
- [ ] Logging configured
- [ ] SSL/TLS enabled
- [ ] Rate limiting enabled
- [ ] Backup strategy in place
- [ ] Monitoring setup
- [ ] Auto-restart policies set

---

**Happy Containerizing! 🐳**
