#!/bin/bash
# Minecraft sunucu yönetimi: mc start|stop|restart|status|console|log
DIR=/home/cinar/mcserver
JAVA=/usr/lib/jvm/java-11-openjdk/bin/java
PIPE="$DIR/console.in"
LOG="$DIR/logs/run.log"
PORT=25565

is_up() { ss -tln 2>/dev/null | grep -q ":$PORT "; }
srv_pid() { ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oP 'pid=\K[0-9]+' | head -1; }

start() {
  if is_up; then echo "Zaten çalışıyor (pid $(srv_pid))."; return 0; fi
  cd "$DIR" || exit 1
  [ -p "$PIPE" ] || mkfifo "$PIPE"
  sleep infinity > "$PIPE" &
  echo $! > "$DIR/.holder.pid"
  nohup "$JAVA" -Xms4G -Xmx4G \
    -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 \
    -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch \
    -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M \
    -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 \
    -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 \
    -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 \
    -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 \
    -jar paper.jar nogui < "$PIPE" > "$LOG" 2>&1 &
  echo "Başlatılıyor... (log: mc log)"
  for i in $(seq 1 60); do grep -q "For help" "$LOG" 2>/dev/null && { echo "Hazır. Adres: localhost / $(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K[0-9.]+')"; return 0; }; sleep 1; done
  echo "60sn'de açılmadı, 'mc log' bak."
}

stop() {
  if ! is_up; then echo "Zaten kapalı."; return 0; fi
  echo "stop" > "$PIPE"
  for i in $(seq 1 30); do is_up || { echo "Durdu."; [ -f "$DIR/.holder.pid" ] && kill "$(cat "$DIR/.holder.pid")" 2>/dev/null; rm -f "$DIR/.holder.pid"; return 0; }; sleep 1; done
  echo "Durmadı, zorla kapatılıyor."; kill "$(srv_pid)" 2>/dev/null
}

status() {
  if is_up; then
    local pid; pid=$(srv_pid)
    local mem; mem=$(ps -o rss= -p "$pid" 2>/dev/null | awk '{printf "%.1fG",$1/1024/1024}')
    echo "ÇALIŞIYOR  pid=$pid  RAM=$mem  port=$PORT"
    echo "Adres: localhost  |  LAN: $(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K[0-9.]+')"
  else
    echo "KAPALI"
  fi
}

console() {
  if ! is_up; then echo "Sunucu kapalı."; return 1; fi
  if [ -n "$1" ]; then echo "$*" > "$PIPE"; echo "Gönderildi: $*"; else
    echo "Komut yaz (çıkış: Ctrl+C). Çıktı için ayrı terminalde: mc log"
    while read -r -p "> " line; do echo "$line" > "$PIPE"; done
  fi
}

case "$1" in
  start)   start ;;
  stop)    stop ;;
  restart) stop; sleep 2; start ;;
  status)  status ;;
  console) shift; console "$@" ;;
  log)     tail -f "$LOG" ;;
  tui|panel|admin) exec python3 "$DIR/panel.py" ;;
  *) echo "Kullanım: mc {start|stop|restart|status|console [komut]|log|tui}" ;;
esac
