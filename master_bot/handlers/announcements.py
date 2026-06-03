from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from master_bot.api import api

router = Router()

class AnnounceForm(StatesGroup):
    text = State()

@router.callback_query(F.data == "announce")
async def announce_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AnnounceForm.text)
    await cb.message.answer("📢 متن اعلان سراسری:")

@router.message(AnnounceForm.text)
async def send_announce(msg: Message, state: FSMContext, bot: Bot):
    tenants = await api.get("/api/v1/tenants/", params={"status": "active"})
    ok = fail = 0
    for t in tenants:
        try:
            await bot.send_message(t["owner_tg_id"], f"📢 <b>اعلان:</b>\n\n{msg.text}")
            ok += 1
        except Exception:
            fail += 1
    await msg.answer(f"✅ ارسال شد: {ok}\n❌ ناموفق: {fail}")
    await state.clear()
