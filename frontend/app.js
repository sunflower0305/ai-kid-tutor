/**
 * AI-KID-TUTOR 前端逻辑
 * 功能：学科 Tab 切换 / SSE 流式接收 / 苏格拉底反问 UI / 例题卡片
 */

const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000'
  : '';  // 生产环境同域

// ─── 状态 ──────────────────────────────────────────────────────────────────
let currentSubject = 'essay';
let sessionId = generateId();
let isLoading = false;
let lastSocraticQuestion = null;
let lastGuidance = null;

const SUBJECT_LABELS = {
  essay:   { name: '作文辅导', class: 'subject-essay' },
  english: { name: '英语单词', class: 'subject-english' },
  math:    { name: '数学题意', class: 'subject-math' },
  mistake: { name: '错题分析', class: 'subject-mistake' },
};

const PLACEHOLDERS = {
  essay:   '输入作文题目，比如：写一篇关于秋天的作文...',
  english: '输入英语单词，比如：apple、beautiful...',
  math:    '粘贴数学题目，比如：小明有5个苹果，给了小红2个...',
  mistake: '描述你做错的题，比如：这道应用题我算出来是10，但答案是8...',
};

// ─── 初始化 ─────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  setupTabs();
  setupInput();
  updateSubjectHint();
});

function setupTabs() {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      currentSubject = tab.dataset.subject;
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      updateSubjectHint();
      // 清空会话，新学科新对话
      sessionId = generateId();
      lastSocraticQuestion = null;
      lastGuidance = null;
    });
  });
}

function setupInput() {
  const input = document.getElementById('messageInput');
  const charCount = document.getElementById('charCount');

  input.addEventListener('input', () => {
    // 自动撑高 textarea
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    charCount.textContent = input.value.length;
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
}

function updateSubjectHint() {
  const label = SUBJECT_LABELS[currentSubject];
  document.getElementById('currentSubject').textContent = label.name;
  document.getElementById('messageInput').placeholder = PLACEHOLDERS[currentSubject];
}

// ─── 发送消息 ────────────────────────────────────────────────────────────────
async function sendMessage() {
  if (isLoading) return;

  const input = document.getElementById('messageInput');
  const message = input.value.trim();
  if (!message) return;

  // 判断是否是在回答苏格拉底反问
  const isAnswerToSocratic = lastSocraticQuestion !== null;

  appendUserMessage(message);
  input.value = '';
  input.style.height = 'auto';
  document.getElementById('charCount').textContent = '0';

  if (isAnswerToSocratic) {
    await handleSocraticAnswer(message);
  } else {
    await handleTutorRequest(message);
  }
}

// ─── 主辅导请求（SSE 流式） ──────────────────────────────────────────────────
async function handleTutorRequest(message) {
  setLoading(true, '老师正在思考...');

  const payload = {
    message,
    subject: currentSubject,
    session_id: sessionId,
    is_answer_to_socratic: false,
  };

  try {
    const response = await fetch(`${API_BASE}/api/tutor`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n');
      buffer = events.pop() || '';

      for (const eventStr of events) {
        if (!eventStr.trim()) continue;
        parseSSEEvent(eventStr);
      }
    }
  } catch (err) {
    appendBotMessage(`连接失败，请检查网络后重试。(${err.message})`);
  } finally {
    setLoading(false);
  }
}

function parseSSEEvent(eventStr) {
  const lines = eventStr.split('\n');
  let eventType = 'message';
  let dataStr = '';

  for (const line of lines) {
    if (line.startsWith('event: ')) eventType = line.slice(7).trim();
    if (line.startsWith('data: ')) dataStr = line.slice(6).trim();
  }

  if (!dataStr) return;

  try {
    const data = JSON.parse(dataStr);

    switch (eventType) {
      case 'status':
        updateThinkingText(data.message);
        break;

      case 'routed':
        updateThinkingText(`识别为：${SUBJECT_LABELS[data.subject]?.name || data.subject}`);
        break;

      case 'response':
        setLoading(false);
        appendTutoringResponse(data);
        lastSocraticQuestion = data.socratic_question;
        lastGuidance = data.guidance;
        sessionId = data.session_id || sessionId;
        break;

      case 'guardrail_triggered':
        setLoading(false);
        appendGuardrailNotice();
        break;

      case 'error':
        setLoading(false);
        appendBotMessage(`出错了：${data.message}`);
        break;

      case 'done':
        setLoading(false);
        break;
    }
  } catch (e) {
    console.error('SSE parse error:', e, dataStr);
  }
}

// ─── 评价苏格拉底回答 ────────────────────────────────────────────────────────
async function handleSocraticAnswer(answer) {
  setLoading(true, '老师正在批改...');

  const savedQuestion = lastSocraticQuestion;
  lastSocraticQuestion = null;  // 重置，下次不再当成反问回答
  lastGuidance = null;

  try {
    const response = await fetch(`${API_BASE}/api/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        original_problem: savedQuestion,
        student_answer: answer,
        subject: currentSubject,
        session_id: sessionId,
      }),
    });

    const data = await response.json();
    appendEvaluation(data);
  } catch (err) {
    appendBotMessage(`评价失败：${err.message}`);
  } finally {
    setLoading(false);
  }
}

// ─── UI 渲染函数 ─────────────────────────────────────────────────────────────
function appendUserMessage(text) {
  const container = document.getElementById('chatMessages');
  const msgEl = document.createElement('div');
  msgEl.className = 'message user-message';
  msgEl.innerHTML = `
    <div class="avatar">😊</div>
    <div class="bubble">${escapeHtml(text)}</div>
  `;
  container.appendChild(msgEl);
  scrollToBottom();
}

function appendBotMessage(text) {
  const container = document.getElementById('chatMessages');
  const msgEl = document.createElement('div');
  msgEl.className = 'message bot-message';
  msgEl.innerHTML = `
    <div class="avatar">🎓</div>
    <div class="bubble">${escapeHtml(text)}</div>
  `;
  container.appendChild(msgEl);
  scrollToBottom();
}

function appendTutoringResponse(data) {
  const container = document.getElementById('chatMessages');
  const label = SUBJECT_LABELS[data.subject] || SUBJECT_LABELS['essay'];

  const msgEl = document.createElement('div');
  msgEl.className = 'message bot-message';
  msgEl.innerHTML = `
    <div class="avatar">🎓</div>
    <div class="bubble">
      <span class="subject-label ${label.class}">${label.name}</span>

      <div class="guidance-content">${formatText(data.guidance)}</div>

      <div class="socratic-card">
        <div class="card-label">💭 老师想问你</div>
        <div class="card-content">${escapeHtml(data.socratic_question)}</div>
      </div>

      <div class="example-card">
        <div class="card-label">✏️ 试一试这道练习题</div>
        <div class="card-content">${escapeHtml(data.example_problem)}</div>
        <div class="hint">提示：${escapeHtml(data.hint_for_example)}</div>
      </div>

      <div style="margin-top:10px;font-size:12px;color:#a0aec0;">
        💡 回答老师的问题，我会给你评价哦～
      </div>
    </div>
  `;
  container.appendChild(msgEl);
  scrollToBottom();
}

function appendEvaluation(data) {
  const container = document.getElementById('chatMessages');
  const emoji = data.is_correct_thinking ? '🌟' : '💪';

  const msgEl = document.createElement('div');
  msgEl.className = 'message bot-message';

  let html = `
    <div class="avatar">🎓</div>
    <div class="bubble">
      <div class="evaluation-card">
        <div class="card-label">${emoji} 老师的评价</div>
        <p>${escapeHtml(data.encouragement)}</p>
        ${data.correction_hint ? `<p style="margin-top:6px;color:#7b341e;">${escapeHtml(data.correction_hint)}</p>` : ''}
      </div>
      <p style="margin-top:10px;">${escapeHtml(data.next_step)}</p>
    </div>
  `;

  msgEl.innerHTML = html;
  container.appendChild(msgEl);
  scrollToBottom();
}

function appendGuardrailNotice() {
  const container = document.getElementById('chatMessages');
  const msgEl = document.createElement('div');
  msgEl.className = 'message bot-message';
  msgEl.innerHTML = `
    <div class="avatar">🎓</div>
    <div class="bubble">
      <div class="guardrail-notice">
        🛡️ 我注意到这个问题可能需要直接给答案，但我的原则是引导你自己找到答案。<br>
        请换一种方式告诉我，你在哪里卡住了？
      </div>
    </div>
  `;
  container.appendChild(msgEl);
  scrollToBottom();
}

// ─── Loading 控制 ────────────────────────────────────────────────────────────
function setLoading(loading, text = '正在思考...') {
  isLoading = loading;
  const overlay = document.getElementById('thinkingOverlay');
  const sendBtn = document.getElementById('sendBtn');

  overlay.style.display = loading ? 'flex' : 'none';
  sendBtn.disabled = loading;

  if (loading) updateThinkingText(text);
}

function updateThinkingText(text) {
  document.getElementById('thinkingText').textContent = text;
}

// ─── 工具函数 ────────────────────────────────────────────────────────────────
function scrollToBottom() {
  requestAnimationFrame(() => {
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
  });
}

function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/\n/g, '<br>');
}

function formatText(str) {
  if (!str) return '';
  // 处理换行 + 简单 markdown（粗体）
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
}

function generateId() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}
