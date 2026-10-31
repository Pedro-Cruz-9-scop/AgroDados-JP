document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-delete-form]').forEach((form) => {
    const openButton = form.querySelector('[data-open-delete]');
    const confirmation = form.querySelector('[data-delete-confirmation]');
    const passwordInput = form.querySelector('input[name="password"]');
    const cancelButton = form.querySelector('[data-cancel-delete]');

    openButton.addEventListener('click', () => {
      confirmation.hidden = false;
      openButton.hidden = true;
      openButton.setAttribute('aria-expanded', 'true');
      passwordInput.focus();
    });

    cancelButton.addEventListener('click', () => {
      confirmation.hidden = true;
      openButton.hidden = false;
      openButton.setAttribute('aria-expanded', 'false');
      passwordInput.value = '';
      openButton.focus();
    });
  });
});
