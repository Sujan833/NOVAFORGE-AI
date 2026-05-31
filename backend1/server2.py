# ============================================================
# NovaForge AI Website Generator Backend
# FULL-STACK | DB-SAFE | FEATURE-ATOMIC | PREVIEW-STABLE
# ============================================================

from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import os
import pathlib
import sqlite3
import traceback
import requests
import re
import json
import hashlib
import random
from difflib import SequenceMatcher

# Dynamic generation pipeline - intent-driven UI generation
from generation_pipeline import (
    analyze_project_prompt,
    generate_ui_plan,
    generate_theme,
    export_analysis,
    export_ui_plan,
    apply_layout_variation,
    generate_modular_html,
    place_images_in_html,
)

# git helper for pushing projects
from git_push import push_to_github, GitPushError

# ----------------- LOAD ENV -----------------
load_dotenv()

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("âŒ GEMINI_API_KEY not found")

genai.configure(api_key=GEMINI_API_KEY)

# ----------------- PATHS -----------------
BASE_DIR = pathlib.Path(__file__).resolve().parent
GENERATED_ROOT = BASE_DIR / "generated_projects"
GENERATED_ROOT.mkdir(exist_ok=True)
NOVAFORGE_BUILD = "2026-03-23-uniqueness-guard-v2"


# ----------------- HELPERS -----------------
def extract_between(text, start, end):
    try:
        s = text.index(start) + len(start)
        e = text.index(end)
        return text[s:e].strip()
    except Exception:
        return None


def inject_preview_guard(js_code: str) -> str:
    guard = """
// ===== NovaForge Preview Guard =====
const IS_PREVIEW = window.location.protocol === "about:";
if (IS_PREVIEW) {
  console.warn("Preview mode active: backend calls disabled");
}
"""
    if guard.strip() in js_code:
        return js_code
    return guard + "\n" + js_code


NO_BACKEND_TYPES = {"static", "portfolio", "blog", "landing"}
BACKEND_FEATURES = {"Database", "Authentication", "Admin Dashboard", "Contact Form", "File Upload"}
FRONTEND_ONLY_TYPES = {"static", "portfolio", "blog", "landing"}
FULLSTACK_TYPES = {"fullstack", "ecommerce", "saas"}


DEFAULT_IMAGE_URLS = [
    "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1550547660-d9450f859349?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=1200&q=80",
]


def _infer_site_archetype(name: str, desc: str, project_type: str) -> str:
    text = f"{name or ''} {desc or ''}".lower()
    if project_type in {"ecommerce"}:
        return "ecommerce"
    ecommerce_markers = (
        "ecommerce", "e-commerce", "amazon", "flipkart", "shop", "store",
        "product", "catalog", "wishlist", "checkout", "delivery"
    )
    food_markers = ("food", "restaurant", "zomato", "swiggy", "menu", "order food")
    saas_markers = ("saas", "dashboard", "kpi", "subscription", "crm", "analytics")
    jobs_markers = ("job", "jobs", "career", "recruitment", "hiring", "employer", "candidate")
    library_markers = ("library", "books", "bookstore", "reading", "catalogue", "catalog", "author")
    healthcare_markers = ("hospital", "clinic", "doctor", "patient", "appointment", "medical", "healthcare")
    travel_markers = ("travel", "trip", "tour", "hotel", "booking", "flight", "destination")
    if any(m in text for m in ecommerce_markers):
        return "ecommerce"
    if any(m in text for m in food_markers):
        return "food"
    if any(m in text for m in jobs_markers):
        return "jobs"
    if any(m in text for m in library_markers):
        return "library"
    if any(m in text for m in healthcare_markers):
        return "healthcare"
    if any(m in text for m in travel_markers):
        return "travel"
    if any(m in text for m in saas_markers):
        return "saas"
    return "generic"


def _default_hero_subtitle(archetype: str) -> str:
    mapping = {
        "ecommerce": "Discover products, compare options, and complete your journey with a polished shopping experience.",
        "food": "Explore curated options, manage your selections, and place requests through a smooth interactive flow.",
        "jobs": "Discover opportunities, evaluate roles, and manage your applications with confidence.",
        "library": "Browse collections, save favorites, and manage your reading journey in one place.",
        "healthcare": "Access services, review care options, and manage appointments with clarity and trust.",
        "travel": "Explore destinations, compare packages, and plan trips using a seamless booking-style experience.",
        "saas": "Track workflows, monitor outcomes, and keep teams aligned through an intuitive product experience.",
    }
    return mapping.get(archetype, "A production-ready digital experience with modern UI, responsive sections, and interactive flows.")


def _description_feature_inference(description: str):
    text = (description or "").lower()
    inferred = set()
    if any(k in text for k in ("login", "signup", "sign up", "register", "authentication", "account")):
        inferred.add("Authentication")
    if any(k in text for k in ("admin", "dashboard", "manage users", "manage doctors", "manage products", "panel")):
        inferred.add("Admin Dashboard")
    if any(k in text for k in ("contact form", "contact us", "phone number", "email us", "reach us")):
        inferred.add("Contact Form")
    if any(k in text for k in ("upload", "profile photo", "resume", "document", "image upload", "file upload")):
        inferred.add("File Upload")
    return inferred


def _extract_description_requirements(description: str, archetype: str):
    text = (description or "").lower()
    req = []
    generic = [
        ("faq", "Frequently asked questions"),
        ("testimonial", "Testimonials and trust signals"),
        ("contact", "Contact and support section"),
    ]
    healthcare = [
        ("doctor", "Doctors directory with specialization filters"),
        ("specialization", "Department and specialization explorer"),
        ("appointment", "Appointment booking flow with date and slot"),
        ("facility", "Hospital facilities and infrastructure showcase"),
        ("insurance", "Insurance and cashless partners section"),
        ("award", "Awards, accreditations, and recognitions"),
        ("phone", "Contact phone and emergency helpline"),
    ]
    jobs = [
        ("company", "Employer/company profile blocks"),
        ("apply", "Application workflow and status tracking"),
        ("resume", "Resume/profile upload process"),
        ("salary", "Compensation and role benefits section"),
        ("skills", "Skills and eligibility breakdown"),
    ]
    library = [
        ("author", "Author and publisher highlights"),
        ("category", "Book categories and genre navigation"),
        ("borrow", "Borrow/return workflow"),
        ("membership", "Membership plans and benefits"),
        ("digital", "Digital library and e-book access"),
    ]
    travel = [
        ("itinerary", "Itinerary planner section"),
        ("package", "Travel package comparison grid"),
        ("booking", "Booking flow and confirmation states"),
        ("visa", "Visa and travel advisory section"),
        ("hotel", "Hotel and stay options"),
    ]
    pool = generic[:]
    if archetype == "healthcare":
        pool += healthcare
    elif archetype == "jobs":
        pool += jobs
    elif archetype == "library":
        pool += library
    elif archetype == "travel":
        pool += travel

    for key, label in pool:
        if key in text:
            req.append(label)

    if not req:
        defaults = {
            "healthcare": ["Doctors directory with specialization filters", "Appointment booking flow with date and slot", "Hospital facilities and infrastructure showcase"],
            "jobs": ["Employer/company profile blocks", "Application workflow and status tracking", "Skills and eligibility breakdown"],
            "library": ["Book categories and genre navigation", "Borrow/return workflow", "Membership plans and benefits"],
            "travel": ["Travel package comparison grid", "Booking flow and confirmation states", "Itinerary planner section"],
            "generic": ["Feature breakdown section", "Customer testimonials", "FAQ and contact support"],
        }
        req = defaults.get(archetype, defaults["generic"])

    # keep unique order and limit
    seen = set()
    out = []
    for item in req:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out[:6]


def _variation_index(name: str, desc: str, archetype: str, modulo: int = 3) -> int:
    # Include entropy so repeated prompts can still produce distinct layout variants.
    key = f"{name or ''}|{desc or ''}|{archetype or ''}|{os.urandom(3).hex()}".encode("utf-8", errors="ignore")
    digest = hashlib.sha256(key).hexdigest()
    return int(digest[:8], 16) % max(1, modulo)


def _style_signature(name: str, desc: str, archetype: str) -> str:
    directions = [
        "Use a clean clinical visual system with cool palette, card elevation, and information hierarchy.",
        "Use a bold editorial layout with stronger typographic contrast and asymmetric section rhythms.",
        "Use a modern product aesthetic with gradient accents, compact spacing, and dashboard-like clarity.",
    ]
    motion = [
        "Use subtle reveal animations and interactive tabs.",
        "Use progressive disclosure panels and sticky section navigation.",
        "Use animated counters, accordion FAQs, and polished hover transitions.",
    ]
    idx = _variation_index(name, desc, archetype, 3)
    return f"- style_signature: {directions[idx]}\n- interaction_signature: {motion[idx]}"


def _ecommerce_fallback_html(name: str, desc: str, project_type: str, features) -> str:
    title = name or "ShopSphere"
    subtitle = _default_hero_subtitle("ecommerce")
    tpl = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>__TITLE__</title>
  <style>
    :root { --ink:#111827; --bg:#f8fafc; --brand:#0f172a; --accent:#f59e0b; --card:#ffffff; --ok:#16a34a; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; background:var(--bg); color:var(--ink); }
    .top { position:sticky; top:0; z-index:20; background:linear-gradient(90deg,#0f172a,#1e293b); color:#fff; padding:12px 16px; display:flex; align-items:center; gap:12px; flex-wrap:wrap; }
    .brand { font-size:1.2rem; font-weight:800; letter-spacing:.3px; margin-right:auto; }
    .top input { min-width:220px; flex:1; max-width:420px; border:0; border-radius:10px; padding:10px 12px; }
    .top button { border:0; border-radius:999px; padding:8px 12px; cursor:pointer; background:rgba(255,255,255,.14); color:#fff; }
    .top .solid { background:var(--accent); color:#111827; font-weight:700; }
    .hero { margin:16px auto; max-width:1200px; padding:24px; border-radius:16px; color:#fff; background:linear-gradient(120deg, rgba(15,23,42,.88), rgba(245,158,11,.88)), url('__HERO__'); background-size:cover; background-position:center; }
    .hero h1 { margin:0 0 8px; font-size:clamp(1.6rem,2.8vw,2.6rem); }
    .hero p { margin:0; line-height:1.6; max-width:860px; }
    main { max-width:1200px; margin:0 auto; padding:0 16px 28px; display:grid; gap:14px; }
    .view { display:none; }
    .view.active { display:block; }
    .card { background:var(--card); border-radius:14px; border:1px solid #e2e8f0; padding:14px; box-shadow:0 8px 18px rgba(15,23,42,.07); }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; }
    .product { border:1px solid #e5e7eb; border-radius:12px; overflow:hidden; background:#fff; }
    .product img { width:100%; height:170px; object-fit:cover; display:block; }
    .meta { padding:10px; display:grid; gap:8px; }
    .meta h3 { margin:0; font-size:1rem; }
    .price { font-weight:800; font-size:1rem; }
    .delivery { color:#334155; font-size:.9rem; }
    .actions { display:flex; gap:8px; flex-wrap:wrap; }
    .actions button { border:0; border-radius:10px; padding:8px 10px; cursor:pointer; }
    .actions .cart-btn { background:#0f172a; color:#fff; }
    .actions .wish-btn { background:#fef3c7; color:#92400e; }
    .qty { display:flex; align-items:center; gap:8px; }
    .qty button { border:0; border-radius:8px; padding:4px 8px; cursor:pointer; background:#e2e8f0; }
    .row { display:flex; justify-content:space-between; align-items:center; gap:10px; }
    .auth-form { display:grid; gap:10px; max-width:360px; }
    .auth-form input { border:1px solid #d1d5db; border-radius:10px; padding:10px; }
    .auth-form button { border:0; border-radius:10px; padding:10px; cursor:pointer; background:#0f172a; color:#fff; font-weight:700; }
    .muted { color:#64748b; }
    footer { padding:22px; text-align:center; color:#64748b; }
  </style>
</head>
<body>
  <header class="top">
    <div class="brand">__TITLE__</div>
    <input id="searchInput" placeholder="Search products, categories, brands..." />
    <button class="solid" data-view="products">Products</button>
    <button data-view="wishlist">Wishlist (<span id="wishCount">0</span>)</button>
    <button data-view="cart">Cart (<span id="cartCount">0</span>)</button>
    <button data-view="orders">Orders</button>
    <button data-view="login" id="navLogin">Login</button>
    <button data-view="signup" id="navSignup">Signup</button>
    <button id="logoutBtn" style="display:none;">Logout</button>
  </header>

  <section class="hero">
    <h1>Shop smarter with fast delivery</h1>
    <p>__SUBTITLE__</p>
  </section>

  <main>
    <section id="products" class="view active card">
      <div class="row"><h2>Featured Products</h2><span class="muted" id="resultCount"></span></div>
      <div id="productGrid" class="grid"></div>
    </section>

    <section id="wishlist" class="view card">
      <h2>Wishlist</h2>
      <div id="wishlistList" class="muted">No saved products yet.</div>
    </section>

    <section id="cart" class="view card">
      <h2>Your Cart</h2>
      <div id="cartItems" class="muted">Your cart is empty.</div>
      <div class="row" style="margin-top:10px;">
        <strong>Total: $<span id="cartTotal">0.00</span></strong>
        <button id="checkoutBtn" class="solid">Place Order</button>
      </div>
    </section>

    <section id="orders" class="view card">
      <h2>Your Orders</h2>
      <div id="orderList" class="muted">No orders yet.</div>
    </section>

    <section id="login" class="view card">
      <h2>Login</h2>
      <form id="login-form" data-auth="login" class="auth-form">
        <input type="email" name="email" placeholder="Email" required />
        <input type="password" name="password" placeholder="Password" required />
        <button type="submit">Login</button>
      </form>
      <p id="login-message" class="muted"></p>
    </section>

    <section id="signup" class="view card">
      <h2>Create Account</h2>
      <form id="signup-form" data-auth="signup" class="auth-form">
        <input type="email" name="email" placeholder="Email" required />
        <input type="password" name="password" placeholder="Password" required />
        <button type="submit">Signup</button>
      </form>
      <p id="signup-message" class="muted"></p>
    </section>
  </main>

  <footer>Built by NovaForge | __TYPE__</footer>

  <script>
    const API_BASE = "http://localhost:5001/api";
    let authToken = localStorage.getItem("nova_auth_token") || "";
    let currentUser = null;
    let search = "";
    let cart = [];
    let wishlist = [];
    let orders = [];

    const products = [
      { id:"p1", name:"Wireless Earbuds Pro", category:"Electronics", price:49.99, delivery:"Tomorrow", img:"https://images.unsplash.com/photo-1583394838336-acd977736f90?auto=format&fit=crop&w=800&q=80" },
      { id:"p2", name:"Smart Watch Active", category:"Wearables", price:79.00, delivery:"2-Day Delivery", img:"https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=800&q=80" },
      { id:"p3", name:"Laptop Backpack", category:"Accessories", price:34.50, delivery:"Tomorrow", img:"https://images.unsplash.com/photo-1491637639811-60e2756cc1c7?auto=format&fit=crop&w=800&q=80" },
      { id:"p4", name:"Bluetooth Speaker", category:"Audio", price:39.90, delivery:"Same Day", img:"https://images.unsplash.com/photo-1545454675-3531b543be5d?auto=format&fit=crop&w=800&q=80" },
      { id:"p5", name:"Mechanical Keyboard", category:"Computers", price:89.99, delivery:"2-Day Delivery", img:"https://images.unsplash.com/photo-1517336714739-489689fd1ca8?auto=format&fit=crop&w=800&q=80" },
      { id:"p6", name:"Portable SSD 1TB", category:"Storage", price:99.00, delivery:"Tomorrow", img:"https://images.unsplash.com/photo-1593642632823-8f785ba67e45?auto=format&fit=crop&w=800&q=80" }
    ];

    function view(id) {
      document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
      const el = document.getElementById(id);
      if (el) el.classList.add("active");
      if (id === "orders") renderOrders();
      if (id === "cart") renderCart();
      if (id === "wishlist") renderWishlist();
    }

    function filteredProducts() {
      const q = search.trim().toLowerCase();
      if (!q) return products;
      return products.filter(p => (p.name + " " + p.category).toLowerCase().includes(q));
    }

    function renderProducts() {
      const list = filteredProducts();
      document.getElementById("resultCount").textContent = list.length + " products";
      const grid = document.getElementById("productGrid");
      grid.innerHTML = list.map(p => `
        <article class="product">
          <img src="${p.img}" alt="${p.name}" />
          <div class="meta">
            <h3>${p.name}</h3>
            <div class="muted">${p.category}</div>
            <div class="price">$${p.price.toFixed(2)}</div>
            <div class="delivery">Delivery: ${p.delivery}</div>
            <div class="actions">
              <button class="cart-btn" onclick="addToCart('${p.id}')">Add to Cart</button>
              <button class="wish-btn" onclick="toggleWish('${p.id}')">${wishlist.includes(p.id) ? "Wishlisted" : "Wishlist"}</button>
            </div>
          </div>
        </article>
      `).join("");
    }

    function addToCart(pid) {
      const p = products.find(x => x.id === pid);
      if (!p) return;
      const hit = cart.find(i => i.id === pid);
      if (hit) hit.qty += 1; else cart.push({ id:p.id, name:p.name, price:p.price, qty:1 });
      syncCounts();
    }

    function toggleWish(pid) {
      if (wishlist.includes(pid)) wishlist = wishlist.filter(x => x !== pid);
      else wishlist.push(pid);
      syncCounts();
      renderProducts();
    }

    function syncCounts() {
      document.getElementById("cartCount").textContent = String(cart.reduce((a,b)=>a+b.qty,0));
      document.getElementById("wishCount").textContent = String(wishlist.length);
    }

    function renderWishlist() {
      const host = document.getElementById("wishlistList");
      const items = products.filter(p => wishlist.includes(p.id));
      if (!items.length) {
        host.textContent = "No saved products yet.";
        return;
      }
      host.innerHTML = items.map(p => `<div class="row"><span>${p.name}</span><strong>$${p.price.toFixed(2)}</strong></div>`).join("");
    }

    function renderCart() {
      const host = document.getElementById("cartItems");
      if (!cart.length) {
        host.textContent = "Your cart is empty.";
        document.getElementById("cartTotal").textContent = "0.00";
        return;
      }
      host.innerHTML = cart.map(item => `
        <div class="row">
          <span>${item.name}</span>
          <div class="qty">
            <button onclick="qty('${item.id}',-1)">-</button>
            <span>${item.qty}</span>
            <button onclick="qty('${item.id}',1)">+</button>
          </div>
          <strong>$${(item.price * item.qty).toFixed(2)}</strong>
        </div>
      `).join("");
      const total = cart.reduce((a,b)=>a+(b.price*b.qty),0);
      document.getElementById("cartTotal").textContent = total.toFixed(2);
    }

    function qty(pid, d) {
      const hit = cart.find(i => i.id === pid);
      if (!hit) return;
      hit.qty += d;
      if (hit.qty <= 0) cart = cart.filter(i => i.id !== pid);
      syncCounts();
      renderCart();
    }

    function authHeaders() {
      const h = { "Content-Type": "application/json" };
      if (authToken) h.Authorization = "Bearer " + authToken;
      return h;
    }

    async function submitAuth(form, endpoint, messageId) {
      const email = form.querySelector('input[name="email"]').value.trim();
      const password = form.querySelector('input[name="password"]').value.trim();
      const msg = document.getElementById(messageId);
      msg.textContent = "";
      try {
        const res = await fetch("http://localhost:5001" + endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password })
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || !data.success) {
          msg.textContent = data.error || "Authentication failed.";
          return;
        }
        authToken = data.token || "";
        if (authToken) localStorage.setItem("nova_auth_token", authToken);
        currentUser = data.user || { email };
        msg.textContent = endpoint.includes("signup") ? "Signup successful." : "Login successful.";
        syncAuthUI();
        await loadOrders();
        view("products");
      } catch (e) {
        msg.textContent = "Backend not reachable on port 5001.";
      }
    }

    async function restoreSession() {
      if (!authToken) return;
      try {
        const res = await fetch(API_BASE + "/auth/me", { headers: authHeaders() });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.success) {
          currentUser = data.user;
          await loadOrders();
          syncAuthUI();
          return;
        }
      } catch {}
      authToken = "";
      currentUser = null;
      localStorage.removeItem("nova_auth_token");
      syncAuthUI();
    }

    function syncAuthUI() {
      const login = document.getElementById("navLogin");
      const signup = document.getElementById("navSignup");
      const logout = document.getElementById("logoutBtn");
      const on = !!currentUser;
      login.style.display = on ? "none" : "inline-block";
      signup.style.display = on ? "none" : "inline-block";
      logout.style.display = on ? "inline-block" : "none";
    }

    async function loadOrders() {
      if (!authToken) {
        orders = [];
        return;
      }
      try {
        const res = await fetch(API_BASE + "/orders/mine", { headers: authHeaders() });
        const data = await res.json().catch(() => ({}));
        orders = (res.ok && data.success && Array.isArray(data.orders)) ? data.orders : [];
      } catch {
        orders = [];
      }
      renderOrders();
    }

    async function checkout() {
      if (!currentUser) {
        alert("Login required before placing order.");
        view("login");
        return;
      }
      if (!cart.length) return;
      const total = cart.reduce((a,b)=>a+(b.price*b.qty),0);
      const items = cart.map(c => ({ id:c.id, name:c.name, price:c.price, qty:c.qty }));
      try {
        const res = await fetch(API_BASE + "/orders", {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({ items, total })
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || !data.success) {
          alert(data.error || "Could not place order.");
          return;
        }
        cart = [];
        syncCounts();
        await loadOrders();
        view("orders");
      } catch {
        alert("Backend not reachable while placing order.");
      }
    }

    function renderOrders() {
      const host = document.getElementById("orderList");
      if (!orders.length) {
        host.textContent = "No orders yet.";
        return;
      }
      host.innerHTML = orders.map(o => `
        <div class="card" style="margin-top:8px;">
          <div class="row"><strong>Order #${o.order_id || o.id}</strong><span>${o.order_date || ""}</span></div>
          <div class="muted">Status: ${o.status || "placed"}</div>
          <div><strong>Total: $${Number(o.total_amount || 0).toFixed(2)}</strong></div>
        </div>
      `).join("");
    }

    document.querySelectorAll("[data-view]").forEach(btn => btn.addEventListener("click", () => view(btn.getAttribute("data-view"))));
    document.getElementById("searchInput").addEventListener("input", e => { search = e.target.value; renderProducts(); });
    document.getElementById("checkoutBtn").addEventListener("click", checkout);
    document.getElementById("signup-form").addEventListener("submit", e => { e.preventDefault(); submitAuth(e.target, "/api/auth/signup", "signup-message"); });
    document.getElementById("login-form").addEventListener("submit", e => { e.preventDefault(); submitAuth(e.target, "/api/auth/login", "login-message"); });
    document.getElementById("logoutBtn").addEventListener("click", () => {
      currentUser = null;
      authToken = "";
      orders = [];
      localStorage.removeItem("nova_auth_token");
      syncAuthUI();
      view("products");
    });

    renderProducts();
    renderCart();
    syncCounts();
    syncAuthUI();
    restoreSession();
  </script>
</body>
</html>
"""
    return (
        tpl.replace("__TITLE__", title)
        .replace("__SUBTITLE__", subtitle)
        .replace("__TYPE__", project_type or "fullstack")
        .replace("__HERO__", "https://images.unsplash.com/photo-1607083206869-4c7672e72a8a?auto=format&fit=crop&w=1400&q=80")
    )


def _normalize_project_type(project_type: str, description: str = "") -> str:
    raw = (project_type or "").strip().lower()
    aliases = {
        "advertisement": "landing",
        "advertising": "landing",
        "marketing": "landing",
        "campaign": "landing",
        "ads": "landing",
        "full-stack web application": "fullstack",
        "full stack web application": "fullstack",
        "full stack": "fullstack",
        "full-stack": "fullstack",
        "static website": "static",
        "landing page": "landing",
        "portfolio website": "portfolio",
    }
    raw = aliases.get(raw, raw)
    if raw in {
        "static", "landing", "portfolio", "apibased",
        "fullstack", "ai", "business", "custom",
        "ecommerce", "saas", "blog"
    }:
        return raw
    desc_low = (description or "").lower()
    if "blog" in desc_low:
        return "blog"
    return raw or "custom"


def _no_backend_template_html(name: str, desc: str, project_type: str) -> str:
    title = name or "Modern Website"
    subtitle = _default_hero_subtitle(_infer_site_archetype(name, desc, project_type))
    is_blog = project_type == "blog"
    hero_title = "Stories, insights, and ideas" if is_blog else "Grow your reach with a high-conversion page"
    hero_cta_1 = "Read Latest" if is_blog else "Get Started"
    hero_cta_2 = "Categories" if is_blog else "View Pricing"
    cards = """
      <article class="card"><h3>Design Systems in 2026</h3><p>Practical patterns to ship faster without losing quality.</p><button>Read</button></article>
      <article class="card"><h3>Performance for Real Users</h3><p>How to tune rendering and interactions for every device.</p><button>Read</button></article>
      <article class="card"><h3>Writing Better Product Copy</h3><p>Use clarity and structure to improve signups and retention.</p><button>Read</button></article>
      <article class="card"><h3>Launch Checklists</h3><p>Ship confidently with practical pre-release QA playbooks.</p><button>Read</button></article>
      <article class="card"><h3>SEO for Product Teams</h3><p>Build pages that rank, convert, and stay fast.</p><button>Read</button></article>
      <article class="card"><h3>Creative Direction</h3><p>Turn vague ideas into consistent visual language.</p><button>Read</button></article>
    """ if is_blog else """
      <article class="card"><h3>Lead Generation</h3><p>Capture qualified leads with clear, persuasive CTAs.</p><button>Explore</button></article>
      <article class="card"><h3>Campaign Landing Pages</h3><p>Launch promotions with focused storytelling and trust signals.</p><button>Explore</button></article>
      <article class="card"><h3>Conversion Analytics</h3><p>Measure click-through and engagement with no backend dependency.</p><button>Explore</button></article>
      <article class="card"><h3>Smart Automation</h3><p>Automate follow-ups and nurture leads automatically.</p><button>Explore</button></article>
      <article class="card"><h3>Audience Segments</h3><p>Deliver targeted messaging for different buyer groups.</p><button>Explore</button></article>
      <article class="card"><h3>Operational Dashboards</h3><p>Give teams clear visibility into performance and outcomes.</p><button>Explore</button></article>
    """
    tpl = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>__TITLE__</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Manrope:wght@400;500;700;800&display=swap');
    :root { --bg:#f5f7ff; --ink:#0f172a; --muted:#4b5563; --brand:#1450ff; --brand2:#13c9b5; --accent:#ff7a18; --card:#ffffff; --line:#dbe2ff; }
    *{ box-sizing:border-box; }
    body{ margin:0; font-family: "Manrope", system-ui, sans-serif; color:var(--ink); background:
      radial-gradient(1200px 500px at -10% -10%, #dbeafe 0%, transparent 50%),
      radial-gradient(900px 380px at 110% 0%, #d1fae5 0%, transparent 52%),
      var(--bg); }
    header{ position:sticky; top:0; z-index:10; display:flex; justify-content:space-between; align-items:center; padding:14px 20px; background:rgba(255,255,255,.8); border-bottom:1px solid var(--line); backdrop-filter:blur(10px); }
    .brand{ font-family:"Space Grotesk", sans-serif; font-weight:800; letter-spacing:.2px; }
    nav{ display:flex; gap:10px; flex-wrap:wrap; }
    nav button{ border:1px solid var(--line); border-radius:999px; padding:8px 14px; cursor:pointer; background:#fff; color:var(--ink); font-weight:600; }
    .hero{ max-width:1200px; margin:26px auto 12px; padding:0 18px; display:grid; grid-template-columns:1.1fr .9fr; gap:16px; }
    .hero-box{ border-radius:20px; padding:30px; color:#fff; background:linear-gradient(120deg, #0833b9, #0e76ff 56%, #0fb3b5); box-shadow:0 24px 45px rgba(12,70,196,.28); }
    .hero h1{ margin:0 0 10px; font-family:"Space Grotesk", sans-serif; font-size:clamp(1.85rem, 3.1vw, 3rem); line-height:1.1; }
    .hero p{ margin:0; line-height:1.65; max-width:850px; opacity:.94; }
    .quick-panel{ background:#fff; border:1px solid var(--line); border-radius:20px; padding:20px; box-shadow:0 14px 30px rgba(14,36,88,.08); }
    .quick-panel h3{ margin:0 0 6px; font-family:"Space Grotesk", sans-serif; }
    .stats{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-top:14px; }
    .stat{ border:1px solid var(--line); border-radius:12px; padding:10px; background:#fafcff; text-align:center; }
    .stat strong{ display:block; font-size:1.1rem; font-family:"Space Grotesk", sans-serif; }
    .cta{ margin-top:16px; display:flex; gap:10px; flex-wrap:wrap; }
    .cta button{ border:0; border-radius:10px; padding:10px 14px; cursor:pointer; font-weight:700; }
    .cta .primary{ background:#fff; color:#0f172a; }
    .cta .secondary{ background:rgba(15,23,42,.22); color:#fff; border:1px solid rgba(255,255,255,.32); }
    .section{ max-width:1200px; margin:0 auto; padding:18px; }
    .section h2{ font-family:"Space Grotesk", sans-serif; margin:4px 0 14px; font-size:clamp(1.2rem,2vw,1.7rem); }
    .trust{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; }
    .chip{ border:1px solid var(--line); background:#fff; border-radius:999px; padding:10px 12px; text-align:center; font-weight:700; color:#1f3b80; }
    main{ max-width:1200px; margin:0 auto; padding:0 18px; display:grid; gap:14px; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); }
    .card{ background:var(--card); border-radius:16px; border:1px solid var(--line); padding:16px; box-shadow:0 10px 20px rgba(15,23,42,.06); transition:transform .2s ease, box-shadow .2s ease; }
    .card:hover{ transform:translateY(-4px); box-shadow:0 14px 26px rgba(15,23,42,.11); }
    .card h3{ margin:0 0 8px; }
    .card p{ margin:0 0 12px; color:var(--muted); }
    .card button{ border:0; border-radius:10px; padding:8px 12px; cursor:pointer; background:var(--brand); color:#fff; }
    .split{ max-width:1200px; margin:18px auto 8px; padding:0 18px; display:grid; grid-template-columns:1fr 1fr; gap:14px; }
    .panel{ background:#fff; border:1px solid var(--line); border-radius:16px; padding:18px; box-shadow:0 10px 20px rgba(15,23,42,.05); }
    .faq-item{ border-bottom:1px solid var(--line); padding:10px 0; }
    .faq-item button{ width:100%; text-align:left; border:0; background:none; cursor:pointer; font-weight:700; color:var(--ink); padding:0; }
    .faq-item p{ max-height:0; overflow:hidden; margin:0; color:var(--muted); transition:max-height .25s ease, margin .25s ease; }
    .faq-item.open p{ max-height:130px; margin-top:8px; }
    footer{ margin-top:18px; text-align:center; color:#475569; padding:24px; }
    @media (max-width: 980px){
      .hero{ grid-template-columns:1fr; }
      .split{ grid-template-columns:1fr; }
    }
    @media (max-width: 640px){
      .stats{ grid-template-columns:1fr 1fr; }
      nav{ justify-content:flex-end; }
    }
  </style>
</head>
<body>
  <header>
    <strong class="brand">__TITLE__</strong>
    <nav>
      <button data-scroll="#home">Home</button>
      <button data-scroll="#services">Services</button>
      <button data-scroll="#faq">FAQ</button>
      <button data-scroll="#contact">Contact</button>
    </nav>
  </header>
  <section class="hero" id="home">
    <div class="hero-box reveal">
      <h1>__HERO_TITLE__</h1>
      <p>__SUBTITLE__</p>
      <div class="cta">
        <button class="primary">__CTA1__</button>
        <button class="secondary">__CTA2__</button>
      </div>
    </div>
    <aside class="quick-panel reveal">
      <h3>Why teams choose this setup</h3>
      <p>Optimized for modern launch velocity with clear sections, conversion-focused messaging, and polished interactions.</p>
      <div class="stats">
        <div class="stat"><strong>92%</strong><span>Engagement Lift</span></div>
        <div class="stat"><strong>4.8/5</strong><span>User Rating</span></div>
        <div class="stat"><strong>2.1x</strong><span>Faster Launch</span></div>
      </div>
    </aside>
  </section>
  <section class="section reveal">
    <h2>Trusted by fast-moving teams</h2>
    <div class="trust">
      <div class="chip">Design-Led</div>
      <div class="chip">Mobile Ready</div>
      <div class="chip">Performance First</div>
      <div class="chip">Conversion Focused</div>
      <div class="chip">SEO Friendly</div>
      <div class="chip">Launch Ready</div>
    </div>
  </section>
  <section class="section reveal" id="services"><h2>Services & Highlights</h2></section>
  <main>
    __CARDS__
  </main>
  <section class="split">
    <article class="panel reveal" id="faq">
      <h2>Frequently Asked Questions</h2>
      <div class="faq-item"><button>How customizable is this website template?</button><p>Fully customizable. You can adjust typography, sections, colors, content blocks, and interactions to fit your niche.</p></div>
      <div class="faq-item"><button>Is it suitable for live deployment?</button><p>Yes. It is structured to be production-friendly with responsive layout, semantic sections, and stable interactions.</p></div>
      <div class="faq-item"><button>Can I extend this into multiple pages?</button><p>Yes. The section-based architecture can be split into dedicated pages like pricing, blog, product, and contact with minimal refactoring.</p></div>
    </article>
    <article class="panel reveal" id="contact">
      <h2>Contact & Next Steps</h2>
      <p style="color:var(--muted);margin-bottom:10px;">Tell us your goals and we will shape a launch plan tailored to your users.</p>
      <div style="display:grid;gap:8px;">
        <input placeholder="Your Name" />
        <input placeholder="Work Email" />
        <textarea rows="4" placeholder="Project details"></textarea>
        <button style="border:0;background:var(--brand);color:#fff;padding:10px;border-radius:10px;cursor:pointer;">Request Demo</button>
      </div>
    </article>
  </section>
  <footer>Built by NovaForge | __TYPE__ | frontend-only | official-ready layout</footer>
  <script>
    document.querySelectorAll('[data-scroll]').forEach(btn => {
      btn.addEventListener('click', () => {
        const target = document.querySelector(btn.getAttribute('data-scroll'));
        if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
    document.querySelectorAll('.faq-item button').forEach(btn => {
      btn.addEventListener('click', () => btn.parentElement.classList.toggle('open'));
    });
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = "1";
          entry.target.style.transform = "translateY(0)";
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.2 });
    document.querySelectorAll('.reveal').forEach(el => {
      el.style.opacity = "0";
      el.style.transform = "translateY(14px)";
      el.style.transition = "opacity .45s ease, transform .45s ease";
      observer.observe(el);
    });
    document.querySelectorAll('button').forEach(btn => {
      btn.addEventListener('click', () => {
        btn.style.transform = 'translateY(-1px)';
        setTimeout(() => { btn.style.transform = ''; }, 140);
      });
    });
  </script>
</body>
</html>
"""
    raw_html = (
        tpl.replace("__TITLE__", title)
        .replace("__SUBTITLE__", subtitle)
        .replace("__TYPE__", project_type)
        .replace("__HERO_TITLE__", hero_title)
        .replace("__CTA1__", hero_cta_1)
        .replace("__CTA2__", hero_cta_2)
        .replace("__CARDS__", cards)
    )
    return _diversify_fallback_layout(raw_html, name, desc, _infer_site_archetype(name, desc, project_type))


def _is_generation_quality_ok(html: str, features, project_type: str = "") -> bool:
    if not html or len(html.strip()) < 1300:
        return False

    low = html.lower()
    if "<style" not in low or "<script" not in low:
        return False
    if "<header" not in low or "<footer" not in low:
        return False
    if "<nav" not in low and low.count("href=") < 4:
        return False
    if low.count("<section") < 5 and low.count("class=\"page\"") < 4:
        return False
    if ":root" not in low:
        return False
    if "addeventlistener(" not in low and "onclick=" not in low:
        return False
    modern_markers = ["linear-gradient", "radial-gradient", "@media", "clamp("]
    if sum(1 for marker in modern_markers if marker in low) < 2:
        return False
    structure_markers = ["hero", "feature", "testimonial", "faq", "contact", "pricing"]
    if sum(1 for marker in structure_markers if marker in low) < 3:
        return False

    # Bad image payload leakage from model output.
    if "data:image" in low and "..." in html:
        return False

    features_set = set(features or [])
    if "Authentication" in features_set:
        required = ("signup-form", "login-form")
        if any(token not in low for token in required):
            return False

    if project_type in FULLSTACK_TYPES:
        has_api_usage = ("localhost:5001" in low) or ("/api/" in low and "fetch(" in low)
        if not has_api_usage:
            return False

    if project_type in FRONTEND_ONLY_TYPES and "localhost:5001" in low:
        return False

    return True


def _has_domain_mismatch(html: str, archetype: str) -> bool:
    low = (html or "").lower()
    if archetype != "ecommerce" and any(tok in low for tok in ("shop smarter", "featured products", "add to cart", "wishlist", "search products", "checkout")):
        return True
    if archetype != "food" and any(tok in low for tok in ("restaurants near you", "selected restaurant menu", "burger", "pizza avenue", "sushi spot", "zomato", "swiggy")):
        return True
    if archetype != "jobs" and any(tok in low for tok in ("featured job openings", "apply role", "salary range", "job seeker")):
        return True
    if archetype != "healthcare" and any(tok in low for tok in ("clinical services", "doctor directory", "appointment booking", "hospital facilities")):
        return True
    if archetype != "library" and any(tok in low for tok in ("reading list", "borrow book", "library catalog", "book details")):
        return True
    return False


def _domain_requirements_ok(html: str, archetype: str, description: str, features) -> bool:
    low = (html or "").lower()
    text = (description or "").lower()
    feature_set = set(features or [])

    if archetype == "healthcare":
        buckets = []
        if any(k in text for k in ("doctor", "specialization", "department")):
            buckets.append(("doctor/specialization", ("doctor", "specialization", "department")))
        if any(k in text for k in ("appointment", "slot", "schedule", "booking")):
            buckets.append(("appointment flow", ("appointment", "slot", "schedule", "book")))
        if any(k in text for k in ("history", "manage booking", "booking history")):
            buckets.append(("history", ("history", "my appointments", "bookings")))
        if ("Authentication" in feature_set) or any(k in text for k in ("login", "signup", "sign up", "account", "patient login")):
            buckets.append(("auth", ("login", "signup")))
        for _, tokens in buckets:
            if not any(tok in low for tok in tokens):
                return False

    if archetype == "jobs":
        if any(k in text for k in ("job", "jobs", "role", "application")) and not any(tok in low for tok in ("job", "role", "application")):
            return False

    if archetype == "library":
        if any(k in text for k in ("book", "library", "borrow", "author")) and not any(tok in low for tok in ("book", "library", "borrow", "author")):
            return False

    return True


def _build_generation_blueprint(project_name: str, description: str, project_type: str, features) -> str:
    feature_set = set(features or [])
    archetype = _infer_site_archetype(project_name, description, project_type)

    if archetype == "ecommerce":
        audience = "online shoppers comparing products, value, and delivery speed"
        section_plan = "hero with offer, category grid, product spotlight, value props, testimonials, FAQ, contact/footer"
        interactive_plan = "search/filter chips, quick-view modal or detail drawer, cart/wishlist interactions"
    elif archetype == "jobs":
        audience = "job seekers and recruiters discovering roles, profiles, and applications"
        section_plan = "hero, job categories, featured roles, employer highlights, application flow, FAQ, contact/footer"
        interactive_plan = "search + filters, role detail drawer, save/apply states, admin/recruiter dashboard"
    elif archetype == "library":
        audience = "readers, students, and members browsing books and managing borrowing"
        section_plan = "hero, categories, featured books, new arrivals, member highlights, FAQ, contact/footer"
        interactive_plan = "catalog search, category tabs, save/borrow list, member dashboard"
    elif archetype == "travel":
        audience = "travelers comparing destinations, packages, and bookings"
        section_plan = "hero, destination categories, package cards, trust signals, itinerary section, FAQ, contact/footer"
        interactive_plan = "destination filters, save itinerary, booking flow states, price highlights"
    elif archetype == "healthcare":
        audience = "patients finding services, doctors, and appointments"
        section_plan = "hero, service categories, doctor cards, care process, trust badges, FAQ, contact/footer"
        interactive_plan = "service filters, appointment states, profile forms, admin appointment overview"
    elif project_type == "blog":
        audience = "readers looking for useful and trustworthy editorial content"
        section_plan = "hero, featured stories, category navigation, newsletter, author section, FAQ, contact/footer"
        interactive_plan = "category tabs, search by title/tag, expandable FAQ"
    elif project_type in {"landing", "portfolio", "business"}:
        audience = "new visitors evaluating credibility and value quickly"
        section_plan = "hero, proof/metrics, services/features, workflow/process, testimonials, pricing/CTA, FAQ, contact/footer"
        interactive_plan = "sticky nav scroll, animated reveal, FAQ accordion"
    else:
        audience = "end users expecting an official and modern digital product"
        section_plan = "hero, capabilities, use cases, trust signals, testimonials, FAQ, contact/footer"
        interactive_plan = "tabs/cards filtering, animated reveals, sticky section navigation"

    if "Authentication" in feature_set:
        interactive_plan += ", login/signup state and account-aware navigation"
    if "Admin Dashboard" in feature_set:
        interactive_plan += ", admin summary/management panel"
    style_sig = _style_signature(project_name, description, archetype)
    requirements = _extract_description_requirements(description, archetype)
    req_lines = "\n".join(f"- must_include_requirement: {item}" for item in requirements)

    return f"""
Design analysis:
- inferred_archetype: {archetype}
- target_audience: {audience}
- section_plan: {section_plan}
- interaction_plan: {interactive_plan}
- quality_target: official website quality suitable for real-world launch demos
{style_sig}
{req_lines}
""".strip()


def _generation_creative_direction(name: str, desc: str, archetype: str, attempt: int = 1) -> str:
    palettes = [
        ("#0f172a", "#0ea5e9", "#22c55e", "#f8fafc"),
        ("#1f2937", "#f97316", "#14b8a6", "#fff7ed"),
        ("#0b132b", "#5bc0be", "#f4d35e", "#f6f7fb"),
        ("#111827", "#e11d48", "#0ea5e9", "#fff1f2"),
        ("#102a43", "#2bb0ed", "#f7b267", "#f4f9ff"),
    ]
    typography = [
        "Space Grotesk + Manrope",
        "Poppins + DM Sans",
        "Sora + Inter",
        "Urbanist + Source Sans 3",
        "Outfit + Nunito Sans",
    ]
    layouts = [
        "staggered editorial blocks with asymmetric rhythm",
        "dashboard-inspired modular cards with compact spacing",
        "storytelling narrative flow with alternating light/dark bands",
        "magazine-like hero with split utility panel and trust rail",
        "conversion-focused sections with sticky navigation and jump links",
    ]
    interactions = [
        "filter chips + dynamic cards + accordion FAQ",
        "tabbed feature matrix + count-up stats + sticky section nav",
        "search + sorting + detail drawer interactions",
        "wizard-like progression and status badges",
        "interactive pricing toggles + reveal-on-scroll + quick actions",
    ]

    idx = _variation_index(name, desc + f"|a{attempt}|{random.randint(1, 9999)}", archetype, len(palettes))
    p = palettes[idx]
    return f"""
CREATIVE DIRECTION:
- palette_hint: primary {p[0]}, accent {p[1]}, support {p[2]}, surface {p[3]}
- typography_hint: {typography[idx]}
- layout_hint: {layouts[idx]}
- interaction_hint: {interactions[idx]}
- novelty_rule: avoid same section naming, avoid same hero sentence, avoid same nav label set from prior attempts
""".strip()


def _extract_visual_mood(description: str, archetype: str) -> str:
    text = (description or "").lower()
    if archetype == "healthcare":
        return "clean, trustworthy, clinical, calm, premium"
    if archetype == "travel":
        return "immersive, aspirational, scenic, editorial, atmospheric"
    if archetype == "jobs":
        return "credible, professional, structured, high-clarity"
    if archetype == "library":
        return "thoughtful, quiet, editorial, curated"
    if archetype == "ecommerce":
        return "conversion-focused, energetic, polished, promotional"
    if archetype == "saas":
        return "product-led, data-rich, enterprise-modern, efficient"
    if any(k in text for k in ("luxury", "premium", "elite")):
        return "premium, spacious, refined, high-contrast"
    if any(k in text for k in ("youth", "bold", "creative", "modern")):
        return "bold, expressive, modern, high-energy"
    return "modern, official, polished, distinctive"


def _extract_description_entities(description: str):
    text = (description or "").lower()
    entities = []
    entity_map = [
        ("doctor", "doctor profiles"),
        ("appointment", "appointment flow"),
        ("department", "department explorer"),
        ("patient", "patient account area"),
        ("hotel", "hotel listings"),
        ("room", "room availability"),
        ("booking", "booking management"),
        ("flight", "travel routes"),
        ("product", "product grid"),
        ("cart", "cart workflow"),
        ("wishlist", "wishlist flow"),
        ("dashboard", "dashboard summary"),
        ("analytics", "analytics widgets"),
        ("pricing", "pricing or plans"),
        ("contact", "contact support"),
        ("faq", "FAQ section"),
    ]
    for needle, label in entity_map:
        if needle in text and label not in entities:
            entities.append(label)
    return entities[:8]


def _derive_section_labels(description: str, archetype: str, project_type: str, features):
    feature_set = set(features or [])
    if archetype == "healthcare":
        labels = ["Care Overview", "Specialists", "Departments", "Appointments", "Facilities", "Insurance", "FAQ", "Contact"]
    elif archetype == "travel":
        labels = ["Destinations", "Packages", "Stays", "Itinerary", "Booking Flow", "Traveler Reviews", "FAQ", "Contact"]
    elif archetype == "jobs":
        labels = ["Open Roles", "Teams", "Why Join", "Application Flow", "Success Stories", "FAQ", "Contact"]
    elif archetype == "library":
        labels = ["Collections", "Categories", "Featured Books", "Membership", "Digital Access", "FAQ", "Contact"]
    elif archetype == "ecommerce":
        labels = ["Featured Picks", "Categories", "Offers", "Benefits", "Reviews", "FAQ", "Support"]
    elif archetype == "saas":
        labels = ["Overview", "Capabilities", "Workflows", "Metrics", "Integrations", "Pricing", "FAQ", "Contact"]
    else:
        labels = ["Overview", "Features", "Proof", "Workflow", "Testimonials", "FAQ", "Contact"]

    desc_entities = _extract_description_entities(description)
    if "Authentication" in feature_set and "Account" not in labels:
        labels.insert(min(4, len(labels)), "Account")
    if "Admin Dashboard" in feature_set and "Admin" not in labels:
        labels.insert(min(5, len(labels)), "Admin")
    for entity in desc_entities:
        normalized = entity.title()
        if normalized not in labels:
            labels.insert(min(4, len(labels)), normalized)
    seen = set()
    out = []
    for label in labels:
        if label not in seen:
            seen.add(label)
            out.append(label)
    return out[:9]


def _recent_layout_constraints(limit: int = 12) -> str:
    examples = []
    for html in _recent_generated_htmls(limit=limit):
        fp = _html_layout_fingerprint(html)
        if fp:
            examples.append(fp[:260])
    if not examples:
        return ""
    sample = "\n".join(f"- avoid_similarity_to: {item}" for item in examples[:6])
    return f"RECENT LAYOUT CONSTRAINTS:\n{sample}"


def _html_layout_fingerprint(html: str) -> str:
    if not html:
        return ""
    low = html.lower()
    # Keep only structural signals and key labels so we compare layout shape, not raw content length.
    section_ids = re.findall(r'<section[^>]*id=["\']([^"\']+)["\']', low)
    headings = re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", low, flags=re.DOTALL)
    nav_labels = re.findall(r"<button[^>]*data-view=[\"'][^\"']+[\"'][^>]*>(.*?)</button>", low, flags=re.DOTALL)
    clean = lambda arr: [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", x)).strip()[:48] for x in arr]
    parts = [
        "sections:" + "|".join(section_ids[:12]),
        "heads:" + "|".join(clean(headings)[:12]),
        "nav:" + "|".join(clean(nav_labels)[:10]),
        "tokens:" + "|".join(tok for tok in ("hero", "faq", "testimonial", "pricing", "contact", "admin", "cart", "wishlist") if tok in low),
    ]
    return " || ".join(parts)


def _recent_generated_htmls(limit: int = 30):
    rows = []
    try:
        for proj in GENERATED_ROOT.iterdir():
            if not proj.is_dir():
                continue
            f = proj / "frontend" / "index.html"
            if f.exists():
                rows.append((f.stat().st_mtime, f))
    except Exception:
        return []
    rows.sort(key=lambda x: x[0], reverse=True)
    out = []
    for _, path in rows[:limit]:
        try:
            out.append(path.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
    return out


def _is_layout_too_similar_to_existing(candidate_html: str, threshold: float = 0.88) -> bool:
    cand_fp = _html_layout_fingerprint(candidate_html)
    if not cand_fp:
        return False
    for old_html in _recent_generated_htmls(limit=30):
        old_fp = _html_layout_fingerprint(old_html)
        if not old_fp:
            continue
        ratio = SequenceMatcher(None, cand_fp, old_fp).ratio()
        if ratio >= threshold:
            return True
    return False


def _domain_professional_fallback_html(name: str, desc: str, project_type: str, features, archetype: str) -> str:
    profiles = {
        "jobs": {
            "accent": "#2563eb",
            "hero_image": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=1400&q=80",
            "home_title": "Featured Job Openings",
            "detail_title": "Role Details",
            "saved_title": "Saved Applications",
            "saved_button": "Save Role",
            "open_button": "View Role",
            "action_label": "Apply",
            "meta_label": "Location",
            "items": [
                {"id": "i1", "title": "Frontend Engineer", "subtitle": "Nova Labs", "meta": "Bengaluru | Hybrid", "value": "LPA 18-24", "img": "https://images.unsplash.com/photo-1521737711867-e3b97375f902?auto=format&fit=crop&w=900&q=80"},
                {"id": "i2", "title": "Backend Developer", "subtitle": "Orbit Systems", "meta": "Hyderabad | Remote", "value": "LPA 16-22", "img": "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?auto=format&fit=crop&w=900&q=80"},
                {"id": "i3", "title": "Product Designer", "subtitle": "Pixel Forge", "meta": "Pune | On-site", "value": "LPA 14-19", "img": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=900&q=80"},
                {"id": "i4", "title": "Data Analyst", "subtitle": "Insight Grid", "meta": "Chennai | Hybrid", "value": "LPA 10-15", "img": "https://images.unsplash.com/photo-1516321497487-e288fb19713f?auto=format&fit=crop&w=900&q=80"},
            ],
        },
        "library": {
            "accent": "#7c3aed",
            "hero_image": "https://images.unsplash.com/photo-1521587760476-6c12a4b040da?auto=format&fit=crop&w=1400&q=80",
            "home_title": "Popular Books & Collections",
            "detail_title": "Book Details",
            "saved_title": "Reading List",
            "saved_button": "Save Book",
            "open_button": "Open Book",
            "action_label": "Borrow",
            "meta_label": "Author",
            "items": [
                {"id": "i1", "title": "Modern Systems Design", "subtitle": "Technology", "meta": "Ava Mitchell", "value": "4.8/5", "img": "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=900&q=80"},
                {"id": "i2", "title": "History of Civilizations", "subtitle": "History", "meta": "Noah Carter", "value": "4.7/5", "img": "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?auto=format&fit=crop&w=900&q=80"},
                {"id": "i3", "title": "Practical Data Science", "subtitle": "Science", "meta": "Liam Hart", "value": "4.9/5", "img": "https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=900&q=80"},
                {"id": "i4", "title": "Business Strategy Essentials", "subtitle": "Business", "meta": "Emma Reid", "value": "4.6/5", "img": "https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&w=900&q=80"},
            ],
        },
        "healthcare": {
            "accent": "#0891b2",
            "hero_image": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=1400&q=80",
            "home_title": "Doctors, Departments & Services",
            "detail_title": "Doctor Profile & Available Slots",
            "saved_title": "Appointment History",
            "saved_button": "Save Doctor",
            "open_button": "View Doctor",
            "action_label": "Book Appointment",
            "meta_label": "Specialization",
            "items": [
                {"id": "i1", "title": "Dr. Anika Rao", "subtitle": "Senior Consultant", "meta": "Cardiology", "value": "Slots: 10:00, 11:30, 16:00", "img": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&w=900&q=80"},
                {"id": "i2", "title": "Dr. Karthik Menon", "subtitle": "Consultant", "meta": "Orthopedics", "value": "Slots: 09:30, 13:00, 17:15", "img": "https://images.unsplash.com/photo-1612349316228-5942a9b489c2?auto=format&fit=crop&w=900&q=80"},
                {"id": "i3", "title": "Dr. Meera Iyer", "subtitle": "Consultant", "meta": "Neurology", "value": "Slots: 08:45, 12:15, 15:30", "img": "https://images.unsplash.com/photo-1594824475544-3fa0f0f31f8e?auto=format&fit=crop&w=900&q=80"},
                {"id": "i4", "title": "Dr. Salman Yusuf", "subtitle": "Consultant", "meta": "General Medicine", "value": "Slots: 10:30, 14:00, 18:00", "img": "https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&w=900&q=80"},
            ],
        },
        "travel": {
            "accent": "#ea580c",
            "hero_image": "https://images.unsplash.com/photo-1488085061387-422e29b40080?auto=format&fit=crop&w=1400&q=80",
            "home_title": "Top Destinations",
            "detail_title": "Trip Details",
            "saved_title": "Saved Trips",
            "saved_button": "Save Trip",
            "open_button": "View Trip",
            "action_label": "Book",
            "meta_label": "Duration",
            "items": [
                {"id": "i1", "title": "Bali Escape", "subtitle": "Indonesia", "meta": "5 Nights", "value": "$699", "img": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=900&q=80"},
                {"id": "i2", "title": "Swiss Alps Tour", "subtitle": "Switzerland", "meta": "7 Nights", "value": "$1499", "img": "https://images.unsplash.com/photo-1464822759844-d150baec0494?auto=format&fit=crop&w=900&q=80"},
                {"id": "i3", "title": "Tokyo Explorer", "subtitle": "Japan", "meta": "6 Nights", "value": "$1299", "img": "https://images.unsplash.com/photo-1492571350019-22de08371fd3?auto=format&fit=crop&w=900&q=80"},
                {"id": "i4", "title": "Dubai Weekend", "subtitle": "UAE", "meta": "3 Nights", "value": "$499", "img": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=900&q=80"},
            ],
        },
        "saas": {
            "accent": "#0f766e",
            "hero_image": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1400&q=80",
            "home_title": "Active Workspaces",
            "detail_title": "Workspace Details",
            "saved_title": "Pinned Workspaces",
            "saved_button": "Pin Workspace",
            "open_button": "Open Workspace",
            "action_label": "Launch",
            "meta_label": "Plan",
            "items": [
                {"id": "i1", "title": "Growth Dashboard", "subtitle": "Marketing Ops", "meta": "Pro Plan", "value": "412 KPIs", "img": "https://images.unsplash.com/photo-1551281044-8b6d7f0f8f84?auto=format&fit=crop&w=900&q=80"},
                {"id": "i2", "title": "Sales Pipeline", "subtitle": "Revenue Team", "meta": "Business Plan", "value": "89 deals", "img": "https://images.unsplash.com/photo-1557804506-669a67965ba0?auto=format&fit=crop&w=900&q=80"},
                {"id": "i3", "title": "Customer Support Hub", "subtitle": "Support Team", "meta": "Pro Plan", "value": "1.4k tickets", "img": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=900&q=80"},
                {"id": "i4", "title": "Finance Console", "subtitle": "Finance Team", "meta": "Enterprise", "value": "MRR $82k", "img": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=900&q=80"},
            ],
        },
        "generic": {
            "accent": "#4f46e5",
            "hero_image": "https://images.unsplash.com/photo-1552664730-d307ca884978?auto=format&fit=crop&w=1400&q=80",
            "home_title": "Featured Solutions",
            "detail_title": "Solution Details",
            "saved_title": "Saved Items",
            "saved_button": "Save Item",
            "open_button": "View Item",
            "action_label": "Explore",
            "meta_label": "Category",
            "items": [
                {"id": "i1", "title": "Customer Growth Program", "subtitle": "Business", "meta": "Acquisition", "value": "High Impact", "img": "https://images.unsplash.com/photo-1556740749-887f6717d7e4?auto=format&fit=crop&w=900&q=80"},
                {"id": "i2", "title": "Automation Toolkit", "subtitle": "Operations", "meta": "Workflow", "value": "Fast Setup", "img": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=900&q=80"},
                {"id": "i3", "title": "Analytics Studio", "subtitle": "Insights", "meta": "Reporting", "value": "Live Data", "img": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=900&q=80"},
                {"id": "i4", "title": "Team Collaboration Hub", "subtitle": "Productivity", "meta": "Workspace", "value": "Multi-team", "img": "https://images.unsplash.com/photo-1551434678-e076c223a692?auto=format&fit=crop&w=900&q=80"},
            ],
        },
    }

    profile = profiles.get(archetype, profiles["generic"])
    title = name or "Generated Website"
    subtitle = _default_hero_subtitle(archetype)
    feature_set = set(features or [])
    show_auth = ("Authentication" in feature_set) or ("Authentication" in _description_feature_inference(desc))
    items_json = json.dumps(profile["items"])
    variant = _variation_index(name, desc, archetype, 3)
    hero_titles = [
        "Interactive, professional, and ready for real-world use",
        "Built for real users with focused workflows and trusted interactions",
        "Modern, high-clarity interface designed for real operations",
    ]
    detail_labels = ["Details", "Insights", "Overview"]
    saved_labels = ["Saved", "Shortlist", "Bookmarks"]
    hero_title = hero_titles[variant]
    detail_tab = detail_labels[variant]
    saved_tab = saved_labels[variant]

    auth_nav = """
          <button data-view="login" class="ghost">Login</button>
          <button data-view="signup" class="ghost">Signup</button>
          <button id="logoutBtn" class="ghost hidden">Logout</button>
    """ if show_auth else ""
    auth_sections = """
      <section id="login" class="view hidden card">
        <h2>Login</h2>
        <form id="login-form" data-auth="login" class="auth-form">
          <input type="email" name="email" placeholder="Email" required />
          <input type="password" name="password" placeholder="Password" required />
          <button type="submit">Login</button>
        </form>
        <p id="login-message" class="hint"></p>
      </section>

      <section id="signup" class="view hidden card">
        <h2>Create Account</h2>
        <form id="signup-form" data-auth="signup" class="auth-form">
          <input type="email" name="email" placeholder="Email" required />
          <input type="password" name="password" placeholder="Password" required />
          <button type="submit">Signup</button>
        </form>
        <p id="signup-message" class="hint"></p>
      </section>
    """ if show_auth else ""

    tpl = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>__TITLE__</title>
  <style>
    :root { --brand:__ACCENT__; --ink:#111827; --bg:#f7f8fc; --card:#ffffff; --line:#e2e8f0; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; background:var(--bg); color:var(--ink); }
    .topbar { position:sticky; top:0; z-index:10; display:flex; align-items:center; justify-content:space-between; padding:14px 20px; background:#0f172a; color:#fff; }
    .brand { font-size:1.35rem; font-weight:700; }
    .nav { display:flex; gap:10px; flex-wrap:wrap; }
    .nav button { border:0; border-radius:999px; padding:8px 14px; cursor:pointer; background:rgba(255,255,255,.14); color:#fff; }
    .nav .solid { background:var(--brand); }
    .hero { min-height:290px; background-image:linear-gradient(120deg, rgba(15,23,42,.75), rgba(15,23,42,.42)), url('__HERO__'); background-size:cover; background-position:center; color:#fff; display:grid; place-items:center; text-align:center; padding:40px 16px; }
    .hero h1 { margin:0 0 10px; font-size:clamp(1.9rem,3vw,3rem); }
    .hero p { margin:0; max-width:820px; line-height:1.6; opacity:.95; }
    main { max-width:1180px; margin:20px auto; padding:0 16px 30px; display:grid; gap:16px; }
    .view { display:none; }
    .view.active { display:block; }
    .card { background:var(--card); border-radius:14px; border:1px solid var(--line); box-shadow:0 8px 18px rgba(15,23,42,.07); padding:16px; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:14px; }
    .item { border:1px solid #e5e7eb; border-radius:12px; overflow:hidden; background:#fff; }
    .item img { width:100%; height:160px; object-fit:cover; display:block; }
    .item .meta { padding:12px; display:grid; gap:6px; }
    .item h3 { margin:0; font-size:1.05rem; }
    .hint { color:#475569; font-size:.94rem; }
    .row { display:flex; align-items:center; justify-content:space-between; gap:10px; }
    .row button, .primary { background:var(--brand); color:#fff; border:0; border-radius:10px; padding:8px 12px; cursor:pointer; }
    .ghost-btn { background:#eef2ff; color:#1e293b; }
    .auth-form { display:grid; gap:10px; max-width:380px; }
    .auth-form input { padding:10px; border:1px solid #d1d5db; border-radius:10px; }
    .auth-form button { padding:10px; border:0; border-radius:10px; background:var(--brand); color:#fff; cursor:pointer; font-weight:600; }
    .hidden { display:none !important; }
    footer { text-align:center; padding:24px; color:#64748b; }
    @media (max-width: 700px) { .topbar { padding:10px 12px; } .nav { gap:6px; } .nav button { padding:7px 10px; font-size:.86rem; } }
  </style>
</head>
<body>
  <header class="topbar">
    <div class="brand">__TITLE__</div>
    <nav class="nav">
      <button class="solid" data-view="home">Home</button>
      <button data-view="details">__DETAIL_TAB__</button>
      <button data-view="saved">__SAVED_TAB__ (<span id="savedCount">0</span>)</button>
      <button data-view="admin">Admin</button>
      __AUTH_NAV__
    </nav>
  </header>

  <section class="hero">
    <div>
      <h1>__HERO_TITLE__</h1>
      <p>__SUBTITLE__</p>
    </div>
  </section>

  <main>
    <section id="home" class="view active card">
      <h2>__HOME_TITLE__</h2>
      <div id="listingGrid" class="grid"></div>
    </section>

    <section id="details" class="view card">
      <h2>__DETAIL_TITLE__</h2>
      <div id="detailsHost" class="hint">Select an item from Home to view details.</div>
    </section>

    <section id="saved" class="view card">
      <h2>__SAVED_TITLE__</h2>
      <div id="savedHost" class="hint">No saved items yet.</div>
    </section>

    <section id="admin" class="view card">
      <h2>Admin Dashboard</h2>
      <p class="hint">Manage catalog entries, user activity, and operational workflows from one place.</p>
      <div class="row" style="margin-top:10px;">
        <button class="ghost-btn">Export Report</button>
        <button class="primary">Create Entry</button>
      </div>
    </section>

    __AUTH_SECTIONS__
  </main>

  <footer>Built by NovaForge | Type: __TYPE__</footer>

  <script>
    const catalog = __ITEMS__;
    let selected = null;
    let saved = [];
    let currentUser = null;
    let authToken = localStorage.getItem('nova_auth_token') || '';
    const API_BASE = 'http://localhost:5001/api';
    const views = Array.from(document.querySelectorAll('.view'));

    function view(id) {
      views.forEach(v => v.classList.remove('active'));
      const el = document.getElementById(id);
      if (el) el.classList.add('active');
      if (id === 'saved') renderSaved();
      if (id === 'details') renderDetails();
    }

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, (ch) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
    }

    function renderCatalog() {
      const host = document.getElementById('listingGrid');
      host.innerHTML = catalog.map(item => '<article class="item"><img src="' + item.img + '" alt="' + escapeHtml(item.title) + '"/><div class="meta"><h3>' + escapeHtml(item.title) + '</h3><div class="hint">' + escapeHtml(item.subtitle) + '</div><div class="hint">__META_LABEL__: ' + escapeHtml(item.meta) + '</div><div class="row"><small>' + escapeHtml(item.value) + '</small><button data-open="' + item.id + '">__OPEN_BUTTON__</button></div></div></article>').join('');
      host.querySelectorAll('button[data-open]').forEach(btn => {
        btn.addEventListener('click', () => {
          selected = catalog.find(it => it.id === btn.getAttribute('data-open'));
          view('details');
        });
      });
    }

    function renderDetails() {
      const host = document.getElementById('detailsHost');
      if (!selected) {
        host.textContent = 'Select an item from Home to view details.';
        return;
      }
      host.innerHTML = '<div class="row"><h3>' + escapeHtml(selected.title) + '</h3><button id="saveBtn">__SAVED_BUTTON__</button></div><p class="hint">' + escapeHtml(selected.subtitle) + ' | __META_LABEL__: ' + escapeHtml(selected.meta) + '</p><p class="hint">Value: ' + escapeHtml(selected.value) + '</p><div class="row"><button class="ghost-btn" id="backBtn">Back</button><button class="primary" id="actionBtn">__ACTION_LABEL__</button></div>';
      const saveBtn = document.getElementById('saveBtn');
      if (saveBtn) saveBtn.addEventListener('click', () => saveSelected());
      const backBtn = document.getElementById('backBtn');
      if (backBtn) backBtn.addEventListener('click', () => view('home'));
      const actionBtn = document.getElementById('actionBtn');
      if (actionBtn) actionBtn.addEventListener('click', () => {
        if (!currentUser) {
          alert('Login required for this action.');
          view('login');
          return;
        }
        alert('__ACTION_LABEL__ request created successfully.');
      });
    }

    function saveSelected() {
      if (!selected) return;
      if (!saved.find(it => it.id === selected.id)) saved.push(selected);
      document.getElementById('savedCount').textContent = String(saved.length);
      renderSaved();
    }

    function renderSaved() {
      const host = document.getElementById('savedHost');
      if (!saved.length) {
        host.textContent = 'No saved items yet.';
        return;
      }
      host.innerHTML = saved.map(item => '<div class="row"><span>' + escapeHtml(item.title) + '</span><button data-remove="' + item.id + '" class="ghost-btn">Remove</button></div>').join('');
      host.querySelectorAll('button[data-remove]').forEach(btn => {
        btn.addEventListener('click', () => {
          saved = saved.filter(it => it.id !== btn.getAttribute('data-remove'));
          document.getElementById('savedCount').textContent = String(saved.length);
          renderSaved();
        });
      });
    }

    function getAuthHeaders() {
      const headers = { 'Content-Type': 'application/json' };
      if (authToken) headers.Authorization = 'Bearer ' + authToken;
      return headers;
    }

    async function submitAuth(form, endpoint, messageId) {
      const email = form.querySelector('input[name="email"]').value.trim();
      const password = form.querySelector('input[name="password"]').value.trim();
      const msg = document.getElementById(messageId);
      msg.textContent = '';
      try {
        const res = await fetch('http://localhost:5001' + endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || !data.success) {
          msg.textContent = data.error || 'Authentication failed.';
          return;
        }
        authToken = data.token || '';
        if (authToken) localStorage.setItem('nova_auth_token', authToken);
        currentUser = data.user || { email };
        syncAuthUI();
        msg.textContent = endpoint.includes('signup') ? 'Signup successful.' : 'Login successful.';
        view('home');
      } catch {
        msg.textContent = 'Backend not reachable on port 5001.';
      }
    }

    function syncAuthUI() {
      const login = document.querySelector('[data-view="login"]');
      const signup = document.querySelector('[data-view="signup"]');
      const logout = document.getElementById('logoutBtn');
      const hasUser = !!currentUser;
      if (login) login.classList.toggle('hidden', hasUser);
      if (signup) signup.classList.toggle('hidden', hasUser);
      if (logout) logout.classList.toggle('hidden', !hasUser);
    }

    document.querySelectorAll('nav button[data-view]').forEach(btn => {
      btn.addEventListener('click', () => view(btn.getAttribute('data-view')));
    });
    const signupForm = document.getElementById('signup-form');
    if (signupForm) signupForm.addEventListener('submit', (e) => { e.preventDefault(); submitAuth(signupForm, '/api/auth/signup', 'signup-message'); });
    const loginForm = document.getElementById('login-form');
    if (loginForm) loginForm.addEventListener('submit', (e) => { e.preventDefault(); submitAuth(loginForm, '/api/auth/login', 'login-message'); });
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) logoutBtn.addEventListener('click', () => { currentUser = null; authToken = ''; localStorage.removeItem('nova_auth_token'); syncAuthUI(); view('home'); });

    renderCatalog();
    renderSaved();
    syncAuthUI();
  </script>
</body>
</html>
"""
    return (
        tpl.replace("__TITLE__", title)
        .replace("__SUBTITLE__", subtitle)
        .replace("__TYPE__", project_type or "fullstack")
        .replace("__AUTH_NAV__", auth_nav)
        .replace("__AUTH_SECTIONS__", auth_sections)
        .replace("__HOME_TITLE__", profile["home_title"])
        .replace("__DETAIL_TITLE__", profile["detail_title"])
        .replace("__SAVED_TITLE__", profile["saved_title"])
        .replace("__HERO_TITLE__", hero_title)
        .replace("__DETAIL_TAB__", detail_tab)
        .replace("__SAVED_TAB__", saved_tab)
        .replace("__OPEN_BUTTON__", profile["open_button"])
        .replace("__SAVED_BUTTON__", profile["saved_button"])
        .replace("__ACTION_LABEL__", profile["action_label"])
        .replace("__META_LABEL__", profile["meta_label"])
        .replace("__ACCENT__", profile["accent"])
        .replace("__HERO__", profile["hero_image"])
        .replace("__ITEMS__", items_json)
    )


def _diversify_fallback_layout(html: str, name: str, desc: str, archetype: str) -> str:
    if not html:
        return html
    variant = _variation_index(name, desc, archetype, 5)
    nav_sets = {
        "healthcare": [("Overview", "Doctors", "Appointments", "Operations"), ("Portal", "Care Team", "My Visits", "Admin"), ("Services", "Specialists", "Records", "Control")],
        "travel": [("Explore", "Packages", "Saved Trips", "Operations"), ("Discover", "Itineraries", "Shortlist", "Admin"), ("Destinations", "Trip Plans", "Wishlist", "Control")],
        "jobs": [("Openings", "Role View", "Saved Roles", "Recruiter"), ("Careers", "Details", "Shortlist", "Admin"), ("Talent Hub", "Job View", "Bookmarks", "Control")],
        "library": [("Catalog", "Book View", "Reading List", "Librarian"), ("Explore", "Details", "Saved Books", "Admin"), ("Collections", "Insights", "Bookmarks", "Control")],
        "saas": [("Workspace", "Modules", "Pinned", "Ops"), ("Overview", "Insights", "Saved Views", "Admin"), ("Command", "Details", "Shortlist", "Control")],
        "generic": [("Overview", "Details", "Saved", "Admin"), ("Homebase", "Insights", "Bookmarks", "Control"), ("Start", "Explore", "Library", "Manage")],
    }
    labels = nav_sets.get(archetype, nav_sets["generic"])[variant % 3]
    patterns = [
        (r'(<button class="solid" data-view="home">)(.*?)(</button>)', labels[0]),
        (r'(<button data-view="details">)(.*?)(</button>)', labels[1]),
        (r'(<button data-view="saved">)(.*?)(</button>)', labels[2] + " (<span id=\"savedCount\">0</span>)"),
        (r'(<button data-view="admin">)(.*?)(</button>)', labels[3]),
    ]
    for pattern, new_label in patterns:
        html = re.sub(pattern, lambda m: f"{m.group(1)}{new_label}{m.group(3)}", html, count=1, flags=re.IGNORECASE | re.DOTALL)

    hero_titles = [
        "Designed for real operations with clarity and confidence",
        "Official-grade interface optimized for daily workflows",
        "Built for production-like demos with polished interactions",
        "Modern, trusted experience shaped for real users",
        "High-clarity product experience with practical workflows",
    ]
    html = re.sub(r"(<section class=\"hero\">.*?<h1>)(.*?)(</h1>)", lambda m: f"{m.group(1)}{hero_titles[variant]}{m.group(3)}", html, count=1, flags=re.IGNORECASE | re.DOTALL)

    extra_blocks = [
        "<section class=\"card\"><h2>Trust & Outcomes</h2><p class=\"hint\">Service quality metrics, verified reviews, and transparent process highlights.</p></section>",
        "<section class=\"card\"><h2>Workflow Snapshot</h2><p class=\"hint\">Track your progress through clear states, quick actions, and centralized records.</p></section>",
        "<section class=\"card\"><h2>Why This Experience Works</h2><p class=\"hint\">Fast navigation, clear information hierarchy, and role-aware interactions built for reliability.</p></section>",
        "<section class=\"card\"><h2>Support & Guidance</h2><p class=\"hint\">Built-in help paths, contact channels, and accountable service ownership.</p></section>",
        "<section class=\"card\"><h2>Performance Highlights</h2><p class=\"hint\">Responsive layouts, structured content, and interaction consistency across devices.</p></section>",
    ]
    if "</main>" in html:
        html = html.replace("</main>", f"\n    {extra_blocks[variant]}\n  </main>", 1)

    palette = [
        ("#0ea5e9", "#f0f9ff"),
        ("#f97316", "#fff7ed"),
        ("#10b981", "#ecfdf5"),
        ("#e11d48", "#fff1f2"),
        ("#6366f1", "#eef2ff"),
    ][variant]
    html = re.sub(r"--brand:[^;]+;", f"--brand:{palette[0]};", html, count=1, flags=re.IGNORECASE)
    html = re.sub(r"--bg:[^;]+;", f"--bg:{palette[1]};", html, count=1, flags=re.IGNORECASE)
    return html


def _professional_fallback_html(name: str, desc: str, project_type: str, features) -> str:
    archetype = _infer_site_archetype(name, desc, project_type)
    desc_low = (desc or "").lower()
    if archetype == "food" and any(k in desc_low for k in ("hospital", "clinic", "doctor", "patient", "healthcare", "medical")):
        archetype = "healthcare"
    if archetype == "ecommerce":
        raw = _ecommerce_fallback_html(name, desc, project_type, features)
        return _diversify_fallback_layout(raw, name, desc, archetype)
    if archetype != "food":
        raw = _domain_professional_fallback_html(name, desc, project_type, features, archetype)
        return _diversify_fallback_layout(raw, name, desc, archetype)

    title = name or "Generated Website"
    subtitle = _default_hero_subtitle(archetype)
    show_auth = ("Authentication" in set(features or [])) or ("Authentication" in _description_feature_inference(desc))
    auth_nav = """
          <button data-view="login" class="ghost">Login</button>
          <button data-view="signup" class="ghost">Signup</button>
          <button id="logoutBtn" class="ghost hidden">Logout</button>
    """ if show_auth else ""
    auth_sections = """
      <section id="login" class="view hidden card">
        <h2>Login</h2>
        <form id="login-form" data-auth="login" class="auth-form">
          <input type="email" name="email" placeholder="Email" required />
          <input type="password" name="password" placeholder="Password" required />
          <button type="submit">Login</button>
        </form>
        <p id="login-message" class="hint"></p>
      </section>

      <section id="signup" class="view hidden card">
        <h2>Sign Up</h2>
        <form id="signup-form" data-auth="signup" class="auth-form">
          <input type="email" name="email" placeholder="Email" required />
          <input type="password" name="password" placeholder="Password" required />
          <button type="submit">Create account</button>
        </form>
        <p id="signup-message" class="hint"></p>
      </section>
    """ if show_auth else ""

    tpl = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>__TITLE__</title>
  <style>
    :root { --brand:#e23744; --ink:#1f2937; --bg:#f3f4f6; --card:#ffffff; --ok:#15803d; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; background:var(--bg); color:var(--ink); }
    .topbar { position:sticky; top:0; z-index:10; display:flex; align-items:center; justify-content:space-between; padding:14px 20px; background:var(--brand); color:#fff; }
    .brand { font-size:1.4rem; font-weight:700; letter-spacing:.3px; }
    .nav { display:flex; gap:10px; flex-wrap:wrap; }
    .nav button { border:0; border-radius:999px; padding:8px 14px; cursor:pointer; }
    .nav .ghost { background:rgba(255,255,255,.18); color:#fff; }
    .nav .solid { background:#fff; color:var(--brand); font-weight:700; }
    .hero { min-height:300px; background-image:linear-gradient(120deg, rgba(226,55,68,.8), rgba(16,24,40,.72)), url('__HERO__'); background-size:cover; background-position:center; color:#fff; display:grid; place-items:center; text-align:center; padding:40px 16px; }
    .hero h1 { margin:0 0 10px; font-size:clamp(1.9rem,3vw,3rem); }
    .hero p { margin:0; max-width:760px; line-height:1.6; opacity:.96; }
    main { max-width:1180px; margin:20px auto; padding:0 16px 30px; display:grid; gap:16px; }
    .card { background:var(--card); border-radius:14px; box-shadow:0 10px 24px rgba(0,0,0,.08); padding:16px; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:14px; }
    .item { border:1px solid #e5e7eb; border-radius:12px; overflow:hidden; background:#fff; }
    .item img { width:100%; height:150px; object-fit:cover; display:block; }
    .item .meta { padding:12px; display:grid; gap:8px; }
    .item h3 { margin:0; font-size:1.05rem; }
    .row { display:flex; align-items:center; justify-content:space-between; gap:10px; }
    .row button { background:var(--brand); color:#fff; border:0; border-radius:10px; padding:8px 12px; cursor:pointer; }
    .hidden { display:none !important; }
    .hint { font-size:.94rem; opacity:.85; min-height:1.2rem; }
    .auth-form { display:grid; gap:10px; max-width:380px; }
    .auth-form input { padding:10px; border:1px solid #d1d5db; border-radius:10px; }
    .auth-form button { padding:10px; border:0; border-radius:10px; background:var(--brand); color:#fff; cursor:pointer; font-weight:600; }
    footer { text-align:center; padding:24px; color:#6b7280; }
  </style>
</head>
<body>
  <header class="topbar">
    <div class="brand">__TITLE__</div>
    <nav class="nav">
      <button class="solid" data-view="home">Home</button>
      <button class="ghost" data-view="menu">Menu</button>
      <button class="ghost" data-view="cart">Cart (<span id="cartCount">0</span>)</button>
      <button class="ghost" data-view="orders">Orders</button>
      <button class="ghost" data-view="admin">Admin</button>
      __AUTH_NAV__
    </nav>
  </header>

  <section class="hero">
    <div>
      <h1>Interactive, professional, and ready to demo</h1>
      <p>__SUBTITLE__</p>
    </div>
  </section>

  <main>
    <section id="home" class="view card">
      <h2>Restaurants Near You</h2>
      <div id="restaurantGrid" class="grid"></div>
    </section>

    <section id="menu" class="view hidden card">
      <h2>Selected Restaurant Menu</h2>
      <div id="menuGrid" class="grid"></div>
    </section>

    <section id="cart" class="view hidden card">
      <h2>Your Cart</h2>
      <div id="cartItems" class="hint">No items yet.</div>
      <div class="row" style="margin-top:10px;">
        <strong>Total: $<span id="cartTotal">0.00</span></strong>
        <button id="checkoutBtn">Checkout</button>
      </div>
    </section>

    <section id="orders" class="view hidden card">
      <h2>Order History</h2>
      <div id="orderHistory" class="hint">No orders yet.</div>
    </section>

    <section id="admin" class="view hidden card">
      <h2>Admin Dashboard</h2>
      <p class="hint">Manage listings, users, and operations from one place.</p>
    </section>

    __AUTH_SECTIONS__
  </main>

  <footer>Built by NovaForge | Type: __TYPE__</footer>

  <script>
    const restaurants = [
      { id:'r1', name:'Grand Indian', cuisine:'Indian', img:'__IMG1__', menu:[['Paneer Tikka',8.5],['Butter Chicken',11.2],['Naan Basket',4.0]] },
      { id:'r2', name:'Pizza Avenue', cuisine:'Italian', img:'__IMG2__', menu:[['Margherita',9.1],['Farmhouse',10.4],['Garlic Bread',3.8]] },
      { id:'r3', name:'Sushi Spot', cuisine:'Japanese', img:'__IMG3__', menu:[['California Roll',10.8],['Miso Soup',3.1],['Salmon Nigiri',12.2]] },
      { id:'r4', name:'Burger Foundry', cuisine:'American', img:'__IMG4__', menu:[['Classic Burger',8.9],['Fries',2.9],['Cola',1.8]] }
    ];

    let selectedRestaurant = null;
    let cart = [];
    let orders = [];
    let currentUser = null;
    let authToken = localStorage.getItem('zomato2_auth_token') || '';
    const API_BASE = 'http://localhost:5001/api';
    const views = Array.from(document.querySelectorAll('.view'));

    function setView(id) {
      views.forEach(v => v.classList.toggle('hidden', v.id !== id));
      if (id === 'home') renderRestaurants();
      if (id === 'menu') renderMenu();
      if (id === 'cart') renderCart();
      if (id === 'orders') renderOrders();
    }

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, (ch) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
    }

    function renderRestaurants() {
      const host = document.getElementById('restaurantGrid');
      host.innerHTML = restaurants.map(r => '<article class="item"><img src="' + r.img + '" alt="' + escapeHtml(r.name) + '"/><div class="meta"><h3>' + escapeHtml(r.name) + '</h3><p class="hint">' + escapeHtml(r.cuisine) + '</p><div class="row"><small>Open now</small><button data-open="' + r.id + '">View Menu</button></div></div></article>').join('');
      host.querySelectorAll('button[data-open]').forEach(btn => {
        btn.addEventListener('click', () => {
          selectedRestaurant = restaurants.find(r => r.id === btn.getAttribute('data-open'));
          setView('menu');
        });
      });
    }

    function renderMenu() {
      const host = document.getElementById('menuGrid');
      if (!selectedRestaurant) {
        host.innerHTML = '<p class="hint">Select a restaurant from Home first.</p>';
        return;
      }
      host.innerHTML = selectedRestaurant.menu.map(([name, price], idx) => '<article class="item"><div class="meta"><h3>' + escapeHtml(name) + '</h3><p class="hint">$' + price.toFixed(2) + '</p><div class="row"><small>Ready in 20 mins</small><button data-add="' + idx + '">Add</button></div></div></article>').join('');
      host.querySelectorAll('button[data-add]').forEach(btn => {
        btn.addEventListener('click', () => {
          const row = selectedRestaurant.menu[Number(btn.getAttribute('data-add'))];
          const id = selectedRestaurant.id + ':' + row[0];
          const hit = cart.find(i => i.id === id);
          if (hit) hit.qty += 1;
          else cart.push({ id, name: row[0], price: row[1], qty: 1 });
          updateCartCount();
        });
      });
    }

    function updateCartCount() {
      const count = cart.reduce((a, b) => a + b.qty, 0);
      document.getElementById('cartCount').textContent = String(count);
    }

    function renderCart() {
      const host = document.getElementById('cartItems');
      if (!cart.length) {
        host.textContent = 'No items yet.';
        document.getElementById('cartTotal').textContent = '0.00';
        return;
      }
      host.innerHTML = cart.map(item => '<div class="row"><span>' + escapeHtml(item.name) + ' x ' + item.qty + '</span><strong>$' + (item.qty * item.price).toFixed(2) + '</strong></div>').join('');
      const total = cart.reduce((a, b) => a + b.qty * b.price, 0);
      document.getElementById('cartTotal').textContent = total.toFixed(2);
    }

    function renderOrders() {
      const host = document.getElementById('orderHistory');
      if (!orders.length) {
        host.textContent = 'No orders yet.';
        return;
      }
      host.innerHTML = orders.map(o => {
        const total = Number(o.total_amount || o.total || 0);
        const date = o.order_date || o.date || '';
        const oid = o.order_id || o.id || '';
        const items = Array.isArray(o.items) ? o.items : [];
        const itemText = items.map(it => (it.name || 'item') + ' x ' + (it.qty || it.quantity || 1)).join(', ');
        return '<div class="card"><strong>Order #' + escapeHtml(String(oid)) + '</strong><p class="hint">' + escapeHtml(String(date)) + ' | $' + total.toFixed(2) + '</p><p class="hint">' + escapeHtml(itemText || 'No items') + '</p></div>';
      }).join('');
    }

    function getAuthHeaders() {
      const h = { 'Content-Type': 'application/json' };
      if (authToken) h.Authorization = 'Bearer ' + authToken;
      return h;
    }

    async function loadOrdersFromServer() {
      if (!authToken) {
        orders = [];
        return;
      }
      try {
        const res = await fetch(API_BASE + '/orders/mine', { headers: getAuthHeaders() });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.success && Array.isArray(data.orders)) {
          orders = data.orders;
        } else {
          orders = [];
        }
      } catch {
        orders = [];
      }
    }

    async function restoreSession() {
      if (!authToken) return;
      try {
        const res = await fetch(API_BASE + '/auth/me', { headers: getAuthHeaders() });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.success && data.user) {
          currentUser = data.user;
          await loadOrdersFromServer();
          syncAuthUI();
          return;
        }
      } catch {}
      authToken = '';
      currentUser = null;
      localStorage.removeItem('zomato2_auth_token');
      orders = [];
      syncAuthUI();
    }

    async function submitAuth(form, endpoint, msgId) {
      const email = form.querySelector('input[name=\"email\"]').value.trim();
      const password = form.querySelector('input[name=\"password\"]').value.trim();
      const msg = document.getElementById(msgId);
      msg.textContent = '';
      if (!email || !password) {
        msg.textContent = 'Email and password are required.';
        return;
      }
      try {
        const res = await fetch('http://localhost:5001' + endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || !data.success) {
          msg.textContent = data.error || 'Authentication failed.';
          return;
        }
        currentUser = data.user || { email };
        authToken = data.token || '';
        if (authToken) {
          localStorage.setItem('zomato2_auth_token', authToken);
        }
        await loadOrdersFromServer();
        msg.textContent = endpoint.includes('signup') ? 'Signup successful.' : 'Login successful.';
        syncAuthUI();
        setView('home');
      } catch (err) {
        msg.textContent = 'Backend not reachable. Start backend on port 5001 and try again.';
      }
    }

    function syncAuthUI() {
      const logout = document.getElementById('logoutBtn');
      if (!logout) return;
      const loginBtn = document.querySelector('[data-view=\"login\"]');
      const signupBtn = document.querySelector('[data-view=\"signup\"]');
      const loggedIn = !!currentUser;
      if (loginBtn) loginBtn.classList.toggle('hidden', loggedIn);
      if (signupBtn) signupBtn.classList.toggle('hidden', loggedIn);
      logout.classList.toggle('hidden', !loggedIn);
    }

    document.querySelectorAll('nav button[data-view]').forEach(btn => {
      btn.addEventListener('click', () => setView(btn.getAttribute('data-view')));
    });

    const checkoutBtn = document.getElementById('checkoutBtn');
    if (checkoutBtn) {
      checkoutBtn.addEventListener('click', async () => {
        if (!cart.length) return;
        if (!currentUser) {
          alert('Please login first.');
          setView('login');
          return;
        }
        const total = cart.reduce((a, b) => a + b.qty * b.price, 0);
        const items = cart.map(it => ({ id: it.id, name: it.name, price: it.price, qty: it.qty }));
        try {
          const res = await fetch(API_BASE + '/orders', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ items, total })
          });
          const data = await res.json().catch(() => ({}));
          if (!res.ok || !data.success) {
            alert(data.error || 'Could not save order.');
            return;
          }
          await loadOrdersFromServer();
        } catch (e) {
          alert('Failed to connect backend while placing order.');
          return;
        }
        cart = [];
        updateCartCount();
        setView('orders');
      });
    }

    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
      signupForm.addEventListener('submit', (e) => {
        e.preventDefault();
        submitAuth(signupForm, '/api/auth/signup', 'signup-message');
      });
    }

    const loginForm = document.getElementById('login-form');
    if (loginForm) {
      loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        submitAuth(loginForm, '/api/auth/login', 'login-message');
      });
    }

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => {
        currentUser = null;
        authToken = '';
        localStorage.removeItem('zomato2_auth_token');
        orders = [];
        syncAuthUI();
        setView('home');
      });
    }

    renderRestaurants();
    updateCartCount();
    syncAuthUI();
    restoreSession();
  </script>
</body>
</html>
"""
    raw_html = (
        tpl.replace("__TITLE__", title)
        .replace("__SUBTITLE__", subtitle)
        .replace("__TYPE__", project_type or "custom")
        .replace("__AUTH_NAV__", auth_nav)
        .replace("__AUTH_SECTIONS__", auth_sections)
        .replace("__HERO__", DEFAULT_IMAGE_URLS[0])
        .replace("__IMG1__", DEFAULT_IMAGE_URLS[0])
        .replace("__IMG2__", DEFAULT_IMAGE_URLS[1])
        .replace("__IMG3__", DEFAULT_IMAGE_URLS[2])
        .replace("__IMG4__", DEFAULT_IMAGE_URLS[3])
    )
    return _diversify_fallback_layout(raw_html, name, desc, archetype)


def _normalize_image_data_url(image_data: str) -> str:
    if not image_data:
        return ""
    src = image_data.strip()
    if src.startswith("data:image/"):
        return src
    # base64-only payload fallback
    return f"data:image/png;base64,{src}"


def _insert_image_by_feature(html: str, feature: str, image_data: str) -> str:
    if not html:
        return html

    src = _normalize_image_data_url(image_data)
    if not src:
        return html

    safe_alt = (feature or "Uploaded image").replace('"', "'")
    img_tag = f'<img src="{src}" alt="{safe_alt}" data-agent-image="1" style="max-width:100%;height:auto;display:block;margin:12px auto;border-radius:10px;" />'
    lower = (feature or "").lower()

    # Replace by explicit named image request.
    named = re.search(r"named\s+[\"']?([a-z0-9_-]+)[\"']?", lower)
    if named:
        key = named.group(1)
        rx_named = re.compile(
            rf'<img\b(?=[^>]*(?:alt|id|class)=["\'][^"\']*{re.escape(key)}[^"\']*["\'])[^>]*>',
            flags=re.IGNORECASE,
        )
        m_named = rx_named.search(html)
        if m_named:
            return html[:m_named.start()] + img_tag + html[m_named.end():]

    if "replace" in lower or "swap" in lower:
        first_img = re.search(r"<img\b[^>]*>", html, flags=re.IGNORECASE)
        if first_img:
            return html[:first_img.start()] + img_tag + html[first_img.end():]

    # Try context-aware insertion near user keywords: "in/at/inside ..."
    place_match = re.search(r"(?:in|at|inside|near|under|below)\s+([a-z0-9 _-]{3,40})", lower)
    if place_match:
        phrase = place_match.group(1).strip()
        idx = html.lower().find(phrase)
        if idx != -1:
            open_pos = max(
                html.rfind("<section", 0, idx),
                html.rfind("<div", 0, idx),
                html.rfind("<article", 0, idx),
            )
            if open_pos != -1:
                gt = html.find(">", open_pos)
                if gt != -1:
                    return html[: gt + 1] + "\n" + img_tag + html[gt + 1 :]

    # Keyword-to-zone mapping.
    zones = [
        ("hero", ("<section", "<header", "<main")),
        ("header", ("<header", "<nav")),
        ("footer", ("<footer",)),
        ("menu", ('id="menu', "menu")),
        ("cart", ('id="cart', "cart")),
        ("admin", ('id="admin', "admin")),
    ]
    for key, probes in zones:
        if key in lower:
            probe_idx = -1
            for probe in probes:
                probe_idx = html.lower().find(str(probe).lower())
                if probe_idx != -1:
                    break
            if probe_idx != -1:
                gt = html.find(">", probe_idx)
                if gt != -1:
                    return html[: gt + 1] + "\n" + img_tag + html[gt + 1 :]

    # Safe fallback: add to main content if possible, else body.
    for closing in ("</main>", "</body>", "</html>"):
        pos = html.lower().rfind(closing)
        if pos != -1:
            return html[:pos] + "\n" + img_tag + "\n" + html[pos:]

    return html + "\n" + img_tag


def _classify_modification_mode(instruction: str) -> str:
    text = (instruction or "").lower()
    if any(k in text for k in ["fix", "bug", "error", "broken", "not working"]):
        return "bugfix"
    if any(k in text for k in ["replace", "swap", "change this with", "update this"]):
        return "replace"
    if any(k in text for k in ["refactor", "clean", "optimize", "improve code"]):
        return "refactor"
    if any(k in text for k in ["ui", "design", "style", "responsive", "modern"]):
        return "ui"
    if any(k in text for k in ["auth", "login", "signup", "logout", "profile"]):
        return "auth"
    if any(k in text for k in ["order", "cart", "history", "database", "backend"]):
        return "data"
    return "feature"


def _build_copilot_prompt(mode: str, instruction: str, html: str, css: str, js: str, backend_code: str) -> str:
    return f"""
You are a senior coding copilot modifying an existing generated website.
Apply the request safely, preserve existing working features, and avoid regressions.

MODE: {mode}
REQUEST:
{instruction}

RETURN COMPLETE UPDATED FILES ONLY in this exact format:

HTML_START
(updated html)
HTML_END

CSS_START
(updated css)
CSS_END

JS_START
(updated js)
JS_END

BACKEND_START
(updated backend; if unchanged return original backend exactly)
BACKEND_END

HARD RULES:
- Keep all existing working features unless the request explicitly removes them.
- Keep login/signup/logout flows working if they already exist.
- Keep order/cart and data routing working if they already exist.
- Do not return markdown fences or explanations.
- Do not truncate content.
- Ensure all buttons and interactions referenced in HTML have JS handlers.
- Return valid plain code only.

CURRENT HTML:
{html}

CURRENT CSS:
{css}

CURRENT JS:
{js}

CURRENT BACKEND:
{backend_code}
"""


def _copilot_response_ok(new_html: str, new_css: str, new_js: str) -> bool:
    if not new_html or not new_css or not new_js:
        return False
    low_html = new_html.lower()
    if "<html" not in low_html and "<!doctype" not in low_html:
        return False
    if "```" in new_html or "```" in new_css or "```" in new_js:
        return False
    if len(new_html) < 200 or len(new_js) < 40:
        return False
    return True


def enforced_app_js(project_type: str, features):
    features_set = set(features or [])

    parts = []

    if project_type == "ecommerce":
        parts.append("""
const API_BASE = "http://localhost:5001";

document.addEventListener("DOMContentLoaded", () => {
  if (!IS_PREVIEW) loadProducts();
});

async function loadProducts() {
  try {
    const res = await fetch(`${API_BASE}/api/products`);
    const data = await res.json();
    renderProducts(data);
  } catch {
    renderProducts([]);
  }
}

function renderProducts(items) {
  const list = document.getElementById("product-list");
  if (!list) return;
  list.innerHTML = "";
  items.forEach(p => {
    const card = document.createElement("div");
    card.className = "product-card";
    card.innerHTML = `<h4>${p.name}</h4><p>${p.description || ""}</p><strong>$${p.price}</strong>`;
    list.appendChild(card);
  });
}
""")
    elif project_type == "saas":
        parts.append("""
const API_BASE = "http://localhost:5001";

document.addEventListener("DOMContentLoaded", () => {
  if (!IS_PREVIEW) loadMetrics();
});

async function loadMetrics() {
  try {
    const res = await fetch(`${API_BASE}/api/metrics`);
    const data = await res.json();
    renderMetrics(data);
  } catch {
    renderMetrics({ active_users: 0, projects: 0, mrr: 0 });
  }
}

function renderMetrics(m) {
  const el = document.getElementById("metrics");
  if (!el) return;
  el.innerHTML = `Active Users: ${m.active_users} | Projects: ${m.projects} | MRR: $${m.mrr}`;
}
""")
    elif project_type in NO_BACKEND_TYPES:
        parts.append("""
// Static-type project: no backend calls required.
""")
    else:
        parts.append("""
const API_URL = "http://localhost:5001/api/data";

document.addEventListener("DOMContentLoaded", () => {
  if (!IS_PREVIEW) loadData();
});

async function loadData() {
  try {
    const res = await fetch(API_URL);
    const data = await res.json();
    render(data);
  } catch {
    render([]);
  }
}

async function submitData(e) {
  e.preventDefault();
  if (IS_PREVIEW) return;
  const input = document.getElementById("content");
  if (!input.value) return;
  await fetch(API_URL, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({content: input.value})
  });
  input.value = "";
  loadData();
}

function render(data) {
  const list = document.getElementById("data-list");
  if (!list) return;
  list.innerHTML = "";
  data.forEach(r => {
    const li = document.createElement("li");
    li.textContent = r[1];
    list.appendChild(li);
  });
}
""")

    if "Authentication" in features_set:
        parts.append("""
async function submitAuthForm(form, endpoint) {
  if (!form || IS_PREVIEW) return;
  const emailInput = form.querySelector('input[name="email"], input[name="username"], #email, #username');
  const passInput = form.querySelector('input[name="password"], #password');
  const email = emailInput ? emailInput.value.trim() : "";
  const password = passInput ? passInput.value.trim() : "";
  if (!email || !password) {
    alert("Email and password required");
    return;
  }
  const res = await fetch(`http://localhost:5001${endpoint}`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ email, password })
  });
  const data = await res.json();
  if (!data.success) {
    alert(data.error || "Authentication failed");
    return;
  }
  if (data.token) localStorage.setItem("auth_token", data.token);
  alert("Success");
}

document.addEventListener("submit", e => {
  const form = e.target;
  if (!form) return;
  if (form.matches("#signup-form, [data-auth='signup']")) {
    e.preventDefault();
    submitAuthForm(form, "/api/auth/signup");
  }
  if (form.matches("#login-form, [data-auth='login']")) {
    e.preventDefault();
    submitAuthForm(form, "/api/auth/login");
  }
});
""")

    return inject_preview_guard("\n".join(parts))


def _feature_auth_imports():
    return "from werkzeug.security import generate_password_hash, check_password_hash\nimport uuid\nimport json"


def _feature_auth_routes():
    return """
TOKENS = {}

def _read_auth_payload():
    data = request.get_json(silent=True) or {}
    if not data:
        # fallback for form-encoded submissions
        data = request.form.to_dict() if request.form else {}
    email = (data.get("email") or data.get("username") or "").strip().lower()
    password = (data.get("password") or "").strip()
    full_name = (data.get("full_name") or data.get("fullName") or data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    return email, password, full_name, phone

def _extract_auth_token():
    auth_header = (request.headers.get("Authorization") or "").strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return (request.headers.get("X-Auth-Token") or "").strip()

def _auth_user_payload(row):
    # row order: id, email, full_name, phone, role
    return {
        "id": row[0],
        "email": row[1],
        "full_name": row[2] or "",
        "phone": row[3] or "",
        "role": row[4] or "customer"
    }

def _ensure_user_columns(conn):
    cols = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
    migrations = [
        ("full_name", "TEXT DEFAULT ''"),
        ("phone", "TEXT DEFAULT ''"),
        ("role", "TEXT DEFAULT 'customer'"),
        ("updated_at", "TIMESTAMP")
    ]
    for col_name, col_def in migrations:
        if col_name not in cols:
            conn.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
    conn.commit()

def init_auth_tables(conn):
    conn.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            role TEXT DEFAULT 'customer',
            updated_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    \"\"\")
    _ensure_user_columns(conn)

@app.route("/api/auth/signup", methods=["POST"])
def auth_signup():
    email, password, full_name, phone = _read_auth_payload()
    if not email or not password:
        return jsonify(success=False, error="Email and password required"), 400
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (email, password_hash, full_name, phone, role) VALUES (?, ?, ?, ?, ?)",
            (email, generate_password_hash(password), full_name, phone, "customer")
        )
        conn.commit()
    except Exception:
        conn.close()
        return jsonify(success=False, error="User already exists"), 409
    row = conn.execute(
        "SELECT id, email, full_name, phone, role FROM users WHERE email = ?",
        (email,)
    ).fetchone()
    conn.close()
    token = str(uuid.uuid4())
    TOKENS[token] = row[0]
    return jsonify(success=True, token=token, user=_auth_user_payload(row))

@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    email, password, _, _ = _read_auth_payload()
    if not email or not password:
        return jsonify(success=False, error="Email and password required"), 400
    conn = get_db()
    row = conn.execute(
        "SELECT id, email, password_hash, full_name, phone, role FROM users WHERE email = ?",
        (email,)
    ).fetchone()
    conn.close()
    if not row or not check_password_hash(row[2], password):
        return jsonify(success=False, error="Invalid credentials"), 401
    token = str(uuid.uuid4())
    TOKENS[token] = row[0]
    user = (row[0], row[1], row[3], row[4], row[5])
    return jsonify(success=True, token=token, user=_auth_user_payload(user))

@app.route("/api/auth/me", methods=["GET"])
def auth_me():
    token = _extract_auth_token()
    uid = TOKENS.get(token)
    if not uid:
        return jsonify(success=False, error="Unauthorized"), 401
    conn = get_db()
    row = conn.execute(
        "SELECT id, email, full_name, phone, role FROM users WHERE id = ?",
        (uid,)
    ).fetchone()
    conn.close()
    if not row:
        TOKENS.pop(token, None)
        return jsonify(success=False, error="Unauthorized"), 401
    return jsonify(success=True, user=_auth_user_payload(row))

@app.route("/api/auth/profile", methods=["PUT"])
def auth_update_profile():
    token = _extract_auth_token()
    uid = TOKENS.get(token)
    if not uid:
        return jsonify(success=False, error="Unauthorized"), 401
    data = request.get_json(silent=True) or {}
    full_name = (data.get("full_name") or data.get("fullName") or data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    conn = get_db()
    conn.execute(
        "UPDATE users SET full_name = ?, phone = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (full_name, phone, uid)
    )
    conn.commit()
    row = conn.execute(
        "SELECT id, email, full_name, phone, role FROM users WHERE id = ?",
        (uid,)
    ).fetchone()
    conn.close()
    return jsonify(success=True, user=_auth_user_payload(row))

@app.route("/api/auth/logout", methods=["POST"])
def auth_logout():
    token = _extract_auth_token()
    if token:
        TOKENS.pop(token, None)
    return jsonify(success=True)

@app.route("/api/orders", methods=["POST"])
def create_order():
    token = _extract_auth_token()
    uid = TOKENS.get(token)
    if not uid:
        return jsonify(success=False, error="Unauthorized"), 401
    data = request.get_json(silent=True) or {}
    items = data.get("items") or []
    if not items:
        return jsonify(success=False, error="Order items required"), 400
    total = float(data.get("total") or 0)
    if total <= 0:
        total = sum(float(i.get("price", 0)) * int(i.get("qty", 0)) for i in items)
    conn = get_db()
    conn.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            items_json TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'placed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    \"\"\")
    conn.execute(
        "INSERT INTO orders (user_id, items_json, total, status) VALUES (?, ?, ?, ?)",
        (uid, json.dumps(items), total, "placed")
    )
    order_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    return jsonify(success=True, order_id=order_id)

@app.route("/api/orders/mine", methods=["GET"])
def list_my_orders():
    token = _extract_auth_token()
    uid = TOKENS.get(token)
    if not uid:
        return jsonify(success=False, error="Unauthorized"), 401
    conn = get_db()
    conn.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            items_json TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'placed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    \"\"\")
    rows = conn.execute(
        "SELECT id, items_json, total, status, created_at FROM orders WHERE user_id = ? ORDER BY id DESC",
        (uid,)
    ).fetchall()
    conn.close()
    return jsonify(success=True, orders=[
        {
            "order_id": r[0],
            "items": json.loads(r[1] or "[]"),
            "total_amount": float(r[2]),
            "status": r[3] or "placed",
            "order_date": r[4]
        }
        for r in rows
    ])
"""


def _feature_contact_block():
    return """
def init_contact_tables(conn):
    conn.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    \"\"\")

@app.route("/api/contact", methods=["POST"])
def submit_contact():
    data = request.json or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify(success=False, error="Message required"), 400
    conn = get_db()
    conn.execute(
        "INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)",
        (data.get("name"), data.get("email"), message)
    )
    conn.commit()
    conn.close()
    return jsonify(success=True)
"""


def _feature_upload_imports():
    return "from werkzeug.utils import secure_filename"


def _feature_upload_routes():
    return """
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify(success=False, error="No file provided"), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify(success=False, error="Empty filename"), 400
    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_DIR, filename)
    file.save(path)
    return jsonify(success=True, filename=filename)
"""


def _feature_admin_block():
    return """
@app.route("/api/admin/stats")
def admin_stats():
    return jsonify(success=True, status="ok")
"""


def generate_backend_code(project_type: str, features):
    features_set = set(features or [])
    if project_type in NO_BACKEND_TYPES:
        return ""

    needs_db = (
        "Database" in features_set
        or "Authentication" in features_set
        or "Admin Dashboard" in features_set
        or "Contact Form" in features_set
        or project_type in {"ecommerce", "saas"}
    )

    auth_imports = _feature_auth_imports() if "Authentication" in features_set else ""
    auth_routes = _feature_auth_routes() if "Authentication" in features_set else ""
    auth_init = "    init_auth_tables(conn)\n" if "Authentication" in features_set else ""
    contact_block = _feature_contact_block() if "Contact Form" in features_set else ""
    contact_init = "    init_contact_tables(conn)\n" if "Contact Form" in features_set else ""
    upload_imports = _feature_upload_imports() if "File Upload" in features_set else ""
    upload_routes = _feature_upload_routes() if "File Upload" in features_set else ""
    admin_block = _feature_admin_block() if "Admin Dashboard" in features_set else ""

    if project_type == "ecommerce":
        return f"""\
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
import json
{auth_imports}
{upload_imports}

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            image_url TEXT,
            stock INTEGER DEFAULT 0
        )
    \"\"\")
    conn.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            items_json TEXT NOT NULL,
            total REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    \"\"\")
    conn.commit()
{auth_init}{contact_init}
    seed_products(conn)
    return conn

def seed_products(conn):
    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count:
        return
    seed = [
        ("Linen Shirt", 39.0, "Soft, breathable linen for summer.", "", 20),
        ("Leather Tote", 89.0, "Handcrafted carry-all bag.", "", 12),
        ("Minimal Sneakers", 69.0, "Everyday comfort in neutral tones.", "", 30),
    ]
    conn.executemany(
        "INSERT INTO products (name, price, description, image_url, stock) VALUES (?, ?, ?, ?, ?)",
        seed
    )
    conn.commit()

@app.route("/api/products", methods=["GET"])
def list_products():
    conn = get_db()
    rows = conn.execute("SELECT id, name, price, description, image_url, stock FROM products").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    conn = get_db()
    row = conn.execute(
        "SELECT id, name, price, description, image_url, stock FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify(success=False, error="Product not found"), 404
    return jsonify(dict(row))

@app.route("/api/orders", methods=["POST"])
def create_order():
    data = request.json or {{}}
    items = data.get("items") or []
    if not items:
        return jsonify(success=False, error="Order items required"), 400
    conn = get_db()
    total = 0.0
    for item in items:
        pid = item.get("product_id")
        qty = int(item.get("qty", 1))
        row = conn.execute("SELECT price FROM products WHERE id = ?", (pid,)).fetchone()
        if not row:
            conn.close()
            return jsonify(success=False, error=f"Invalid product {pid}"), 400
        total += float(row[0]) * qty
    payload = json.dumps(items)
    conn.execute("INSERT INTO orders (items_json, total) VALUES (?, ?)", (payload, total))
    order_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    return jsonify(success=True, order_id=order_id, total=total)

@app.route("/api/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    conn = get_db()
    row = conn.execute("SELECT id, items_json, total, created_at FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify(success=False, error="Order not found"), 404
    return jsonify({{"id": row[0], "items": json.loads(row[1]), "total": row[2], "created_at": row[3]}})

{contact_block}
{auth_routes}
{upload_routes}
{admin_block}

@app.route("/api/health")
def health():
    return jsonify(status="ok")

if __name__ == "__main__":
    app.run(port=5001, debug=True)
"""

    if project_type == "saas":
        return f"""\
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
{auth_imports}
{upload_imports}

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    \"\"\")
    conn.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            active_users INTEGER DEFAULT 0,
            mrr REAL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    \"\"\")
    conn.commit()
{auth_init}{contact_init}
    seed_metrics(conn)
    return conn

def seed_metrics(conn):
    count = conn.execute("SELECT COUNT(*) FROM metrics").fetchone()[0]
    if count:
        return
    conn.execute("INSERT INTO metrics (active_users, mrr) VALUES (?, ?)", (120, 4500))
    conn.executemany(
        "INSERT INTO projects (name, status) VALUES (?, ?)",
        [("Onboarding Flow", "active"), ("Billing Revamp", "active"), ("Churn Analysis", "paused")]
    )
    conn.commit()

@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    conn = get_db()
    row = conn.execute("SELECT active_users, mrr FROM metrics ORDER BY updated_at DESC LIMIT 1").fetchone()
    projects = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    conn.close()
    if not row:
        return jsonify(active_users=0, projects=0, mrr=0)
    return jsonify(active_users=row[0], projects=projects, mrr=row[1])

@app.route("/api/projects", methods=["GET"])
def list_projects():
    conn = get_db()
    rows = conn.execute("SELECT id, name, status, created_at FROM projects ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/projects", methods=["POST"])
def create_project():
    data = request.json or {{}}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify(success=False, error="Project name required"), 400
    conn = get_db()
    conn.execute("INSERT INTO projects (name, status) VALUES (?, ?)", (name, data.get("status") or "active"))
    conn.commit()
    conn.close()
    return jsonify(success=True)

{contact_block}
{auth_routes}
{upload_routes}
{admin_block}

@app.route("/api/health")
def health():
    return jsonify(status="ok")

if __name__ == "__main__":
    app.run(port=5001, debug=True)
"""

    if not needs_db:
        return """\
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/api/health")
def health():
    return jsonify(status="ok")

if __name__ == "__main__":
    app.run(port=5001, debug=True)
"""

    return f"""\
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
{auth_imports}
{upload_imports}

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    \"\"\")
    conn.commit()
{auth_init}{contact_init}
    return conn

@app.route("/api/data", methods=["GET"])
def get_data():
    conn = get_db()
    rows = conn.execute("SELECT id, content FROM data").fetchall()
    conn.close()
    return jsonify(rows)

@app.route("/api/data", methods=["POST"])
def add_data():
    content = (request.json or {{}}).get("content")
    if not content:
        return jsonify(success=False, error="Empty content"), 400
    conn = get_db()
    conn.execute("INSERT INTO data (content) VALUES (?)", (content,))
    conn.commit()
    conn.close()
    return jsonify(success=True)

{contact_block}
{auth_routes}
{upload_routes}
{admin_block}

@app.route("/api/health")
def health():
    return jsonify(status="ok")

if __name__ == "__main__":
    app.run(port=5001, debug=True)
"""


def validate_database(db_path: pathlib.Path) -> bool:
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("SELECT 1")
        conn.close()
        return True
    except Exception:
        traceback.print_exc()
        return False


def _backend_contract_ok(backend_code: str, project_type: str, features) -> bool:
    if not backend_code:
        return False
    low = backend_code.lower()
    required_common = ["flask", "@app.route(\"/api/health\")"]
    if any(tok not in low for tok in required_common):
        return False
    if project_type in FULLSTACK_TYPES and "@app.route(\"/api/data\"" not in low and "/api/products" not in low and "/api/metrics" not in low:
        return False
    feature_set = set(features or [])
    if "Authentication" in feature_set and "/api/auth/login" not in low:
        return False
    if "File Upload" in feature_set and "/api/upload" not in low:
        return False
    return True


# ============================================================
# GENERATE PROJECT
# ============================================================
@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.json or {}
    name = data.get("projectName", "Website")
    desc = data.get("description", "")
    project_type = _normalize_project_type(data.get("projectType", ""), desc)
    features = data.get("features", []) or []
    inferred_features = _description_feature_inference(desc)
    for f in inferred_features:
        if f not in features:
            features.append(f)

    # hard contract by type
    if project_type in FRONTEND_ONLY_TYPES:
        features = [f for f in features if f not in BACKEND_FEATURES]
    if project_type in FULLSTACK_TYPES and "Database" not in features:
        features = features + ["Database"]

    # build feature description for prompt
    feat_text = ""
    if project_type:
        feat_text += f"\nTYPE: {project_type}"
    if features:
        feat_text += "\nFEATURES: " + ", ".join(features)
        # add special guidance
        if "Database" in features:
            feat_text += "\n- include a basic database schema in the backend code"
        if "Authentication" in features:
            feat_text += "\n- include login/signup routes and comments on how auth should work"
        if "Static Site" in features:
            feat_text += "\n- this should be a static frontend only, no backend code generated"

    api_guidance = ""
    if project_type == "ecommerce":
        api_guidance = """
- If you include JS, use GET http://localhost:5001/api/products for product lists
- To place orders, POST to http://localhost:5001/api/orders with JSON {items:[{product_id, qty}]}
"""
    elif project_type == "saas":
        api_guidance = """
- If you include JS, use GET http://localhost:5001/api/metrics for KPI tiles
- Use GET/POST http://localhost:5001/api/projects for project lists
"""
    elif project_type in {"fullstack", "custom"} or any(f in features for f in BACKEND_FEATURES):
        api_guidance = """
- If you include JS, use GET/POST http://localhost:5001/api/data for simple data demo
"""
    if "Authentication" in features:
        api_guidance += """
- Include signup and login forms with ids signup-form and login-form (or data-auth="signup"/"login")
- POST JSON {email, password} to http://localhost:5001/api/auth/signup and /api/auth/login
- After login, call GET http://localhost:5001/api/auth/me with Authorization: Bearer <token>
- Include profile update flow using PUT http://localhost:5001/api/auth/profile
"""

    type_contract = ""
    if project_type in FULLSTACK_TYPES:
        type_contract = """
- This is a FULL-STACK project. Include UI states that connect to backend endpoints.
- Include resilient fetch logic (loading/error/success), and never leave dead buttons.
"""
    elif project_type in FRONTEND_ONLY_TYPES:
        type_contract = """
- This is FRONTEND-ONLY. Do not include backend/database dependencies.
- Do not call localhost backend APIs in JS.
"""

    design_blueprint = _build_generation_blueprint(name, desc, project_type, features)
    requirement_contract = "\n".join(f"- MUST include: {item}" for item in _extract_description_requirements(desc, _infer_site_archetype(name, desc, project_type)))
    archetype = _infer_site_archetype(name, desc, project_type)
    section_labels = _derive_section_labels(desc, archetype, project_type, features)
    visual_mood = _extract_visual_mood(desc, archetype)
    recent_layout_constraints = _recent_layout_constraints(limit=12)
    section_contract = "\n".join(f"- section_label: {label}" for label in section_labels)

    prompt = f"""
Generate ONLY valid HTML.

STRICT RULES:
- NO explanations
- Return ONE complete, professional, production-style single-page app in pure HTML
- Produce launch-quality visuals, not a basic demo or classroom layout
- Use <style> and <script>
- JS must not crash if backend unavailable
- Every visible button/link should be mapped to working behavior
- Use semantic layout and responsive design
- Use tasteful stock/placeholder images where needed
- Authentication requests must include working login/signup/logout interactions when requested
- Never dump raw/truncated base64 into normal text fields (name/address/description)
- Use centralized API helpers for data routing with clear loading/success/error UI states
- Do not display the raw user prompt/description verbatim in hero banners, top bars, or visible body copy
- Define a clear design system with CSS variables in :root (colors, spacing, radius, shadows)
- Use layered/interesting backgrounds (gradients, soft glows, subtle textures), avoid flat plain backgrounds
- Include a sticky navigation and at least 6 meaningful sections tailored to the prompt
- Include trust/credibility sections such as testimonials, stats, client logos, FAQ, and contact footer
- Include at least 3 real interactions (filters, tabs, accordions, scroll nav, cart updates, modals, search, etc.)
- Include polished mobile behavior using @media rules and preserve desktop quality
- Avoid generic filler text; write context-aware copy based on the project description
- Prioritize explicit requirements from description over generic template defaults
- Never reuse previous project skeletons (e.g., same nav labels/section order/hero copy) from earlier generations
- For same-domain prompts, create a distinct visual language and section flow each run
- Before generating, internally analyze the description and derive a fresh site architecture from it
- The chosen sections, labels, and visual tone must clearly reflect the specific user prompt, not a generic domain shell
{api_guidance}
{type_contract}

DESIGN BRIEF:
{design_blueprint}

USER INTENT ANALYSIS:
- inferred_visual_mood: {visual_mood}
- inferred_entities: {", ".join(_extract_description_entities(desc)) or "general product sections"}
- section_strategy: use these or close semantic equivalents, but do not collapse into generic repeated labels
{section_contract}

REQUIREMENT CONTRACT:
{requirement_contract}

{recent_layout_constraints}

PROJECT: {name}
DESCRIPTION: {desc}{feat_text}
"""

    # NEW DYNAMIC GENERATION PIPELINE
    # Step 1: Analyze project requirements
    analysis = analyze_project_prompt(name, desc, project_type, features)
    
    # Step 2: Generate UI plan
    ui_plan = generate_ui_plan(analysis)
    
    # Step 3: Generate HTML using modular approach
    html = ""
    for attempt in range(1, 4):  # Try up to 3 attempts for uniqueness
        candidate_html = generate_modular_html(ui_plan, analysis, attempt)
        
        # Apply layout variation
        candidate_html = apply_layout_variation(candidate_html, ui_plan, attempt)
        
        # Check quality and uniqueness
        if (
            _is_generation_quality_ok(candidate_html, features, project_type)
            and not _has_domain_mismatch(candidate_html, archetype)
            and _domain_requirements_ok(candidate_html, archetype, desc, features)
            and not _is_layout_too_similar_to_existing(candidate_html, threshold=0.85)
        ):
            html = candidate_html
            break
    
    # Step 4: Place images intelligently
    if html:
        available_images = DEFAULT_IMAGE_URLS.copy()  # Use default images or add generated ones
        html = place_images_in_html(html, ui_plan, analysis, available_images)
    
    # Fallback to old system if new pipeline fails
    if not html:
        print("New pipeline failed, falling back to Gemini generation.")
        
        # OLD GEMINI-BASED GENERATION (keep as fallback)
        try:
            model = genai.GenerativeModel("models/gemini-2.5-flash")
            for attempt in range(1, 6):
                creative_direction = _generation_creative_direction(name, desc, archetype, attempt)
                uniqueness_retry = ""
                if attempt > 1:
                    uniqueness_retry = f"""

RETRY OVERRIDE {attempt}:
- Previous attempt was too generic or repetitive.
- Generate a clearly different information architecture and section order.
- Do not use nav labels: Home, Details, Saved, Admin as the primary set unless explicitly required.
- Ensure healthcare/job/library/travel domain semantics appear in labels and section names.
- Change the hero composition, card system, and section naming from previous attempts.
- If the previous attempt resembled an earlier generated project, rebuild from a different layout family entirely.
"""
                res = model.generate_content(prompt + "\n\n" + creative_direction + "\n" + uniqueness_retry)
                if not res or not res.text:
                    continue
                candidate = res.text.replace("```html", "").replace("```", "").strip()
                if not candidate or len(candidate) < 50:
                    continue
                if (
                    _is_generation_quality_ok(candidate, features, project_type)
                    and not _has_domain_mismatch(candidate, archetype)
                    and _domain_requirements_ok(candidate, archetype, desc, features)
                    and not _is_layout_too_similar_to_existing(candidate, threshold=0.82)
                ):
                    html = candidate
                    break

            if not html:
                print("Generated HTML failed quality checks after retries. Using professional fallback template.")
                if project_type in FRONTEND_ONLY_TYPES:
                    html = _no_backend_template_html(name, desc, project_type)
                else:
                    html = _professional_fallback_html(name, desc, project_type, features)
                # If fallback still looks too close to recent projects, regenerate fallback variants.
                if _is_layout_too_similar_to_existing(html, threshold=0.86):
                    for _ in range(5):
                        candidate_fb = _professional_fallback_html(name, desc, project_type, features) if project_type not in FRONTEND_ONLY_TYPES else _no_backend_template_html(name, desc, project_type)
                        if not _is_layout_too_similar_to_existing(candidate_fb, threshold=0.86):
                            html = candidate_fb
                            break

        except Exception as e:
            print("Gemini error:", str(e))
            traceback.print_exc()
            if project_type in FRONTEND_ONLY_TYPES:
                html = _no_backend_template_html(name, desc, project_type)
            else:
                html = _professional_fallback_html(name, desc, project_type, features)

        # Final safety: never persist wrong-domain HTML for the detected archetype.
        if _has_domain_mismatch(html, archetype) or not _domain_requirements_ok(html, archetype, desc, features):
            print("Final domain/requirement safety fallback triggered.")
            if project_type in FRONTEND_ONLY_TYPES:
                html = _no_backend_template_html(name, desc, project_type)
            else:
                html = _professional_fallback_html(name, desc, project_type, features)
        # Final anti-duplication safety pass.
        if _is_layout_too_similar_to_existing(html, threshold=0.88):
            for _ in range(5):
                alt = _professional_fallback_html(name, desc, project_type, features) if project_type not in FRONTEND_ONLY_TYPES else _no_backend_template_html(name, desc, project_type)
                if not _is_layout_too_similar_to_existing(alt, threshold=0.88):
                    html = alt
                    break

    css = extract_between(html, "<style>", "</style>") or ""
    raw_js = extract_between(html, "<script>", "</script>") or enforced_app_js(project_type, features)
    js = inject_preview_guard(raw_js)

    safe = "".join(c for c in name if c.isalnum() or c in "-_")
    pdir = GENERATED_ROOT / safe
    frontend = pdir / "frontend"
    backend = pdir / "backend"
    frontend.mkdir(parents=True, exist_ok=True)
    backend.mkdir(parents=True, exist_ok=True)

    backend_code = ""
    # decide if backend should exist at all
    needs_backend = (
        project_type in FULLSTACK_TYPES
        or project_type == "custom"
        or any(f in features for f in BACKEND_FEATURES)
    )
    if project_type in NO_BACKEND_TYPES:
        needs_backend = False
    if project_type in {"landing", "apibased", "portfolio", "static", "blog"} and not any(f in features for f in BACKEND_FEATURES):
        needs_backend = False

    if needs_backend:
        needs_db = (
            "Database" in features
            or "Authentication" in features
            or "Admin Dashboard" in features
            or "Contact Form" in features
            or project_type in {"ecommerce", "saas"}
        )
        if needs_db:
            db_path = backend / "database.db"
            conn = sqlite3.connect(db_path)
            conn.close()
            if not validate_database(db_path):
                return jsonify(success=False, error="Database validation failed"), 500

        backend_code = generate_backend_code(project_type, features)
        if not _backend_contract_ok(backend_code, project_type, features):
            print("Generated backend failed contract checks. Falling back to deterministic backend template.")
            backend_code = generate_backend_code("fullstack" if project_type in FULLSTACK_TYPES else project_type, features)
    else:
        # no backend required for this configuration
        backend_code = ""


    (frontend / "index.html").write_text(html, encoding="utf-8")
    (frontend / "style.css").write_text(css, encoding="utf-8")
    (frontend / "app.js").write_text(js, encoding="utf-8")
    if backend_code is not None:
        (backend / "app.py").write_text(backend_code, encoding="utf-8")

    resp = {"html": html, "css": css, "js": js}
    if backend_code:
        resp["backend"] = backend_code
    return jsonify(success=True, code=resp)


# ============================================================
# PUSH TO GITHUB
# ============================================================
@app.route("/api/push-github", methods=["POST"])
def push_github():
    data = request.json or {}
    project = data.get("projectName")
    username = data.get("githubUsername")
    repo = data.get("repoName")
    token = data.get("token")
    if not project or not username or not repo or not token:
        return jsonify(success=False, error="Missing parameters"), 400

    safe = "".join(c for c in project if c.isalnum() or c in "-_")
    pdir = GENERATED_ROOT / safe
    if not pdir.exists():
        return jsonify(success=False, error="Project not found"), 404

    try:
        push_result = push_to_github(str(pdir), username, repo, token)
    except GitPushError as e:
        return jsonify(success=False, error=f"Git push failed: {str(e)}"), 500
    except Exception as e:
        return jsonify(success=False, error=f"Unexpected error: {str(e)}"), 500

    repo_name_sanitized = (push_result or {}).get("repo_name") or repo.strip().replace(" ", "-")
    branch = (push_result or {}).get("branch") or "main"
    return jsonify(
        success=True,
        repoNameSanitized=repo_name_sanitized,
        branch=branch
    )


# ============================================================
# PROJECT STORAGE / RETRIEVAL
@app.route("/api/projects", methods=["GET"])
def list_projects():
    # return names of directories under GENERATED_ROOT
    try:
        names = [p.name for p in GENERATED_ROOT.iterdir() if p.is_dir()]
        return jsonify(success=True, projects=names)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@app.route("/api/projects/<project_name>", methods=["GET"])
def load_project(project_name):
    safe = "".join(c for c in project_name if c.isalnum() or c in "-_")
    pdir = GENERATED_ROOT / safe / "frontend"
    if not pdir.exists():
        return jsonify(success=False, error="Project not found"), 404
    html = (pdir / "index.html").read_text(encoding="utf-8")
    css = (pdir / "style.css").read_text(encoding="utf-8")
    js = (pdir / "app.js").read_text(encoding="utf-8")
    backend_code = ""
    backend_file = GENERATED_ROOT / safe / "backend" / "app.py"
    if backend_file.exists():
        backend_code = backend_file.read_text(encoding="utf-8")
    return jsonify(success=True, code={"html": html, "css": css, "js": js, "backend": backend_code})


# ============================================================
# RENDER DEPLOYMENT (ONEâ€‘CLICK)
def _get_latest_deploy(service_id, headers):
    resp = requests.get(f"https://api.render.com/v1/services/{service_id}/deploys", headers=headers)
    if not resp.ok:
        return None
    data = resp.json() or []
    # deploys are typically returned most recent first
    if isinstance(data, list) and len(data) > 0:
        return data[0]
    return None


def _make_github_headers(provided_token=None):
    # Prefer explicit request token, fallback to environment values.
    token = (provided_token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "NovaForge/1.0"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers, token


def _get_first_owner_id(headers):
    """
    Render API requires an ownerId (workspace) when creating services.
    We fetch the first accessible workspace and use its ID.
    """
    try:
        owners_resp = requests.get("https://api.render.com/v1/owners", headers=headers, timeout=10)
        if not owners_resp.ok:
            return None, f"Failed to fetch owners: {owners_resp.text}"
        owners = owners_resp.json()
        if not owners:
            return None, "No owners found"
        first = owners[0]
        if "owner" in first:
            owner_id = first["owner"].get("id")
        else:
            owner_id = first.get("id")
        if not owner_id:
            return None, "Owner ID extraction failed"
        return owner_id, None
    except requests.Timeout:
        return None, "Render API timeout. Please try again in a moment."
    except Exception as e:
        return None, f"Error communicating with Render API: {str(e)}"


def _is_billing_or_plan_error(status_code, error_text):
    text = (error_text or "").lower()
    billing_markers = (
        "billing",
        "payment",
        "credit card",
        "plan",
        "upgrade",
        "insufficient balance",
        "subscription",
        "not allowed on free",
    )
    if any(marker in text for marker in billing_markers):
        return True
    return status_code in (402, 403)


class RenderRateLimitError(Exception):
    def __init__(self, retry_after=None):
        self.retry_after = retry_after
        super().__init__("Render API rate limit exceeded")


def _extract_services_list(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("services", "items", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []


def _find_existing_service_by_name(headers, service_name):
    cursor = None
    for _ in range(10):
        params = {"limit": 100}
        if cursor:
            params["cursor"] = cursor
        resp = requests.get(
            "https://api.render.com/v1/services",
            headers=headers,
            params=params,
            timeout=10
        )
        if resp.status_code == 429:
            raise RenderRateLimitError(resp.headers.get("Retry-After"))
        if not resp.ok:
            return None
        body = resp.json() or {}
        services = _extract_services_list(body)
        hit = next((s for s in services if isinstance(s, dict) and s.get("name") == service_name), None)
        if hit:
            return hit
        if isinstance(body, dict):
            cursor = body.get("nextCursor") or body.get("cursor")
        else:
            cursor = None
        if not cursor:
            break
    return None


def _infer_static_deploy_settings(repo, branch, github_headers):
    """
    Infer static rootDir/publishPath from common repo layouts.
    """
    candidates = [
        ("frontend/index.html", "frontend", "."),
        ("public/index.html", "", "public"),
        ("dist/index.html", "", "dist"),
        ("index.html", "", "."),
    ]
    for probe_path, root_dir, publish_path in candidates:
        try:
            resp = requests.get(
                f"https://api.github.com/repos/{repo}/contents/{probe_path}?ref={branch}",
                headers=github_headers,
                timeout=10
            )
            if resp.status_code == 200:
                return {
                    "root_dir": root_dir,
                    "publish_path": publish_path,
                    "build_command": "echo build complete",
                }
        except Exception:
            pass

    # NovaForge projects commonly publish from frontend/
    return {
        "root_dir": "frontend",
        "publish_path": ".",
        "build_command": "echo build complete",
    }


def _patch_static_service_config(service_id, headers, root_dir, publish_path, build_command):
    """
    Best-effort patch to ensure static service settings are correctly applied.
    """
    patch_variants = [
        {
            "rootDir": root_dir,
            "serviceDetails": {
                "buildCommand": build_command,
                "publishPath": publish_path,
            }
        },
        {
            "rootDir": root_dir,
            "buildCommand": build_command,
            "publishPath": publish_path,
        },
        {
            "serviceDetails": {
                "buildCommand": build_command,
                "publishPath": publish_path,
            }
        },
    ]

    last_resp = None
    for idx, payload in enumerate(patch_variants, start=1):
        resp = requests.patch(
            f"https://api.render.com/v1/services/{service_id}",
            headers=headers,
            json=payload,
            timeout=30
        )
        last_resp = resp
        print("=== STATIC PATCH DEBUG ===")
        print("Patch Variant:", idx)
        print("Patch Payload:", payload)
        print("Render Status:", resp.status_code)
        print("Render Response:", resp.text)
        print("==========================")
        if resp.ok:
            try:
                return resp.json(), None
            except Exception:
                return None, None

    return None, (last_resp.text if last_resp is not None else "Unknown patch error")


def _build_render_service_payload_variants(
    service_type,
    service_name,
    owner_id,
    repo_url,
    branch,
    repo_slug=None,
    start_command=None,
    static_root_dir="frontend",
    static_publish_path=".",
    static_build_command="echo build complete"
):
    if service_type == "web_service":
        return [
            {
                "type": "web_service",
                "name": service_name,
                "ownerId": owner_id,
                "repo": repo_url,
                "branch": branch,
                "autoDeploy": True,
                "serviceDetails": {
                    "runtime": "python",
                    "envSpecificDetails": {
                        "buildCommand": "pip install -r requirements.txt || pip install flask",
                        "startCommand": start_command or "python backend/app.py"
                    }
                }
            },
            {
                "service": {
                    "name": service_name,
                    "repo": repo_url,
                    "branch": branch,
                    "type": "web_service",
                    "autoDeploy": True,
                    "buildCommand": "pip install -r requirements.txt || pip install flask",
                    "startCommand": start_command or "python backend/app.py",
                    "envVars": []
                }
            }
        ]

    repo_values = [repo_url]

    variants = []
    for repo_value in repo_values:
        # Render static_site endpoint can be finicky across accounts/API versions.
        # Keep multiple payload shapes for best compatibility.
        variants.append({
            "type": "static_site",
            "name": service_name,
            "ownerId": owner_id,
            "repo": repo_value,
            "branch": branch,
            "autoDeploy": "yes",
            "rootDir": static_root_dir,
            "serviceDetails": {
                "buildCommand": static_build_command,
                "publishPath": static_publish_path
            }
        })
        variants.append({
            "type": "static_site",
            "name": service_name,
            "ownerId": owner_id,
            "repo": repo_value,
            "branch": branch,
            "autoDeploy": "yes",
            "serviceDetails": {
                "buildCommand": static_build_command,
                "publishPath": static_publish_path
            }
        })
        variants.append({
            "type": "static_site",
            "name": service_name,
            "ownerId": owner_id,
            "repo": repo_value,
            "branch": branch,
            "autoDeploy": "yes",
            "rootDir": static_root_dir,
            "buildCommand": static_build_command,
            "publishPath": static_publish_path
        })
        variants.append({
            "type": "static_site",
            "name": service_name,
            "ownerId": owner_id,
            "repo": repo_value,
            "branch": branch,
            "autoDeploy": True,
            "rootDir": static_root_dir,
            "serviceDetails": {
                "buildCommand": static_build_command,
                "publishPath": static_publish_path
            }
        })
        variants.append({
            "type": "static_site",
            "name": service_name,
            "ownerId": owner_id,
            "repo": repo_value,
            "branch": branch,
            "autoDeploy": True,
            "rootDir": static_root_dir,
            "buildCommand": static_build_command,
            "publishPath": static_publish_path
        })
    return variants


@app.route("/api/deploy", methods=["POST"])
def render_deploy():
    """
    Deploy a GitHub repo to Render as a static site.
    - Validates GitHub repo exists and contains required files
    - Reuses existing service if available
    - Returns deployment tracking info
    """
    data = request.json or {}
    raw_repo = (data.get("repo") or "").strip()
    branch = data.get("branch") or "main"
    api_key = data.get("api_key") or os.environ.get("RENDER_API_KEY")
    provided_github_token = data.get("github_token")
    github_headers, github_token = _make_github_headers(provided_github_token)

    print(f"=== DEPLOY REQUEST === repo={raw_repo!r} branch={branch!r} using_github_token={bool(github_token)}")
    if not github_token:
        print("âš ï¸ No GitHub token configured; unauthenticated API calls are rate-limited.")

    # Force static-only deployment for now (free-tier friendly).
    deploy_mode = "static"

    # URL or owner/repo formats accepted
    def normalize_repo(repo_value):
        if not repo_value:
            return None
        value = repo_value.strip()
        if value.endswith(".git"):
            value = value[:-4]
        if value.startswith("https://github.com/"):
            value = value[len("https://github.com/"):]
        elif value.startswith("http://github.com/"):
            value = value[len("http://github.com/"):]
        elif value.startswith("git@github.com:"):
            value = value[len("git@github.com:"):]
        value = value.strip("/ ")
        if "/" in value:
            owner, repo_part = value.split("/", 1)
            repo_part = re.sub(r"\s+", "-", repo_part.strip())
            value = f"{owner.strip()}/{repo_part}"
        return value

    repo = normalize_repo(raw_repo)

    # Validation
    if not repo or "/" not in repo:
        return jsonify(success=False, error="Invalid repo format. Use 'username/repo'"), 400
    if not api_key:
        return jsonify(success=False, error="Render API key required"), 401

    service_name = repo.replace("/", "-")
    repo_url = f"https://github.com/{repo}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Step 0: Resolve workspace (owner) ID required by Render API
    owner_id, owner_err = _get_first_owner_id(headers)
    if not owner_id:
        return jsonify(success=False, error="Failed to resolve Render workspace", details=owner_err), 500

    # Step 1: Verify GitHub repo exists and branch is accessible
    try:
        repo_info = requests.get(
            f"https://api.github.com/repos/{repo}",
            headers=github_headers,
            timeout=10
        )
        print(f"GitHub repo check: status={repo_info.status_code} repo={repo}")
        if repo_info.status_code == 403 and "rate limit exceeded" in (repo_info.text or "").lower():
            reset_at = repo_info.headers.get("X-RateLimit-Reset")
            details = "GitHub API rate limit exceeded. Add GITHUB_TOKEN in backend/.env for authenticated requests."
            if reset_at:
                details += f" Rate limit reset epoch: {reset_at}."
            return jsonify(success=False, error="GitHub API rate limit exceeded", details=details), 429
        if repo_info.status_code == 401:
            return jsonify(
                success=False,
                error="GitHub authentication failed",
                details="Invalid or expired GitHub token. Check GITHUB_TOKEN and retry."
            ), 401
        if repo_info.status_code != 200:
            print(f"GitHub repo check body: {repo_info.text[:500]}")
            details = f"GitHub repo check failed ({repo_info.status_code}) for {repo}: {repo_info.text[:300]}"
            if not github_token and repo_info.status_code == 403:
                details += " (No token configured; this is likely rate limit.)"
            return jsonify(
                success=False,
                error="Invalid repo or branch",
                details=details
            ), 400

        repo_json = repo_info.json() or {}
        default_branch = repo_json.get("default_branch", "main")

        if not branch:
            branch = default_branch

        branch_check = requests.get(
            f"https://api.github.com/repos/{repo}/branches/{branch}",
            headers=github_headers,
            timeout=10
        )
        print(f"GitHub branch check: status={branch_check.status_code} repo={repo} branch={branch}")
        if branch_check.status_code == 403 and "rate limit exceeded" in (branch_check.text or "").lower():
            reset_at = branch_check.headers.get("X-RateLimit-Reset")
            details = "GitHub API rate limit exceeded. Add GITHUB_TOKEN in backend/.env for authenticated requests."
            if reset_at:
                details += f" Rate limit reset epoch: {reset_at}."
            return jsonify(success=False, error="GitHub API rate limit exceeded", details=details), 429
        if branch_check.status_code == 401:
            return jsonify(
                success=False,
                error="GitHub authentication failed",
                details="Invalid or expired GitHub token. Check GITHUB_TOKEN and retry."
            ), 401

        if branch_check.status_code == 404:
            for fallback in (default_branch, "main", "master"):
                if fallback == branch:
                    continue
                fallback_resp = requests.get(
                    f"https://api.github.com/repos/{repo}/branches/{fallback}",
                    headers=github_headers,
                    timeout=10
                )
                if fallback_resp.status_code == 200:
                    branch = fallback
                    branch_check = fallback_resp
                    break

        if branch_check.status_code != 200:
            print(f"GitHub branch check body: {branch_check.text[:500]}")
            return jsonify(
                success=False,
                error="Invalid repo or branch",
                details=f"GitHub branch check failed ({branch_check.status_code}) for {repo}@{branch}: {branch_check.text[:300]}"
            ), 400

    except Exception as e:
        return jsonify(success=False, error=f"Cannot access GitHub repo: {str(e)}"), 400

    # Step 1b: Detect service type based on repo contents
    detected_web_service = False
    render_yaml_exists = False
    start_command = None
    try:
        backend_app = requests.get(
            f"https://api.github.com/repos/{repo}/contents/backend/app.py?ref={branch}",
            headers=github_headers,
            timeout=10
        )
        root_app = requests.get(
            f"https://api.github.com/repos/{repo}/contents/app.py?ref={branch}",
            headers=github_headers,
            timeout=10
        )
        render_yaml = requests.get(
            f"https://api.github.com/repos/{repo}/contents/render.yaml?ref={branch}",
            headers=github_headers,
            timeout=10
        )
        if backend_app.status_code == 200:
            detected_web_service = True
            start_command = "python backend/app.py"
        elif root_app.status_code == 200:
            detected_web_service = True
            start_command = "python app.py"
        render_yaml_exists = render_yaml.status_code == 200
    except Exception:
        pass

    static_settings = _infer_static_deploy_settings(repo, branch, github_headers)
    static_root_dir = static_settings.get("root_dir", "frontend")
    static_publish_path = static_settings.get("publish_path", ".")
    static_build_command = static_settings.get("build_command", "echo build complete")
    print(
        f"Static deploy settings: rootDir={static_root_dir!r} "
        f"publishPath={static_publish_path!r} buildCommand={static_build_command!r}"
    )

    # Step 2: Check if service already exists
    try:
        existing_service = _find_existing_service_by_name(headers, service_name)
            
        if existing_service:
            # Service exists - ensure static settings, then trigger a new deploy
            try:
                if deploy_mode == "static":
                    _patch_static_service_config(
                        service_id=existing_service["id"],
                        headers=headers,
                        root_dir=static_root_dir,
                        publish_path=static_publish_path,
                        build_command=static_build_command
                    )
                deploy_resp = requests.post(
                    f"https://api.render.com/v1/services/{existing_service['id']}/deploys",
                    headers=headers,
                    timeout=10
                )
                if deploy_resp.ok:
                    deploy_data = deploy_resp.json()
                    existing_url = (
                        existing_service.get("url")
                        or existing_service.get("defaultDomain")
                        or existing_service.get("serviceUrl")
                        or ((existing_service.get("serviceDetails") or {}).get("url") if isinstance(existing_service.get("serviceDetails"), dict) else None)
                    )
                    return jsonify(
                        success=True,
                        service_id=existing_service.get("id"),
                        service_name=existing_service.get("name"),
                        service_url=existing_url,
                        deploy_id=deploy_data.get("id"),
                        deploy_status=deploy_data.get("status"),
                        message="Redeployed existing service"
                    )
                else:
                    return jsonify(
                        success=False,
                        error="Failed to trigger deploy on existing service",
                        details=deploy_resp.text
                    ), 500
            except Exception as e:
                return jsonify(success=False, error=f"Deploy trigger failed: {str(e)}"), 500
    except RenderRateLimitError as e:
        retry_after = e.retry_after or "30"
        return jsonify(
            success=False,
            error="Render API rate limit exceeded",
            details=f"Please retry after about {retry_after} seconds."
        ), 429
    except requests.Timeout:
        return jsonify(success=False, error="Render API timeout"), 504
    except Exception as e:
        return jsonify(success=False, error=f"Service check failed: {str(e)}"), 500

    # Step 3: Optional Render Blueprint deploy (only when render.yaml exists)
    create_resp = None
    if render_yaml_exists:
        blueprint_payload = {
            "repo": repo_url,
            "branch": branch
        }
        try:
            create_resp = requests.post(
                "https://api.render.com/v1/blueprints/deploys",
                headers=headers,
                json=blueprint_payload,
                timeout=30
            )
            print("=== DEPLOY DEBUG ===")
            print("Blueprint Payload:", blueprint_payload)
            print("Render Status:", create_resp.status_code)
            print("Render Response:", create_resp.text)
            print("====================")
            # Explicitly skip blueprint fallback for unsupported endpoint.
            if create_resp.status_code == 405:
                create_resp = None
        except Exception:
            create_resp = None

    try:
        chosen_type = None
        if create_resp is None:
            if deploy_mode == "static":
                desired_types = ["static_site"]
            elif deploy_mode == "web":
                desired_types = ["web_service"]
            else:
                # Auto mode is intentionally static-only for now.
                # Web service should be opt-in via deploy_mode="web".
                desired_types = ["static_site"]

            create_errors = []
            for service_type in desired_types:
                payload_variants = _build_render_service_payload_variants(
                    service_type=service_type,
                    service_name=service_name,
                    owner_id=owner_id,
                    repo_url=repo_url,
                    branch=branch,
                    repo_slug=repo,
                    start_command=start_command,
                    static_root_dir=static_root_dir,
                    static_publish_path=static_publish_path,
                    static_build_command=static_build_command,
                )
                last_variant_resp = None
                for variant_index, payload in enumerate(payload_variants, start=1):
                    candidate_resp = requests.post(
                        "https://api.render.com/v1/services",
                        headers=headers,
                        json=payload,
                        timeout=30
                    )
                    last_variant_resp = candidate_resp
                    print("=== DEPLOY FALLBACK DEBUG ===")
                    print("Service Type:", service_type)
                    print("Payload Variant:", variant_index)
                    print("Service Payload:", payload)
                    print("Render Status:", candidate_resp.status_code)
                    print("Render Response:", candidate_resp.text)
                    print("====================")

                    if candidate_resp.ok:
                        create_resp = candidate_resp
                        chosen_type = service_type
                        break
                    if candidate_resp.status_code == 429:
                        retry_after = candidate_resp.headers.get("Retry-After") or "30"
                        return jsonify(
                            success=False,
                            error="Render API rate limit exceeded",
                            details=f"Please retry after about {retry_after} seconds."
                        ), 429

                if create_resp is not None:
                    break

                error_status = last_variant_resp.status_code if last_variant_resp is not None else 500
                error_details = last_variant_resp.text if last_variant_resp is not None else "Unknown Render error"
                create_errors.append({
                    "type": service_type,
                    "status": error_status,
                    "details": error_details
                })
                can_try_next_mode = (
                    deploy_mode == "auto"
                    and service_type != desired_types[-1]
                )
                if can_try_next_mode:
                    continue

                return jsonify(
                    success=False,
                    error="Render API error",
                    details=error_details,
                    attempted_service_type=service_type
                ), error_status

            if create_resp is None:
                existing_service = _find_existing_service_by_name(headers, service_name)
                if existing_service:
                    try:
                        if deploy_mode == "static":
                            _patch_static_service_config(
                                service_id=existing_service["id"],
                                headers=headers,
                                root_dir=static_root_dir,
                                publish_path=static_publish_path,
                                build_command=static_build_command
                            )
                        deploy_resp = requests.post(
                            f"https://api.render.com/v1/services/{existing_service['id']}/deploys",
                            headers=headers,
                            timeout=10
                        )
                        if deploy_resp.ok:
                            deploy_data = deploy_resp.json() or {}
                            existing_url = (
                                existing_service.get("url")
                                or existing_service.get("defaultDomain")
                                or existing_service.get("serviceUrl")
                                or ((existing_service.get("serviceDetails") or {}).get("url") if isinstance(existing_service.get("serviceDetails"), dict) else None)
                            )
                            return jsonify(
                                success=True,
                                service_id=existing_service.get("id"),
                                service_name=existing_service.get("name"),
                                service_url=existing_url,
                                deploy_id=deploy_data.get("id"),
                                deploy_status=deploy_data.get("status"),
                                message="Recovered existing service and redeployed"
                            )
                    except Exception:
                        pass
                return jsonify(
                    success=False,
                    error="Render API error",
                    details="No deploy mode succeeded",
                    attempts=create_errors
                ), 500

        if not create_resp.ok:
            return jsonify(
                success=False,
                error="Render API error",
                details=create_resp.text
            ), create_resp.status_code

        create_resp.raise_for_status()
        service_payload = create_resp.json()
        service = None
        deploy = None
        if isinstance(service_payload, dict):
            if isinstance(service_payload.get("service"), dict):
                service = service_payload.get("service")
            if isinstance(service_payload.get("deploy"), dict):
                deploy = service_payload.get("deploy")
            if deploy is None and service_payload.get("deployId"):
                deploy = {"id": service_payload.get("deployId")}
            if deploy is None and all(k in service_payload for k in ("id", "status")):
                deploy = service_payload
        elif isinstance(service_payload, list) and service_payload:
            if isinstance(service_payload[0], dict):
                service = service_payload[0]

        service_id = None
        if isinstance(service, dict):
            service_id = service.get("id") or service.get("serviceId")
        if service_id is None and isinstance(deploy, dict):
            service_id = deploy.get("serviceId")

        resolved_service_type = (
            service.get("type")
            if isinstance(service, dict)
            else None
        ) or chosen_type

        # Render sometimes creates static services with default publishPath/public.
        # Force intended static settings and trigger a fresh deploy.
        if service_id and resolved_service_type == "static_site":
            _patch_static_service_config(
                service_id=service_id,
                headers=headers,
                root_dir=static_root_dir,
                publish_path=static_publish_path,
                build_command=static_build_command
            )
            try:
                redeploy_resp = requests.post(
                    f"https://api.render.com/v1/services/{service_id}/deploys",
                    headers=headers,
                    timeout=15
                )
                if redeploy_resp.ok:
                    redeploy_data = redeploy_resp.json() or {}
                    if isinstance(redeploy_data, dict) and redeploy_data.get("id"):
                        deploy = redeploy_data
            except Exception:
                pass
        
        # Get latest deploy
        deploy_data = deploy
        if service_id:
            deploy_resp = requests.get(
                f"https://api.render.com/v1/services/{service_id}/deploys",
                headers=headers,
                timeout=10
            )
            if deploy_resp.ok:
                deploys = deploy_resp.json() or []
                if isinstance(deploys, list) and deploys:
                    deploy_data = deploys[0]
        
        return jsonify(
            success=True,
            service_id=service_id,
            service_name=service.get("name") if isinstance(service, dict) else None,
            service_url=(
                service.get("url")
                or service.get("defaultDomain")
                or service.get("serviceUrl")
                or ((service.get("serviceDetails") or {}).get("url") if isinstance(service.get("serviceDetails"), dict) else None)
            ) if isinstance(service, dict) else None,
            deploy_id=deploy_data.get("id") if isinstance(deploy_data, dict) else None,
            deploy_status=deploy_data.get("status") if isinstance(deploy_data, dict) else "pending",
            deploy_mode=deploy_mode
        )
        
    except requests.HTTPError as e:
        error_text = e.response.text if e.response else str(e)
        if "already exists" in error_text.lower():
            return jsonify(
                success=False,
                error="Service name already exists",
                details="Try renaming your repository"
            ), 409
        return jsonify(success=False, error="Render API error", details=error_text), 500
    except requests.Timeout:
        return jsonify(success=False, error="Render API timeout during service creation"), 504
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@app.route("/api/deploy-status", methods=["GET"])
def render_deploy_status():
    service_id = request.args.get("service_id")
    deploy_id = request.args.get("deploy_id")
    api_key = request.args.get("api_key") or os.environ.get("RENDER_API_KEY")

    if not service_id or not deploy_id:
        return jsonify(success=False, error="Missing service_id or deploy_id"), 400
    if not api_key:
        return jsonify(success=False, error="Render API key not configured"), 500

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    resp = requests.get(f"https://api.render.com/v1/services/{service_id}/deploys/{deploy_id}", headers=headers)
    if not resp.ok:
        return jsonify(success=False, error="Failed to query deploy status", details=resp.text), 500

    data = resp.json()
    return jsonify(success=True, deploy=data)


@app.errorhandler(Exception)
def handle_unexpected_error(e):
    """Ensure all errors return JSON so the frontend can parse the response."""
    try:
        # Werkzeug HTTPExceptions have a code and description
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            return jsonify(success=False, error=str(e)), e.code
    except Exception:
        pass

    return jsonify(success=False, error=str(e)), 500


# ============================================================
# ADD FEATURE (ATOMIC + SAFE)
# ============================================================
def _run_copilot_modify(project: str, instruction: str, mode: str = "auto"):
    safe = "".join(c for c in project if c.isalnum() or c in "-_")
    pdir = GENERATED_ROOT / safe
    frontend = pdir / "frontend"
    backend = pdir / "backend"

    if not frontend.exists():
        return {"success": False, "error": "Project not found"}, 404

    html = (frontend / "index.html").read_text(encoding="utf-8")
    css = (frontend / "style.css").read_text(encoding="utf-8")
    js = (frontend / "app.js").read_text(encoding="utf-8")
    backend_file = backend / "app.py"
    backend_code = backend_file.read_text(encoding="utf-8") if backend_file.exists() else ""

    effective_mode = mode if mode and mode != "auto" else _classify_modification_mode(instruction)
    prompt = _build_copilot_prompt(effective_mode, instruction, html, css, js, backend_code)

    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        res = model.generate_content(prompt)
        if not res or not res.text:
            return {"success": False, "error": "Model returned empty response"}, 500
        text = res.text
    except Exception as e:
        return {"success": False, "error": f"Gemini failed: {str(e)}"}, 500

    new_html = extract_between(text, "HTML_START", "HTML_END")
    new_css = extract_between(text, "CSS_START", "CSS_END")
    new_js = extract_between(text, "JS_START", "JS_END")
    new_backend = extract_between(text, "BACKEND_START", "BACKEND_END")

    if not _copilot_response_ok(new_html, new_css, new_js):
        return {"success": False, "error": "Copilot returned incomplete/invalid update"}, 500
    if new_backend is None:
        new_backend = backend_code

    new_js = inject_preview_guard(new_js)

    try:
        (frontend / "index.html").write_text(new_html, encoding="utf-8")
        (frontend / "style.css").write_text(new_css, encoding="utf-8")
        (frontend / "app.js").write_text(new_js, encoding="utf-8")
        if new_backend is not None:
            (backend / "app.py").write_text(new_backend, encoding="utf-8")
    except Exception as e:
        return {"success": False, "error": f"Write failed: {str(e)}"}, 500

    return {
        "success": True,
        "mode": effective_mode,
        "assistantMessage": f"Applied {effective_mode} update successfully.",
        "code": {
            "html": new_html,
            "css": new_css,
            "js": new_js,
            "backend": new_backend
        }
    }, 200


@app.route("/api/copilot-modify", methods=["POST"])
def copilot_modify():
    data = request.json or {}
    project = data.get("projectName")
    instruction = data.get("instruction") or data.get("featureDescription")
    mode = data.get("mode", "auto")
    if not project or not instruction:
        return jsonify(success=False, error="Invalid request"), 400
    payload, status = _run_copilot_modify(project, instruction, mode)
    return jsonify(payload), status


@app.route("/api/add-feature", methods=["POST"])
def add_feature():
    data = request.json or {}
    project = data.get("projectName")
    feature = data.get("featureDescription")

    if not project or not feature:
        return jsonify(success=False, error="Invalid request"), 400

    payload, status = _run_copilot_modify(project, feature, "auto")
    return jsonify(payload), status


@app.route("/api/add-feature-with-image", methods=["POST"])
def add_feature_with_image():
    data = request.json or {}
    project = data.get("projectName")
    feature = data.get("featureDescription")
    image_data = data.get("imageData")

    if not project or not feature:
        return jsonify(success=False, error="Invalid request"), 400

    # Log for debugging
    print(f"Processing image feature for project: {project}")
    print(f"Feature description: {feature}")
    print(f"Image data length: {len(image_data) if image_data else 0}")

    safe = "".join(c for c in project if c.isalnum() or c in "-_")
    pdir = GENERATED_ROOT / safe
    frontend = pdir / "frontend"
    backend = pdir / "backend"

    if not frontend.exists():
        return jsonify(success=False, error="Project not found"), 404

    html = (frontend / "index.html").read_text(encoding="utf-8")
    css = (frontend / "style.css").read_text(encoding="utf-8")
    js = (frontend / "app.js").read_text(encoding="utf-8")
    backend_file = backend / "app.py"
    backend_code = backend_file.read_text(encoding="utf-8") if backend_file.exists() else ""

    # Deterministic image placement: preserves existing structure and avoids model corruption.
    new_html = _insert_image_by_feature(html, feature, image_data)
    new_css = css
    new_js = js
    new_backend = backend_code

    try:
        (frontend / "index.html").write_text(new_html, encoding="utf-8")
        (frontend / "style.css").write_text(new_css, encoding="utf-8")
        (frontend / "app.js").write_text(new_js, encoding="utf-8")
        if new_backend is not None:
            (backend / "app.py").write_text(new_backend, encoding="utf-8")
        print("Files updated successfully")
    except Exception as e:
        print(f"Write failed: {str(e)}")
        return jsonify(success=False, error=f"Write failed: {str(e)}"), 500

    return jsonify(success=True, code={
        "html": new_html,
        "css": new_css,
        "js": new_js,
        "backend": new_backend
    })


# ============================================================
# HEALTH
# ============================================================
@app.route("/api/health")
def novaforge_health():
    return jsonify(status="ok", engine="NovaForge", build=NOVAFORGE_BUILD)


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    print("ðŸš€ NovaForge running at http://localhost:5000")
    app.run(port=5000, debug=True)
