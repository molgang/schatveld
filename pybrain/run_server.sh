#!/usr/bin/env bash
# Start de lokale Fabric-server (Modrinth-mods + Schatveld-datapack) voor de brug.
SRV="$HOME/Documents/schatveld/.mcserver"
JAVA=$(cat "$SRV/.javapath")
cd "$SRV" && nohup "$JAVA" -Xmx2G -jar fabric-server.jar nogui > server.log 2>&1 &
echo "server gestart (pid $!); RCON op 127.0.0.1:25575 wachtwoord 'schatveld'"
