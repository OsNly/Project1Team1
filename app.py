from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime
import pandas as pd
import re
import plotly.express as px

import openai
from fastapi.responses import JSONResponse

client = openai.OpenAI(api_key="secret-key")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="CHANGE_THIS_TO_A_RANDOM_SECRET")

merchant_keywords = {
    "Amazon":        "Shopping",
    "Hungerstation": "Food",
    "Uber":          "Transport",
    "Alothaim":      "Shopping",
    "Jahez":         "Food",
    "Webook":        "Entertainment",
    "Keeta":         "Food",
    "Jarir":         "Shopping",
    "Bolt":          "Transport",
    "Aldrees":       "Fuel",
}

categories = ["Food", "Transport", "Entertainment", "Bills", "Shopping", "Other"]

translations = {
    "en": {
        "title": "Smart Expense Analyzer",
        "set_budgets": "Set Monthly Budgets",
        "save_budgets": "Save Budgets",
        "budget_alerts": "Budget Alerts",
        "within_budgets": "✅ You are within your budgets for all categories!",
        "upload_sms": "Upload your bank SMS CSV",
        "add_manual": "Add Expense Manually",
        "description": "Description",
        "category": "Category",
        "amount": "Amount ($)",
        "date": "Date",
        "add": "Add",
        "all_expenses": "All Expenses",
        "spend_cat": "Spending by Category",
        "spend_time": "Spending Over Time",
        "advice": "Advice",
        "no_data": "Add some expenses or upload SMS to get started.",
        "watch_high": "⚠️ Watch out for high spending in:",
        "stay_control": "✅ Great job keeping your spending in control!"
    },
    "ar": {
        "title": "مُحلّل المصاريف الذكي",
        "set_budgets": "🔔 ضع ميزانيات شهرية",
        "save_budgets": "حفظ الميزانيات",
        "budget_alerts": "🚨 تنبيهات الميزانية",
        "within_budgets": "✅ أنت ضمن الميزانيات المحددة لجميع الفئات!",
        "upload_sms": "📂 حمّل رسائل SMS البنكي (CSV)",
        "add_manual": "📝 أضف مصروفًا يدويًا",
        "description": "الوصف",
        "category": "الفئة",
        "amount": "المبلغ ($)",
        "date": "التاريخ",
        "add": "أضف",
        "all_expenses": "📋 جميع المصروفات",
        "spend_cat": "📊 الإنفاق حسب الفئة",
        "spend_time": "📈 الإنفاق بمرور الوقت",
        "advice": "💡 نصيحة",
        "no_data": "🛒 أضف مصروفات أو حمّل رسائل لبدء التحليل.",
        "watch_high": "⚠️ احذر من الإنفاق العالي في:",
        "stay_control": "✅ أحسنت، إنفاقك مضبوط!"
    }
}
for lang in ("en","ar"):
    for cat in categories:
        translations[lang][f"cat_{cat}"] = cat if lang=="en" else {
            "Food":"طعام","Transport":"تنقل","Entertainment":"ترفيه",
            "Bills":"فواتير","Shopping":"تسوق","Other":"أخرى"
        }[cat]

def _(lang, key):
    return translations.get(lang, translations["en"]).get(key, key)

def extract_expense_from_sms(sms: str, date=None):
    # 1) matching kown merchants
    for keyword, cat in merchant_keywords.items():
        if keyword.lower() in sms.lower():
            m = re.search(r'SAR[.\s]?\s?(\d+\.?\d*)', sms, re.IGNORECASE)
            if m:
                return {
                    "description": f"Auto: {keyword}",
                    "category":    cat,
                    "amount":      float(m.group(1)),
                    "date":        date or datetime.today().strftime('%Y-%m-%d')
                }
    m = re.search(r'SAR[.\s]?\s?(\d+\.?\d*)', sms, re.IGNORECASE)
    if not m:
        return None
    amount = float(m.group(1))
    merchant = None
    patterns = [
        r'at\s+([A-Za-z\s]+)',
        r'to\s+([A-Za-z\s]+)',
        r'for\s+([A-Za-z\s]+)',
        r'order of\s+([A-Za-z\s]+)',
        r'purchase of\s+([A-Za-z\s]+)',
        r'charge of\s+([A-Za-z\s]+)',
        r'on\s+([A-Za-z\s]+)',
        r'from\s+([A-Za-z\s]+)',
    ]
    for patt in patterns:
        m2 = re.search(patt, sms, re.IGNORECASE)
        if m2:
            merchant = m2.group(1).strip()
            break
    if not merchant:
        tail = sms[m.end():]
        m3 = re.search(r'\b([A-Za-z]{3,})\b', tail)
        if m3:
            merchant = m3.group(1)
    if not merchant:
        merchant = "Unknown Merchant"
    return {
        "description": f"Auto: {merchant}",
        "category":    "Uncategorized",
        "amount":      amount,
        "date":        date or datetime.today().strftime('%Y-%m-%d')
    }

def make_charts(expenses):
    if not expenses:
        return "", ""
    df = pd.DataFrame(expenses)
    df["date"] = pd.to_datetime(df["date"])
    pie = px.pie(
        df.groupby("category", as_index=False)["amount"].sum(),
        names="category", values="amount"
    ).to_html(full_html=False, include_plotlyjs="cdn")
    df["month"] = df["date"].dt.to_period("M").astype(str)
    bar = px.bar(
        df.groupby(["month","category"], as_index=False)["amount"].sum(),
        x="month", y="amount", color="category", barmode="group"
    ).to_html(full_html=False, include_plotlyjs=False)
    return pie, bar

def get_spending_summary(expenses):
    summary = {}
    for e in expenses:
        summary[e["category"]] = summary.get(e["category"], 0) + e["amount"]
    return summary

def check_budget_alerts(summary, budgets):
    alerts = []
    for cat, spent in summary.items():
        b = budgets.get(cat, 0)
        if b and spent > b:
            alerts.append(f"⚠️ You've exceeded your budget for {cat}: Spent {spent} (Budget {b})")
    return alerts

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, lang: str = "en"):
    sess = request.session
    sess.setdefault("expenses", [])
    sess.setdefault("budgets", {})

    expenses = sess["expenses"]
    budgets  = sess["budgets"]
    pie, bar = make_charts(expenses)
    summary  = get_spending_summary(expenses)
    alerts   = check_budget_alerts(summary, budgets)

    return templates.TemplateResponse("index.html", {
        "request":    request,
        "lang":       lang,
        "t":          lambda k: _(lang, k),
        "categories": categories,
        "expenses":   expenses,
        "budgets":    budgets,
        "alerts":     alerts,
        "pie":        pie,
        "bar":        bar,
        "now":        datetime.now
    })

@app.post("/set_budgets")
async def set_budgets(request: Request):
    form = await request.form()
    lang = form.get("lang", "en")
    sess = request.session
    sess.setdefault("budgets", {})
    for cat in categories:
        try:
            sess["budgets"][cat] = float(form.get(f"budget_{cat}", 0))
        except:
            sess["budgets"][cat] = 0.0
    return RedirectResponse(f"/?lang={lang}", status_code=303)

@app.post("/upload")
async def upload_sms(request: Request, file: UploadFile = File(...)):
    form = await request.form()
    lang = form.get("lang", "en")
    df = pd.read_csv(file.file, header=None)
    for sms in df[0].astype(str):
        e = extract_expense_from_sms(sms)
        if e:
            request.session["expenses"].append(e)
    return RedirectResponse(f"/?lang={lang}", status_code=303)

@app.post("/add")
async def add_manual(
    request: Request,
    description: str = Form(...),
    category:    str = Form(...),
    amount:      float = Form(...),
    date:        str = Form(...),
    lang:        str = Form("en")
):
    request.session["expenses"].append({
        "description": description,
        "category":    category,
        "amount":      amount,
        "date":        date
    })
    return RedirectResponse(f"/?lang={lang}", status_code=303)

@app.get("/get_ai_advice")
async def get_ai_advice():
    prompt = (
        "تصرّف كمستشار مالي. قدّم نصيحة مالية قصيرة وعملية وإيجابية "
        "لشخص يقوم بتتبع مصروفاته في فئات مثل الطعام، النقل، الترفيه، "
        "الفواتير، التسوق، وغيرها. اجعل النصيحة تحفيزية وتركّز على الادخار الذكي."

    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # use "gpt-3.5-turbo" if gpt-4 is not available
            messages=[
                {"role": "system", "content": "You are a financial advisor."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.7
        )
        advice = response.choices[0].message.content.strip()
        return JSONResponse(content={"advice": advice})
    except Exception as e:
        print("OpenAI Error:", e)
        return JSONResponse(content={"advice": "⚠️ Unable to generate advice at the moment."})
