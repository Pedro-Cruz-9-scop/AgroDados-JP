document.addEventListener('DOMContentLoaded', () => {
  const openButton = document.querySelector('[data-modal-open="propertyModal"]');
  const modal = document.getElementById('propertyModal');
  if (!openButton || !modal) return;

  openButton.addEventListener('click', () => modal.classList.add('open'));
  modal.querySelectorAll('[data-modal-close]').forEach((button) => {
    button.addEventListener('click', () => modal.classList.remove('open'));
  });
});
