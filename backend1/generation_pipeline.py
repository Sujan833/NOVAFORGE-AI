# ============================================================
# NOVAFORGE DYNAMIC GENERATION PIPELINE
# Intent-driven, non-repetitive UI generation system
# ============================================================

import json
import random
import hashlib
import re
from urllib.parse import quote_plus
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass, asdict


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ProjectAnalysis:
    """Structured analysis of user intent"""
    project_type: str
    primary_features: List[str]
    secondary_features: List[str]
    user_roles: List[str]
    required_sections: List[str]
    complexity_level: str  # basic, medium, advanced
    domain_archetype: str
    project_category: str
    ui_style: str
    needs_images: bool
    primary_cta: str  # primary call-to-action
    target_audience: str
    tone: str  # professional, casual, luxurious, friendly, etc.
    navigation_mode: str  # single or multi


@dataclass
class UIComponentStyle:
    """Component styling options"""
    layout_type: str  # grid, list, card, table, flex
    card_elevation: bool
    use_icons: bool
    compact: bool
    rounded: bool


@dataclass
class ThemeConfig:
    """Color and style configuration"""
    primary_color: str
    secondary_color: str
    accent_color: str
    bg_color: str
    text_color: str
    gradient_style: str  # none, subtle, bold, rainbow
    border_radius: str  # round, sharp, soft
    font_style: str  # serif, sans-serif, modern, classic
    shadow_depth: str  # none, light, medium, heavy
    animations_enabled: bool


@dataclass
class UISection:
    """Planned UI section"""
    name: str
    section_type: str  # hero, features, showcase, form, dashboard, gallery, testimonials, etc.
    component_style: UIComponentStyle
    content_items: List[str]
    priority: int  # 1-10, higher = more prominent
    has_cta: bool


@dataclass
class UIPlan:
    """Complete UI architecture plan"""
    layout_family: str  # dashboard, marketplace, blog, portfolio, fullstack, landingpage
    sections: List[UISection]
    navigation_style: str  # sidebar, top, minimal
    mobile_optimized: bool
    theme: ThemeConfig
    uniqueness_seed: str
    page_mode: str = "single"  # single or multi


SECTION_IMAGE_URLS = {
    "general": {
        "hero": "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1600&q=80",
        "showcase": "https://images.unsplash.com/photo-1497366412874-3415097a27e7?auto=format&fit=crop&w=1200&q=80",
        "features": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1200&q=80",
        "pricing": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=1200&q=80",
        "testimonials": "https://images.unsplash.com/photo-1543269865-cbf427effbad?auto=format&fit=crop&w=1200&q=80",
        "contact": "https://images.unsplash.com/photo-1556761175-4b46a572b786?auto=format&fit=crop&w=1200&q=80",
        "generic": "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1200&q=80",
    },
    "food": {
        "hero": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1600&q=80",
        "showcase": "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?auto=format&fit=crop&w=1200&q=80",
        "features": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1200&q=80",
        "gallery": "https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=1200&q=80",
        "pricing": "https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=1200&q=80",
        "testimonials": "https://images.unsplash.com/photo-1528605248644-14dd04022da1?auto=format&fit=crop&w=1200&q=80",
        "contact": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=1200&q=80",
        "generic": "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=1200&q=80",
    },
    "healthcare": {
        "hero": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=1600&q=80",
        "showcase": "https://images.unsplash.com/photo-1538108149393-fbbd81895907?auto=format&fit=crop&w=1200&q=80",
        "features": "https://images.unsplash.com/photo-1516549655169-df83a0774514?auto=format&fit=crop&w=1200&q=80",
        "pricing": "https://images.unsplash.com/photo-1584515933487-779824d29309?auto=format&fit=crop&w=1200&q=80",
        "testimonials": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&w=1200&q=80",
        "contact": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=1200&q=80",
        "generic": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    },
    "travel": {
        "hero": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1600&q=80",
        "showcase": "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1200&q=80",
        "features": "https://images.unsplash.com/photo-1488085061387-422e29b40080?auto=format&fit=crop&w=1200&q=80",
        "pricing": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1200&q=80",
        "testimonials": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "contact": "https://images.unsplash.com/photo-1503220317375-aaad61436b1b?auto=format&fit=crop&w=1200&q=80",
        "generic": "https://images.unsplash.com/photo-1527631746610-bca00a040d60?auto=format&fit=crop&w=1200&q=80",
    },
    "jobs": {
        "hero": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1600&q=80",
        "showcase": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=1200&q=80",
        "features": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=1200&q=80",
        "pricing": "https://images.unsplash.com/photo-1552664730-d307ca884978?auto=format&fit=crop&w=1200&q=80",
        "testimonials": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1200&q=80",
        "contact": "https://images.unsplash.com/photo-1520607162513-77705c0f0d4a?auto=format&fit=crop&w=1200&q=80",
        "generic": "https://images.unsplash.com/photo-1516321497487-e288fb19713f?auto=format&fit=crop&w=1200&q=80",
    },
    "library": {
        "hero": "https://images.unsplash.com/photo-1521587760476-6c12a4b040da?auto=format&fit=crop&w=1600&q=80",
        "showcase": "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=1200&q=80",
        "features": "https://images.unsplash.com/photo-1491841573634-28140fc7ced7?auto=format&fit=crop&w=1200&q=80",
        "pricing": "https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=1200&q=80",
        "testimonials": "https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&w=1200&q=80",
        "contact": "https://images.unsplash.com/photo-1526243741027-444d633d7365?auto=format&fit=crop&w=1200&q=80",
        "generic": "https://images.unsplash.com/photo-1519682577862-22b62b24e493?auto=format&fit=crop&w=1200&q=80",
    },
    "ecommerce": {
        "hero": "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=1600&q=80",
        "showcase": "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?auto=format&fit=crop&w=1200&q=80",
        "features": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=1200&q=80",
        "pricing": "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=1200&q=80",
        "testimonials": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=1200&q=80",
        "contact": "https://images.unsplash.com/photo-1556740749-887f6717d7e4?auto=format&fit=crop&w=1200&q=80",
        "generic": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=1200&q=80",
    },
}


def _extract_image_terms(analysis: ProjectAnalysis, section_name: str) -> List[str]:
    domain = analysis.domain_archetype.replace("-", " ")
    section = section_name.replace("_", " ")
    category = analysis.project_category.replace("_", " ")
    tone = analysis.ui_style.replace("-", " ")
    base = [domain, category, section, tone, "modern ui", "cinematic lighting"]
    unique = []
    for term in base:
        cleaned = re.sub(r"[^a-zA-Z0-9 ]+", " ", term).strip().lower()
        if cleaned and cleaned not in unique:
            unique.append(cleaned)
    return unique[:6]


def _dynamic_image_url(terms: List[str], seed_key: str, width: int = 1400, height: int = 900) -> str:
    query = quote_plus(", ".join(terms) or "modern web interface")
    sig = int(hashlib.sha1(seed_key.encode("utf-8")).hexdigest(), 16) % 1000
    return f"https://source.unsplash.com/{width}x{height}/?{query}&sig={sig}"


def _get_section_image(section_name: str, analysis: ProjectAnalysis, variant_key: str = "") -> str:
    terms = _extract_image_terms(analysis, section_name)
    base_seed = analysis.project_type
    if hasattr(analysis, "uniqueness_seed"):
        base_seed = getattr(analysis, "uniqueness_seed") or base_seed
    if not variant_key:
        variant_key = "base"
    return _dynamic_image_url(
        terms,
        f"{analysis.project_category}:{section_name}:{base_seed}:{variant_key}",
    )


# ============================================================
# LAYER 1: PROJECT ANALYSIS
# ============================================================

def analyze_project_prompt(user_prompt: str, description: str, project_type: str, features: List[str]) -> ProjectAnalysis:
    """
    Extract structured intent from user prompt.
    Determines what the user actually needs, not just surface features.
    """
    
    prompt_lower = f"{user_prompt} {description}".lower()
    
    # Determine complexity
    if any(w in prompt_lower for w in ["simple", "basic", "minimal", "blog", "landing"]):
        complexity = "basic"
    elif any(w in prompt_lower for w in ["complex", "advanced", "enterprise", "dashboard", "admin", "multiple", "modern", "interactive", "experience", "immersive"]):
        complexity = "advanced"
    else:
        complexity = "medium"
    
    # Extract user roles
    roles = set()
    role_keywords = {
        "customer": ["customer", "buyer", "shopper", "user"],
        "admin": ["admin", "manager", "moderator"],
        "seller": ["seller", "vendor", "merchant"],
        "doctor": ["doctor", "physician", "specialist"],
        "patient": ["patient", "client"],
        "investor": ["investor", "stakeholder"],
        "employee": ["employee", "staff", "team member"],
    }
    for role, keywords in role_keywords.items():
        if any(kw in prompt_lower for kw in keywords):
            roles.add(role)
    
    if not roles:
        roles.add("user")  # default
    
    # Primary features vs secondary
    primary_features = set(features[:3]) if features else set()
    secondary_features = set(features[3:]) if len(features) > 3 else set()

    # navigation mode: single-page or multi-page based on prompt
    navigation_mode = "single"
    if any(k in prompt_lower for k in ["multi-page", "multi page", "multiple pages", "separate pages", "page per section", "new page", "section per page", "split pages", "tabs", "router"]):
        navigation_mode = "multi"
    elif project_type in {"fullstack", "ecommerce", "saas", "custom"}:
        navigation_mode = "multi"
    elif "modern" in prompt_lower and "pages" in prompt_lower:
        navigation_mode = "multi"

    # Tone defaults
    tone = "professional"
    if navigation_mode == "multi":
        tone = "luxurious"
    elif any(w in prompt_lower for w in ["friendly", "warm", "social", "community"]):
        tone = "friendly"
    elif any(w in prompt_lower for w in ["casual", "fun", "relaxed"]):
        tone = "casual"

    # Required sections based on domain and prompt intent
    sections = _infer_required_sections(description, project_type, features)
    
    # Primary CTA
    primary_cta = _infer_primary_cta(project_type, features, description)
    
    # Target audience
    audience = _infer_audience(description, project_type, roles)
    
    archetype = _infer_archetype(project_type, description)
    project_category = _infer_project_category(project_type, description, user_prompt)
    ui_style = _infer_ui_style(prompt_lower, archetype)
    needs_images = _infer_needs_images(prompt_lower, archetype)

    return ProjectAnalysis(
        project_type=project_type,
        primary_features=list(primary_features),
        secondary_features=list(secondary_features),
        user_roles=list(roles),
        required_sections=sections,
        complexity_level=complexity,
        domain_archetype=archetype,
        project_category=project_category,
        ui_style=ui_style,
        needs_images=needs_images,
        primary_cta=primary_cta,
        target_audience=audience,
        tone=tone,
        navigation_mode=navigation_mode,
    )


def _infer_required_sections(description: str, project_type: str, features: List[str]) -> List[str]:
    """Determine what sections this project type needs"""
    sections = []
    desc_lower = description.lower()
    
    # Always start with hero or banner
    sections.append("hero")
    
    # Feature-driven sections
    if "Authentication" in features:
        sections.append("login_signup")
    if "Admin Dashboard" in features:
        sections.append("dashboard")
    if "Contact Form" in features:
        sections.append("contact")
    if "File Upload" in features:
        sections.append("gallery")
    
    booking_intent = any(k in desc_lower for k in ("appointment", "appointments", "schedule", "slot", "provider availability", "service provider", "booking system"))
    travel_intent = any(k in desc_lower for k in ("hotel", "travel", "flight", "itinerary", "destination", "tour", "vacation"))

    # Domain-specific sections
    if project_type == "ecommerce" or any(k in desc_lower for k in ("product", "shop", "checkout", "cart", "catalog")):
        sections.extend(["featured_products", "categories", "testimonials", "newsletter"])
    elif project_type == "saas" or any(k in desc_lower for k in ("dashboard", "analytics", "subscription", "workflow", "metrics")):
        sections.extend(["features_grid", "pricing", "dashboard_preview", "integration_showcase"])
    elif booking_intent:
        sections.extend(["services", "appointment_booking", "dashboard", "stats", "testimonials", "contact"])
    elif "healthcare" in desc_lower or "hospital" in desc_lower or "clinic" in desc_lower:
        sections.extend(["doctors_directory", "services", "appointment_booking", "testimonials", "contact"])
    elif "job" in desc_lower or "recruitment" in desc_lower or "career" in desc_lower:
        sections.extend(["job_listings", "employer_profile", "application_form", "stats"])
    elif travel_intent:
        sections.extend(["room_showcase", "booking_form", "amenities", "reviews"])
    elif "restaurant" in desc_lower or "food" in desc_lower or "menu" in desc_lower:
        sections.extend(["gallery", "menu", "reviews", "contact"])
    elif project_type == "portfolio" or "portfolio" in desc_lower:
        sections.extend(["about", "gallery", "testimonials", "contact"])
    elif project_type == "blog" or "blog" in desc_lower:
        sections.extend(["about", "featured_products", "testimonials", "newsletter"])
    else:
        sections.extend(["features", "showcase", "testimonials"])

    if any(phrase in desc_lower for phrase in ["about us", "about", "our story"]):
        sections.append("about")
    if "gallery" in desc_lower or "interior" in desc_lower or "images" in desc_lower:
        sections.append("gallery")
    if "menu" in desc_lower or "dishes" in desc_lower or "prices" in desc_lower:
        sections.append("menu")
    if "contact" in desc_lower:
        sections.append("contact")

    # Contact/footer fallback
    if "contact_footer" not in sections:
        sections.append("contact_footer")

    # Keep order stable while removing duplicates
    seen = set()
    ordered = []
    for section in sections:
        if section not in seen:
            seen.add(section)
            ordered.append(section)
    return ordered


def _infer_primary_cta(project_type: str, features: List[str], description: str) -> str:
    """What's the main action users should take?"""
    if project_type == "ecommerce":
        return "Shop Now"
    elif project_type == "saas":
        return "Start Free Trial"
    elif any(word in description.lower() for word in ["restaurant", "food", "menu", "dining"]):
        return "Reserve a Table"
    elif "booking" in description.lower() or "appointment" in description.lower():
        return "Book Now"
    elif "Authentication" in features:
        return "Sign Up"
    elif "job" in description.lower():
        return "Apply Now"
    else:
        return "Get Started"


def _infer_audience(description: str, project_type: str, roles: Set[str]) -> str:
    """Who is the primary user?"""
    desc_lower = description.lower()
    
    if "customer" in roles:
        return "End Customers"
    elif "admin" in roles:
        return "Administrators"
    elif "B2B" in description or "enterprise" in desc_lower:
        return "Business Professionals"
    elif "developer" in desc_lower or "api" in desc_lower:
        return "Developers"
    else:
        return "General Users"


def _infer_archetype(project_type: str, description: str) -> str:
    """Determine the design archetype"""
    desc_lower = description.lower()
    
    if any(word in desc_lower for word in ["restaurant", "food", "dining", "cafe", "menu", "dish"]):
        return "food"
    if "healthcare" in desc_lower or "hospital" in desc_lower or "clinic" in desc_lower:
        return "healthcare"
    if any(word in desc_lower for word in ["appointment", "appointments", "schedule", "slot", "provider availability", "service provider", "booking system"]):
        return "booking"
    if "job" in desc_lower or "recruitment" in desc_lower or "career" in desc_lower:
        return "job-board"
    if "travel" in desc_lower or "hotel" in desc_lower or "flight" in desc_lower:
        return "travel"
    if "library" in desc_lower or re.search(r"\bbook\b", desc_lower) or "reading" in desc_lower:
        return "library"
    if project_type == "ecommerce":
        return "marketplace"
    if project_type == "saas":
        return "dashboard"
    if project_type == "blog":
        return "content-hub"
    if project_type == "portfolio":
        return "portfolio"
    return "general"


def _infer_project_category(project_type: str, description: str, user_prompt: str) -> str:
    """Generate a more specific prompt category for content and copy."""
    prompt_lower = f"{project_type} {description} {user_prompt}".lower()
    if any(k in prompt_lower for k in ["restaurant", "food delivery", "menu", "dining", "cafe"]):
        return "food_delivery"
    if any(k in prompt_lower for k in ["ecommerce", "shop", "store", "cart", "product"]):
        return "ecommerce"
    if any(k in prompt_lower for k in ["dashboard", "analytics", "saas", "subscription", "crm"]):
        return "saas_dashboard"
    if any(k in prompt_lower for k in ["portfolio", "photography", "designer", "creative", "personal site"]):
        return "portfolio"
    if any(k in prompt_lower for k in ["blog", "editorial", "articles", "stories"]):
        return "blog"
    if any(k in prompt_lower for k in ["appointment", "appointments", "schedule", "booking system", "book appointment", "service provider"]):
        return "appointment_booking"
    if any(k in prompt_lower for k in ["travel", "hotel", "trip", "itinerary", "destination", "vacation"]):
        return "travel_portal"
    if any(k in prompt_lower for k in ["job", "recruitment", "hire", "career"]):
        return "job_board"
    if any(k in prompt_lower for k in ["healthcare", "hospital", "clinic", "patient", "appointment"]):
        return "healthcare_portal"
    return project_type or "web_app"


def _infer_ui_style(prompt_lower: str, archetype: str) -> str:
    """Infer the UI style from prompt text and archetype."""
    if any(k in prompt_lower for k in ["minimal", "clean", "simple"]):
        return "minimal"
    if any(k in prompt_lower for k in ["dark", "neumorphism", "glass", "luxury"]):
        return "dark glass"
    if any(k in prompt_lower for k in ["colorful", "vibrant", "playful", "bold"]):
        return "modern colorful"
    if archetype == "healthcare":
        return "calm clinical"
    if archetype == "dashboard":
        return "clean data-focused"
    return "modern"


def _infer_needs_images(prompt_lower: str, archetype: str) -> bool:
    return any(k in prompt_lower for k in ["image", "gallery", "photo", "visual", "hero", "background"]) or archetype in {"food", "travel", "ecommerce", "healthcare", "library", "job-board"}


# ============================================================
# LAYER 2: DYNAMIC UI PLANNER
# ============================================================

def generate_ui_plan(analysis: ProjectAnalysis) -> UIPlan:
    """
    Dynamically plan the UI architecture based on project analysis.
    No two projects with different features will have identical layouts.
    """
    
    # Choose layout family
    layout_family = _choose_layout_family(analysis)
    
    # Generate unique theme
    theme = generate_theme(analysis)
    
    # Plan sections based on analysis
    sections = _plan_sections(analysis, layout_family)
    
    # Navigation style
    nav_style = _choose_navigation_style(layout_family, analysis.complexity_level)
    
    # Create uniqueness seed (for variation engine)
    uniqueness_seed = _create_uniqueness_seed(analysis)

    # Decide final page_mode for modern multi-section experiences
    page_mode = analysis.navigation_mode
    if page_mode == "single" and (len(sections) >= 5 or analysis.complexity_level == "advanced"):
        page_mode = "multi"

    return UIPlan(
        layout_family=layout_family,
        sections=sections,
        navigation_style=nav_style,
        mobile_optimized=True,
        theme=theme,
        uniqueness_seed=uniqueness_seed,
        page_mode=page_mode,
    )


def _choose_layout_family(analysis: ProjectAnalysis) -> str:
    """Choose the main layout pattern"""
    
    if analysis.project_type == "ecommerce":
        options = ["grid-sidebar", "full-grid", "featured-sidebar"]
        return random.choice(options)
    elif analysis.project_type == "saas":
        options = ["dashboard", "split-layout", "hero-features"]
        return random.choice(options)
    elif analysis.project_type in ["portfolio", "blog"]:
        return "blog-timeline"
    elif "dashboard" in analysis.primary_features:
        return "dashboard"
    elif analysis.complexity_level == "advanced":
        options = ["split-layout", "dashboard", "multi-column"]
        return random.choice(options)
    else:
        options = ["landing-page", "card-grid", "hero-sections"]
        return random.choice(options)


def _plan_sections(analysis: ProjectAnalysis, layout_family: str) -> List[UISection]:
    """Generate section plan with appropriate component styles"""
    sections = []
    
    for idx, section_name in enumerate(analysis.required_sections):
        # Determine section type
        section_type = _map_section_name_to_type(section_name)
        
        # Component style varies by section type and layout
        component_style = _choose_component_style(section_type, layout_family, analysis.complexity_level)
        
        # Content items (estimated)
        content_items = _estimate_content_items(section_name, analysis)
        
        # Priority (hero = highest, footer = lowest)
        priority = 10 - (idx * 1.5)
        
        # Has CTA?
        has_cta = section_type in ["form", "featured_products", "pricing", "hero"]
        
        section = UISection(
            name=section_name,
            section_type=section_type,
            component_style=component_style,
            content_items=content_items,
            priority=priority,
            has_cta=has_cta,
        )
        sections.append(section)
    
    return sections


def _map_section_name_to_type(section_name: str) -> str:
    """Map section name to section type"""
    mapping = {
        "hero": "hero",
        "featured_products": "showcase",
        "categories": "filter",
        "testimonials": "testimonials",
        "newsletter": "form",
        "features_grid": "features",
        "pricing": "pricing",
        "dashboard_preview": "showcase",
        "doctors_directory": "directory",
        "services": "features",
        "appointment_booking": "form",
        "job_listings": "list",
        "room_showcase": "gallery",
        "booking_form": "form",
        "menu": "list",
        "login_signup": "form",
        "admin_panel_hint": "showcase",
        "dashboard": "dashboard",
        "contact_footer": "contact",
        "about": "features",
        "gallery": "showcase",
        "integration_showcase": "showcase",
        "class_schedule": "schedule",
        "membership_plans": "pricing",
        "trainers": "directory",
        "ordering_system": "form",
        "reviews": "testimonials",
        "amenities": "features",
        "contact": "contact",
        "employer_profile": "showcase",
        "application_form": "form",
        "stats": "stats",
    }
    return mapping.get(section_name, "generic")


def _choose_component_style(section_type: str, layout_family: str, complexity: str) -> UIComponentStyle:
    """Choose how to display this section's components"""
    
    if section_type == "hero":
        return UIComponentStyle(
            layout_type="flex",
            card_elevation=False,
            use_icons=False,
            compact=False,
            rounded=False,
        )
    elif section_type in ["showcase", "directory", "gallery"]:
        layout = "grid" if layout_family == "full-grid" else "card"
        return UIComponentStyle(
            layout_type=layout,
            card_elevation=True,
            use_icons=True,
            compact=False,
            rounded=True,
        )
    elif section_type == "list":
        return UIComponentStyle(
            layout_type="list",
            card_elevation=True,
            use_icons=True,
            compact=complexity == "basic",
            rounded=True,
        )
    elif section_type == "form":
        return UIComponentStyle(
            layout_type="flex",
            card_elevation=True,
            use_icons=False,
            compact=True,
            rounded=True,
        )
    elif section_type == "dashboard":
        return UIComponentStyle(
            layout_type="grid",
            card_elevation=True,
            use_icons=True,
            compact=False,
            rounded=True,
        )
    elif section_type == "pricing":
        return UIComponentStyle(
            layout_type="grid",
            card_elevation=True,
            use_icons=False,
            compact=False,
            rounded=True,
        )
    elif section_type == "testimonials":
        return UIComponentStyle(
            layout_type="card",
            card_elevation=True,
            use_icons=True,
            compact=False,
            rounded=True,
        )
    elif section_type == "features":
        return UIComponentStyle(
            layout_type="grid",
            card_elevation=False,
            use_icons=True,
            compact=False,
            rounded=True,
        )
    else:
        return UIComponentStyle(
            layout_type="flex",
            card_elevation=False,
            use_icons=False,
            compact=False,
            rounded=True,
        )


def _estimate_content_items(section_name: str, analysis: ProjectAnalysis) -> List[str]:
    """Estimate what content items this section should have"""
    
    if section_name == "hero":
        return ["headline", "subheading", "cta_button"]
    elif section_name == "about":
        return ["our_story", "chef_philosophy", "restaurant_ambience"]
    elif section_name == "gallery":
        return ["interior_view", "signature_dish", "chef_table", "dining_space"]
    elif section_name in ["featured_products", "services", "doctors_directory"]:
        return ["item_1", "item_2", "item_3", "item_4"]
    elif section_name == "categories":
        return ["cat_1", "cat_2", "cat_3", "cat_4"]
    elif section_name == "testimonials":
        return ["testimonial_1", "testimonial_2", "testimonial_3"]
    elif section_name == "pricing":
        return ["plan_basic", "plan_pro", "plan_enterprise"]
    elif section_name == "job_listings":
        return ["job_1", "job_2", "job_3", "job_4", "job_5"]
    elif section_name == "class_schedule":
        return ["class_1", "class_2", "class_3", "class_4"]
    else:
        return ["content"]


def _choose_navigation_style(layout_family: str, complexity: str) -> str:
    """Choose navigation design"""
    if layout_family == "dashboard":
        return "sidebar"
    elif complexity == "advanced":
        options = ["top", "sticky-top", "sidebar"]
        return random.choice(options)
    else:
        return "top"


def _hero_headline(analysis: ProjectAnalysis) -> str:
    """Generate a prompt-aware hero headline."""
    if analysis.domain_archetype == "booking":
        return f"Appointment and Scheduling Experiences Built for {analysis.target_audience}."
    if analysis.domain_archetype == "food":
        return f"Delicious {analysis.project_category.replace('_', ' ').title()} Experiences for {analysis.target_audience}."
    if analysis.domain_archetype == "travel":
        return f"Travel, Booking, and Stay Experiences Built for {analysis.target_audience}."
    if analysis.domain_archetype == "job-board":
        return f"Connect Talent and Opportunities with a Smarter {analysis.project_category.replace('_', ' ').title()}."
    if analysis.domain_archetype == "healthcare":
        return f"Patient-Centered Care Experiences for Modern Health Services."
    if analysis.project_type == "saas":
        return f"Launch your next {analysis.project_category.replace('_', ' ').title()} platform with confidence."
    return f"{analysis.project_category.replace('_', ' ').title()} experiences for {analysis.target_audience}."


def _hero_body(analysis: ProjectAnalysis) -> str:
    """Generate a prompt-aware hero body copy."""
    if analysis.domain_archetype == "booking":
        return "Enable registration, provider availability, and smooth appointment flows with a modern product-grade interface."
    if analysis.project_type == "ecommerce":
        return "Showcase products, categories, and compelling offers with a polished checkout-first layout."
    if analysis.domain_archetype == "food":
        return "Invite guests to explore menus, book tables, and discover your signature dishes with vivid flavor-led visuals."
    if analysis.domain_archetype == "travel":
        return "Immerse visitors in curated journeys, room options, and destination stories that drive bookings."
    if analysis.domain_archetype == "job-board":
        return "Match roles, employers, and career seekers with a clean, trust-building interface."
    if analysis.domain_archetype == "healthcare":
        return "Build trust with clear care pathways, practitioner details, and appointment-ready interactions."
    return "This site is shaped by your brief, with real sections, smarter navigation, and a UI that feels intentionally designed."


def _hero_stats(analysis: ProjectAnalysis) -> List[Tuple[str, str]]:
    """Generate small hero stats that support the prompt."""
    if analysis.domain_archetype == "booking":
        return [("Live", "Availability"), ("Fast", "Scheduling"), ("Secure", "User access")]
    if analysis.project_type == "ecommerce":
        return [("24/7", "Online storefront"), ("3x", "Conversion-ready design"), ("100+", "Featured products")]
    if analysis.project_type == "saas":
        return [("Realtime", "Insights"), ("Secure", "Onboarding"), ("Optimized", "Flows")]
    if analysis.domain_archetype == "food":
        return [("Reservations", "Booking flows"), ("Menus", "Curated dishes"), ("Experiences", "In-store charm")]
    if analysis.domain_archetype == "travel":
        return [("Trips", "Best routes"), ("Stays", "Handpicked rooms"), ("Deals", "Instant booking")]
    return [("Adaptive", "Layout"), ("Modern", "Design"), ("Ready", "To launch")]


def _section_intro_copy(section: UISection, analysis: ProjectAnalysis) -> str:
    """Generate section intro copy from analysis."""
    name = section.name.lower()
    if name == "about":
        return f"Learn how this {analysis.project_category.replace('_', ' ')} solution delivers value for {analysis.target_audience}."
    if name == "menu":
        return "Explore the curated menu items and signature offerings designed to delight guests."
    if name == "gallery":
        return "Browse a visual story of the experience, products, or spaces that define the brand."
    if name == "featured_products":
        return "A selection of standout products and services that capture the best of this experience."
    if name == "job_listings":
        return "Open roles are presented with clear categories, priorities, and quick apply actions."
    if name == "services":
        return "Features and services that solve core user needs in a memorable, easy-to-scan layout."
    if name == "pricing":
        return "Compare the right plans at a glance and choose the best option for your team or customers."
    if name == "contact" or name == "contact_footer":
        return "Get in touch quickly to turn this concept into a working site." 
    return f"Purpose-built for {analysis.target_audience.lower()}, this section aligns with the {analysis.project_category.replace('_', ' ')} journey."


def _section_item_description(section: UISection, item: str, analysis: ProjectAnalysis) -> str:
    """Generate descriptive text for showcase items."""
    item_label = item.replace('_', ' ').title()
    if section.name == "featured_products":
        return f"Highlight {item_label} with strong product benefits for {analysis.target_audience}."
    if section.name == "categories":
        return f"Browse {item_label} categories tailored to the user's journey and intent."
    if section.name == "menu":
        return f"A delicious, easy-to-scan {item_label} designed for quick ordering and discovery."
    if section.name == "job_listings":
        return f"A clear job post showing role details, location, and how candidates can apply."
    if section.name == "gallery":
        return f"A visual highlight that brings your brand story and experience to life."
    if section.name == "services":
        return f"Describe {item_label} in a way that makes its value obvious to visitors."
    return f"{item_label} designed to support the larger brand story and prompt intent."


def _feature_copy(feature: str, analysis: ProjectAnalysis) -> str:
    """Generate feature descriptions aligned to the analysis."""
    phrase = feature.lower()
    if "analytics" in phrase or "dashboard" in phrase:
        return "Live metrics and dashboards help users make better decisions faster."
    if "subscription" in phrase or "pricing" in phrase:
        return "Transparent plans with clear benefits keep visitors confident and engaged."
    if "booking" in phrase or "appointment" in phrase:
        return "Fast booking options that reduce friction and drive conversions."
    if "inventory" in phrase or "product" in phrase:
        return "Beautiful product experiences that make discovery and purchase effortless."
    if "career" in phrase or "job" in phrase:
        return "Showcase open positions with compelling details and easy next steps."
    if analysis.domain_archetype == "food":
        return "Designed for hospitality, this feature highlights flavor, ambience, and ease of booking."
    if analysis.domain_archetype == "travel":
        return "Perfect for travel experiences, it combines trust signals with beautiful imagery."
    return f"A thoughtful feature that supports {analysis.target_audience} with a practical, modern experience."


def _create_uniqueness_seed(analysis: ProjectAnalysis) -> str:
    """Create a seed for variation engine"""
    text = f"{analysis.project_type}|{','.join(sorted(analysis.primary_features))}|{analysis.domain_archetype}|{hash(str(analysis.required_sections))}"
    return hashlib.sha256(text.encode()).hexdigest()[:16]


# ============================================================
# LAYER 3: THEME GENERATOR
# ============================================================

THEME_PALETTES = {
    "professional": [
        {"primary": "#1e40af", "secondary": "#1e3a8a", "accent": "#0ea5e9"},
        {"primary": "#374151", "secondary": "#111827", "accent": "#f59e0b"},
        {"primary": "#1f2937", "secondary": "#111827", "accent": "#8b5cf6"},
    ],
    "modern": [
        {"primary": "#ec4899", "secondary": "#db2777", "accent": "#06b6d4"},
        {"primary": "#8b5cf6", "secondary": "#6d28d9", "accent": "#10b981"},
        {"primary": "#f59e0b", "secondary": "#d97706", "accent": "#3b82f6"},
    ],
    "luxurious": [
        {"primary": "#1f2937", "secondary": "#111827", "accent": "#d4af37"},
        {"primary": "#4c1d95", "secondary": "#2e1065", "accent": "#e879f9"},
        {"primary": "#0f172a", "secondary": "#1e293b", "accent": "#c084fc"},
    ],
    "casual": [
        {"primary": "#06b6d4", "secondary": "#0891b2", "accent": "#64748b"},
        {"primary": "#10b981", "secondary": "#059669", "accent": "#ec4899"},
        {"primary": "#84cc16", "secondary": "#65a30d", "accent": "#06b6d4"},
    ],
    "healthcare": [
        {"primary": "#0ea5e9", "secondary": "#0284c7", "accent": "#10b981"},
        {"primary": "#06b6d4", "secondary": "#0891b2", "accent": "#8b5cf6"},
    ],
    "ecommerce": [
        {"primary": "#d97706", "secondary": "#b45309", "accent": "#1e3a8a"},
        {"primary": "#dc2626", "secondary": "#991b1b", "accent": "#1e40af"},
        {"primary": "#06b6d4", "secondary": "#0891b2", "accent": "#1f2937"},
    ],
}


def generate_theme(analysis: ProjectAnalysis) -> ThemeConfig:
    """
    Generate a unique color theme based on project analysis.
    Ensures variety across generations.
    """
    
    # Choose palette family based on project type and tone
    palette_family = _choose_palette_family(analysis.project_type, analysis.tone, analysis.domain_archetype)
    palettes = THEME_PALETTES.get(palette_family, THEME_PALETTES["professional"])
    
    # Pick a random palette variant
    palette = random.choice(palettes)
    
    # Generate theme
    return ThemeConfig(
        primary_color=palette["primary"],
        secondary_color=palette["secondary"],
        accent_color=palette["accent"],
        bg_color=_choose_bg_color(analysis.tone),
        text_color=_choose_text_color(analysis.tone),
        gradient_style=_choose_gradient_style(analysis.complexity_level),
        border_radius=_choose_border_radius(analysis.tone),
        font_style=_choose_font_style(analysis.tone),
        shadow_depth=_choose_shadow_depth(analysis.domain_archetype),
        animations_enabled=analysis.complexity_level != "basic",
    )


def _choose_palette_family(project_type: str, tone: str, archetype: str) -> str:
    """Intelligently choose color palette family"""
    
    if archetype == "healthcare":
        return "healthcare"
    elif project_type == "ecommerce":
        return "ecommerce"
    elif tone == "luxurious":
        return "luxurious"
    elif tone == "casual" or tone == "friendly":
        return "casual"
    elif tone == "professional":
        return "professional"
    else:
        return "modern"


def _choose_bg_color(tone: str) -> str:
    """Background color based on tone"""
    if tone == "luxurious":
        return "#0f172a"
    elif tone == "casual":
        return "#f8fafc"
    else:
        return "#ffffff"


def _choose_text_color(tone: str) -> str:
    """Text color based on tone"""
    if tone == "luxurious":
        return "#f1f5f9"
    elif tone == "casual":
        return "#1e293b"
    else:
        return "#1f2937"


def _choose_gradient_style(complexity: str) -> str:
    """Gradient complexity based on project complexity"""
    if complexity == "advanced":
        options = ["bold", "rainbow", "subtle"]
        return random.choice(options)
    elif complexity == "medium":
        return random.choice(["subtle", "bold"])
    else:
        return "none"


def _choose_border_radius(tone: str) -> str:
    """Border radius based on tone"""
    if tone == "professional":
        return "medium"
    elif tone == "luxurious":
        return "soft"
    else:
        return "round"


def _choose_font_style(tone: str) -> str:
    """Font pairing based on tone"""
    if tone == "luxurious":
        return "serif"
    elif tone == "casual":
        return "modern"
    else:
        return "sans-serif"


def _choose_shadow_depth(archetype: str) -> str:
    """Shadow depth based on archetype"""
    if archetype == "healthcare":
        return "light"
    elif archetype == "dashboard":
        return "medium"
    else:
        return "light"


# ============================================================
# LAYER 6: VARIATION ENGINE
# ============================================================

def apply_layout_variation(html: str, ui_plan: UIPlan, attempt: int = 1) -> str:
    """
    Apply variation to prevent layout repetition.
    Different attempts produce different section ordering/styling.
    """
    
    # Use uniqueness seed to deterministically vary layout
    seed_int = int(ui_plan.uniqueness_seed, 16)
    random.seed(seed_int + attempt)  # Different seed per attempt
    
    # Variation 1: Shuffle specific sections (not hero/footer)
    if attempt > 1:
        # Insert variation comment
        variation_marker = f"<!-- variation_attempt_{attempt} -->\n"
        html = variation_marker + html
    
    return html


def _site_brand(analysis: ProjectAnalysis) -> str:
    brands = {
        "food": "Restaurant",
        "healthcare": "Healthcare",
        "booking": "Booking",
        "job-board": "Careers",
        "marketplace": "Storefront",
        "dashboard": "Platform",
    }
    if analysis.project_category:
        return analysis.project_category.replace("_", " ").title()
    return brands.get(analysis.domain_archetype, analysis.project_type.title())


def _section_label(name: str) -> str:
    labels = {
        "hero": "Home",
        "menu": "Menu",
        "about": "About Us",
        "gallery": "Gallery",
        "ordering_system": "Reservations",
        "reviews": "Reviews",
        "contact": "Contact",
        "contact_footer": "Contact",
        "login_signup": "Account",
        "dashboard": "Dashboard",
        "doctors_directory": "Doctors",
        "services": "Services",
        "appointment_booking": "Appointments",
        "job_listings": "Jobs",
    }
    return labels.get(name, name.replace("_", " ").title())


def _page_filename(name: str) -> str:
    if name == "hero":
        return "home.html"
    return name.lower().replace("_", "-") + ".html"


# ============================================================
# LAYER 4: MODULAR HTML GENERATOR
# ============================================================

def generate_modular_html(ui_plan: UIPlan, analysis: ProjectAnalysis, attempt: int = 1) -> str:
    """
    Generate HTML from UI plan using modular section generation.
    Each section is generated independently for maximum flexibility.
    """
    
    # Apply variation based on attempt
    varied_plan = apply_layout_variation_to_plan(ui_plan, attempt)
    
    # Generate CSS from theme
    css = generate_css_from_theme(varied_plan.theme, analysis)
    
    # Generate navigation
    nav_html = generate_navigation(varied_plan, analysis)
    
    # Generate sections
    sections_html = ""
    for section in varied_plan.sections:
        section_html = generate_section_html(section, varied_plan.theme, analysis)
        sections_html += section_html
    
    # Generate footer
    footer_html = generate_footer(analysis)
    
    # Assemble complete HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{_site_brand(analysis)} - {analysis.primary_cta}</title>
  <style>
{css}
  </style>
</head>
<body>
{nav_html}

<main>
{sections_html}
</main>

{footer_html}

<script>
{generate_javascript(analysis)}
</script>
</body>
</html>"""
    
    return html


def generate_section_page(ui_plan: UIPlan, analysis: ProjectAnalysis, focused_section: UISection) -> str:
    """Generate a single page focusing on one section (for multi-page generation)."""
    varied_plan = apply_layout_variation_to_plan(ui_plan, 1)
    css = generate_css_from_theme(varied_plan.theme, analysis)
    nav_html = generate_navigation(varied_plan, analysis)
    section_html = generate_section_html(focused_section, varied_plan.theme, analysis)
    footer_html = generate_footer(analysis)

    page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{_site_brand(analysis)} - {_section_label(focused_section.name)}</title>
  <style>
{css}
  </style>
</head>
<body>
{nav_html}

<main>
{section_html}
</main>

{footer_html}

<script>
{generate_javascript(analysis)}
</script>
</body>
</html>"""
    return page_html


def generate_multipage_html(ui_plan: UIPlan, analysis: ProjectAnalysis) -> dict:
    """Create a dictionary of filename->html for multi-page sites."""
    output = {"index.html": generate_modular_html(ui_plan, analysis, attempt=1)}
    for section in ui_plan.sections:
        if section.section_type == "footer":
            continue
        fname = _page_filename(section.name)
        output[fname] = generate_section_page(ui_plan, analysis, section)
    return output


def apply_layout_variation_to_plan(ui_plan: UIPlan, attempt: int) -> UIPlan:
    """Apply layout variation to the UI plan itself"""
    if attempt == 1:
        return ui_plan
    
    # Create a copy and modify
    varied_plan = UIPlan(
        layout_family=ui_plan.layout_family,
        sections=ui_plan.sections.copy(),
        navigation_style=ui_plan.navigation_style,
        mobile_optimized=ui_plan.mobile_optimized,
        theme=ui_plan.theme,
        uniqueness_seed=ui_plan.uniqueness_seed,
        page_mode=ui_plan.page_mode,
    )
    
    # Keep hero first and contact_footer last, shuffle everything in between.
    start_sections = [s for s in varied_plan.sections if s.name == "hero"]
    end_sections = [s for s in varied_plan.sections if s.name == "contact_footer"]
    middle_sections = [s for s in varied_plan.sections if s.name not in {"hero", "contact_footer"}]

    seed_int = int(ui_plan.uniqueness_seed, 16)
    rng = random.Random(seed_int + attempt)
    rng.shuffle(middle_sections)

    varied_plan.sections = start_sections + middle_sections + end_sections
    
    return varied_plan


def generate_css_from_theme(theme: ThemeConfig, analysis: ProjectAnalysis) -> str:
    """Generate richer, modern CSS variables and base styles from theme."""
    hero_image = _get_section_image("hero", analysis, "hero")
    text_on_dark = "#f8fafc" if analysis.tone in {"luxurious", "professional"} else "#ffffff"
    body_background_options = [
        f"radial-gradient(circle at 14% 18%, rgba(255,255,255,0.92), rgba(255,255,255,0.52)), linear-gradient(145deg, {theme.bg_color}, #eef4ff 48%, #fff9f2 100%)",
        f"radial-gradient(circle at 86% 12%, rgba(255,255,255,0.86), rgba(255,255,255,0.35)), linear-gradient(160deg, {theme.bg_color}, #f3f9ff 52%, #fef3f2 100%)",
        f"radial-gradient(circle at 28% 78%, rgba(255,255,255,0.84), rgba(255,255,255,0.35)), linear-gradient(132deg, {theme.bg_color}, #ecfeff 46%, #fff7ed 100%)",
    ]
    reveal_presets = [
        ("18px", "0.40s", "cubic-bezier(0.16, 1, 0.3, 1)"),
        ("24px", "0.52s", "cubic-bezier(0.22, 1, 0.36, 1)"),
        ("14px", "0.36s", "ease-out"),
    ]
    body_background = random.choice(body_background_options)
    reveal_distance, reveal_duration, reveal_ease = random.choice(reveal_presets)
    return f""":root {{
  --primary: {theme.primary_color};
  --secondary: {theme.secondary_color};
  --accent: {theme.accent_color};
  --bg: {theme.bg_color};
  --surface: rgba(255,255,255,0.88);
  --surface-strong: #ffffff;
  --text: {theme.text_color};
  --muted: rgba(31,41,55,0.74);
  --line: rgba(15,23,42,0.08);
  --radius-xl: 28px;
  --radius-lg: 20px;
  --radius-md: 14px;
  --shadow-lg: 0 26px 60px rgba(15,23,42,0.16);
  --shadow-md: 0 18px 40px rgba(15,23,42,0.08);
  --max-width: 1180px;
  --reveal-distance: {reveal_distance};
  --reveal-duration: {reveal_duration};
  --reveal-ease: {reveal_ease};
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ scroll-behavior: smooth; }}
body {{
  font-family: {theme.font_style}, sans-serif;
  background: {body_background};
  color: var(--text);
  line-height: 1.6;
}}
a {{ color: inherit; text-decoration: none; }}
button {{
  background: linear-gradient(135deg, var(--accent), #ffe0a3);
  color: #111827;
  border: none;
  padding: 12px 22px;
  border-radius: 999px;
  cursor: pointer;
  transition: transform 0.22s ease, box-shadow 0.22s ease;
  box-shadow: 0 12px 24px rgba(0,0,0,0.12);
  font-weight: 700;
}}
button:hover {{ transform: translateY(-2px); }}
.top-nav {{
  position: sticky;
  top: 0;
  z-index: 40;
  backdrop-filter: blur(18px);
  background: rgba(10, 16, 28, 0.78);
  border-bottom: 1px solid rgba(255,255,255,0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 16px 20px;
}}
.nav-brand {{
  color: #fff;
  font-size: 1.2rem;
  font-weight: 800;
  letter-spacing: 0.02em;
}}
.nav-links {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  list-style: none;
}}
.nav-links a {{
  color: rgba(255,255,255,0.84);
  padding: 10px 14px;
  border-radius: 999px;
  transition: 0.2s ease;
}}
.nav-links a:hover {{
  background: rgba(255,255,255,0.12);
  color: #fff;
}}
.nav-links .nav-primary {{
  background: linear-gradient(135deg, var(--accent), #ffe0a3);
  color: #111827;
  font-weight: 800;
}}
main {{
  display: grid;
  gap: 28px;
  padding-bottom: 48px;
}}
.container, .section-wrap {{
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 20px;
}}
.hero-section {{
  min-height: 76vh;
  margin: 22px auto 0;
  max-width: var(--max-width);
  border-radius: 34px;
  overflow: hidden;
  box-shadow: var(--shadow-lg);
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  background: linear-gradient(135deg, rgba(10,16,28,0.86), rgba(10,16,28,0.52));
}}
.hero-content {{
  padding: 56px;
  color: {text_on_dark};
  display: grid;
  align-content: center;
  gap: 18px;
}}
.hero-content .eyebrow {{
  display: inline-flex;
  width: fit-content;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(255,255,255,0.12);
  color: rgba(255,255,255,0.82);
  font-size: 0.86rem;
}}
.hero-content h1 {{
  color: #ffffff;
  font-size: clamp(2.4rem, 5vw, 5rem);
  line-height: 0.98;
}}
.hero-content p {{
  max-width: 58ch;
  color: rgba(255,255,255,0.82);
  font-size: 1.04rem;
}}
.hero-actions {{
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
}}
.hero-secondary {{
  background: rgba(255,255,255,0.12);
  color: #fff;
  border: 1px solid rgba(255,255,255,0.16);
  box-shadow: none;
}}
.hero-visual {{
  position: relative;
  background: linear-gradient(180deg, rgba(0,0,0,0.12), rgba(0,0,0,0.18)), url('{hero_image}') center/cover no-repeat;
}}
.hero-stats {{
  position: absolute;
  left: 24px;
  right: 24px;
  bottom: 24px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}}
.stat-chip {{
  padding: 16px;
  border-radius: 18px;
  background: rgba(255,255,255,0.14);
  border: 1px solid rgba(255,255,255,0.18);
  backdrop-filter: blur(10px);
  color: #fff;
}}
.stat-chip strong {{
  display: block;
  font-size: 1.3rem;
}}
.section-block {{
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 20px;
}}
.section-header {{
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 18px;
  margin-bottom: 18px;
}}
.section-header h2 {{
  font-size: clamp(1.6rem, 3vw, 2.6rem);
  color: var(--primary);
}}
.section-header p {{
  max-width: 54ch;
  color: var(--muted);
}}
.grid {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}}
.card {{
  background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(255,255,255,0.84));
  border-radius: var(--radius-xl);
  padding: 20px;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--line);
}}
.showcase-item, .feature-card, .testimonial-card, .pricing-card {{
  border-radius: var(--radius-xl);
  overflow: hidden;
  background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(255,255,255,0.84));
  box-shadow: var(--shadow-md);
  border: 1px solid var(--line);
  transition: transform 0.24s ease, box-shadow 0.24s ease;
}}
.showcase-item:hover, .feature-card:hover, .testimonial-card:hover, .pricing-card:hover {{
  transform: translateY(-4px);
  box-shadow: 0 22px 38px rgba(15,23,42,0.14);
}}
.section-image {{
  width: 100%;
  height: 220px;
  object-fit: cover;
  margin-bottom: 0;
}}
.feature-card, .pricing-card {{
  padding: 24px;
}}
.feature-icon {{
  width: 48px;
  height: 48px;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  color: #fff;
  display: grid;
  place-items: center;
  font-weight: 800;
  margin-bottom: 14px;
}}
.filter-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 18px;
}}
.filter-chip {{
  padding: 10px 14px;
  border-radius: 999px;
  border: 1px solid rgba(15,23,42,0.08);
  background: rgba(255,255,255,0.8);
}}
.pricing-card.featured {{
  background: linear-gradient(180deg, rgba(29,78,216,0.08), rgba(255,255,255,0.98));
}}
.pricing-card .price {{
  font-size: 2rem;
  font-weight: 800;
  margin: 10px 0;
}}
.pricing-card ul {{
  list-style: none;
  display: grid;
  gap: 10px;
  margin: 14px 0 18px;
}}
.pricing-card li::before {{
  content: "•";
  color: var(--accent);
  margin-right: 8px;
}}
.testimonial-card .quote {{
  font-size: 1.04rem;
  line-height: 1.8;
}}
.faq-item {{
  border-top: 1px solid rgba(15,23,42,0.08);
  padding: 14px 0;
}}
.faq-item:first-child {{ border-top: 0; }}
.faq-question {{
  width: 100%;
  text-align: left;
  background: transparent;
  color: var(--text);
  border-radius: 0;
  padding: 0;
  box-shadow: none;
}}
.faq-answer {{
  max-height: 0;
  overflow: hidden;
  color: var(--muted);
  transition: max-height 0.22s ease;
}}
.faq-item.open .faq-answer {{
  max-height: 140px;
  margin-top: 10px;
}}
.contact-grid {{
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 18px;
}}
.contact-form {{
  display: grid;
  gap: 12px;
}}
.contact-form input, .contact-form textarea {{
  width: 100%;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(15,23,42,0.08);
  background: rgba(255,255,255,0.92);
}}
.main-footer {{
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 20px 40px;
}}
.main-footer .footer-panel {{
  border-radius: 28px;
  padding: 28px;
  background: linear-gradient(135deg, rgba(8,15,29,0.94), rgba(28,38,56,0.9));
  color: rgba(255,255,255,0.82);
}}
.reveal {{
  opacity: 0;
  transform: translateY(var(--reveal-distance)) scale(0.985);
  transition: opacity var(--reveal-duration) var(--reveal-ease), transform var(--reveal-duration) var(--reveal-ease);
}}
.reveal.is-visible {{
  opacity: 1;
  transform: translateY(0) scale(1);
}}
@media (max-width: 980px) {{
  .hero-section, .contact-grid, .grid, .hero-stats {{
    grid-template-columns: 1fr;
  }}
}}
@media (max-width: 768px) {{
  .top-nav {{
    flex-direction: column;
    align-items: flex-start;
  }}
  .nav-links {{
    width: 100%;
  }}
  .hero-content {{
    padding: 32px 24px;
  }}
}}
"""


def generate_navigation(ui_plan: UIPlan, analysis: ProjectAnalysis) -> str:
    """Generate navigation HTML with real section/page routing."""
    nav_class = "top-nav" if ui_plan.navigation_style == "top" else "sidebar-nav"
    nav_html = f"""<nav class="{nav_class}">
  <div class="nav-brand">{_site_brand(analysis)}</div>
  <ul class="nav-links">
"""
    nav_sections = [section for section in ui_plan.sections if section.section_type != "footer"]
    for section in nav_sections:
        label = _section_label(section.name)
        if ui_plan.page_mode == "multi":
            href = _page_filename(section.name)
        else:
            href = "#" + section.name.lower().replace("_", "-")
        nav_html += f'    <li><a href="{href}">{label}</a></li>\n'
    cta_href = "#contact" if ui_plan.page_mode == "single" else "contact-footer.html"
    nav_html += f'    <li><a href="{cta_href}" class="nav-primary">{analysis.primary_cta}</a></li>\n'
    nav_html += "  </ul>\n</nav>"
    return nav_html


def generate_section_html(section: UISection, theme: ThemeConfig, analysis: ProjectAnalysis) -> str:
    """Generate HTML for a single section"""
    
    section_id = section.name.lower().replace("_", "-")
    
    if section.section_type == "hero":
        return generate_hero_section(section, theme, analysis)
    elif section.section_type in {"showcase", "list", "gallery", "directory", "filter"}:
        return generate_showcase_section(section, theme, analysis)
    elif section.section_type == "features":
        return generate_features_section(section, theme, analysis)
    elif section.section_type == "form":
        return generate_form_section(section, theme, analysis)
    elif section.section_type == "pricing":
        return generate_pricing_section(section, theme, analysis)
    elif section.section_type == "testimonials":
        return generate_testimonials_section(section, theme, analysis)
    elif section.section_type == "contact":
        return generate_form_section(section, theme, analysis)
    elif section.section_type == "footer":
        return generate_footer_section(section, theme, analysis)
    else:
        return generate_generic_section(section, theme, analysis)


def generate_hero_section(section: UISection, theme: ThemeConfig, analysis: ProjectAnalysis) -> str:
    """Generate hero section HTML"""
    headline = _hero_headline(analysis)
    body = _hero_body(analysis)
    stats = _hero_stats(analysis)
    stat_html = "".join(f'<div class="stat-chip"><strong class="counter" data-target="100">{value}</strong><span>{label}</span></div>' for value, label in stats)
    return f"""<section id="{section.name.lower().replace('_', '-') }" class="hero-section reveal">
  <div class="hero-content">
    <span class="eyebrow">{analysis.project_category.replace('_', ' ').title()}</span>
    <h1>{headline}</h1>
    <p>{body}</p>
    <div class="hero-actions">
      <button class="cta-button">{analysis.primary_cta}</button>
      <button class="hero-secondary" type="button" onclick="const target=document.querySelector('#highlights')||document.querySelector('main section:nth-of-type(2)'); if(target) target.scrollIntoView({{behavior:'smooth'}});">Explore sections</button>
    </div>
  </div>
  <div class="hero-visual">
    <div class="hero-stats">
      {stat_html}
    </div>
  </div>
</section>"""

def generate_showcase_section(section: UISection, theme: ThemeConfig, analysis: ProjectAnalysis) -> str:
    """Generate showcase section HTML"""
    items_html = ""
    for i, item in enumerate(section.content_items):
        image_url = _get_section_image(section.name, analysis, f"{section.name}-{i}")
        description = _section_item_description(section, item, analysis)
        items_html += f"""    <div class="showcase-item reveal">
      <img class="section-image" src="{image_url}" alt="{item}">
      <div class="card">
        <div class="feature-icon">0{i + 1}</div>
        <h3>{item.replace('_', ' ').title()}</h3>
        <p>{description}</p>
      </div>
    </div>
"""

    filters = ""
    if section.name in {"featured_products", "categories", "menu", "job_listings"}:
        labels = {
            "featured_products": ["Featured", "New arrivals", "Popular", "Premium"],
            "categories": ["All", "Trending", "Value", "Signature"],
            "menu": ["Chef picks", "Starters", "Mains", "Desserts"],
            "job_listings": ["All roles", "Remote", "Operations", "Engineering"],
        }
        filters = '<div class="filter-row">' + "".join(f'<span class="filter-chip">{label}</span>' for label in labels.get(section.name, [])) + "</div>"

    return f"""<section id="{section.name.lower().replace('_', '-') }" class="section-block">
  <div class="section-header reveal" id="highlights">
    <div>
      <h2>{_section_label(section.name)}</h2>
      <p>{_section_intro_copy(section, analysis)}</p>
    </div>
  </div>
  {filters}
  <div class="grid">
{items_html}    </div>
</section>"""


def generate_features_section(section: UISection, theme: ThemeConfig, analysis: ProjectAnalysis) -> str:
    """Generate features section HTML"""
    features_html = ""
    if section.name == "about":
        story_cards = [
            ("Our Story", "A warm introduction to the brand, its mission, and how the experience is shaped by the prompt."),
            ("What Sets Us Apart", "Highlight the unique offering, audience value, and how the solution solves the core need."),
            ("How It Works", "Explain the main flow clearly so visitors understand the service and feel invited to act."),
        ]
        for i, (title, copy) in enumerate(story_cards):
            features_html += f"""    <div class="feature-card reveal">
      <div class="feature-icon">0{i + 1}</div>
      <h3>{title}</h3>
      <p>{copy}</p>
    </div>
"""
    else:
        source_features = analysis.primary_features or ["Responsive UI", "Context-aware content", "Modern interaction"]
        for i, feature in enumerate(source_features):
            features_html += f"""    <div class="feature-card reveal">
      <div class="feature-icon">0{i + 1}</div>
      <h3>{feature}</h3>
      <p>{_feature_copy(feature, analysis)}</p>
    </div>
"""

    return f"""<section id="{section.name.lower().replace('_', '-') }" class="section-block">
  <div class="section-header reveal">
    <div>
      <h2>{_section_label(section.name)}</h2>
      <p>{_section_intro_copy(section, analysis)}</p>
    </div>
  </div>
  <div class="filter-row reveal"><span class="filter-chip">Responsive</span><span class="filter-chip">Interactive</span><span class="filter-chip">Modern</span><span class="filter-chip">Prompt-led</span></div>
  <div class="grid">
{features_html}    </div>
</section>"""


def generate_form_section(section: UISection, theme: ThemeConfig, analysis: ProjectAnalysis) -> str:
    """Generate form section HTML"""
    if section.name == "login_signup":
        return f"""<section id="{section.name.lower().replace('_', '-') }" class="section-block">
  <div class="contact-grid">
    <div class="card reveal">
      <div class="section-header">
        <div>
          <h2>Sign Up</h2>
          <p>Create your account to continue.</p>
        </div>
      </div>
      <form id="signup-form" data-auth="signup" class="contact-form" data-demo-form="{section.name}-signup">
        <input type="text" placeholder="Full name" required>
        <input type="email" placeholder="Email" required>
        <input type="password" placeholder="Password" required>
        <button type="submit">Create Account</button>
        <p data-form-status></p>
      </form>
    </div>
    <div class="card reveal">
      <div class="section-header">
        <div>
          <h2>Log In</h2>
          <p>Access your dashboard and saved activity.</p>
        </div>
      </div>
      <form id="login-form" data-auth="login" class="contact-form" data-demo-form="{section.name}-login">
        <input type="email" placeholder="Email" required>
        <input type="password" placeholder="Password" required>
        <button type="submit">Log In</button>
        <p data-form-status></p>
      </form>
    </div>
  </div>
</section>"""

    form_label = "Tell us how we can shape your idea" if section.name == "appointment_booking" else "Send your request"
    return f"""<section id="{section.name.lower().replace('_', '-') }" class="section-block">
  <div class="contact-grid">
    <div class="card reveal">
      <div class="section-header">
        <div>
          <h2>{_section_label(section.name)}</h2>
          <p>{form_label}</p>
        </div>
      </div>
      <form class="contact-form" data-demo-form="{section.name}">
        <input type="text" placeholder="Name" required>
        <input type="email" placeholder="Email" required>
        <textarea placeholder="{analysis.target_audience} needs, goals, or questions" required></textarea>
        <button type="submit">{analysis.primary_cta}</button>
        <p data-form-status></p>
      </form>
    </div>
    <div class="card reveal">
      <h3>Why this section matters</h3>
      <p>Users reach this block through dedicated navigation and clearer content flow instead of a long one-page stack where everything competes for attention.</p>
    </div>
  </div>
</section>"""


def generate_pricing_section(section: UISection, theme: ThemeConfig, analysis: ProjectAnalysis) -> str:

    """Generate pricing section HTML"""
    plans = ["Launch", "Growth", "Flagship"]
    prices = ["$19/mo", "$49/mo", "$99/mo"]
    
    pricing_html = ""
    for i, plan in enumerate(plans):
        featured = " featured" if i == 1 else ""
        pricing_html += f"""    <div class="pricing-card{featured} reveal">
      <h3>{plan}</h3>
      <div class="price">{prices[i]}</div>
      <ul>
        <li>Prompt-aware section planning</li>
        <li>Modern navigation flow</li>
        <li>Interactive UI feedback</li>
      </ul>
      <button>Choose {plan}</button>
    </div>\n"""
    
    return f"""<section id="{section.name.lower().replace('_', '-')}" class="section-block">
  <div class="section-header reveal">
    <div>
      <h2>Pricing Plans</h2>
      <p>Pricing now feels like part of the overall design system instead of a detached demo block.</p>
    </div>
  </div>
  <div class="grid">
{pricing_html}    </div>
</section>"""


def generate_testimonials_section(section: UISection, theme: ThemeConfig, analysis: ProjectAnalysis) -> str:
    """Generate testimonials section HTML"""
    if analysis.domain_archetype == "food":
        testimonials = [
            {"name": "Aisha K.", "role": "Guest", "text": "The site finally feels like a real dining brand and not a flat generator template."},
            {"name": "Rahul M.", "role": "Regular", "text": "Menu discovery and booking cues are much clearer now."},
            {"name": "Neha P.", "role": "Event Planner", "text": "Different sections finally have purpose and flow."},
        ]
    elif analysis.domain_archetype == "healthcare":
        testimonials = [
            {"name": "Anita S.", "role": "Patient Coordinator", "text": "Doctors, departments, and appointments feel far easier to understand."},
            {"name": "Dr. Roy", "role": "Specialist", "text": "The structure builds trust much better than the earlier generic layout."},
            {"name": "Manish T.", "role": "Admin", "text": "This feels closer to a real healthcare interface than a placeholder demo."},
        ]
    else:
        testimonials = [
            {"name": "Maya R.", "role": "Product Lead", "text": "The generator now produces stronger visual systems and more believable structure."},
            {"name": "Karan D.", "role": "Founder", "text": "It feels less like a template and more like something shaped by the brief."},
            {"name": "Sara J.", "role": "Operations Manager", "text": "Separate navigation and working interactions made a big difference."},
        ]
    
    testimonial_html = ""
    for i, testimonial in enumerate(testimonials):
        image_url = _get_section_image(section.name, analysis, f"{section.name}-testimonial-{i}")
        testimonial_html += f"""    <div class="testimonial-card reveal">
      <img class="section-image" src="{image_url}" alt="{testimonial['name']}">
      <div class="card">
        <p class="quote">"{testimonial['text']}"</p>
        <cite>- {testimonial['name']}, {testimonial['role']}</cite>
      </div>
    </div>\n"""
    
    return f"""<section id="{section.name.lower().replace('_', '-')}" class="section-block">
  <div class="section-header reveal">
    <div>
      <h2>What Our Users Say</h2>
      <p>Testimonials now act as trust-building content instead of filler paragraphs.</p>
    </div>
  </div>
  <div class="grid">
{testimonial_html}    </div>
  </div>
</section>"""


def generate_footer_section(section: UISection, theme: ThemeConfig, analysis: ProjectAnalysis) -> str:
    """Generate footer section HTML"""
    return f"""<footer id="{section.name.lower().replace('_', '-')}" class="footer-section">
  <div class="container">
    <p>&copy; 2024 {analysis.project_type.title()}. Built with NovaForge.</p>
  </div>
</footer>"""


def generate_generic_section(section: UISection, theme: ThemeConfig, analysis: ProjectAnalysis) -> str:
    """Generate generic section HTML"""
    return f"""<section id="{section.name.lower().replace('_', '-')}" class="section-block">
  <div class="card reveal">
    <div class="section-header">
      <div>
    <h2>{_section_label(section.name)}</h2>
        <p>{_section_intro_copy(section, analysis)}</p>
      </div>
    </div>
    <p>{_section_item_description(section, section.content_items[0] if section.content_items else "content", analysis)}</p>
  </div>
</section>"""


def generate_footer(analysis: ProjectAnalysis) -> str:
    """Generate footer HTML"""
    return f"""<footer class="main-footer">
  <div class="footer-panel">
    <p>&copy; 2026 {analysis.project_type.title()}. Powered by NovaForge AI with prompt-aware layouts, richer sections, and modern interactions.</p>
  </div>
</footer>"""


def generate_javascript(analysis: ProjectAnalysis) -> str:
    """Generate JavaScript based on analysis"""
    reveal_threshold = random.choice([0.12, 0.16, 0.22])
    stagger_delay = random.choice([35, 55, 80])
    counter_steps = random.choice([16, 18, 22])
    api_helper = ""
    if analysis.project_type in {"fullstack", "ecommerce", "saas", "custom"}:
        api_helper = """
const API_BASE = 'http://localhost:5001/api';
async function apiRequest(path, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${path}`, options);
    const data = await response.json().catch(() => ({}));
    return { ok: response.ok, data };
  } catch (error) {
    return { ok: false, data: { message: 'Backend unavailable in preview mode.' } };
  }
}
"""
    js = f"""{api_helper}// NovaForge Generated JavaScript
document.addEventListener('DOMContentLoaded', function() {{
  const forms = document.querySelectorAll('form[data-demo-form]');
  forms.forEach(form => {{
    form.addEventListener('submit', async function(e) {{
      e.preventDefault();
      const status = form.querySelector('[data-form-status]');
      if (status) status.textContent = 'Sending...';
      await new Promise(resolve => setTimeout(resolve, 280));
      if (status) status.textContent = 'Thanks. This demo interaction is wired and working.';
    }});
  }});

  const faqButtons = document.querySelectorAll('.faq-question');
  faqButtons.forEach(button => {{
    button.addEventListener('click', function() {{
      const item = this.closest('.faq-item');
      if (item) item.classList.toggle('open');
    }});
  }});

  const revealObserver = new IntersectionObserver(entries => {{
    entries.forEach(entry => {{
      if (entry.isIntersecting) {{
        entry.target.classList.add('is-visible');
      }}
    }});
  }}, {{ threshold: {reveal_threshold} }});
  document.querySelectorAll('.reveal').forEach((el, idx) => {{
    el.style.transitionDelay = `${{idx * {stagger_delay}}}ms`;
    revealObserver.observe(el);
  }});

  const counters = document.querySelectorAll('.counter');
  counters.forEach(counter => {{
    const raw = counter.textContent.trim();
    const target = Number((raw.match(/\\d+/) || ['0'])[0]);
    if (!target) return;
    let current = 0;
    const timer = setInterval(() => {{
      current += Math.max(1, Math.ceil(target / {counter_steps}));
      if (current >= target) {{
        current = target;
        clearInterval(timer);
      }}
      counter.textContent = raw.includes('%') ? current + '%' : raw.includes('+') ? current + '+' : current + (raw.includes('m') ? 'm' : '');
    }}, 40);
  }});

  const navLinks = document.querySelectorAll('nav a[href^="#"]');
  navLinks.forEach(link => {{
    link.addEventListener('click', function(e) {{
      const target = document.querySelector(this.getAttribute('href'));
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({{ behavior: 'smooth' }});
    }});
  }});
}});"""
    return js


# ============================================================
# LAYER 5: IMAGE PLACEMENT SYSTEM
# ============================================================

def place_images_in_html(html: str, ui_plan: UIPlan, analysis: ProjectAnalysis, available_images: List[str]) -> str:
    """
    Intelligently place images in appropriate UI sections based on content and context.
    Maps images to sections that would benefit most from visual content.
    """
    
    if not available_images:
        return html
    
    # Analyze which sections need images
    image_sections = identify_image_sections(ui_plan, analysis)
    
    # Map images to sections
    image_mapping = map_images_to_sections(image_sections, available_images, analysis)
    
    # Insert images into HTML
    for section_id, image_url in image_mapping.items():
        html = insert_image_into_section(html, section_id, image_url, ui_plan.theme)
    
    return html


def identify_image_sections(ui_plan: UIPlan, analysis: ProjectAnalysis) -> List[str]:
    """Identify which sections would benefit from images"""
    
    image_sections = []
    
    for section in ui_plan.sections:
        # Hero sections always get images
        if section.section_type == "hero":
            image_sections.append(section.name)
        # Showcase sections for products/services
        elif section.section_type in ["showcase", "gallery", "directory"]:
            image_sections.append(section.name)
        # Testimonials if they have profile images
        elif section.section_type == "testimonials":
            image_sections.append(section.name)
        # Features if they need visual explanation
        elif section.section_type == "features" and len(analysis.primary_features) > 2:
            image_sections.append(section.name)
    
    return image_sections


def map_images_to_sections(section_ids: List[str], available_images: List[str], analysis: ProjectAnalysis) -> Dict[str, str]:
    """Map available images to appropriate sections"""
    
    mapping = {}
    images_used = 0
    
    for section_id in section_ids:
        if images_used >= len(available_images):
            break
            
        # Select image based on section type and project type
        image_index = select_image_for_section(section_id, analysis, images_used, len(available_images))
        if image_index < len(available_images):
            mapping[section_id] = available_images[image_index]
            images_used += 1
    
    return mapping


def select_image_for_section(section_id: str, analysis: ProjectAnalysis, current_index: int, total_images: int) -> int:
    """Select the most appropriate image for a section"""
    
    # Use deterministic selection based on section and project type
    seed = hash(f"{section_id}_{analysis.project_type}_{analysis.domain_archetype}") % 1000
    random.seed(seed + current_index)
    
    # Prefer different images for different sections
    return random.randint(0, total_images - 1)


def insert_image_into_section(html: str, section_id: str, image_url: str, theme: ThemeConfig) -> str:
    """Insert an image into the specified section"""
    
    section_selector = f'id="{section_id.lower().replace("_", "-")}"'
    
    # Find the section in HTML
    section_start = html.find(f'<section {section_selector}')
    if section_start == -1:
        return html
    section_end = html.find("</section>", section_start)
    if section_end != -1 and 'class="section-image"' in html[section_start:section_end]:
        return html
    
    # Find the end of the opening tag
    tag_end = html.find('>', section_start)
    if tag_end == -1:
        return html
    
    # Insert image at the beginning of the section content
    insert_pos = tag_end + 1
    
    # Create image HTML with theme-appropriate styling
    image_html = f"""
  <div class="section-image" style="background-image: url('{image_url}'); background-size: cover; background-position: center; height: 300px; border-radius: var(--radius-lg); margin-bottom: 20px;"></div>
"""
    
    # Insert the image
    html = html[:insert_pos] + image_html + html[insert_pos:]
    
    return html


def generate_image_prompts(project_name: str, description: str, analysis: ProjectAnalysis, ui_plan: UIPlan) -> List[Dict[str, str]]:
    """Create prompt-driven image prompts for every visual section."""
    prompts: List[Dict[str, str]] = []
    base_topic = analysis.project_category.replace("_", " ")
    desc_bits = [bit.strip() for bit in re.split(r"[.,;]", description or "") if bit.strip()]
    for section in ui_plan.sections:
        if section.section_type not in {"hero", "showcase", "gallery", "directory", "testimonials", "features"}:
            continue
        section_topic = section.name.replace("_", " ")
        detail = desc_bits[0] if desc_bits else f"{analysis.target_audience} experience"
        prompt = (
            f"{project_name} {base_topic} product design, {section_topic}, {analysis.ui_style} style, "
            f"{detail}, modern interactive website scene, no text overlays"
        )
        prompts.append({"section": section.name, "purpose": section.section_type, "prompt": prompt})
    if not prompts:
        prompts.append(
            {
                "section": "hero",
                "purpose": "hero",
                "prompt": f"{project_name} {base_topic} modern web interface visual, {analysis.ui_style}, no text overlays",
            }
        )
    return prompts


def generate_contextual_image_urls(project_name: str, description: str, analysis: ProjectAnalysis, ui_plan: UIPlan, max_images: int = 14) -> List[str]:
    """Turn image prompts into dynamic image URLs (no predefined static image list)."""
    prompts = generate_image_prompts(project_name, description, analysis, ui_plan)
    urls: List[str] = []
    for i, payload in enumerate(prompts):
        terms = [payload.get("section", ""), payload.get("purpose", ""), analysis.project_category, analysis.domain_archetype, analysis.ui_style]
        cleaned_terms = [re.sub(r"[^a-zA-Z0-9 ]+", " ", t).strip() for t in terms if t]
        query = quote_plus(", ".join(cleaned_terms[:5]) or "modern website")
        sig = int(hashlib.md5(f"{project_name}:{payload.get('section')}:{i}".encode("utf-8")).hexdigest(), 16) % 1000
        urls.append(f"https://source.unsplash.com/1400x900/?{query}&sig={sig}")
        if len(urls) >= max_images:
            break
    return urls

# ============================================================
# JSON EXPORT FOR DEBUGGING
# ============================================================

def export_analysis(analysis: ProjectAnalysis) -> str:
    """Export analysis as JSON for debugging"""
    return json.dumps(asdict(analysis), indent=2)


def export_ui_plan(plan: UIPlan) -> str:
    """Export UI plan as JSON for debugging"""
    plan_dict = asdict(plan)
    # Convert theme to dict
    plan_dict["theme"] = asdict(plan.theme)
    # Convert sections to dicts
    plan_dict["sections"] = [
        {
            **asdict(section),
            "component_style": asdict(section.component_style)
        }
        for section in plan.sections
    ]
    return json.dumps(plan_dict, indent=2)
