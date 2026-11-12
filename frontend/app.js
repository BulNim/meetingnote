'use strict';

// ===== 상수 =====
const THEME_KEY = 'theme';
const TABS = ['list', 'new', 'todos'];
const VIEW_IDS = { list: 'viewList', new: 'viewNew', todos: 'viewTodos' };
const SEARCH_DELAY_MS = 250;
const DELETE_CONFIRM_MS = 3000;
const UNASSIGNED = '미정';

const TAB_ACTIVE = ['bg-slate-800', 'text-white', 'shadow-sm', 'dark:bg-white', 'dark:text-neutral-900'];
const TAB_IDLE = ['text-neutral-600', 'hover:bg-black/5', 'dark:text-neutral-300', 'dark:hover:bg-white/10'];

const STATUS_TONE = {
  info: 'text-neutral-500 dark:text-neutral-400',
  ok: 'text-emerald-600 dark:text-emerald-400',
  error: 'text-rose-600 dark:text-rose-400',
};

// 결과 세 칸 (02-specs 1.2 - 각 칸은 줄바꿈 구분)
const SECTIONS = [
  { key: 'summary', label: '요약', hint: '3~5줄로 줄인 회의 내용', bar: 'border-l-cyan-600', heading: 'text-cyan-700 dark:text-cyan-400' },
  { key: 'decisions', label: '결정사항', hint: '합의가 끝난 것만', bar: 'border-l-orange-500', heading: 'text-orange-600 dark:text-orange-400' },
  { key: 'todos', label: '할 일', hint: '담당자 · 기한 포함', bar: 'border-l-emerald-600', heading: 'text-emerald-700 dark:text-emerald-400' },
];

// ===== 상태 (모듈 변수) =====
let currentTab = 'list';
let listRequestSeq = 0; // 늦게 도착한 옛 검색 결과가 새 결과를 덮지 않게 한다
let searchTimer = null;
let busy = false; // 받아쓰기 · 저장 중이면 true - 버튼을 잠가 중복 요청을 막는다
let openNote = null; // 상세 창에 열린 회의록 (단건 응답)
let modalBusy = false;
let deleteArmed = false;
let deleteTimer = null;
let lastFocus = null;

const $ = (id) => document.getElementById(id);

// ===== 공통 도구 =====
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = text;
  return node;
}

function setStatus(id, text, tone = 'info') {
  const node = $(id);
  node.textContent = text;
  node.className = `${node.dataset.base} ${STATUS_TONE[tone]}`;
}

class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function errorMessage(status) {
  switch (status) {
    case 400: return '입력값을 확인해 주세요. 제목 · 일시 · 본문은 꼭 넣어야 합니다.';
    case 404: return '회의록을 찾을 수 없습니다. 이미 지워졌을 수 있습니다.';
    case 413: return '파일이 25MB 를 넘습니다. 25MB 이하 파일만 받아쓸 수 있습니다.';
    case 415: return 'mp3 · wav 파일만 받아쓸 수 있습니다. 파일 형식을 확인해 주세요.';
    case 422: return '요청 형식이 맞지 않습니다. 화면을 새로고침한 뒤 다시 시도해 주세요.';
    case 502: return '받아쓰기 서비스에 연결하지 못했습니다. 잠시 뒤 다시 시도해 주세요.';
    default: return `요청을 처리하지 못했습니다. (오류 ${status})`;
  }
}

// API 는 같은 오리진의 /api/... 상대 경로로 부른다
async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(path, options);
  } catch (networkError) {
    throw new ApiError(0, '서버에 연결하지 못했습니다. 서버가 켜져 있는지 확인해 주세요.');
  }
  if (!response.ok) throw new ApiError(response.status, errorMessage(response.status));
  if (response.status === 204) return null;
  return response.json();
}

function sendJson(method, body) {
  return { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
}

// ===== 시각 변환 (02-specs 5절) - 화면은 로컬, 서버는 UTC =====
function pad(n) {
  return String(n).padStart(2, '0');
}

// Date → datetime-local 값 (로컬 시각, 분 단위)
function toLocalInputValue(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

// datetime-local 값(로컬) → UTC ISO 문자열. 시간대 없는 날짜·시각 문자열은 브라우저가 로컬로 읽는다
function localInputToUtcIso(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

// 서버의 UTC 문자열 → 로컬 시각 표시 "YYYY-MM-DD HH:mm"
function formatLocal(isoUtc) {
  const date = new Date(isoUtc);
  if (Number.isNaN(date.getTime())) return isoUtc;
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

// ===== 세 갈래 =====
function splitLines(text) {
  return (text || '').split('\n').map((line) => line.trim()).filter(Boolean);
}

// 「내용 | 담당자 | 기한」 한 줄을 나눈다 (02-specs 1.2)
function parseTodoLine(line) {
  const parts = line.split('|').map((part) => part.trim());
  return { what: parts[0] || '', who: parts[1] || UNASSIGNED, when: parts[2] || '' };
}

// 세 칸이 모두 비면 구분 실패 (02-specs 7.1)
function isSplitFailed(note) {
  return SECTIONS.every((section) => splitLines(note[section.key]).length === 0);
}

function renderSectionItems(box, section, text) {
  const lines = splitLines(text);
  if (lines.length === 0) {
    box.append(el('p', 'mt-2 text-sm text-neutral-400 dark:text-neutral-500', '없음'));
    return;
  }
  const list = el('ul', 'mt-2 space-y-2 text-sm leading-relaxed');
  for (const line of lines) {
    const item = el('li', 'break-words');
    if (section.key === 'todos') {
      const todo = parseTodoLine(line);
      item.append(el('span', '', todo.what));
      const meta = el('span', 'block text-xs text-neutral-500 dark:text-neutral-400');
      meta.append(el('b', 'font-semibold text-neutral-700 dark:text-neutral-200', todo.who));
      if (todo.when) meta.append(document.createTextNode(` · ${todo.when}`));
      item.append(meta);
    } else {
      item.textContent = `- ${line.replace(/^[-•·]\s*/, '')}`;
    }
    list.append(item);
  }
  box.append(list);
}

// 결과 세 칸을 그린다. note 가 없으면 안내 문구만 보인다
function renderThreeWay(container, note) {
  container.replaceChildren();
  if (note && isSplitFailed(note)) {
    const banner = el('div', 'rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800 ring-1 ring-amber-200 sm:col-span-3 dark:bg-amber-400/10 dark:text-amber-300 dark:ring-amber-400/30');
    banner.dataset.split = 'failed';
    banner.append(el('b', 'font-semibold', '구분 실패'));
    banner.append(document.createTextNode(' - 요약 · 결정사항 · 할 일로 나누지 못했습니다. 본문은 저장되어 있습니다. (본문이 20자 미만이거나 회의 내용이 아니면 나누지 않습니다)'));
    container.append(banner);
  }
  for (const section of SECTIONS) {
    const box = el('div', `min-w-0 rounded-xl border border-black/5 border-l-4 ${section.bar} bg-white/60 p-4 shadow-sm dark:border-white/10 dark:bg-white/5`);
    box.dataset.part = section.key;
    box.append(el('h3', `text-sm font-semibold ${section.heading}`, section.label));
    if (note) {
      renderSectionItems(box, section, note[section.key]);
    } else {
      box.append(el('p', 'mt-1 text-xs text-neutral-500 dark:text-neutral-400', section.hint));
    }
    container.append(box);
  }
}

// ===== 테마 (03-design 1절 8행) =====
function readSavedTheme() {
  try {
    const saved = localStorage.getItem(THEME_KEY);
    return saved === 'light' || saved === 'dark' ? saved : null;
  } catch (storageError) {
    return null;
  }
}

function systemTheme() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyTheme(theme) {
  document.documentElement.classList.toggle('dark', theme === 'dark');
  $('btnTheme').title = theme === 'dark' ? '라이트 테마로 바꾸기' : '다크 테마로 바꾸기';
}

function toggleTheme() {
  const next = document.documentElement.classList.contains('dark') ? 'light' : 'dark';
  try {
    localStorage.setItem(THEME_KEY, next);
  } catch (storageError) {
    // 저장이 막힌 브라우저에서도 이번 화면에는 적용한다
  }
  applyTheme(next);
}

// ===== 탭 =====
function showTab(tab) {
  currentTab = TABS.includes(tab) ? tab : 'list';
  for (const name of TABS) {
    $(VIEW_IDS[name]).classList.toggle('hidden', name !== currentTab);
  }
  for (const button of document.querySelectorAll('[data-tab]')) {
    const active = button.dataset.tab === currentTab;
    button.setAttribute('aria-selected', String(active));
    button.classList.remove(...(active ? TAB_IDLE : TAB_ACTIVE));
    button.classList.add(...(active ? TAB_ACTIVE : TAB_IDLE));
  }
  // 새로고침해도 같은 탭이 열리게 주소에 남긴다
  if (location.hash !== `#${currentTab}`) history.replaceState(null, '', `#${currentTab}`);
  refreshCurrentView();
}

function refreshCurrentView() {
  if (currentTab === 'list') loadNotes();
  if (currentTab === 'todos') loadTodos();
}

// ===== 화면 1: 목록 + 검색 (02-specs 6절) =====
function scheduleSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadNotes, SEARCH_DELAY_MS);
}

async function loadNotes() {
  const seq = ++listRequestSeq;
  const q = $('q').value.trim();
  const from = $('from').value;
  const to = $('to').value;
  const params = new URLSearchParams();
  if (q) params.set('q', q);
  if (from) params.set('from', from);
  if (to) params.set('to', to);
  // from · to 는 로컬 날짜 기준 - 서버가 UTC 로 바꿀 수 있게 시간대를 함께 보낸다
  params.set('tz_offset', String(new Date().getTimezoneOffset()));

  let notes;
  try {
    notes = await api(`/api/notes?${params}`);
  } catch (err) {
    if (seq === listRequestSeq) setStatus('listStatus', err.message, 'error');
    return;
  }
  if (seq !== listRequestSeq) return;

  renderCards(notes);
  const filtered = Boolean(q || from || to);
  if (from && to && from > to) {
    setStatus('listStatus', '시작 날짜(from)가 끝 날짜(to)보다 늦습니다.', 'error');
  } else if (notes.length === 0) {
    setStatus('listStatus', filtered ? '검색 결과가 없습니다.' : '아직 저장된 회의록이 없습니다. 「넣기」에서 첫 회의록을 만들어 보세요.');
  } else {
    setStatus('listStatus', filtered ? `검색 결과 ${notes.length}건` : `회의록 ${notes.length}건`);
  }
}

function renderCards(notes) {
  const cards = $('cards');
  cards.replaceChildren();
  for (const note of notes) {
    const card = el('button', 'min-w-0 rounded-2xl bg-white/70 p-5 text-left shadow-sm ring-1 ring-black/5 backdrop-blur-xl transition hover:-translate-y-0.5 hover:shadow-md focus:outline-none focus-visible:ring-4 focus-visible:ring-sky-500/30 dark:bg-white/5 dark:ring-white/10 dark:hover:bg-white/10');
    card.type = 'button';
    card.dataset.id = String(note.id);
    card.append(el('h3', 'truncate font-semibold', note.title));
    card.append(el('p', 'mt-1 truncate text-xs text-neutral-500 dark:text-neutral-400', `${formatLocal(note.met_at)} · ${note.attendees || '참석자 없음'}`));
    if (isSplitFailed(note)) {
      card.append(el('p', 'mt-3 inline-block rounded-md bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800 dark:bg-amber-400/10 dark:text-amber-300', '구분 실패'));
    } else {
      const firstLine = splitLines(note.summary)[0] || splitLines(note.decisions)[0] || '';
      card.append(el('p', 'mt-3 line-clamp-2 text-sm text-neutral-700 dark:text-neutral-300', firstLine.replace(/^[-•·]\s*/, '')));
    }
    card.addEventListener('click', () => openModal(note.id));
    cards.append(card);
  }
}

// ===== 화면 2: 넣기 =====
// 받아쓰기 · 저장 중에는 두 버튼과 파일 칸을 함께 잠근다
function setBusy(on, activeButtonId, activeLabel) {
  busy = on;
  for (const id of ['btnUp', 'btnSave']) {
    const button = $(id);
    button.disabled = on;
    button.textContent = on && id === activeButtonId ? activeLabel : button.dataset.label;
    button.setAttribute('aria-busy', String(on && id === activeButtonId));
  }
  $('file').disabled = on;
}

// 오래 걸리는 요청 동안 지난 초를 보여 준다. 멈추는 함수를 돌려준다
function startElapsed(statusId, label) {
  const startedAt = Date.now();
  const tick = () => {
    const seconds = Math.floor((Date.now() - startedAt) / 1000);
    setStatus(statusId, `${label}… ${seconds}초 (서버를 켠 뒤 첫 요청은 몇 분 걸릴 수 있습니다)`);
  };
  tick();
  const timer = setInterval(tick, 1000);
  return () => clearInterval(timer);
}

async function transcribe() {
  if (busy) return;
  const file = $('file').files[0];
  if (!file) {
    setStatus('upStatus', '먼저 녹취 파일(mp3 · wav)을 골라 주세요.', 'error');
    return;
  }
  const form = new FormData();
  form.append('file', file);

  setBusy(true, 'btnUp', '받아쓰는 중…');
  const stopElapsed = startElapsed('upStatus', '받아쓰는 중');
  try {
    const data = await api('/api/upload', { method: 'POST', body: form });
    $('body').value = data.body;
    setStatus('upStatus', '받아쓴 본문을 채웠습니다. 확인한 뒤 「정리하기」를 누르세요.', 'ok');
  } catch (err) {
    setStatus('upStatus', err.message, 'error');
  } finally {
    stopElapsed();
    setBusy(false);
  }
}

function resetForm() {
  $('title').value = '';
  $('attendees').value = '';
  $('file').value = '';
  $('body').value = '';
  $('metAt').value = toLocalInputValue(new Date());
  setStatus('upStatus', '녹취 파일(mp3 · wav, 25MB 이하)을 고른 뒤 누르세요');
}

async function saveNote() {
  if (busy) return;
  const fields = {
    title: $('title').value.trim(),
    metAt: $('metAt').value,
    attendees: $('attendees').value.trim(),
    body: $('body').value.trim(),
  };
  const missing = [];
  if (!fields.title) missing.push(['title', '제목']);
  if (!fields.metAt) missing.push(['metAt', '일시']);
  if (!fields.body) missing.push(['body', '본문']);
  if (missing.length > 0) {
    setStatus('saveStatus', `${missing.map(([, label]) => label).join(' · ')}을(를) 넣어 주세요.`, 'error');
    $(missing[0][0]).focus();
    return;
  }
  const metAtUtc = localInputToUtcIso(fields.metAt);
  if (!metAtUtc) {
    setStatus('saveStatus', '일시를 다시 확인해 주세요.', 'error');
    return;
  }
  // 스펙 외 필드를 보내면 422 - 정해진 네 필드만 보낸다
  const payload = { title: fields.title, met_at: metAtUtc, attendees: fields.attendees, body: fields.body };

  setBusy(true, 'btnSave', '정리하는 중…');
  const stopElapsed = startElapsed('saveStatus', '저장하고 세 갈래로 나누는 중');
  try {
    const note = await api('/api/notes', sendJson('POST', payload));
    stopElapsed();
    renderThreeWay($('result'), note);
    setStatus('saveStatus', isSplitFailed(note) ? '저장했습니다. 다만 세 갈래 구분에 실패했습니다.' : '저장하고 세 갈래로 정리했습니다.', isSplitFailed(note) ? 'error' : 'ok');
    const viewButton = el('button', 'ml-2 underline underline-offset-2', '상세 보기');
    viewButton.type = 'button';
    viewButton.addEventListener('click', () => openModal(note.id));
    $('saveStatus').append(' ', viewButton);
    resetForm();
  } catch (err) {
    stopElapsed();
    setStatus('saveStatus', err.message, 'error');
  } finally {
    setBusy(false);
  }
}

// ===== 화면 3: 상세 창 =====
async function openModal(id) {
  let note;
  try {
    note = await api(`/api/notes/${id}`);
  } catch (err) {
    const statusId = currentTab === 'todos' ? 'todoStatus' : currentTab === 'new' ? 'saveStatus' : 'listStatus';
    setStatus(statusId, err.message, 'error');
    if (err.status === 404) refreshCurrentView();
    return;
  }
  lastFocus = document.activeElement;
  fillModal(note);
  disarmDelete();
  setStatus('mStatus', '삭제는 한 번 더 눌러야 지워집니다.');
  const modal = $('modal');
  modal.classList.remove('hidden');
  modal.classList.add('flex');
  document.body.classList.add('overflow-hidden');
  $('btnClose').focus();
}

function fillModal(note) {
  openNote = note;
  $('mHeading').textContent = note.title;
  $('mMeta').textContent = `${formatLocal(note.met_at)} · ${note.attendees || '참석자 없음'}`;
  renderThreeWay($('mResult'), note);
  $('mBody').textContent = note.body;
  $('mTitle').value = note.title;
}

function closeModal() {
  const modal = $('modal');
  if (modal.classList.contains('hidden')) return;
  modal.classList.add('hidden');
  modal.classList.remove('flex');
  document.body.classList.remove('overflow-hidden');
  disarmDelete();
  openNote = null;
  if (lastFocus && document.body.contains(lastFocus)) lastFocus.focus();
}

function setModalBusy(on) {
  modalBusy = on;
  $('btnRename').disabled = on;
  $('btnDelete').disabled = on;
}

async function renameNote() {
  if (!openNote || modalBusy) return;
  const title = $('mTitle').value.trim();
  if (!title) {
    setStatus('mStatus', '제목을 넣어 주세요.', 'error');
    $('mTitle').focus();
    return;
  }
  if (title === openNote.title) {
    setStatus('mStatus', '바뀐 제목이 없습니다.');
    return;
  }
  // PUT 은 title · met_at · body 필수. 세 갈래는 보내지 않아 그대로 둔다 (02-specs 3.0)
  const payload = { title, met_at: openNote.met_at, attendees: openNote.attendees, body: openNote.body };
  setModalBusy(true);
  try {
    const updated = await api(`/api/notes/${openNote.id}`, sendJson('PUT', payload));
    fillModal(updated);
    setStatus('mStatus', '제목을 고쳤습니다.', 'ok');
    refreshCurrentView();
  } catch (err) {
    setStatus('mStatus', err.message, 'error');
  } finally {
    setModalBusy(false);
  }
}

function disarmDelete() {
  deleteArmed = false;
  clearTimeout(deleteTimer);
  $('btnDelete').textContent = $('btnDelete').dataset.label;
}

// 실수로 지우지 않게 한 번 더 눌러야 지운다
async function deleteNote() {
  if (!openNote || modalBusy) return;
  if (!deleteArmed) {
    deleteArmed = true;
    $('btnDelete').textContent = '한 번 더 누르면 삭제';
    setStatus('mStatus', '정말 지우려면 3초 안에 한 번 더 누르세요.', 'error');
    deleteTimer = setTimeout(() => {
      disarmDelete();
      setStatus('mStatus', '삭제는 한 번 더 눌러야 지워집니다.');
    }, DELETE_CONFIRM_MS);
    return;
  }
  disarmDelete();
  setModalBusy(true);
  try {
    await api(`/api/notes/${openNote.id}`, { method: 'DELETE' });
    closeModal();
    refreshCurrentView();
  } catch (err) {
    setStatus('mStatus', err.message, 'error');
  } finally {
    setModalBusy(false);
  }
}

// ===== 화면 4: 할 일 =====
async function loadTodos() {
  let todos;
  try {
    todos = await api('/api/todos');
  } catch (err) {
    setStatus('todoStatus', err.message, 'error');
    return;
  }
  const tbody = $('todoBody');
  tbody.replaceChildren();
  if (todos.length === 0) {
    const row = el('tr');
    const cell = el('td', 'px-4 py-8 text-center text-neutral-500 dark:text-neutral-400', '아직 모인 할 일이 없습니다.');
    cell.colSpan = 4;
    row.append(cell);
    tbody.append(row);
    setStatus('todoStatus', '');
    return;
  }
  // 서버가 회의 날짜 오래된 순으로 준다. 기한으로는 정렬하지 않는다 (02-specs 2.1)
  todos.forEach((todo, index) => {
    const row = el('tr', index % 2 === 1 ? 'bg-black/[0.03] dark:bg-white/[0.03]' : '');
    row.append(el('td', 'break-words px-4 py-3', todo.what));
    row.append(el('td', 'px-4 py-3 font-semibold', todo.who || UNASSIGNED));
    row.append(el('td', 'px-4 py-3 text-neutral-600 dark:text-neutral-300', todo.when || '-'));
    const noteCell = el('td', 'px-4 py-3');
    const link = el('button', 'text-left text-sky-700 underline-offset-2 hover:underline dark:text-sky-400', todo.note_title);
    link.type = 'button';
    link.addEventListener('click', () => openModal(todo.note_id));
    noteCell.append(link);
    row.append(noteCell);
    tbody.append(row);
  });
  setStatus('todoStatus', `할 일 ${todos.length}건 · 회의 날짜 오래된 순`);
}

// ===== 시작 =====
function init() {
  applyTheme(readSavedTheme() || systemTheme());
  // 사용자가 고른 적이 없으면 시스템 설정이 바뀔 때 따라간다
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (!readSavedTheme()) applyTheme(systemTheme());
  });
  $('btnTheme').addEventListener('click', toggleTheme);

  for (const button of document.querySelectorAll('[data-tab]')) {
    button.addEventListener('click', () => showTab(button.dataset.tab));
  }

  $('q').addEventListener('input', scheduleSearch);
  $('from').addEventListener('change', loadNotes);
  $('to').addEventListener('change', loadNotes);

  $('btnUp').addEventListener('click', transcribe);
  $('btnSave').addEventListener('click', saveNote);
  $('metAt').value = toLocalInputValue(new Date());
  renderThreeWay($('result'), null);

  $('btnClose').addEventListener('click', closeModal);
  $('modal').addEventListener('click', (event) => {
    if (event.target === event.currentTarget) closeModal(); // 바깥 어두운 영역
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeModal();
  });
  $('btnRename').addEventListener('click', renameNote);
  $('mTitle').addEventListener('keydown', (event) => {
    if (event.key === 'Enter') renameNote();
  });
  $('btnDelete').addEventListener('click', deleteNote);

  // 주소의 #탭 을 직접 바꿔도 따라간다
  window.addEventListener('hashchange', () => {
    const tab = location.hash.slice(1);
    if (tab !== currentTab) showTab(tab);
  });
  showTab(location.hash.slice(1));
}

init();
