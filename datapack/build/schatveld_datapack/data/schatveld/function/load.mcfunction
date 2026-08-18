# objectieven
scoreboard objectives add sv_metal dummy "Metaalwaarde"
scoreboard objectives add sv_x dummy
scoreboard objectives add sv_z dummy
scoreboard objectives add sv_role dummy "Rol"
scoreboard objectives add sv_choose trigger
scoreboard objectives add sv_coins dummy "MolCoin"
# graven detecteren: mined-objectieven voor typische marsch-grondblokken
scoreboard objectives add dig_dirt minecraft.mined:minecraft.dirt
scoreboard objectives add dig_grass minecraft.mined:minecraft.grass_block
scoreboard objectives add dig_coarse minecraft.mined:minecraft.coarse_dirt
scoreboard objectives add dig_mud minecraft.mined:minecraft.mud
scoreboard objectives add dig_clay minecraft.mined:minecraft.clay
scoreboard objectives add dig_gravel minecraft.mined:minecraft.gravel
scoreboard objectives add dig_sand minecraft.mined:minecraft.sand
scoreboard objectives add dig_farm minecraft.mined:minecraft.farmland
scoreboard objectives add dig_podzol minecraft.mined:minecraft.podzol
# hash-constanten
scoreboard players set #c101 sv_metal 101
tellraw @a {"text":"[Schatveld] geladen — /function schatveld:menu voor rol & detector","color":"gold"}
function schatveld:load_const
