# Nextcloud to prom

Get Nextcloud server's info in JSON and convert to [node_exporter textfile format](https://github.com/prometheus/node_exporter?tab=readme-ov-file#textfile-collector).

## Install

### On Nextcloud

* Make sur that application server info is enable:

```bash
https://domain.ltd/settings/admin/serverinfo
```

* Set a token:

```bash
occ config:app:set serverinfo token --value MY_TOKEN
```

### On your server

* Create folder /var/lib/prometheus/node-exporter

```bash
mkdir /var/lib/prometheus/node-exporter
chown prometheus:prometheus /var/lib/prometheus/node-exporter
```

* Allow collect textfiles from it:

```bash
cat /etc/default/node_exporter
NODE_EXPORTER_OPTS="--collector.textfile.directory=/var/lib/prometheus/node-exporter"
```

* Get scripts:

```bash
cd /tmp
git clone https://github.com/llaumgui/nextcloud2prom.git
cd nextcloud2prom
```

* Install requirements from `dnf`, `apt`, etc. Or use `pip`:

```bash
pip install -r requirements.txt
```

* Install scripts:

```bash
cp prom_nextcloud.py /usr/local/bin
chmod +x /usr/local/bin/prom_nextcloud.py
cp system.d/prom* /etc/systemd/system
```

* Edit /usr/local/bin/prom-nextcloud.py with your `NC_URL` and `NC_TOKEN` informations.
* Check:

```bash
systemd-analyze verify /etc/systemd/system/prom-nextcloud*
systemctl start prom-nextcloud.service
```

* and start systemd:

```bash
systemctl start prom-nextcloud.timer
systemctl enable prom-nextcloud.timer
```
