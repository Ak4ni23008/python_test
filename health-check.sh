#!/bin/bash

# Health check and auto-restart script
# Run via cron: */5 * * * * /opt/cloudtrade/health-check.sh

PROJECT_DIR="/opt/cloudtrade"
LOG_FILE="/var/log/cloudtrade/health.log"

cd $PROJECT_DIR

echo "[$(date)] Running health check..." >> $LOG_FILE

# Check backend
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "[$(date)] Backend unhealthy, restarting..." >> $LOG_FILE
    docker-compose restart backend >> $LOG_FILE 2>&1
fi

# Check frontend
if ! curl -s http://localhost:3000 > /dev/null; then
    echo "[$(date)] Frontend unhealthy, restarting..." >> $LOG_FILE
    docker-compose restart frontend >> $LOG_FILE 2>&1
fi

# Check database
if ! docker exec cloudtrade-db pg_isready -U cloudtrade > /dev/null 2>&1; then
    echo "[$(date)] Database unhealthy, restarting..." >> $LOG_FILE
    docker-compose restart db >> $LOG_FILE 2>&1
fi

# Check worker
if ! docker ps | grep cloudtrade-worker > /dev/null; then
    echo "[$(date)] Worker unhealthy, restarting..." >> $LOG_FILE
    docker-compose restart worker >> $LOG_FILE 2>&1
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "[$(date)] WARNING: Disk usage at ${DISK_USAGE}%!" >> $LOG_FILE
fi

echo "[$(date)] Health check complete" >> $LOG_FILE
