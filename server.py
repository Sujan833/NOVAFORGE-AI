# # AI Website Generator Backend - Using FREE Google Gemini (Latest API)
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import google.generativeai as genai
# from dotenv import load_dotenv
# import os
# import pathlib
# import requests

# # Load environment variables from .env file
# load_dotenv()

# app = Flask(__name__)
# CORS(app)

# # Get API key from .env file
# GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# if not GEMINI_API_KEY:
#     print("❌ ERROR: GEMINI_API_KEY not found in .env file!")
#     print("💡 Create a .env file in the backend folder with:")
#     print("   GEMINI_API_KEY=your-api-key-here")
#     exit(1)
# else:
#     print(f"✅ API Key loaded: {GEMINI_API_KEY[:10]}...")

# NETLIFY_BUILD_HOOK = os.getenv('NETLIFY_BUILD_HOOK')  # Netlify build hook URL
# NETLIFY_SITE_URL = os.getenv('NETLIFY_SITE_URL')      # Your public site URL, e.g. https://my-app.netlify.app
# BASE_DIR = pathlib.Path(__file__).resolve().parent
# GENERATED_ROOT = BASE_DIR / "generated_projects"
# GENERATED_ROOT.mkdir(exist_ok=True)

# # Configure Gemini API
# genai.configure(api_key=GEMINI_API_KEY)

# # Use the latest API - gemini-1.5-flash (works with version 0.8.3)
# model = genai.GenerativeModel('models/gemini-2.5-flash')

# @app.route('/api/generate', methods=['POST'])
# def generate_code():
#     """Generate website code using FREE Gemini AI"""
#     try:
#         data = request.json
#         project_name = data.get('projectName', 'Website')
#         project_type = data.get('projectType', 'landing')
#         description = data.get('description', '')
#         tech_stack = data.get('techStack', [])
        
#         # Create detailed prompt for Gemini
#         prompt = f"""
# You are an expert full-stack web developer. Generate complete, production-ready code.

# PROJECT DETAILS:
# - Name: {project_name}
# - Type: {project_type}
# - Description: {description}
# - Tech Stack: {', '.join(tech_stack) if tech_stack else 'HTML, CSS, JavaScript'}

# REQUIREMENTS:
# 1. Generate a complete HTML file with embedded CSS and JavaScript
# 2. Use modern, clean design with gradients and animations
# 3. Make it fully responsive (mobile-friendly)
# 4. Include proper semantic HTML5
# 5. Add interactive features with JavaScript
# 6. Use beautiful color schemes (purple/blue gradients preferred)
# 7. Make sure all code is production-ready and well-commented
# 8. **IMPORTANT:** In the JavaScript (<script>) section, use `fetch()` to retrieve live data from a public REST API (such as https://jsonplaceholder.typicode.com or https://fakestoreapi.com), and dynamically render this data on the site. For a blog, fetch posts; for products, fetch products; for user list, fetch users, etc.

# OUTPUT FORMAT:
# Return ONLY the complete HTML code (including <style> and <script> tags).
# No explanations, just the code starting with <!DOCTYPE html>

# Generate the code now:
# """
        
#         # Call Gemini API (FREE!)
#         print(f"🤖 Calling Gemini API for: {project_name}")
#         response = model.generate_content(prompt)
#         generated_code = response.text
        
#         # Clean up the response (remove markdown code blocks if present)
#         generated_code = generated_code.replace('``````', '').strip()
        
#         # Parse into sections (for frontend tabs)
#         html_code = generated_code
#         css_code = extract_between_tags(generated_code, '<style>', '</style>')
#         js_code = extract_between_tags(generated_code, '<script>', '</script>')
        
#         print(f"✅ Code generated successfully!")
        
#         return jsonify({
#             'success': True,
#             'code': {
#                 'html': html_code,
#                 'css': css_code if css_code else '/* CSS is embedded in HTML */',
#                 'js': js_code if js_code else '// JavaScript is embedded in HTML',
#                 'backend': generate_backend_code(project_type, project_name)
#             },
#             'projectName': project_name,
#             'model': 'gemini-1.5-flash'
#         })
        
#     except Exception as e:
#         print(f"❌ Error: {str(e)}")
#         return jsonify({
#             'success': False, 
#             'error': f'Generation failed: {str(e)}'
#         }), 500

# def extract_between_tags(html, start_tag, end_tag):
#     """Extract content between HTML tags"""
#     try:
#         start = html.find(start_tag)
#         end = html.find(end_tag)
#         if start != -1 and end != -1:
#             return html[start + len(start_tag):end].strip()
#     except:
#         pass
#     return None

# def generate_backend_code(project_type, project_name):
#     """Generate simple Flask backend based on project type"""
#     backend_template = f"""# Flask Backend for {project_name}
# from flask import Flask, jsonify, request
# from flask_cors import CORS

# app = Flask(__name__)
# CORS(app)

# # Sample data storage (use database in production)
# data_store = []

# @app.route('/api/data', methods=['GET'])
# def get_data():
#     return jsonify({{'data': data_store, 'count': len(data_store)}})

# @app.route('/api/data', methods=['POST'])
# def add_data():
#     new_data = request.json
#     data_store.append(new_data)
#     return jsonify({{'success': True, 'message': 'Data added successfully'}}), 201

# @app.route('/api/health', methods=['GET'])
# def health():
#     return jsonify({{'status': 'healthy', 'project': '{project_name}'}})

# if __name__ == '__main__':
#     print('🚀 Backend running on http://localhost:5000')
#     app.run(debug=True, port=5000)
# """
#     return backend_template

# @app.route('/api/health', methods=['GET'])
# def health_check():
#     """Check if server is running"""
#     return jsonify({
#         'status': 'healthy', 
#         'message': 'Gemini-powered AI Website Generator is running!',
#         'model': 'gemini-1.5-flash',
#         'library_version': genai.__version__
#     })

# @app.route('/api/test-gemini', methods=['GET'])
# def test_gemini():
#     """Test if Gemini API is working"""
#     try:
#         response = model.generate_content("Say 'Hello! Gemini is working!' in one sentence.")
#         return jsonify({
#             'success': True,
#             'response': response.text,
#             'message': '✅ Gemini API is connected and working!',
#             'library_version': genai.__version__
#         })
#     except Exception as e:
#         return jsonify({
#             'success': False,
#             'error': str(e),
#             'message': '❌ Gemini API connection failed. Check your API key.'
#         }), 500

# if __name__ == '__main__':
#     print("=" * 60)
#     print("🚀 AI Website Generator Backend Starting...")
#     print("🤖 Using: Google Gemini 1.5 Flash (FREE)")
#     print(f"📦 Library Version: {genai.__version__}")
#     print("📡 Server: http://localhost:5000")
#     print("🔑 API Key:", "✅ Set" if GEMINI_API_KEY else "❌ Not set")
#     print("=" * 60)
#     print("\n💡 Test Gemini: http://localhost:5000/api/test-gemini\n")
#     app.run(debug=True, port=5000)

# # AI Website Generator Backend - Using FREE Google Gemini (Latest API)
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import google.generativeai as genai
# from dotenv import load_dotenv
# import os
# import pathlib
# import requests

# # Load environment variables from .env file
# load_dotenv()

# app = Flask(__name__)
# CORS(app)

# # Get API key from .env file
# GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
# NETLIFY_BUILD_HOOK = os.getenv('NETLIFY_BUILD_HOOK')  # Netlify build hook URL
# NETLIFY_SITE_URL = os.getenv('NETLIFY_SITE_URL')      # Your public site URL, e.g. https://my-app.netlify.app

# BASE_DIR = pathlib.Path(__file__).resolve().parent
# GENERATED_ROOT = BASE_DIR / "generated_projects"
# GENERATED_ROOT.mkdir(exist_ok=True)

# if not GEMINI_API_KEY:
#     print("❌ ERROR: GEMINI_API_KEY not found in .env file!")
#     print("💡 Create a .env file in the backend folder with:")
#     print("   GEMINI_API_KEY=your-api-key-here")
#     exit(1)
# else:
#     print(f"✅ API Key loaded: {GEMINI_API_KEY[:10]}...")

# # Configure Gemini API
# genai.configure(api_key=GEMINI_API_KEY)

# # Use the latest API
# model = genai.GenerativeModel('models/gemini-2.5-flash')


# @app.route('/api/generate', methods=['POST'])
# def generate_code():
#     """Generate website code using FREE Gemini AI"""
#     try:
#         data = request.json
#         project_name = data.get('projectName', 'Website')
#         project_type = data.get('projectType', 'landing')
#         description = data.get('description', '')
#         tech_stack = data.get('techStack', [])

#         # Create detailed prompt for Gemini
#         prompt = f"""
# You are an expert full-stack web developer. Generate complete, production-ready code.

# PROJECT DETAILS:
# - Name: {project_name}
# - Type: {project_type}
# - Description: {description}
# - Tech Stack: {', '.join(tech_stack) if tech_stack else 'HTML, CSS, JavaScript'}

# REQUIREMENTS:
# 1. Generate a complete HTML file with embedded CSS and JavaScript
# 2. Use modern, clean design with gradients and animations
# 3. Make it fully responsive (mobile-friendly)
# 4. Include proper semantic HTML5
# 5. Add interactive features with JavaScript
# 6. Use beautiful color schemes (purple/blue gradients preferred)
# 7. Make sure all code is production-ready and well-commented
# 8. In the JavaScript (<script>) section, use fetch() to retrieve live data from a public REST API (e.g. jsonplaceholder.typicode.com or fakestoreapi.com) and render it on the site.

# OUTPUT FORMAT:
# Return ONLY the complete HTML code (including <style> and <script> tags).
# No explanations, just the code starting with <!DOCTYPE html>

# Generate the code now:
# """

#         # Call Gemini API
#         print(f"🤖 Calling Gemini API for: {project_name}")
#         response = model.generate_content(prompt)
#         generated_code = response.text or ""

#         # Clean up the response (remove markdown fences if present)
#         generated_code = generated_code.replace("``````", "").strip()

#         # Parse into sections (for frontend tabs)
#         html_code = generated_code
#         css_code = extract_between_tags(generated_code, '<style>', '</style>')
#         js_code = extract_between_tags(generated_code, '<script>', '</script>')

#         # Save project to disk for deployment
#         safe_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in project_name.strip() or "website")
#         project_dir = GENERATED_ROOT / safe_name
#         save_project_to_disk(project_dir, html_code, css_code, js_code)
#         print(f"✅ Code generated and saved in: {project_dir}")

#         print("✅ Code generated successfully!")

#         return jsonify({
#             'success': True,
#             'code': {
#                 'html': html_code,
#                 'css': css_code if css_code else '/* CSS is embedded in HTML */',
#                 'js': js_code if js_code else '// JavaScript is embedded in HTML',
#                 'backend': generate_backend_code(project_type, project_name)
#             },
#             'projectName': project_name,
#             'model': 'gemini-1.5-flash'
#         })

#     except Exception as e:
#         print(f"❌ Error: {str(e)}")
#         return jsonify({
#             'success': False,
#             'error': f'Generation failed: {str(e)}'
#         }), 500


# def save_project_to_disk(project_dir: pathlib.Path, html_code: str, css_code: str, js_code: str):
#     """Save generated project files into a folder so Netlify can build them."""
#     project_dir.mkdir(parents=True, exist_ok=True)

#     # Save index.html as returned by Gemini
#     index_path = project_dir / "index.html"
#     with index_path.open("w", encoding="utf-8") as f:
#         f.write(html_code or "<!-- empty -->")

#     # Optional separate files
#     (project_dir / "style.css").write_text(css_code or "/* CSS is embedded in index.html */", encoding="utf-8")
#     (project_dir / "app.js").write_text(js_code or "// JS is embedded in index.html", encoding="utf-8")


# def extract_between_tags(html, start_tag, end_tag):
#     """Extract content between HTML tags"""
#     try:
#         start = html.find(start_tag)
#         end = html.find(end_tag)
#         if start != -1 and end != -1:
#             return html[start + len(start_tag):end].strip()
#     except Exception:
#         pass
#     return None


# def generate_backend_code(project_type, project_name):
#     """Generate simple Flask backend based on project type"""
#     backend_template = f"""# Flask Backend for {project_name}
# from flask import Flask, jsonify, request
# from flask_cors import CORS

# app = Flask(__name__)
# CORS(app)

# # Sample data storage (use database in production)
# data_store = []

# @app.route('/api/data', methods=['GET'])
# def get_data():
#     return jsonify({{'data': data_store, 'count': len(data_store)}})

# @app.route('/api/data', methods=['POST'])
# def add_data():
#     new_data = request.json
#     data_store.append(new_data)
#     return jsonify({{'success': True, 'message': 'Data added successfully'}}), 201

# @app.route('/api/health', methods=['GET'])
# def health():
#     return jsonify({{'status': 'healthy', 'project': '{project_name}'}})

# if __name__ == '__main__':
#     print('🚀 Backend running on http://localhost:5000')
#     app.run(debug=True, port=5000)
# """
#     return backend_template


# @app.route('/api/deploy', methods=['POST'])
# def deploy_project():
#     """Trigger Netlify build hook to deploy the site."""
#     try:
#         if not NETLIFY_BUILD_HOOK or not NETLIFY_SITE_URL:
#             return jsonify({
#                 "success": False,
#                 "error": "NETLIFY_BUILD_HOOK or NETLIFY_SITE_URL not configured in .env"
#             }), 500

#         data = request.json or {}
#         project_name = data.get("projectName") or "website"
#         safe_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in project_name.strip())
#         project_dir = GENERATED_ROOT / safe_name

#         if not project_dir.exists():
#             return jsonify({
#                 "success": False,
#                 "error": f"Project folder not found for '{safe_name}'. Generate code first."
#             }), 400

#         print(f"🚀 Triggering Netlify build hook for project: {safe_name}")
#         resp = requests.post(NETLIFY_BUILD_HOOK, json={})
#         if resp.status_code not in (200, 201, 202):
#             return jsonify({
#                 "success": False,
#                 "error": f"Netlify build hook failed with status {resp.status_code}"
#             }), 500

#         return jsonify({
#             "success": True,
#             "message": "Deployment triggered successfully.",
#             "deployUrl": NETLIFY_SITE_URL
#         })
#     except Exception as e:
#         print("Deploy error:", e)
#         return jsonify({
#             "success": False,
#             "error": str(e)
#         }), 500


# @app.route('/api/health', methods=['GET'])
# def health_check():
#     """Check if server is running"""
#     return jsonify({
#         'status': 'healthy',
#         'message': 'Gemini-powered AI Website Generator is running!',
#         'model': 'gemini-1.5-flash',
#         'library_version': genai.__version__
#     })


# @app.route('/api/test-gemini', methods=['GET'])
# def test_gemini():
#     """Test if Gemini API is working"""
#     try:
#         response = model.generate_content("Say 'Hello! Gemini is working!' in one sentence.")
#         return jsonify({
#             'success': True,
#             'response': response.text,
#             'message': '✅ Gemini API is connected and working!',
#             'library_version': genai.__version__
#         })
#     except Exception as e:
#         return jsonify({
#             'success': False,
#             'error': str(e),
#             'message': '❌ Gemini API connection failed. Check your API key.'
#         }), 500


# if __name__ == '__main__':
#     print("=" * 60)
#     print("🚀 AI Website Generator Backend Starting...")
#     print("🤖 Using: Google Gemini 1.5 Flash (FREE)")
#     print(f"📦 Library Version: {genai.__version__}")
#     print("📡 Server: http://localhost:5000")
#     print("🔑 API Key:", "✅ Set" if GEMINI_API_KEY else "❌ Not set")
#     print("🔗 NETLIFY_BUILD_HOOK:", "✅ Set" if NETLIFY_BUILD_HOOK else "❌ Not set")
#     print("🔗 NETLIFY_SITE_URL:", NETLIFY_SITE_URL or "❌ Not set")
#     print("=" * 60)
#     print("\n💡 Test Gemini: http://localhost:5000/api/test-gemini\n")
#     app.run(debug=True, port=5000)
# AI Website Generator Backend - Using FREE Google Gemini (Latest API)
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import os
import pathlib
import requests
import shutil

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Get API key and Netlify config from .env
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
NETLIFY_BUILD_HOOK = os.getenv('NETLIFY_BUILD_HOOK')   # Netlify build hook URL
NETLIFY_SITE_URL = os.getenv('NETLIFY_SITE_URL')       # e.g. https://my-app.netlify.app

BASE_DIR = pathlib.Path(__file__).resolve().parent
GENERATED_ROOT = BASE_DIR / "generated_projects"
GENERATED_ROOT.mkdir(exist_ok=True)
DEPLOY_TARGET = BASE_DIR / "deploy_target"
DEPLOY_TARGET.mkdir(exist_ok=True)

if not GEMINI_API_KEY:
    print("❌ ERROR: GEMINI_API_KEY not found in .env file!")
    print("💡 Create a .env file in the backend folder with:")
    print("   GEMINI_API_KEY=your-api-key-here")
    exit(1)
else:
    print(f"✅ API Key loaded: {GEMINI_API_KEY[:10]}...")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Use the latest API
model = genai.GenerativeModel('models/gemini-2.5-flash')


@app.route('/api/generate', methods=['POST'])
def generate_code():
    """Generate website code using FREE Gemini AI"""
    try:
        data = request.json
        project_name = data.get('projectName', 'Website')
        project_type = data.get('projectType', 'landing')
        description = data.get('description', '')
        tech_stack = data.get('techStack', [])

        # Create detailed prompt for Gemini
        prompt = f"""
You are an expert full-stack web developer. Generate complete, production-ready code.

PROJECT DETAILS:
- Name: {project_name}
- Type: {project_type}
- Description: {description}
- Tech Stack: {', '.join(tech_stack) if tech_stack else 'HTML, CSS, JavaScript'}

REQUIREMENTS:
1. Generate a complete SINGLE-PAGE HTML file with embedded CSS and JavaScript.
2. The page must have a fixed navigation bar at the top with links like "Home", "About", "Services", "Contact".
3. Each navigation link must scroll to a full-screen section on the SAME page using anchor links (e.g. <a href="#about"> and <section id="about">).
4. Use smooth scrolling between sections (CSS scroll-behavior: smooth on the html or body element).
5. Use a modern, clean design with gradients, glassmorphism, and subtle animations on hover/scroll.
6. Make it fully responsive (mobile-friendly) with a hamburger menu on small screens.
7. Include proper semantic HTML5 structure (header, main, section, footer, etc.).
8. Add interactive features with JavaScript (e.g. animated nav highlight on scroll, reveal-on-scroll effects, API data cards).
9. Use a beautiful color scheme (purple/blue gradients preferred).
10. In the JavaScript (<script>) section, use fetch() to retrieve live data from a public REST API (e.g. jsonplaceholder.typicode.com or fakestoreapi.com) and render it in one of the sections as cards.
11. Include all CSS inside a single <style> tag in the <head>.
12. Include all JavaScript inside a single <script> tag at the end of the <body>.
13. Do NOT use any external CSS or JS libraries (no Bootstrap, no Tailwind, no CDN links).
14. If you include any <img> tags, they MUST be directly relevant to the project type and description (e.g. SaaS dashboards for a SaaS app, fitness images for a gym site, etc.). Do NOT use fashion, clothing, model, or generic ecommerce product photos unless the project itself is about clothing or fashion.
15. If you are not sure which images are relevant, avoid <img> tags and instead use CSS gradients, shapes, icons, or illustration-style sections.
16. Write clear, concise, grammatically correct marketing copy for each section that matches the project description. Avoid lorem ipsum or generic filler text.

OUTPUT FORMAT:
Return ONLY the complete HTML code (including <style> and <script> tags).
No explanations, just the code starting with <!DOCTYPE html>.

Generate the code now:
"""

#         prompt = f"""
# You are an expert full-stack web developer. Generate complete, production-ready code.

# PROJECT DETAILS:
# - Name: {project_name}
# - Type: {project_type}
# - Description: {description}
# - Tech Stack: {', '.join(tech_stack) if tech_stack else 'HTML, CSS, JavaScript'}

# REQUIREMENTS:
# 1. Generate a complete HTML file with embedded CSS and JavaScript
# 2. Use modern, clean design with gradients and animations
# 3. Make it fully responsive (mobile-friendly)
# 4. Include proper semantic HTML5
# 5. Add interactive features with JavaScript
# 6. Use beautiful color schemes (purple/blue gradients preferred)
# 7. Make sure all code is production-ready and well-commented
# 8. In the JavaScript (<script>) section, use fetch() to retrieve live data from a public REST API (e.g. jsonplaceholder.typicode.com or fakestoreapi.com) and render it on the site.

# OUTPUT FORMAT:
# Return ONLY the complete HTML code (including <style> and <script> tags).
# No explanations, just the code starting with <!DOCTYPE html>

# Generate the code now:
# """
        # Call Gemini API
        print(f"🤖 Calling Gemini API for: {project_name}")
        response = model.generate_content(prompt)
        generated_code = response.text or ""

        # Clean up the response (remove markdown fences if present)
        # generated_code = generated_code.replace("``````", "").strip()
        for fence in ["```html", "```HTML", "```"]:
           generated_code = generated_code.replace(fence, "")
        generated_code = generated_code.strip()
        # Parse into sections (for frontend tabs)
        html_code = generated_code
        css_code = extract_between_tags(generated_code, '<style>', '</style>')
        js_code = extract_between_tags(generated_code, '<script>', '</script>')

        # Save project to disk for deployment
        safe_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in project_name.strip() or "website")
        project_dir = GENERATED_ROOT / safe_name
        save_project_to_disk(project_dir, html_code, css_code, js_code)
        print(f"✅ Code generated and saved in: {project_dir}")

        print("✅ Code generated successfully!")

        return jsonify({
            'success': True,
            'code': {
                'html': html_code,
                'css': css_code if css_code else '/* CSS is embedded in HTML */',
                'js': js_code if js_code else '// JavaScript is embedded in HTML',
                'backend': generate_backend_code(project_type, project_name)
            },
            'projectName': project_name,
            'model': 'gemini-1.5-flash'
        })

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Generation failed: {str(e)}'
        }), 500


def save_project_to_disk(project_dir: pathlib.Path, html_code: str, css_code: str, js_code: str):
    """Save generated project files into a folder so Netlify can build them."""
    project_dir.mkdir(parents=True, exist_ok=True)

    # Save index.html as returned by Gemini
    index_path = project_dir / "index.html"
    with index_path.open("w", encoding="utf-8") as f:
        f.write(html_code or "<!-- empty -->")

    # Optional separate files
    (project_dir / "style.css").write_text(css_code or "/* CSS is embedded in index.html */", encoding="utf-8")
    (project_dir / "app.js").write_text(js_code or "// JS is embedded in index.html", encoding="utf-8")


def extract_between_tags(html, start_tag, end_tag):
    """Extract content between HTML tags"""
    try:
        start = html.find(start_tag)
        end = html.find(end_tag)
        if start != -1 and end != -1:
            return html[start + len(start_tag):end].strip()
    except Exception:
        pass
    return None


def generate_backend_code(project_type, project_name):
    """Generate simple Flask backend based on project type"""
    backend_template = f"""# Flask Backend for {project_name}
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Sample data storage (use database in production)
data_store = []

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({{'data': data_store, 'count': len(data_store)}})

@app.route('/api/data', methods=['POST'])
def add_data():
    new_data = request.json
    data_store.append(new_data)
    return jsonify({{'success': True, 'message': 'Data added successfully'}}), 201

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({{'status': 'healthy', 'project': '{project_name}'}})

if __name__ == '__main__':
    print('🚀 Backend running on http://localhost:5000')
    app.run(debug=True, port=5000)
"""
    return backend_template


@app.route('/api/deploy', methods=['POST'])
def deploy_project():
    """Copy selected project into deploy_target/ and trigger Netlify build hook."""
    try:
        if not NETLIFY_BUILD_HOOK or not NETLIFY_SITE_URL:
            return jsonify({
                "success": False,
                "error": "NETLIFY_BUILD_HOOK or NETLIFY_SITE_URL not configured in .env"
            }), 500

        data = request.json or {}
        project_name = data.get("projectName") or "website"
        safe_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in project_name.strip())
        project_dir = GENERATED_ROOT / safe_name

        if not project_dir.exists():
            return jsonify({
                "success": False,
                "error": f"Project folder not found for '{safe_name}'. Generate code first."
            }), 400

        # 1) Clear old deploy_target files
        for item in DEPLOY_TARGET.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

        # 2) Copy this project into deploy_target/
        for item in project_dir.iterdir():
            dest = DEPLOY_TARGET / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        print(f"📦 Copied project '{safe_name}' to deploy_target/")

        # 3) Trigger Netlify build hook
        print("🚀 Triggering Netlify build hook")
        resp = requests.post(NETLIFY_BUILD_HOOK, json={})
        if resp.status_code not in (200, 201, 202):
            return jsonify({
                "success": False,
                "error": f"Netlify build hook failed with status {resp.status_code}"
            }), 500

        return jsonify({
            "success": True,
            "message": f"Deployment triggered successfully for project '{safe_name}'.",
            "deployUrl": NETLIFY_SITE_URL
        })
    except Exception as e:
        print("Deploy error:", e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Check if server is running"""
    return jsonify({
        'status': 'healthy',
        'message': 'Gemini-powered AI Website Generator is running!',
        'model': 'gemini-1.5-flash',
        'library_version': genai.__version__
    })


@app.route('/api/test-gemini', methods=['GET'])
def test_gemini():
    """Test if Gemini API is working"""
    try:
        response = model.generate_content("Say 'Hello! Gemini is working!' in one sentence.")
        return jsonify({
            'success': True,
            'response': response.text,
            'message': '✅ Gemini API is connected and working!',
            'library_version': genai.__version__
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '❌ Gemini API connection failed. Check your API key.'
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 AI Website Generator Backend Starting...")
    print("🤖 Using: Google Gemini 1.5 Flash (FREE)")
    print(f"📦 Library Version: {genai.__version__}")
    print("📡 Server: http://localhost:5000")
    print("🔑 API Key:", "✅ Set" if GEMINI_API_KEY else "❌ Not set")
    print("🔗 NETLIFY_BUILD_HOOK:", "✅ Set" if NETLIFY_BUILD_HOOK else "❌ Not set")
    print("🔗 NETLIFY_SITE_URL:", NETLIFY_SITE_URL or "❌ Not set")
    print("=" * 60)
    print("\n💡 Test Gemini: http://localhost:5000/api/test-gemini\n")
    app.run(debug=True, port=5000)
