from models import ActionCallback
from aiogram.utils.keyboard import InlineKeyboardBuilder

join_game_builder = InlineKeyboardBuilder()
join_game_builder.button(text="Start bot", url='https://t.me/jackbox_ua_bot') 
join_game_builder.button(text="Join", callback_data=ActionCallback(action='joingame'))
join_game_builder.button(text="Start!", callback_data=ActionCallback(action='startgame'))
join_game_builder.button(text="Stop!", callback_data=ActionCallback(action='stopgame'))
join_game_builder.adjust(1, 1, 1, 1)
    
game_stage1_q1_builder = InlineKeyboardBuilder()
game_stage1_q1_builder.button(text="Continue", callback_data=ActionCallback(action='continuegame1'))
game_stage1_q1_builder.button(text="-", callback_data=ActionCallback(action='none'))
game_stage1_q1_builder.button(text="Traitor lose!", callback_data=ActionCallback(action='traitorlose'))
game_stage1_q1_builder.adjust(1, 1)

game_stage1_q2_builder = InlineKeyboardBuilder()
game_stage1_q2_builder.button(text="Continue", callback_data=ActionCallback(action='continuegame2'))
game_stage1_q2_builder.button(text="-", callback_data=ActionCallback(action='none'))
game_stage1_q2_builder.button(text="Traitor lose!", callback_data=ActionCallback(action='traitorlose'))
game_stage1_q2_builder.adjust(1, 1)

game_stage1_q3_builder = InlineKeyboardBuilder()
game_stage1_q3_builder.button(text="Continue", callback_data=ActionCallback(action='continuegame3'))
game_stage1_q3_builder.button(text="-", callback_data=ActionCallback(action='none'))
game_stage1_q3_builder.button(text="Traitor lose!", callback_data=ActionCallback(action='traitorlose'))
game_stage1_q3_builder.adjust(1, 1)