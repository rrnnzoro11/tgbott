import telebot
import buttons
import database
from rich import print
from telebot import types

bot = telebot.TeleBot('8096141474:AAFIij09SktiKiLpd-JOe9KYK014mmlRK9w')

users = {}


# database.delete_product()
# database.delete_user()
# database.delete_all_users()
# database.delete_all_products()
# database.add_product('Hawaiian Delight', 150, 1234567887654, 'A sweet and savory masterpiece! Juicy pineapple chunks, tender ham, and a layer of mozzarella come together on a flavorful tomato sauce base. A tropical twist on a pizza classic!', 'https://dinnerthendessert.com/wp-content/uploads/2023/06/Hawaiian-Pizza-7.jpg')

@bot.message_handler(commands=['start'])
def start_message(message):
    # получаем тг ид
    user_id = message.from_user.id
    # Проверка пользователя
    checker = database.check_user(user_id)

    # Если пользователь есть в базе
    if checker:
        # Получаем актуальный список продуктов
        products = database.get_pr_name_id()
        print(products)

        # Отправим сообщение с меню
        bot.send_message(user_id, 'Hello 👋, welcome to our <b>FastPizza</b> pizzeria bot 🍕', parse_mode='HTML')
        bot.send_message(user_id, 'Menu ⬇️', reply_markup=buttons.main_menu(products))

    # Если пользователя нету в базе
    elif not checker:
        bot.send_message(user_id, 'Hello 👋, send your name to register')

        # Переход на этап получения имени
        bot.register_next_step_handler(message, get_name)


# Этап получении имени
def get_name(message):
    user_id = message.from_user.id

    # сохранить имю в переменную
    username = message.text

    # Отправим ответ
    bot.send_message(user_id, 'Send your phone number 📞', reply_markup=buttons.number_buttons())
    # перенаправить на этап получения номера
    bot.register_next_step_handler(message, get_number, username)


# получаем номер пользователя
def get_number(message, name):
    user_id = message.from_user.id

    if message.contact:
        # сохраняем контакт
        phone_number = message.contact.phone_number

        # Сохраняем его в базе
        database.register_user(user_id, name, phone_number, 'Not yet')
        bot.send_message(user_id, f'You have successfully registered ✅, <b>{name}</b> !', parse_mode='HTML',
                         reply_markup=telebot.types.ReplyKeyboardRemove()),

        # Открываем меню
        products = database.get_pr_name_id()
        bot.send_message(user_id, 'Menu ⬇️', reply_markup=buttons.main_menu(products))

    # если пользователь не отправил контакт
    elif not message.contact:
        bot.send_message(user_id, 'Send contact using the button 📞', reply_markup=buttons.number_buttons())

        # Обратно на этап получения номера
        bot.register_next_step_handler(message, get_number, name)

# Обработчик выбора количества
@bot.callback_query_handler(lambda call: call.data in ['plus', 'minus', 'to_cart', 'back'])
def get_user_product_count(call):
    # Сохраним айди пользователя
    user_id = call.message.chat.id

    # Если пользователь нажал на +
    if call.data == 'plus':
        print(users)
        actual_count = users[user_id]['pr_count']
        print(actual_count)
        print(call)
        users[user_id]['pr_count'] += 1
        # Меняем значение кнопки
        bot.edit_message_reply_markup(chat_id=user_id,
                                      message_id=call.message.message_id,
                                      reply_markup=buttons.choose_product_count('plus', actual_count))

    # Если пользователь нажал на -
    elif call.data == 'minus':
        print(users)
        actual_count = users[user_id]['pr_count']
        print(actual_count)
        print(call)
        users[user_id]['pr_count'] -= 1
        # Меняем значение кнопки
        bot.edit_message_reply_markup(chat_id=user_id,
                                      message_id=call.message.message_id,
                                      reply_markup=buttons.choose_product_count('minus', actual_count))

    # back
    # Если пользователь нажал 'назад'
    elif call.data == 'back':
        # Получаем меню
        products = database.get_pr_name_id()
        # меняем на меню
        bot.edit_message_text('Menu ⬇️',
                              user_id,
                              call.message.message_id,
                              reply_markup=buttons.main_menu(products))

    # Если нажал Добавить в корзину
    elif call.data == 'to_cart':
        # Получаем данные
        product_count = users[user_id]['pr_count']
        user_product = users[user_id]['pr_name']
        print(users)
        # Добавляем в базу(корзина пользователя)
        database.add_product_to_cart(user_id, user_product, product_count)

        # Получаем обратно меню
        products = database.get_pr_name_id()
        # меняем на меню
        bot.edit_message_text('Product added to cart ✅ \nAnything else ?',
                              user_id,
                              call.message.message_id,
                              reply_markup=buttons.main_menu(products))



@bot.callback_query_handler(lambda call: call.data in ['order', 'cart', 'clear_cart'])
def main_menu_handle(call):
    user_id = call.message.chat.id
    message_id = call.message.message_id

    # Если нажал на кнопку: Оформить заказ
    if call.data == 'order':
        # Получим корзину пользователя
        user_cart = database.get_exact_user_cart(user_id)

        if not user_cart:
            # Если корзина пуста
            bot.send_message(user_id, 'Your cart is empty, <b>add items to cart</b> before checking out ❗', parse_mode='HTML')
            return

        # Удалим сообщение с верхними кнопками
        bot.delete_message(user_id, message_id)

        # формируем сообщение со всеми данными
        full_text = '<b>Your order</b> 🔽\n\n'
        user_info = database.get_user_number_name(user_id)
        full_text += f'💬 Name: {user_info[0]}\n📞 Phone number: {user_info[1]}\n\n'
        total_amount = 0

        for i in user_cart:
            full_text += f'{i[0]} x {i[1]} = {i[2]}\n'
            total_amount += i[2]

        # Итог и Адрес
        full_text += f'\n✅ Total: {total_amount}'

        bot.send_message(user_id, full_text, reply_markup=buttons.get_accept_kb(), parse_mode='HTML')
        # Переход на этап подтверждение
        bot.register_next_step_handler(call.message, get_accept,  full_text)

    # Если нажал на кнопку "Корзина"
    elif call.data == 'cart':
        # получим корзину пользователя
        user_cart = database.get_exact_user_cart(user_id)

        # формируем сообщение со всеми данными
        full_text = 'Your cart 🗑:\n\n'
        total_amount = 0

        for i in user_cart:
            full_text += f'{i[0]} x {i[1]} = {i[2]}\n'
            total_amount += i[2]

        # Итог
        full_text += f'\n✅ Total: {total_amount}'

        # отправляем ответ пользователю
        bot.edit_message_text(full_text,
                              user_id,
                              message_id,
                              reply_markup=buttons.get_cart())

    # Если нажал на очистить корзину
    elif call.data == 'clear_cart':
        # вызов функции очистки корзины
        database.delete_product_from_cart(user_id)

        # отправим ответ
        bot.edit_message_text('Your cart has been emptied ✅',
                              user_id,
                              message_id,
                              reply_markup=buttons.main_menu(database.get_pr_name_id()))

# функция сохранения статуса заказа
def get_accept(message, full_text):
    user_id = message.from_user.id
    message_id = message.message_id  # Используем другую переменную для message_id
    user_answer = message.text

    # получим все продукты из базы для кнопок
    products = database.get_pr_name_id()

    # Если пользователь нажал "подтвердить"
    if user_answer == 'Confirm':
        admin_id = -4634068119
        # очистить корзину пользователя
        database.delete_product_from_cart(user_id)
        user_info = database.get_user_number_name(user_id)

        # отправим админу сообщение о новом заказе
        try:
            bot.send_message(admin_id, full_text.replace("Your", "<b>🆕 New</b>"), parse_mode='HTML')
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Error sending message to admin: {e}")

        # отправим ответ
        try:
            bot.send_message(user_id, f'The order has been placed ✅\n\nWe will contact you at the number: 📞 {user_info[1]} ', reply_markup=types.ReplyKeyboardRemove())
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Error sending message to user: {e}")

    elif user_answer == 'Cancel':
        # отправим ответ
        try:
            bot.send_message(user_id, 'Заказ отменен  ✅', reply_markup=types.ReplyKeyboardRemove())
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Error sending message to user: {e}")

    # Обратно в меню
    try:
        bot.send_message(user_id, 'Menu 🔽', reply_markup=buttons.main_menu(products))
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Error sending message from menu: {e}")


@bot.callback_query_handler(lambda call: int(call.data) in database.get_pr_id())
def get_user_product(call):
    # Сохраним ID пользователя
    user_id = call.message.chat.id
    product_id = int(call.data)  # Преобразуем data в int для поиска в БД

    # Получаем данные о продукте
    product_details = database.get_product_details(product_id)

    if product_details:
        # Сохраняем продукт во временный словарь для дальнейших действий
        users[user_id] = {'pr_name': product_id, 'pr_count': 1}
        print(users)

        # Формируем сообщение
        message = (
            f"🏷️ Product name:\n\n{product_details['name']}\n\n"
            f"📝 Product description:\n\n{product_details['description']}\n\n"
        )

        # Отправляем сообщение и фотографию товара, если она есть
        if product_details['photo']:
            bot.send_photo(user_id, product_details['photo'], caption=message)
        else:
            bot.send_message(user_id, message)

        # Поменять кнопки на выбор количества
        bot.send_message(user_id, 'Select quantity 🔢:', reply_markup=buttons.choose_product_count())
    else:
        bot.send_message(user_id, "Sorry, product not found")
        
        
        
bot.infinity_polling()
