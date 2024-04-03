import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
MY_CHAT_ID = int(os.getenv("MY_CHAT_ID"))

storage = MemoryStorage()

bot = Bot(TOKEN)
dp = Dispatcher(storage=storage)


class FSMForm(StatesGroup):
    send_fio = State()
    send_phone_number = State()
    send_comment = State()
    read_info = State()


@dp.message(CommandStart())
async def process_cmd_start(message: Message, state: FSMContext):
    await message.answer(f"{message.from_user.username}, Добро пожаловать в компанию DamnIT")
    await message.answer("Напишите свое ФИО")
    await state.update_data(username=message.from_user.username)
    await state.set_state(FSMForm.send_fio)


@dp.message(StateFilter(FSMForm.send_fio), F.text.regexp(r"^(([А-Яа-яёЁ]|[a-zA-Z])+(-| )?){3,}$"))
async def get_fio(message: Message, state: FSMContext):
    await state.update_data(fio=message.text)
    await message.answer("Укажите ваш номер телефона в формате +7 (xxx) xxx xx xx")
    await state.set_state(FSMForm.send_phone_number)


@dp.message(StateFilter(FSMForm.send_fio))
async def get_incorrect_fio(message: Message):
    await message.answer("То, что вы отправили, не похоже на ФИО\nПожалуйста, введите ваше ФИО")


@dp.message(StateFilter(FSMForm.send_phone_number), F.text.regexp(r"^\+7 \([0-9]{3}\) [0-9]{3} [0-9]{2} [0-9]{2}$"))
async def get_phone_number(message: Message, state: FSMContext):
    await state.update_data(phone_number=message.text)
    await message.answer("Напишите любой комментарий")
    await state.set_state(FSMForm.send_comment)


@dp.message(StateFilter(FSMForm.send_phone_number))
async def get_incorrect_phone_number(message: Message):
    await message.answer("Кажется, вы ввели номер в неверном формате\nПожалуйста, введите ваш номер телефона")


@dp.message(StateFilter(FSMForm.send_comment))
async def get_any_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    yes_button = InlineKeyboardButton(text="ДА!", callback_data="yes_button_pressed")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[yes_button]])
    await message.answer_document(FSInputFile("test.pdf"),
                                  caption="Последний шаг! Ознакомься с вводными положениями")
    await message.answer("Ознакомился?", reply_markup=keyboard)
    await state.set_state(FSMForm.read_info)


@dp.callback_query(StateFilter(FSMForm.read_info), F.data == "yes_button_pressed")
async def process_button_press(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    user_data = await state.get_data()
    await state.clear()
    await callback.message.answer_photo(FSInputFile("photo_5213382929571503438_y.jpg"),
                                        caption="Спасибо за успешную регистрацию")
    await bot.send_message(MY_CHAT_ID,
                           f"Пришла новая заявка от @{user_data['username']}!\n"
                           f"ФИО: {user_data['fio']}\n"
                           f"Номер телефона: {user_data['phone_number']}\n"
                           f"Комментарий: {user_data['comment']}")


@dp.message(StateFilter(FSMForm.read_info))
async def process_button_not_press(message: Message):
    await message.answer("Если вы прочитали вводные положения, пожалуйста, нажмите на кнопку \"ДА!\"")


@dp.message(StateFilter(default_state))
async def send_echo(message: Message):
    await message.answer("Извините, но я вас не понимаю(")

if __name__ == "__main__":
    dp.run_polling(bot)
