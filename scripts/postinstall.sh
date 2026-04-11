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
# Allow the hearth user to see and modify the config via the Setup Wizard
mkdir -p /etc/hearth
chown -R hearth:hearth /etc/hearth
chmod 770 /etc/hearth
chown hearth:hearth /etc/hearth/hearth.conf
chmod 660 /etc/hearth/hearth.conf

# Attempt Automated Database Setup
if command -v psql > /dev/null; then
    echo "PostgreSQL detected, attempting automated setup..."
    # We use sudo -u postgres because the installer typically runs as root
    # Check if user exists
    if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='hearth'" | grep -q 1; then
        echo "Creating database user 'hearth'..."
        sudo -u postgres psql -c "CREATE USER hearth WITH PASSWORD 'postgres';" || echo "Warning: Could not create user."
    fi
    # Check if database exists
    if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw hearth; then
        echo "Creating database 'hearth'..."
        sudo -u postgres psql -c "CREATE DATABASE hearth OWNER hearth;" || echo "Warning: Could not create database."
        sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hearth TO hearth;" || echo "Warning: Could not grant privileges."
    fi
else
    echo "PostgreSQL not found locally. Skipping automated database setup."
fi

# Reload systemd and start/enable service
systemctl daemon-reload
if [ -d /run/systemd/system ]; then
    systemctl enable hearth
    systemctl restart hearth
fi

echo "Hearth post-install complete."
