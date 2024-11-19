import discord
from discord.ext import commands, tasks
from discord import app_commands
import subprocess
import asyncio
import os
import psutil
from threading import Thread
import datetime
import time
# pip install discord.py psutil

# Anti Resource - makes it so that people cant break your local machine
CPU_THRESHOLD=25 # % of max cpu for processes
BANDWIDTH_THRESHOLD_MBPS = 40 # this is in mbps so putting 100 means 100mbps is your max network usage.
# This also stops people from using your machine for mining or other resource intensive tasks, such as DDoSing or Minecraft bots.

CHECK_INTERVAL=5
MONITOR_INTERVAL=1
ALLOWED_CHANNEL_ID = 000000000000000 # Replace this with your channel id for the bot commands to be in.

# Change your bot token, otherwise this obviously wont work. You can get your Discord bot token from the Discord developer portal.
TOKEN = 'YOUR_BOT_TOKEN'

intents = discord.Intents.default()

client = commands.Bot(command_prefix="!", intents=intents) # DO NOT CHANGE

# You need to change these. You first need to pull these:
# pull ubuntu:latest
# pull debian:latest
# pull alpine:latest
# then it will save them. If it is a different image name, just make it the image name.
DOCKER_IMAGE_UBUNTU = "ubuntu"
DOCKER_IMAGE_DEBIAN = "debian"
DOCKER_IMAGE_ALPINE = "alpine"
#
user_last_command_time = {}
monitored_containers = {}

MAX_MEMORY = '2g' # Change to your desired memory usage. 2g = 2gb, 4g = 4gb, 8g = 8gb, etc.
# If you are looking for the server limit, they can make one of each container before being unable to make any more.

# !! Editing below this may result in the code not working. !!
async def get_network_usage_per_process():
    """
    Get network usage for each process on the system.
    Returns a dictionary with PID as keys and bandwidth (in MBps) as values.
    """
    network_usage = {}

    for proc in psutil.process_iter(attrs=['pid', 'name']):
        try:
            pid = proc.info['pid']
            io_counters = proc.net_io_counters()
            if io_counters:
                network_usage[pid] = {
                    'name': proc.info['name'],
                    'sent': io_counters.bytes_sent / (1024 * 1024),  
                    'recv': io_counters.bytes_recv / (1024 * 1024),  
                }
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue

    return network_usage

async def monitor_cpu(container_id): # This may not work for alpine sadly, but they cant do much with alpine.
    """
    Monitors CPU usage of a container and kills high-CPU processes.
    Stops monitoring if the container is deleted.
    """
    while True:
        try:

            result = await asyncio.create_subprocess_exec(
                'docker', 'ps', '--filter', f'id={container_id}', '-q',
                stdout=subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            if not stdout.decode('utf-8').strip():
                print(f"Container {container_id} has been deleted. Stopping monitoring.")
                break

            result = await asyncio.create_subprocess_exec(
                'docker', 'exec', container_id, 'top', '-b', '-n', '1',
                stdout=subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            output = stdout.decode('utf-8').strip()
            lines = output.splitlines()

            processes = None
            for i, line in enumerate(lines):
                if "PID" in line and "COMMAND" in line:  
                    processes = lines[i+1:]
                    break

            if processes is None:
                print(f"Unable to parse 'top' output for container {container_id}")
                await asyncio.sleep(5)
                continue

            for line in processes:
                columns = line.split()
                if len(columns) < 12:
                    continue  

                pid = columns[0]
                cpu_usage = float(columns[8])  
                process_name = columns[11].strip()

                # Command whitelist. *apt and http are required to install tmate*
                if any(proc in process_name.lower() for proc in ['apt', 'http', 'dpkg', 'dpkg-deb', 'store', 'deb-syste+', 'curl', 'xz', 'tar', 'python3.12', 'pip']):
                    continue  

                if cpu_usage > CPU_THRESHOLD:
                    await asyncio.create_subprocess_exec('docker', 'exec', container_id, 'kill', '-9', pid)
                    print(f"Killed process {process_name} (PID: {pid}, CPU: {cpu_usage}%)")

        except Exception as e:
            print(f"Error monitoring container {container_id}: {e}")

        await asyncio.sleep(5)

async def monitor_container(container_id):
    """
    Monitor both CPU and network usage for a container.
    """
    while True:
        try:

            await monitor_cpu(container_id)

            network_usage = await get_network_usage_per_process()
            for pid, stats in network_usage.items():
                total_usage = stats['sent'] + stats['recv']  
                if total_usage > BANDWIDTH_THRESHOLD_MBPS:

                    print(f"Killed process {stats['name']} (PID: {pid}) due to high network usage: {total_usage:.2f} MBps")
                    psutil.Process(pid).kill()

        except Exception as e:
            print(f"Error monitoring container {container_id}: {e}")

        await asyncio.sleep(5)

async def monitor_containers():
    """
    Monitor all running containers concurrently.
    """
    while True:
        try:

            result = await asyncio.create_subprocess_exec(
                'docker', 'ps', '-q',
                stdout=subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            container_ids = stdout.decode('utf-8').strip().splitlines()

            tasks = []
            for container_id in container_ids:
                tasks.append(monitor_container(container_id))

            await asyncio.gather(*tasks)  

        except Exception as e:
            print(f"Error checking containers: {e}")

        await asyncio.sleep(5)

def get_containers():

    result = subprocess.run(['docker', 'ps', '-a', '--format', '{{.ID}} {{.Names}}'], stdout=subprocess.PIPE)
    container_data = result.stdout.decode('utf-8').strip().splitlines()

    containers = []
    for line in container_data:
        container_id, container_name = line.split()
        containers.append({"id": container_id, "name": container_name})
    return containers

# This is broken because the container commands delete all containers at once.
'''
@client.tree.command(name="list-containers", description="Lists your containers.")
async def list_containers(interaction: discord.Interaction):
    containers = get_containers()
    if containers:
        response = "Here are the containers:\n"
        for container in containers:
            response += f"**{container['name']}** (ID: {container['id']})\n"
            response += f"Use `/delete-container {container['id']}`, `/stop-container {container['id']}`, `/start-container {container['id']}`, `/restart-container {container['id']}`\n"
        await interaction.response.send_message(response)
    else:
        await interaction.response.send_message("No containers are currently running.")
'''
@client.tree.command(name="deploy-ubuntu", description="Deploy an Ubuntu container.")
async def deploy_ubuntu(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    container_name = f"ubuntu_container_{user_id}"

    check_container = subprocess.run(
        ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    existing_container = check_container.stdout.decode('utf-8').strip()

    if existing_container == container_name:
        await interaction.response.send_message(f"Container `{container_name}` is already running.")
        return

    check_existing_stopped_container = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    existing_stopped_container = check_existing_stopped_container.stdout.decode('utf-8').strip()

    if existing_stopped_container == container_name:
        subprocess.run(["docker", "start", container_name])
        await interaction.response.send_message(f"Container `{container_name}` was restarted.")
    else:
        await interaction.response.send_message(f"Creating instance, this should only take a few seconds... | Powered by [Hagey VPS](https://discord.gg/XpKkXt9T9A)")

        subprocess.run([
            "docker", "run", "-d", "--name", container_name, 
            "--memory", MAX_MEMORY, DOCKER_IMAGE_UBUNTU, "bash", "-c", 
            """
            apt update && apt install -y tmate &&
            tmate -F
            """
        ])

    for _ in range(10):  
        docker_logs = subprocess.run(
            ["docker", "logs", container_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        log_output = docker_logs.stdout.decode('utf-8').strip()

        if "ssh session:" in log_output:
            tmate_link = log_output.split("ssh session: ")[1].strip()
            user = interaction.user
            await user.send(f"Your tmate session is ready! You can access it here: {tmate_link}")
            await interaction.followup.send(f"Container `{container_name}` is ready. A DM has been sent with the tmate session link.")
            return

        await asyncio.sleep(5)

    await interaction.followup.send(f"Error: Failed to initialize tmate session for `{container_name}`. Logs: {log_output}")

@client.tree.command(name="deploy-debian", description="Deploy a Debian container.")
async def deploy_debian(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    container_name = f"debian_container_{user_id}"

    check_container = subprocess.run(
        ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    existing_container = check_container.stdout.decode('utf-8').strip()

    if existing_container == container_name:
        await interaction.response.send_message(f"Container `{container_name}` is already running.")
        return

    check_existing_stopped_container = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    existing_stopped_container = check_existing_stopped_container.stdout.decode('utf-8').strip()

    if existing_stopped_container == container_name:
        subprocess.run(["docker", "start", container_name])
        await interaction.response.send_message(f"Container `{container_name}` was restarted.")
    else:
        await interaction.response.send_message(f"Creating instance, this should only take a few seconds... | Powered by [Hagey VPS](https://discord.gg/XpKkXt9T9A)")

        subprocess.run([
            "docker", "run", "-d", "--name", container_name, 
            "--memory", MAX_MEMORY, DOCKER_IMAGE_UBUNTU, "bash", "-c", 
            """
            apt update && apt install -y tmate &&
            tmate -F
            """
        ])

    for _ in range(10):  
        docker_logs = subprocess.run(
            ["docker", "logs", container_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        log_output = docker_logs.stdout.decode('utf-8').strip()

        if "ssh session:" in log_output:
            tmate_link = log_output.split("ssh session: ")[1].strip()
            user = interaction.user
            await user.send(f"Your tmate session is ready! You can access it here: {tmate_link}")
            await interaction.followup.send(f"Container `{container_name}` is ready. A DM has been sent with the tmate session link.")
            return

        await asyncio.sleep(5)

    await interaction.followup.send(f"Error: Failed to initialize tmate session for `{container_name}`. Logs: {log_output}")

@client.tree.command(name="deploy-alpine", description="Deploy a lightweight Alpine container.")
async def deploy_alpine(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    container_name = f"alpine_container_{user_id}"

    result = subprocess.run(
        ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if container_name in result.stdout.decode('utf-8'):
        await interaction.response.send_message(f"Container `{container_name}` is already running.")
        return

    await interaction.response.defer(thinking=True)
    subprocess.run([
        "docker", "run", "-d", "--name", container_name,
        "--memory", MAX_MEMORY, DOCKER_IMAGE_ALPINE, "sh", "-c",
        """
        echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories &&
        apk update &&
        apk add --no-cache tmate procps &&
        tmate -F
        """
    ])

    for _ in range(10):  
        docker_logs = subprocess.run(
            ["docker", "logs", container_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        log_output = docker_logs.stdout.decode('utf-8').strip()

        if "ssh session:" in log_output:
            tmate_link = log_output.split("ssh session: ")[1].strip()
            user = interaction.user
            await user.send(f"Your tmate session is ready! You can access it here: {tmate_link}")
            await interaction.followup.send(f"Container `{container_name}` is ready. A DM has been sent with the tmate session link.")
            asyncio.create_task(monitor_cpu(container_name))  
            return

        await asyncio.sleep(5)

    await interaction.followup.send(f"Error: Failed to initialize tmate session for `{container_name}`. Logs: {log_output}")

@client.tree.command(name="start-container", description="Starts your containers.")
async def start_container(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    container_names = [
        f"ubuntu_container_{user_id}",
        f"debian_container_{user_id}",
        f"alpine_container_{user_id}"
    ]

    for container_name in container_names:

        check_container = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        existing_container = check_container.stdout.decode('utf-8').strip()

        if existing_container == container_name:

            subprocess.run(["docker", "start", container_name])
            await interaction.response.send_message(f"Container `{container_name}` has been started.")
            return
        else:
            await interaction.response.send_message(f"Container `{container_name}` does not exist.")
            return

@client.tree.command(name="stop-container", description="Stops your containers.")
async def stop_container(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    container_names = [
        f"ubuntu_container_{user_id}",
        f"debian_container_{user_id}",
        f"alpine_container_{user_id}"
    ]

    for container_name in container_names:

        check_container = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        existing_container = check_container.stdout.decode('utf-8').strip()

        if existing_container == container_name:

            subprocess.run(["docker", "stop", container_name])
            await interaction.response.send_message(f"Container `{container_name}` has been stopped.")
            return
        else:
            await interaction.response.send_message(f"Container `{container_name}` does not exist.")
            return

@client.tree.command(name="restart-container", description="Restarts your containers.")
async def restart_container(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    container_names = [
        f"ubuntu_container_{user_id}",
        f"debian_container_{user_id}",
        f"alpine_container_{user_id}"
    ]

    for container_name in container_names:

        check_container = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        existing_container = check_container.stdout.decode('utf-8').strip()

        if existing_container == container_name:

            subprocess.run(["docker", "restart", container_name])
            await interaction.response.send_message(f"Container `{container_name}` has been restarted.")
            return
        else:
            await interaction.response.send_message(f"Container `{container_name}` does not exist.")
            return

@client.tree.command(name="delete-container", description="Deletes your containers.")
async def delete_container(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    ubuntu_container_name = f"ubuntu_container_{user_id}"
    debian_container_name = f"debian_container_{user_id}"
    alpine_container_name = f"alpine_container_{user_id}"

    check_ubuntu_container = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name={ubuntu_container_name}", "--format", "{{.Names}}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    ubuntu_container_exists = check_ubuntu_container.stdout.decode('utf-8').strip() == ubuntu_container_name
    if ubuntu_container_exists:
        subprocess.run(["docker", "rm", "-f", ubuntu_container_name])
        await interaction.response.send_message(f"Container `{ubuntu_container_name}` has been deleted.")
    else:
        await interaction.response.send_message(f"Container `{ubuntu_container_name}` does not exist.")

    check_debian_container = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name={debian_container_name}", "--format", "{{.Names}}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    debian_container_exists = check_debian_container.stdout.decode('utf-8').strip() == debian_container_name
    if debian_container_exists:
        subprocess.run(["docker", "rm", "-f", debian_container_name])
        await interaction.response.send_message(f"Container `{debian_container_name}` has been deleted.")
    else:
        await interaction.response.send_message(f"Container `{debian_container_name}` does not exist.")

    check_alpine_container = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name={alpine_container_name}", "--format", "{{.Names}}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    alpine_container_exists = check_alpine_container.stdout.decode('utf-8').strip() == alpine_container_name
    if alpine_container_exists:
        subprocess.run(["docker", "rm", "-f", alpine_container_name])
        await interaction.response.send_message(f"Container `{alpine_container_name}` has been deleted.")
    else:
        await interaction.response.send_message(f"Container `{alpine_container_name}` does not exist.")

    if not ubuntu_container_exists and not debian_container_exists and not alpine_container_exists:
        await interaction.response.send_message(f"No containers found for you to delete.")

async def update_bot_status():
    """
    Periodically updates the bot's status with the number of running Docker containers.
    """
    while True:
        try:

            running_containers = subprocess.run(
                ["docker", "ps", "-q"], stdout=subprocess.PIPE
            )
            num_containers = len(running_containers.stdout.decode().splitlines())

            await client.change_presence(activity=discord.Game(f'with {num_containers} instances running'))
        except Exception as e:
            print(f"Error updating bot status: {e}")

        await asyncio.sleep(5)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    await client.tree.sync()
    print(f'Synced commands.')
    try:
        client.loop.create_task(monitor_containers())
        print(f'Started monitoring containers.')
        await update_bot_status()
    except Exception as e:
        print(f'Error in monitor_containers: {e}')

if __name__ == "__main__":
    client.run(TOKEN)  
