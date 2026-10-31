document.addEventListener('DOMContentLoaded', () => {
  const profileCard = document.querySelector('.profile-card');
  if (profileCard) {
    profileCard.setAttribute('data-ready', 'true');
  }

  const photoInput = document.querySelector('[data-profile-photo-input]');
  const photoPreview = document.querySelector('.profile-avatar');
  const photoStatus = document.querySelector('[data-profile-photo-status]');
  let previewUrl = null;

  photoInput?.addEventListener('change', () => {
    const photo = photoInput.files?.[0];
    if (!photo || !photoPreview || !photoStatus) return;

    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = URL.createObjectURL(photo);

    const image = document.createElement('img');
    image.src = previewUrl;
    image.alt = 'Prévia da foto de perfil';
    photoPreview.replaceChildren(image);
    photoStatus.textContent = `${photo.name} selecionada. Clique em “Salvar foto” para aplicar.`;
  });
});
