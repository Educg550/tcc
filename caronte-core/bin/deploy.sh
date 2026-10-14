#!/bin/bash
set -e 

## configurações recomendadas do *redis*
# Permitir overcommit (para fork não falhar)
sudo sysctl -w vm.overcommit_memory=1
echo "vm.overcommit_memory=1" | sudo tee -a /etc/sysctl.conf

# Evitar swap agressivo
sudo sysctl -w vm.swappiness=1
echo "vm.swappiness=1" | sudo tee -a /etc/sysctl.conf

# Desativar Transparent Huge Pages
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/defrag

git pull origin main

DIRECTORY=docker
DOCKER_DATA_PATH=${DOCKER_DATA_PATH:-./docker}

if [ ! -d "$DIRECTORY" ]; then
    echo "$DIRECTORY/ does not exist."
    exit 1
fi

volumes=(
    "postgres_data:999:999"
    "redis_cache:999:999"
    "shared_tmp:1001:1001"
    "clamd_socket:1001:1001"
    "shared_uploads:1001:1001"
)

for vol in "${volumes[@]}"; do
    IFS=":" read -r dir uid gid <<< "$vol"
    path="$DOCKER_DATA_PATH/$dir"

    sudo mkdir -p "$path"
    sudo chown -R $uid:$gid "$path"
    sudo chmod 755 "$path"
done

echo "Volumes criados e permissões ajustadas!"

cd static-assets
npm install
npm run build
cd ..

docker compose -f docker-compose.yml up --build -d --remove-orphans
    
docker image prune -a -f