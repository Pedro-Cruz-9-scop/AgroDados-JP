import json
import math
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import FotoPerfilForm
from .models import (
    Atividade,
    DocumentoPropriedade,
    Insumo,
    PerfilUsuario,
    Propriedade,
    Talhao,
)


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    properties = Propriedade.objects.filter(proprietario=request.user)
    inputs = Insumo.objects.filter(proprietario=request.user)
    activities = Atividade.objects.filter(proprietario=request.user)
    plot_count = Talhao.objects.filter(propriedade__proprietario=request.user).count()
    activity_stats = list(
        activities.values('tipo').annotate(total=Count('id')).order_by('-total', 'tipo')
    )
    max_activity_count = max((item['total'] for item in activity_stats), default=0)
    for item in activity_stats:
        item['percentage'] = (
            round(item['total'] * 100 / max_activity_count) if max_activity_count else 0
        )
    return render(
        request,
        'core/dashboard.html',
        {
            'properties': properties,
            'activities': activities[:5],
            'property_count': properties.count(),
            'input_count': inputs.count(),
            'activity_count': activities.count(),
            'plot_count': plot_count,
            'activity_stats': activity_stats,
        },
    )


@login_required
def propriedades(request):
    properties = Propriedade.objects.filter(proprietario=request.user)
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        municipio = request.POST.get('municipio', '').strip()
        responsavel = request.POST.get('responsavel', '').strip()
        cultura = request.POST.get('cultura', '').strip()
        try:
            area = Decimal((request.POST.get('area') or '0').replace(',', '.'))
            if area < 0:
                raise InvalidOperation
            if not nome:
                raise ValueError
            Propriedade.objects.create(
                proprietario=request.user,
                nome=nome,
                municipio=municipio,
                area_hectares=area,
                responsavel=responsavel,
                cultura_principal=cultura,
            )
            messages.success(request, 'Propriedade cadastrada com sucesso.')
            return redirect('propriedades')
        except (InvalidOperation, ValueError):
            messages.error(request, 'Informe um nome e uma área válida (zero ou maior).')
    return render(request, 'core/propriedades.html', {'properties': properties})


@login_required
def talhoes(request):
    properties = Propriedade.objects.filter(proprietario=request.user)
    activities = Atividade.objects.filter(proprietario=request.user)
    if request.method == 'POST':
        if request.POST.get('action') == 'delete':
            messages.error(request, 'Use o botão Excluir da tabela e confirme sua senha.')
            return redirect('talhoes')

        try:
            property_id = int(request.POST.get('propriedade', ''))
        except (TypeError, ValueError):
            property_id = None
        propriedade = properties.filter(pk=property_id).first()
        nome = request.POST.get('nome', '').strip()
        cultura = request.POST.get('cultura', '').strip()
        try:
            if propriedade is None:
                raise ValueError('Selecione uma propriedade da sua conta.')
            if not nome or len(nome) > 80 or len(cultura) > 80:
                raise ValueError('Informe um nome e uma cultura válidos para o talhão.')

            limites = json.loads(request.POST.get('limites', ''))
            if not isinstance(limites, list) or not 3 <= len(limites) <= 1000:
                raise ValueError('O limite do talhão precisa ter pelo menos 3 pontos.')

            coordenadas = []
            for ponto in limites:
                if (
                    not isinstance(ponto, list)
                    or len(ponto) != 2
                    or any(isinstance(valor, bool) for valor in ponto)
                ):
                    raise ValueError('O limite do talhão contém coordenadas inválidas.')
                latitude, longitude = map(float, ponto)
                if (
                    not math.isfinite(latitude)
                    or not math.isfinite(longitude)
                    or not -90 <= latitude <= 90
                    or not -180 <= longitude <= 180
                ):
                    raise ValueError('O limite do talhão contém coordenadas inválidas.')
                coordenadas.append([latitude, longitude])

            earth_radius_meters = 6_378_137
            ring_sum = 0
            for index, (latitude, longitude) in enumerate(coordenadas):
                next_latitude, next_longitude = coordenadas[(index + 1) % len(coordenadas)]
                ring_sum += (
                    (next_longitude - longitude)
                    * math.pi
                    / 180
                    * (2 + math.sin(math.radians(latitude)) + math.sin(math.radians(next_latitude)))
                )
            area_hectares = Decimal(
                str(abs(ring_sum) * earth_radius_meters**2 / 2 / 10_000)
            ).quantize(Decimal('0.01'))
            if area_hectares <= 0 or area_hectares > Decimal('9999999999.99'):
                raise ValueError('Desenhe um limite com área maior que zero.')

            Talhao.objects.create(
                propriedade=propriedade,
                nome=nome,
                cultura=cultura,
                area_hectares=area_hectares,
                limites=coordenadas,
            )
            messages.success(request, 'Talhão salvo com sucesso.')
            return redirect('talhoes')
        except (
            json.JSONDecodeError,
            TypeError,
            ValueError,
            OverflowError,
            InvalidOperation,
        ) as error:
            messages.error(request, str(error) or 'Confira os dados do talhão e tente novamente.')

    fields = Talhao.objects.filter(
        propriedade__proprietario=request.user,
    ).select_related('propriedade')
    saved_fields = [
        {
            'name': field.nome,
            'property': field.propriedade.nome,
            'culture': field.cultura,
            'area': str(field.area_hectares),
            'coordinates': field.limites,
        }
        for field in fields
    ]
    return render(
        request,
        'core/talhoes.html',
        {
            'properties': properties,
            'activities': activities,
            'fields': fields,
            'saved_fields': saved_fields,
            'total_area': properties.aggregate(total=Sum('area_hectares'))['total'] or 0,
        },
    )


@login_required
def buscar(request):
    query = request.GET.get('q', '').strip()[:100]
    properties = Propriedade.objects.none()
    fields = Talhao.objects.none()
    activities = Atividade.objects.none()
    inputs = Insumo.objects.none()
    documents = DocumentoPropriedade.objects.none()

    if query:
        properties = Propriedade.objects.filter(proprietario=request.user).filter(
            Q(nome__icontains=query)
            | Q(municipio__icontains=query)
            | Q(cultura_principal__icontains=query)
        )
        fields = (
            Talhao.objects.filter(
                propriedade__proprietario=request.user,
            )
            .filter(
                Q(nome__icontains=query)
                | Q(cultura__icontains=query)
                | Q(propriedade__nome__icontains=query)
            )
            .select_related('propriedade')
        )
        activities = Atividade.objects.filter(proprietario=request.user).filter(
            Q(propriedade__icontains=query)
            | Q(talhao__icontains=query)
            | Q(cultura__icontains=query)
            | Q(tipo__icontains=query)
            | Q(produto__icontains=query)
            | Q(responsavel__icontains=query)
        )
        inputs = Insumo.objects.filter(proprietario=request.user).filter(
            Q(nome__icontains=query)
            | Q(categoria__icontains=query)
            | Q(observacoes__icontains=query)
        )
        documents = (
            DocumentoPropriedade.objects.filter(
                propriedade__proprietario=request.user,
            )
            .filter(
                Q(titulo__icontains=query)
                | Q(categoria__icontains=query)
                | Q(numero__icontains=query)
                | Q(observacoes__icontains=query)
                | Q(propriedade__nome__icontains=query)
            )
            .select_related('propriedade')
        )

    result_count = sum(
        results.count() for results in (properties, fields, activities, inputs, documents)
    )
    return render(
        request,
        'core/busca.html',
        {
            'query': query,
            'properties': properties[:25],
            'fields': fields[:25],
            'activities': activities[:25],
            'inputs': inputs[:25],
            'documents': documents[:25],
            'result_count': result_count,
        },
    )


@login_required
def insumos(request):
    inputs = Insumo.objects.filter(proprietario=request.user)
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        try:
            quantidade = Decimal((request.POST.get('quantidade') or '0').replace(',', '.'))
            if not nome or quantidade < 0:
                raise ValueError
            Insumo.objects.create(
                proprietario=request.user,
                nome=nome,
                categoria=request.POST.get('categoria', 'Outros'),
                quantidade=quantidade,
                unidade=request.POST.get('unidade', 'kg'),
                observacoes=request.POST.get('observacoes', '').strip(),
            )
            messages.success(request, 'Insumo adicionado ao estoque.')
            return redirect('insumos')
        except (InvalidOperation, ValueError):
            messages.error(request, 'Informe um produto e uma quantidade válida.')
    query = request.GET.get('q', '').strip()[:100]
    if query:
        inputs = inputs.filter(
            Q(nome__icontains=query)
            | Q(categoria__icontains=query)
            | Q(observacoes__icontains=query)
        )
    return render(
        request,
        'core/insumos.html',
        {
            'inputs': inputs,
            'search_query': query,
            'category_count': inputs.values('categoria').distinct().count(),
        },
    )


@login_required
def atividades(request):
    activities = Atividade.objects.filter(proprietario=request.user)
    properties = Propriedade.objects.filter(proprietario=request.user)
    if request.method == 'POST':
        nome_propriedade = request.POST.get('propriedade', '').strip()
        if nome_propriedade and not properties.filter(nome=nome_propriedade).exists():
            messages.error(request, 'Selecione uma propriedade cadastrada na sua conta.')
        else:
            try:
                data_atividade = date.fromisoformat(
                    request.POST.get('data') or date.today().isoformat()
                )
                cultura = request.POST.get('cultura', '').strip()
                talhao = request.POST.get('talhao', '').strip()
                responsavel = request.POST.get('responsavel', '').strip()
                tipo = request.POST.get('tipo', 'Plantio')
                if not (nome_propriedade and cultura and talhao and responsavel):
                    raise ValueError
                valid_types = dict(Atividade.TIPO)
                if tipo not in valid_types:
                    raise ValueError
                Atividade.objects.create(
                    proprietario=request.user,
                    data=data_atividade,
                    propriedade=nome_propriedade,
                    talhao=talhao,
                    cultura=cultura,
                    tipo=tipo,
                    produto=request.POST.get('produto', '').strip(),
                    quantidade=request.POST.get('quantidade', '').strip(),
                    responsavel=responsavel,
                    observacoes=request.POST.get('observacoes', '').strip(),
                )
                messages.success(request, 'Atividade registrada no histórico.')
                return redirect('atividades')
            except ValueError:
                messages.error(
                    request, 'Confira a data e preencha propriedade, talhão, cultura e responsável.'
                )
    selected_property = request.GET.get('propriedade', '').strip()[:120]
    product_query = request.GET.get('produto', '').strip()[:120]
    if selected_property and properties.filter(nome=selected_property).exists():
        activities = activities.filter(propriedade=selected_property)
    if product_query:
        activities = activities.filter(
            Q(produto__icontains=product_query)
            | Q(talhao__icontains=product_query)
            | Q(cultura__icontains=product_query)
        )
    return render(
        request,
        'core/atividades.html',
        {
            'activities': activities,
            'properties': properties,
            'today': date.today().isoformat(),
            'selected_property': selected_property,
            'product_query': product_query,
        },
    )


@login_required
def relatorios(request):
    return render(
        request,
        'core/relatorios.html',
        {
            'activities': Atividade.objects.filter(proprietario=request.user),
            'properties': Propriedade.objects.filter(proprietario=request.user),
            'inputs': Insumo.objects.filter(proprietario=request.user),
        },
    )


@login_required
def perfil(request):
    user_profile, _ = PerfilUsuario.objects.get_or_create(usuario=request.user)
    if request.method == 'POST':
        if request.POST.get('acao') == 'foto':
            photo_form = FotoPerfilForm(request.POST, request.FILES)
            if not photo_form.is_valid():
                errors = '; '.join(
                    error for field_errors in photo_form.errors.values() for error in field_errors
                )
                messages.error(request, errors)
            elif photo_form.cleaned_data['remover_foto']:
                user_profile.foto.delete(save=False)
                user_profile.save(update_fields=['foto'])
                messages.success(request, 'Sua foto de perfil foi removida.')
                return redirect('perfil')
            elif photo_form.cleaned_data['foto']:
                old_photo = user_profile.foto.name if user_profile.foto else ''
                user_profile.foto = photo_form.cleaned_data['foto']
                user_profile.save(update_fields=['foto'])
                if old_photo and old_photo != user_profile.foto.name:
                    user_profile.foto.storage.delete(old_photo)
                messages.success(request, 'Sua foto de perfil foi atualizada.')
                return redirect('perfil')
            else:
                messages.error(request, 'Escolha uma foto antes de salvar.')
        else:
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            if len(username) < 3 or len(username) > 150:
                messages.error(request, 'O nome de usuário deve ter entre 3 e 150 caracteres.')
            elif (
                User.objects.filter(username__iexact=username).exclude(pk=request.user.pk).exists()
            ):
                messages.error(request, 'Esse nome de usuário já está em uso.')
            else:
                request.user.username = username
                request.user.email = email
                request.user.save(update_fields=['username', 'email'])
                messages.success(request, 'Seu perfil foi atualizado.')
                return redirect('perfil')
    return render(
        request,
        'core/perfil.html',
        {
            'properties': Propriedade.objects.filter(proprietario=request.user),
            'user_profile': user_profile,
        },
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        user = authenticate(request, username=username, password=request.POST.get('password', ''))
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Usuário ou senha incorretos.')
    return render(request, 'core/auth.html', {'register': False})


def cadastro(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        if len(username) < 3 or len(password) < 8:
            messages.error(
                request,
                'Use um nome de usuário com 3 caracteres ou mais e uma senha com pelo menos 8 caracteres.',
            )
        elif User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'Esse nome de usuário já está cadastrado.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            messages.success(
                request, 'Conta criada. Cadastre sua primeira propriedade para começar.'
            )
            return redirect('dashboard')
    return render(request, 'core/auth.html', {'register': True})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def documentos(request):
    propriedades = Propriedade.objects.filter(proprietario=request.user)
    if request.method == 'POST':
        propriedade_id = request.POST.get('propriedade')
        propriedade = propriedades.filter(pk=propriedade_id).first()
        arquivo = request.FILES.get('arquivo')
        if not propriedade or not arquivo:
            messages.error(request, 'Selecione uma propriedade e um arquivo.')
        elif arquivo.size > 15 * 1024 * 1024:
            messages.error(request, 'O arquivo deve ter no máximo 15 MB.')
        elif arquivo.content_type not in ['application/pdf', 'image/jpeg', 'image/png']:
            messages.error(request, 'Envie um PDF, JPG ou PNG.')
        elif request.POST.get('categoria') not in dict(DocumentoPropriedade.CATEGORIAS):
            messages.error(request, 'Selecione uma categoria de documento válida.')
        else:
            DocumentoPropriedade.objects.create(
                propriedade=propriedade,
                categoria=request.POST.get('categoria', 'Outro'),
                titulo=request.POST.get('titulo', '').strip() or arquivo.name,
                arquivo=arquivo,
                numero=request.POST.get('numero', '').strip(),
                emitido_em=request.POST.get('emitido_em') or None,
                validade=request.POST.get('validade') or None,
                observacoes=request.POST.get('observacoes', '').strip(),
            )
            messages.success(request, 'Documento anexado à propriedade.')
            return redirect('documentos')
    selected_property = propriedades.filter(
        pk=request.GET.get('propriedade'),
    ).first()
    docs = DocumentoPropriedade.objects.filter(
        propriedade__proprietario=request.user,
    ).select_related('propriedade')
    if selected_property:
        docs = docs.filter(propriedade=selected_property)
    return render(
        request,
        'core/documentos.html',
        {
            'properties': propriedades,
            'documents': docs,
            'selected_property': selected_property,
        },
    )


@login_required
def download_documento(request, documento_id):
    documentos = DocumentoPropriedade.objects.select_related('propriedade')
    if not request.user.has_perm('core.view_documentopropriedade'):
        documentos = documentos.filter(propriedade__proprietario=request.user)
    documento = get_object_or_404(documentos, pk=documento_id)
    return FileResponse(
        documento.arquivo.open('rb'),
        as_attachment=True,
        filename=Path(documento.arquivo.name).name,
    )


def _delete_with_password(request, queryset, pk, redirect_name, label, name_attr, after=None):
    obj = get_object_or_404(queryset, pk=pk)
    if not request.user.check_password(request.POST.get('password', '')):
        messages.error(request, f'Senha incorreta. {label} não foi excluído.')
        return redirect(redirect_name)
    nome = getattr(obj, name_attr)
    if after:
        after(obj)
    obj.delete()
    messages.success(request, f'{label} "{nome}" excluído.')
    return redirect(redirect_name)


@login_required
@require_POST
def excluir_insumo(request, insumo_id):
    return _delete_with_password(
        request,
        Insumo.objects.filter(proprietario=request.user),
        insumo_id,
        'core:insumos',
        'O insumo',
        'nome',
    )


@login_required
@require_POST
def excluir_propriedade(request, propriedade_id):
    def remove_files(propriedade):
        for documento in propriedade.documentos.all():
            documento.arquivo.delete(save=False)

    return _delete_with_password(
        request,
        Propriedade.objects.filter(proprietario=request.user),
        propriedade_id,
        'core:propriedades',
        'A propriedade',
        'nome',
        after=remove_files,
    )


@login_required
@require_POST
def excluir_talhao(request, talhao_id):
    return _delete_with_password(
        request,
        Talhao.objects.filter(propriedade__proprietario=request.user),
        talhao_id,
        'core:talhoes',
        'O talhão',
        'nome',
    )


@login_required
@require_POST
def excluir_atividade(request, atividade_id):
    return _delete_with_password(
        request,
        Atividade.objects.filter(proprietario=request.user),
        atividade_id,
        'core:atividades',
        'A atividade',
        'tipo',
    )


@login_required
@require_POST
def excluir_documento(request, documento_id):
    documento = get_object_or_404(
        DocumentoPropriedade.objects.filter(
            propriedade__proprietario=request.user,
        ),
        pk=documento_id,
    )
    if not request.user.check_password(request.POST.get('password', '')):
        messages.error(request, 'Senha incorreta. O documento não foi excluído.')
        return redirect('core:documentos')

    titulo = documento.titulo
    documento.arquivo.delete(save=False)
    documento.delete()
    messages.success(request, f'Documento "{titulo}" excluído.')
    return redirect('core:documentos')
