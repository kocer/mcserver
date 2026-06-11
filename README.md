# mcserver — Minecraft 1.16.5 LAN sunucu + TUI admin panel

Paper 1.16.5 + EssentialsX, LAN paylaşımı, tek komut yönetimi (`mc`) ve
Textual tabanlı sekmeli admin panel (`mc tui`).

## Kurulum

```bash
git clone <repo> mcserver && cd mcserver
./setup.sh          # Paper + EssentialsX jar'larını indirir, eula kabul eder
./mc.sh start       # sunucuyu başlatır (arka plan, 4G RAM)
```

Gereksinim: **Java 11** (1.16.5 için). `mc.sh` içindeki `JAVA` değişkeni
`/usr/lib/jvm/java-11-openjdk/bin/java`'ya bakar — sistemine göre düzelt.

İstersen `mc.sh` ve `panel.py`'yi PATH'e bağla:
```bash
ln -sf "$PWD/mc.sh" ~/.local/bin/mc
```

## Yönetim komutu: `mc`

| Komut | İş |
|-------|-----|
| `mc start` | başlat (arka plan, 4G, Aikar GC flagleri) |
| `mc stop` | düzgün durdur |
| `mc restart` | yeniden başlat |
| `mc status` | çalışıyor mu, pid/RAM/LAN adresi |
| `mc console "komut"` | konsola tek komut gönder |
| `mc console` | interaktif konsol |
| `mc log` | canlı log akışı |
| `mc tui` | admin panel (TUI) |

## Admin panel (`mc tui`)

Textual TUI, 4 sekme:

- **Konsol** — canlı renkli log + serbest komut girişi
- **Oyuncular** — online liste; seçince sağda tam `whois` bilgisi
  (can, açlık, konum, IP, gamemode, OP, playtime, AFK...). OP/DEOP/Kick/Ban/IP-Ban.
- **Yasaklı** — yasaklı oyuncu/IP listesi, Pardon / Pardon-IP
- **Sunucu** — Start/Stop/Restart, zorluk (peaceful/easy/normal/hard),
  save-all / gündüz / gece / hava

Kısayollar: `Ctrl+R` yenile, `Ctrl+C` çık.

Gereksinim (panel): Python 3 + `textual`.
```bash
pip install --user textual
```

## Bağlanma

- Aynı PC: `localhost`
- LAN: sunucu IP'si (panel/`mc status` gösterir), port `25565`
- Sürüm: **Minecraft Java 1.16.5**

ufw aktifse portu aç:
```bash
sudo ufw allow 25565/tcp && sudo ufw allow 25565/udp
```

## Notlar

- `online-mode=false` (offline/cracked istemci). Sadece güvenilir LAN'da kullan.
- `keepInventory=true` (3 dünyada da).
- Jar'lar, dünya verisi, loglar ve oyuncu json'ları repoya dahil değil
  (`.gitignore`). Binary'ler `setup.sh` ile gelir.
