const state = {
  view: 'list',
  notes: [],
  todos: [],
  selectedNote: null,
  filters: { q: '', from: '', to: '' },
};

const app = document.querySelector('#app');
const statusBox = document.querySelector('#status');

function escapeHtml(value = '') {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#039;', '"': '&quot;'
  }[character]));
}

function setStatus(message, type = 'info') {
  statusBox.textContent = message;
  statusBox.className = `mb-4 rounded-2xl px-4 py-3 text-sm ${type === 'error' ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-200' : 'bg-cyan-100 text-cyan-800 dark:bg-cyan-950/60 dark:text-cyan-200'}`;
}

function clearStatus() {
  statusBox.className = 'mb-4 hidden rounded-2xl px-4 py-3 text-sm';
}

async function apiRequest(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    let message = `요청 실패 (${response.status})`;
    try { message = (await response.json()).detail || message; } catch (error) { /* 응답 본문 없음 */ }
    throw new Error(Array.isArray(message) ? message.map((item) => item.msg).join(', ') : message);
  }
  return response.status === 204 ? null : response.json();
}

function formatLocalDate(value) {
  if (!value) return '-';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('ko-KR', { dateStyle: 'medium', timeStyle: 'short' });
}

function toUtcValue(value) {
  if (!value) return '';
  return new Date(value).toISOString();
}

function toLocalInputValue(value) {
  if (!value) return '';
  const date = new Date(value);
  const offset = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

function renderShell(content) {
  app.innerHTML = `<div class="animate-[fadeIn_.2s_ease-out]">${content}</div>`;
  document.querySelectorAll('.navButton').forEach((button) => {
    const active = button.dataset.view === state.view;
    button.className = `navButton rounded-xl px-3 py-2 font-medium ${active ? 'bg-slate-800 text-white dark:bg-white dark:text-slate-900' : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'}`;
  });
}

function renderList() {
  const cards = state.notes.length ? state.notes.map((note) => `
    <button data-note-id="${note.id}" class="noteCard rounded-3xl border border-white/80 bg-white/80 p-5 text-left shadow-lg shadow-slate-200/50 backdrop-blur transition hover:-translate-y-0.5 hover:shadow-xl dark:border-white/10 dark:bg-slate-900/80 dark:shadow-black/20">
      <h3 class="truncate text-lg font-semibold">${escapeHtml(note.title)}</h3>
      <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">${formatLocalDate(note.met_at)} · ${escapeHtml(note.attendees || '참석자 미정')}</p>
      <p class="mt-4 line-clamp-2 text-sm text-slate-700 dark:text-slate-300">${escapeHtml((note.summary || '').split('\n')[0] || '요약 없음')}</p>
    </button>`).join('') : '<p class="col-span-full rounded-3xl bg-white/70 p-10 text-center text-slate-500 dark:bg-slate-900/70">저장된 회의록이 없습니다.</p>';
  renderShell(`
    <section>
      <div class="mb-5">
        <p class="text-sm font-medium text-cyan-600 dark:text-cyan-400">회의 기록</p>
        <h2 class="mt-1 text-3xl font-semibold tracking-tight">목록</h2>
      </div>
      <div class="mb-5 grid gap-3 rounded-3xl border border-white/70 bg-white/60 p-4 shadow-lg shadow-slate-200/40 backdrop-blur dark:border-white/10 dark:bg-slate-900/60 dark:shadow-black/20 md:grid-cols-[1fr_auto_auto]">
        <input id="searchInput" value="${escapeHtml(state.filters.q)}" placeholder="제목 또는 참석자로 검색" class="rounded-2xl border-0 bg-slate-100 px-4 py-3 outline-none ring-cyan-500 focus:ring-2 dark:bg-slate-800">
        <input id="fromInput" type="date" value="${state.filters.from}" class="rounded-2xl border-0 bg-slate-100 px-4 py-3 outline-none ring-cyan-500 focus:ring-2 dark:bg-slate-800">
        <input id="toInput" type="date" value="${state.filters.to}" class="rounded-2xl border-0 bg-slate-100 px-4 py-3 outline-none ring-cyan-500 focus:ring-2 dark:bg-slate-800">
      </div>
      <div id="cards" class="grid gap-4 md:grid-cols-2">${cards}</div>
    </section>`);
  document.querySelector('#searchInput').addEventListener('input', debounce(loadNotes, 250));
  document.querySelector('#fromInput').addEventListener('change', loadNotes);
  document.querySelector('#toInput').addEventListener('change', loadNotes);
  document.querySelectorAll('.noteCard').forEach((card) => card.addEventListener('click', () => showDetail(Number(card.dataset.noteId))));
}

function renderCreate(note = {}) {
  const isEdit = Boolean(note.id);
  renderShell(`
    <section>
      <div class="mb-5"><p class="text-sm font-medium text-cyan-600 dark:text-cyan-400">새 회의록</p><h2 class="mt-1 text-3xl font-semibold tracking-tight">${isEdit ? '회의록 수정' : '넣기'}</h2></div>
      <form id="noteForm" class="space-y-4 rounded-3xl border border-white/70 bg-white/70 p-5 shadow-xl shadow-slate-200/50 backdrop-blur dark:border-white/10 dark:bg-slate-900/70 dark:shadow-black/20">
        <input id="title" required maxlength="200" value="${escapeHtml(note.title || '')}" placeholder="제목" class="w-full rounded-2xl border-0 bg-slate-100 px-4 py-3 outline-none ring-cyan-500 focus:ring-2 dark:bg-slate-800">
        <div class="grid gap-4 md:grid-cols-2"><input id="metAt" required type="datetime-local" value="${toLocalInputValue(note.met_at)}" class="rounded-2xl border-0 bg-slate-100 px-4 py-3 outline-none ring-cyan-500 focus:ring-2 dark:bg-slate-800"><input id="attendees" value="${escapeHtml(note.attendees || '')}" placeholder="참석자 (쉼표로 구분)" class="rounded-2xl border-0 bg-slate-100 px-4 py-3 outline-none ring-cyan-500 focus:ring-2 dark:bg-slate-800"></div>
        <div class="grid gap-3 md:grid-cols-[1fr_auto]"><input id="audioFile" type="file" accept=".mp3,.wav,audio/mpeg,audio/wav" class="w-full rounded-2xl bg-slate-100 px-4 py-3 text-sm dark:bg-slate-800"><button type="button" id="transcribeButton" class="rounded-2xl bg-cyan-600 px-5 py-3 font-medium text-white hover:bg-cyan-700">받아쓰기</button></div>
        <textarea id="body" required rows="8" placeholder="본문 - 받아쓴 원문 또는 붙여넣은 메모" class="w-full resize-y rounded-2xl border-0 bg-slate-100 px-4 py-3 outline-none ring-cyan-500 focus:ring-2 dark:bg-slate-800">${escapeHtml(note.body || '')}</textarea>
        <div class="flex flex-wrap items-center gap-3"><button class="rounded-2xl bg-slate-800 px-6 py-3 font-medium text-white hover:bg-slate-700 dark:bg-white dark:text-slate-900" type="submit">${isEdit ? '저장' : '정리하기'}</button><span id="saveStatus" class="text-sm text-slate-500"></span></div>
        ${isEdit ? `<button type="button" id="deleteButton" class="rounded-2xl bg-rose-600 px-5 py-3 font-medium text-white hover:bg-rose-700">삭제</button>` : ''}
      </form>
    </section>`);
  document.querySelector('#noteForm').addEventListener('submit', (event) => saveNote(event, note.id));
  document.querySelector('#transcribeButton').addEventListener('click', transcribeFile);
  if (isEdit) document.querySelector('#deleteButton').addEventListener('click', () => deleteNote(note.id));
}

function renderDetail(note) {
  const section = (title, value, color) => `<article class="border-l-4 ${color} rounded-2xl bg-slate-100/80 p-4 dark:bg-slate-800/80"><h3 class="font-semibold">${title}</h3><p class="mt-3 whitespace-pre-wrap text-sm">${escapeHtml(value || '없음')}</p></article>`;
  renderShell(`<section class="rounded-3xl border border-white/70 bg-white/70 p-5 shadow-xl shadow-slate-200/50 backdrop-blur dark:border-white/10 dark:bg-slate-900/70 dark:shadow-black/20"><div class="flex items-start justify-between gap-4"><div><p class="text-sm text-slate-500">${formatLocalDate(note.met_at)} · ${escapeHtml(note.attendees || '참석자 미정')}</p><h2 class="mt-2 text-3xl font-semibold">${escapeHtml(note.title)}</h2></div><button id="closeDetail" class="rounded-xl px-3 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-800">닫기</button></div><div class="mt-6 grid gap-3 md:grid-cols-3">${section('요약', note.summary, 'border-cyan-500')}${section('결정사항', note.decisions, 'border-orange-500')}${section('할 일', note.todos, 'border-emerald-500')}</div><details class="mt-5 rounded-2xl bg-slate-100/70 p-4 dark:bg-slate-800/70"><summary class="cursor-pointer font-medium">받아쓴 본문 보기</summary><p class="mt-3 whitespace-pre-wrap text-sm">${escapeHtml(note.body)}</p></details><div class="mt-5 flex gap-3"><button id="editButton" class="rounded-2xl bg-slate-800 px-5 py-3 font-medium text-white dark:bg-white dark:text-slate-900">제목 수정</button><button id="detailDeleteButton" class="rounded-2xl bg-rose-600 px-5 py-3 font-medium text-white">삭제</button></div></section>`);
  document.querySelector('#closeDetail').addEventListener('click', () => navigate('list'));
  document.querySelector('#editButton').addEventListener('click', () => { state.view = 'create'; renderCreate(note); });
  document.querySelector('#detailDeleteButton').addEventListener('click', () => deleteNote(note.id));
}

function renderTodos() {
  const rows = state.todos.map((todo) => `<tr class="border-b border-slate-200/70 dark:border-slate-700"><td class="px-3 py-3">${escapeHtml(todo.what)}</td><td class="px-3 py-3">${escapeHtml(todo.who)}</td><td class="px-3 py-3">${escapeHtml(todo.when)}</td><td class="px-3 py-3">${escapeHtml(todo.note_title)}</td></tr>`).join('');
  renderShell(`<section><div class="mb-5"><p class="text-sm font-medium text-emerald-600 dark:text-emerald-400">Action items</p><h2 class="mt-1 text-3xl font-semibold tracking-tight">할 일</h2></div><div class="overflow-x-auto rounded-3xl border border-white/70 bg-white/70 shadow-xl shadow-slate-200/50 backdrop-blur dark:border-white/10 dark:bg-slate-900/70 dark:shadow-black/20"><table class="w-full min-w-[620px] text-left text-sm"><thead class="bg-slate-800 text-white dark:bg-slate-700"><tr><th class="px-3 py-3">내용</th><th class="px-3 py-3">담당자</th><th class="px-3 py-3">기한</th><th class="px-3 py-3">회의</th></tr></thead><tbody>${rows || '<tr><td colspan="4" class="px-3 py-10 text-center text-slate-500">등록된 할 일이 없습니다.</td></tr>'}</tbody></table></div></section>`);
}

async function loadNotes() {
  state.filters.q = document.querySelector('#searchInput')?.value || state.filters.q;
  state.filters.from = document.querySelector('#fromInput')?.value || state.filters.from;
  state.filters.to = document.querySelector('#toInput')?.value || state.filters.to;
  const params = new URLSearchParams(Object.entries(state.filters).filter(([, value]) => value));
  try { state.notes = await apiRequest(`/api/notes?${params}`); renderList(); clearStatus(); } catch (error) { setStatus(error.message, 'error'); }
}

async function showDetail(id) {
  try { state.selectedNote = await apiRequest(`/api/notes/${id}`); state.view = 'detail'; renderDetail(state.selectedNote); clearStatus(); } catch (error) { setStatus(error.message, 'error'); }
}

async function saveNote(event, id) {
  event.preventDefault();
  const payload = { title: document.querySelector('#title').value.trim(), met_at: toUtcValue(document.querySelector('#metAt').value), attendees: document.querySelector('#attendees').value.trim(), body: document.querySelector('#body').value.trim() };
  try { state.selectedNote = await apiRequest(id ? `/api/notes/${id}` : '/api/notes', { method: id ? 'PUT' : 'POST', body: JSON.stringify(payload) }); setStatus('회의록을 저장했습니다.'); state.view = 'detail'; renderDetail(state.selectedNote); } catch (error) { setStatus(error.message, 'error'); }
}

async function transcribeFile() {
  const file = document.querySelector('#audioFile').files[0];
  if (!file) return setStatus('mp3 또는 wav 파일을 선택해 주세요.', 'error');
  const formData = new FormData(); formData.append('file', file);
  const button = document.querySelector('#transcribeButton'); button.disabled = true; button.textContent = '받아쓰는 중...';
  try { const result = await apiRequest('/api/upload', { method: 'POST', headers: {}, body: formData }); document.querySelector('#body').value = result.text; setStatus('받아쓰기가 완료되었습니다.'); } catch (error) { setStatus(error.message, 'error'); } finally { button.disabled = false; button.textContent = '받아쓰기'; }
}

async function deleteNote(id) {
  if (!window.confirm('회의록을 삭제할까요?')) return;
  try { await apiRequest(`/api/notes/${id}`, { method: 'DELETE' }); state.view = 'list'; await loadNotes(); setStatus('회의록을 삭제했습니다.'); } catch (error) { setStatus(error.message, 'error'); }
}

async function loadTodos() {
  try { state.todos = await apiRequest('/api/todos'); renderTodos(); clearStatus(); } catch (error) { setStatus(error.message, 'error'); }
}

function navigate(view) {
  state.view = view;
  if (view === 'list') loadNotes();
  else if (view === 'create') renderCreate();
  else if (view === 'todos') loadTodos();
}

function debounce(callback, delay) { let timer; return (...args) => { clearTimeout(timer); timer = setTimeout(() => callback(...args), delay); }; }

document.querySelectorAll('.navButton').forEach((button) => button.addEventListener('click', () => navigate(button.dataset.view)));
document.querySelector('#themeButton').addEventListener('click', () => { const dark = document.documentElement.classList.toggle('dark'); localStorage.setItem('theme', dark ? 'dark' : 'light'); });
if (localStorage.getItem('theme') === 'dark' || (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) document.documentElement.classList.add('dark');
navigate('list');
