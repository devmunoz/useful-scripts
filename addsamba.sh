#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <path> <share_name> <username>"
    exit 1
fi

FOLDER="$1"
SHARE_NAME="$2"
USER="$3"
SMB_CONF="/etc/samba/smb.casa.conf" #casaos specific conf

# 1. Create the folder
sudo mkdir -p "$FOLDER"

# 2. Create the user (prompt for password)
if ! id "$USER" &>/dev/null; then
    sudo adduser --disabled-password --gecos "" "$USER"
    echo "Set Samba password for $USER:"
    sudo smbpasswd -a "$USER"
else
    echo "User $USER already exists."
fi

# 3. Add Samba configuration only if share doesn't exist
if grep -q "^\[$USER\]" "$SMB_CONF"; then
    echo "Samba share [$USER] already exists in configuration."
else
    SHARE_CONF="
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
"
    echo "$SHARE_CONF" | sudo tee -a "$SMB_CONF" > /dev/null
    echo "Samba share [$USER] added to configuration."
fi

# 4. Set permissions recursively
sudo chown -R "$USER":root "$FOLDER"
sudo chmod -R 770 "$FOLDER"

# 5. Reload Samba service
sudo systemctl reload smbd

echo "Samba share for $USER at $FOLDER created and configured."