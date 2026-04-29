let lastGeneratedProjectName = "";

// =====================
// DOM ELEMENTS
// =====================
document.addEventListener('DOMContentLoaded', () => {

  const generateBtn = document.getElementById('generateBtn');
  const outputPanel = document.getElementById('outputPanel');
  const projectNameInput = document.getElementById('projectName');
  const projectTypeSelect = document.getElementById('projectType');
  const descriptionTextarea = document.getElementById('description');
  const existingProjectsGroup = document.getElementById('existingProjectsGroup');
  const existingProjectsSelect = document.getElementById('existingProjects');
  const loadProjectBtn = document.getElementById('loadProjectBtn');
  // feature checkboxes
  const optDatabase = document.getElementById('optDatabase');
  const optAuth = document.getElementById('optAuth');
  const optAdmin = document.getElementById('optAdmin');
  const optContact = document.getElementById('optContact');
  const optUpload = document.getElementById('optUpload');
  const tabButtons = document.querySelectorAll('.tab-button');
  const tabContents = document.querySelectorAll('.tab-content');
  const downloadBtn = document.getElementById('downloadBtn');
  const themeToggle = document.getElementById('themeToggle');
  const deployBtn = document.getElementById('deployBtn');
  const pushGithubBtn = document.getElementById('pushGithubBtn');
  const agentBtn = document.getElementById('agentBtn');
  const agentModal = document.getElementById('agentModal');
  const agentCloseBtn = document.getElementById('agentCloseBtn');
  const agentSendBtn = document.getElementById('agentSendBtn');
  const agentInput = document.getElementById('agentInput');
  const agentMessages = document.getElementById('agentMessages');
  const agentImageInput = document.getElementById('agentImageInput');

  // API base: if running on VSCode Live Server (port 5500), point to the backend Flask server on 5000.
  const apiBaseUrl = (() => {
    const { hostname, port } = window.location;
    if ((hostname === '127.0.0.1' || hostname === 'localhost') && port === '5500') {
      return 'http://127.0.0.1:5000';
    }
    return window.location.origin;
  })();

  let isMutating = false;
  let lastStableCode = null;

  const getAgentHistoryKey = () => 'nova_modifying_agent_chat_history_' + (lastGeneratedProjectName || 'default');

  function loadAgentHistory() {
    try {
      const raw = localStorage.getItem(getAgentHistoryKey());
      if (!raw) return;
      const items = JSON.parse(raw);
      if (!Array.isArray(items)) return;
      items.forEach(item => {
        appendAgentMessage(item.text, item.type, item.imageData, false);
      });
    } catch (e) {
      console.warn('Failed to load Copilot history', e);
    }
  }

  function saveAgentHistory() {
    try {
      const messages = Array.from(agentMessages.querySelectorAll('.message')).map(msg => {
        const type = msg.classList.contains('agent') ? 'agent' : 'user';
        const text = msg.querySelector('div')?.textContent || '';
        const img = msg.querySelector('img');
        const imageData = img ? img.src : null;
        return { text, type, imageData };
      });
      localStorage.setItem(getAgentHistoryKey(), JSON.stringify(messages));
    } catch (e) {
      console.warn('Failed to save Copilot history', e);
    }
  }

  function clearAgentHistory() {
    localStorage.removeItem(getAgentHistoryKey());
  }

  function switchAgentHistory() {
    // Clear current messages
    agentMessages.innerHTML = '';
    // Load history for new project
    loadAgentHistory();
  }

  loadAgentHistory();

  
  // GitHub Modal elements
  const githubModal = document.getElementById('githubModal');
  const githubCloseBtn = document.getElementById('githubCloseBtn');
  const githubUsername = document.getElementById('githubUsername');
  const githubRepoName = document.getElementById('githubRepoName');
  const githubToken = document.getElementById('githubToken');
  const githubSubmitBtn = document.getElementById('githubSubmitBtn');
  const githubCancelBtn = document.getElementById('githubCancelBtn');
  const githubMessage = document.getElementById('githubMessage');
  
  const previewFrame = document.getElementById('preview-frame');
  let designInsightsPanel = null;

  // new UI elements
  const sidebarButtons = document.querySelectorAll('.sidebar-button');
  const panels = document.querySelectorAll('.panel');
  const botMessages = document.getElementById('botMessages');
  const botInput = document.getElementById('botInput');
  const botSendBtn = document.getElementById('botSendBtn');
  const botClearBtn = document.getElementById('botClearBtn');
  const botImageInput = document.getElementById('botImageInput');
  const botSuggestions = document.getElementById('botSuggestions');
  const uploadInput = document.getElementById('uploadInput');
  const uploadList = document.getElementById('uploadList');

  // =====================
  // BACKEND ENDPOINTS
  // =====================
  const GENERATOR_API = "http://localhost:5000";
  const PROJECT_BACKEND_API = "http://localhost:5001/api/data";

  function ensureDesignInsightsPanel() {
    if (designInsightsPanel) return designInsightsPanel;
    const tabs = outputPanel?.querySelector('.tabs');
    if (!tabs) return null;

    const tabButton = document.createElement('button');
    tabButton.className = 'tab-button';
    tabButton.dataset.tab = 'blueprint';
    tabButton.textContent = 'Blueprint';
    tabs.appendChild(tabButton);
    tabButton.addEventListener('click', () => setActiveCodeTab('blueprint'));

    const tab = document.createElement('div');
    tab.className = 'tab-content';
    tab.id = 'blueprint-tab';
    tab.innerHTML = `
      <div class="code-toolbar">
        <span class="file-name">design-blueprint.json</span>
        <button class="copy-button" data-target="blueprint-code">Copy</button>
      </div>
      <pre><code id="blueprint-code" class="language-json">{}</code></pre>
    `;
    outputPanel.appendChild(tab);

    const copyBtn = tab.querySelector('.copy-button');
    if (copyBtn) {
      copyBtn.addEventListener('click', async () => {
        const target = document.getElementById(copyBtn.dataset.target);
        const text = target ? target.textContent : '';
        if (!text) return;
        try {
          await navigator.clipboard.writeText(text);
          notify('Blueprint copied', 'success');
        } catch (err) {
          notify('Could not copy blueprint', 'error');
        }
      });
    }

    designInsightsPanel = tab;
    return tab;
  }

  function updateGenerationInsights(code) {
    const panel = ensureDesignInsightsPanel();
    if (!panel) return;
    const blueprintEl = document.getElementById('blueprint-code');
    const payload = {
      blueprint: code?.blueprint || null,
      analysis: code?.analysis || null,
      uiPlan: code?.uiPlan || null,
      projectStructure: code?.projectStructure || []
    };
    if (blueprintEl) {
      const text = JSON.stringify(payload, null, 2);
      blueprintEl.textContent = text;
      blueprintEl.innerHTML = Prism.highlight(text, Prism.languages.json || Prism.languages.javascript, 'json');
    }
  }

  // =====================
  // THEME TOGGLE
  // =====================
  (function setupThemeToggle() {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    let currentTheme = localStorage.getItem('theme') || (prefersDark ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', currentTheme);

    if (themeToggle) {
      themeToggle.textContent = currentTheme === 'dark' ? '☀️' : '🌙';
      themeToggle.onclick = () => {
        currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', currentTheme);
        localStorage.setItem('theme', currentTheme);
        themeToggle.textContent = currentTheme === 'dark' ? '☀️' : '🌙';
      };
    }
  })();

  // =====================
  // TAB SWITCHING (code panels)
  // =====================
  function setActiveCodeTab(tabName) {
    document.querySelectorAll('.tab-button').forEach(b => b.classList.toggle('active', b.dataset.tab === tabName));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.toggle('active', c.id === `${tabName}-tab`));
  }

  tabButtons.forEach(button => {
    button.addEventListener('click', () => {
      setActiveCodeTab(button.dataset.tab);
    });
  });

  // =====================
  // PANEL SWITCHING (sidebar)
  // =====================
  function showPanel(id) {
    panels.forEach(p => p.classList.toggle('hidden', p.id !== id));
    sidebarButtons.forEach(b => b.classList.toggle('active', b.dataset.panel === id));
  }

  sidebarButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      showPanel(btn.dataset.panel);
    });
  });
  // default
  showPanel('home-panel');

  // =====================
  // SIDEBAR COLLAPSE
  // =====================
  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');
  function setSidebarCollapsed(collapsed) {
    if (collapsed) {
      sidebar.classList.add('collapsed');
      sidebarToggle.textContent = '▶';
      localStorage.setItem('sidebarCollapsed', '1');
    } else {
      sidebar.classList.remove('collapsed');
      sidebarToggle.textContent = '◀';
      localStorage.removeItem('sidebarCollapsed');
    }
  }
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
      setSidebarCollapsed(!sidebar.classList.contains('collapsed'));
    });
    // restore state
    setSidebarCollapsed(!!localStorage.getItem('sidebarCollapsed'));
  }

  // links that jump to panel
  document.body.addEventListener('click', e => {
    const link = e.target.closest('[data-panel-link]');
    if (link) {
      e.preventDefault();
      const target = link.getAttribute('data-panel-link');
      showPanel(target);
    }
  });

 // =====================
// STABLE PREVIEW ENGINE (FIXED)
// =====================
function updatePreview(html, css = "", js = "") {
  if (!previewFrame || !html) return;

  try {
    previewFrame.setAttribute(
      "sandbox",
      "allow-scripts allow-forms allow-modals allow-same-origin"
    );

    const previewGuard = `
<script>
window.__IS_PREVIEW__ = true;
const originalFetch = window.fetch;
window.fetch = function(...args){
  if(args[0] && args[0].includes("localhost:5001")){
    return Promise.resolve({
      ok:true,
      json: async()=>[],
      text: async()=> ""
    });
  }
  return originalFetch(...args);
};

// helper to detect absolute/external URLs
const urlPattern = /^(https?:\\/\\/)?([\\w.-]+)\\.([a-z]{2,})/i;
function isExternalUrl(url) {
  if (!url) return false;
  const trimmed = url.trim();
  return urlPattern.test(trimmed);
}

// intercept link clicks and block all navigation (to avoid loading NovaForge UI in preview)
document.addEventListener('click', e => {
  const link = e.target && e.target.closest ? e.target.closest('a') : null;
  if (!link) return;
  const href = link.getAttribute('href') || '';
  // allow in-page anchors (hash links)
  if (!href || href.startsWith('#') || href.startsWith('javascript:')) return;
  e.preventDefault();
  e.stopImmediatePropagation();
  alert('Navigation blocked in preview mode. This link would navigate to: ' + href + '\\n\\nUse the generator to create full multi-page sites or implement client-side routing for SPAs.');
}, true);

// block all form submissions
document.addEventListener('submit', e => {
  e.preventDefault();
  e.stopImmediatePropagation();
  console.warn('Blocked preview form submission');
}, true);

// block window.open and location navigation entirely
window.open = function(url) {
  console.warn('Blocked preview window.open to', url);
  return null;
};

const _assign = window.location.assign.bind(window.location);
const _replace = window.location.replace.bind(window.location);
window.location.assign = function(url) {
  console.warn('Blocked preview location.assign to', url);
};
window.location.replace = function(url) {
  console.warn('Blocked preview location.replace to', url);
};

// override top/parent references so they point to the iframe itself
Object.defineProperty(window, 'top', { get: () => window });
Object.defineProperty(window, 'parent', { get: () => window });
</script>
<base href="about:blank" target="_self">
`;

    const lower = html.trim().toLowerCase();
    const isFull =
      lower.startsWith("<!doctype") || lower.startsWith("<html");

    let finalDoc = html;

    if (isFull) {

      // Inject inside <head> safely (case insensitive)
      const headMatch = html.match(/<head[^>]*>/i);

      if (headMatch) {
        finalDoc = html.replace(
          headMatch[0],
          headMatch[0] + previewGuard
        );
      } else {
        // Inject before closing html
        finalDoc = html.replace(
          /<\/html>/i,
          previewGuard + "</html>"
        );
      }

      if (css) {
        finalDoc = finalDoc.replace(/<link[^>]+href="styles\/main\.css"[^>]*>/i, `<style>${css}</style>`);
        finalDoc = finalDoc.replace(/<link[^>]+href="style\.css"[^>]*>/i, `<style>${css}</style>`);
      }
      if (js) {
        finalDoc = finalDoc.replace(/<script[^>]+src="app\.js"[^>]*><\/script>/i, `<script>${js}</script>`);
      }

    } else {
      finalDoc = `
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>${css || ""}</style>
${previewGuard}
</head>
<body>
${html}
<script>${js || ""}</script>
</body>
</html>
`;
    }

    function sanitizePreviewHtml(htmlString) {
      try {
        const parser = new DOMParser();
        const doc = parser.parseFromString(htmlString, "text/html");
        const doctypeMatch = htmlString.match(/<!doctype[^>]*>/i);
        const doctype = doctypeMatch ? doctypeMatch[0] : "<!DOCTYPE html>";

        // disable navigation links to external sites (allow relative/internal routing)
        const urlPattern = /^(https?:\/\/)?([\w.-]+)\.([a-z]{2,})/i;
        function isExternalHref(url) {
          if (!url) return false;
          const trimmed = url.trim();
          return urlPattern.test(trimmed);
        }

        doc.querySelectorAll("a[href]").forEach(a => {
          const href = a.getAttribute("href") || "";
          if (!href || href.startsWith("#") || href.startsWith("javascript:")) return;
          if (!isExternalHref(href)) return; // keep relative / internal links working
          a.setAttribute("data-preview-href", href);
          a.setAttribute("href", "#");
          a.setAttribute("onclick", "return false");
        });

        // disable form submissions that would navigate to external URLs
        doc.querySelectorAll("form").forEach(f => {
          const action = f.getAttribute("action");
          if (action && isExternalHref(action)) {
            f.setAttribute("data-preview-action", action);
            f.setAttribute("action", "#");
            f.setAttribute("onsubmit", "return false");
          }
        });

        return `${doctype}\n${doc.documentElement.outerHTML}`;
      } catch (e) {
        console.warn("Preview sanitization failed", e);
        return htmlString;
      }
    }

    previewFrame.srcdoc = sanitizePreviewHtml(finalDoc);

  } catch (err) {
    console.error("Preview engine crashed:", err);
  }
}

  // =====================
  // UI LOCK
  // =====================

  // =====================
  // FEATURE CONSTRAINTS
  // =====================
  function updateFeatureConstraints() {
    const pt = projectTypeSelect.value;
    const noBackendTypes = ['static', 'portfolio', 'blog', 'landing', 'ads'];
    const backendDisabled = noBackendTypes.includes(pt);

    if (backendDisabled) {
      [optDatabase, optAuth, optAdmin, optContact, optUpload].forEach(cb => {
        cb.checked = false;
        cb.disabled = true;
      });
    } else {
      [optDatabase, optAuth, optAdmin, optContact, optUpload].forEach(cb => cb.disabled = false);
    }

    // if any backend feature is checked and type isn't fullstack, switch to fullstack
    if (!backendDisabled && (optDatabase.checked || optAuth.checked || optAdmin.checked || optContact.checked || optUpload.checked) && pt !== 'fullstack') {
      projectTypeSelect.value = 'fullstack';
    }
  }

  [projectTypeSelect, optDatabase, optAuth, optAdmin, optContact, optUpload].forEach(cb => {
    if (cb) cb.addEventListener('change', updateFeatureConstraints);
  });

  // run once to set initial state
  updateFeatureConstraints();


  function lockUI(lock, mode = "generate") {
    isMutating = lock;
    generateBtn.disabled = lock;
    agentBtn.disabled = lock;

    if (mode === "feature") {
      agentBtn.textContent = lock ? "🤖 Updating..." : "🤖 Copilot";
    } else {
      generateBtn.textContent = lock ? "⚙️ Generating..." : "✨ Generate Website";
    }
  }

  // =====================
  // RESPONSE NORMALIZER
  // =====================
  function normalizeCodeResponse(newCode) {
    if (!lastStableCode) return newCode;
    return {
      html: newCode.html ?? lastStableCode.html,
      css: newCode.css ?? lastStableCode.css,
      js: newCode.js ?? lastStableCode.js,
      backend: newCode.backend ?? lastStableCode.backend,
      blueprint: newCode.blueprint ?? lastStableCode.blueprint,
      analysis: newCode.analysis ?? lastStableCode.analysis,
      uiPlan: newCode.uiPlan ?? lastStableCode.uiPlan,
      projectStructure: newCode.projectStructure ?? lastStableCode.projectStructure,
      files: newCode.files ?? lastStableCode.files
    };
  }

  // =====================
  // GENERATE PROJECT
  // =====================
  async function generateProject() {
    const projectName = projectNameInput.value || 'My Website';
    const projectType = projectTypeSelect.value;
    const description = descriptionTextarea.value;
    // collect features
    const features = [];
    if (projectTypeSelect.value === 'static') features.push('Static Site');
    if (projectTypeSelect.value === 'fullstack') features.push('Full-Stack App');
    [optDatabase, optAuth, optAdmin, optContact, optUpload].forEach(cb => {
      if (cb && cb.checked) features.push(cb.value);
    });

    if (!description.trim()) {
      alert("Please describe your project!");
      return;
    }

    lockUI(true, "generate");

    try {
      const res = await fetch(`${GENERATOR_API}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ projectName, projectType, description, features })
      });

      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      lastStableCode = data.code;
      lastGeneratedProjectName = projectName;

      // Switch agent chat history for new project
      switchAgentHistory();

      // persist to storage so we can restore later
      try {
        localStorage.setItem('nova_lastProject', JSON.stringify({
          name: lastGeneratedProjectName,
          code: lastStableCode
        }));
      } catch (e) {
        console.warn('could not save project', e);
      }

      updateCodePanels(data.code);
      updateGenerationInsights(data.code);
      updatePreview(data.code.html, data.code.css, data.code.js);

      // show generator output and preview tab by default
      showPanel('generator-panel');
      setActiveCodeTab('preview');

      outputPanel.style.display = "block";
      notify("Website generated successfully", "success");
      // new project created, refresh dropdown
      refreshProjectList();

    } catch (err) {
      console.error(err);
      notify("Generation failed", "error");
    } finally {
      lockUI(false, "generate");
    }
  }

  generateBtn.addEventListener("click", e => {
    e.preventDefault();
    if (!isMutating) generateProject();
  });

  // restore last project from localStorage when page loads
  (function restoreLastProject() {
    try {
      const saved = localStorage.getItem('nova_lastProject');
      if (saved) {
        const obj = JSON.parse(saved);
        if (obj && obj.code) {
          lastStableCode = obj.code;
          lastGeneratedProjectName = obj.name || null;
          updateCodePanels(lastStableCode);
          updateGenerationInsights(lastStableCode);
          updatePreview(lastStableCode.html, lastStableCode.css, lastStableCode.js);
          // show generator output and preview tab when restoring
          showPanel('generator-panel');
          setActiveCodeTab('preview');
          outputPanel.style.display = "block";
          // Switch agent chat history for restored project
          switchAgentHistory();
          notify('Restored previous project', 'success');
        }
      }
    } catch (e) {
      console.warn('Failed to restore project from localStorage', e);
    }
  })();

  // load list of saved projects from backend (async)
  async function refreshProjectList() {
    try {
      const res = await fetch(`${GENERATOR_API}/api/projects`);
      const data = await res.json();
      if (data.success && Array.isArray(data.projects)) {
        // clear
        existingProjectsSelect.innerHTML = '<option value="">-- select project --</option>';
        data.projects.forEach(name => {
          const opt = document.createElement('option');
          opt.value = name;
          opt.textContent = name;
          existingProjectsSelect.appendChild(opt);
        });
        if (data.projects.length) {
          existingProjectsGroup.style.display = 'block';
        }
      }
    } catch (e) {
      console.warn('could not fetch project list', e);
    }
  }

  if (loadProjectBtn) {
    loadProjectBtn.addEventListener('click', async () => {
      const name = existingProjectsSelect.value;
      if (!name) return;
      lockUI(true);
      try {
        const res = await fetch(`${GENERATOR_API}/api/projects/${encodeURIComponent(name)}`);
        const data = await res.json();
        if (!data.success || !data.code) throw new Error(data.error || 'no code');
        lastStableCode = data.code;
        lastGeneratedProjectName = name;
        updateCodePanels(data.code);
        updateGenerationInsights(data.code);
        updatePreview(data.code.html, data.code.css, data.code.js);
        outputPanel.style.display = 'block';
        // store locally too
        localStorage.setItem('nova_lastProject', JSON.stringify({name, code: data.code}));
        // Switch agent chat history for loaded project
        switchAgentHistory();
        notify('Loaded project ' + name, 'success');
      } catch (err) {
        console.error(err);
        notify('Failed to load project', 'error');
      } finally {
        lockUI(false);
      }
    });
  }

  // refresh project list on load
  refreshProjectList();

  // =====================
  // BOT/IDEAS PANEL
  // =====================
  const IDEA_SEEDS = [
    {
      id: "ecommerce",
      title: "E-commerce Store",
      keywords: ["ecommerce", "e-commerce", "online store", "shop", "shopping", "cart", "checkout", "product"],
      tagline: "A focused online storefront with conversion-first flows.",
      users: [
        "Shoppers looking for a fast, trustworthy checkout",
        "Returning customers managing orders and wishlists",
        "Admins managing inventory, pricing, and promotions"
      ],
      pages: [
        "Home / category grid",
        "Product detail page",
        "Cart + checkout",
        "Account / orders / returns",
        "Search + filters",
        "FAQ + shipping policy"
      ],
      features: [
        "Product variants (size, color) and stock levels",
        "Promo codes and featured collections",
        "Reviews + ratings",
        "Saved addresses and quick re-order",
        "Email order confirmations"
      ],
      data: [
        "Product, Variant, Inventory",
        "Cart, CartItem, Order",
        "Customer, Address, Payment",
        "Promotion, Review"
      ],
      flows: [
        "Browse -> filter -> PDP -> add to cart -> checkout -> confirmation",
        "Account -> order history -> return request",
        "Admin -> add product -> set price -> publish"
      ],
      ops: [
        "Inventory alerts and low-stock rules",
        "Refunds and return management",
        "Fulfillment status updates"
      ],
      growth: [
        "SEO-friendly product URLs",
        "Abandoned cart reminder",
        "Related products and bundles"
      ],
      ideas: [
        "Subscription / refill option",
        "Live chat for pre-sale questions",
        "Gift cards and store credit"
      ],
      prompt: "Create a highly realistic, modern e-commerce website for [niche] that looks and feels like a professional, production-ready online store. Include comprehensive product listings with advanced filtering and search, detailed product pages with image galleries, reviews, and related products. Implement a fully functional shopping cart with quantity controls, persistent storage, and real-time updates. Build a secure, multi-step checkout process with address forms, payment options, and order confirmation. Add user authentication with login/register modals, account dashboards for order history and profile management. Include an admin panel for inventory management, order processing, and analytics. Use modern UI/UX with smooth animations, responsive design, loading states, progress indicators, and interactive elements. Ensure all features are working: add to cart animations, form validations, search autocomplete, wishlist functionality, and email notifications. Make it SEO-optimized with proper meta tags, fast loading, and mobile-first approach. Include trust elements like security badges, customer reviews, and live chat. The site should appear as if it's a real business with working progress bars, loading spinners, and dynamic content updates."
    },
    {
      id: "retail",
      title: "Retail Shop (Local + Online)",
      keywords: ["retail", "retail shop", "storefront", "boutique", "local store", "brick and mortar", "inventory", "pos"],
      tagline: "A hybrid retail experience that connects in-store and online.",
      users: [
        "Local shoppers checking availability before visiting",
        "Customers reserving items for pickup",
        "Store staff updating inventory and promotions"
      ],
      pages: [
        "Store homepage with featured items",
        "In-stock catalog with filters",
        "Store locator + hours",
        "Reserve / click-and-collect",
        "Events / new arrivals"
      ],
      features: [
        "Real-time stock and size availability",
        "Reserve online, pay in-store",
        "Staff picks and seasonal collections",
        "Integrated social proof and Instagram feed"
      ],
      data: [
        "Product, Inventory, StoreLocation",
        "Reservation, Customer",
        "Promotion, Event"
      ],
      flows: [
        "Find store -> browse stock -> reserve -> pickup",
        "New arrivals -> notification signup",
        "Admin -> update hours -> publish event"
      ],
      ops: [
        "Multi-location inventory sync",
        "Staff roles and approvals",
        "Promotion scheduling"
      ],
      growth: [
        "Local SEO + Google Maps embeds",
        "Email / SMS back-in-stock alerts",
        "Loyalty points for repeat visits"
      ],
      ideas: [
        "Community events calendar",
        "Consignment / trade-in flow",
        "Gift wrapping add-on"
      ],
      prompt: "Develop a sophisticated retail shop website for a local [store type] that seamlessly blends online and in-store experiences. Feature a dynamic homepage with hero banners, featured products, and promotional sections. Create an extensive product catalog with real-time inventory display, advanced filters by category/size/color, and search with autocomplete. Include store locator with interactive maps, hours display, and contact information. Implement a reserve-online-pickup system with inventory checking, reservation forms, and confirmation emails. Add sections for events, new arrivals, and staff picks with social media integration. Build user accounts for reservation history and preferences. Provide an admin dashboard for multi-location inventory management, staff scheduling, and promotion creation. Use cutting-edge design with parallax scrolling, hover effects, image zoom, and smooth transitions. Ensure all interactions work: live inventory updates, reservation confirmations, form submissions with validation, and responsive mobile layout. Include progress indicators for reservations, loading states for searches, and interactive elements throughout. Make it appear as a premium, operational retail business with professional photography, customer testimonials, and integrated payment options."
    },
    {
      id: "default",
      title: "Product / Service Website",
      keywords: [],
      tagline: "A clear, user-focused site with structured features and flows.",
      users: [
        "Primary customers who need a quick solution",
        "Returning users managing their account",
        "Admins managing content and operations"
      ],
      pages: [
        "Landing page with value prop",
        "Features / pricing",
        "FAQ + contact",
        "User account area"
      ],
      features: [
        "Clear onboarding CTA",
        "Responsive layout",
        "Testimonials and trust badges"
      ],
      data: [
        "User, Content, Plan",
        "Order / Subscription",
        "Support ticket"
      ],
      flows: [
        "Landing -> sign up -> onboarding",
        "Account -> settings -> support"
      ],
      ops: [
        "Basic CMS controls",
        "Role-based access"
      ],
      growth: [
        "SEO-ready pages",
        "Email capture"
      ],
      ideas: [
        "Referral program",
        "Live chat support"
      ],
      prompt: "Build a professional, fully functional website for [business] that demonstrates real-world quality and usability. Create an impactful landing page with compelling hero section, value propositions, and clear call-to-action buttons. Develop detailed features and pricing pages with interactive elements, testimonials, and comparison tables. Include a comprehensive FAQ section with expandable answers and a contact form with validation. Add user authentication and account management with dashboards, settings, and subscription handling. Implement modern design with smooth animations, gradient backgrounds, card layouts, and micro-interactions. Ensure all forms work with proper validation, success messages, and error handling. Add progress bars for multi-step processes, loading animations, and dynamic content updates. Make it mobile-responsive with hamburger menus, swipe gestures, and optimized layouts. Include SEO optimization, fast loading, and accessibility features. The site should feel like a legitimate business platform with working chat support, notification systems, and data persistence. Use professional color schemes, typography, and imagery to create a trustworthy, modern appearance."
    }
  ];

  function findIdeaSeed(text) {
    const lower = text.toLowerCase();
    for (const seed of IDEA_SEEDS) {
      if (!seed.keywords.length) continue;
      if (seed.keywords.some(k => lower.includes(k))) return seed;
    }
    return IDEA_SEEDS.find(s => s.id === "default");
  }

  function extractNiche(text) {
    const match = text.match(/for (a|an|the)?\s*([a-z0-9\s-]{3,})/i);
    if (match && match[2]) return match[2].trim();
    return null;
  }

  function renderSection(title, items) {
    if (!items || !items.length) return "";
    return `${title}\n- ${items.join("\n- ")}`;
  }

  function buildDetailedPrompt(seed, niche) {
    const target = niche || (seed.id === "retail" ? "your local store" : seed.id === "ecommerce" ? "your niche" : "your business");
    const title = niche ? `${seed.title} for ${niche}` : seed.title;

    const lines = [];
    lines.push(`Build a ${seed.title.toLowerCase()} website for ${target}.`);
    lines.push(`Primary goal: ${seed.tagline}`);
    lines.push(`Pages: ${seed.pages.join(", ")}.`);
    lines.push(`Core features: ${seed.features.join(", ")}.`);
    lines.push(`User flows: ${seed.flows.join("; ")}.`);
    lines.push(`Admin/Ops: ${seed.ops.join("; ")}.`);
    lines.push(`Data entities: ${seed.data.join(", ")}.`);
    lines.push(`Growth/SEO: ${seed.growth.join("; ")}.`);
    lines.push("Design: modern, mobile-first, fast loading, clear CTAs, and strong trust cues.");
    lines.push("Accessibility: semantic HTML, good contrast, keyboard-friendly components.");
    lines.push(`Brand context: ${title}.`);
    return lines.join("\n");
  }

  function buildIdeaResponse(text) {
    const seed = findIdeaSeed(text);
    const niche = extractNiche(text);
    const title = niche ? `${seed.title} for ${niche}` : seed.title;

    const lines = [];
    lines.push(`Idea Pack: ${title}`);
    lines.push(`Overview\n${seed.tagline}`);
    lines.push(renderSection("Target Users", seed.users));
    lines.push(renderSection("Core Pages", seed.pages));
    lines.push(renderSection("MVP Features", seed.features));
    lines.push(renderSection("Data Entities", seed.data));
    lines.push(renderSection("Key User Flows", seed.flows));
    lines.push(renderSection("Admin / Ops", seed.ops));
    lines.push(renderSection("Growth / SEO", seed.growth));
    lines.push(renderSection("Extra Ideas", seed.ideas));

    const detailedPrompt = buildDetailedPrompt(seed, niche);
    lines.push("Detailed Generator Prompt (copy/paste)\n" + detailedPrompt);
    lines.push("Questions to Clarify\n- What is the target customer and price range?\n- How many products or categories at launch?\n- Shipping, pickup, or both?\n- Do you need payments now or later?");

    return { response: lines.filter(Boolean).join("\n\n"), detailedPrompt };
  }

  function appendBotMessage(text, sender) {
    const div = document.createElement('div');
    div.className = 'message ' + sender;
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text;
    div.appendChild(bubble);
    botMessages.appendChild(div);
    botMessages.scrollTop = botMessages.scrollHeight;
  }

  function appendPromptAction(promptText) {
    if (!promptText) return;
    const div = document.createElement('div');
    div.className = 'message bot';
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    const text = document.createElement('div');
    text.textContent = 'Use this prompt in Generate Your Website?';
    const btn = document.createElement('button');
    btn.className = 'button-secondary';
    btn.textContent = 'OK';
    btn.dataset.action = 'use-prompt';
    btn.dataset.prompt = promptText;
    bubble.appendChild(text);
    bubble.appendChild(btn);
    div.appendChild(bubble);
    botMessages.appendChild(div);
    botMessages.scrollTop = botMessages.scrollHeight;
  }

  function appendSystemMessage(text) {
    const div = document.createElement('div');
    div.className = 'message system';
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text;
    div.appendChild(bubble);
    botMessages.appendChild(div);
    botMessages.scrollTop = botMessages.scrollHeight;
  }

  function appendImageMessage(src, caption, sender) {
    const div = document.createElement('div');
    div.className = 'message ' + sender;
    const bubble = document.createElement('div');
    bubble.className = 'bubble image-bubble';
    const img = document.createElement('img');
    img.src = src;
    img.alt = caption || "uploaded image";
    bubble.appendChild(img);
    if (caption) {
      const cap = document.createElement('div');
      cap.style.marginTop = '0.4rem';
      cap.textContent = caption;
      bubble.appendChild(cap);
    }
    div.appendChild(bubble);
    botMessages.appendChild(div);
    botMessages.scrollTop = botMessages.scrollHeight;
  }

  function showTyping() {
    const div = document.createElement('div');
    div.className = 'message bot';
    div.id = 'botTyping';
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.innerHTML = '<span class="typing-indicator"><span></span><span></span><span></span></span>';
    div.appendChild(bubble);
    botMessages.appendChild(div);
    botMessages.scrollTop = botMessages.scrollHeight;
  }

  function hideTyping() {
    const t = document.getElementById('botTyping');
    if (t) t.remove();
  }

  function basicImageInsight() {
    return "I cant truly analyze images without an API, but tell me what you want to build from it and Ill draft ideas, structure, and prompts around your description.";
  }

  function smallTalkReply(text) {
    const lower = text.toLowerCase();
    if (/(hi|hello|hey|yo)\b/.test(lower)) return "Hey! Tell me what youre building and Ill shape it into a clear plan.";
    if (/(thanks|thank you)/.test(lower)) return "Youre welcome! Want me to refine the idea or turn it into a generator prompt?";
    if (/(who are you|what are you)/.test(lower)) return "Im NovaForges local idea assistant. I cant call external APIs, but I can craft detailed plans, prompts, and structure.";
    if (/(can you help|help me)/.test(lower)) return "Absolutely. Describe the project or paste a rough idea, and Ill structure it.";
    return null;
  }

  function generalizeIdea(text) {
    const seed = findIdeaSeed(text);
    const { response, detailedPrompt } = buildIdeaResponse(text);
    return { seed, pack: response, detailedPrompt };
  }

  function followupQuestions(seed) {
    const base = [
      "Do you want payments now or later?",
      "Any preferred style (minimal, bold, luxury, playful)?",
      "Target audience and price point?"
    ];
    if (seed.id === "ecommerce") {
      base.push("Physical shipping or digital products?");
    }
    if (seed.id === "retail") {
      base.push("Single location or multiple stores?");
    }
    return base.slice(0, 4);
  }

  function buildChatPayload(text) {
    const smallTalk = smallTalkReply(text);
    if (smallTalk) return { response: smallTalk, detailedPrompt: null };

    const { seed, pack, detailedPrompt } = generalizeIdea(text);
    const questions = followupQuestions(seed);
    return {
      response: `${pack}\n\nIf you want, answer these:\n- ${questions.join("\n- ")}`,
      detailedPrompt
    };
  }

  function injectPromptIntoGenerator(promptText) {
    if (!descriptionTextarea || !promptText) return;
    descriptionTextarea.value = promptText;
    showPanel('generator-panel');
    descriptionTextarea.focus();
    notify(' Detailed prompt added to Generate Your Website', 'success');
  }

  function sendBotMessage(message, options = {}) {
    const msg = (message || botInput.value).trim();
    if (!msg) return;
    appendBotMessage(msg, 'user');
    botInput.value = '';
    showTyping();
    setTimeout(() => {
      hideTyping();
      const { response, detailedPrompt } = buildChatPayload(msg);
      appendBotMessage(response, 'bot');
      if (options.showPromptAction && detailedPrompt) {
        appendPromptAction(detailedPrompt);
      }
    }, 550);
  }

  if (botSendBtn) {
    botSendBtn.addEventListener('click', sendBotMessage);
    botInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        e.preventDefault();
        sendBotMessage();
      }
    });
  }

  if (botClearBtn) {
    botClearBtn.addEventListener('click', () => {
      botMessages.innerHTML = '';
      appendSystemMessage('Chat cleared.');
    });
  }

  if (botSuggestions) {
    botSuggestions.addEventListener('click', e => {
      const chip = e.target.closest('.suggestion-chip');
      if (!chip) return;
      const suggestion = chip.dataset.suggestion || chip.textContent;
      sendBotMessage(suggestion, { showPromptAction: true });
    });
  }

  if (botMessages) {
    botMessages.addEventListener('click', e => {
      const btn = e.target.closest('button[data-action="use-prompt"]');
      if (!btn) return;
      const promptText = btn.dataset.prompt;
      injectPromptIntoGenerator(promptText);
    });
  }

  if (botImageInput) {
    botImageInput.addEventListener('change', e => {
      const file = e.target.files && e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {
        appendImageMessage(reader.result, file.name, 'user');
        showTyping();
        setTimeout(() => {
          hideTyping();
          appendBotMessage(basicImageInsight(), 'bot');
        }, 600);
      };
      reader.readAsDataURL(file);
      botImageInput.value = '';
    });
  }

  // =====================
  // UPLOAD PANEL
  // =====================
  if (uploadInput) {
    uploadInput.addEventListener('change', async e => {
      const file = e.target.files[0];
      if (!file) return;
      try {
        const z = await JSZip.loadAsync(file);
        const list = [];
        z.forEach((path, f) => list.push(path));
        uploadList.innerHTML = '<ul>' + list.map(f => `<li>${f}</li>`).join('') + '</ul>';
      } catch (err) {
        uploadList.textContent = 'Failed to read zip file.';
      }
    });
  }

  // =====================
  // ADD FEATURE (GLITCH-PROOF + SAFE ROLLBACK)
  // =====================
    function classifyModificationMode(message = "") {
    const text = String(message || "").toLowerCase();
    if (/(fix|bug|error|broken|not working)/.test(text)) return "bugfix";
    if (/(replace|swap|change this|replace this)/.test(text)) return "replace";
    if (/(refactor|clean code|optimize)/.test(text)) return "refactor";
    if (/(ui|design|style|responsive|modern)/.test(text)) return "ui";
    if (/(auth|login|signup|logout|profile)/.test(text)) return "auth";
    if (/(order|cart|history|database|backend|api|route)/.test(text)) return "data";
    return "feature";
  }

  async function addFeature(featureDescription) {
    if (!lastGeneratedProjectName || isMutating) return;
    if (!featureDescription?.trim()) return;

    lockUI(true, "feature");

    try {
      const mode = classifyModificationMode(featureDescription);
      let res = await fetch(`${GENERATOR_API}/api/copilot-modify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          projectName: lastGeneratedProjectName,
          instruction: featureDescription,
          mode
        })
      });
      if (!res.ok) {
        // backward compatibility with older backend
        res = await fetch(`${GENERATOR_API}/api/add-feature`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            projectName: lastGeneratedProjectName,
            featureDescription
          })
        });
      }

      const data = await res.json();
      if (!data.success || !data.code) {
        throw new Error(data.error || "Invalid feature response");
      }

      const mergedCode = normalizeCodeResponse(data.code);
      lastStableCode = mergedCode;

      try {
        localStorage.setItem('nova_lastProject', JSON.stringify({
          name: lastGeneratedProjectName,
          code: lastStableCode
        }));
      } catch (e) {
        console.warn('could not update project storage', e);
      }

      updateCodePanels(mergedCode);
      updateGenerationInsights(mergedCode);
      updatePreview(mergedCode.html, mergedCode.css, mergedCode.js);

      notify(data.assistantMessage || "Copilot update applied successfully!", "success");

    } catch (err) {
      console.error(err);
      notify("Feature update failed - restored previous state", "error");

      if (lastStableCode) {
        updateCodePanels(lastStableCode);
        updateGenerationInsights(lastStableCode);
        updatePreview(
          lastStableCode.html,
          lastStableCode.css,
          lastStableCode.js
        );
      }
    } finally {
      lockUI(false, "feature");
    }
  }

  function insertImageTagIntoHtml(html, src, featureDescription = "Uploaded image") {
    try {
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");

      const img = doc.createElement('img');
      img.src = src;
      img.alt = featureDescription;
      img.style.maxWidth = '100%';
      img.style.display = 'block';
      img.style.margin = '1rem auto';

      const lower = featureDescription.toLowerCase();
      const setBackground = (el) => {
        el.style.backgroundImage = `url(${src})`;
        el.style.backgroundSize = 'cover';
        el.style.backgroundPosition = 'center';
        el.style.backgroundRepeat = 'no-repeat';
        // keep text legible
        if (!el.style.color) {
          el.style.color = '#ffffff';
        }
      };

      if (lower.includes('background')) {
        // Prefer explicit target blocks when found
        let target = doc.querySelector('main, .hero, header, .banner, .jumbotron');
        if (!target) target = doc.body;
        setBackground(target);

        // optionally hide existing no-longer needed default image elements
        const existingImgs = target.querySelectorAll('img');
        existingImgs.forEach(i => {
          if (i.src && i.src !== src) {
            i.style.display = 'none';
          }
        });

        return '<!DOCTYPE html>\n' + doc.documentElement.outerHTML;
      }

      const tryReplaceNamedImage = () => {
        const named = lower.match(/named\s+["']?([a-zA-Z0-9_-]+)["']?/);
        if (!named) return false;
        const needle = named[1].trim().toLowerCase();
        const candidate = Array.from(doc.querySelectorAll('img')).find(i => {
          const alt = (i.alt || '').toLowerCase();
          const srcVal = (i.src || '').toLowerCase();
          return alt.includes(needle) || srcVal.includes(needle) || (i.id || '').toLowerCase() === needle || (i.className || '').toLowerCase().includes(needle);
        });
        if (candidate) {
          candidate.src = src;
          candidate.alt = featureDescription;
          return true;
        }
        return false;
      };

      const tryReplaceAnyImage = () => {
        const existing = doc.querySelector('img');
        if (existing) {
          existing.src = src;
          existing.alt = featureDescription;
          return true;
        }
        return false;
      };

      const targetZones = {
        header: 'header',
        hero: '.hero, .hero-section',
        banner: '.banner',
        footer: 'footer'
      };

      if (lower.includes('replace') || lower.includes('swap')) {
        if (tryReplaceNamedImage() || tryReplaceAnyImage()) {
          return '<!DOCTYPE html>\n' + doc.documentElement.outerHTML;
        }
      }

      for (const key in targetZones) {
        if (lower.includes(key)) {
          const selector = targetZones[key];
          const section = doc.querySelector(selector);
          if (section) {
            setBackground(section);
            return '<!DOCTYPE html>\n' + doc.documentElement.outerHTML;
          }
        }
      }

      const findKeyword = () => {
        const match = lower.match(/(?:at|for|in)\s+([^.,\n]+)/);
        return match ? match[1].trim() : null;
      };

      const keyword = findKeyword();
      const findClosestElement = (text) => {
        if (!text) return null;
        const normalized = text.trim().toLowerCase();
        let best = null;
        let bestScore = Infinity;
        const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT, null, false);
        while (walker.nextNode()) {
          const node = walker.currentNode;
          const value = node.textContent.trim();
          if (!value) continue;
          const lowerValue = value.toLowerCase();
          if (lowerValue.includes(normalized)) {
            const length = value.length;
            if (length < bestScore) {
              bestScore = length;
              best = node.parentElement;
            }
          }
        }
        return best;
      };

      const target = keyword ? findClosestElement(keyword) : null;

      const findCardContainer = (el) => {
        if (!el) return null;
        const patterns = /(card|hotel|listing|property|item|tile|panel|box|container)/i;
        let node = el;
        for (let i = 0; i < 6 && node; i += 1) {
          if (node.className && patterns.test(node.className)) {
            return node;
          }
          if (node.tagName && /article|section|aside|div/i.test(node.tagName)) {
            if (node.getAttribute('role') === 'article' || node.getAttribute('role') === 'region') {
              return node;
            }
          }
          node = node.parentElement;
        }
        return el.parentElement || el;
      };

      const replaceExistingImage = (el) => {
        if (!el) return false;
        const existing = el.querySelector('img');
        if (existing) {
          existing.src = src;
          existing.alt = featureDescription;
          return true;
        }
        return false;
      };

      let inserted = false;
      if (target) {
        const container = findCardContainer(target);
        if (container) {
          inserted = replaceExistingImage(container);
          if (!inserted) {
            container.insertBefore(img, container.firstChild);
            inserted = true;
          }
        }
      }

      if (!inserted) {
        const main = doc.querySelector('main');
        const body = doc.body || doc.getElementsByTagName('body')[0];
        if (main) {
          main.appendChild(img);
        } else if (body) {
          body.appendChild(img);
        } else {
          doc.documentElement.appendChild(img);
        }
      }

      return '<!DOCTYPE html>\n' + doc.documentElement.outerHTML;
    } catch (e) {
      console.warn('Failed to inject image into HTML for preview', e);
      return html;
    }
  }

  async function addFeatureWithImage(featureDescription, imageData) {
    if (!lastGeneratedProjectName || isMutating) return;
    if (!featureDescription?.trim()) return;

    lockUI(true, "feature");

    try {
      console.log('Sending image feature request to backend...');
      console.log('Feature:', featureDescription);
      console.log('Image data length:', imageData.length);

      const res = await fetch(`${GENERATOR_API}/api/add-feature-with-image`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          projectName: lastGeneratedProjectName,
          featureDescription,
          imageData
        })
      });

      console.log('Backend response status:', res.status);

      if (!res.ok) {
        const errorText = await res.text();
        console.error('Backend error:', errorText);
        throw new Error(`Backend error: ${res.status} - ${errorText}`);
      }

      const data = await res.json();
      console.log('Backend response:', data);

      if (!data.success || !data.code) {
        throw new Error(data.error || "Invalid feature response");
      }

      const mergedCode = normalizeCodeResponse(data.code);

      // Backend now applies deterministic placement. Preview-side fallback only if image is still missing.
      if (imageData && !mergedCode.html.includes(imageData)) {
        mergedCode.html = insertImageTagIntoHtml(mergedCode.html, imageData, featureDescription);
      }

      lastStableCode = mergedCode;

      // update persisted storage as well
      try {
        localStorage.setItem('nova_lastProject', JSON.stringify({
          name: lastGeneratedProjectName,
          code: lastStableCode
        }));
      } catch (e) {
        console.warn('could not update project storage', e);
      }

      updateCodePanels(mergedCode);
      updateGenerationInsights(mergedCode);
      updatePreview(mergedCode.html, mergedCode.css, mergedCode.js);
      setActiveCodeTab('preview');

      notify(" Image feature added successfully!", "success");

    } catch (err) {
      console.error('addFeatureWithImage error:', err);
      notify(` Image feature failed: ${err.message}`, "error");

      if (lastStableCode) {
        updateCodePanels(lastStableCode);
        updateGenerationInsights(lastStableCode);
        updatePreview(
          lastStableCode.html,
          lastStableCode.css,
          lastStableCode.js
        );
      }
    } finally {
      lockUI(false, "feature");
    }
  }

  agentBtn.addEventListener("click", () => {
    // open chat modal when clicking agent button
    if (!lastGeneratedProjectName || isMutating) return;
    agentModal.classList.remove('hidden');
    agentInput.focus();
  });

  // chat modal close
  if (agentCloseBtn) {
    agentCloseBtn.addEventListener('click', () => {
      agentModal.classList.add('hidden');
    });
  }

  // send message
  if (agentSendBtn) {
    agentSendBtn.addEventListener('click', async () => {
      const msg = agentInput.value.trim();
      const imageFile = agentImageInput.files[0];

      if (!msg && !imageFile) return;

      // Handle image display
      let imageData = null;
      if (imageFile) {
        try {
          imageData = await readFileAsDataURL(imageFile);
          appendAgentMessage(msg, 'user', imageData);
          agentImageInput.value = ''; // Clear the file input
        } catch (error) {
          appendAgentMessage(`Error loading image: ${error.message}`, 'agent');
          return; // Don't proceed with processing
        }
      } else {
        appendAgentMessage(msg, 'user');
      }

      agentInput.value = '';

      // Process the message (with or without image)
      await processAgentMessage(msg, imageData);
    });
  }

  // Allow sending message with Enter key
  if (agentInput) {
    agentInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        agentSendBtn.click();
      }
    });
  }

  function readFileAsDataURL(file) {
    return new Promise((resolve, reject) => {
      // Check file size (limit to 5MB to avoid API issues)
      const maxSize = 5 * 1024 * 1024; // 5MB
      if (file.size > maxSize) {
        reject(new Error('Image file is too large. Please choose an image smaller than 5MB.'));
        return;
      }

      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

    async function processAgentMessage(message, imageData) {
    try {
      if (!lastGeneratedProjectName) {
        appendAgentMessage('Please generate or load a project first so I can modify it.', 'agent');
        return;
      }

      const imageCommands = ['add this image', 'replace this image', 'use this image', 'include this image', 'add image', 'replace image', 'use image', 'include image'];
      const hasImageCommand = imageCommands.some(cmd => message.toLowerCase().includes(cmd));
      const mode = classifyModificationMode(message);

      if (imageData) {
        let featureDescription = message.trim();
        if (!featureDescription || !hasImageCommand) {
          featureDescription = message.trim() || "Add this image to the website";
        }

        const processingMsg = appendAgentMessage(`Copilot (${mode}) is applying image changes...`, 'agent');
        await addFeatureWithImage(featureDescription, imageData);
        processingMsg.remove();
        appendAgentMessage('Copilot applied image modification successfully.', 'agent');
      } else {
        const processingMsg = appendAgentMessage(`Copilot (${mode}) is updating your project...`, 'agent');
        await addFeature(message);
        processingMsg.remove();
        appendAgentMessage('Copilot update completed. Review preview and code tabs.', 'agent');
      }
    } catch (error) {
      console.error('Error processing agent message:', error);
      appendAgentMessage(`Copilot update failed: ${error.message || 'Please try again.'}`, 'agent');
    }
  }

  function appendAgentMessage(text, type, imageData = null, save = true) {
    const div = document.createElement('div');
    div.className = 'message ' + type;

    if (imageData) {
      const img = document.createElement('img');
      img.src = imageData;
      img.style.maxWidth = '200px';
      img.style.maxHeight = '200px';
      img.style.borderRadius = '8px';
      img.style.marginBottom = '0.5rem';
      div.appendChild(img);
    }

    if (text) {
      const textDiv = document.createElement('div');
      textDiv.textContent = text;
      div.appendChild(textDiv);
    }

    agentMessages.appendChild(div);
    agentMessages.scrollTop = agentMessages.scrollHeight;

    if (save) {
      saveAgentHistory();
    }

    return div; // Return the message element for potential removal
  }

  // =====================
  // CODE DISPLAY
  // =====================
  function updateCodePanels(code) {
    setHighlighted("html", code.html, "html");
    setHighlighted("css", code.css, "css");
    setHighlighted("js", code.js, "javascript");
    setHighlighted("backend", code.backend || "" , "python");
  }

  function setHighlighted(lang, code, prismLang) {
    const el = document.getElementById(`${lang}-code`);
    if (!el) return;
    el.innerHTML = Prism.highlight(code || "", Prism.languages[prismLang], prismLang);
  }

  // =====================
  // NOTIFY
  // =====================
  function notify(msg, type = "info") {
    const n = document.createElement("div");
    n.textContent = msg;
    n.style.cssText = `
      position:fixed;
      top:20px;
      right:20px;
      background:${type === "success" ? "#10b981" : "#ef4444"};
      color:white;
      padding:14px 20px;
      border-radius:8px;
      z-index:9999;
    `;
    document.body.appendChild(n);
    setTimeout(() => n.remove(), 3500);
  }

  // =====================
  // DOWNLOAD PROJECT
  // =====================
  if (downloadBtn) {
    downloadBtn.addEventListener('click', async () => {
      if (!lastStableCode) {
        alert('Generate a project first before downloading.');
        return;
      }

      const zip = new JSZip();
      if (lastStableCode.files && typeof lastStableCode.files === 'object') {
        Object.entries(lastStableCode.files).forEach(([filePath, content]) => {
          zip.file(filePath, content || '');
        });
      } else {
        zip.file('index.html', lastStableCode.html || '');
        zip.file('style.css', lastStableCode.css || '');
        zip.file('app.js', lastStableCode.js || '');
        if (lastStableCode.blueprint) {
          zip.file('design-blueprint.json', JSON.stringify(lastStableCode.blueprint, null, 2));
        }
        if (lastStableCode.analysis) {
          zip.file('analysis.json', JSON.stringify(lastStableCode.analysis, null, 2));
        }
        if (lastStableCode.uiPlan) {
          zip.file('ui-plan.json', JSON.stringify(lastStableCode.uiPlan, null, 2));
        }
        if (lastStableCode.backend) {
          zip.file('server.py', lastStableCode.backend);
        }
      }

      try {
        const blob = await zip.generateAsync({ type: 'blob' });
        const name = `${lastGeneratedProjectName || 'project'}.zip`;
        saveAs(blob, name);
        notify(' Project zip created', 'success');
      } catch (err) {
        console.error('Zip generation failed', err);
        notify(' Download failed', 'error');
      }
    });
  }

  // =====================
  // DEPLOY (ONE-CLICK RENDER)
  // =====================
  const deployStatusEl = document.getElementById('deployStatus');
  let deployPollInterval = null;

  function setDeployStatus(text, type = 'info') {
    if (!deployStatusEl) return;
    deployStatusEl.textContent = text;
    deployStatusEl.className = `deploy-status ${type}`;
  }

// Helper: Polling function with better state handling
async function startDeployPolling(serviceId, deployId, apiKey, fallbackUrl) {
  const MAX_POLL_TIME = 600000; // 10 minutes
  const POLL_INTERVAL = 3000; // 3 seconds
  const startTime = Date.now();
  
  return new Promise((resolve, reject) => {
    const pollInterval = setInterval(async () => {
      const elapsed = Date.now() - startTime;
      
      try {
        const url = new URL('/api/deploy-status', apiBaseUrl);
        url.searchParams.set('service_id', serviceId);
        url.searchParams.set('deploy_id', deployId);
        if (apiKey) url.searchParams.set('api_key', apiKey);

        const resp = await fetch(url.toString());
        const text = await resp.text();
        let data;
        try {
          data = text ? JSON.parse(text) : null;
        } catch {
          data = null;
        }

        if (!resp.ok || !data?.success) {
          const message = data?.error || data?.details || text || resp.statusText;
          throw new Error(message || "Status check failed");
        }

        const status = (data.deploy?.status || 'unknown').toLowerCase();
        const statusText = {
          'pending': ' Pending...',
          'queued': ' Queued for build...',
          'building': ' Building deployment...',
          'deploying': ' Deploying...',
          'live': ' Live!',
          'success': ' Deployed successfully!',
          'failed': ' Deployment failed',
          'error': ' Error during deployment',
          'canceled': ' Deployment cancelled'
        };

        setDeployStatus(statusText[status] || `Status: ${status}`, 'info');

        // Check for terminal states
        if (['live', 'success', 'failed', 'error', 'canceled'].includes(status)) {
          clearInterval(pollInterval);
          
          if (status === 'failed' || status === 'error' || status === 'canceled') {
            setDeployStatus(
              `${statusText[status]} - Review logs at https://dashboard.render.com`,
              'error'
            );
            reject(new Error(`Deploy ${status}`));
          } else {
            // Deployment successful - get the live URL
            const liveUrl = data.deploy?.service?.url || 
                          data.deploy?.service?.defaultDomain || 
                          fallbackUrl;
            
            if (liveUrl) {
              setDeployStatus(
                ` Live at: ${liveUrl}`,
                'success'
              );
              // Automatically open the URL after success
              setTimeout(() => {
                window.open(liveUrl, "_blank");
              }, 500);
            } else {
              setDeployStatus(
                " Deployed! Check Render dashboard for URL.",
                'success'
              );
            }
            resolve(data);
          }
        }

        // Timeout after 10 minutes
        if (elapsed > MAX_POLL_TIME) {
          clearInterval(pollInterval);
          setDeployStatus(
            " Deployment taking longer than expected. Check Render dashboard: https://dashboard.render.com",
            'info'
          );
          reject(new Error("Deployment timeout"));
        }

      } catch (err) {
        clearInterval(pollInterval);
        setDeployStatus(` Polling failed: ${err.message}`, 'error');
        reject(err);
      }
    }, POLL_INTERVAL);
  });
}

deployBtn.addEventListener("click", async () => {
  // Validation
  if (!lastGithubUsername || !lastGithubRepo) {
    alert("Push the project to GitHub first (use 'Push to GitHub' button).");
    return;
  }

  // CLEAR any previous error immediately
  if (deployStatusEl) {
    deployStatusEl.textContent = '';
    deployStatusEl.className = 'deploy-status';
  }

  const deployRepoName = String(lastGithubRepo || '').trim().replace(/\s+/g, '-');
  const repo = `${lastGithubUsername}/${deployRepoName}`;
  const storedRenderKey = localStorage.getItem('nova_render_api_key');

  // Helper: Execute deploy attempt with error handling
  const attemptDeploy = async (apiKey, retryCount = 0) => {
    const MAX_RETRIES = 2;
    
    try {
      setDeployStatus(" Initiating deployment...", 'info');
      
      const resp = await fetch("http://localhost:5000/api/deploy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          repo, 
          api_key: apiKey,
          branch: "main",
          // Ship static first; web service can be enabled later.
          deploy_mode: "static"
        }),
      });

      // Parse response safely (some errors may return non-JSON HTML)
      const text = await resp.text();
      let data;
      try {
        data = text ? JSON.parse(text) : null;
      } catch (parseErr) {
        data = null;
      }

      // Handle API errors
      if (!resp.ok) {
        const details = data?.details || '';
        const message = data?.error || text || resp.statusText;
        const fullMessage = details ? `${message}: ${details}` : message;
        
        if (resp.status === 401) {
          throw new Error("Invalid Render API key. Get a new one from https://dashboard.render.com/account/api-tokens");
        } else if (resp.status === 404) {
          throw new Error("GitHub repository not found or not accessible. Ensure the repo is public and you have push access.");
        } else if (resp.status === 504) {
          if (retryCount < MAX_RETRIES) {
            setDeployStatus(` Render API timeout. Retrying (${retryCount + 1}/${MAX_RETRIES})...`, 'info');
            await new Promise(r => setTimeout(r, 2000));
            return attemptDeploy(apiKey, retryCount + 1);
          }
          throw new Error("Render API unavailable. Try again shortly.");
        }
        throw new Error(fullMessage || `API error: ${resp.statusText}`);
      }

      // Validate response structure
      if (!data || !data.success) {
        const errorMsg = data?.error || data?.details || "Deployment request rejected";
        throw new Error(errorMsg);
      }

      const serviceId = data.service_id;
      const deployId = data.deploy_id;

      if (!serviceId) {
        throw new Error("Missing service ID in response");
      }

      setDeployStatus(" Deployment initiated on Render...", 'info');

      // If we have deploy tracking info, start polling
      if (deployId) {
        await startDeployPolling(serviceId, deployId, apiKey, data.service_url);
      } else {
        // No deploy ID, but service created - use fallback
        const serviceUrl = data.service_url || `https://${repo.replace("/", "-")}.onrender.com`;
        setDeployStatus(` Service created! Check at: ${serviceUrl}`, 'success');
        setTimeout(() => window.open(serviceUrl, "_blank"), 1000);
      }

      return true;

    } catch (err) {
      if (retryCount < MAX_RETRIES && err.message.includes("timeout")) {
        await new Promise(r => setTimeout(r, 2000));
        return attemptDeploy(apiKey, retryCount + 1);
      }
      throw err;
    }
  };

  // Main flow
  try {
    // Option 1: Use stored key if available
    if (storedRenderKey) {
      setDeployStatus(" Using stored Render API key...", 'info');
      await attemptDeploy(storedRenderKey);
      return;
    }

    // Option 2: Try without key (server environment variable)
    try {
      setDeployStatus(" Checking for server-side API key...", 'info');
      await attemptDeploy(undefined);
      return;
    } catch (innerErr) {
      console.warn('Server-side key not available:', innerErr.message);
    }

    // Option 3: User must provide key
    const renderKey = prompt(
      "No Render API key found.\n\nProvide your Render API key to deploy automatically:\n\n" +
      "(Get it from: https://dashboard.render.com/account/api-tokens)\n\n" +
      "Leave blank to cancel."
    );

    if (!renderKey) {
      setDeployStatus(" Deployment cancelled (API key required for automation)", 'info');
      const confirmManual = confirm(
        "Automated deployment requires a Render API key.\n\n" +
        "Would you like to deploy manually via Render dashboard?\n" +
        "(You'll need to push your frontend to GitHub first)"
      );
      
      if (confirmManual) {
        const repoUrl = encodeURIComponent(`https://github.com/${repo}`);
        window.open(`https://dashboard.render.com/new?repo=${repoUrl}`, "_blank");
      }
      return;
    }

    // Store key for future use
    localStorage.setItem('nova_render_api_key', renderKey);
    setDeployStatus(" Using provided API key...", 'info');
    await attemptDeploy(renderKey);

  } catch (err) {
    console.error("Deployment error:", err);

    setDeployStatus(
      ` Deployment failed: ${err.message}`,
      'error'
    );

    if (deployStatusEl) {
      deployStatusEl.title = "Check the error message above and try again. Clear your API key if it's invalid?";
    }
  }
});

  // =====================
  // PUSH TO GITHUB (TRACK REPO)
  // =====================
  let lastGithubUsername = null;
  let lastGithubRepo = null;

  if (pushGithubBtn) {
    pushGithubBtn.addEventListener("click", () => {
      if (!lastGeneratedProjectName) {
        alert("Generate a project before pushing to GitHub.");
        return;
      }
      // Clear previous values
      githubUsername.value = '';
      githubRepoName.value = '';
      githubToken.value = '';
      githubMessage.textContent = '';
      githubMessage.className = 'github-message';
      
      // Open modal
      githubModal.classList.remove('hidden');
      githubUsername.focus();
    });
  }

  // GitHub Modal - Close button
  if (githubCloseBtn) {
    githubCloseBtn.addEventListener('click', () => {
      githubModal.classList.add('hidden');
    });
  }

  // GitHub Modal - Cancel button
  if (githubCancelBtn) {
    githubCancelBtn.addEventListener('click', () => {
      githubModal.classList.add('hidden');
    });
  }

  // GitHub Modal - Submit button
  if (githubSubmitBtn) {
    githubSubmitBtn.addEventListener('click', async () => {
      const username = githubUsername.value.trim();
      const repo = githubRepoName.value.trim();
      const token = githubToken.value.trim();

      // Validation
      if (!username) {
        showGithubMessage('Please enter your GitHub username.', 'error');
        githubUsername.focus();
        return;
      }
      if (!repo) {
        showGithubMessage('Please enter the repository name.', 'error');
        githubRepoName.focus();
        return;
      }
      if (!token) {
        showGithubMessage('Please enter your personal access token.', 'error');
        githubToken.focus();
        return;
      }

      // Push to GitHub
      githubSubmitBtn.disabled = true;
      showGithubMessage('Pushing to GitHub...', 'info');

      try {
        const res = await fetch(`${GENERATOR_API}/api/push-github`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            projectName: lastGeneratedProjectName,
            githubUsername: username,
            repoName: repo,
            token: token
          })
        });
        const data = await res.json();
        if (!data.success) {
          throw new Error(data.error || "Unknown error");
        }
        showGithubMessage('Project pushed to GitHub successfully!', 'success');
        lastGithubUsername = username;
        lastGithubRepo = data.repoNameSanitized || repo.replace(/\s+/g, '-');
        
        // Close modal after success
        setTimeout(() => {
          githubModal.classList.add('hidden');
          notify("Project pushed to GitHub!", "success");
        }, 1500);
      } catch (err) {
        console.error(err);
        showGithubMessage(`Git push failed: ${err.message}`, 'error');
      } finally {
        githubSubmitBtn.disabled = false;
      }
    });
  }

  // Helper function to display messages in GitHub modal
  function showGithubMessage(msg, type) {
    githubMessage.textContent = msg;
    githubMessage.className = `github-message ${type}`;
  }

  // Close GitHub modal when clicking outside
  githubModal.addEventListener('click', (e) => {
    if (e.target === githubModal) {
      githubModal.classList.add('hidden');
    }
  });
});



