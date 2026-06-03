from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from master_bot.api import api

router = Router()

class NewTenant(StatesGroup):
    name = State(); bot_token = State(); owner_tg_id = State(); plan = State(); days = State()

class RenewTenant(StatesGroup):
    days = State()

def tenant_list_kb(tenants):
    kb = InlineKeyboardBuilder()
    for t in tenants[:15]:
        icon = "🟢" if t["status"] == "active" else "🔴"
        kb.button(text=f"{icon} {t['name']}", callback_data=f"t_{t['id']}")
    kb.button(text="➕ ثبت مشتری جدید", callback_data="tenant_new")
    kb.button(text="🔙 منو", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()

@router.callback_query(F.data == "tenants")
async def tenants_menu(cb: CallbackQuery):
    tenants = await api.get("/api/v1/tenants/")
    await cb.message.edit_text(f"🏢 <b>مشتریان</b> ({len(tenants)} عدد)", reply_markup=tenant_list_kb(tenants))

@router.callback_query(F.data == "tenant_new")
async def new_tenant_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(NewTenant.name)
    await cb.message.answer("📝 نام کسب‌وکار:")

@router.message(NewTenant.name)
async def nt_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text.strip())
    await state.set_state(NewTenant.bot_token)
    await msg.answer("🤖 توکن بات تلگرام مشتری:")

@router.message(NewTenant.bot_token)
async def nt_token(msg: Message, state: FSMContext):
    await state.update_data(bot_token=msg.text.strip())
    await state.set_state(NewTenant.owner_tg_id)
    await msg.answer("👤 آیدی عددی تلگرام مالک:")

@router.message(NewTenant.owner_tg_id)
async def nt_owner(msg: Message, state: FSMContext):
    if not msg.text.strip().lstrip("-").isdigit():
        return await msg.answer("❌ فقط عدد:")
    await state.update_data(owner_tg_id=int(msg.text.strip()))
    kb = InlineKeyboardBuilder()
    kb.button(text="ماهانه", callback_data="np_monthly")
    kb.button(text="سالانه", callback_data="np_yearly")
    kb.button(text="آزمایشی", callback_data="np_trial")
    kb.adjust(3)
    await state.set_state(NewTenant.plan)
    await msg.answer("📋 طرح اشتراک:", reply_markup=kb.as_markup())

@router.callback_query(NewTenant.plan, F.data.startswith("np_"))
async def nt_plan(cb: CallbackQuery, state: FSMContext):
    await state.update_data(plan=cb.data.split("_", 1)[1])
    await state.set_state(NewTenant.days)
    await cb.message.answer("📅 مدت اشتراک (روز):")

@router.message(NewTenant.days)
async def nt_days(msg: Message, state: FSMContext):
    if not msg.text.strip().isdigit():
        return await msg.answer("❌ فقط عدد:")
    data = await state.get_data()
    try:
        result = await api.post("/api/v1/tenants/", json={"name": data["name"], "bot_token": data["bot_token"], "owner_tg_id": data["owner_tg_id"], "subscription_plan": data["plan"], "subscription_days": int(msg.text.strip()), "amount": 0})
        await msg.answer(f"✅ <b>مشتری ثبت شد</b>\n🆔 ID: <code>{result['id']}</code>\n🔑 API Key: <code>{result['api_key']}</code>\n📅 انقضا: {result['expires_at']}")
    except Exception as e:
        await msg.answer(f"❌ خطا: {e}")
    await state.clear()

@router.callback_query(F.data.startswith("t_"))
async def tenant_detail(cb: CallbackQuery):
    tid = int(cb.data.split("_")[1])
    try:
        t = await api.get(f"/api/v1/tenants/{tid}")
        s = await api.get(f"/api/v1/tenants/{tid}/stats")
        icon = "🟢" if t["status"] == "active" else "🔴"
        text = (f"{icon} <b>{t['name']}</b>\n📊 وضعیت: {t['status']}\n📋 طرح: {t['plan']}\n📅 انقضا: {t['expires_at']}\n👥 کاربران: {s['customers']:,}\n📅 نوبت‌ها: {s['bookings']:,}\n💰 درآمد: {s['revenue']:,} تومان")
        kb = InlineKeyboardBuilder()
        if t["status"] != "suspended": kb.button(text="⏸ تعلیق", callback_data=f"suspend_{tid}")
        else: kb.button(text="▶️ فعال‌سازی", callback_data=f"activate_{tid}")
        kb.button(text="🔄 تمدید", callback_data=f"renew_{tid}")
        kb.button(text="🔙 مشتریان", callback_data="tenants")
        kb.adjust(2, 1)
        await cb.message.edit_text(text, reply_markup=kb.as_markup())
    except Exception as e:
        await cb.answer(f"❌ {e}", show_alert=True)

@router.callback_query(F.data.startswith("suspend_"))
async def suspend_tenant(cb: CallbackQuery):
    tid = int(cb.data.split("_")[1])
    await api.post(f"/api/v1/tenants/{tid}/suspend")
    await cb.answer("✅ تعلیق شد")
    tenants = await api.get("/api/v1/tenants/")
    await cb.message.edit_text(f"🏢 <b>مشتریان</b> ({len(tenants)} عدد)", reply_markup=tenant_list_kb(tenants))

@router.callback_query(F.data.startswith("activate_"))
async def activate_tenant(cb: CallbackQuery):
    tid = int(cb.data.split("_")[1])
    await api.post(f"/api/v1/tenants/{tid}/activate")
    await cb.answer("✅ فعال شد")
    tenants = await api.get("/api/v1/tenants/")
    await cb.message.edit_text(f"🏢 <b>مشتریان</b> ({len(tenants)} عدد)", reply_markup=tenant_list_kb(tenants))

@router.callback_query(F.data.startswith("renew_"))
async def renew_start(cb: CallbackQuery, state: FSMContext):
    tid = int(cb.data.split("_")[1])
    await state.update_data(renew_tid=tid)
    await state.set_state(RenewTenant.days)
    await cb.message.answer("📅 تعداد روز تمدید:")

@router.message(RenewTenant.days)
async def renew_days(msg: Message, state: FSMContext):
    if not msg.text.strip().isdigit():
        return await msg.answer("❌ فقط عدد:")
    data = await state.get_data()
    try:
        result = await api.post(f"/api/v1/tenants/{data['renew_tid']}/renew", json={"days": int(msg.text.strip()), "plan": "monthly", "amount": 0, "admin_tg_id": msg.from_user.id})
        await msg.answer(f"✅ تمدید شد تا: {result['expires_at']}")
    except Exception as e:
        await msg.answer(f"❌ {e}")
    await state.clear()
