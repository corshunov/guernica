- make initial preparations
  * flash image to SD card  
    `sudo dd if=<image>.img of=/dev/sdX bs=4M status=progress && sync`
  * power on RPi with physical screen and keyboard connected to create user (tami:tami)
  * log in with created user

- change setting via `sudo raspi-config`
  * enable SSH server
  * enable hardware UART (serial port) without console (no login shell)
  * connect to WiFi
    Country: Israel

- reboot

- check IP and connect via SSH

- install packages
  ```
  apt update
  apt upgrade -y
  apt autoremove
  apt install -y vim tree screen git python3-pip openvpn mpv socat
  ```

- create `/home/tami/.screenrc` config file with line  
  `hardstatus alwayslastline "%{= KW} %H %{= Kw}|%{-} %-Lw%{= bW}%    n%f %t%{-}%+Lw %=%c %d.%m.%Y "`

- change hostname
  * copy `/etc/rc.local` script
  * make the script executable
  * execute the script and note new hostname

- set up WiFi
  * copy NetworkManager connections
  * set owner to `root` with `600` rights
  * copy `/root/check_hotspot.sh` script
  * make the script executable
  * create cron job for the script  
    Execute `crontab -e` and add line to the end:  
    `* * * * * /root/check_hotspot.sh`

- reboot

- set up VPN (based on [this](https://github.com/OpenVPN/openvpn/blob/master/doc/man-sections/example-fingerprint.rst) instruction)
  * copy client config file to `/etc/openvpn/client/client.conf`
  * generate private key and certificate with the command below and paste them into `client.conf`  
    `openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:secp384r1 -keyout - -nodes -sha256 -days 3650 -subj "/CN=$(hostname)"`
  * generate fingerprint with the command below and paste it into `server.conf` on server  
    `openssl x509 -fingerprint -sha256 -noout -in /etc/openvpn/client/client.conf`
  * create file `/etc/openvpn/server/server-clients/<hostname>` with the following content (replace `x` with proper number)  
    `ifconfig-push 10.1.10.x 255.255.255.0`
  * enable and start service
    ```
    systemctl enable openvpn-client@client.service
    systemctl start openvpn-client@client.service
    ```

- set up this repo
  * copy private and public keys to `/home/tami/.ssh/id_ed25519` and `/home/tami/.ssh/id_ed25519.pub` accordingly
  * download repo and set up Python environment
  ```
  git clone git@github.com:corshunov/guernica.git /home/tami/guernica
  cd /home/tami/guernica
  python -m venv .venv
  pip install -r requirements.txt
  pip install -r requirements_debug.txt # in case you want to debug via Jupyter
  ```

- set up Jupyter (in case you want to debug via Jupyter)
  * generate config
  `jupyter notebook --generate-config`
  * adjust the following settings in config file `/home/tami/.jupyter/jupyter_notebook_config.py`
  ```
  c.ServerApp.allow_origin = '*'
  c.ServerApp.ip = '0.0.0.0'
  ```
  * set password via `jupyter notebook password`

