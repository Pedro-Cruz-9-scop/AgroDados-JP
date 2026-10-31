document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('.auth-form-wrap form');
  if (!form) return;

  form.addEventListener('submit', () => {
    form.classList.add('is-submitting');
  });
});
