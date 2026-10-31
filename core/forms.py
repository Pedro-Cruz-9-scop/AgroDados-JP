from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError


class FotoPerfilForm(forms.Form):
    foto = forms.ImageField(required=False)
    remover_foto = forms.BooleanField(required=False)

    def clean_foto(self):
        foto = self.cleaned_data.get('foto')
        limite = min(5 * 1024 * 1024, settings.MAX_UPLOAD_BYTES)
        if foto and foto.size > limite:
            raise ValidationError(f'A foto deve ter no máximo {limite // (1024 * 1024)} MB.')
        if foto and foto.image.format not in {'JPEG', 'PNG', 'WEBP'}:
            raise ValidationError('Use uma imagem nos formatos JPG, PNG ou WEBP.')
        if foto and (
            foto.image.width > 6000
            or foto.image.height > 6000
            or foto.image.width * foto.image.height > 25_000_000
        ):
            raise ValidationError('A resolução da foto deve ser de até 25 megapixels.')
        return foto

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('foto') and cleaned_data.get('remover_foto'):
            raise ValidationError('Envie uma foto ou escolha removê-la, não os dois.')
        return cleaned_data
