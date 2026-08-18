"""schatveld_core — de gedeelde, autoritatieve spel-brain (pure Python, 0 deps).

Eén bron van waarheid voor Schatveld Weddewarden, gedeeld door:
  * de HTTP-API (Roblox-client)  en
  * de Minecraft-brug (datapack via RCON).
Zo delen beide werelden hetzelfde veld (0-100), dezelfde loot-randomizer en dezelfde
economie/handhaving.
"""
from . import config, field, loot, cadastre, economy
from .economy import Brain

__version__ = "1.0.0"
__all__ = ["Brain", "config", "field", "loot", "cadastre", "economy", "__version__"]
