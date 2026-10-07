const THEME_KEY = 'meetingnote-theme';
const VIEWS = ['list', 'add', 'todos'];
const MAX_UPLOAD_BYTES = 25 * 1024 * 1024;
const SEARCH_DELAY_MS = 250;

const TAB_ACTIVE = 'bg-slate-800 text-white dark:bg-slate-100 dark:text-slate-900'.split(' ');
const TAB_IDLE = 'text-slate-600 dark:text-slate-300 hover:bg-slate-200/60 dark:hover:bg-slate-700/60'.split(' ');

// 세 갈래 칸 정의: 키, 제목, 색상
const SECTIONS = [
  { key: 'summary', label: '요약', hint: '3~5줄로 줄인 회의 내용', bar: 'border-cyan-600', text: 'text-cyan-700 dark:text-cyan-400' },
  { key: 'decisions', label: '결정사항', hint: '합의가 끝난 것만', bar: 'border-orange-500', text: 'text-orange-600 dark:text-orange-400' },
  { key: 'todos', label: '할 일', hint: '담당자 · 기한 포함', bar: 'border-emerald-600', text: 'text-emerald-700 dark:text-emerald-400' },
];

let notes = [];
let currentNote = null;
let deleteArmed = false;
let deleteTimer = null;
let searchTimer = null;

const $ = (role) => document.querySelector(`[data-role="${role}"]`);
const byId = (id) => document.getElementById(id);

// ---------- 공통 도우미 ----------

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function errorMessage(status, data) {
  const detail = data && data.detail;
  if (typeof detail === 'string') return detail;
  if (status === 400 || status === 422) return '입력값을 확인해 주세요.';
  return `요청에 실패했습니다. (${status})`;
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (response.status === 204) return null;
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(errorMessage(response.status, data));
  return data;
}

function formatDateTime(iso) {
  return new Date(iso).toLocaleString('ko-KR', {
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  });
}

// datetime-local 입력값(YYYY-MM-DDTHH:mm)을 로컬 시각 기준으로 만든다
function toLocalInputValue(date) {
  const pad = (n) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function lines(text) {
  return (text || '').split('\n').map((line) => line.trim()).filter(Boolean);
}

function isSplitFailed(note) {
  return !lines(note.summary).length && !lines(note.decisions).length && !lines(note.todos).length;
}

function setBusy(button, busy, busyLabel) {
  if (busy) {
    button.dataset.label = button.textContent;
    button.textContent = busyLabel;
  } else if (button.dataset.label) {
    button.textContent = button.dataset.label;
  }
  button.disabled = busy;
}

function setStatus(role, message, isError = false) {
  const node = $(role);
  node.textContent = message;
  node.classList.toggle('text-rose-600', isError);
  node.classList.toggle('text-slate-500', !isError);
}

// ---------- 테마 ----------

// 초기 테마(저장값 > 시스템 설정)는 index.html 의 head 스크립트가 먼저 적용한다
function toggleTheme() {
  const next = document.documentElement.classList.contains('dark') ? 'light' : 'dark';
  document.documentElement.classList.toggle('dark', next === 'dark');
  try {
    localStorage.setItem(THEME_KEY, next);
  } catch (e) {
    // 저장이 막혀 있어도 화면 전환은 그대로 동작한다
  }
}

// ---------- 화면 전환 ----------

function showView(name) {
  const view = VIEWS.includes(name) ? name : 'list';
  document.querySelectorAll('[data-panel]').forEach((panel) => {
    panel.classList.toggle('hidden', panel.dataset.panel !== view);
  });
  document.querySelectorAll('[data-tab]').forEach((tab) => {
    const active = tab.dataset.tab === view;
    tab.classList.remove(...TAB_ACTIVE, ...TAB_IDLE);
    tab.classList.add(...(active ? TAB_ACTIVE : TAB_IDLE));
  });
  history.replaceState(null, '', `#${view}`);
  if (view === 'list') loadNotes();
  if (view === 'todos') loadTodos();
}

// ---------- 세 갈래 칸 (넣기 결과 · 상세 공통) ----------

function renderColumns(container, note) {
  container.replaceChildren();
  SECTIONS.forEach((section) => {
    const card = el('div', `rounded-2xl border-l-4 ${section.bar} bg-white/70 p-4 shadow-sm backdrop-blur dark:bg-slate-800/70`);
    card.append(el('h3', `text-sm font-bold ${section.text}`, section.label));
    const items = note ? lines(note[section.key]) : [];
    if (!note) {
      card.append(el('p', 'mt-2 text-sm text-slate-400', section.hint));
    } else if (!items.length) {
      card.append(el('p', 'mt-2 text-sm text-slate-400', '내용 없음'));
    } else {
      const list = el('ul', 'mt-2 space-y-1 text-sm');
      items.forEach((item) => list.append(el('li', 'break-words', `- ${formatItem(section.key, item)}`)));
      card.append(list);
    }
    container.append(card);
  });
}

// todos 한 줄(내용 | 담당자 | 기한)을 보기 좋게 바꾼다
function formatItem(key, item) {
  if (key !== 'todos') return item;
  const [what, who, when] = item.split('|').map((part) => part.trim());
  const extra = [who, when].filter(Boolean).join(' · ');
  return extra ? `${what} (${extra})` : what;
}

function splitFailNotice() {
  return el('p', 'col-span-full rounded-2xl bg-amber-100 px-4 py-3 text-sm text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
    '구분 실패: 본문은 저장되었지만 요약 · 결정사항 · 할 일을 나누지 못했습니다.');
}

// ---------- 목록 ----------

async function loadNotes() {
  const params = new URLSearchParams();
  [['q', 'q'], ['from', 'from'], ['to', 'to']].forEach(([id, name]) => {
    const value = byId(id).value.trim();
    if (value) params.set(name, value);
  });
  try {
    notes = await api(`/api/notes?${params}`);
    setStatus('listStatus', notes.length ? '' : '회의록이 없습니다.');
  } catch (error) {
    notes = [];
    setStatus('listStatus', error.message, true);
  }
  renderCards();
}

function renderCards() {
  const container = byId('cards');
  container.replaceChildren();
  notes.forEach((note) => {
    const card = el('button', 'rounded-2xl border border-slate-200 bg-white/70 p-5 text-left shadow-sm backdrop-blur transition hover:-translate-y-0.5 hover:shadow-lg dark:border-slate-700 dark:bg-slate-800/70');
    card.type = 'button';
    card.dataset.noteId = note.id;
    card.append(el('h3', 'break-words font-bold', note.title));
    const meta = [formatDateTime(note.met_at), note.attendees].filter(Boolean).join(' · ');
    card.append(el('p', 'mt-1 text-xs text-slate-400', meta));
    if (isSplitFailed(note)) {
      card.append(el('p', 'mt-3 inline-block rounded-lg bg-amber-100 px-2 py-0.5 text-xs text-amber-800 dark:bg-amber-900/40 dark:text-amber-200', '구분 실패'));
    } else {
      card.append(el('p', 'mt-3 line-clamp-2 break-words text-sm text-slate-600 dark:text-slate-300', lines(note.summary)[0] || ''));
    }
    container.append(card);
  });
}

function scheduleSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadNotes, SEARCH_DELAY_MS);
}

// ---------- 넣기 ----------

async function uploadAudio() {
  const file = byId('file').files[0];
  if (!file) return setStatus('upStatus', '파일을 먼저 선택하세요.', true);
  if (!/\.(mp3|wav)$/i.test(file.name)) return setStatus('upStatus', 'mp3, wav 파일만 올릴 수 있습니다.', true);
  if (file.size > MAX_UPLOAD_BYTES) return setStatus('upStatus', '25MB 이하 파일만 올릴 수 있습니다.', true);

  const button = byId('btnUp');
  const form = new FormData();
  form.append('file', file);
  setBusy(button, true, '받아쓰는 중…');
  setStatus('upStatus', '받아쓰는 중입니다. 잠시만 기다려 주세요.');
  try {
    const data = await api('/api/upload', { method: 'POST', body: form });
    byId('body').value = data.text;
    setStatus('upStatus', '받아쓰기 완료. 본문을 확인하세요.');
  } catch (error) {
    setStatus('upStatus', error.message, true);
  } finally {
    setBusy(button, false);
  }
}

async function saveNote() {
  const title = byId('title').value.trim();
  const metAt = byId('metAt').value;
  const attendees = byId('attendees').value.trim();
  const body = byId('body').value.trim();
  if (!title) return setStatus('saveStatus', '제목을 입력하세요.', true);
  if (!metAt || Number.isNaN(new Date(metAt).getTime())) return setStatus('saveStatus', '일시를 입력하세요.', true);
  if (!body) return setStatus('saveStatus', '본문을 입력하세요.', true);

  const button = byId('btnSave');
  setBusy(button, true, '정리 중…');
  setStatus('saveStatus', '세 갈래로 정리하는 중입니다.');
  try {
    // 화면의 일시는 로컬 시각이므로 UTC 로 바꿔 보낸다
    const note = await api('/api/notes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, met_at: new Date(metAt).toISOString(), attendees: attendees || null, body }),
    });
    renderColumns(byId('result'), note);
    if (isSplitFailed(note)) byId('result').prepend(splitFailNotice());
    setStatus('saveStatus', '저장되었습니다.');
  } catch (error) {
    setStatus('saveStatus', error.message, true);
  } finally {
    setBusy(button, false);
  }
}

// ---------- 상세 ----------

async function openModal(noteId) {
  try {
    currentNote = await api(`/api/notes/${noteId}`);
  } catch (error) {
    setStatus('listStatus', error.message, true);
    return;
  }
  $('mHeading').textContent = currentNote.title;
  $('mMeta').textContent = [formatDateTime(currentNote.met_at), currentNote.attendees].filter(Boolean).join(' · ');
  const columns = $('mColumns');
  renderColumns(columns, currentNote);
  if (isSplitFailed(currentNote)) columns.prepend(splitFailNotice());
  $('mBody').textContent = currentNote.body;
  byId('mTitle').value = currentNote.title;
  setStatus('mStatus', '');
  resetDelete();
  const modal = byId('modal');
  modal.classList.remove('hidden');
  modal.classList.add('flex');
}

function closeModal() {
  const modal = byId('modal');
  modal.classList.add('hidden');
  modal.classList.remove('flex');
  resetDelete();
  currentNote = null;
}

function resetDelete() {
  clearTimeout(deleteTimer);
  deleteArmed = false;
  $('mDelete').textContent = '삭제';
}

async function saveTitle() {
  const title = byId('mTitle').value.trim();
  if (!title) return setStatus('mStatus', '제목을 입력하세요.', true);
  const button = $('mSave');
  setBusy(button, true, '수정 중…');
  try {
    // PUT 은 전체 교체이므로 기존 값을 그대로 함께 보낸다
    const { id, ...rest } = currentNote;
    currentNote = await api(`/api/notes/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...rest, title }),
    });
    $('mHeading').textContent = currentNote.title;
    setStatus('mStatus', '제목을 수정했습니다.');
    loadNotes();
  } catch (error) {
    setStatus('mStatus', error.message, true);
  } finally {
    setBusy(button, false);
  }
}

async function deleteNote() {
  const button = $('mDelete');
  if (!deleteArmed) {
    // 첫 클릭은 확인만 받고, 한 번 더 눌러야 지운다
    deleteArmed = true;
    button.textContent = '정말 삭제';
    deleteTimer = setTimeout(resetDelete, 4000);
    return;
  }
  clearTimeout(deleteTimer);
  setBusy(button, true, '삭제 중…');
  try {
    await api(`/api/notes/${currentNote.id}`, { method: 'DELETE' });
    closeModal();
    loadNotes();
  } catch (error) {
    setStatus('mStatus', error.message, true);
    resetDelete();
  } finally {
    setBusy(button, false);
  }
}

// ---------- 할 일 ----------

async function loadTodos() {
  const tbody = byId('todoBody');
  tbody.replaceChildren();
  let todos = [];
  try {
    todos = await api('/api/todos');
    setStatus('todoStatus', todos.length ? '' : '할 일이 없습니다.');
  } catch (error) {
    setStatus('todoStatus', error.message, true);
  }
  todos.forEach((todo, index) => {
    const row = el('tr', index % 2 ? 'bg-slate-100/60 dark:bg-slate-900/30' : '');
    row.append(el('td', 'px-4 py-3', todo.what));
    row.append(el('td', 'px-4 py-3 font-bold', todo.who));
    row.append(el('td', 'px-4 py-3', todo.when));
    row.append(el('td', 'px-4 py-3', todo.note_title));
    tbody.append(row);
  });
}

// ---------- 시작 ----------

function init() {
  document.querySelectorAll('[data-tab]').forEach((tab) => {
    tab.addEventListener('click', () => showView(tab.dataset.tab));
  });
  $('themeToggle').addEventListener('click', toggleTheme);

  ['q', 'from', 'to'].forEach((id) => byId(id).addEventListener('input', scheduleSearch));
  byId('cards').addEventListener('click', (event) => {
    const card = event.target.closest('[data-note-id]');
    if (card) openModal(card.dataset.noteId);
  });

  byId('btnUp').addEventListener('click', uploadAudio);
  byId('btnSave').addEventListener('click', saveNote);
  byId('metAt').value = toLocalInputValue(new Date());
  renderColumns(byId('result'), null);

  byId('modal').addEventListener('click', (event) => {
    if (event.target === byId('modal')) closeModal();
  });
  $('mClose').addEventListener('click', closeModal);
  $('mSave').addEventListener('click', saveTitle);
  $('mDelete').addEventListener('click', deleteNote);
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && currentNote) closeModal();
  });

  showView(location.hash.slice(1));
}

init();
