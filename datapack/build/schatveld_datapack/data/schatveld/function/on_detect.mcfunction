advancement revoke @s only schatveld:use_detector
function schatveld:calc_metal
execute store result storage schatveld:tmp v int 1 run scoreboard players get @s sv_metal
tellraw @s ["",{"text":"Metaaldetector: ","color":"aqua"},{"score":{"name":"@s","objective":"sv_metal"},"color":"yellow","bold":true},{"text":"/100","color":"gray"}]
execute if score @s sv_metal matches ..9 run tellraw @s {"text":"  < 10 → hier ligt alleen roestig ijzer.","color":"dark_gray"}
execute if score @s sv_metal matches 80.. run tellraw @s {"text":"  hoge waarde! graaf hier.","color":"gold"}
