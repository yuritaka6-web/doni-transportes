function toggleMenu() { document.getElementById('menu').classList.toggle('active'); }
let previousFocus;
function openModal() {
  previousFocus = document.activeElement;
  const modal = document.getElementById('contactModal');
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
  modal.querySelector('input').focus();
}
function closeModal() {
  document.getElementById('contactModal').style.display = 'none';
  document.body.style.overflow = '';
  previousFocus?.focus();
}
document.getElementById('contactModal')?.addEventListener('click', event => {
  if (event.target.id === 'contactModal') closeModal();
});
document.addEventListener('keydown', event => {
  const modal = document.getElementById('contactModal');
  if (!modal || modal.style.display !== 'flex') return;
  if (event.key === 'Escape') closeModal();
  if (event.key === 'Tab') {
    const focusable = [...modal.querySelectorAll('button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),a[href]')];
    const first = focusable[0], last = focusable.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }
});
