import datetime
from random import choice

from httpx import request
from pydantic_core.core_schema import none_schema
from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, MessageHandler, filters
from credentials import ChatGPT_TOKEN, BOT_TOKEN
from gpt import ChatGptService
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons, Dialog)


#Начальное меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User {update.effective_user.full_name} called /start | {datetime.datetime.now()}")
    dialog.mode = 'main'
    text = load_message('main')
    await send_image(update, context, 'main')
    await send_text(update, context, text)
    await show_main_menu(update, context, {
        'start': 'Главное меню',
        'random': 'Узнать случайный интересный факт 🧠',
        'gpt': 'Задать вопрос чату GPT 🤖',
        'talk': 'Поговорить с известной личностью 👤',
        'quiz': 'Поучаствовать в квизе ❓',
        'translate' : 'Перевести предложение 🌍'
    })

# 1 Задание
#Рандомный факт
async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User {update.effective_user.full_name} called /random_fact | {datetime.datetime.now()}")
    prompt = load_prompt('random')
    message = load_message('random')
    await send_image(update,context,'random')
    await send_text(update, context, message)
    answer = await chat_gpt.send_question(prompt,'')
    await send_text_buttons(update, context, answer, {
        'random_more': 'Хочу еще рандомный факт',
        'random_end': 'Выйти'
    })

#Обработка кнопок в рандомном факте
async def random_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    answer = update.callback_query.data
    if answer == 'random_more':
        await random_fact(update, context)
    else:
        await start(update, context)

# 2 Задание
#GPT
async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User {update.effective_user.full_name} called /gpt | {datetime.datetime.now()}")
    dialog.mode = 'gpt'
    prompt = load_prompt('gpt')
    message = load_message('gpt')
    chat_gpt.set_prompt(prompt)
    await send_image(update, context, 'gpt')
    await send_text(update, context, message)

async def gpt_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    message = await send_text(update,context, 'Думаю над вашим вопросом...')
    answer = await chat_gpt.add_message(text)
    #print(f"GPT Response: {answer}")
    await message.edit_text(answer)
    await send_text_buttons(update, context, 'Что делаем дальше?', {
        'gpt_more': 'Хочу задать еще вопрос!',
        'gpt_end': 'Выйти'
    })

#Обработка кнопок в разговоре с gpt
async def gpt_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    answer = update.callback_query.data
    if answer == 'gpt_more':
        await gpt(update, context)
    else:
        await start(update, context)

# 3 Задание
#Разговор с личностью - главное меню
async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User {update.effective_user.full_name} called /talk | {datetime.datetime.now()}")
    dialog.mode = 'talk'
    message = load_message('talk')
    await send_image(update,context,'talk')
    await send_text_buttons(update, context, message, {
        'talk_cobain': 'Курт Кобейн',
        'talk_queen': 'Елизавета II',
        'talk_tolkien': 'Джон Толкиен',
        'talk_nietzsche': 'Фридрих Ницше',
        'talk_hawking': 'Стивен Хокинг'
    })

#Обработка кнопок с меню
async def talk_button(update:Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    choice = update.callback_query.data
    prompt = load_prompt(choice)
    chat_gpt.set_prompt(prompt)
    answer = await chat_gpt.send_question(prompt, '')
    await send_image(update,context,choice)
    await send_text(update,context,answer)

#Разговор с личностью
async def talk_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    message = await send_text(update, context, 'Думаю над вопросом...')
    answer = await chat_gpt.add_message(text)
    await message.edit_text(answer)


# 4 Задание
#КВИЗ
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User {update.effective_user.full_name} called /quiz | {datetime.datetime.now()}")
    dialog.mode = 'quiz'
    message = load_message('quiz')
    context.user_data['current_quiz'] = None
    context.user_data['quiz_theme'] = None
    context.user_data['count'] = 0
    await send_image(update,context,'quiz')
    await send_text_buttons(update, context, message, {
        'quiz_prog': 'Программирование на Python',
        'quiz_math': 'Математические теории',
        'quiz_biology': 'Биология'
    })

async def quiz_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    prompt = load_prompt('quiz')
    choice = update.callback_query.data
    if choice == 'quiz_more':
        choice = context.user_data['current_quiz']
    elif choice == 'quiz_exit':
        await send_text(update, context, f'Правильных ответов: {context.user_data['count']}')
        context.user_data['current_quiz'] = None
        context.user_data['quiz_theme'] = None
        context.user_data['count'] = 0
        await start(update, context)
        return
    else:
        context.user_data['current_quiz'] = choice
    answer = await chat_gpt.send_question(prompt, choice)
    await send_text(update, context, answer)
    context.user_data['quiz_theme'] = 'next'


async def quiz_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data['current_quiz'] or not context.user_data['quiz_theme']:
        return
    context.user_data['quiz_theme'] = None
    text = update.message.text
    answer = await chat_gpt.add_message(text)
    if answer == 'Правильно!':
        context.user_data['count'] += 1
    await send_text_buttons(update, context, answer, {
        'quiz_more': 'Следующий вопрос',
        'quiz_another': 'Другая тема',
        'quiz_exit': 'Завершить'
    })


# 5 Задание
#Переводчик
async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dialog.mode = 'translate'
    await send_image(update, context, 'translate')
    message = "Выберите язык, на который нужно перевести текст:"
    languages = {
        'translate_en': 'Английский',
        'translate_de': 'Немецкий',
        'translate_fr': 'Французский',
        'translate_es': 'Испанский',
        'translate_ru': 'Русский',
        'translate_ch': 'Китайский'
    }
    await send_text_buttons(update, context, message,languages)

async def translate_language_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    cb = update.callback_query.data
    if cb == 'translate_another':
        await translate(update, context)
        return
    elif cb == 'translate_end':
        await start(update,context)
        return

    prompt = load_prompt(cb)
    chat_gpt.set_prompt(prompt)
    #print(prompt)
    language_map = {
        'translate_en': 'Английский',
        'translate_de': 'Немецкий',
        'translate_fr': 'Французский',
        'translate_es': 'Испанский',
        'translate_ru': 'Русский',
        'translate_ch': 'Китайский'
    }
    selected_language = language_map.get(cb, 'Выберете язык из списка')  # Получаем название выбранного языка
    await send_text(update, context, f'Вы выбрали язык: {selected_language}. Теперь введите текст для перевода:')

async def translate_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    message = await send_text(update, context, 'Перевожу...')
    answer = await chat_gpt.add_message(text)
    #await message.edit_text(answer)
    await send_text_buttons(update, context, answer, {
        'translate_another' : 'Выбрать другой язык',
        'translate_end': 'Закончить'
    })


async def translate_continue_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await send_text(update, context, 'Введите текст для перевода:')
    dialog.mode = 'translate'

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'{update.message.text} - {update.effective_user.full_name} | {datetime.datetime.now()}')
    if dialog.mode == 'gpt':
        await gpt_dialog(update, context)
    elif dialog.mode == 'talk':
        await talk_dialog(update, context)
    elif dialog.mode == 'quiz':
        await quiz_dialog(update, context)
    elif dialog.mode == 'translate':
        await translate_dialog(update,context)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


chat_gpt = ChatGptService(ChatGPT_TOKEN)
app = ApplicationBuilder().token(BOT_TOKEN).build()

dialog = Dialog()
dialog.mode = None

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

# Зарегистрировать обработчик команды можно так:
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random_fact))
app.add_handler(CommandHandler('gpt', gpt))
app.add_handler(CommandHandler('talk', talk))
app.add_handler(CommandHandler('quiz', quiz))
app.add_handler(CommandHandler('translate', translate))

# Зарегистрировать обработчик коллбэка можно так:
app.add_handler(CallbackQueryHandler(random_button, pattern='^random_.*'))
app.add_handler(CallbackQueryHandler(gpt_button, pattern='^gpt_.*'))
app.add_handler(CallbackQueryHandler(talk_button, pattern='^talk_.*'))
app.add_handler(CallbackQueryHandler(quiz_button, pattern='^quiz_.*'))
app.add_handler(CallbackQueryHandler(translate_language_button, pattern='^translate_.*'))


app.add_handler(CallbackQueryHandler(default_callback_handler))
app.run_polling()
