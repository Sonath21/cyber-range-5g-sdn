## 2025-06-01 – Resolved Docker permissions

- Confirmed: Ubuntu 24.04 LTS (“noble”)
- Removed any old Docker snaps/packages
- Installed Docker CE (docker.service now present)
- Created “docker” group, added $USER to it, and fully re-logged in
- Verified `docker run --rm hello-world` works without sudo
- Installed docker-compose-plugin, vagrant, openssh-server, wireshark, tcpdump, VirtualBox, bat, fzf, tldr
