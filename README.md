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
## For CentOS/RHEL:
1. sudo yum install -y yum-utils
2. sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
3. sudo yum install -y docker-ce
## For Fedora:
1. sudo dnf install -y dnf-plugins-core
2. sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
3. sudo dnf install -y docker-ce

## Check for Docker
1. docker --version
2. sudo systemctl start docker
3. sudo systemctl enable docker
4. sudo systemctl status docker
5. If you want to allow docker commands without sudo, you can do sudo usermod -aG docker $USER, then logout and login.

## Discord bot prepping:
1. pip install discord.py psutil
2. Go to config.json and change the values to what you want.
3. python linuxvpsbot.py
