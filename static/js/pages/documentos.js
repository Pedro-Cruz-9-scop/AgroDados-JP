document.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.querySelector('input[type="file"]');
  if (!fileInput) return;

  fileInput.addEventListener('change', () => {
    const label = fileInput.closest('label');
    if (label) label.classList.add('has-file');
  });
});
