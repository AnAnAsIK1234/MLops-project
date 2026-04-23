from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

pages_router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory="templates")


@pages_router.get("/")
def index_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "page_title": "Главная"})


@pages_router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "page_title": "Вход"})


@pages_router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "page_title": "Регистрация"})


@pages_router.get("/dashboard")
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "page_title": "Личный кабинет"})


@pages_router.get("/balance-page")
def balance_page(request: Request):
    return templates.TemplateResponse("balance.html", {"request": request, "page_title": "Баланс"})


@pages_router.get("/predict-page")
def predict_page(request: Request):
    return templates.TemplateResponse("predict.html", {"request": request, "page_title": "ML-запрос"})


@pages_router.get("/history-page")
def history_page(request: Request):
    return templates.TemplateResponse("history.html", {"request": request, "page_title": "История"})


@pages_router.get("/logout")
def logout_page():
    response = RedirectResponse(url="/login", status_code=302)
    return response