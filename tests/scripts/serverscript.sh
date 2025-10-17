sudo bash -c 'cat > /tmp/check_server_live.sh <<'"'EOF'"'
#!/usr/bin/env bash
set -euo pipefail
printf "\n=== SERVER LIVE CHECK: %s ===\n" "$(date -u +"%Y-%m-%d %H:%M:%SZ")"
echo "--- Basic system ---"
echo "Hostname: $(hostname -f 2>/dev/null || hostname)"
echo "Uptime: $(uptime -p)"
echo "Load avg: $(cut -d " " -f1-3 /proc/loadavg)"
uname -a
echo

echo "--- CPU ---"
if command -v lscpu >/dev/null 2>&1; then
  lscpu | sed -n '1,8p'
else
  awk -F: '/model name|cpu MHz|CPU/ {print}' /proc/cpuinfo | uniq | sed -n '1,6p'
fi
echo "Top CPU consumers (snapshot):"
ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu | head -n 10
echo

echo "--- Memory ---"
free -h
echo "Top memory consumers:"
ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%mem | head -n 10
echo

echo "--- Swap ---"
swapon --show || echo "No swap active"
echo

echo "--- Disk ---"
df -hT --total
echo "Inode usage (filesystems):"
df -i | sed -n '1,5p'
echo
echo "Top used dirs (du) at / (may be slow, showing top 10 immediate children):"
for d in /*; do du -sh "$d" 2>/dev/null || true; done | sort -hr | head -n 10
echo

echo "--- Filesystem & mounts ---"
mount | sed -n '1,10p'
lsblk -f
echo

echo "--- Network ---"
echo "IP addresses:"
ip -4 addr show | sed -n '1,20p'
echo "Routing table:"
ip route show
echo "Listening sockets (tcp/udp):"
if command -v ss >/dev/null 2>&1; then
  ss -tulpen | sed -n '1,50p'
else
  netstat -tulpen 2>/dev/null | sed -n '1,50p' || true
fi
echo "Established connections (top remote endpoints):"
ss -tan | awk '\''/ESTAB/ {print $5}'\'' | cut -d: -f1 | sort | uniq -c | sort -nr | head -n 10
echo

echo "--- Firewall / Security ---"
if command -v ufw >/dev/null 2>&1; then
  echo "UFW status:"; ufw status verbose || true
fi
if command -v firewall-cmd >/dev/null 2>&1; then
  echo "firewalld active zones:"; firewall-cmd --get-active-zones || true
fi
if command -v sestatus >/dev/null 2>&1; then
  echo "SELinux:"; sestatus || true
elif command -v getenforce >/dev/null 2>&1; then
  echo "SELinux mode: $(getenforce 2>/dev/null || true)"
fi
echo

echo "--- Processes / Services ---"
echo "Top processes by CPU and MEM already shown above. Now systemctl critical services summary:"
for svc in nginx postgresql docker; do
  if systemctl list-units --type=service --all | grep -q "$svc"; then
    echo ">>> systemctl status $svc --no-pager (short):"
    systemctl is-active "$svc" && systemctl status "$svc" --no-pager --lines=3 || systemctl status "$svc" --no-pager --lines=3
  fi
done
echo

echo "--- Docker (if installed) ---"
if command -v docker >/dev/null 2>&1; then
  echo "Docker version: $(docker --version 2>/dev/null || true)"
  echo "Running containers:"
  docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" || true
  echo "All images (size):"
  docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | sed -n '1,20p' || true
  echo "Docker stats (single snapshot):"
  docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null || true
else
  echo "Docker not installed."
fi
echo

echo "--- PostgreSQL quick check (if reachable locally) ---"
if command -v psql >/dev/null 2>&1; then
  # try default socket / env — safe: will not show secrets
  echo "psql --version: $(psql --version 2>/dev/null || true)"
  echo "Postgres listening sockets:"
  ss -ltnp | grep postgres || true
  # show DB sizes if can connect via localhost without password prompt will fail harmlessly
  echo "Attempt to list databases (requires psql env):"
  psql -c "\l" 2>/dev/null || echo "Cannot list DBs (no auth or not running locally)."
else
  echo "psql client not installed."
fi
echo

echo "--- Logs (tail) ---"
echo "Last 50 syslog/journal messages:"
if command -v journalctl >/dev/null 2>&1; then
  journalctl -n 50 --no-pager
else
  tail -n 50 /var/log/syslog 2>/dev/null || tail -n 50 /var/log/messages 2>/dev/null || echo "No journal/syslog available."
fi
echo
if [ -f /var/log/nginx/error.log ]; then
  echo "Last 50 nginx error log lines:"
  tail -n 50 /var/log/nginx/error.log || true
fi
echo

echo "--- I/O and disk latency (basic) ---"
if command -v iostat >/dev/null 2>&1; then
  iostat -x 1 2 | sed -n '1,40p'
else
  echo "iostat not installed (sysstat). Skipping detailed I/O stats."
fi
echo

echo "--- Open files count ---"
if command -v lsof >/dev/null 2>&1; then
  echo "Open files (count): $(lsof -nP | wc -l)"
  echo "Top processes by open files:"
  lsof -nP | awk '\''{print $1,$2}'\'' | sed 1,1d | awk '{count[$0]++} END {for (i in count) print count[i], i}' | sort -nr | head -n 10 || true
else
  echo "lsof not installed."
fi
echo

echo "--- Summary / Recommendations ---"
echo "1) Check any FAILED/INACTIVE services above (systemctl)."
echo "2) If disk is >80% use, investigate largest directories shown."
echo "3) If memory/swap high, check top processes and consider resizing or optimizing."
echo "4) If unexpected ports listening, investigate services (ss output)."
echo "5) If Docker containers using lots of CPU/MEM, inspect logs and container configs."
echo

printf "=== END CHECK: %s ===\n\n" "$(date -u +"%Y-%m-%d %H:%M:%SZ")"
EOF
chmod +x /tmp/check_server_live.sh && /tmp/check_server_live.sh'
