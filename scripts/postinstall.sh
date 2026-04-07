#!/bin/bash
set -e

# Create hearth group if it doesn't exist
if ! getent group hearth >/dev/null; then
    groupadd --system hearth
fi

# Create hearth user if it doesn't exist
if ! getent passwd hearth >/dev/null; then
    useradd --system \
            --gid hearth \
            --home-dir /var/lib/hearth \
            --create-home \
            --shell /usr/sbin/nologin \
            hearth
fi

# Set directories and permissions
mkdir -p /var/log/hearth
mkdir -p /var/lib/hearth
chown -R hearth:hearth /var/lib/hearth
chown -R hearth:hearth /var/log/hearth
chown -R hearth:hearth /usr/share/hearth

# Set permissions for configuration
chmod 600 /etc/hearth/hearth.conf
chown hearth:hearth /etc/hearth/hearth.conf

# Reload systemd and start/enable service
systemctl daemon-reload
if [ -d /run/systemd/system ]; then
    systemctl enable hearth
    systemctl restart hearth
fi

echo "Hearth post-install complete."
