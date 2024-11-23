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
import requests
import random
import re
import socket
import docker # For linux, make sure docker is running with sudo systemctl start docker
import json

# Load configuration from JSON
with open("config.json", "r") as config_file:
    config = json.load(config_file)

# Docker client setup
docker_client = docker.from_env()

# Discord bot setup
TOKEN = config["TOKEN"]
intents = discord.Intents.default()
client = commands.Bot(command_prefix="!", intents=intents)  # DO NOT CHANGE

# Docker image and resource settings
DOCKER_IMAGE_UBUNTU = config["DOCKER_IMAGES"]["UBUNTU"]
DOCKER_IMAGE_DEBIAN = config["DOCKER_IMAGES"]["DEBIAN"]
DOCKER_IMAGE_ALPINE = config["DOCKER_IMAGES"]["ALPINE"]
MAX_MEMORY = config["MAX_MEMORY"]

# Initialize other variables
user_last_command_time = {}
monitored_containers = {}

# !! Editing below this may result in the code not working. !!
def get_containers():
    result = subprocess.run(['docker', 'ps', '-a', '--format', '{{.ID}} {{.Names}}'], stdout=subprocess.PIPE)
    container_data = result.stdout.decode('utf-8').strip().splitlines()

    containers = []
    for line in container_data:
        container_id, container_name = line.split()
        containers.append({"id": container_id, "name": container_name})
    return containers

@client.tree.command(name="deploy-ubuntu", description="Deploy an Ubuntu container.")
async def deploy_ubuntu_with_tmate(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    container_name = f"ubuntu_container_{user_id}"

    # Check if the image exists locally
    try:
        docker_client.images.get(DOCKER_IMAGE_UBUNTU)
    except docker.errors.ImageNotFound:
        embed = discord.Embed(
            title="Pulling Image",
            description=f"# Pulling Docker image `{DOCKER_IMAGE_UBUNTU}`. This may take some time...",
            color=discord.Color.blue()
        )
        embed.set_footer(text="This is because the person hosting this bot has not pulled any images yet. This may take some time depending on your network speed.")
        await interaction.response.send_message(embed=embed)

        # Pull the Docker image
        try:
            docker_client.images.pull(DOCKER_IMAGE_UBUNTU)
        except Exception as e:
            await interaction.followup.send(f"# Error: Failed to pull Docker image `{DOCKER_IMAGE_UBUNTU}`. Details: {str(e)}")
            return

    # Check if the container is already running
    running_containers = docker_client.containers.list(filters={"name": container_name})
    if running_containers:
        embed = discord.Embed(
            title="Error",
            description=f"# Container `{container_name}` is already running.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return

    # Check if a stopped container exists
    all_containers = docker_client.containers.list(all=True, filters={"name": container_name})
    if all_containers:
        container = all_containers[0]
        container.start()
        embed = discord.Embed(
            title="Success",
            description=f"# Container `{container_name}` was restarted.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
    else:
        # Create a new container
        embed = discord.Embed(
            title="Creating Instance",
            description="# This should only take a few seconds...",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

        try:
            container = docker_client.containers.run(
                image=DOCKER_IMAGE_UBUNTU,
                name=container_name,
                detach=True,
                tty=True,
                stdin_open=True,
                mem_limit=MAX_MEMORY,
                command="bash -c 'apt update && apt install -y tmate && tmate -F'"
            )
        except Exception as e:
            await interaction.followup.send(f"# Error: Failed to create the container `{container_name}`. Details: {str(e)}")
            return

    # Wait for tmate SSH session to appear in logs
    for _ in range(10):
        logs = container.logs().decode('utf-8').strip()
        if "ssh session:" in logs:
            tmate_link = re.search(r"ssh session: (.+)", logs).group(1)

            # Send the tmate link to the user via DM
            try:
                await interaction.user.send(f"# Your tmate SSH session is ready: {tmate_link}")
                await interaction.followup.send(
                    f"# Container `{container_name}` is ready. A DM has been sent with the tmate SSH session link."
                )
            except Exception as e:
                await interaction.followup.send(f"# Error: Failed to send DM. Details: {str(e)}")
            return

        await asyncio.sleep(5)

    # If tmate SSH session fails to appear
    await interaction.followup.send(f"# Error: Failed to initialize tmate SSH session for `{container_name}`.")

@client.tree.command(name="deploy-debian", description="Deploy a Debian container.")
async def deploy_debian(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    container_name = f"debian_container_{user_id}"

    # Check if the image exists locally
    try:
        docker_client.images.get(DOCKER_IMAGE_DEBIAN)
    except docker.errors.ImageNotFound:
        embed = discord.Embed(
            title="Pulling Image",
            description=f"# Pulling Docker image `{DOCKER_IMAGE_DEBIAN}`. This may take some time...",
            color=discord.Color.blue()
        )
        embed.set_footer(text="This process might take a few minutes, depending on your network speed.")
        await interaction.response.send_message(embed=embed)

        # Pull the Docker image
        try:
            docker_client.images.pull(DOCKER_IMAGE_DEBIAN)
        except Exception as e:
            await interaction.followup.send(f"# Error: Failed to pull Docker image `{DOCKER_IMAGE_DEBIAN}`. Details: {str(e)}")
            return

    # Check if the container is already running
    running_containers = docker_client.containers.list(filters={"name": container_name})
    if running_containers:
        embed = discord.Embed(
            title="Error",
            description=f"# Container `{container_name}` is already running.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Stop the container first if you want to redeploy it.")
        await interaction.response.send_message(embed=embed)
        return

    # Check if a stopped container exists
    all_containers = docker_client.containers.list(all=True, filters={"name": container_name})
    if all_containers:
        container = all_containers[0]
        container.start()
        embed = discord.Embed(
            title="Success",
            description=f"# Container `{container_name}` was restarted.",
            color=discord.Color.green()
        )
        embed.set_footer(text="Container has been successfully restarted.")
        await interaction.response.send_message(embed=embed)
    else:
        # Create a new container
        embed = discord.Embed(
            title="Creating Instance",
            description="# This should only take a few seconds...",
            color=discord.Color.blue()
        )
        embed.set_footer(text="The container will initialize with tmate pre-installed.")
        await interaction.response.send_message(embed=embed)

        try:
            container = docker_client.containers.run(
                image=DOCKER_IMAGE_DEBIAN,
                name=container_name,
                detach=True,
                tty=True,
                stdin_open=True,
                mem_limit=MAX_MEMORY,
                command="bash -c 'apt update && apt install -y tmate && tmate -F'"
            )
        except Exception as e:
            await interaction.followup.send(f"# Error: Failed to create the container `{container_name}`. Details: {str(e)}")
            return

    # Wait for tmate SSH session to appear in logs
    for _ in range(10):
        logs = container.logs().decode('utf-8').strip()
        if "ssh session:" in logs:
            tmate_link = re.search(r"ssh session: (.+)", logs).group(1)

            # Send the tmate link to the user via DM
            try:
                await interaction.user.send(f"# Your tmate SSH session is ready: {tmate_link}")
                await interaction.followup.send(
                    f"# Container `{container_name}` is ready. A DM has been sent with the tmate SSH session link."
                )
            except Exception as e:
                await interaction.followup.send(f"# Error: Failed to send DM. Details: {str(e)}")
            return

        await asyncio.sleep(5)

    # If tmate SSH session fails to appear
    await interaction.followup.send(f"# Error: Failed to initialize tmate SSH session for `{container_name}`.")

@client.tree.command(name="deploy-alpine", description="Deploy a lightweight Alpine container.")
async def deploy_alpine(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    container_name = f"alpine_container_{user_id}"

    # Check if the Alpine image exists locally
    try:
        docker_client.images.get(DOCKER_IMAGE_ALPINE)
    except docker.errors.ImageNotFound:
        embed = discord.Embed(
            title="Pulling Image",
            description=f"# Pulling Docker image `{DOCKER_IMAGE_ALPINE}`. This may take some time...",
            color=discord.Color.blue()
        )
        embed.set_footer(text="This process might take a few minutes, depending on your network speed.")
        await interaction.response.send_message(embed=embed)

        # Pull the Docker image
        try:
            docker_client.images.pull(DOCKER_IMAGE_ALPINE)
        except Exception as e:
            await interaction.followup.send(f"# Error: Failed to pull Docker image `{DOCKER_IMAGE_ALPINE}`. Details: {str(e)}")
            return

    # Check if the container is already running
    running_containers = docker_client.containers.list(filters={"name": container_name})
    if running_containers:
        embed = discord.Embed(
            title="Error",
            description=f"# Container `{container_name}` is already running.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Stop the container first if you want to redeploy it.")
        await interaction.response.send_message(embed=embed)
        return

    # Check if a stopped container exists
    all_containers = docker_client.containers.list(all=True, filters={"name": container_name})
    if all_containers:
        container = all_containers[0]
        container.start()
        embed = discord.Embed(
            title="Success",
            description=f"# Container `{container_name}` was restarted.",
            color=discord.Color.green()
        )
        embed.set_footer(text="Container has been successfully restarted.")
        await interaction.response.send_message(embed=embed)
    else:
        # Create a new container
        embed = discord.Embed(
            title="Creating Instance",
            description="# This should only take a few seconds...",
            color=discord.Color.blue()
        )
        embed.set_footer(text="The container will initialize with tmate pre-installed.")
        await interaction.response.send_message(embed=embed)

        try:
            container = docker_client.containers.run(
                image=DOCKER_IMAGE_ALPINE,
                name=container_name,
                detach=True,
                tty=True,
                stdin_open=True,
                mem_limit=MAX_MEMORY,
                command="sh -c 'echo \"http://dl-cdn.alpinelinux.org/alpine/edge/testing\" >> /etc/apk/repositories && apk update && apk add --no-cache tmate procps && tmate -F'"
            )
        except Exception as e:
            await interaction.followup.send(f"# Error: Failed to create the container `{container_name}`. Details: {str(e)}")
            return

    # Wait for tmate SSH session to appear in logs
    for _ in range(10):
        logs = container.logs().decode('utf-8').strip()
        if "ssh session:" in logs:
            tmate_link = re.search(r"ssh session: (.+)", logs).group(1)

            # Send the tmate link to the user via DM
            try:
                await interaction.user.send(f"# Your tmate SSH session is ready: {tmate_link}")
                await interaction.followup.send(
                    f"# Container `{container_name}` is ready. A DM has been sent with the tmate SSH session link."
                )
            except Exception as e:
                await interaction.followup.send(f"# Error: Failed to send DM. Details: {str(e)}")
            return

        await asyncio.sleep(5)

    # If tmate SSH session fails to appear
    await interaction.followup.send(f"# Error: Failed to initialize tmate SSH session for `{container_name}`.")

@client.tree.command(name="start-container", description="Starts your containers.")
async def start_container(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    container_names = [
        f"ubuntu_container_{user_id}",
        f"debian_container_{user_id}",
        f"alpine_container_{user_id}"
    ]

    # Flag to track if we need to send a response
    response_sent = False

    for container_name in container_names:
        check_container = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        existing_container = check_container.stdout.decode('utf-8').strip()

        if existing_container == container_name:
            subprocess.run(["docker", "start", container_name])
            if not response_sent:
                await interaction.response.send_message(f"Container `{container_name}` has been started.")
                response_sent = True
        else:
            if not response_sent:
                await interaction.response.send_message(f"Container `{container_name}` does not exist.")
                response_sent = True

@client.tree.command(name="stop-container", description="Stops your containers.")
async def stop_container(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    container_names = [
        f"ubuntu_container_{user_id}",
        f"debian_container_{user_id}",
        f"alpine_container_{user_id}"
    ]

    # Flag to track if we need to send a response
    response_sent = False

    for container_name in container_names:
        check_container = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        existing_container = check_container.stdout.decode('utf-8').strip()

        if existing_container == container_name:
            subprocess.run(["docker", "stop", container_name])
            if not response_sent:
                await interaction.response.send_message(f"Container `{container_name}` has been stopped.")
                response_sent = True
        else:
            if not response_sent:
                await interaction.response.send_message(f"Container `{container_name}` does not exist.")
                response_sent = True

@client.tree.command(name="restart-container", description="Restarts your containers.")
async def restart_container(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    container_names = [
        f"ubuntu_container_{user_id}",
        f"debian_container_{user_id}",
        f"alpine_container_{user_id}"
    ]

    # Flag to track if we need to send a response
    response_sent = False

    for container_name in container_names:
        check_container = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        existing_container = check_container.stdout.decode('utf-8').strip()

        if existing_container == container_name:
            subprocess.run(["docker", "restart", container_name])
            if not response_sent:
                await interaction.response.send_message(f"Container `{container_name}` has been restarted.")
                response_sent = True
        else:
            if not response_sent:
                await interaction.response.send_message(f"Container `{container_name}` does not exist.")
                response_sent = True

@client.tree.command(name="delete-container", description="Deletes your containers.")
async def delete_container(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    container_names = [
        f"ubuntu_container_{user_id}",
        f"debian_container_{user_id}",
        f"alpine_container_{user_id}"
    ]

    # Flag to track if any container was found and deleted
    response_sent = False

    for container_name in container_names:
        check_container = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        existing_container = check_container.stdout.decode('utf-8').strip()

        if existing_container == container_name:
            subprocess.run(["docker", "rm", "-f", container_name])
            if not response_sent:
                await interaction.response.send_message(f"Container `{container_name}` has been deleted.")
                response_sent = True
        else:
            if not response_sent:
                await interaction.response.send_message(f"Container `{container_name}` does not exist.")
                response_sent = True

    # If no containers were found for deletion
    if not response_sent:
        await interaction.response.send_message("No containers found for you to delete.")

async def update_bot_status():
    """
    Periodically updates the bot's status with the number of running Docker containers.
    """
    while True:
        try:
            # Get the list of running containers
            running_containers = subprocess.run(
                ["docker", "ps", "-q"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            
            # Check for errors in the subprocess call
            if running_containers.stderr:
                raise Exception(f"Error while checking Docker containers: {running_containers.stderr.decode()}")

            # Get the number of running containers
            num_containers = len(running_containers.stdout.decode().splitlines())

            # Update the bot's status
            await client.change_presence(activity=discord.Game(f'with {num_containers} instances running'))
        except Exception as e:
            print(f"Error updating bot status: {e}")

        # Update every 5 seconds
        await asyncio.sleep(5)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    await client.tree.sync()
    print(f'Synced commands.')

    try:
        print(f'Started monitoring containers.')
        # Start the status update loop
        await update_bot_status()
    except Exception as e:
        print(f'Error in monitoring containers: {e}')

if __name__ == "__main__":
    client.run(TOKEN)
