from datetime import date
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from .models import Propriedade, Talhao, Insumo, Atividade


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    properties = Propriedade.objects.filter(proprietario=request.user)
    inputs = Insumo.objects.filter(proprietario=request.user)
    activities = Atividade.objects.filter(proprietario=request.user)
    plots = Talhao.objects.filter(propriedade__proprietario=request.user)
    return render(request, 'core/dashboard.html', {
        'properties': properties,
        'activities': activities[:5],
        'property_count': properties.count(),
        'input_count': inputs.count(),
        'activity_count': activities.count(),
        'plot_count': plots.count(),
    })


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
            Propriedade.objects.create(proprietario=request.user, nome=nome, municipio=municipio,
                                       area_hectares=area, responsavel=responsavel, cultura_principal=cultura)
            messages.success(request, 'Propriedade cadastrada com sucesso.')
            return redirect('propriedades')
        except (InvalidOperation, ValueError):
            messages.error(request, 'Informe um nome e uma área válida (zero ou maior).')
    return render(request, 'core/propriedades.html', {'properties': properties})


@login_required
def talhoes(request):
    properties = Propriedade.objects.filter(proprietario=request.user)
    activities = Atividade.objects.filter(proprietario=request.user)
    plots = Talhao.objects.filter(propriedade__proprietario=request.user).select_related('propriedade')
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        cultura = request.POST.get('cultura', '').strip()
        propriedade_id = request.POST.get('propriedade', '').strip()
        try:
            propriedade = properties.get(pk=propriedade_id)
            area = Decimal((request.POST.get('area') or '0').replace(',', '.'))
            area_parts = area.as_tuple()
            if (
                not nome
                or not area.is_finite()
                or area <= 0
                or area_parts.exponent < -2
                or len(area_parts.digits) + max(area_parts.exponent, 0) > 10
            ):
                raise ValueError
            area_cadastrada = propriedade.talhoes.aggregate(total=Sum('area_hectares'))['total'] or Decimal('0')
            if area_cadastrada + area > propriedade.area_hectares:
                messages.error(request, 'A soma das áreas dos talhões não pode ultrapassar a área da propriedade.')
            elif propriedade.talhoes.filter(nome__iexact=nome).exists():
                messages.error(request, 'Já existe um talhão com esse nome nesta propriedade.')
            else:
                Talhao.objects.create(propriedade=propriedade, nome=nome, area_hectares=area, cultura=cultura)
                messages.success(request, 'Talhão cadastrado com sucesso.')
                return redirect('talhoes')
        except Propriedade.DoesNotExist:
            messages.error(request, 'Selecione uma propriedade cadastrada na sua conta.')
        except (InvalidOperation, ValueError):
            messages.error(request, 'Informe o nome do talhão e uma área válida maior que zero.')
    return render(request, 'core/talhoes.html', {
        'properties': properties,
        'activities': activities,
        'plots': plots,
        'plot_count': plots.count(),
        'total_area': properties.aggregate(total=Sum('area_hectares'))['total'] or 0,
        'plot_area': plots.aggregate(total=Sum('area_hectares'))['total'] or 0,
    })


@login_required
def insumos(request):
    inputs = Insumo.objects.filter(proprietario=request.user)
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        try:
            quantidade = Decimal((request.POST.get('quantidade') or '0').replace(',', '.'))
            if not nome or quantidade < 0:
                raise ValueError
            Insumo.objects.create(proprietario=request.user, nome=nome,
                categoria=request.POST.get('categoria', 'Outros'), quantidade=quantidade,
                unidade=request.POST.get('unidade', 'kg'), observacoes=request.POST.get('observacoes', '').strip())
            messages.success(request, 'Insumo adicionado ao estoque.')
            return redirect('insumos')
        except (InvalidOperation, ValueError):
            messages.error(request, 'Informe um produto e uma quantidade válida.')
    return render(request, 'core/insumos.html', {
        'inputs': inputs,
        'category_count': inputs.values('categoria').distinct().count(),
    })


@login_required
def atividades(request):
    activities = Atividade.objects.filter(proprietario=request.user)
    properties = Propriedade.objects.filter(proprietario=request.user)
    plots = Talhao.objects.filter(propriedade__proprietario=request.user).select_related('propriedade')
    if request.method == 'POST':
        nome_propriedade = request.POST.get('propriedade', '').strip()
        if nome_propriedade and not properties.filter(nome=nome_propriedade).exists():
            messages.error(request, 'Selecione uma propriedade cadastrada na sua conta.')
        else:
            try:
                data_atividade = date.fromisoformat(request.POST.get('data') or date.today().isoformat())
                cultura = request.POST.get('cultura', '').strip()
                talhao = request.POST.get('talhao', '').strip()
                responsavel = request.POST.get('responsavel', '').strip()
                tipo = request.POST.get('tipo', 'Plantio')
                if not (nome_propriedade and cultura and talhao and responsavel):
                    raise ValueError
                valid_types = dict(Atividade.TIPO)
                if tipo not in valid_types:
                    raise ValueError
                Atividade.objects.create(proprietario=request.user, data=data_atividade,
                    propriedade=nome_propriedade, talhao=talhao, cultura=cultura, tipo=tipo,
                    produto=request.POST.get('produto', '').strip(), quantidade=request.POST.get('quantidade', '').strip(),
                    responsavel=responsavel, observacoes=request.POST.get('observacoes', '').strip())
                messages.success(request, 'Atividade registrada no histórico.')
                return redirect('atividades')
            except ValueError:
                messages.error(request, 'Confira a data e preencha propriedade, talhão, cultura e responsável.')
    return render(request, 'core/atividades.html', {
        'activities': activities,
        'properties': properties,
        'plots': plots,
        'activity_types': Atividade.TIPO,
        'today': date.today().isoformat(),
    })


@login_required
def relatorios(request):
    activities = Atividade.objects.filter(proprietario=request.user)
    plots = Talhao.objects.filter(propriedade__proprietario=request.user)
    activity_types = [
        {
            'value': code,
            'label': label,
            'count': activities.filter(tipo=code).count(),
        }
        for code, label in Atividade.TIPO
    ]
    max_count = max((item['count'] for item in activity_types), default=0)
    for item in activity_types:
        item['width'] = round(item['count'] / max_count * 100) if max_count else 0
    return render(request, 'core/relatorios.html', {
        'activities': activities,
        'properties': Propriedade.objects.filter(proprietario=request.user),
        'inputs': Insumo.objects.filter(proprietario=request.user),
        'plot_count': plots.count(),
        'activity_types': activity_types,
    })


@login_required
def perfil(request):
    return render(request, 'core/perfil.html', {'properties': Propriedade.objects.filter(proprietario=request.user)})


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
            messages.error(request, 'Use um nome de usuário com 3 caracteres ou mais e uma senha com pelo menos 8 caracteres.')
        elif User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'Esse nome de usuário já está cadastrado.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            messages.success(request, 'Conta criada. Cadastre sua primeira propriedade para começar.')
            return redirect('dashboard')
    return render(request, 'core/auth.html', {'register': True})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')
