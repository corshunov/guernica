- make initial preparations
* flash image to SD card
sudo dd if=<image>.img of=/dev/sdX bs=4M status=progress && sync
* power on RPi with physical screen and keyboard connected to create user (tami:tami)
* log in with created user

- change setting via `sudo raspi-config`
* enable SSH server
* enable hardware UART (serial port) without console (no login shell)
* connect to WiFi
Country: Israel

- reboot

- check IP and connect via SSH

- packages
* apt update
* apt upgrade -y
* apt autoremove
* apt install -y vim tree screen git python3-pip openvpn mpv socat

- create '/home/tami/.screenrc' config file with line
hardstatus alwayslastline "%{= KW} %H %{= Kw}|%{-} %-Lw%{= bW}%    n%f %t%{-}%+Lw %=%c %d.%m.%Y "

- change hostname
* copy '/etc/rc.local' script
* make the script executable
* execute the script and note new hostname

- WiFi
* copy NetworkManager connections
* set owner to 'root' with '600' rights
* copy '/root/check_hotspot.sh' script
* make the script executable
* create cron job for the script
Execute `crontab -e` and add line to the end:
* * * * * /root/check_hotspot.sh

- reboot

- VPN
https://github.com/OpenVPN/openvpn/blob/master/doc/man-sections/example-fingerprint.rst

* copy client config file to '/etc/openvpn/client/client.conf'
* generate private key and certificate with the command below and paste them into 'client.conf'
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:secp384r1 -keyout - -nodes -sha256 -days 3650 -subj "/CN=`hostname`"
* generate fingerprint with the command below and paste it into 'server.conf' on server
openssl x509 -fingerprint -sha256 -noout -in /etc/openvpn/client/client.conf
* create file /etc/openvpn/server/server-clients/<hostname> with the following content (replace 'x' with proper number)
ifconfig-push 10.1.10.x 255.255.255.0
* enable and start service
systemctl enable openvpn-client@client.service
systemctl start openvpn-client@client.service
