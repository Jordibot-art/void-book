// ══════════════════════════════════════════
// STATE 
// ══════════════════════════════════════════
let bookmarks    = [];
let readHistory  = [];
let progress     = {};
let savedWords   = {}; // ✨ ADD THIS FOR VOCABULARY
let currentUser  = null;

// ✨ FEATURE 6 SETTINGS STATE ✨
let currentFontSize = 100;
let currentTheme = 'dark';

// Django CSRF Helper
function getCookie(name) { /* ... keep your existing getCookie code ... */ 
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

async function save() {
  if (!currentUser) return; 
  try {
    const csrftoken = getCookie('csrftoken');
    await fetch('/api/save-progress/', { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
      // ✨ ADD savedWords TO THIS LINE ✨
      body: JSON.stringify({ bookmarks, readHistory, progress, saved_words: savedWords })
    });
  } catch (error) { console.error("Failed to save progress", error); }
}

// ══════════════════════════════════════════
// UTILITIES
// ══════════════════════════════════════════
function openModal(id)  { document.getElementById(id).classList.add('open'); document.body.style.overflow='hidden'; }
function closeModal(id) { 
  document.getElementById(id).classList.remove('open'); 
  document.body.style.overflow=''; 
  // Auto-close settings if open
  document.getElementById('rs-menu').classList.remove('open');
}
function setNav(el) {
  document.querySelectorAll('.nav-links a').forEach(a=>a.classList.remove('active'));
  el.classList.add('active');
}

// ══════════════════════════════════════════
// FEATURE 5 — TOAST NOTIFICATIONS
// ══════════════════════════════════════════
function toast(msg, type='info', icon='ℹ') {
  const c = document.getElementById('toasts');
  if (!c) return;
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span class="t-icon">${icon}</span>${msg}`;
  c.appendChild(t);
  setTimeout(() => {
    t.style.animation = 'toastOut .25s ease forwards';
    setTimeout(() => t.remove(), 270);
  }, 2800);
}

// ══════════════════════════════════════════
// FEATURE 3 — REAL BACKEND AUTH
// ══════════════════════════════════════════
// ══════════════════════════════════════════
// FEATURE 3 — REAL BACKEND AUTH
// ══════════════════════════════════════════
function renderAuthArea() {
  const area = document.getElementById('auth-area');
  
  if (currentUser) {
    const init = currentUser.username[0].toUpperCase();
    
    // 1. We MUST declare this variable first so JavaScript doesn't crash!
    let adminLink = '';
    
    // 2. If they are staff, fill the variable with the button HTML
    if (currentUser.is_staff) {
        adminLink = `
          <div class="avatar-menu-item" onclick="window.location.href='/custom-admin/'" style="color:var(--accent3); font-weight:bold;">
            <span>⚙️</span>Admin Dashboard
          </div>
          <hr style="border-color:var(--border);margin:.3rem 0;">
        `;
    }

    // 3. Inject the ${adminLink} variable into the dropdown menu
    area.innerHTML = `
      <div class="avatar-wrap">
        <div class="avatar" onclick="toggleAvatarMenu()">${init}</div>
        <div class="avatar-menu" id="av-menu">
          <div class="avatar-menu-item" style="color:var(--muted);font-size:.58rem;cursor:default;"><span>👤</span>${currentUser.username}</div>
          <hr style="border-color:var(--border);margin:.3rem 0;">
          
          ${adminLink}
          
          <div class="avatar-menu-item" onclick="openPanel();closeAvatarMenu()"><span>📚</span>My Library</div>
          <div class="avatar-menu-item danger" onclick="signOut()"><span>↩</span>Sign Out</div>
        </div>
      </div>`;
  } else {
    // If nobody is logged in, show the Sign In button
    area.innerHTML = `<button class="btn-primary" onclick="openModal('auth-modal')">Sign In</button>`;
  }
}

function toggleAvatarMenu() { document.getElementById('av-menu').classList.toggle('open'); }
function closeAvatarMenu()  { const m = document.getElementById('av-menu'); if(m) m.classList.remove('open'); }

function switchAuthTab(el, id) {
  document.querySelectorAll('.auth-tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.auth-form').forEach(f=>f.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('form-'+id).classList.add('active');
}

async function handleSignIn(e) {
  e.preventDefault();
  const u = document.getElementById('si-user').value.trim();
  const p = document.getElementById('si-pass').value;
  const err = document.getElementById('si-err');
  const btn = e.target.querySelector('button');

  if (!u||!p) { showErr(err,'Please fill in all fields.'); return; }

  try {
    btn.textContent = "Signing In..."; btn.disabled = true;
    const csrftoken = getCookie('csrftoken');
    const response = await fetch('/api/login/', { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
      body: JSON.stringify({ username: u, password: p })
    });
    const data = await response.json();
    if (response.ok) {
      err.classList.remove('show');
      
      // ✨ THE FIX: Save the is_staff status to memory! ✨
      currentUser = { 
          username: data.username || u,
          is_staff: data.is_staff || false 
      };
      
      if(data.library) {
         bookmarks = data.library.bookmarks || [];
         readHistory = data.library.readHistory || [];
         progress = data.library.progress || {};
         // ✨ ADD THIS LINE to both SignIn and SignUp functions ✨
         savedWords = data.library.saved_words || data.library.savedWords || {};
      }
      closeModal('auth-modal');
      renderAuthArea();
      renderGrid(); 
      updateBadge();
      updateQuickResume();
      toast(`Welcome back, ${currentUser.username}! 👋`, 'success', '✓');
    } else {
      showErr(err, data.error || 'Invalid credentials.');
    }
  } catch (error) {
    showErr(err, 'Network error. Make sure your backend is running.');
  } finally {
    btn.textContent = "Sign In →"; btn.disabled = false;
  }
}

async function handleSignUp(e) {
  e.preventDefault();
  const u = document.getElementById('su-user').value.trim();
  const email = document.getElementById('su-email').value.trim();
  const p = document.getElementById('su-pass').value;
  const err = document.getElementById('su-err');
  const btn = e.target.querySelector('button');

  if (!u||!email||!p) { showErr(err,'Please fill in all fields.'); return; }
  if (p.length < 6) { showErr(err,'Password must be at least 6 characters.'); return; }

  try {
    btn.textContent = "Creating Account..."; btn.disabled = true;
    const csrftoken = getCookie('csrftoken');
    const response = await fetch('/api/register/', { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
      body: JSON.stringify({ username: u, email: email, password: p })
    });
    const data = await response.json();
    if (response.ok) {
      err.classList.remove('show');
      
      // ✨ Auto sign-in after registration with proper data ✨
      currentUser = { 
          username: data.username || u,
          is_staff: data.is_staff || false 
      };
      
      // ✨ Load library data from backend ✨
      if(data.library) {
         bookmarks = data.library.bookmarks || [];
         readHistory = data.library.readHistory || [];
         progress = data.library.progress || {};
         savedWords = data.library.saved_words || data.library.savedWords || {};
      }
      
      closeModal('auth-modal');
      renderAuthArea();
      renderGrid(); 
      updateBadge();
      updateQuickResume();
      toast(`Welcome, ${currentUser.username}! Your account has been created. 🎉`, 'success', '✓');
    } else {
      showErr(err, data.error || 'Registration failed.');
    }
  } catch (error) {
    showErr(err, 'Network error. Make sure your backend is running.');
  } finally {
    btn.textContent = "Create Account →"; btn.disabled = false;
  }
}

async function signOut() {
  try {
    const csrftoken = getCookie('csrftoken');
    await fetch('/api/logout/', { method: 'POST', headers: { 'X-CSRFToken': csrftoken } });
  } catch(e) {}

  currentUser = null; bookmarks = []; readHistory = []; progress = {}; savedWords = {};
  renderAuthArea(); renderGrid(); updateBadge(); updateQuickResume();
  toast('Signed out. See you next time!', 'info', '↩');
}

function showErr(el, msg) { el.textContent=msg; el.classList.add('show'); }

// ══════════════════════════════════════════
// FEATURE 1 — NOVEL READER LOGIC
// ══════════════════════════════════════════
let readerManga = null;
let currentChapterNumber = null;
let availableChapters = [];

function openReaderById(id) { 
  openReader(mangas.find(m=>m.id===id)||mangas[0]); 
}

function openReader(m) {
  readerManga = m;
  availableChapters = m.chapters ? Object.keys(m.chapters).map(Number).sort((a,b) => a - b) : [];
  
  // Resume from saved progress if it exists!
  if (progress[m.id]) {
      currentChapterNumber = progress[m.id].chapter;
  } else if (availableChapters.length > 0) {
      currentChapterNumber = availableChapters[0];
  } else {
      currentChapterNumber = m.ch || 1; 
  }

  document.getElementById('r-title').textContent    = m.title;

  updateChapterDropdown();
  renderChapter();
  openModal('reader-modal');
  addHistory(m);
}

function updateChapterDropdown() {
  const sel = document.getElementById('ch-select');
  sel.innerHTML = '';
  if (availableChapters.length > 0) {
    availableChapters.forEach(chNum => {
      const o = document.createElement('option');
      o.value = chNum; 
      o.textContent = `Chapter ${chNum}`;
      if (chNum === currentChapterNumber) o.selected = true;
      sel.appendChild(o);
    });
  } else {
    const o = document.createElement('option');
    o.value = currentChapterNumber; 
    o.textContent = `Chapter ${currentChapterNumber}`;
    sel.appendChild(o);
  }
}

function renderChapter() {
  document.getElementById('r-ch-label').textContent = `Chapter ${currentChapterNumber}`;

  let chapterText = "<p>Content for this chapter is not available yet.</p>";
  
  if (readerManga.chapters && readerManga.chapters[currentChapterNumber]) {
      const rawContent = readerManga.chapters[currentChapterNumber];
      if (Array.isArray(rawContent)) {
          chapterText = `<p>${rawContent.join('</p><br><p>')}</p>`;
      } else {
          chapterText = `<p>${rawContent}</p>`;
      }
      
      // ✨ NEW: Automatically highlight the user's saved vocabulary in the text! ✨
      if (savedWords[readerManga.id]) {
          savedWords[readerManga.id].forEach(word => {
              // This safely searches for the exact word and wraps it in a highlight style
              const regex = new RegExp(`\\b(${word})\\b`, 'gi');
              chapterText = chapterText.replace(regex, `<span style="background:rgba(255,60,95,0.3); border-bottom:2px solid var(--accent); color:inherit; padding:0 2px; border-radius:2px;">$1</span>`);
          });
      }

      document.getElementById('r-pages').innerHTML = `
        <div class="chapter-content" id="novel-page-content">
          <h3 style="color:var(--accent); margin-bottom:1.5rem; border-bottom:1px solid var(--border); padding-bottom:0.5rem;">${readerManga.title} - Ch. ${currentChapterNumber}</h3>
          ${chapterText}
        </div>`;
  } else {
      const grad = readerManga.color;
      document.getElementById('r-pages').innerHTML = `<div class="manga-page"><div class="page-art" style="background:${grad}" data-label="Chapter ${currentChapterNumber}">${readerManga.kanji}</div></div>`;
  }

  document.getElementById('page-tracker').style.display = 'none';
  document.getElementById('ch-progress').textContent = `Chapter ${currentChapterNumber}`;
  document.getElementById('ch-select').value = currentChapterNumber;
  
  saveProgress();
  applyReaderSettings(); 
}

function changeChapter() {
  currentChapterNumber = parseInt(document.getElementById('ch-select').value);
  renderChapter();
  toast(`Chapter ${currentChapterNumber} loaded`, 'info', '📖');
}

function nextPage() {
  if (availableChapters.length === 0) return toast('No further chapters available.', 'warn');
  const currentIndex = availableChapters.indexOf(currentChapterNumber);
  if (currentIndex < availableChapters.length - 1) {
      currentChapterNumber = availableChapters[currentIndex + 1];
      renderChapter();
      document.querySelector('.reader-modal').scrollTo(0,0);
  } else {
      toast('You have reached the latest chapter!', 'warn', '🎉');
  }
}

function prevPage() {
  if (availableChapters.length === 0) return;
  const currentIndex = availableChapters.indexOf(currentChapterNumber);
  if (currentIndex > 0) {
      currentChapterNumber = availableChapters[currentIndex - 1];
      renderChapter();
      document.querySelector('.reader-modal').scrollTo(0,0);
  } else {
      toast('You are at the first chapter.', 'warn');
  }
}

function saveProgress() {
  if (!readerManga) return;
  progress[readerManga.id] = { chapter: currentChapterNumber };
  save(); 
  renderGrid();
  updateQuickResume();
}

// ══════════════════════════════════════════
// NEW FEATURE 6 — READER CUSTOMIZATION
// ══════════════════════════════════════════
function toggleReaderSettings() {
  document.getElementById('rs-menu').classList.toggle('open');
}

function changeFontSize(dir) {
  currentFontSize += (dir * 10);
  if(currentFontSize < 50) currentFontSize = 50;
  if(currentFontSize > 200) currentFontSize = 200;
  document.getElementById('rs-size-display').textContent = currentFontSize + '%';
  applyReaderSettings();
}

function changeTheme(theme) {
  currentTheme = theme;
  applyReaderSettings();
}

function applyReaderSettings() {
  const page = document.getElementById('novel-page-content');
  if(!page) return; // if it's an image block, skip
  
  // Apply Font Size
  page.style.fontSize = (currentFontSize / 100) * 1.1 + 'rem'; 
  
  // Apply Theme Colors
  if(currentTheme === 'dark') {
      page.style.background = 'transparent';
      page.style.color = '#f0eef5'; // Light text
  } else if(currentTheme === 'sepia') {
      page.style.background = '#f4ecd8'; // Paper color
      page.style.color = '#433422'; // Dark brown text
      page.style.padding = '3rem 2rem';
      page.style.borderRadius = '8px';
  } else if(currentTheme === 'light') {
      page.style.background = '#ffffff'; // White
      page.style.color = '#111111'; // Black text
      page.style.padding = '3rem 2rem';
      page.style.borderRadius = '8px';
  }
}

// Close setting menu when clicking outside
document.addEventListener('click', e => {
  const rsMenu = document.getElementById('rs-menu');
  const btn = document.querySelector('.icon-btn[title="Reader Settings"]');
  if (rsMenu && rsMenu.classList.contains('open') && !rsMenu.contains(e.target) && !btn.contains(e.target)) {
    rsMenu.classList.remove('open');
  }
});

// ══════════════════════════════════════════
// FEATURE 2 — BOOKMARKS & LIBRARY
// ══════════════════════════════════════════
function toggleBookmark(id, e) {
  if (e) e.stopPropagation();
  if (!currentUser) {
    toast("Please sign in to save to your library.", "warn", "🔒");
    openModal('auth-modal');
    return;
  }
  const m = mangas.find(x=>x.id===id);
  if (!m) return;
  const idx = bookmarks.findIndex(b=>b.id===id);
  if (idx===-1) {
    bookmarks.push({id:m.id,title:m.title,genre:m.genre,ch:m.ch,rating:m.rating,color:m.color,kanji:m.kanji,coverUrl:m.coverUrl});
    toast(`Saved: "${m.title}" is now in your library.`, 'success', '★');
  } else {
    bookmarks.splice(idx,1);
    toast(`Removed "${m.title}" from your library.`, 'info', '✕');
  }
  save(); renderGrid(); updateBadge();
}

function updateBadge() {
  const b = document.getElementById('bm-badge');
  if (bookmarks.length) { b.style.display='flex'; b.textContent=bookmarks.length; }
  else b.style.display='none';
}

function addHistory(m) {
  const idx = readHistory.findIndex(h=>h.id===m.id);
  if (idx!==-1) readHistory.splice(idx,1);
  readHistory.unshift({id:m.id,title:m.title,ch:'Ch. '+ currentChapterNumber, time:'Just now', color:m.color, kanji:m.kanji, coverUrl: m.coverUrl});
  if (readHistory.length>20) readHistory.pop();
  save(); 
  updateQuickResume(); // Refresh widget
}

function openPanel() {
  renderLibrary();
  document.getElementById('library-panel').classList.add('open');
  document.getElementById('panel-overlay').classList.add('open');
  document.body.style.overflow='hidden';
}
function closePanel() {
  document.getElementById('library-panel').classList.remove('open');
  document.getElementById('panel-overlay').classList.remove('open');
  document.body.style.overflow='';
}
function switchPanelTab(el,tab) {
  document.querySelectorAll('.panel-tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.panel-tab-content').forEach(c=>c.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('panel-'+tab).classList.add('active');
}

// ══════════════════════════════════════════
// FIXED: RENDER LIBRARY & HISTORY
// ══════════════════════════════════════════
function renderLibrary() {
  const bEl = document.getElementById('panel-bookmarks');
  if (!bookmarks.length) {
    bEl.innerHTML=`<div class="empty-state"><div class="empty-icon">📚</div><p>No bookmarks yet.<br>Hover a manga and click ☆ Save.</p></div>`;
  } else {
    bEl.innerHTML = bookmarks.map(b=>{
      const p = progress[b.id];
      return `<div class="bookmark-item" onclick="openReaderById(${b.id});closePanel()">
        <div class="bm-cover" style="background:${b.color}">${b.coverUrl ? `<img src="${b.coverUrl}" style="width:100%;height:100%;object-fit:cover;">` : b.kanji}</div>
        <div class="bm-info">
          <div class="bm-title">${b.title}</div>
          <div class="bm-meta">${b.genre} · Ch.${b.ch} · ★${b.rating}</div>
          ${p?`<div class="bm-prog-wrap"><div class="bm-prog-label"><span>Currently on Chapter ${p.chapter}</span></div></div>`:''}
        </div>
        <button class="bm-remove" onclick="toggleBookmark(${b.id},event);renderLibrary()" title="Remove">✕</button>
      </div>`;
    }).join('');
  }

  // ✨ FIXED: This is now safely inside the renderLibrary function! ✨
  const hEl = document.getElementById('panel-history');
  if (!readHistory.length) {
    hEl.innerHTML=`<div class="empty-state"><div class="empty-icon">🕐</div><p>No reading history yet.<br>Start reading to track progress.</p></div>`;
  } else {
    hEl.innerHTML = readHistory.map(h=>{
      
      // Fetch the vocab words for this specific history item
      const vocab = savedWords[h.id] || [];
      let vocabHtml = '';
      if (vocab.length > 0) {
          const badges = vocab.map(w => {
            const enc = encodeURIComponent(w);
            return `<span class="vocab-badge-row" style="display:inline-flex;align-items:center;gap:4px;margin:6px 8px 0 0;">
              <span style="background:rgba(255,60,95,0.15); color:var(--accent); padding:2px 8px; border-radius:4px; font-size:0.65rem; border: 1px solid rgba(255,60,95,0.3);">${String(w).replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}</span>
              <button type="button" class="vocab-remove-btn" data-novel-id="${h.id}" data-w="${enc}" onclick="event.stopPropagation();removeSavedWordFromDataset(this)" title="Remove word">✕</button>
            </span>`;
          }).join('');
          vocabHtml = `<div style="margin-top:10px; border-top:1px solid rgba(255,255,255,0.05); padding-top:8px; width:100%;"><span style="font-size:0.65rem; color:var(--muted); display:block; margin-bottom:4px; text-transform:uppercase; letter-spacing:1px;">Saved Vocabulary:</span><div style="display:flex;flex-wrap:wrap;align-items:center;">${badges}</div></div>`;
      }

      return `
      <div class="history-item" style="flex-direction:column; align-items:flex-start; cursor:default; padding: 1rem;">
        <div style="display:flex; width:100%; align-items:center; cursor:pointer;" onclick="openReaderById(${h.id});closePanel()">
            <div class="hi-cover" style="background:${h.color}">${h.coverUrl ? `<img src="${h.coverUrl}" style="width:100%;height:100%;object-fit:cover;">` : h.kanji}</div>
            <div><div class="hi-title">${h.title}</div><div class="hi-sub">${h.ch} · ${h.time}</div></div>
            <svg style="margin-left:auto;flex-shrink:0" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
        </div>
        ${vocabHtml}
      </div>`;
    }).join('');
  }
} // <--- The function officially closes here now!

// ══════════════════════════════════════════
// NEW FEATURE 7 — QUICK RESUME WIDGET
// ══════════════════════════════════════════
function updateQuickResume() {
    const qr = document.getElementById('quick-resume');
    if (readHistory.length > 0) {
        const last = readHistory[0]; // The most recently read book
        qr.innerHTML = `
            <div class="qr-icon">📖</div>
            <div class="qr-text">
                <span class="qr-label">Resume Reading</span>
                <span class="qr-title">${last.title} <span style="color:var(--accent3);font-weight:normal;">${last.ch}</span></span>
            </div>
        `;
        qr.onclick = () => { openReaderById(last.id); }; 
        qr.style.display = 'flex';
    } else {
        qr.style.display = 'none';
    }
}

// ══════════════════════════════════════════
// FEATURE 4 — LIVE SEARCH
// ══════════════════════════════════════════
function handleSearch(val) {
  const dd = document.getElementById('search-dd');
  if (!val.trim()) { dd.classList.remove('open'); return; }
  const results = mangas.filter(m =>
    m.title.toLowerCase().includes(val.toLowerCase()) ||
    m.genre.toLowerCase().includes(val.toLowerCase())
  );
  if (!results.length) {
    dd.innerHTML = `<div class="search-empty">No results for "${val}"</div>`;
  } else {
    dd.innerHTML = results.slice(0,6).map(m=>{
      const isBm = bookmarks.some(b=>b.id===m.id);
      const coverHtml = m.coverUrl
        ? `<img src="${m.coverUrl}" alt="${m.title} cover" style="width:100%;height:100%;object-fit:cover;">`
        : m.kanji;
      return `<div class="search-result" onclick="openReaderById(${m.id});document.getElementById('global-search').value='';document.getElementById('search-dd').classList.remove('open')">
        <div class="sr-cover" style="background:${m.color}">${coverHtml}</div>
        <div>
          <div class="sr-title">${hilite(m.title, val)}</div>
          <div class="sr-meta">${m.genre} · Ch.${m.ch} · ★${m.rating}${isBm?' · <span style="color:var(--accent2)">★ Saved</span>':''}</div>
        </div>
      </div>`;
    }).join('');
  }
  dd.classList.add('open');
}

function hilite(text, q) {
  const i = text.toLowerCase().indexOf(q.toLowerCase());
  if (i===-1) return text;
  return text.slice(0,i)+`<mark style="background:rgba(255,60,95,.25);color:var(--accent);border-radius:2px;">${text.slice(i,i+q.length)}</mark>`+text.slice(i+q.length);
}

document.addEventListener('click', e=>{
  if (!e.target.closest('.avatar-wrap')) closeAvatarMenu();
  if (!e.target.closest('.search-wrap')) document.getElementById('search-dd').classList.remove('open');
});

// ══════════════════════════════════════════
// RENDER
// ══════════════════════════════════════════
function cardHTML(m) {
  const isBm = bookmarks.some(b=>b.id===m.id);
  const p    = progress[m.id];
  const kanjiFallback = `<div style="width:100%;height:100%;background:${m.color};display:flex;align-items:center;justify-content:center;font-family:'Bebas Neue';font-size:3.5rem;opacity:.8;color:#fff;">${m.kanji}</div>`;
  const coverHtml = m.coverUrl
    ? `<img src="${m.coverUrl}" style="width:100%;height:100%;object-fit:cover;object-position:${m.position || 'center'};" alt="${m.title}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';"><div style="display:none;width:100%;height:100%;background:${m.color};align-items:center;justify-content:center;font-family:'Bebas Neue';font-size:3.5rem;opacity:.8;color:#fff;">${m.kanji}</div>`
    : kanjiFallback;
  return `
    <div class="manga-card">
      <div class="manga-cover" onclick="openReaderById(${m.id})">
        ${m.badge?`<div class="manga-badge ${m.badge}">${m.badge}</div>`:''}
        ${coverHtml}
        <div class="manga-overlay">
          <button class="read-btn" onclick="openReaderById(${m.id})">▶ Read Now</button>
          <button class="bm-btn ${isBm?'bookmarked':''}" onclick="toggleBookmark(${m.id},event)">${isBm?'★ Saved':'☆ Save'}</button>
        </div>
      </div>
      <div class="manga-title">${m.title}</div>
      <div class="manga-info"><span class="genre">${m.genre}</span><span>Ch.${m.ch}</span></div>
    </div>`;
}

function renderGrid(list) {
  const data = list||mangas;
  const grid = document.getElementById('manga-grid');
  if (grid) {
    grid.innerHTML = data.length
      ? data.map(cardHTML).join('')
      : `<p style="color:var(--muted);font-family:'Space Mono';font-size:.75rem;padding:1rem 0;grid-column:1/-1;">No titles found for this genre.</p>`;
  }
}

function renderFeatured(featured) {
  const container = document.getElementById('featured-row');
  if (!container) return;
  
  if (!featured || featured.length === 0) {
    container.innerHTML = '<p style="color:var(--muted);font-family:Space Mono;font-size:.75rem;padding:1rem;">No featured novels yet. Admin can select novels to feature.</p>';
    return;
  }
  
  container.innerHTML = featured.map(m => {
    const genreTag = `<span class="tag tag-${m.genre.toLowerCase()}">${m.genre}</span>`;
    const coverHtml = m.coverUrl 
      ? `<img src="${m.coverUrl}" style="width:100%;height:100%;object-fit:cover;object-position:${m.position || 'center'};-webkit-mask-image:linear-gradient(to right,transparent,black 40%);" alt="${m.title}" onerror="this.style.display='none';">`
      : '';
    
    return `
    <div class="featured-card" onclick="openReaderById(${m.id})" style="background-color:#0a0a0f;">
      <div class="featured-bg" style="left:auto;right:0;width:55%;">${coverHtml}</div>
      <div class="featured-content" style="background:linear-gradient(to right,#0a0a0f 50%,transparent 100%);justify-content:center;">
        <div style="margin-bottom:.4rem">${genreTag}</div>
        <h3>${m.title}</h3>
        <p>Ch.${m.ch} · ${m.genre} · ★${m.rating}</p>
      </div>
    </div>`;
  }).join('');
}

function renderRankings(rankings) {
  const container = document.getElementById('rankings-list');
  if (!container) return;
  
  if (!rankings || rankings.length === 0) {
    container.innerHTML = '<p style="color:var(--muted);font-family:Space Mono;font-size:.75rem;">No top ranked novels yet (rating 9.0+ required).</p>';
    return;
  }
  
  container.innerHTML = rankings.map((r, i) => {
    const coverVisual = r.coverUrl 
      ? `<img src="${r.coverUrl}" style="width:100%;height:100%;object-fit:cover;border-radius:4px;" alt="${r.title}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';"><span style="display:none;width:100%;height:100%;align-items:center;justify-content:center;font-family:'Bebas Neue';font-size:1.2rem;color:#fff;">${r.kanji || (i + 1)}</span>` 
      : (i + 1);
    const coverStyle = r.coverUrl ? 'background:transparent;' : `background:${r.color};`;
    return `
    <div class="rank-item" onclick="openReaderById(${r.id})">
      <div class="rank-num">${String(i+1).padStart(2,'0')}</div>
      <div class="rank-cover" style="${coverStyle}">${coverVisual}</div>
      <div class="rank-info">
        <div class="rank-title">${r.title}</div>
        <div class="rank-sub">Ch.${r.ch} · ★${r.rating}</div>
      </div>
      <div class="rank-score">${r.rating}</div>
    </div>`;
  }).join('');
}

function renderUpdates(updates) {
  const container = document.getElementById('update-list');
  if (!container) return;
  
  if (!updates || updates.length === 0) {
    container.innerHTML = '<p style="color:var(--muted);font-family:Space Mono;font-size:.75rem;">No recent updates. Check back later!</p>';
    return;
  }
  
  container.innerHTML = updates.map(u => {
    const coverVisual = u.coverUrl 
      ? `<img src="${u.coverUrl}" style="width:100%;height:100%;object-fit:cover;border-radius:4px;" alt="${u.title}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';"><span style="display:none;width:100%;height:100%;align-items:center;justify-content:center;font-family:'Bebas Neue';font-size:1.2rem;color:#fff;">${u.kanji}</span>` 
      : u.kanji;
    const coverStyle = u.coverUrl ? 'background:transparent;opacity:1;padding:0;' : `background:${u.color};opacity:0.85;`;
    return `
    <div class="update-item" onclick="openReaderById(${u.id})">
      <div class="update-cover" style="${coverStyle}">${coverVisual}</div>
      <div class="update-info">
        <div class="update-title">${u.title}</div>
        <div class="update-chapter">Ch.${u.ch} — New Chapter</div>
        <div class="update-time">${u.time || 'Recently'}</div>
      </div>
      <button class="btn-primary" style="font-size:.6rem;padding:.4rem .8rem;white-space:nowrap;" onclick="event.stopPropagation();openReaderById(${u.id})">Read →</button>
    </div>`;
  }).join('');
}

function renderNewReleases(newReleases) {
  const container = document.getElementById('new-releases-grid');
  if (!container) return;
  
  if (!newReleases || newReleases.length === 0) {
    container.innerHTML = '<p style="color:var(--muted);font-family:Space Mono;font-size:.75rem;padding:1rem 0;grid-column:1/-1;">No new releases yet. Check back later!</p>';
    return;
  }
  
  container.innerHTML = newReleases.map(cardHTML).join('');
}

function filterGenre(el) {
  document.querySelectorAll('.genre-pill').forEach(p=>p.classList.remove('active'));
  el.classList.add('active');
  const g = el.textContent;
  renderGrid(g==='All'?null:mangas.filter(m=>m.genre.toLowerCase()===g.toLowerCase()));
}

// ══════════════════════════════════════════
// INIT & FETCH DATA (FAST & PARALLEL)
// ══════════════════════════════════════════
async function initializeSystem() {
    if (typeof mangas === 'undefined') window.mangas = [];
    if (typeof rankings === 'undefined') window.rankings = [];
    if (typeof updates === 'undefined') window.updates = [];

    // 1. Instantly restore authenticated user from SSR session if present
    if (window.INITIAL_USER) {
        currentUser = {
            username: window.INITIAL_USER.username,
            is_staff: Boolean(window.INITIAL_USER.is_staff)
        };
        if (window.INITIAL_USER.library) {
            bookmarks = window.INITIAL_USER.library.bookmarks || [];
            readHistory = window.INITIAL_USER.library.readHistory || [];
            progress = window.INITIAL_USER.library.progress || {};
            savedWords = window.INITIAL_USER.library.saved_words || {};
        }
    }

    // 2. ALWAYS RENDER AUTH BUTTONS & BADGES IMMEDIATELY WITHOUT BLOCKING
    renderAuthArea();
    updateBadge();
    updateQuickResume();

    // 3. Fetch popular novels immediately so the grid renders in under 200ms
    const fetchPopular = fetch('/api/popular/')
        .then(res => res.ok ? res.json() : [])
        .then(data => {
            if (Array.isArray(data) && data.length) {
                renderGrid(data);
                if (!mangas.length) {
                    mangas = data;
                }
            }
        })
        .catch(err => console.warn("Could not fetch popular novels.", err));

    const fetchFeatured = fetch('/api/featured/')
        .then(res => res.ok ? res.json() : [])
        .then(data => {
            if (Array.isArray(data)) renderFeatured(data);
        })
        .catch(err => console.warn("Could not fetch featured novels.", err));

    const fetchRankings = fetch('/api/rankings/')
        .then(res => res.ok ? res.json() : [])
        .then(data => {
            if (Array.isArray(data)) renderRankings(data);
        })
        .catch(err => console.warn("Could not fetch rankings.", err));

    const fetchUpdates = fetch('/api/updates/')
        .then(res => res.ok ? res.json() : [])
        .then(data => {
            if (Array.isArray(data)) renderUpdates(data);
        })
        .catch(err => console.warn("Could not fetch updates.", err));

    const fetchNewReleases = fetch('/api/new-releases/')
        .then(res => res.ok ? res.json() : [])
        .then(data => {
            if (Array.isArray(data)) renderNewReleases(data);
        })
        .catch(err => console.warn("Could not fetch new releases.", err));

    // 4. Background fetch for full reader chapters (non-blocking)
    const fetchNovels = fetch('/api/novels/')
        .then(res => res.ok ? res.json() : [])
        .then(dbData => {
            if (Array.isArray(dbData) && dbData.length) {
                const existingIds = new Set(mangas.map(m => m.id));
                const newNovels = dbData.filter(m => !existingIds.has(m.id));
                mangas = [...mangas, ...newNovels];
                dbData.forEach(d => {
                    const match = mangas.find(m => m.id === d.id);
                    if (match && d.chapters) {
                        match.chapters = d.chapters;
                    }
                });
                const grid = document.getElementById('manga-grid');
                if (grid && !grid.children.length) {
                    renderGrid(mangas);
                }
            }
        })
        .catch(err => console.warn("Could not reach database for novels.", err));

    await Promise.allSettled([fetchPopular, fetchFeatured, fetchRankings, fetchUpdates, fetchNewReleases, fetchNovels]);
}


// ══════════════════════════════════════════
// NEW FEATURE 8 — VOCABULARY HIGHLIGHTER
// ══════════════════════════════════════════
let currentHighlightedWord = "";
let isSaving = false; // ✨ Our shield variable

// 1. Listen for mouse release inside the reader
document.addEventListener('mouseup', function(e) {
    if (!currentUser) return; 
    
    // ✨ SAFEGUARD 1: Completely ignore the mouseup if it happens on the tooltip
    if (e.target.closest('#vocab-tooltip')) return;

    // Must be clicking inside the reader pages
    if (!e.target.closest('#r-pages')) return;
    if (isSaving) return;

    setTimeout(() => {
        if (isSaving) return; 

        const selection = window.getSelection();
        const text = selection.toString().trim();
        const tooltip = document.getElementById('vocab-tooltip');

        if (text.length > 0 && text.length < 30) {
            currentHighlightedWord = text;
            
            tooltip.style.left = `${e.clientX - 20}px`;
            tooltip.style.top = `${e.clientY - 40}px`;
            tooltip.style.display = 'block';
        } else {
            if(tooltip) tooltip.style.display = 'none';
        }
    }, 50); 
});

// Hide tooltip if they click away anywhere else on the screen
document.addEventListener('mousedown', function(e) {
    const tooltip = document.getElementById('vocab-tooltip');
    if (tooltip && !e.target.closest('#vocab-tooltip')) {
        tooltip.style.display = 'none';
        
        // Clear highlight if they click away
        const sel = window.getSelection();
        if (sel) sel.removeAllRanges(); 
    }
});

// 2. Save the word when the tooltip is CLICKED
function saveHighlightedWord() {
    if (isSaving) return;
    isSaving = true; // ✨ RAISE THE SHIELD
    
    // Hide it safely now that the full click is registered
    document.getElementById('vocab-tooltip').style.display = 'none';

    if (!readerManga || !currentHighlightedWord) {
        isSaving = false;
        return;
    }

    if (!savedWords[readerManga.id]) {
        savedWords[readerManga.id] = [];
    }

    if (!savedWords[readerManga.id].includes(currentHighlightedWord)) {
        savedWords[readerManga.id].push(currentHighlightedWord);
        save(); // Send to Django!
        toast(`Word saved: "${currentHighlightedWord}" — find it in My Library → History.`, 'success', '📌');
        renderChapter(); // Instantly apply the pink highlight
    } else {
        toast(`"${currentHighlightedWord}" is already in your vocabulary list.`, 'info');
    }

    // ✨ SAFEGUARD 2: Wipe the browser's native text selection clean
    const sel = window.getSelection();
    if (sel) {
        sel.removeAllRanges();
    }
    currentHighlightedWord = ""; // Reset the word

    // ✨ LOWER THE SHIELD after 300ms
    setTimeout(() => { isSaving = false; }, 300);
}

function removeSavedWordFromDataset(btn) {
    if (!currentUser) {
        toast('Please sign in to manage vocabulary.', 'warn', '🔒');
        openModal('auth-modal');
        return;
    }
    const novelId = parseInt(btn.getAttribute('data-novel-id'), 10);
    let word = '';
    try {
        word = decodeURIComponent(btn.getAttribute('data-w') || '');
    } catch (err) {
        return;
    }
    removeSavedWord(novelId, word);
}

function removeSavedWord(novelId, word) {
    const list = savedWords[novelId];
    if (!list || !word) return;
    const idx = list.indexOf(word);
    if (idx === -1) return;
    list.splice(idx, 1);
    if (list.length === 0) delete savedWords[novelId];
    save();
    const panel = document.getElementById('library-panel');
    if (panel && panel.classList.contains('open')) renderLibrary();
    if (readerManga && readerManga.id === novelId) renderChapter();
    toast(`Removed "${word}" from saved vocabulary.`, 'info', '✕');
}

// Start the system!
initializeSystem();
