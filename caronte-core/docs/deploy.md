# Deploy 

Para implementar, é necessário criar um serviço no Linux utilizando o **systemd**.

Pode usar como template a seguinte configuração para o serviço com uso de **Docker**:

```ini
[Unit]
Description=caronte
After=network.target docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/caronte/         # localização dos arquivos
ExecStart=/opt/caronte/bin/deploy.sh
ExecStop=/opt/caronte/bin/stop.sh
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

após configurar o serviço, execute os seguintes comandos:

```
sudo systemctl daemon-reload
sudo systemctl enable caronte.service
sudo systemctl start caronte.service
```

## pasta docker

Dependendo do tamanho do disco, pode ser necessário mover a pasta `/var/lib/docker` para outro lugar.

```sh
sudo systemctl stop docker
```

Por padrão, os dados ficam em `/var/lib/docker`

```sh
# apenas se for querer salvar os dados
sudo rsync -aP /var/lib/docker/ /mnt/disco_docker/
```

`sudo nano /etc/docker/daemon.json`
```json
{
  "data-root": "/mnt/disco_docker"
}
```

```sh
sudo systemctl start docker
sudo rm -rf /var/lib/docker
```