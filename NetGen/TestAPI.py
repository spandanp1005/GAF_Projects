from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

app = FastAPI()

# For rendering HTML templates
templates = Jinja2Templates(directory="templates")

# Serve static files if you have any (CSS, JS) — optional
app.mount("/static", StaticFiles(directory="static"), name="static")

# Show the form
@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("formV2.html", {"request": request})

# Handle form submission
@app.post("/submit")
async def submit_form(
    name: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    dob: str = Form(...)
):
    print(f"Name: {name}")
    print(f"Phone: {phone}")
    print(f"Address: {address}")
    print(f"Date of Birth: {dob}")
    
    return {"message": "Form submitted successfully!"}
