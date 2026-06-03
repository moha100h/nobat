from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from master_bot.config import settings
from master_bot.api import api

router = Router()

def is_admin(uid): return uid == settings.MASTER_ADMIN_ID

def main_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🏢 مشتریان", callback_data="tenants")
    kb.button(text="📊 گزارش‌ها", callback_data="reports")
    kb.button(text="📢 اعلان سراسری", callback_data="announce")
    kb.button(text="🎫 تیکت‌ها", callback_data="tickets")
    kb.button(text="🎁 کد تخفیف", callback_data="discounts")
    kb.adjust(2, 2, 1)
    return kb.as_markup()

@router.message(CommandStart())
async def cmd_start(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ دسترسی ندارید.")
    await api.post("/api/v1/auth/master/init", params={"tg_id": message.from_user.id, "full_name": message.from_user.full_name or "Admin"})
    await message.answer("👑 <b>پنل مدیریت نوبت</b>", reply_markup=main_kb())

@router.callback_query(F.data == "main_menu")
async def back_main(cb: CallbackQuery):
    await cb.message.edit_text("👑 <b>پنل مدیریت نوبت</b>", reply_markup=main_kb())
