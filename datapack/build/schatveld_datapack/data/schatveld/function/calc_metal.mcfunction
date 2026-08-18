execute store result score @s sv_x run data get entity @s Pos[0] 1
execute store result score @s sv_z run data get entity @s Pos[2] 1
# reduceer mod 101 (blijf binnen int-bereik)
scoreboard players operation @s sv_x %= #c101 sv_metal
scoreboard players operation @s sv_z %= #c101 sv_metal
# fix negatieve rest
execute if score @s sv_x matches ..-1 run scoreboard players add @s sv_x 101
execute if score @s sv_z matches ..-1 run scoreboard players add @s sv_z 101
# metal = (x*31 + z*17 + x*z) % 101
scoreboard players operation @s sv_metal = @s sv_x
scoreboard players operation @s sv_metal *= #c31 sv_const
scoreboard players operation #tz sv_const = @s sv_z
scoreboard players operation #tz sv_const *= #c17 sv_const
scoreboard players operation @s sv_metal += #tz sv_const
scoreboard players operation #xz sv_const = @s sv_x
scoreboard players operation #xz sv_const *= @s sv_z
scoreboard players operation @s sv_metal += #xz sv_const
scoreboard players operation @s sv_metal %= #c101 sv_metal
