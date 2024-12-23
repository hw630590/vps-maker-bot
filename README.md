# vps-maker-bot
A Discord VPS maker bot.

## Getting Started - Windows
1. Make sure you have Docker Desktop installed from [Docker](https://www.docker.com/products/docker-desktop) and choose Windows - AMD64 or Windows - ARM64 depending on your computer type.
2. Start Docker Desktop by restarting after the installation and opening it.
3. Install dependencies:
   pip install discord.py psutil
4. Run the bot:
   python windowsvpsbot.py

## Getting Started - Linux

### For Ubuntu/Debian:
1. Update your system:
   sudo apt update
2. Install required packages:
   sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
3. Add Docker's official GPG key:
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
4. Add Docker repository:
   sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
5. Update and install Docker:
   sudo apt update
   sudo apt install -y docker-ce

### For Alpine:
1. Update your system:
   apk update
2. Install Docker:
   apk add docker
3. Start Docker:
   service docker start
4. Add Docker to startup:
   rc-update add docker default

### For CentOS/RHEL:
1. Install required utilities:
   sudo yum install -y yum-utils
2. Add Docker repository:
   sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
3. Install Docker:
   sudo yum install -y docker-ce

### For Fedora:
1. Install required plugins:
   sudo dnf install -y dnf-plugins-core
2. Add Docker repository:
   sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
3. Install Docker:
   sudo dnf install -y docker-ce

## Check for Docker
- Verify Docker installation:
   docker --version

### With systemctl:
1. Start Docker:
   sudo systemctl start docker
2. Enable Docker to start on boot:
   sudo systemctl enable docker
3. Check Docker status:
   sudo systemctl status docker

### Without systemctl:
1. Using service:
   sudo service docker start
2. Start Docker manually:
   sudo dockerd
3. Start Docker using init.d:
   sudo /etc/init.d/docker start
   sudo /etc/init.d/docker enable

- If you want to allow Docker commands without sudo, you can do: sudo usermod -aG docker $USER
Then logout and login.

## Discord bot prepping:
1. Install dependencies:
   pip install discord.py psutil
2. Go to config.json and change the values to what you want.
3. Run the bot:
   python linuxvpsbot.py

## What are we working on?
Well, there are a few things we are working on.
- systemctl support - basicially systemd to be activated at boot for it to work, or just use systemctl3.py
- /port-add - adds a port to the docker container to use
- ssh root@ip -p port - this will be ipv4 support, which will use your public ip address and it uses the port github by steeldev, and add the port then put the port in there
- anti-abuse systems - these include anti cpu (already added), anti ram, anti network, etc
- renew system - allows the user to renew their server, which needs them to run the /renew-container [container-id] command, which will renew the container for the next 3 days, and resets each 2 days so there is a one day timeframe to renew your server.
- anti disk - if a container goes over a limit which you specify in the python file like disk-limit= then if they reach over that limit whatever is installed automaticially gets deleted
- multiple node support - link multiple nodes to make the container create on a server that you have linked and made
- vps node stats - a channel which sends an embed of the cpu, ram, disk and network stats and updates each 10 seconds
