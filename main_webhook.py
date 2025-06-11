@dp.message_handler(lambda m: user_state.get(m.from_user.id, {}).get("step") == "topics_select")
async def ask_topics_inline(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["topics"] = []
    user_state[user_id]["step"] = "topics_inline"
    await send_topic_selection(user_id)

async def send_topic_selection(user_id):
    all_topics = [
        ("A. Государственные дотации и экономия на налогах", "A"),
        ("B. Различные Страховки (авто, адвокат, медстраховка и т.д.)", "B"),
        ("C. Накопительные программы для детей", "C"),
        ("D. Пенсионные Планы и дотации", "D"),
        ("E. Потреб.Кредиты/ Финансирование Недвижимости", "E"),
        ("F. Инвестиции и вложения", "F"),
        ("G. Управление личными расходами", "G"),
        ("I. Стратегия финансового благополучия", "I"),
        ("J. Дополнительного дохода", "J")
    ]
    markup = InlineKeyboardMarkup(row_width=1)
    selected = user_state[user_id].get("topics", [])
    for label, code in all_topics:
        display = f"✅ {label}" if code in selected else label
        markup.add(InlineKeyboardButton(display, callback_data=f"topic_{code}"))
    markup.add(InlineKeyboardButton("✅ Готово", callback_data="topics_done"))
    await bot.send_message(user_id, "Выберите интересующие вас темы (можно несколько):", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith("topic_"))
async def toggle_topic(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    code = callback_query.data.replace("topic_", "")
    selected = user_state[user_id].get("topics", [])
    if code in selected:
        selected.remove(code)
    else:
        selected.append(code)
    user_state[user_id]["topics"] = selected
    await bot.answer_callback_query(callback_query.id)
    await send_topic_selection(user_id)

@dp.callback_query_handler(lambda c: c.data == "topics_done")
async def topics_done(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_state[user_id]["step"] = "messenger"
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("Telegram"), KeyboardButton("WhatsApp"), KeyboardButton("Viber"))
    await bot.send_message(user_id, "Выберите удобный мессенджер для связи:", reply_markup=markup)
