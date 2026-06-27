// API Configuration
const API_URL = ''; // Relative path since we serve statically

// Select DOM utility
const $ = selector => document.querySelector(selector);
const $$ = selector => document.querySelectorAll(selector);

// Session Management
const session = {
  getUser() {
    const user = localStorage.getItem('furniture_user');
    return user ? JSON.parse(user) : null;
  },
  setUser(user) {
    localStorage.setItem('furniture_user', JSON.stringify(user));
  },
  clear() {
    localStorage.removeItem('furniture_user');
  },
  checkAuth(requiredRole = null) {
    const user = this.getUser();
    const currentPage = window.location.pathname.split('/').pop();
    
    // Pages that don't require auth
    const publicPages = ['index.html', '', 'login.html', 'signup.html'];
    
    if (!user) {
      if (!publicPages.includes(currentPage)) {
        window.location.href = 'login.html';
      }
    } else {
      // User is logged in
      if (currentPage === 'login.html' || currentPage === 'signup.html') {
        if (user.role === 'admin') {
          window.location.href = 'admin.html';
        } else {
          window.location.href = 'dashboard.html';
        }
      }
      
      // Role enforcement
      if (requiredRole && user.role !== requiredRole) {
        if (user.role === 'admin') {
          window.location.href = 'admin.html';
        } else {
          window.location.href = 'dashboard.html';
        }
      }
    }
  }
};

// Global Dark/Light Mode Theme Toggle
function initTheme() {
  const isLight = localStorage.getItem('light_theme') === 'true';
  if (isLight) {
    document.body.classList.add('light-mode');
  }
  
  // Find theme togglers and bind click event
  const togglers = $$('.theme-toggle');
  togglers.forEach(btn => {
    btn.innerHTML = isLight ? '🌙' : '☀️';
    btn.addEventListener('click', () => {
      const currentlyLight = document.body.classList.toggle('light-mode');
      localStorage.setItem('light_theme', currentlyLight);
      btn.innerHTML = currentlyLight ? '🌙' : '☀️';
    });
  });
}

// Global Notification alert helper
function showToast(message, type = 'success') {
  let container = $('#toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 1000;
      display: flex;
      flex-direction: column;
      gap: 10px;
    `;
    document.body.appendChild(container);
  }
  
  const toast = document.createElement('div');
  toast.style.cssText = `
    padding: 14px 24px;
    border-radius: 12px;
    background: ${type === 'success' ? '#10B981' : (type === 'danger' ? '#EF4444' : '#F59E0B')};
    color: white;
    font-weight: 600;
    font-size: 0.9rem;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    transform: translateY(20px);
    opacity: 0;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.1);
  `;
  toast.innerText = message;
  container.appendChild(toast);
  
  // Trigger transition
  setTimeout(() => {
    toast.style.transform = 'translateY(0)';
    toast.style.opacity = '1';
  }, 10);
  
  // Hide & remove after delay
  setTimeout(() => {
    toast.style.transform = 'translateY(20px)';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Mouse follow radial glow effect in Hero elements
function initMouseGlow() {
  const mesh = $('.mesh-glow');
  if (!mesh) return;
  
  window.addEventListener('mousemove', (e) => {
    const x = e.clientX - 300;
    const y = e.clientY - 300;
    
    const purpleMesh = $('.glow-purple-mesh');
    const cyanMesh = $('.glow-cyan-mesh');
    
    if (purpleMesh) {
      purpleMesh.style.transform = `translate(${x * 0.1}px, ${y * 0.1}px)`;
    }
    if (cyanMesh) {
      cyanMesh.style.transform = `translate(${x * -0.05}px, ${y * -0.05}px)`;
    }
  });
}

// Dynamic Counter Up Animation
function animateCounter(el, target, suffix = '', duration = 1500) {
  let start = 0;
  const increment = target / (duration / 16);
  const timer = setInterval(() => {
    start += increment;
    if (start >= target) {
      el.innerText = target + suffix;
      clearInterval(timer);
    } else {
      el.innerText = Math.floor(start) + suffix;
    }
  }, 16);
}

// Global Nav setup
function setupGlobalHeader() {
  const user = session.getUser();
  const header = $('header');
  if (!header) return;

  const currentPage = window.location.pathname.split('/').pop() || 'index.html';
  
  let navHTML = '';
  let actionsHTML = '';

  if (user) {
    if (user.role === 'admin') {
      const dashboardActive = (currentPage === 'admin.html') ? 'class="active"' : '';
      const analyticsActive = (currentPage === 'analytics.html') ? 'class="active"' : '';
      
      navHTML = `
        <a href="admin.html" ${dashboardActive}>📊 Dashboard</a>
        <a href="analytics.html" ${analyticsActive}>📈 Analytics</a>
      `;
      actionsHTML = `
        <div class="user-badge">
          <span>👤</span>
          <strong>${user.fullName}</strong>
        </div>
        <button class="btn btn-secondary theme-toggle">☀️</button>
        <div id="logout-btn" class="logout-btn-circle" title="Logout">📤</div>
      `;
    } else {
      const dashActive = (currentPage === 'dashboard.html') ? 'class="active"' : '';
      const genActive = (currentPage === 'generate.html') ? 'class="active"' : '';
      const histActive = (currentPage === 'history.html') ? 'class="active"' : '';
      const analActive = (currentPage === 'analytics.html') ? 'class="active"' : '';

      navHTML = `
        <a href="dashboard.html" ${dashActive}>📊 Dashboard</a>
        <a href="generate.html" ${genActive}>✨ Generate Guide</a>
        <a href="history.html" ${histActive}>🕒 History</a>
        <a href="analytics.html" ${analActive}>📈 Analytics</a>
      `;
      actionsHTML = `
        <div class="user-badge">
          <span>👤</span>
          <strong>${user.fullName.split(' ')[0]}</strong>
        </div>
        <button class="btn btn-secondary theme-toggle">☀️</button>
        <div id="logout-btn" class="logout-btn-circle" title="Logout">📤</div>
      `;
    }
  } else {
    navHTML = `
      <a href="index.html#features">Features</a>
      <a href="index.html#overview">Overview</a>
    `;
    actionsHTML = `
      <button class="btn btn-secondary theme-toggle" style="border-radius: 50%; width: 40px; height: 40px; padding: 0;">☀️</button>
      <a href="login.html" class="btn btn-secondary" style="border-radius: 12px; padding: 8px 18px;">Sign In</a>
      <a href="signup.html" class="btn btn-primary" style="border-radius: 12px; padding: 8px 18px;">Start Free</a>
    `;
  }

  header.innerHTML = `
    <div class="logo-container" onclick="window.location.href='index.html'">
      <div class="logo-icon">🛋️</div>
      <div class="logo-text">AURA<span style="font-size: 0.95rem; font-weight: 700; margin-left: 2px;">AI</span></div>
    </div>
    <nav>
      ${navHTML}
    </nav>
    <div class="actions">
      ${actionsHTML}
    </div>
  `;

  // Bind logout action
  const logoutBtn = $('#logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      session.clear();
      showToast('Logged out successfully.');
      setTimeout(() => {
        window.location.href = 'index.html';
      }, 1000);
    });
  }

  initTheme();
}

// Execute common startup routines
document.addEventListener('DOMContentLoaded', () => {
  setupGlobalHeader();
  initMouseGlow();
  initAIChatbot();
});

// Interactive Floating Chatbot Initialization
function initAIChatbot() {
  const user = session.getUser();
  if (!user) return; // Only show for logged-in personnel

  // Create trigger bubble button
  const trigger = document.createElement('div');
  trigger.className = 'chatbot-trigger';
  trigger.innerHTML = '💬';
  trigger.title = 'AURA AI Chatbot';
  document.body.appendChild(trigger);

  // Create chat window panel
  const windowEl = document.createElement('div');
  windowEl.className = 'chatbot-window';
  
  // Extract active report ID from URL if on report details page
  const urlParams = new URLSearchParams(window.location.search);
  const reportId = urlParams.get('id') || '';

  windowEl.innerHTML = `
    <div class="chatbot-header">
      <div class="chatbot-header-title">
        <span style="font-size: 1.3rem;">🤖</span>
        <div>
          <div style="font-weight: 700; color: white;">AURA AI Care Bot</div>
          <div style="font-size: 0.75rem; color: var(--success); display: flex; align-items: center; gap: 4px;">
            <span style="display:inline-block; width:6px; height:6px; background:var(--success); border-radius:50%; box-shadow:0 0 6px var(--success);"></span> Online
          </div>
        </div>
      </div>
      <button id="close-chat-btn" style="background:none; border:none; color:var(--text-secondary); font-size:1.2rem; cursor:pointer;">×</button>
    </div>
    <div class="chatbot-messages" id="chat-messages-container">
      <div class="message-bubble message-bot">
        Hi! I am AURA AI, your interactive care chatbot. Ask me anything about cleaning fabrics, restoring wood grain, treating leather, or scheduling maintenance.
      </div>
    </div>
    <form class="chat-input-container" id="chat-input-form">
      <input type="text" id="chat-message-input" placeholder="Type your message..." required autocomplete="off">
      <button type="submit">➔</button>
    </form>
  `;
  document.body.appendChild(windowEl);

  // Toggle display
  trigger.addEventListener('click', () => {
    windowEl.classList.toggle('active');
  });

  const closeBtn = windowEl.querySelector('#close-chat-btn');
  closeBtn.addEventListener('click', () => {
    windowEl.classList.remove('active');
  });

  // Submit message
  const chatForm = windowEl.querySelector('#chat-input-form');
  const chatInput = windowEl.querySelector('#chat-message-input');
  const messagesContainer = windowEl.querySelector('#chat-messages-container');

  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;

    chatInput.value = '';

    // Append user bubble
    appendMessage('user', text);

    // Typing bubble
    const typingBubble = appendMessage('bot', 'Thinking...');

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, reportId: reportId })
      });
      const data = await response.json();
      typingBubble.remove();
      appendMessage('bot', data.response || "No response received.");
    } catch (err) {
      typingBubble.remove();
      appendMessage('bot', "Connection error. Couldn't reach AURA AI.");
    }
  });

  function appendMessage(sender, msgText) {
    const bubble = document.createElement('div');
    bubble.className = `message-bubble message-${sender}`;
    bubble.innerText = msgText;
    messagesContainer.appendChild(bubble);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return bubble;
  }
}
