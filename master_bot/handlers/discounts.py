from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from master_bot.api import api

router = Router()

class DiscountForm(StatesGroup):
    tenant_id = State(); code = State(); percent = State()

@router.callback_query(F.data == "discounts")
async def discounts_menu(cb: CallbackQuery):
    tenants = await api.get("/api/v1/tenants/")
    kb = InlineKeyboardBuilder()
    for t in tenants[:15]:
        kb.button(text=t["name"], callback_data=f"disc_{t['id']}")
    kb.button(text="🔙 منو", callback_data="main_menu")
    kb.adjust(1)
    await cb.message.edit_text("🎁 <b>کد تخفیف</b> — مشتری:", reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("disc_"))
async def discount_start(cb: CallbackQuery, state: FSMContext):
    await state.update_data(tenant_id=int(cb.data.split("_")[1]))
    await state.set_state(DiscountForm.code)
    await cb.message.answer("📝 کد تخفیف (مثلاً SUMMER20):")

@router.message(DiscountForm.code)
async def discount_code(msg: Message, state: FSMContext):
    await state.update_data(code=msg.text.strip().upper())
    await state.set_state(DiscountForm.percent)
    await msg.answer("📊 درصد تخفیف (۱ تا ۱۰۰):")

@router.message(DiscountForm.percent)
async def discount_percent(msg: Message, state: FSMContext):
    if not msg.text.strip().isdigit() or not (1 <= int(msg.text.strip()) <= 100):
        return await msg.answer("❌ عدد بین ۱ تا ۱۰۰:")
    data = await state.get_data()
    try:
        await api.post("/api/v1/discounts/", tid=data["tenant_id"], json={"code": data["code"], "discount_percent": int(msg.text.strip())})
        await msg.answer(f"✅ کد <code>{data['code']}</code> با {msg.text.strip()}٪ ایجاد شد")
    except Exception as e:
        await msg.answer(f"❌ {e}")
    await state.clear()
