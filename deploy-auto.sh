#!/bin/bash

# Continuous deployment script
# Run this in a cron job or systemd timer for auto-updates

set -e

PROJECT_DIR="/opt/cloudtrade"
LOG_FILE="/var/log/cloudtrade/deploy.log"

echo "[$(date)] Starting deployment check..." >> $LOG_FILE

cd $PROJECT_DIR

# Pull latest code
git pull origin main >> $LOG_FILE 2>&1

# Check if requirements changed
if git diff HEAD~1 backend/requirements.txt | grep -q .; then
    echo "[$(date)] requirements.txt changed, rebuilding..." >> $LOG_FILE
    docker-compose build backend worker >> $LOG_FILE 2>&1
fi

# Check if frontend packages changed
if git diff HEAD~1 frontend/package.json | grep -q .; then
    echo "[$(date)] package.json changed, rebuilding..." >> $LOG_FILE
    docker-compose build frontend >> $LOG_FILE 2>&1
fi

# Restart services if changes detected
if ! git diff HEAD~1 --exit-code > /dev/null 2>&1; then
    echo "[$(date)] Changes detected, restarting services..." >> $LOG_FILE
    docker-compose up -d >> $LOG_FILE 2>&1
fi

echo "[$(date)] Deployment check complete" >> $LOG_FILE
