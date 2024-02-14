import os
import telebot
import time
from telebot.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from messages import start_message, help_message
from quiz_data import question_list, option_list
from dotenv import load_dotenv


load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(token=TELEGRAM_BOT_TOKEN)
current_questions = {}
user_results = {}
all_results = []


@bot.message_handler(commands=["start"])
def start_command_handler(message: Message):
    bot.send_message(
        chat_id=message.chat.id,
        text=start_message
    )


@bot.message_handler(commands=["help"])
def help_command_handler(message: Message):
    bot.send_message(
        chat_id=message.chat.id,
        text=help_message
    )


@bot.message_handler(commands=["start_quiz"])
def start_quiz_command_handler(message: Message):
    user_id = message.chat.id
    current_questions[user_id] = {
        "question_number": 0,
        "correct_answers": 0,
        "start_time": time.time()
    }
    ask_question(user_id, current_questions[user_id]["question_number"])


def ask_question(chat_id, question_number):
    question_data = question_list[question_number]
    q_text = f"{question_number + 1}. {question_data['question']}"
    markup = InlineKeyboardMarkup(row_width=2)
    btns = []
    for i, option in enumerate(question_data["options"]):
        btn = InlineKeyboardButton(text=option, callback_data=option_list[i])
        btns.append(btn)
    markup.add(*btns)
    bot.send_message(
        chat_id=chat_id,
        text=q_text,
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data in option_list)
def callback_handler(call: CallbackQuery):
    user_id = call.message.chat.id
    current_question_data = current_questions.get(user_id)
    if current_question_data:
        question_number = current_question_data["question_number"]
        old_question_data = question_list[question_number]
        if old_question_data['correct_option'] == call.data:
            current_questions[user_id]["correct_answers"] += 1
        current_questions[user_id]["question_number"] += 1
        if current_questions[user_id]["question_number"] >= len(question_list):
            end_time = time.time()
            elapsed_time_seconds = round(end_time - current_questions[user_id]["start_time"])
            elapsed_time_minutes = elapsed_time_seconds // 60
            remaining_seconds = elapsed_time_seconds % 60
            all_results.append({
                "user_id": user_id,
                "correct_answers": current_questions[user_id]["correct_answers"],
                "time_minutes": elapsed_time_minutes,
                "time_seconds": remaining_seconds
            })
            del current_questions[user_id]
            result_info = next((result for result in all_results if result["user_id"] == user_id), None)
            if result_info:
                correct_answers = result_info["correct_answers"]
                elapsed_time_minutes = result_info["time_minutes"]
                remaining_seconds = result_info["time_seconds"]
                bot.send_message(
                    chat_id=user_id,
                    text=f"Викторина завершена!\n"
                         f"Правильных ответов: {correct_answers}\n"
                         f"Время: {elapsed_time_minutes} минут {remaining_seconds} секунд."
                )
        else:
            ask_question(user_id, current_questions[user_id]["question_number"])


@bot.message_handler(commands=["record_table"])
def record_table_command_handler(message: Message):
    sorted_results = sorted(all_results, key=lambda x: (x["correct_answers"],
                                                        -x["time_minutes"],
                                                        -x["time_seconds"]), reverse=True)
    table_text = "Таблица лучших результатов:\n"
    for idx, result in enumerate(sorted_results, start=1):
        table_text += (f"{idx}. Пользователь {result['user_id']}"
                       f" - {result['correct_answers']}"
                       f" правильных ответов за {result['time_minutes']}"
                       f" минут {result['time_seconds']} секунд\n")
    bot.send_message(
        chat_id=message.chat.id,
        text=table_text
    )


bot.polling()
