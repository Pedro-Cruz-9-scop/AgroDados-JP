document.addEventListener('DOMContentLoaded', () => {
  const categorySelect = document.querySelector('[data-document-category-select]');
  const categoryLogo = document.querySelector('[data-document-category-preview] [data-document-category-logo]');
  const categoryLabel = document.querySelector('[data-document-category-label]');
  const categories = {
    CAR: { abbreviation: 'CAR', label: 'Cadastro Ambiental Rural', className: 'car', logoDataAttribute: 'logoSrcCar' },
    CCIR: { abbreviation: 'CCIR', label: 'Certificado de Cadastro de Imóvel Rural', className: 'ccir', logoDataAttribute: 'logoSrcCcir' },
    ITR: { abbreviation: 'ITR', label: 'Imposto sobre a Propriedade Territorial Rural', className: 'itr', logoDataAttribute: 'logoSrcItr', logoAlt: 'Logo do ITR' },
    Comodato: { abbreviation: 'COM', label: 'Contrato de comodato', className: 'comodato', logoDataAttribute: 'logoSrcComodato' },
    Escritura: { abbreviation: 'ESC', label: 'Escritura / matrícula', className: 'escritura', logoDataAttribute: 'logoSrcEscritura', logoAlt: 'Logo da Escritura' },
    Outro: { abbreviation: 'OUT', label: 'Outro documento', className: 'outro', logoDataAttribute: 'logoSrcOutro', logoAlt: 'Logo OUT' },
  };

  const updateCategoryPreview = () => {
    if (!categorySelect || !categoryLogo || !categoryLabel) return;

    const category = categories[categorySelect.value];
    if (!category) return;

    if (category.logoDataAttribute) {
      const logo = document.createElement('img');
      logo.src = categoryLogo.dataset[category.logoDataAttribute];
      logo.alt = category.logoAlt || `Logo do ${categorySelect.value}`;
      categoryLogo.replaceChildren(logo);
      categoryLogo.setAttribute('aria-label', logo.alt);
    } else {
      categoryLogo.textContent = category.abbreviation;
      categoryLogo.removeAttribute('aria-label');
    }
    categoryLogo.className = `document-type-logo document-type-logo--${category.className}`;
    categoryLabel.textContent = category.label;
  };

  if (categorySelect) {
    categorySelect.addEventListener('change', updateCategoryPreview);
    updateCategoryPreview();
  }

  document.querySelectorAll('[data-delete-document-form]').forEach((form) => {
    const openButton = form.querySelector('[data-open-delete]');
    const confirmation = form.querySelector('[data-delete-confirmation]');
    const passwordInput = form.querySelector('input[name="password"]');
    const cancelButton = form.querySelector('[data-cancel-delete]');

    openButton?.addEventListener('click', () => {
      confirmation.hidden = false;
      openButton.hidden = true;
      openButton.setAttribute('aria-expanded', 'true');
      passwordInput.focus();
    });

    cancelButton?.addEventListener('click', () => {
      confirmation.hidden = true;
      openButton.hidden = false;
      openButton.setAttribute('aria-expanded', 'false');
      passwordInput.value = '';
      openButton.focus();
    });
  });

  const logoLightbox = document.querySelector('[data-logo-lightbox]');
  const lightboxImage = logoLightbox?.querySelector('[data-logo-lightbox-image]');
  const closeLightboxButton = logoLightbox?.querySelector('[data-close-logo-lightbox]');

  document.querySelectorAll('[data-logo-zoom]').forEach((button) => {
    button.addEventListener('click', () => {
      const logo = button.querySelector('img');
      if (!logo || !logoLightbox || !lightboxImage) return;

      lightboxImage.src = logo.src;
      lightboxImage.alt = logo.alt;
      logoLightbox.showModal();
    });
  });

  closeLightboxButton?.addEventListener('click', () => logoLightbox.close());
  logoLightbox?.addEventListener('click', (event) => {
    if (event.target === logoLightbox) logoLightbox.close();
  });

  const fileInput = document.querySelector('input[type="file"]');
  if (!fileInput) return;

  fileInput.addEventListener('change', () => {
    const label = fileInput.closest('label');
    if (label) label.classList.add('has-file');
  });
});
