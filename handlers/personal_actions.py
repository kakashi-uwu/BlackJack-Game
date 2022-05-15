import json
import random

from aiogram import types
from dispatcher import dp
from dispatcher import bot
from bot import db

from game_controls import Game_controls, Keyboard

dealer_score = 0

# keyboard
kbd = Keyboard()
main_menu_markup = kbd.new_game()

# get help command
@dp.message_handler(commands=['help'])
async def info_help(message: types.Message):
    await message.answer("Связаться с разработчиком: @bug_lag_feature")

# get balance command
@dp.message_handler(commands=['balance'])
async def get_balance(message: types.Message):
    user = db.load_user(message.from_user.id)
    await message.answer("💰 Баланс: "+ str(user['balance']))

# get rules command
@dp.message_handler(commands=['rules'])
async def rules(message: types.Message):
    await message.answer("""♦️ <b>Правила игры в Блэк-Джек (двадцать одно)</b> ♦️\n
Мы предоставим краткий свод правил для тех, кто никогда не играл в блэкджек.\n
Магическое число для блэкджека — 21.\nЗначения всех карт, розданных игроку, складываются, и если сумма превышает 21, игрок вылетает и мгновенно проигрывает.\n
Если игрок получает ровно 21, игрок выигрывает у дилера.\nВ противном случае для выигрыша сумма карт игрока должна быть больше суммы карт дилера.\n
Стоимости карт:
- Валет - 2 очка;\n- Дама - 3 очка;\n- Король - 4 очка;\n- Туз - 11 очков (если сумма карт больше 21, может стоить 1 очко);\nСтоимость остальных карт определяется их номиналом.""")

# start command 
@dp.message_handler(commands=['start'])
async def process_start_game(message: types.Message):
    '''bot start'''
    # register user if not exists
    user = db.load_user(message.from_user.id)
    if (not user):
        db.add_user(int(message.from_user.id))

    if (user['is_game'] == True):
        await message.answer("Для начала закончите старую игру")
        return

    db.update('user','is_game = ?','user_id = ?',(False,message.from_user.id,))
    await message.answer("♦️ Добро пожаловать в блэк-джек ♦️", reply_markup=main_menu_markup)

# main game logic
@dp.message_handler(content_types=["text"])
async def process_handler(message: types.Message):
    '''button handlers'''
    if message.chat.type == "private":
        if message.text == "Начать новую игру 🎮":
            user = db.load_user(message.from_user.id)
            if (user['is_game'] ==  True):
                await message.answer("Для начала закончите старую игру")
                return

            # updating deck of cards
            with open('static/deck_of_cards.json','r', encoding="utf-8") as input_f:
                deck = json.load(input_f)
            input_f.close()

            db.update(table='user', set='deck = ?', where='user_id = ?', values=(str(deck), message.from_user.id,))

            # update player score is he lost everything
            if user['balance'] < 1:
                user['balance'] = 100
                db.update(table='user', set='balance = ?, is_game = ?', where='user_id = ?', values=(100, True, message.from_user.id,))

            else: db.update(table='user', set='is_game = ?', where='user_id = ?', values=(True, message.from_user.id,))

            # keyboard
            kbd = Keyboard()
            game_type_markup = kbd.game_type()
            await bot.send_sticker(message.chat.id, "CAACAgIAAxkBAAEEtKFie91Ts3FZ99cztCfWqfxAqNn4FgACaQIAArrAlQUw5zOp4KLsaCQE")
            await message.answer("Добро пожаловать!\nВыберите тип игры", reply_markup=game_type_markup)

        if message.text == "Играть с компьютером 🧠":
            user = db.load_user(message.from_user.id)
            if (user['is_game'] == False):
                await message.answer("Для начала начните новую игру")
                return;

            # keyboard
            kbd = Keyboard()
            choose_pet_markup = kbd.pet(user)
            await message.answer("Сделайте ставку", reply_markup=choose_pet_markup)

        if ("🪙" in message.text or "Ва-банк! 🤑" in message.text):
            user = db.load_user(message.from_user.id)

            if (user['is_game'] == False):
                await message.answer("Для начала начните новую игру")
                return;

            '''Start game'''
            global dealer_score, player_score, player_cards, dealer_cards, pet
            # reset all our local variables
            deck         = []
            dealer_cards = []
            player_cards = []
            player_score = 0
            dealer_score = 0
            deck         = list(eval(user['deck']))

            # keyboard
            kbd = Keyboard()
            game_controls_markup = kbd.game_nav_1()
            
            if ("Ва-банк! 🤑" in message.text):
                pet = user['balance']
            else:
                pet = message.text.split()[0]

            db.update(table='user', set='pet = ?',where='user_id = ?', values=(pet, message.from_user.id,))
            user = db.load_user(message.from_user.id)

            if (int(pet) > int(user['balance'])):
                await message.answer("На вашем балансе недостаточно средств.")
                return

            await message.answer(f"Ставка в {message.text} принята.🤑 Приятной игры!")
            
            # Initial dealing. Two cards for both
            for i in range(2):
                # for player
                player_card = random.choice(deck)
                player_cards.append(player_card)
                deck.remove(player_card)
                player_score += player_card.get('cost')

                # for dealer
                dealer_card = random.choice(deck)
                dealer_cards.append(dealer_card)
                deck.remove(dealer_card)
                dealer_score += dealer_card.get('cost')

            # if both cards are Ace for player
            if player_cards[0].get('cost') == 11 and player_cards[1].get('cost') == 11:
                player_cards[0]['cost'] = 1
                player_score -= 10

            # if both cards are Ace for dealer
            if dealer_cards[0].get('cost') == 11 and dealer_cards[1].get('cost') == 11:
                dealer_cards[0]['cost'] = 1
                dealer_score -= 10

            db.update(table='user', set='player_score = ?, deck = ?, player_cards = ?, dealer_cards = ?, dealer_score = ?', where='user_id = ?', values=(player_score, str(deck), str(player_cards), str(dealer_cards), dealer_score, message.from_user.id,))

            img = Game_controls()
            img.render_cards([dealer_cards[0]['image'], 'static/images/back.png'], 2, f"{message.from_user.id}_out_dealer_close.webp")
            img.render_cards([player_cards[0]['image'], player_cards[1]['image']], 2, f"{message.from_user.id}_out_player.webp")
            
            # print            
            await bot.send_sticker(message.chat.id, sticker=open(f"static/images/{message.from_user.id}_out_dealer_close.webp", 'rb').read())
            await bot.send_message(message.chat.id, f"⬆️ 👽 <b>Карты дилера: </b> Скрыто")

            # print
            await bot.send_sticker(message.chat.id, sticker=open(f"static/images/{message.from_user.id}_out_player.webp", 'rb').read())
            user = db.load_user(message.from_user.id)
            await bot.send_message(message.chat.id, f"⬆️ 👨‍💼 <b>Ваши карты: </b> {user['player_score']}", reply_markup=game_controls_markup)

            # Player gets a blackjack  
            if (player_score == 21):
                global main_menu_markup
                current_win = float(pet)*float(1.5)
                total_win = float(pet)*float(1.5)+user['balance']
                db.update(table='user', set='player_score = ?, is_game = ?, balance = ?', where='user_id = ?', values=(user['player_score'], False, total_win, message.from_user.id, ))
                await message.answer(f"У вас Блэк-Джек! Вы победили! 🥃\n<b>Чистый выигрыш</b>: {current_win} 💴", reply_markup=main_menu_markup)

        # if player decides to go on
        if (message.text == "Еще 🟢"):
            user         = db.load_user(message.from_user.id)
            dealer_cards = list(eval(user['dealer_cards']))
            player_cards = list(eval(user['player_cards']))
            deck         = list(eval(user['deck']))

            if (user['is_game'] == False):
                await message.answer("Для начала начните новую игру")
                return;

            # randomly dealing a card for player
            player_card = random.choice(deck)
            player_cards.append(player_card)
            deck.remove(player_card)
            user['player_score'] += player_card.get('cost')

            db.update(table='user', set='player_score = ?, deck = ?, player_cards = ?', where='user_id = ?', values=(str(user['player_score']), str(deck), str(player_cards), message.from_user.id, ))

            # generate image
            img_path = []
            for i in range(len(player_cards)):
                img_path.append(player_cards[i]['image'])
            
            img = Game_controls()
            img.render_cards(img_path, len(player_cards), f"{message.from_user.id}_out_player.webp")
            img.render_cards([dealer_cards[0]['image'], 'static/images/back.png'], 2, f"{message.from_user.id}_out_dealer_close.webp")
            img.render_cards([dealer_cards[0]['image'], dealer_cards[1]['image']], 2, f"{message.from_user.id}_out_dealer_open.webp")

            # keyboard
            kbd = Keyboard()
            continue_game_controls_markup = kbd.game_nav_2()   

            # if player wons
            if (user['player_score'] == 21):
                current_win = float(user['pet'])*float(1.5)
                total_win = float(user['pet'])+user['balance'] # update win

                await bot.send_sticker(message.chat.id, sticker=open(f"static/images/{message.from_user.id}_out_dealer_open.webp", 'rb').read())
                user = db.load_user(message.from_user.id)
                await message.answer(f"⬆️ 👨‍💼 <b>Карты дилера: </b> {user['dealer_score']}")

                await bot.send_sticker(message.chat.id, sticker=open(f"static/images/{message.from_user.id}_out_player.webp", 'rb').read())
                user = db.load_user(message.from_user.id)
                await message.answer(f"⬆️ 👨‍💼 <b>Ваши карты: </b> {user['player_score']}\nВы победили! 🥃\n<b>Чистый выигрыш</b>: {current_win} 💴", reply_markup=main_menu_markup)
                db.update(table='user', set='balance = ?, is_game = ?', where='user_id = ?', values=(total_win, False, message.from_user.id, ))

                return;

            # if player picks too many cards
            if (user['player_score'] > 21):
                # updating scrore if player has Ace in them
                for i in player_cards:
                    if (i.get('value') == "Туз" and i.get('cost') == 11):
                        user['player_score']-=10
                        i['cost'] = 1
                        db.update(table='user', set='player_score = ?, player_cards = ?', where='user_id = ?', values=(user['player_score'], str(player_cards), message.from_user.id, ))

                # if player loses
                if (user['player_score'] > 21):
                    total_win = user['balance']-float(user['pet']) # update loss

                    await bot.send_sticker(message.chat.id, sticker=open(f"static/images/{message.from_user.id}_out_dealer_open.webp", 'rb').read())
                    user = db.load_user(message.from_user.id)
                    await message.answer(f"⬆️ 👨‍💼 <b>Карты дилера: </b> {user['dealer_score']}")

                    await bot.send_sticker(message.chat.id, sticker=open(f"static/images/{message.from_user.id}_out_player.webp", 'rb').read())
                    user = db.load_user(message.from_user.id)
                    await message.answer(f"⬆️ 👨‍💼 <b>Ваши карты: </b> {user['player_score']}\nПеребор! Вы проиграли ❌\nПроигрыш: -{float(user['pet'])}", reply_markup=main_menu_markup)
                    db.update(table='user', set='balance = ?, is_game = ?', where='user_id = ?', values=(total_win, False, message.from_user.id, ))
                    return;

            await bot.send_sticker(message.chat.id, sticker=open(f"static/images/{message.from_user.id}_out_dealer_close.webp", 'rb').read())
            user = db.load_user(message.from_user.id)
            await message.answer(f"⬆️ 👨‍💼 <b>Карты дилера: </b> Скрыто")

            await bot.send_sticker(message.chat.id, sticker=open(f"static/images/{message.from_user.id}_out_player.webp", 'rb').read())
            user = db.load_user(message.from_user.id)
            await message.answer(f"⬆️ 👨‍💼 <b>Ваши карты: </b> {user['player_score']}", reply_markup=continue_game_controls_markup)

        # if player decides to stand
        if (message.text == "Стоп 🛑"):
            user         = db.load_user(message.from_user.id)
            dealer_cards = list(eval(user['dealer_cards']))
            player_cards = list(eval(user['player_cards']))
            deck         = list(eval(user['deck']))
            img_path_dealer = []
            img_path        = []

            if (user['is_game'] == False):
                await message.answer("Для начала начните новую игру")
                return;

            # generate image for player
            for i in range(len(player_cards)):
                img_path.append(player_cards[i]['image'])
            
            img = Game_controls()
            img.render_cards(img_path, len(player_cards), f"{message.from_user.id}_out_player.webp")
            
            # managing dealer moves
            while (user['dealer_score'] < 17):
                # randomly dealing a card for dealer
                dealer_card = random.choice(deck)
                dealer_cards.append(dealer_card)
                deck.remove(dealer_card)
                user['dealer_score'] += dealer_card.get('cost')

                db.update(table='user', set='dealer_score = ?, deck = ?, dealer_cards = ?', where='user_id = ?', values=(str(user['dealer_score']), str(deck), str(dealer_cards), message.from_user.id, ))
                
                user = db.load_user(message.from_user.id)
                dealer_cards = list(eval(user['dealer_cards']))
                deck         = list(eval(user['deck']))
                
                img_path_dealer = []
                for i in range(len(dealer_cards)):
                    img_path_dealer.append(dealer_cards[i]['image'])

                img = Game_controls()
                img.render_cards(img_path_dealer, len(dealer_cards), f"{message.from_user.id}_out_dealer_open.webp")

                # if dealer picks too many cards
                if (user['dealer_score'] > 21):
                    # updating scrore if player has Ace in them
                    for i in dealer_cards:
                        if (i.get('value') == "Туз" and i.get('cost') == 11):
                            user['dealer_score']-=10
                            i['cost'] = 1
                            db.update(table='user', set='dealer_score = ?, dealer_cards = ?', where='user_id = ?', values=(user['dealer_score'], str(dealer_cards), message.from_user.id, ))
                    
                    # if dealer loses, player win
                    if (user['dealer_score'] > 21):
                        current_win = float(user['pet'])*float(1.5)
                        total_win = float(user['pet'])+user['balance'] # update player win

                        await bot.send_sticker(message.chat.id, sticker=open(f"static/images/{message.from_user.id}_out_dealer_open.webp", 'rb').read())
                        
                        user = db.load_user(message.from_user.id)
                        await message.answer(f"⬆️ 👽 <b>Карты дилера: </b> {user['dealer_score']}")
                        
                        await bot.send_sticker(message.chat.id, sticker=open(f"static/images/{message.from_user.id}_out_player.webp", 'rb').read())
                        user = db.load_user(message.from_user.id)
                        await message.answer(f"⬆️ 👨‍💼 <b>Ваши карты: </b> {user['player_score']}\nВы победили! 🥃\n<b>Чистый выигрыш</b>: {current_win} 💴", reply_markup=main_menu_markup)

                        db.update(table='user', set='balance = ?, is_game = ?', where='user_id = ?', values=(total_win, False, message.from_user.id, ))
                        return
                    break
                
            user = db.load_user(message.from_user.id)            
            dealer_cards = list(eval(user['dealer_cards']))

            for i in range(len(dealer_cards)):
                img_path_dealer.append(dealer_cards[i]['image'])

            img = Game_controls()
            img.render_cards(img_path_dealer, len(dealer_cards), f"{message.from_user.id}_out_dealer_open.webp")
            
            # if dealer loses, player win
            if (user['dealer_score'] < user['player_score']):
                current_win = float(user['pet'])*float(1.5)
                total_win = float(user['pet'])+user['balance'] # update player win
                
                await bot.send_sticker(message.chat.id, sticker=open(f"static/images/{message.from_user.id}_out_dealer_open.webp", 'rb').read())
                user = db.load_user(message.from_user.id)
                await message.answer(f"⬆️ 👽 <b>Карты дилера: </b> {user['dealer_score']}")
                
                await bot.send_sticker(message.chat.id, sticker=open(f"static/images/{message.from_user.id}_out_player.webp", 'rb').read())
                user = db.load_user(message.from_user.id)
                await message.answer(f"⬆️ 👨‍💼 <b>Ваши карты: </b> {user['player_score']}\nВы победили! 🥃\n<b>Чистый выигрыш</b>: {current_win} 💴", reply_markup=main_menu_markup)

                db.update(table='user', set='balance = ?, is_game = ?', where='user_id = ?', values=(total_win, False, message.from_user.id, ))

            # if player loses, dealer win
            if (user['dealer_score'] > user['player_score']):
                total_win = user['balance']-float(user['pet']) # update loss

                await bot.send_sticker(message.chat.id, sticker=open(f"static/images/{message.from_user.id}_out_dealer_open.webp", 'rb').read())
                user = db.load_user(message.from_user.id)
                await message.answer(f"⬆️ 👽 <b>Карты дилера: </b> {user['dealer_score']}")
                
                await bot.send_sticker(message.chat.id, sticker=open(f"static/images/{message.from_user.id}_out_player.webp", 'rb').read())
                user = db.load_user(message.from_user.id)
                await message.answer(f"⬆️ 👨‍💼 <b>Ваши карты: </b> {user['player_score']}\nВы проиграли ❌\nПроигрыш: -{float(user['pet'])}", reply_markup=main_menu_markup)

                db.update(table='user', set='balance = ?, is_game = ?', where='user_id = ?', values=(total_win, False, message.from_user.id, ))
        
            # if draw
            if (user['dealer_score'] == user['player_score']):
                await bot.send_sticker(message.chat.id, sticker=open(f"static/images/{message.from_user.id}_out_dealer_open.webp", 'rb').read())
                
                user = db.load_user(message.from_user.id)
                await message.answer(f"⬆️ 👽 <b>Карты дилера: </b> {user['dealer_score']}")
                
                await bot.send_sticker(message.chat.id, sticker=open(f"static/images/{message.from_user.id}_out_player.webp", 'rb').read())
                user = db.load_user(message.from_user.id)
                await message.answer(f"⬆️ 👨‍💼 <b>Ваши карты: </b> {user['player_score']}\nНичья", reply_markup=main_menu_markup)

        # if player gives up
        if (message.text == "Сдаюсь 😵"):
            user         = db.load_user(message.from_user.id)
            dealer_cards = list(eval(user['dealer_cards']))
            player_cards = list(eval(user['player_cards']))
            deck         = list(eval(user['deck']))

            if (user['is_game'] == False):
                await message.answer("Для начала начните новую игру")
                return;

            total_win = user['balance']-float(user['pet']) # update loss
            
            img = Game_controls()
            img.render_cards([dealer_cards[0]['image'], dealer_cards[1]['image']], 2, f"{message.from_user.id}_out_dealer_open.webp")
            
            await bot.send_sticker(message.chat.id, sticker=open(f"static/images/{message.from_user.id}_out_dealer_open.webp", 'rb').read())
            user = db.load_user(message.from_user.id)
            await message.answer(f"⬆️ 👽 <b>Карты дилера: </b> {user['dealer_score']}")
            
            await bot.send_sticker(message.chat.id, sticker=open(f"static/images/{message.from_user.id}_out_player.webp", 'rb').read())
            user = db.load_user(message.from_user.id)
            await message.answer(f"⬆️ 👨‍💼 <b>Ваши карты: </b> {user['player_score']}\nВы сдались :(\nПроигрыш: -{float(user['pet'])}", reply_markup=main_menu_markup)

            db.update(table='user', set='balance = ?, is_game = ?', where='user_id = ?', values=(total_win, False, message.from_user.id, ))

        # view balance
        if (message.text == "Просмотреть баланс 💰"):
            user = db.load_user(message.from_user.id)
            await message.answer("💰 Баланс: "+ str(user['balance']))