
from pyinfra import host
from pyinfra.operations import apt, server, files, systemd, docker
from pyinfra.facts.server import LinuxDistribution, Arch

# Get distribution info
distro = host.get_fact(LinuxDistribution)

def install_docker():
    apt.packages(
        name="Remove old Docker versions",
        packages=[
            "docker",
            "docker-engine",
            "docker.io",
            "containerd",
            "runc",
        ],
        present=False,
        _sudo=True,
    )

    # Install prerequisites
    apt.packages(
        name="Install prerequisites",
        packages=[
            "ca-certificates",
            "curl",
            "gnupg",
            "lsb-release",
        ],
        update=True,
        _sudo=True,
    )

    # Create keyrings directory
    files.directory(
        name="Create /etc/apt/keyrings directory",
        path="/etc/apt/keyrings",
        mode="755",
        _sudo=True,
    )

    # Add Docker's official GPG key (idempotent)
    docker_key_file = '/usr/share/keyrings/docker-archive-keyring.gpg'
    server.shell(
        name="Add Docker GPG key",
        commands=[
            f"test -f {docker_key_file} || curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o {docker_key_file}",
        ],
        _sudo=True,
    )

    # Add Docker repository (idempotent using files.line)
    arch_fact = host.get_fact(Arch)
    arch = 'arm64' if arch_fact == 'aarch64' else 'amd64'
    codename = host.get_fact(LinuxDistribution)['release_meta']['CODENAME']
    files.line(
        name="Add Docker repository",
        path="/etc/apt/sources.list.d/docker.list",
        line=f'deb [arch={arch} signed-by={docker_key_file}] https://download.docker.com/linux/ubuntu {codename} stable',
        present=True,
        _sudo=True,
    )

    # Update apt cache
    apt.update(
        name="Update apt cache",
        _sudo=True,
    )

    # Install Docker Engine, containerd, and Docker Compose plugin
    apt.packages(
        name="Install Docker Engine and Docker Compose",
        packages=[
            "docker-ce",
            "docker-ce-cli",
            "containerd.io",
            "docker-buildx-plugin",
            "docker-compose-plugin",
        ],
        _sudo=True,
    )

    # Enable and start Docker service
    systemd.service(
        name="Enable and start Docker service",
        service="docker",
        enabled=True,
        running=True,
        _sudo=True,
    )

    # Add current user to docker group (idempotent check)
    server.shell(
        name="Add user to docker group",
        commands=[
            f'usermod -aG docker {host.data.app_user}'
        ],
        _sudo=True,
    )

    # Verify Docker installation
    server.shell(
        name="Verify Docker installation",
        commands=[
            "docker --version",
            "docker compose version",
        ],
    )

def allow_ufw_port(port: int, description: str):
    server.shell(
        name=f"Allow ufw port ({port})",
        commands=[
            f"ufw allow {port}/tcp comment '{description}'"
        ],
        _sudo=True,
    )


def install_portainer():

    # Allow Portainer ports
    allow_ufw_port(9000, 'Portainer HTTP')
    allow_ufw_port(9443, 'Portainer HTTPS')
    allow_ufw_port(8000, 'Portainer Edge Agent')

    # Reload UFW to apply rules
    server.shell(
        name="Reload UFW firewall",
        commands=[
            "ufw reload"
        ],
        _sudo=True,
    )

    # Create Portainer volume (idempotent)
    docker.volume(
        name="Create Portainer volume",
        volume="portainer_data",
        present=True,
        _sudo=True,
    )

    docker.container(
        name="Deploy Portainer container",
        container="portainer",
        image="portainer/portainer-ce:lts",
        ports=[
            "8000:8000",
            "9443:9443",
            "9000:9000",
        ],
        present=True,
        volumes=[
            "portainer_data:/data",
            "/var/run/docker.sock:/var/run/docker.sock"
        ],
        pull_always=True,
        force=True
    )

# install_docker()
install_portainer()