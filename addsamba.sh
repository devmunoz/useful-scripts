#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <path> <share_name> <username>"
    exit 1
fi

FOLDER="$1"
SHARE_NAME="$2"
USER="$3"
SMB_CONF="/etc/samba/smb.casa.conf" # casaos specific conf; fallback handled below

# 1. Create the user (prompt for password) - do this before creating the folder so we don't leave partial state
if id "$USER" &>/dev/null; then
    echo "User $USER already exists."
else
    echo "Creating user '$USER'..."
    if sudo adduser --disabled-password --gecos "" "$USER"; then
        echo "User $USER created."
    else
        echo "adduser failed for '$USER'."
        # Offer to retry with --force-badname
        read -r -p "Retry adduser with --force-badname to relax the name check? [y/N] " RESP
        RESP=${RESP:-N}
        case "$RESP" in
            [yY]|[yY][eE][sS])
                echo "Retrying adduser --force-badname ..."
                if sudo adduser --force-badname --disabled-password --gecos "" "$USER"; then
                    echo "User $USER created with --force-badname."
                else
                    echo "Failed to create user $USER even with --force-badname. Exiting."
                    exit 1
                fi
                ;;
            *)
                echo "Aborting. User not created."
                exit 1
                ;;
        esac
    fi
fi

# After user exists, set Samba password
echo "Set Samba password for $USER:"
sudo smbpasswd -a "$USER"

# 2. Create the folder (only after user exists)
if [ -d "$FOLDER" ]; then
    echo "Folder $FOLDER already exists."
else
    echo "Creating folder $FOLDER ..."
    if ! sudo mkdir -p "$FOLDER"; then
        echo "Failed to create folder $FOLDER. Exiting."
        exit 1
    fi
fi

# 3. Ensure SMB config file exists; fallback to /etc/samba/smb.conf if the casa-specific one is missing
if [ ! -f "$SMB_CONF" ]; then
    echo "Warning: $SMB_CONF not found. Falling back to /etc/samba/smb.conf (will create if missing)."
    SMB_CONF="/etc/samba/smb.conf"
    if [ ! -f "$SMB_CONF" ]; then
        echo "Creating empty $SMB_CONF (you may need to merge with your distro's default)."
        sudo touch "$SMB_CONF"
        sudo chmod 0644 "$SMB_CONF"
    fi
fi

# 4. Add Samba configuration only if share doesn't exist (check by share name)
if sudo grep -q "^\[$SHARE_NAME\]" "$SMB_CONF"; then
    echo "Samba share [$SHARE_NAME] already exists in configuration."
else
    SHARE_CONF="$(cat <<EOF
[$SHARE_NAME]
    path = $FOLDER
    comment = $SHARE_NAME shared for $USER
    valid users = $USER
    read only = no
    browseable = yes
    public = no
    guest ok = no
    vfs objects = catia fruit streams_xattr
    create mask = 0770
    directory mask = 0770
    force user = $USER
EOF
)"
    echo "$SHARE_CONF" | sudo tee -a "$SMB_CONF" > /dev/null
    echo "Samba share [$SHARE_NAME] added to configuration."
fi

# 5. Set permissions recursively
# Use user's primary group rather than root to avoid permission surprises
if sudo chown -R "$USER":"$USER" "$FOLDER"; then
    sudo chmod -R 770 "$FOLDER"
else
    echo "Failed to chown $FOLDER to $USER. Please check manually."
fi

# 6. Reload Samba service (be resilient across systems)
if command -v systemctl >/dev/null 2>&1; then
    echo "Reloading smbd via systemctl..."
    if ! sudo systemctl reload smbd 2>/dev/null; then
        echo "systemctl reload failed, trying restart..."
        sudo systemctl restart smbd || echo "Failed to restart smbd via systemctl. Please reload Samba manually."
    fi
elif command -v service >/dev/null 2>&1; then
    echo "Reloading smbd via service..."
    sudo service smbd reload 2>/dev/null || sudo service smbd restart 2>/dev/null || echo "Failed to restart smbd via service. Please reload Samba manually."
else
    echo "Could not find systemctl or service. Please reload your Samba daemon manually (example: sudo systemctl restart smbd)."
fi

echo "Samba share for $USER at $FOLDER created and configured."