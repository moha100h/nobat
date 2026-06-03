from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from master_bot.api import api

router = Router()

@router.callback_query(F.data == "reports")
async def reports_menu(cb: CallbackQuery):
    tenants = await api.get("/api/v1/tenants/")
    total_b = total_c = total_r = 0
    for t in tenants:
        try:
            s = await api.get(f"/api/v1/tenants/{t['id']}/stats")
            total_b += s["bookings"]; total_c += s["customers"]; total_r += s["revenue"]
        except Exception:
            pass
    text = (f"📊 <b>گزارش کلی</b>\n\n🏢 مشتریان: {len(tenants)}\n👥 کل کاربران: {total_c:,}\n📅 کل نوبت‌ها: {total_b:,}\n💰 کل درآمد: {total_r:,} تومان")
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 منو", callback_data="main_menu")
    await cb.message.edit_text(text, reply_markup=kb.as_markup())
