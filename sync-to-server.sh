#!/bin/bash
# doc2sop-core sync script
# Pushes changes from local to server

SERVER="root@207.246.117.224"
SERVER_CORE="/opt/doc2sop-core"
SERVER_SOP="/opt/dynamic-sop"

echo "=== Syncing doc2sop-core to server ==="

# Sync the core package files to server
echo "Copying core files..."
scp /home/xbill/.openclaw/workspace/doc2sop-core/src/doc2sop_core/*.py ${SERVER}:${SERVER_CORE}/

# Sync the server api
echo "Copying api_server.py..."
scp /home/xbill/.openclaw/workspace/doc2sop-core/server-api.py ${SERVER}:${SERVER_SOP}/api_server.py

# Install dependencies on server if needed
echo "Ensuring dependencies..."
ssh ${SERVER} "pip3 install --break-system-packages pypdf flask flask-cors requests -q"

# Restart the Flask server
echo "Restarting server..."
ssh ${SERVER} "pkill -f api_server || true; cd ${SERVER_SOP} && python3 api_server.py >/dev/null 2>&1 &"

echo "=== Sync complete! ==="
echo "Server running at: http://207.246.117.224:8080"