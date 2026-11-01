# Imagen base del clúster: OpenMPI + GCC + SSH sin contraseña
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential make openmpi-bin libopenmpi-dev \
        openssh-server openssh-client htop python3 iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Usuario sin privilegios para correr MPI (sin contraseña: solo entra por clave SSH)
RUN useradd -m -s /bin/bash mpiuser && usermod -p '*' mpiuser

# SSH sin contraseña entre nodos.
# Se genera una clave durante el build y queda igual en los 3 nodos
# (solo para este clúster de pruebas; la clave no se guarda en el repositorio).
RUN mkdir -p /var/run/sshd && ssh-keygen -A \
    && mkdir -p /home/mpiuser/.ssh \
    && ssh-keygen -t ed25519 -N "" -f /home/mpiuser/.ssh/id_ed25519 \
    && cp /home/mpiuser/.ssh/id_ed25519.pub /home/mpiuser/.ssh/authorized_keys \
    && printf "Host *\n  StrictHostKeyChecking no\n  UserKnownHostsFile /dev/null\n  LogLevel ERROR\n" > /home/mpiuser/.ssh/config \
    && chmod 700 /home/mpiuser/.ssh \
    && chmod 600 /home/mpiuser/.ssh/id_ed25519 /home/mpiuser/.ssh/authorized_keys /home/mpiuser/.ssh/config \
    && chown -R mpiuser:mpiuser /home/mpiuser/.ssh \
    && sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config

# Ajustes de OpenMPI para correr dentro de contenedores
ENV OMPI_MCA_btl_vader_single_copy_mechanism=none \
    OMPI_MCA_btl_tcp_if_include=eth0

WORKDIR /home/mpiuser/proyecto
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
