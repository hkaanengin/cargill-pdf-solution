#!/usr/bin/env bash
# One-time setup of a fresh Ubuntu VM on Oracle Cloud. Run it on the VM:
#
#   bash setup-vm.sh
#
# Then log out and back in, so the docker group applies, and run
# deploy/deploy.sh from your own machine.
set -euo pipefail

sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2 rsync
# Docker starts on boot, and brings the app back up with it (restart policy in
# compose.yaml). Starting the VM is all it takes to start the app (R35).
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"

# Oracle's Ubuntu images ship an iptables rule set that rejects everything
# except SSH, on top of the security list in the console. Open 80 and 443 here too.
for rule in "tcp --dport 80" "tcp --dport 443" "udp --dport 443"; do
  # shellcheck disable=SC2086
  sudo iptables -C INPUT -p $rule -j ACCEPT 2>/dev/null \
    || sudo iptables -I INPUT -p $rule -j ACCEPT
done
if command -v netfilter-persistent >/dev/null; then
  sudo netfilter-persistent save
fi

echo "Done. Log out and back in, then run deploy/deploy.sh from your machine."
