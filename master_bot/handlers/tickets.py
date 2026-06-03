from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from master_bot.api import api

router = Router()

@router.callback_query(F.data == "tickets")
async def tickets_menu(cb: CallbackQuery):
    tenants = await api.get("/api/v1/tenants/")
    kb = InlineKeyboardBuilder()
    for t in tenants[:15]:
        kb.button(text=t["name"], callback_data=f"tkt_{t['id']}")
    kb.button(text="🔙 منو", callback_data="main_menu")
    kb.adjust(1)
    await cb.message.edit_text("🎫 <b>تیکت‌ها</b> — مشتری:", reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("tkt_"))
async def tenant_tickets(cb: CallbackQuery):
    tid = int(cb.data.split("_")[1])
    try:
        tickets = await api.get("/api/v1/tickets/", tid=tid)
        if not tickets:
            return await cb.answer("تیکتی وجود ندارد", show_alert=True)
        lines = ["🎫 <b>تیکت‌ها:</b>"]
        for tk in tickets[:20]:
            lines.append(f"#{tk['id']} — {tk['subject']} [{tk['status']}]")
        kb = InlineKeyboardBuilder()
        kb.button(text="🔙 برگشت", callback_data="tickets")
        await cb.message.edit_text("\n".join(lines), reply_markup=kb.as_markup())
    except Exception as e:
        await cb.answer(f"❌ {e}", show_alert=True)
