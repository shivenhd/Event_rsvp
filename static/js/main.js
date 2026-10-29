// Theme toggle (saved in localStorage)
document.getElementById('theme-toggle').addEventListener('click', () => {
  const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem('theme', next); } catch (e) {}
});

// Auto-dismiss toast notifications
document.querySelectorAll('.toast').forEach(t => {
  setTimeout(() => t.classList.add('hide'), 4500);
  setTimeout(() => t.remove(), 5000);
});

// Live countdown on the event page
const cd = document.getElementById('countdown');
if (cd) {
  const target = new Date(cd.dataset.ts).getTime();
  const tick = () => {
    const diff = target - Date.now();
    if (diff <= 0) { cd.innerHTML = '<b>Event has started 🎉</b>'; return; }
    const d = Math.floor(diff / 864e5), h = Math.floor(diff % 864e5 / 36e5),
          m = Math.floor(diff % 36e5 / 6e4), s = Math.floor(diff % 6e4 / 1e3);
    cd.innerHTML = [[d,'days'],[h,'hrs'],[m,'min'],[s,'sec']]
      .map(([v,l]) => `<div><b>${v}</b><span>${l}</span></div>`).join('');
  };
  tick(); setInterval(tick, 1000);
}

// Client-side validation for the RSVP form (server validates again)
const form = document.getElementById('rsvp-form');
if (form) form.addEventListener('submit', e => {
  const name = form.name.value.trim(), email = form.email.value.trim();
  let msg = '';
  if (name.length < 2) msg = 'Please enter your full name.';
  else if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) msg = 'Please enter a valid email address.';
  if (msg) {
    e.preventDefault();
    const t = document.createElement('div');
    t.className = 'toast error'; t.textContent = msg;
    document.getElementById('toasts').appendChild(t);
    setTimeout(() => t.remove(), 4000);
  }
});
