scoreboard players set @s sv_role 2
tag @s add sv_archeoloog
tellraw @s {"text":"Rol: archeoloog","color":"yellow"}
function schatveld:shop/give_detector
give @s wooden_shovel[item_name='"Schep"',custom_data={sv_shovel:1b}]
