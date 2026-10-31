document.addEventListener('DOMContentLoaded', () => {
  const profileCard = document.querySelector('.profile-card');
  if (profileCard) {
    profileCard.setAttribute('data-ready', 'true');
  }
});
