/**
 * AI Warrior widget — drop-in web component for The Kiwi Dialectic.
 *
 * Usage on any HTML page:
 *
 *   <script type="module" src="/ai-warrior/assets/js/ai-warrior-widget.js"></script>
 *
 *   <!-- Reo helper -->
 *   <ai-warrior-widget mode="reo" endpoint="https://ai-warrior-tutor.YOURNAME.workers.dev"></ai-warrior-widget>
 *
 *   <!-- Course tutor -->
 *   <ai-warrior-widget mode="tutor" endpoint="https://ai-warrior-tutor.YOURNAME.workers.dev"></ai-warrior-widget>
 *
 * Attributes:
 *   mode       "reo" | "tutor"                     (required)
 *   endpoint   full URL of the Worker              (required)
 *   subscriber-id  optional, identifies a paid Kiwi Dialectic subscriber
 *
 * Pure vanilla. No framework. Shadow DOM = no CSS bleed into host page.
 */

const PROMPTS = {
  reo: {
    label: 'Reo Helper',
    placeholder: 'Ask in English or te reo Māori — translation, macrons, phrasing…',
    intro:
      'Tēnā koe. I help with te reo Māori translation and explanations for the AI Warrior course. Ask me anything.',
  },
  tutor: {
    label: 'Course Tutor',
    placeholder: 'Ask about Gramsci, Kropotkin, Graeber, Freire, Deleuze, Bakunin — or anything in the course…',
    intro:
      "Kia ora. I'm the AI Warrior tutor. I'll ask sharpening questions, not give you commandments. What are you working through?",
  },
};

const STYLES = `
  :host {
    display: block;
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
    --bg: #f7f6f2;
    --surface: #fbfbf9;
    --border: #d4d1ca;
    --text: #28251d;
    --muted: #7a7974;
    --primary: #01696f;
    --primary-hover: #0c4e54;
    --user-bg: #01696f;
    --user-fg: #ffffff;
    --bot-bg: #ffffff;
    --bot-fg: #28251d;
    --error: #a12c7b;
    --radius: 14px;
    color: var(--text);
  }
  .wrap {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    max-height: 600px;
    min-height: 380px;
  }
  .head {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 10px;
    background: var(--surface);
  }
  .dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--primary);
    animation: pulse 2s ease-in-out infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.45; }
  }
  .title { font-weight: 600; font-size: 14px; }
  .quota { margin-left: auto; font-size: 11px; color: var(--muted); font-variant-numeric: tabular-nums; }
  .log {
    flex: 1;
    overflow-y: auto;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    background: var(--bg);
  }
  .msg {
    max-width: 86%;
    padding: 10px 13px;
    border-radius: 12px;
    font-size: 14px;
    line-height: 1.5;
    white-space: pre-wrap;
    word-wrap: break-word;
  }
  .msg.user {
    align-self: flex-end;
    background: var(--user-bg);
    color: var(--user-fg);
    border-bottom-right-radius: 4px;
  }
  .msg.bot {
    align-self: flex-start;
    background: var(--bot-bg);
    color: var(--bot-fg);
    border: 1px solid var(--border);
    border-bottom-left-radius: 4px;
  }
  .msg.system {
    align-self: center;
    background: transparent;
    color: var(--muted);
    font-style: italic;
    font-size: 12px;
    max-width: 100%;
    text-align: center;
  }
  .upgrade {
    align-self: stretch;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px;
    font-size: 13px;
    color: var(--text);
  }
  .upgrade h3 {
    margin: 0 0 6px;
    font-size: 14px;
    font-weight: 600;
  }
  .upgrade p { margin: 0 0 10px; color: var(--muted); }
  .upgrade .ctas { display: flex; gap: 8px; flex-wrap: wrap; }
  .upgrade a {
    display: inline-block;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    text-decoration: none;
    border: 1px solid var(--border);
  }
  .upgrade a.primary {
    background: var(--primary);
    color: #fff;
    border-color: var(--primary);
  }
  .upgrade a.primary:hover { background: var(--primary-hover); }
  .upgrade a.secondary {
    background: transparent;
    color: var(--primary);
  }
  .upgrade a.secondary:hover { background: var(--surface); }
  .upgrade .footnote {
    margin-top: 10px; font-size: 11px; color: var(--muted);
  }
  .input {
    border-top: 1px solid var(--border);
    padding: 10px;
    display: flex;
    gap: 8px;
    background: var(--surface);
  }
  textarea {
    flex: 1;
    resize: none;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 10px;
    font: inherit;
    font-size: 14px;
    line-height: 1.4;
    background: #fff;
    color: var(--text);
    min-height: 38px;
    max-height: 120px;
  }
  textarea:focus { outline: 2px solid var(--primary); outline-offset: -1px; border-color: var(--primary); }
  button {
    background: var(--primary);
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 0 16px;
    font: inherit;
    font-weight: 500;
    font-size: 14px;
    cursor: pointer;
    min-width: 72px;
  }
  button:hover:not(:disabled) { background: var(--primary-hover); }
  button:disabled { opacity: 0.5; cursor: not-allowed; }
  .typing {
    align-self: flex-start;
    display: flex;
    gap: 4px;
    padding: 12px 14px;
    background: var(--bot-bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    border-bottom-left-radius: 4px;
  }
  .typing span {
    width: 6px; height: 6px; border-radius: 50%; background: var(--muted);
    animation: bounce 1.2s ease-in-out infinite;
  }
  .typing span:nth-child(2) { animation-delay: 0.15s; }
  .typing span:nth-child(3) { animation-delay: 0.3s; }
  @keyframes bounce {
    0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
    40% { transform: translateY(-4px); opacity: 1; }
  }
  @media (prefers-color-scheme: dark) {
    :host {
      --bg: #171614; --surface: #1c1b19; --border: #393836;
      --text: #cdccca; --muted: #797876; --primary: #4f98a3;
      --primary-hover: #227f8b; --user-bg: #4f98a3; --user-fg: #0a0a09;
      --bot-bg: #201f1d; --bot-fg: #cdccca;
    }
    textarea { background: #0f0e0d; }
  }
`;

class AIWarriorWidget extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.history = [];
    this.busy = false;
  }

  connectedCallback() {
    const mode = this.getAttribute('mode') || 'tutor';
    const endpoint = this.getAttribute('endpoint');
    this.subscriberId = this.getAttribute('subscriber-id') || null;

    if (!endpoint) {
      this.shadowRoot.innerHTML = `<style>${STYLES}</style><div class="wrap"><div class="head"><div class="title">AI Warrior widget</div></div><div class="log"><div class="msg system">Missing required attribute: endpoint</div></div></div>`;
      return;
    }

    this.mode = mode;
    this.endpoint = endpoint.replace(/\/$/, '');
    this.config = PROMPTS[mode] || PROMPTS.tutor;
    this.render();
  }

  render() {
    this.shadowRoot.innerHTML = `
      <style>${STYLES}</style>
      <div class="wrap">
        <div class="head">
          <div class="dot"></div>
          <div class="title">${this.config.label}</div>
          <div class="quota" id="quota"></div>
        </div>
        <div class="log" id="log" role="log" aria-live="polite"></div>
        <div class="input">
          <textarea
            id="input"
            placeholder="${this.config.placeholder}"
            aria-label="Message"
            rows="1"></textarea>
          <button id="send">Send</button>
        </div>
      </div>
    `;

    this.logEl = this.shadowRoot.getElementById('log');
    this.inputEl = this.shadowRoot.getElementById('input');
    this.sendEl = this.shadowRoot.getElementById('send');
    this.quotaEl = this.shadowRoot.getElementById('quota');

    this.appendMessage('bot', this.config.intro);

    this.sendEl.addEventListener('click', () => this.send());
    this.inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.send();
      }
    });
    this.inputEl.addEventListener('input', () => {
      this.inputEl.style.height = 'auto';
      this.inputEl.style.height = Math.min(120, this.inputEl.scrollHeight) + 'px';
    });
  }

  appendMessage(role, text) {
    const el = document.createElement('div');
    el.className = `msg ${role}`;
    el.textContent = text;
    this.logEl.appendChild(el);
    this.logEl.scrollTop = this.logEl.scrollHeight;
    return el;
  }

  showTyping() {
    const el = document.createElement('div');
    el.className = 'typing';
    el.id = 'typing';
    el.innerHTML = '<span></span><span></span><span></span>';
    this.logEl.appendChild(el);
    this.logEl.scrollTop = this.logEl.scrollHeight;
  }

  hideTyping() {
    const t = this.shadowRoot.getElementById('typing');
    if (t) t.remove();
  }

  updateQuota(usage) {
    if (!usage) { this.quotaEl.textContent = ''; return; }
    const { used, limit, is_pro } = usage;
    if (!limit || limit === 0) { this.quotaEl.textContent = is_pro ? 'pro · unlimited' : ''; return; }
    this.quotaEl.textContent = `${used}/${limit} ${is_pro ? 'pro' : 'free'}`;
  }

  showUpgrade(data) {
    const card = document.createElement('div');
    card.className = 'upgrade';
    card.innerHTML = `
      <h3>You've used your quota for this month</h3>
      <p>${escapeHtml(data.message || '')}</p>
      <div class="ctas">
        ${data.upgrade_url ? `<a class="primary" href="${escapeAttr(data.upgrade_url)}" target="_blank" rel="noopener">Upgrade subscription</a>` : ''}
        ${data.perplexity_referral_url ? `<a class="secondary" href="${escapeAttr(data.perplexity_referral_url)}" target="_blank" rel="noopener">Get Perplexity Pro</a>` : ''}
      </div>
      <div class="footnote">Perplexity is the research and management tool the AI Warrior course uses. Using the referral link supports The Kiwi Dialectic at no extra cost.</div>
    `;
    this.logEl.appendChild(card);
    this.logEl.scrollTop = this.logEl.scrollHeight;
  }

  async send() {
    if (this.busy) return;
    const text = this.inputEl.value.trim();
    if (!text) return;
    this.busy = true;
    this.sendEl.disabled = true;
    this.inputEl.disabled = true;

    this.appendMessage('user', text);
    this.history.push({ role: 'user', content: text });
    this.inputEl.value = '';
    this.inputEl.style.height = 'auto';
    this.showTyping();

    try {
      const res = await fetch(`${this.endpoint}/${this.mode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: this.history,
          ...(this.subscriberId ? { subscriber_id: this.subscriberId } : {}),
        }),
      });
      this.hideTyping();

      if (res.status === 402) {
        const data = await res.json();
        this.showUpgrade(data);
        this.updateQuota({ used: data.used, limit: data.limit, is_pro: data.is_pro });
        return;
      }

      if (!res.ok) {
        const detail = await res.text();
        this.appendMessage('system', `Error ${res.status}: ${detail.slice(0, 200)}`);
        return;
      }

      const data = await res.json();
      const reply = data.reply || '(no response)';
      this.history.push({ role: 'assistant', content: reply });
      this.appendMessage('bot', reply);
      this.updateQuota(data.usage);
    } catch (err) {
      this.hideTyping();
      this.appendMessage('system', `Network error: ${err && err.message ? err.message : err}`);
    } finally {
      this.busy = false;
      this.sendEl.disabled = false;
      this.inputEl.disabled = false;
      this.inputEl.focus();
    }
  }
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
function escapeAttr(s) {
  return escapeHtml(s);
}

customElements.define('ai-warrior-widget', AIWarriorWidget);
