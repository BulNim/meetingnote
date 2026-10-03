// MeetingNote 화면 - 03-design #6 모듈 변수 + DOM 직접 갱신
const $ = (id) => document.getElementById(id);

let notes = [];            // 목록 화면의 현재 결과
let currentId = null;      // 상세 창에 띄운 회의록 id
let pendingDelete = false; // 삭제는 한 번 더 눌러야 지워짐

// --- 공통 ---------------------------------------------------------------
async function api(path, options = {}) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = '';
    try { detail = JSON.stringify(await res.json()); } catch (e) { detail = res.statusText; }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  return res.status === 204 ? null : res.json();
}

// datetime-local 값은 로컬 시각이므로 보낼 때 UTC 로 바꾼다 (02-specs)
function localToUtc(value) {
  if (!value) return null;
  return new Date(value).toISOString().slice(0, 19);
}
// 받아서 표시할 때는 로컬로 되돌린다
function utcToLocalText(value) {
  if (!value) return '';
  const d = new Date(value.endsWith('Z') ? value : value + 'Z');
  return d.toLocaleString('ko-KR', { dateStyle: 'medium', timeStyle: 'short' });
}
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

// --- 탭 -----------------------------------------------------------------
const VIEWS = { list: 'viewList', new: 'viewNew', todos: 'viewTodos' };
function showTab(name) {
  Object.entries(VIEWS).forEach(([k, id]) => $(id).classList.toggle('hidden', k !== name));
  document.querySelectorAll('.tab').forEach((b) => {
    const on = b.dataset.tab === name;
    b.classList.toggle('bg-zinc-800', on);
    b.classList.toggle('text-white', on);
    b.classList.toggle('dark:bg-zinc-200', on);
    b.classList.toggle('dark:text-zinc-900', on);
  });
  if (name === 'list') loadNotes();
  if (name === 'todos') loadTodos();
}
document.querySelectorAll('.tab').forEach((b) => b.addEventListener('click', () => showTab(b.dataset.tab)));

// --- 테마 (03-design #8) ------------------------------------------------
$('btnTheme').addEventListener('click', () => {
  const dark = document.documentElement.classList.toggle('dark');
  localStorage.setItem('theme', dark ? 'dark' : 'light');
});

// --- 화면 1 목록 --------------------------------------------------------
async function loadNotes() {
  const params = new URLSearchParams();
  if ($('q').value.trim()) params.set('q', $('q').value.trim());
  if ($('from').value) params.set('from', $('from').value);
  if ($('to').value) params.set('to', $('to').value);
  const qs = params.toString();
  notes = await api('/api/notes' + (qs ? '?' + qs : ''));
  renderCards();
}

function renderCards() {
  const box = $('cards');
  if (!notes.length) {
    box.innerHTML = '<p class="text-sm text-zinc-500">저장된 회의록이 없습니다.</p>';
    return;
  }
  box.innerHTML = notes.map((n) => [
    '<article data-id="' + n.id + '" class="card cursor-pointer rounded-2xl p-4 bg-white/70 dark:bg-zinc-900/70 border border-zinc-200 dark:border-zinc-800 shadow-lg hover:shadow-xl transition">',
    '<h2 class="font-bold">' + esc(n.title) + '</h2>',
    '<p class="text-xs text-zinc-500 mt-1">' + esc(utcToLocalText(n.met_at)) + ' · ' + esc(n.attendees || '참석자 미기재') + '</p>',
    '<p class="text-sm mt-3">' + esc((n.summary || '').split('\n')[0] || '구분 실패') + '</p>',
    '</article>'
  ].join('')).join('');
  box.querySelectorAll('.card').forEach((el) =>
    el.addEventListener('click', () => openDetail(Number(el.dataset.id))));
}

['q', 'from', 'to'].forEach((id) => $(id).addEventListener('input', loadNotes));

// --- 화면 2 넣기 --------------------------------------------------------
$('btnUp').addEventListener('click', async () => {
  const f = $('file').files[0];
  if (!f) { $('upState').textContent = '파일을 먼저 고르세요'; return; }
  const ext = f.name.toLowerCase().slice(f.name.lastIndexOf('.'));
  if (ext !== '.mp3' && ext !== '.wav') { $('upState').textContent = 'mp3, wav 만 됩니다 (415)'; return; }
  if (f.size > 25 * 1024 * 1024) { $('upState').textContent = '25MB 를 넘습니다 (413)'; return; }
  $('btnUp').disabled = true;
  $('upState').textContent = '받아쓰는 중...';
  try {
    const fd = new FormData();
    fd.append('file', f);
    const out = await api('/api/upload', { method: 'POST', body: fd });
    $('body').value = out.body;
    $('upState').textContent = '받아쓰기 완료 (' + out.body.length + '자)';
  } catch (e) {
    $('upState').textContent = '받아쓰기 실패 (' + (e.status || '오류') + ')';
  } finally {
    $('btnUp').disabled = false;
  }
});

$('btnSave').addEventListener('click', async () => {
  if (!$('title').value.trim()) { $('saveState').textContent = '제목을 적으세요'; return; }
  if (!$('metAt').value) { $('saveState').textContent = '일시를 고르세요'; return; }
  if (!$('body').value.trim()) { $('saveState').textContent = '본문이 비었습니다'; return; }
  $('btnSave').disabled = true;
  $('saveState').textContent = '정리하는 중...';
  try {
    const saved = await api('/api/notes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: $('title').value.trim(),
        met_at: localToUtc($('metAt').value),
        attendees: $('attendees').value.trim() || null,
        body: $('body').value,
      }),
    });
    renderResult(saved);
    $('saveState').textContent = '저장 완료';
  } catch (e) {
    $('saveState').textContent = '저장 실패 (' + (e.status || '오류') + ')';
  } finally {
    $('btnSave').disabled = false;
  }
});

function renderResult(n) {
  const col = (title, color, text) => [
    '<div class="rounded-2xl p-4 bg-white/70 dark:bg-zinc-900/70 border-l-4 ' + color + ' shadow-lg">',
    '<h3 class="font-bold mb-2">' + title + '</h3>',
    '<p class="text-sm whitespace-pre-line">' + esc(text || '구분 실패') + '</p>',
    '</div>'
  ].join('');
  $('result').innerHTML =
    col('요약', 'border-sky-500', n.summary) +
    col('결정사항', 'border-orange-500', n.decisions) +
    col('할 일', 'border-emerald-500', n.todos);
}

// --- 화면 3 상세 (겹침 창) ----------------------------------------------
async function openDetail(id) {
  const n = await api('/api/notes/' + id);
  currentId = id;
  pendingDelete = false;
  const col = (title, color, text) => [
    '<div class="rounded-2xl p-4 bg-zinc-50 dark:bg-zinc-800/60 border-l-4 ' + color + '">',
    '<h3 class="font-bold mb-2">' + title + '</h3>',
    '<p class="text-sm whitespace-pre-line">' + esc(text || '구분 실패') + '</p>',
    '</div>'
  ].join('');
  $('modal').innerHTML = [
    '<div class="max-w-4xl mx-auto my-8 rounded-2xl p-5 bg-white dark:bg-zinc-900 shadow-xl">',
    '<div class="flex items-start gap-3">',
    '<div><h2 class="text-xl font-bold">' + esc(n.title) + '</h2>',
    '<p class="text-xs text-zinc-500 mt-1">' + esc(utcToLocalText(n.met_at)) + ' · ' + esc(n.attendees || '참석자 미기재') + '</p></div>',
    '<button id="mClose" class="ml-auto text-sm text-zinc-500 min-h-11 px-2">닫기</button>',
    '</div>',
    '<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">',
    col('요약', 'border-sky-500', n.summary),
    col('결정사항', 'border-orange-500', n.decisions),
    col('할 일', 'border-emerald-500', n.todos),
    '</div>',
    '<details class="mt-4"><summary class="cursor-pointer text-sm text-zinc-500">받아쓴 본문 보기</summary>',
    '<p class="text-sm mt-2 whitespace-pre-line">' + esc(n.body) + '</p></details>',
    '<div class="grid grid-cols-1 sm:grid-cols-[1fr_auto_auto] gap-3 mt-5">',
    '<input id="mTitle" value="' + esc(n.title) + '" placeholder="제목 수정칸" class="rounded-xl px-3 py-2 bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 min-h-11" />',
    '<button id="mSave" class="rounded-xl px-4 py-2 bg-zinc-800 dark:bg-zinc-200 text-white dark:text-zinc-900 font-semibold min-h-11">제목 수정</button>',
    '<button id="mDel" class="rounded-xl px-4 py-2 bg-rose-600 text-white font-semibold min-h-11">삭제</button>',
    '</div>',
    '<p id="mState" class="text-xs text-zinc-500 mt-2">삭제는 한 번 더 눌러야 지워짐</p>',
    '</div>'
  ].join('');
  $('modal').classList.remove('hidden');

  $('mClose').addEventListener('click', closeDetail);
  // 바깥 어두운 영역을 누르면 닫힘
  $('modal').onclick = (e) => { if (e.target === $('modal')) closeDetail(); };

  $('mSave').addEventListener('click', async () => {
    await api('/api/notes/' + currentId, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: $('mTitle').value.trim(),
        met_at: n.met_at,
        attendees: n.attendees,
        body: n.body,
      }),
    });
    $('mState').textContent = '제목을 고쳤습니다';
    await loadNotes();
  });

  $('mDel').addEventListener('click', async () => {
    if (!pendingDelete) {
      pendingDelete = true;
      $('mState').textContent = '한 번 더 누르면 지워집니다';
      return;
    }
    await api('/api/notes/' + currentId, { method: 'DELETE' });
    closeDetail();
    await loadNotes();
  });
}

function closeDetail() {
  $('modal').classList.add('hidden');
  $('modal').innerHTML = '';
  currentId = null;
}

// --- 화면 4 할 일 -------------------------------------------------------
async function loadTodos() {
  const rows = await api('/api/todos');
  $('todoBody').innerHTML = rows.length
    ? rows.map((t) => [
        '<tr class="border-t border-zinc-200 dark:border-zinc-800">',
        '<td class="px-3 py-2">' + esc(t.what) + '</td>',
        '<td class="px-3 py-2 font-semibold">' + esc(t.who) + '</td>',
        '<td class="px-3 py-2">' + esc(t.when) + '</td>',
        '<td class="px-3 py-2 text-zinc-500">' + esc(t.note_title) + '</td>',
        '</tr>'
      ].join('')).join('')
    : '<tr><td class="px-3 py-3 text-sm text-zinc-500" colspan="4">할 일이 없습니다.</td></tr>';
}

// --- 시작 ---------------------------------------------------------------
showTab('list');
