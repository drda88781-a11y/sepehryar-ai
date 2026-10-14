/**
 * Sepehryar AI Enterprise - Application Logic & State Controller
 */

// Persian digits helper
function toPersianDigits(n) {
  if (n === null || n === undefined) return '';
  const farsiDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
  return n.toString().replace(/\d/g, (x) => farsiDigits[x]);
}

// Image Lightbox Controllers
window.openImageLightbox = function(url, caption) {
  const modal = document.getElementById('imageLightboxModal');
  const img = document.getElementById('lightboxImg');
  const cap = document.getElementById('lightboxCaption');
  if (modal && img) {
    img.src = url;
    if (cap) cap.textContent = caption ? ('🖼️ ' + caption) : '🖼️ تصویر محیط نرم‌افزار سپهریار';
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
};

window.closeImageLightbox = function() {
  const modal = document.getElementById('imageLightboxModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
};

// Company Contact & Support Modal Controllers
window.openCompanyModal = function() {
  const modal = document.getElementById('companyContactModal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
};

window.closeCompanyModal = function() {
  const modal = document.getElementById('companyContactModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
};

// Global Esc key listener for modals
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    window.closeImageLightbox();
    window.closeCompanyModal();
  }
});

// Robust multi-fallback clipboard copy
function copyTextToClipboard(text, onSuccess, onError) {
  if (!text) return;
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text)
      .then(() => { if (onSuccess) onSuccess(); })
      .catch(() => fallbackCopyText(text, onSuccess, onError));
  } else {
    fallbackCopyText(text, onSuccess, onError);
  }
}

function fallbackCopyText(text, onSuccess, onError) {
  try {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.left = '-9999px';
    ta.style.top = '-9999px';
    ta.style.opacity = '0';
    ta.setAttribute('readonly', '');
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    const successful = document.execCommand('copy');
    document.body.removeChild(ta);
    if (successful) {
      if (onSuccess) onSuccess();
    } else {
      if (onError) onError();
    }
  } catch (err) {
    if (onError) onError(err);
  }
}

// Global button handler for copying code blocks
window.copyCodeBlock = function(btn) {
  try {
    const pre = btn.closest('pre');
    const codeEl = pre ? pre.querySelector('code') : null;
    const text = codeEl ? (codeEl.getAttribute('data-raw') || codeEl.textContent) : '';
    if (!text) return;

    copyTextToClipboard(text, () => {
      const orig = btn.innerHTML;
      btn.innerHTML = '✅ کپی شد!';
      btn.classList.add('copied');
      setTimeout(() => {
        btn.innerHTML = orig;
        btn.classList.remove('copied');
      }, 2000);
    }, () => {
      window.prompt('متن کوئری را با کلیدهای Ctrl+C کپی کنید:', text);
    });
  } catch (e) {
    console.error('Copy code block error:', e);
  }
};

// Global button handler for copying entire assistant message
window.copyMessageText = function(btn) {
  try {
    const row = btn.closest('.message-row');
    const body = row ? row.querySelector('.message-body') : null;
    if (!body) return;
    const text = body.innerText || body.textContent;
    copyTextToClipboard(text, () => {
      const orig = btn.innerHTML;
      btn.innerHTML = '✅ کپی شد!';
      btn.classList.add('copied');
      setTimeout(() => {
        btn.innerHTML = orig;
        btn.classList.remove('copied');
      }, 2000);
    });
  } catch (e) {
    console.error('Copy message error:', e);
  }
};

// Global button handler for executing code in SQL Explorer
window.runCodeBlockInSqlTab = function(btn) {
  try {
    const pre = btn.closest('pre');
    const codeEl = pre ? pre.querySelector('code') : null;
    const text = codeEl ? (codeEl.getAttribute('data-raw') || codeEl.textContent) : '';
    if (text && window.app && typeof window.app.runCodeInSqlTab === 'function') {
      window.app.runCodeInSqlTab(text);
    }
  } catch (e) {
    console.error('Run code error:', e);
  }
};

// Global helper for toggling Thinking Accordion
window.toggleThinking = function(id) {
  const el = document.getElementById(id);
  if (el) {
    el.classList.toggle('open');
  }
};

// Global helper to switch thinking mode
window.setThinkingMode = function(mode) {
  try {
    document.querySelectorAll('#thinkingModeSelector .mode-pill-btn').forEach(b => {
      if (b.getAttribute('data-mode') === mode) {
        b.classList.add('active');
      } else {
        b.classList.remove('active');
      }
    });
    if (window.app) {
      window.app.currentThinkingMode = mode;
    }
  } catch (e) {
    console.error('Error switching thinking mode:', e);
  }
};

// Global helper to send chat message
window.sendChatMessage = function() {
  try {
    if (window.app && typeof window.app.handleSendMessage === 'function') {
      window.app.handleSendMessage();
    }
  } catch (e) {
    console.error('Error sending message:', e);
  }
};

// Global helper to switch workspace tabs
window.switchAppTab = function(tabName) {
  try {
    if (window.app && typeof window.app.switchTab === 'function') {
      window.app.switchTab(tabName);
    }
  } catch (e) {
    console.error('Error switching tab:', e);
  }
};

// Global helper to send prompt chip
window.sendPromptChip = function(elOrText) {
  try {
    const text = typeof elOrText === 'string' ? elOrText : elOrText.getAttribute('data-prompt');
    const input = document.getElementById('chatInput');
    if (input && text) {
      input.value = text;
      if (window.app && typeof window.app.handleSendMessage === 'function') {
        window.app.handleSendMessage();
      }
    }
  } catch (e) {
    console.error('Error sending prompt chip:', e);
  }
};

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// Simple robust Markdown to HTML parser
function renderMarkdown(md) {
  if (!md) return '';
  let html = md;

  // 1. Stash Code blocks ```lang ... ``` before HTML escaping to prevent mangling <, >, quotes
  const codeBlocks = [];
  html = html.replace(/```([a-zA-Z0-9_\-#+]*)\s*([\s\S]*?)```/g, (match, lang, code) => {
    const rawCode = code.trim();
    const cleanLang = (lang || 'sql').toLowerCase();
    const isSql = cleanLang === 'sql' || cleanLang === 'tsql' || cleanLang === '';
    const langLabel = isSql ? 'دستور T-SQL استاندارد سپهریار' : (cleanLang.toUpperCase() || 'کد برنامه');
    
    const idx = codeBlocks.length;
    const displayHtml = escapeHtml(rawCode);
    const rawAttr = escapeHtml(rawCode);

    codeBlocks.push(`
      <pre class="code-container">
        <div class="code-header">
          <span class="code-title">💻 ${langLabel}</span>
          <div class="code-actions">
            <button class="btn-copy-code" onclick="window.copyCodeBlock(this)" title="کپی کردن تمام کوئری">📋 کپی کوئری</button>
            ${isSql ? `<button class="btn-copy-code btn-run-sql" style="margin-right: 6px;" onclick="window.runCodeBlockInSqlTab(this)" title="انتقال و اجرا در تب کاوشگر">⚡ اجرا در کاوشگر</button>` : ''}
          </div>
        </div>
        <code data-raw="${rawAttr}">${displayHtml}</code>
      </pre>
    `);
    return `%%%CODE_BLOCK_${idx}%%%`;
  });

  // 2. Escape basic HTML for the text content
  html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  // Inline code `...`
  html = html.replace(/`([^`]+)`/g, '<code style="background: rgba(0,229,255,0.1); color: #00E5FF; padding: 2px 6px; border-radius: 4px; font-family: monospace;">$1</code>');

  // Helper to render responsive, clickable image cards
  const renderImgCard = (alt, url) => {
    let webUrl = (url || '').trim();
    if (webUrl.includes('knowledge_base/manuals/images/') || webUrl.startsWith('file:///')) {
      const parts = webUrl.split('/');
      const filename = parts[parts.length - 1];
      webUrl = `/images/${filename}`;
    }
    const cleanAlt = (alt || 'تصویر محیط نرم‌افزار سپهریار').trim();
    const safeEscaped = cleanAlt.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    return `<div class="chat-image-card">
      <div class="chat-image-preview-wrapper" onclick="window.openImageLightbox('${webUrl}', '${safeEscaped}')" title="برای مشاهده بزرگ‌نمایی کلیک کنید">
        <img src="${webUrl}" alt="${safeEscaped}" class="chat-manual-img" loading="lazy">
        <div class="chat-image-zoom-overlay">🔍 مشاهده تمام‌صفحه</div>
      </div>
      <div class="chat-image-footer">
        <span class="img-caption">🖼️ ${cleanAlt}</span>
        <a href="${webUrl}" target="_blank" rel="noopener noreferrer" class="img-external-link" title="دانلود یا مشاهده در تب مجزا">⤢ مشاهده مستقیم</a>
      </div>
    </div>`;
  };

  // 1. Standard markdown images ![alt](url)
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (match, alt, url) => renderImgCard(alt, url));

  // 2. Links pointing to image files or local file paths [alt](...png)
  html = html.replace(/\[([^\]]*)\]\(([^)]+\.(?:png|PNG|jpg|JPG|jpeg|JPEG|webp|gif))\)/g, (match, alt, url) => renderImgCard(alt, url));
  html = html.replace(/\[([^\]]*)\]\((file:\/\/\/[^)]+)\)/g, (match, alt, url) => renderImgCard(alt, url));

  // 3. Raw file:/// image URLs in text
  html = html.replace(/(?:file:\/\/\/[^\s<)"']+[\/\\]([^\s<)"']+\.(?:png|PNG|jpg|JPG|jpeg|JPEG|webp)))/g, (match, filename) => {
    return renderImgCard('تصویر محیط نرم‌افزار سپهریار', `/images/${filename}`);
  });

  // Regular web links [text](url)
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" style="color: var(--accent-cyan); text-decoration: underline;">$1</a>');

  // Headings
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

  // Bold & Italic
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  // Unordered list items
  html = html.replace(/^\* (.*$)/gim, '<li>$1</li>');
  html = html.replace(/^- (.*$)/gim, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/gim, '<ul>$1</ul>');

  // Markdown Tables (| ... |)
  html = html.replace(/((?:\|[^\n]+\|\r?\n?)+)/g, (match) => {
    const lines = match.trim().split(/\r?\n/).filter(l => l.trim().startsWith('|'));
    if (lines.length < 2) return match;
    
    let headerLine = lines[0];
    let dataStartIdx = 1;
    if (lines[1] && lines[1].includes('---')) {
      dataStartIdx = 2;
    }
    
    const parseCells = (row) => row.split('|').slice(1, -1).map(c => c.trim());
    const headers = parseCells(headerLine);
    
    let tableHtml = '<div class="table-container" style="overflow-x:auto; margin: 14px 0; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px;"><table class="data-table" style="width:100%; border-collapse: collapse; font-size: 0.88rem;">';
    tableHtml += '<thead><tr style="background: rgba(0, 229, 255, 0.08); border-bottom: 2px solid rgba(0, 229, 255, 0.2);">';
    headers.forEach(h => {
      tableHtml += `<th style="padding: 10px 14px; text-align: right; color: var(--accent-cyan); font-weight: 600;">${h}</th>`;
    });
    tableHtml += '</tr></thead><tbody>';
    
    for (let i = dataStartIdx; i < lines.length; i++) {
      const cells = parseCells(lines[i]);
      const bg = i % 2 === 0 ? 'background: rgba(255,255,255,0.02);' : '';
      tableHtml += `<tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.05); ${bg}">`;
      cells.forEach(c => {
        tableHtml += `<td style="padding: 8px 14px; text-align: right; color: var(--text-main);">${c}</td>`;
      });
      tableHtml += '</tr>';
    }
    tableHtml += '</tbody></table></div>';
    return tableHtml;
  });

  // Paragraphs
  html = html.split('\n\n').map(p => {
    p = p.trim();
    if (!p) return '';
    if (p.startsWith('<h') || p.startsWith('<pre') || p.startsWith('<ul') || p.startsWith('<table') || p.startsWith('<div')) return p;
    return `<p>${p.replace(/\n/g, '<br>')}</p>`;
  }).join('');

  // Restore Code blocks
  codeBlocks.forEach((block, idx) => {
    html = html.replace(`%%%CODE_BLOCK_${idx}%%%`, block);
  });

  return html;
}

class SepehryarApp {
  constructor() {
    this.currentTab = 'chat';
    this.selectedDb = 'Sepehr_Main2_1405';
    this.lastSqlResult = null;
    this.currentThinkingMode = 'balanced';

    this.initElements();
    this.initEvents();
    this.initHealthPolling();
  }

  initElements() {
    // Navigation items
    this.navItems = document.querySelectorAll('.nav-item');
    this.views = document.querySelectorAll('.view-panel');

    // Header controls
    this.dbSelect = document.getElementById('dbSelector');
    this.statusPill = document.getElementById('systemStatusPill');
    this.statusText = document.getElementById('systemStatusText');
    this.btnDbToggle = document.getElementById('btnDbToggle');
    this.dbToggleText = document.getElementById('dbToggleText');
    this.isDbConnected = false;

    // Chat elements
    this.messagesStream = document.getElementById('messagesStream');
    this.chatInput = document.getElementById('chatInput');
    this.btnSend = document.getElementById('btnSend');

    // SQL Explorer elements
    this.sqlPresets = document.getElementById('sqlPresets');
    this.sqlEditor = document.getElementById('sqlEditor');
    this.btnExecuteSql = document.getElementById('btnExecuteSql');
    this.resultsTable = document.getElementById('resultsTable');
    this.tableHeader = document.getElementById('tableHeader');
    this.tableBody = document.getElementById('tableBody');
    this.totalRowsCount = document.getElementById('totalRowsCount');
    this.executionTime = document.getElementById('executionTime');
    this.btnExportCsv = document.getElementById('btnExportCsv');

    // Spotlight elements
    this.spotlightTrigger = document.getElementById('spotlightTrigger');
    this.spotlightModal = document.getElementById('spotlightModal');
    this.spotlightInput = document.getElementById('spotlightInput');
  }

  initEvents() {
    // Brand Logo toggle between dark/white/neon variations
    const brandLogo = document.getElementById('brandLogo');
    if (brandLogo) {
      let logoImg = brandLogo.querySelector('.brand-logo-img');
      if (!logoImg) {
        brandLogo.innerHTML = '<img src="images/logo_badge_dark.png?v=10" alt="لوگوی سپهریار" class="brand-logo-img">';
        logoImg = brandLogo.querySelector('.brand-logo-img');
      }
      const logoThemes = [
        'images/logo_badge_dark.png?v=10',
        'images/logo_badge_white.png?v=10',
        'images/logo_badge_neon.png?v=10'
      ];
      let curLogo = 0;
      try {
        curLogo = parseInt(localStorage.getItem('sepehryar_logo_idx') || '0', 10);
      } catch (e) {
        curLogo = 0;
      }
      if (curLogo >= logoThemes.length) curLogo = 0;
      if (logoImg) logoImg.src = logoThemes[curLogo];

      brandLogo.addEventListener('click', () => {
        curLogo = (curLogo + 1) % logoThemes.length;
        if (logoImg) logoImg.src = logoThemes[curLogo];
        try {
          localStorage.setItem('sepehryar_logo_idx', curLogo.toString());
        } catch (e) {}
      });
    }

    // Tab switching
    this.navItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        const tab = item.getAttribute('data-tab');
        this.switchTab(tab);
      });
    });

    // Database change
    if (this.dbSelect) {
      this.dbSelect.addEventListener('change', (e) => {
        this.selectedDb = e.target.value;
      });
    }

    // Database manual toggle
    if (this.btnDbToggle) {
      this.btnDbToggle.addEventListener('click', () => this.handleToggleDatabase());
    }

    // Chat send
    if (this.btnSend && this.chatInput) {
      this.btnSend.addEventListener('click', () => this.handleSendMessage());
      this.chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.handleSendMessage();
        }
      });
      // Auto-grow textarea without scrollbar arrows
      this.chatInput.addEventListener('input', () => {
        this.chatInput.style.height = 'auto';
        this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 140) + 'px';
      });
    }

    // Thinking Depth Mode Selector (Fast, Balanced, Deep Audit)
    document.querySelectorAll('#thinkingModeSelector .mode-pill-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#thinkingModeSelector .mode-pill-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentThinkingMode = btn.getAttribute('data-mode') || 'balanced';
      });
    });

    // Quick Prompt Chips
    document.querySelectorAll('.chip-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const text = btn.getAttribute('data-prompt');
        if (text && this.chatInput) {
          this.chatInput.value = text;
          this.handleSendMessage();
        }
      });
    });

    // SQL Presets
    if (this.sqlPresets) {
      this.sqlPresets.addEventListener('change', (e) => {
        const val = e.target.value;
        if (val && this.sqlEditor) {
          this.sqlEditor.value = val;
        }
      });
    }

    // SQL Execute
    if (this.btnExecuteSql) {
      this.btnExecuteSql.addEventListener('click', () => this.handleExecuteSql());
    }

    // CSV Export
    if (this.btnExportCsv) {
      this.btnExportCsv.addEventListener('click', () => this.handleExportCsv());
    }

    // Spotlight Modal Events
    if (this.spotlightTrigger) {
      this.spotlightTrigger.addEventListener('click', () => this.openSpotlight());
    }

    if (this.spotlightModal) {
      this.spotlightModal.addEventListener('click', (e) => {
        if (e.target === this.spotlightModal) this.closeSpotlight();
      });
    }

    if (this.spotlightInput) {
      this.spotlightInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          const val = this.spotlightInput.value.trim();
          if (val) {
            this.closeSpotlight();
            this.switchTab('chat');
            if (this.chatInput) {
              this.chatInput.value = val;
              this.handleSendMessage();
            }
          }
        } else if (e.key === 'Escape') {
          this.closeSpotlight();
        }
      });
    }

    // Global Shortcut Ctrl + Space for Spotlight
    window.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.code === 'Space') {
        e.preventDefault();
        this.openSpotlight();
      }
      if (e.key === 'Escape' && this.spotlightModal.classList.contains('open')) {
        this.closeSpotlight();
      }
    });
  }

  switchTab(tabName) {
    this.currentTab = tabName;
    this.navItems.forEach(item => {
      item.classList.toggle('active', item.getAttribute('data-tab') === tabName);
    });
    this.views.forEach(view => {
      view.classList.toggle('active', view.id === `view-${tabName}`);
    });

    // Refresh tab-specific data
    if (tabName === 'health') {
      this.loadHealthDiagnostics();
    }
  }

  openSpotlight() {
    if (!this.spotlightModal) return;
    this.spotlightModal.classList.add('open');
    setTimeout(() => {
      if (this.spotlightInput) {
        this.spotlightInput.focus();
        this.spotlightInput.select();
      }
    }, 50);
  }

  closeSpotlight() {
    if (!this.spotlightModal) return;
    this.spotlightModal.classList.remove('open');
  }

  /* ==================== Chat Controller ==================== */
  async handleSendMessage() {
    const query = this.chatInput.value.trim();
    if (!query) return;

    this.chatInput.value = '';
    this.btnSend.disabled = true;

    // Render User Message
    this.appendMessage('user', query);

    // Dynamic Thinking & Response Component IDs
    const timestamp = Date.now();
    const loadingId = 'loading-' + timestamp;
    const accordionId = 'think-acc-' + timestamp;
    const timerId = 'think-timer-' + timestamp;
    const stepsChipId = 'think-steps-' + timestamp;
    const timelineId = 'think-timeline-' + timestamp;
    const subtextId = 'think-subtext-' + timestamp;
    const waveId = 'think-wave-' + timestamp;
    const titleTextId = 'think-title-' + timestamp;
    const answerContainerId = 'think-ans-' + timestamp;

    // Mode specifics
    const activeMode = this.currentThinkingMode || 'balanced';
    let initialModeIcon = '🧠';
    let initialModeTitle = 'در حال تفکر و تحلیل عمیق...';
    let initialSubtext = 'تحلیل ساختار پرسش و انطباق با پایگاه داده و استانداردهای سپهریار...';
    let modeBadgeLabel = '🧠 حالت متعادل';

    if (activeMode === 'fast') {
      initialModeIcon = '⚡';
      initialModeTitle = 'در حال استخراج سریع پاسخ...';
      initialSubtext = 'پاسخ مستقیم بدون تاخیر استدلال چندمرحله‌ای (Fast Mode)';
      modeBadgeLabel = '⚡ حالت سریع';
    } else if (activeMode === 'deep') {
      initialModeIcon = '🔬';
      initialModeTitle = 'در حال حسابرسی عمیق با ۷ ایجنت تخصصی...';
      initialSubtext = 'کاوش چندلایه در اسکیما، تحلیل ترازهای مالی و بازرسی سخت‌گیرانه Critic';
      modeBadgeLabel = '🔬 حسابرسی عمیق';
    }

    const initialThinkingHtml = `
      <div id="${accordionId}" class="thinking-loader-simple" style="display: flex; align-items: center; gap: 8px; color: var(--text-muted); font-size: 0.88rem; padding: 6px 0;">
        <span style="display:inline-block; animation: pulse 1.2s infinite; color: var(--accent-cyan);">✍️</span>
        <span id="${subtextId}">در حال تدوین آموزش گام‌به‌گام...</span>
      </div>
      <div class="message-answer-stream" id="${answerContainerId}"></div>
    `;

    this.appendMessage('assistant', initialThinkingHtml, loadingId);

    const startTime = Date.now();
    let thinkingCompleted = false;

    const markThinkingDone = () => {
      if (thinkingCompleted) return;
      thinkingCompleted = true;
      const loaderEl = document.getElementById(accordionId);
      if (loaderEl) {
        loaderEl.style.display = 'none';
      }
    };

    const addThinkingStep = (stepObj) => {
      // Optional minimal step subtext
      const subtextEl = document.getElementById(subtextId);
      if (subtextEl && stepObj.detail) {
        subtextEl.textContent = stepObj.detail;
      }
    };

    let accumulatedText = '';
    let renderAnimationFrame = null;

    const doRenderProgressive = () => {
      markThinkingDone();
      const ansEl = document.getElementById(answerContainerId);
      if (!ansEl) return;
      ansEl.innerHTML = `
        <div class="rendered-answer">
          ${renderMarkdown(accumulatedText)}
          <span class="streaming-cursor"></span>
        </div>
      `;
      this.messagesStream.scrollTop = this.messagesStream.scrollHeight;
    };

    const finishResponse = () => {
      markThinkingDone();
      if (renderAnimationFrame) cancelAnimationFrame(renderAnimationFrame);

      const ansEl = document.getElementById(answerContainerId);
      if (ansEl) {
        ansEl.innerHTML = `
          <div class="rendered-answer fade-in-reveal">
            ${renderMarkdown(accumulatedText || 'پاسخی دریافت نشد.')}
          </div>
        `;
      }
      this.btnSend.disabled = false;
      this.messagesStream.scrollTop = this.messagesStream.scrollHeight;
    };

    try {
      if (window.apiClient && typeof window.apiClient.sendChatStream === 'function') {
        let isDoneHandled = false;
        await window.apiClient.sendChatStream(
          query,
          this.selectedDb,
          (token) => {
            // First answer token arrived: close active thinking phase
            markThinkingDone();
            accumulatedText += token;
            if (!renderAnimationFrame) {
              renderAnimationFrame = requestAnimationFrame(() => {
                renderAnimationFrame = null;
                doRenderProgressive();
              });
            }
          },
          () => {
            if (!isDoneHandled) {
              isDoneHandled = true;
              finishResponse();
            }
          },
          async (streamErr) => {
            if (isDoneHandled) return;
            console.warn('Stream fallback to standard sendChat:', streamErr);
            const res = await window.apiClient.sendChat(query, this.selectedDb, null, activeMode);
            if (res.reasoning_steps && res.reasoning_steps.length) {
              for (const s of res.reasoning_steps) {
                addThinkingStep({ title: s, detail: '' });
              }
            }
            accumulatedText = res.persian_answer || '';
            const tSec = res.thinking_duration_ms ? (res.thinking_duration_ms / 1000).toFixed(1) : null;
            markThinkingDone(tSec);
            isDoneHandled = true;
            finishResponse();
          },
          (stepData) => {
            addThinkingStep(stepData);
          },
          (doneData) => {
            const durSec = doneData.duration_ms ? (doneData.duration_ms / 1000).toFixed(1) : null;
            markThinkingDone(durSec);
          },
          activeMode
        );
      } else {
        const res = await window.apiClient.sendChat(query, this.selectedDb, null, activeMode);
        if (res.reasoning_steps && res.reasoning_steps.length) {
          for (const s of res.reasoning_steps) {
            addThinkingStep({ title: s, detail: '' });
          }
        }
        accumulatedText = res.persian_answer || '';
        const tSec = res.thinking_duration_ms ? (res.thinking_duration_ms / 1000).toFixed(1) : null;
        markThinkingDone(tSec);
        finishResponse();
      }
    } catch (err) {
      markThinkingDone();
      const ansEl = document.getElementById(answerContainerId);
      if (ansEl) {
        ansEl.innerHTML = `
          <div style="color: var(--accent-rose); font-weight: 600; padding: 8px 0;">
            ⚠️ خطا در برقراری ارتباط: ${err.message}
          </div>
        `;
      }
      this.btnSend.disabled = false;
      this.messagesStream.scrollTop = this.messagesStream.scrollHeight;
    }
  }

  appendMessage(role, htmlContent, id = null) {
    const row = document.createElement('div');
    row.className = `message-row ${role}`;
    if (id) row.id = id;

    const userAvatarSvg = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:block;">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
        <circle cx="12" cy="7" r="4"></circle>
      </svg>
    `;

    const aiAvatarSvg = `
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" style="display:block;">
        <path d="M12 2L14.8 9.2L22 12L14.8 14.8L12 22L9.2 14.8L2 12L9.2 9.2L12 2Z" fill="url(#aiBadgeGradDynamic)"/>
        <circle cx="12" cy="12" r="3" fill="#FFFFFF"/>
        <defs>
          <linearGradient id="aiBadgeGradDynamic" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
            <stop stop-color="#00E5FF"/>
            <stop offset="1" stop-color="#3B82F6"/>
          </linearGradient>
        </defs>
      </svg>
    `;

    const avatarIcon = role === 'user' ? userAvatarSvg : aiAvatarSvg;
    const authorName = role === 'user' ? 'شما' : 'مربی هوشمند سپهریار';

    row.innerHTML = `
      <div class="avatar" title="${authorName}">${avatarIcon}</div>
      <div class="message-content">
        <div class="message-meta">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="author-name">${authorName}</span>
            <span>${new Date().toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' })}</span>
          </div>
          ${role === 'assistant' ? `<button class="btn-copy-msg" onclick="window.copyMessageText(this)" title="کپی کردن متن کامل این پاسخ">📋 کپی کل پاسخ</button>` : ''}
        </div>
        <div class="message-body">${htmlContent}</div>
      </div>
    `;

    this.messagesStream.appendChild(row);
    this.messagesStream.scrollTop = this.messagesStream.scrollHeight;
  }

  /* ==================== SQL Explorer Controller ==================== */
  runCodeInSqlTab(sql) {
    this.switchTab('sql');
    if (this.sqlEditor) {
      this.sqlEditor.value = sql;
      this.sqlEditor.focus();
      this.sqlEditor.scrollIntoView({ behavior: 'smooth', block: 'center' });
      if (this.isDbConnected || this.selectedDb === 'DEMO') {
        this.handleExecuteSql();
      }
    }
  }

  async handleExecuteSql() {
    const sql = this.sqlEditor.value.trim();
    if (!sql) return;

    if (!this.isDbConnected && this.selectedDb !== 'DEMO') {
      const wantConnect = confirm('اتصال به پایگاه داده در حال حاضر غیرفعال (قطع) است.\nآیا مایلید ابتدا اتصال به دیتابیس را برقرار کنید؟');
      if (wantConnect) {
        await this.handleToggleDatabase();
        if (!this.isDbConnected) return;
      } else {
        return;
      }
    }

    this.btnExecuteSql.disabled = true;
    this.btnExecuteSql.textContent = 'در حال اجرا...';

    try {
      const res = await window.apiClient.executeSql(sql, this.selectedDb);
      this.lastSqlResult = res;

      this.totalRowsCount.textContent = res.total_rows || 0;
      this.executionTime.textContent = `${res.duration_ms || 0} ms`;

      this.renderTable(res.columns || [], res.rows || []);
      if (this.btnExportCsv) this.btnExportCsv.disabled = false;
    } catch (err) {
      alert(`خطا در اجرای کوئری: ${err.message}`);
    } finally {
      this.btnExecuteSql.disabled = false;
      this.btnExecuteSql.innerHTML = '⚡ اجرای کوئری امن (F5)';
    }
  }

  renderTable(columns, rows) {
    if (!this.tableHeader || !this.tableBody) return;

    this.tableHeader.innerHTML = '';
    this.tableBody.innerHTML = '';

    if (columns.length === 0 || rows.length === 0) {
      this.tableBody.innerHTML = '<tr><td colspan="100%" style="text-align: center; color: var(--text-muted); padding: 20px;">هیچ رکوردی یافت نشد.</td></tr>';
      return;
    }

    // Header
    const trHead = document.createElement('tr');
    columns.forEach(col => {
      const th = document.createElement('th');
      th.textContent = col;
      trHead.appendChild(th);
    });
    this.tableHeader.appendChild(trHead);

    // Rows
    rows.forEach(row => {
      const tr = document.createElement('tr');
      columns.forEach(col => {
        const td = document.createElement('td');
        const val = row[col];
        td.textContent = (val !== null && val !== undefined) ? String(val) : '-';
        tr.appendChild(td);
      });
      this.tableBody.appendChild(tr);
    });
  }

  handleExportCsv() {
    if (!this.lastSqlResult || !this.lastSqlResult.rows || this.lastSqlResult.rows.length === 0) {
      alert('داده‌ای برای دانلود وجود ندارد.');
      return;
    }

    const cols = this.lastSqlResult.columns;
    const rows = this.lastSqlResult.rows;

    let csvContent = '\uFEFF'; // UTF-8 BOM for Excel Persian display
    csvContent += cols.join(',') + '\n';

    rows.forEach(row => {
      const line = cols.map(col => {
        let val = row[col];
        if (val === null || val === undefined) val = '';
        val = String(val).replace(/"/g, '""');
        return `"${val}"`;
      }).join(',');
      csvContent += line + '\n';
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `Sepehryar_Export_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  /* ==================== Health Polling ==================== */
  initHealthPolling() {
    this.updateHealth();
    setInterval(() => this.updateHealth(), 15000);
  }

  async updateHealth() {
    const health = await window.apiClient.checkHealth();
    if (health.status === 'ok') {
      this.isDbConnected = !!health.db_connected;
      this.renderDbConnectionState(this.isDbConnected, health.database);
    } else {
      if (this.statusText) this.statusText.textContent = 'عدم اتصال به سرور';
      if (this.statusPill) this.statusPill.className = 'status-pill disconnected';
    }
  }

  renderDbConnectionState(isConnected, dbName) {
    if (this.btnDbToggle && this.dbToggleText) {
      const icon = this.btnDbToggle.querySelector('.db-toggle-icon');
      if (isConnected) {
        this.btnDbToggle.className = 'btn-db-toggle connected';
        if (icon) icon.textContent = '🔌';
        this.dbToggleText.textContent = 'قطع اتصال';
      } else {
        this.btnDbToggle.className = 'btn-db-toggle disconnected';
        if (icon) icon.textContent = '⚡';
        this.dbToggleText.textContent = 'اتصال به دیتابیس';
      }
    }

    if (this.statusPill && this.statusText) {
      if (isConnected) {
        this.statusPill.className = 'status-pill';
        this.statusText.textContent = `دیتابیس: متصل (${dbName || this.selectedDb})`;
      } else {
        this.statusPill.className = 'status-pill disconnected';
        this.statusText.textContent = 'دیتابیس: غیرفعال (پیش‌فرض)';
      }
    }
  }

  async handleToggleDatabase() {
    if (!this.btnDbToggle) return;
    this.btnDbToggle.disabled = true;

    try {
      if (this.isDbConnected) {
        // Disconnect
        await window.apiClient.disconnectDatabase();
        this.isDbConnected = false;
        this.renderDbConnectionState(false, null);
      } else {
        // Connect
        const icon = this.btnDbToggle.querySelector('.db-toggle-icon');
        if (icon) icon.textContent = '⏳';
        if (this.dbToggleText) this.dbToggleText.textContent = 'در حال اتصال...';

        const res = await window.apiClient.connectDatabase(this.selectedDb);
        if (res.connected) {
          this.isDbConnected = true;
          this.renderDbConnectionState(true, res.database);
          if (res.databases && res.databases.length > 0 && this.dbSelect) {
            const currentVal = this.selectedDb;
            this.dbSelect.innerHTML = '';
            res.databases.forEach(db => {
              const opt = document.createElement('option');
              opt.value = db;
              opt.textContent = db;
              if (db === currentVal) opt.selected = true;
              this.dbSelect.appendChild(opt);
            });
            if (res.databases.includes(currentVal)) {
              this.dbSelect.value = currentVal;
            } else {
              this.selectedDb = res.databases[0];
            }
          }
        } else {
          alert(`خطا در اتصال به دیتابیس: ${res.message || 'پاسخی دریافت نشد'}`);
          this.renderDbConnectionState(false, null);
        }
      }
    } catch (err) {
      alert(`خطا در تغییر وضعیت دیتابیس: ${err.message}`);
      this.renderDbConnectionState(this.isDbConnected, null);
    } finally {
      this.btnDbToggle.disabled = false;
    }
  }

  async loadHealthDiagnostics() {
    try {
      const diag = await window.apiClient.getDiagnostics();
      const listEl = document.getElementById('healthChecksList');
      if (!listEl) return;

      listEl.innerHTML = '';
      if (diag.checks) {
        diag.checks.forEach(chk => {
          const item = document.createElement('div');
          item.className = 'check-item';
          item.innerHTML = `
            <div class="check-lead">
              <span style="font-size: 1.1rem;">${chk.status === 'healthy' ? '✅' : '⚠️'}</span>
              <div>
                <strong>${chk.title}</strong>
                <div style="font-size: 0.8rem; color: var(--text-muted);">${chk.message}</div>
              </div>
            </div>
            <span class="check-status-badge ${chk.status}">${chk.value || chk.status}</span>
          `;
          listEl.appendChild(item);
        });
      }
    } catch (err) {
      console.warn('Failed to load diagnostics:', err);
    }
  }
}

// Robust application bootstrap
function bootSepehryarApp() {
  if (!window.app) {
    try {
      window.app = new SepehryarApp();
    } catch (e) {
      console.error('Fatal initialization error in SepehryarApp:', e);
    }
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bootSepehryarApp);
} else {
  bootSepehryarApp();
}
