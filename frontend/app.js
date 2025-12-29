// // DOM Elements
// const generateBtn = document.getElementById('generateBtn');
// const outputPanel = document.getElementById('outputPanel');
// const projectNameInput = document.getElementById('projectName');
// const projectTypeSelect = document.getElementById('projectType');
// const descriptionTextarea = document.getElementById('description');
// const tabButtons = document.querySelectorAll('.tab-button');
// const tabContents = document.querySelectorAll('.tab-content');
// const downloadBtn = document.getElementById('downloadBtn');
// const themeToggle = document.getElementById('themeToggle');
// const deployBtn = document.getElementById('deployBtn');

// // Backend API URL
// const API_URL = 'http://localhost:5000';

// let lastGeneratedProjectName = null;

// // ----- DARK/LIGHT MODE LOGIC -----
// (function setupThemeToggle() {
//     // Prefer system, else saved, else default light
//     const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
//     let currentTheme = localStorage.getItem('theme') || (prefersDark ? 'dark' : 'light');
//     document.documentElement.setAttribute('data-theme', currentTheme);
//     if (themeToggle) {
//         themeToggle.textContent = currentTheme === 'dark' ? '🌞' : '🌗';
//         themeToggle.onclick = () => {
//             currentTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
//             document.documentElement.setAttribute('data-theme', currentTheme);
//             localStorage.setItem('theme', currentTheme);
//             themeToggle.textContent = currentTheme === 'dark' ? '🌞' : '🌗';
//         };
//     }
// })();

// // Tab switching logic (code, css, js, backend, preview)
// tabButtons.forEach(button => {
//     button.addEventListener('click', () => {
//         const tabName = button.dataset.tab;
//         tabButtons.forEach(btn => btn.classList.remove('active'));
//         tabContents.forEach(content => content.classList.remove('active'));
//         button.classList.add('active');
//         document.getElementById(`${tabName}-tab`).classList.add('active');
//     });
// });

// // Generate code using AI backend
// // generateBtn.addEventListener('click', async (e) => {
// //     e.preventDefault();
// //     const projectName = projectNameInput.value || 'My Website';
// //     const projectType = projectTypeSelect.value;
// //     const description = descriptionTextarea.value;
// //     if (!description.trim()) {
// //         alert('Please describe your project in detail!');
// //         descriptionTextarea.focus();
// //         return;
// //     }
// // generateBtn.addEventListener('click', async () => {
// //     const buttonText = generateBtn.querySelector('.button-text');
// //     const buttonLoader = generateBtn.querySelector('.button-loader');
// //     buttonText.style.display = 'none';
// //     buttonLoader.style.display = 'inline-flex';
// //     generateBtn.disabled = true;

// //     // Show placeholder while generating
// //     const previewFrame = document.getElementById('preview-frame');
// //     previewFrame.srcdoc = `<div style="display:flex;justify-content:center;align-items:center;height:100%;color:#888;font-size:1.25rem;">Generating your website...</div>`;

// //     try {
// //         // ... your existing API call logic
// //     } finally {
// //         buttonText.style.display = 'inline';
// //         buttonLoader.style.display = 'none';
// //         generateBtn.disabled = false;
// //     }
// // });
// // Generate code using AI backend
// generateBtn.addEventListener('click', async (e) => {
//     e.preventDefault();

//     const projectName = projectNameInput.value || 'My Website';
//     const projectType = projectTypeSelect.value;
//     const description = descriptionTextarea.value;

//     if (!description.trim()) {
//         alert('Please describe your project in detail!');
//         descriptionTextarea.focus();
//         return;
//     }

//     // Get selected tech stack
//     const techStackCheckboxes = document.querySelectorAll('.tech-stack input[type="checkbox"]:checked');
//     const techStack = Array.from(techStackCheckboxes).map(cb => cb.value);

//     // Show loading state
//     const buttonText = generateBtn.querySelector('.button-text');
//     const buttonLoader = generateBtn.querySelector('.button-loader');
//     buttonText.style.display = 'none';
//     buttonLoader.style.display = 'inline-flex';
//     generateBtn.disabled = true;

//     // Show placeholder while generating
//     const previewFrame = document.getElementById('preview-frame');
//     previewFrame.srcdoc = `<div style="display:flex;justify-content:center;align-items:center;height:100%;color:#888;font-size:1.25rem;">Generating your website...</div>`;

//     try {
//         // Call backend API to generate code with Gemini
//         const response = await fetch(`${API_URL}/api/generate`, {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({ projectName, projectType, description, techStack }),
//         });
//         if (!response.ok) throw new Error(`Backend error: ${response.status}`);

//         const result = await response.json();
//         if (!result.success) throw new Error(result.error || 'Failed to generate code');

//         // Display generated code (with syntax highlighting)
//         setHighlighted('html', result.code.html, 'html');
//         setHighlighted('css', result.code.css, 'css');
//         setHighlighted('js', result.code.js, 'javascript');
//         setHighlighted('backend', result.code.backend, 'python');

//         // Update preview panel with full HTML directly (no extra wrapper)
//         previewFrame.srcdoc = result.code.html || "<h2>Preview not available</h2>";

//         // Show output
//         outputPanel.style.display = 'block';
//         outputPanel.scrollIntoView({ behavior: 'smooth' });

//         showNotification('✅ Code generated successfully by Gemini AI!', 'success');
//         lastGeneratedProjectName = projectName;
//     } catch (error) {
//         console.error('❌ Error:', error);
//         let errorMessage = 'Failed to generate code. ';
//         errorMessage += error.message.includes('Failed to fetch')
//             ? 'Make sure your backend server is running on http://localhost:5000'
//             : error.message;
//         showNotification('❌ ' + errorMessage, 'error');
//         if (confirm('Backend connection failed. Would you like to see a template instead?')) {
//             loadTemplateCode(projectType);
//         }
//     } finally {
//         buttonText.style.display = 'inline';
//         buttonLoader.style.display = 'none';
//         generateBtn.disabled = false;
//     }
// });


//     // Get selected tech stack
//     const techStackCheckboxes = document.querySelectorAll('.tech-stack input[type="checkbox"]:checked');
//     const techStack = Array.from(techStackCheckboxes).map(cb => cb.value);

//     // Show loading state
//     const buttonText = generateBtn.querySelector('.button-text');
//     const buttonLoader = generateBtn.querySelector('.button-loader');
//     buttonText.style.display = 'none';
//     buttonLoader.style.display = 'inline-flex';
//     generateBtn.disabled = true;

//     try {
//         // Call backend API to generate code with Gemini
//         const response = await fetch(`${API_URL}/api/generate`, {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({ projectName, projectType, description, techStack }),
//         });
//         if (!response.ok) throw new Error(`Backend error: ${response.status}`);

//         const result = await response.json();
//         if (!result.success) throw new Error(result.error || 'Failed to generate code');

//         // Display generated code (with syntax highlighting)
//         const htmlForTab = result.code.html.slice(0, 15000);
//         setHighlighted('html', htmlForTab, 'html');
//         setHighlighted('css', result.code.css, 'css');
//         setHighlighted('js', result.code.js, 'javascript');
//         setHighlighted('backend', result.code.backend, 'python');

//         // Update preview panel
//         const previewFrame = document.getElementById('preview-frame');
//         // previewFrame.srcdoc = result.code.html;
//         // result.code.html, result.code.css, and result.code.js MUST exist!
// previewFrame.srcdoc = `
//   <html>
//     <head>
//       <style>${result.code.css || ''}</style>
//     </head>
//     <body>
//       ${result.code.html || ''}
//       <script>${result.code.js || ''}<\/script>
//     </body>
//   </html>
// `;


//         // Show output
//         outputPanel.style.display = 'block';
//         outputPanel.scrollIntoView({ behavior: 'smooth' });

//         showNotification('✅ Code generated successfully by Gemini AI!', 'success');
//         lastGeneratedProjectName = projectName;

//     }  catch (error) {
//     console.error('❌ Error:', error);
//     let errorMessage = 'Failed to generate code. ';
//     if (error.message && error.message.includes('Failed to fetch')) {
//         errorMessage += 'Backend not reachable; showing a template instead.';
//     } else {
//         errorMessage += error.message || '';
//     }

//     showNotification('⚠️ ' + errorMessage, 'error');

//     // Always show a simple template when backend fails
//     loadTemplateCode(projectType);
// }
//  finally {
//         buttonText.style.display = 'inline';
//         buttonLoader.style.display = 'none';
//         generateBtn.disabled = false;
//     }
// });

// // Utility for code highlighting
// function setHighlighted(lang, code, prismLang) {
//     document.getElementById(`${lang}-code`).innerHTML =
//         Prism.highlight(code, Prism.languages[prismLang], prismLang);
// }

// // Copy code buttons per section
// document.querySelectorAll('.copy-button').forEach(button => {
//     button.addEventListener('click', () => {
//         const targetId = button.dataset.target;
//         const code = document.getElementById(targetId).textContent;
//         navigator.clipboard.writeText(code).then(() => {
//             button.textContent = '✓ Copied!';
//             button.style.background = '#10b981';
//             setTimeout(() => {
//                 button.textContent = 'Copy';
//                 button.style.background = '';
//             }, 2000);
//         }).catch(() => {
//             alert('Failed to copy. Please select and copy manually.');
//         });
//     });
// });

// // Download all files as a single ZIP
// downloadBtn?.addEventListener('click', async () => {
//     const htmlCode = document.getElementById('html-code').textContent;
//     const cssCode = document.getElementById('css-code').textContent;
//     const jsCode = document.getElementById('js-code').textContent;
//     const backendCode = document.getElementById('backend-code').textContent;
//     let projectName = projectNameInput.value || 'my-website';

//     // Sanitize project name for file system
//     projectName = projectName.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-_]/g, '');

//     const zip = new JSZip();
//     zip.file('index.html', htmlCode);
//     zip.file('style.css', cssCode);
//     zip.file('app.js', jsCode);
//     zip.file('server.py', backendCode);

//     try {
//         const content = await zip.generateAsync({ type: 'blob' });
//         saveAs(content, `${projectName}.zip`);
//         showNotification('📥 ZIP file downloaded! Check your Downloads folder.', 'success');
//     } catch (err) {
//         console.error('Error generating ZIP:', err);
//         showNotification('❌ Failed to create ZIP file.', 'error');
//     }
// });

// deployBtn?.addEventListener('click', async () => {
//     if (!lastGeneratedProjectName) {
//         showNotification('⚠️ Please generate a project before deploying.', 'error');
//         return;
//     }

//     try {
//         deployBtn.disabled = true;
//         const originalText = deployBtn.textContent;
//         deployBtn.textContent = 'Deploying...';

//         const response = await fetch(`${API_URL}/api/deploy`, {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({ projectName: lastGeneratedProjectName }),
//         });

//         const result = await response.json();
//         if (!response.ok || !result.success) {
//             throw new Error(result.error || 'Deployment failed');
//         }

//         showNotification(`🚀 Deployed! Live URL: ${result.deployUrl}`, 'success');
//     } catch (err) {
//         console.error('Deploy error:', err);
//         showNotification('❌ ' + err.message, 'error');
//     } finally {
//         deployBtn.disabled = false;
//         deployBtn.textContent = '🚀 Deploy to Netlify';
//     }
// });


// // Notifications (toast/slide)
// function showNotification(message, type = 'info') {
//     const notification = document.createElement('div');
//     notification.className = `notification notification-${type}`;
//     notification.textContent = message;
//     notification.style.cssText = `
//         position: fixed;
//         top: 20px;
//         right: 20px;
//         padding: 16px 24px;
//         background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
//         color: white;
//         border-radius: 8px;
//         box-shadow: 0 4px 12px rgba(0,0,0,0.15);
//         z-index: 10000;
//         font-weight: 600;
//         max-width: 400px;
//         animation: slideIn 0.3s ease;
//     `;
//     document.body.appendChild(notification);
//     setTimeout(() => {
//         notification.style.animation = 'slideOut 0.3s ease';
//         setTimeout(() => document.body.removeChild(notification), 300);
//     }, 5000);
// }
// const style = document.createElement('style');
// style.textContent = `
//     @keyframes slideIn {
//         from { transform: translateX(400px); opacity: 0; }
//         to { transform: translateX(0); opacity: 1; }
//     }
//     @keyframes slideOut {
//         from { transform: translateX(0); opacity: 1; }
//         to { transform: translateX(400px); opacity: 0; }
//     }
// `;
// document.head.appendChild(style);

// // Fallback template (minimal example for landing)
// function loadTemplateCode(projectType) {
//     const templates = {
//         landing: {
//             html: `<!DOCTYPE html>
// <html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Landing Page</title><style>*{box-sizing: border-box}body{font-family:sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;color:white;text-align:center;padding:20px}.container{max-width:800px}h1{font-size:3.5rem;margin-bottom:1rem}p{font-size:1.25rem;margin-bottom:2rem;opacity:.9}.btn{padding:1rem 2.5rem;background:white;color:#667eea;border:none;border-radius:50px;font-size:1.125rem;font-weight:600;cursor:pointer;transition:transform .2s}.btn:hover{transform:translateY(-2px)}</style></head><body><div class="container"><h1>Welcome to Your Website</h1><p>This is a fallback template. Connect your backend for AI-generated code!</p><button class="btn">Get Started</button></div></body></html>`,
//             css: '/* CSS is embedded in HTML above */',
//             js: '// No JavaScript needed for this simple template',
//             backend: '# Backend template shown above'
//         }
//     };
//     const template = templates[projectType] || templates.landing;
//     setHighlighted('html', template.html, 'html');
//     setHighlighted('css', template.css, 'css');
//     setHighlighted('js', template.js, 'javascript');
//     setHighlighted('backend', template.backend, 'python');
//     // Preview update
//     const previewFrame = document.getElementById('preview-frame');
//     previewFrame.srcdoc = template.html;
//     outputPanel.style.display = 'block';
//     outputPanel.scrollIntoView({ behavior: 'smooth' });
// }

// // Health check
// window.addEventListener('DOMContentLoaded', async () => {
//     try {
//         const response = await fetch(`${API_URL}/api/health`);
//         const data = await response.json();
//         if (data.status === 'healthy') {
//             showNotification('✅ Connected to Gemini AI backend!', 'success');
//         }
//     } catch (error) {
//         showNotification('⚠️ Backend not connected. Make sure server.py is running!', 'error');
//     }
// });

// // Auto-save description in localStorage
// descriptionTextarea?.addEventListener('input', () => {
//     localStorage.setItem('lastDescription', descriptionTextarea.value);
// });
// window.addEventListener('DOMContentLoaded', () => {
//     const lastDescription = localStorage.getItem('lastDescription');
//     if (lastDescription && descriptionTextarea) {
//         descriptionTextarea.value = lastDescription;
//     }
// });

// // Optional: focus first input on page load
// window.addEventListener('DOMContentLoaded', () => {
//     projectNameInput?.focus();
// });
// DOM Elements
const generateBtn = document.getElementById('generateBtn');
const outputPanel = document.getElementById('outputPanel');
const projectNameInput = document.getElementById('projectName');
const projectTypeSelect = document.getElementById('projectType');
const descriptionTextarea = document.getElementById('description');
const tabButtons = document.querySelectorAll('.tab-button');
const tabContents = document.querySelectorAll('.tab-content');
const downloadBtn = document.getElementById('downloadBtn');
const themeToggle = document.getElementById('themeToggle');
const deployBtn = document.getElementById('deployBtn');

// Backend API URL
const API_URL = 'http://localhost:5000';

let lastGeneratedProjectName = null;

// ----- DARK/LIGHT MODE LOGIC -----
(function setupThemeToggle() {
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  let currentTheme = localStorage.getItem('theme') || (prefersDark ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', currentTheme);
  if (themeToggle) {
    themeToggle.textContent = currentTheme === 'dark' ? '🌞' : '🌗';
    themeToggle.onclick = () => {
      currentTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', currentTheme);
      localStorage.setItem('theme', currentTheme);
      themeToggle.textContent = currentTheme === 'dark' ? '🌞' : '🌗';
    };
  }
})();

// Tab switching logic
tabButtons.forEach(button => {
  button.addEventListener('click', () => {
    const tabName = button.dataset.tab;
    tabButtons.forEach(btn => btn.classList.remove('active'));
    tabContents.forEach(content => content.classList.remove('active'));
    button.classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');
  });
});

// ------- GENERATE HANDLER (single, clean) -------
// generateBtn.addEventListener('click', async (e) => {
//   e.preventDefault();

//   const projectName = projectNameInput.value || 'My Website';
//   const projectType = projectTypeSelect.value;
//   const description = descriptionTextarea.value;

//   if (!description.trim()) {
//     alert('Please describe your project in detail!');
//     descriptionTextarea.focus();
//     return;
//   }

//   // Tech stack
//   const techStackCheckboxes = document.querySelectorAll('.tech-stack input[type="checkbox"]:checked');
//   const techStack = Array.from(techStackCheckboxes).map(cb => cb.value);

//   // Button loading state
//   const buttonText = generateBtn.querySelector('.button-text');
//   const buttonLoader = generateBtn.querySelector('.button-loader');
//   buttonText.style.display = 'none';
//   buttonLoader.style.display = 'inline-flex';
//   generateBtn.disabled = true;

//   // Preview placeholder
//   const previewFrame = document.getElementById('preview-frame');
//   previewFrame.srcdoc = `<div style="display:flex;justify-content:center;align-items:center;height:100%;color:#888;font-size:1.25rem;">Generating your website...</div>`;

//   try {
//     const response = await fetch(`${API_URL}/api/generate`, {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify({ projectName, projectType, description, techStack }),
//     });
//     if (!response.ok) throw new Error(`Backend error: ${response.status}`);

//     const result = await response.json();
//     if (!result.success) throw new Error(result.error || 'Failed to generate code');

//     // Limit HTML length inside code tab to avoid freezing
//     const htmlForTab = result.code.html.slice(0, 15000);
//     setHighlighted('html', htmlForTab, 'html');
//     setHighlighted('css', result.code.css, 'css');
//     setHighlighted('js', result.code.js, 'javascript');
//     setHighlighted('backend', result.code.backend, 'python');

//     // Full HTML in preview
//     previewFrame.srcdoc = result.code.html || "<h2>Preview not available</h2>";

//     outputPanel.style.display = 'block';
//     outputPanel.scrollIntoView({ behavior: 'smooth' });

//     showNotification('✅ Code generated successfully by Gemini AI!', 'success');
//     lastGeneratedProjectName = projectName;
//   } catch (error) {
//     console.error('❌ Error:', error);
//     let errorMessage = 'Failed to generate code. ';
//     if (error.message && error.message.includes('Failed to fetch')) {
//       errorMessage += 'Backend not reachable; showing a template instead.';
//     } else {
//       errorMessage += error.message || '';
//     }
//     showNotification('⚠️ ' + errorMessage, 'error');

//     // Fallback template
//     loadTemplateCode(projectType);
//   } finally {
//     buttonText.style.display = 'inline';
//     buttonLoader.style.display = 'none';
//     generateBtn.disabled = false;
//   }
// });
// Generate code using AI backend
generateBtn.addEventListener('click', async (e) => {
    e.preventDefault();

    const projectName = projectNameInput.value || 'My Website';
    const projectType = projectTypeSelect.value;
    const description = descriptionTextarea.value;

    if (!description.trim()) {
        alert('Please describe your project in detail!');
        descriptionTextarea.focus();
        return;
    }

    // Get selected tech stack
    const techStackCheckboxes = document.querySelectorAll('.tech-stack input[type="checkbox"]:checked');
    const techStack = Array.from(techStackCheckboxes).map(cb => cb.value);

    // Show loading state
    const buttonText = generateBtn.querySelector('.button-text');
    const buttonLoader = generateBtn.querySelector('.button-loader');
    buttonText.style.display = 'none';
    buttonLoader.style.display = 'inline-flex';
    generateBtn.disabled = true;

    // Show placeholder while generating
    const previewFrame = document.getElementById('preview-frame');
    previewFrame.srcdoc = `<div style="display:flex;justify-content:center;align-items:center;height:100%;color:#888;font-size:1.25rem;">Generating your website...</div>`;

    try {
        // Call backend API to generate code with Gemini
        const response = await fetch(`${API_URL}/api/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ projectName, projectType, description, techStack }),
        });
        if (!response.ok) throw new Error(`Backend error: ${response.status}`);

        const result = await response.json();
        if (!result.success) throw new Error(result.error || 'Failed to generate code');

        // Display generated code (with syntax highlighting)
        setHighlighted('html', result.code.html, 'html');
        setHighlighted('css', result.code.css, 'css');
        setHighlighted('js', result.code.js, 'javascript');
        setHighlighted('backend', result.code.backend, 'python');

        // Update preview panel with full HTML directly (no extra wrapper)
        previewFrame.srcdoc = result.code.html || "<h2>Preview not available</h2>";

        // Show output
        outputPanel.style.display = 'block';
        outputPanel.scrollIntoView({ behavior: 'smooth' });

        showNotification('✅ Code generated successfully by Gemini AI!', 'success');
        lastGeneratedProjectName = projectName;
    } catch (error) {
        console.error('❌ Error:', error);
        let errorMessage = 'Failed to generate code. ';
        errorMessage += error.message.includes('Failed to fetch')
            ? 'Make sure your backend server is running on http://localhost:5000'
            : error.message;
        showNotification('❌ ' + errorMessage, 'error');
        if (confirm('Backend connection failed. Would you like to see a template instead?')) {
            loadTemplateCode(projectType);
        }
    } finally {
        buttonText.style.display = 'inline';
        buttonLoader.style.display = 'none';
        generateBtn.disabled = false;
    }
});

// Utility for code highlighting
function setHighlighted(lang, code, prismLang) {
  document.getElementById(`${lang}-code`).innerHTML =
    Prism.highlight(code, Prism.languages[prismLang], prismLang);
}

// Copy buttons
document.querySelectorAll('.copy-button').forEach(button => {
  button.addEventListener('click', () => {
    const targetId = button.dataset.target;
    const code = document.getElementById(targetId).textContent;
    navigator.clipboard.writeText(code).then(() => {
      button.textContent = '✓ Copied!';
      button.style.background = '#10b981';
      setTimeout(() => {
        button.textContent = 'Copy';
        button.style.background = '';
      }, 2000);
    }).catch(() => {
      alert('Failed to copy. Please select and copy manually.');
    });
  });
});

// Download ZIP
downloadBtn?.addEventListener('click', async () => {
  const htmlCode = document.getElementById('html-code').textContent;
  const cssCode = document.getElementById('css-code').textContent;
  const jsCode = document.getElementById('js-code').textContent;
  const backendCode = document.getElementById('backend-code').textContent;
  let projectName = projectNameInput.value || 'my-website';

  projectName = projectName.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-_]/g, '');

  const zip = new JSZip();
  zip.file('index.html', htmlCode);
  zip.file('style.css', cssCode);
  zip.file('app.js', jsCode);
  zip.file('server.py', backendCode);

  try {
    const content = await zip.generateAsync({ type: 'blob' });
    saveAs(content, `${projectName}.zip`);
    showNotification('📥 ZIP file downloaded! Check your Downloads folder.', 'success');
  } catch (err) {
    console.error('Error generating ZIP:', err);
    showNotification('❌ Failed to create ZIP file.', 'error');
  }
});

// Deploy to Netlify
deployBtn?.addEventListener('click', async () => {
  if (!lastGeneratedProjectName) {
    showNotification('⚠️ Please generate a project before deploying.', 'error');
    return;
  }

  try {
    deployBtn.disabled = true;
    const originalText = deployBtn.textContent;
    deployBtn.textContent = 'Deploying...';

    const response = await fetch(`${API_URL}/api/deploy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ projectName: lastGeneratedProjectName }),
    });

    const result = await response.json();
    if (!response.ok || !result.success) {
      throw new Error(result.error || 'Deployment failed');
    }

    showNotification(`🚀 Deployed! Live URL: ${result.deployUrl}`, 'success');
    deployBtn.textContent = originalText;
  } catch (err) {
    console.error('Deploy error:', err);
    showNotification('❌ ' + err.message, 'error');
  } finally {
    deployBtn.disabled = false;
  }
});

// Notifications
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.textContent = message;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 16px 24px;
    background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
    color: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 10000;
    font-weight: 600;
    max-width: 400px;
    animation: slideIn 0.3s ease;
  `;
  document.body.appendChild(notification);
  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => document.body.removeChild(notification), 300);
  }, 5000);
}

const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from { transform: translateX(400px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }
  @keyframes slideOut {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(400px); opacity: 0; }
  }
`;
document.head.appendChild(style);

// Fallback template
function loadTemplateCode(projectType) {
  const templates = {
    landing: {
      html: `<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Landing Page</title><style>*{box-sizing: border-box}body{font-family:sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;color:white;text-align:center;padding:20px}.container{max-width:800px}h1{font-size:3.5rem;margin-bottom:1rem}p{font-size:1.25rem;margin-bottom:2rem;opacity:.9}.btn{padding:1rem 2.5rem;background:white;color:#667eea;border:none;border-radius:50px;font-size:1.125rem;font-weight:600;cursor:pointer;transition:transform .2s}.btn:hover{transform:translateY(-2px)}</style></head><body><div class="container"><h1>Welcome to Your Website</h1><p>This is a fallback template. Connect your backend for AI-generated code!</p><button class="btn">Get Started</button></div></body></html>`,
      css: '/* CSS is embedded in HTML above */',
      js: '// No JavaScript needed for this simple template',
      backend: '# Backend template shown above'
    }
  };
  const template = templates[projectType] || templates.landing;
  setHighlighted('html', template.html, 'html');
  setHighlighted('css', template.css, 'css');
  setHighlighted('js', template.js, 'javascript');
  setHighlighted('backend', template.backend, 'python');
  const previewFrame = document.getElementById('preview-frame');
  previewFrame.srcdoc = template.html;
  outputPanel.style.display = 'block';
  outputPanel.scrollIntoView({ behavior: 'smooth' });
}

// Health check
window.addEventListener('DOMContentLoaded', async () => {
  try {
    const response = await fetch(`${API_URL}/api/health`);
    const data = await response.json();
    if (data.status === 'healthy') {
      showNotification('✅ Connected to Gemini AI backend!', 'success');
    }
  } catch (error) {
    console.warn('Backend not connected. Using templates only.');
  }
});

// Auto-save description
descriptionTextarea?.addEventListener('input', () => {
  localStorage.setItem('lastDescription', descriptionTextarea.value);
});
window.addEventListener('DOMContentLoaded', () => {
  const lastDescription = localStorage.getItem('lastDescription');
  if (lastDescription && descriptionTextarea) {
    descriptionTextarea.value = lastDescription;
  }
});

// Focus first input
window.addEventListener('DOMContentLoaded', () => {
  projectNameInput?.focus();
});
