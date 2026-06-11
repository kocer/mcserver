#!/bin/bash
# Sunucu binary'lerini indirir (jar'lar repoda yok). Bir kez çalıştır.
set -e
cd "$(dirname "$0")"

PAPER_VER=1.16.5
ESS_VER=2.19.7

echo "==> Paper $PAPER_VER indiriliyor..."
BUILD=$(curl -s "https://api.papermc.io/v2/projects/paper/versions/$PAPER_VER/builds" \
  | grep -oP '"build":\K[0-9]+' | tail -1)
curl -fSL -o paper.jar \
  "https://api.papermc.io/v2/projects/paper/versions/$PAPER_VER/builds/$BUILD/downloads/paper-$PAPER_VER-$BUILD.jar"
echo "    paper.jar (build $BUILD)"

echo "==> EssentialsX $ESS_VER indiriliyor..."
mkdir -p plugins
curl -fSL -o plugins/EssentialsX.jar \
  "https://github.com/EssentialsX/Essentials/releases/download/$ESS_VER/EssentialsX-$ESS_VER.jar"
echo "    plugins/EssentialsX.jar"

echo "==> EULA kabul (eula.txt)"
echo "eula=true" > eula.txt

echo
echo "Hazır. Başlat:  ./mc.sh start   |   Panel:  ./mc.sh tui"
echo "NOT: Java 11 gerekir (1.16.5 için). mc.sh içindeki JAVA yolunu kontrol et."
