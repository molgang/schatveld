function schatveld:calc_metal
# < 10 = ALTIJD roestig ijzer
execute if score @s sv_metal matches ..9 run loot give @s loot schatveld:finds/rusty_iron
execute if score @s sv_metal matches ..9 run tellraw @s {"text":"Gevonden: roestig ijzer (metaalwaarde < 10)","color":"dark_gray"}
# banden
execute if score @s sv_metal matches 10..39 run function schatveld:reward/common
execute if score @s sv_metal matches 40..79 run function schatveld:reward/mid
execute if score @s sv_metal matches 80..100 run function schatveld:reward/rich
