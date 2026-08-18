#!/usr/bin/env bash
# Start de lokale Fabric-server (Modrinth-mods + Schatveld-datapack) voor de brug.
SRV="$HOME/Documents/schatveld/.mcserver"
# Java 21: gebruik bij voorkeur de systeem-JDK (java_home), anders de gebundelde in .mcserver.
JAVA="$(/usr/libexec/java_home -v 21 2>/dev/null)/bin/java"
[ -x "$JAVA" ] || JAVA="$(cat "$SRV/.javapath" 2>/dev/null)"
cd "$SRV" && nohup "$JAVA" -Xmx2G -jar fabric-server.jar nogui > server.log 2>&1 &
echo "server gestart (pid $!, java: $JAVA); RCON op 127.0.0.1:25575 wachtwoord 'schatveld'"
