#!/bin/bash
# doc2sop-core sync script
# Pushes changes from local to server

SERVER="root@207.246.117.224"
SERVER_PATH="/opt/doc2sop-core"

echo "Syncing doc2sop-core to server..."

# Sync the core package to server
rsync -avz --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' \
    /home/xbill/.openclaw/workspace/doc2sop-core/src/doc2sop_core/ \
    ${SERVER}:${SERVER_PATH}/

# Install/update on server
ssh ${SERVER} "pip3 install --user -e ${SERVER_PATH} || pip3 install --user --break-system-packages -e ${SERVER_PATH}"

echo "Sync complete!"