document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('activityModal');
  if (!modal) return;

  const openButton = document.querySelector('[data-modal-open="activityModal"]');
  if (openButton) {
    openButton.addEventListener('click', () => modal.classList.add('open'));
  }

  modal.querySelectorAll('[data-modal-close]').forEach((button) => {
    button.addEventListener('click', () => modal.classList.remove('open'));
  });
});
