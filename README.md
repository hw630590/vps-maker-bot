# vps-maker-bot
A Discord VPS maker bot.

# Getting Started - Windows
1. Make sure you have Docker Desktop installed from https://www.docker.com/products/docker-desktop/ and choose Windows - AMD64 or Windows - ARM64 depending on your computer type.
2. Start Docker Desktop by restarting after the installation and opening it.
3. pip install discord.py psutil
4. python windowsvpsbot.py

# Getting Started - Linux
## For Ubuntu/Debian:
1. sudo apt update
2. sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
3. curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
4. sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
5. sudo apt update
6. sudo apt install -y docker-ce
## For Alpine:
1. apk update
2. apk add docker
3. service docker start
4. rc-update add docker default
## For CentOS/RHEL:
1. sudo yum install -y yum-utils
2. sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
3. sudo yum install -y docker-ce
## For Fedora:
1. sudo dnf install -y dnf-plugins-core
2. sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
3. sudo dnf install -y docker-ce

## Check for Docker
- docker --version
## With systemctl:
1. sudo systemctl start docker
2. sudo systemctl enable docker
3. sudo systemctl status docker
## Without systemctl:
1. Using service: sudo service docker start
2. Starting manually: sudo dockerd
3. sudo /etc/init.d/docker start
4. sudo /etc/init.d/docker enable
5. ps aux | grep dockerd
- If you want to allow docker commands without sudo, you can do sudo usermod -aG docker $USER, then logout and login.

## Discord bot prepping:
1. pip install discord.py psutil
2. Go to config.json and change the values to what you want.
3. python linuxvpsbot.py

# Future Plans
- In the future, we are planning to add the following things:
Commands being added:
/port-add - adds a port
/setup-serveo [port] - deploys a serveo.io and sends it to you
/deploy-arch - Deploys a Linux Arch container
/port-remove [port] – Removes a specific port from the system or configuration.
/status-check [id] – Checks the status of a deployed service or container.
/container-start [id] – Starts a specific container by name or ID.
/container-stop [id] – Stops a specific container by name or ID.
/list-containers – Lists all running or deployed containers.
/log-view [id] – Views logs for a specific container or service.
/resource-monitor [id] – Monitors CPU, memory, and disk usage of containers or system resources.
/backup-container [id] – Backs up a specific container's data or configuration.
/restore-backup [id] – Restores a container from a backup.
/update-container [id] – Updates the image or service running inside a container.
/config-dump [id] – Dumps the configuration of a system or container for backup or debugging purposes.
/clear-cache [id] – Clears the system or application cache to free up resources.
/create-user [username] [password] – Creates a new user account in the system or container.
/user-remove [username] [password] – Removes an existing user from the system or container.
/container-info – Displays detailed information about a specific container or service.
/renew-container [id] - Renews your container with 10 credits each 3 days.
/deploy-centos - Deploy a CentOS container.
/deploy-rehl - Deploy a REHL container.

HOW TO EARN CREDITS:
/daily-credits - Earn your daily credits (3)
/minigame - Earn 0.0025 coins per click
/daily-wordle - Earn your daily wordle credits for completing it. (1)
/daily-globle - Earn your daily globle credits for completing the correct country.

COMMANDS BEING CHANGED:
/deploy-ubuntu -> /deploy-ubuntu [version]
/deploy-debian -> /deploy-debian [version]
/deploy-alpine -> /deploy-alpine [version]

We will also add back LIVE VPS Node stats
