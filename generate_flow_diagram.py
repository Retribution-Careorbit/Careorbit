from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1920, 1080
img = Image.new("RGB", (W, H), "#0A0C10")
draw = ImageDraw.Draw(img)

try:
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    font_heading = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    font_mono = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
    font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
except:
    font_title = font_heading = font_body = font_small = font_mono = font_label = ImageFont.load_default()

CYAN = "#00D4FF"
VIOLET = "#8B5CF6"
EMERALD = "#10B981"
ROSE = "#F43F5E"
AMBER = "#F59E0B"
GRAY = "#6B7280"
DARK_SURFACE = "#12141A"
DARK_CARD = "#1A1D27"
BORDER = "#2A2D3A"
WHITE = "#E8EAED"
DIM_WHITE = "#9CA3AF"

def rounded_rect(x, y, w, h, color, fill=None, radius=12):
    if fill:
        draw.rounded_rectangle([x, y, x+w, y+h], radius=radius, fill=fill, outline=color, width=2)
    else:
        draw.rounded_rectangle([x, y, x+w, y+h], radius=radius, outline=color, width=2)

def draw_arrow(x1, y1, x2, y2, color=GRAY, dashed=False):
    draw.line([(x1, y1), (x2, y2)], fill=color, width=2)
    dx = x2 - x1
    dy = y2 - y1
    length = (dx*dx + dy*dy) ** 0.5
    if length == 0:
        return
    ux, uy = dx/length, dy/length
    px, py = -uy, ux
    arrow_len = 10
    ax1 = x2 - arrow_len * ux + arrow_len * 0.4 * px
    ay1 = y2 - arrow_len * uy + arrow_len * 0.4 * py
    ax2 = x2 - arrow_len * ux - arrow_len * 0.4 * px
    ay2 = y2 - arrow_len * uy - arrow_len * 0.4 * py
    draw.polygon([(x2, y2), (int(ax1), int(ay1)), (int(ax2), int(ay2))], fill=color)

def draw_node(x, y, w, h, title, subtitle, accent, icon_text=None):
    rounded_rect(x, y, w, h, accent, fill=DARK_CARD)
    draw.rectangle([x, y, x+w, y+4], fill=accent)
    if icon_text:
        draw.text((x+12, y+14), icon_text, fill=accent, font=font_heading)
        draw.text((x+38, y+14), title, fill=WHITE, font=font_heading)
    else:
        draw.text((x+12, y+14), title, fill=WHITE, font=font_heading)
    if subtitle:
        lines = subtitle.split("\n")
        for i, line in enumerate(lines):
            draw.text((x+12, y+38 + i*18), line, fill=DIM_WHITE, font=font_small)

draw.text((60, 30), "CareOrbit  Login — User Flow & Request Architecture", fill=WHITE, font=font_title)
draw.text((60, 72), "How a patient goes from opening the app to reaching their health dashboard", fill=DIM_WHITE, font=font_body)

draw.rectangle([60, 100, W-60, 102], fill=BORDER)

# ===== ROW 1: USER FLOW (y=130) =====
draw.text((60, 118), "USER JOURNEY", fill=CYAN, font=font_label)

# Step 1: Open App
draw_node(60, 145, 200, 85, "Open App", "Patient visits\ncareorbit.dev", CYAN, None)

# Arrow
draw_arrow(260, 187, 290, 187, CYAN)

# Step 2: Login Page Loads
draw_node(290, 145, 220, 85, "Login Page", "Particles render\nForm appears", CYAN, None)

draw_arrow(510, 187, 540, 187, CYAN)

# Step 3: Enter Email
draw_node(540, 145, 200, 85, "Enter Email", "Live regex check\nGreen checkmark", EMERALD, None)

draw_arrow(740, 187, 770, 187, CYAN)

# Step 4: Enter Password
draw_node(770, 145, 200, 85, "Enter Password", "Strength meter\nShow/hide toggle", AMBER, None)

draw_arrow(970, 187, 1000, 187, CYAN)

# Step 5: Sign In
draw_node(1000, 145, 190, 85, "Click Sign In", "Gradient button\nLoader spinner", VIOLET, None)

draw_arrow(1190, 187, 1220, 187, CYAN)

# Step 6: OR Social
draw_node(1220, 145, 200, 85, "OR Social Login", "Google / Apple\nOne-tap auth", GRAY, None)

draw_arrow(1420, 187, 1450, 187, CYAN)

# Step 7: Dashboard
draw_node(1450, 145, 220, 85, "Dashboard", "Onboarding or\nHealth overview", EMERALD, None)

# Alt: Error
draw_arrow(1095, 230, 1095, 265, ROSE)
draw_node(1000, 265, 190, 65, "Error Toast", "Show message\nRetry available", ROSE, None)

# ===== ROW 2: REQUEST FLOW (y=380) =====
draw.rectangle([60, 365, W-60, 367], fill=BORDER)
draw.text((60, 378), "REQUEST FLOW (HTTP)", fill=VIOLET, font=font_label)

# Frontend
rounded_rect(60, 410, 350, 260, CYAN, fill=DARK_SURFACE)
draw.rectangle([60, 410, 410, 414], fill=CYAN)
draw.text((75, 422), "FRONTEND  (React + Vite :5000)", fill=CYAN, font=font_heading)
items_fe = [
    "login.tsx — Login page component",
    "useState() — email, password, loading",
    "isEmailValid — /regex/.test(email)",
    "getPasswordStrength() — 0-3 score",
    "handleSubmit() — fetch('/api/auth/login')",
    "Content-Type: application/json",
    "Body: { email, password }",
    "setAuth() — store tokens in Zustand",
    "navigate('/') or navigate('/onboarding')",
]
for i, item in enumerate(items_fe):
    c = WHITE if i < 4 else AMBER if i < 7 else EMERALD
    draw.text((75, 450 + i*22), item, fill=c, font=font_mono)

# Arrow FE -> API
draw_arrow(410, 540, 480, 540, AMBER)
draw.text((420, 518), "POST", fill=AMBER, font=font_label)
draw.text((410, 555), "/api/auth/login", fill=DIM_WHITE, font=font_mono)

# API Gateway / Express
rounded_rect(480, 410, 340, 260, VIOLET, fill=DARK_SURFACE)
draw.rectangle([480, 410, 820, 414], fill=VIOLET)
draw.text((495, 422), "API  (Express Proxy :5000)", fill=VIOLET, font=font_heading)
items_api = [
    "Vite dev middleware",
    "Proxy /api/* -> FastAPI :8000",
    "Preserves headers & cookies",
    "Returns JSON response",
    "",
    "Response 200:",
    "  { access_token, refresh_token,",
    "    user: { id, email, name,",
    "    onboarding_complete } }",
]
for i, item in enumerate(items_api):
    c = WHITE if i < 4 else EMERALD
    draw.text((495, 450 + i*22), item, fill=c, font=font_mono)

# Arrow API -> Backend
draw_arrow(820, 540, 890, 540, AMBER)
draw.text((832, 518), "PROXY", fill=AMBER, font=font_label)

# Backend FastAPI
rounded_rect(890, 410, 350, 260, EMERALD, fill=DARK_SURFACE)
draw.rectangle([890, 410, 1240, 414], fill=EMERALD)
draw.text((905, 422), "BACKEND  (FastAPI :8000)", fill=EMERALD, font=font_heading)
items_be = [
    "POST /api/auth/login",
    "Validate email + password",
    "Query user from PostgreSQL",
    "bcrypt.verify(password, hash)",
    "Generate JWT access_token",
    "Generate refresh_token",
    "Return user profile data",
    "Set onboarding_complete flag",
    "401 if invalid credentials",
]
for i, item in enumerate(items_be):
    c = WHITE if i < 1 else EMERALD if i < 8 else ROSE
    draw.text((905, 450 + i*22), item, fill=c, font=font_mono)

# Arrow Backend -> DB
draw_arrow(1240, 540, 1310, 540, AMBER)
draw.text((1250, 518), "SQL", fill=AMBER, font=font_label)

# Database
rounded_rect(1310, 440, 240, 170, AMBER, fill=DARK_SURFACE)
draw.rectangle([1310, 440, 1550, 444], fill=AMBER)
draw.text((1325, 452), "DATABASE (PostgreSQL)", fill=AMBER, font=font_heading)
items_db = [
    "users table:",
    "  id, email, name",
    "  password_hash (bcrypt)",
    "  onboarding_complete",
    "  created_at",
]
for i, item in enumerate(items_db):
    draw.text((1325, 478 + i*20), item, fill=WHITE, font=font_mono)

# ===== ROW 3: AUTH STATE (y=710) =====
draw.rectangle([60, 700, W-60, 702], fill=BORDER)
draw.text((60, 712), "CLIENT-SIDE AUTH STATE", fill=EMERALD, font=font_label)

rounded_rect(60, 740, 500, 130, EMERALD, fill=DARK_SURFACE)
draw.rectangle([60, 740, 560, 744], fill=EMERALD)
draw.text((75, 752), "ZUSTAND AUTH STORE", fill=EMERALD, font=font_heading)
items_auth = [
    "access_token  — JWT for API requests",
    "refresh_token — for token renewal",
    "user: { id, email, name, onboardingComplete }",
    "setAuth() / clearAuth() / isAuthenticated()",
]
for i, item in enumerate(items_auth):
    draw.text((75, 778 + i*20), item, fill=WHITE, font=font_mono)

draw_arrow(560, 805, 630, 805, CYAN)

rounded_rect(630, 740, 380, 130, CYAN, fill=DARK_SURFACE)
draw.rectangle([630, 740, 1010, 744], fill=CYAN)
draw.text((645, 752), "ROUTE GUARD", fill=CYAN, font=font_heading)
items_guard = [
    "isAuthenticated? -> Dashboard",
    "!isAuthenticated? -> /login",
    "!onboardingComplete? -> /onboarding",
    "Token in Authorization header",
]
for i, item in enumerate(items_guard):
    draw.text((645, 778 + i*20), item, fill=WHITE, font=font_mono)

draw_arrow(1010, 805, 1080, 805, CYAN)

rounded_rect(1080, 740, 380, 130, VIOLET, fill=DARK_SURFACE)
draw.rectangle([1080, 740, 1460, 744], fill=VIOLET)
draw.text((1095, 752), "PROTECTED API CALLS", fill=VIOLET, font=font_heading)
items_protected = [
    "GET /api/orbit/score",
    "GET /api/patients/overview",
    "GET /api/patients/vitals",
    "All require: Bearer <token>",
]
for i, item in enumerate(items_protected):
    draw.text((1095, 778 + i*20), item, fill=WHITE, font=font_mono)

# ===== ROW 4: DESIGN TOKENS (y=910) =====
draw.rectangle([60, 900, W-60, 902], fill=BORDER)
draw.text((60, 912), "UX DESIGN DECISIONS (V2 — ADOPTED)", fill=VIOLET, font=font_label)

decisions = [
    ("Real-time Validation", "Email regex + password strength give instant feedback before submit", EMERALD),
    ("Gradient CTA", "Cyan-to-violet gradient signals primary action, scales on hover", VIOLET),
    ("Social Login", "Google + Apple reduce signup friction for new-to-tech patients", CYAN),
    ("Particle Field", "Ambient motion creates premium feel without distracting from the form", DIM_WHITE),
    ("Remember Me", "Custom checkbox persists session — critical for returning patients", AMBER),
]
for i, (title, desc, color) in enumerate(decisions):
    x = 60 + i * 370
    draw.ellipse([x, 938, x+10, 948], fill=color)
    draw.text((x+16, 935), title, fill=WHITE, font=font_label)
    draw.text((x+16, 955), desc[:45], fill=DIM_WHITE, font=font_small)
    if len(desc) > 45:
        draw.text((x+16, 970), desc[45:], fill=DIM_WHITE, font=font_small)

# Footer
draw.rectangle([60, 1010, W-60, 1012], fill=BORDER)
draw.text((60, 1025), "CareOrbit  |  Healthcare AI Platform  |  Login Architecture v2.0", fill=GRAY, font=font_small)
draw.text((W-350, 1025), "Built for Indian patients", fill=GRAY, font=font_small)

out_path = "/home/runner/workspace/careorbit_login_architecture.png"
img.save(out_path, "PNG", quality=95)
print(f"Saved to {out_path} — {os.path.getsize(out_path)} bytes")
