# views.py
from django.shortcuts import render, HttpResponse, get_object_or_404, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.contrib import messages
from .forms import FormAluno, FormCadastro, FormLogin, FormCurso, FormTurma
from .models import AAluno, Cadastro, ACurso, ATurma, Login, Aviso
from django.http import JsonResponse
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test

@login_required
def homepage(request):
    if request.method == "POST":
        form = FormLogin(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('inicio')
            else:
                form.add_error(None, "Nome de usuário ou senha inválidos.")
    else:
        form = FormLogin()
    return render(request, 'homepage.html', {'form': form})

def inicio(request):
    return render(request, 'telainicial.html')

@login_required
def cadastro(request):
    context = {}
    is_coordenador = request.user.groups.filter(name='Coordenador').exists()
    if request.method == "POST":
        form = FormCadastro(request.POST)
        if form.is_valid():
            var_nome = form.cleaned_data['nome']
            var_email = form.cleaned_data['email']
            var_profissao = form.cleaned_data['profissao']
            var_criar_senha = form.cleaned_data['criarsenha']
            try:
                if User.objects.filter(email=var_email).exists():
                    context["error"] = "Este email já está cadastrado!"
                else:
                    # Criação do usuário no sistema de autenticação
                    novo_usuario = User.objects.create_user(
                        username=var_nome,
                        email=var_email,
                        password=var_criar_senha
                    )

                    # Associa o usuário a um grupo com base na profissão
                    if var_profissao.lower() == 'coordenador':
                        coordenador_group = Group.objects.get(name='Coordenador')
                        novo_usuario.groups.add(coordenador_group)
                    elif var_profissao.lower() == 'colaborador':
                        colaborador_group = Group.objects.get(name='Colaborador')
                        novo_usuario.groups.add(colaborador_group)

                    novo_usuario.save()  # Salva o usuário com o grupo associado

                    # Salva no modelo `Cadastro` se for necessário
                    novo_cadastro = Cadastro(
                        nome=var_nome,
                        email=var_email,
                        profissao=var_profissao,
                        criarsenha=var_criar_senha
                    )
                    novo_cadastro.save()

                    context["success"] = "Cadastro realizado com sucesso!"
                    form = FormCadastro()  # Reseta o formulário
            except Group.DoesNotExist:
                context["error"] = "Erro: O grupo associado não existe. Verifique sua configuração no Django Admin."
            except Exception as e:
                context["error"] = f"Ocorreu um erro: {str(e)}"
    else:
        form = FormCadastro()

    context["form"] = form
    context["is_coordenador"] = is_coordenador
    return render(request, 'cadastro.html', context)

@login_required
def carometro(request):
    cursos = ACurso.objects.all()

    is_coordenador = request.user.groups.filter(name='Coordenador').exists()

    context = {'cursos': cursos}
    context["is_coordenador"] = is_coordenador
    return render(request, 'carometro.html', context)

@login_required
def carometro2(request, curso_id):
    turmas = ATurma.objects.filter(curso=curso_id)

    is_coordenador = request.user.groups.filter(name='Coordenador').exists()

    print("Turmas encontradas:", turmas)
    context = {'turmas': turmas}
    context["is_coordenador"] = is_coordenador
    return render(request, 'carometro2.html', context)

@login_required
def carometro3(request, turma_id):
    alunos = AAluno.objects.filter(turma=turma_id)

    is_coordenador = request.user.groups.filter(name='Coordenador').exists()

    print("Alunos encontrados:", alunos)
    context = {'alunos': alunos}
    context["is_coordenador"] = is_coordenador
    return render(request, 'carometro3.html', context)

def informacoescar(request, aluno_id):
    alunos = AAluno.objects.filter(id=aluno_id)
    context = {'alunos': alunos}
    return render(request, 'informacoescar.html', context)

def adicionarcurso(request):
    context = {}
    if request.method == "POST":
        form = FormCurso(request.POST)
        if form.is_valid():
            var_curso = form.cleaned_data['curso']
            try:
                if ACurso.objects.filter(curso=var_curso).exists():
                    context["error"] = "Curso já adicionado!"
                else:
                    user_curso = ACurso(curso=var_curso)
                    user_curso.save()
                    context["success"] = "Curso adicionado com sucesso!"
                    form = FormCurso()  
                    return redirect('carometro')
            except Exception as e:
                context["error"] = f"Ocorreu um erro: {str(e)}"
        context["form"] = form 
    else:
        form = FormCurso()
    context["form"] = form
    return render(request, 'adicionarcurso.html', context)


def editarcurso(request, curso_id):
    curso = get_object_or_404(ACurso, id=curso_id)

    if request.method == 'POST':
        form = FormCurso(request.POST, instance=curso)
        
        if form.is_valid():
            form.save()
            messages.success(request, "Curso editado com sucesso!")  
            return redirect('carometro')  
            
    else:
       form = FormCurso(instance=curso)

    return render(request, 'editarcurso.html', {'form': form, 'curso': curso})

def excluircurso(request, curso_id):
    curso = get_object_or_404(ACurso, id=curso_id)

    if request.method == 'POST':
        curso.delete()
        return JsonResponse({'status': 'sucesso', 'mensagem': 'Curso excluído com sucesso!'})
    return JsonResponse({'status': 'erro', 'mensagem': 'Método não permitido'}, status=405)

def adicionarturma(request):
    context = {}

    if request.method == "POST":
        form = FormTurma(request.POST)
        if form.is_valid():
            var_turma = form.cleaned_data['turma']
            var_periodo = form.cleaned_data['periodo']
            var_curso = form.cleaned_data['curso']  # Captura o curso selecionado
            try:
                if ATurma.objects.filter(turma=var_turma, curso=var_curso).exists():
                    context["error"] = "Essa turma já foi adicionada para o curso selecionado!"
                else:
                    user_turma = ATurma(turma=var_turma, periodo=var_periodo, curso=var_curso)
                    user_turma.save()
                    context["success"] = "Turma adicionada com sucesso!"
                    return redirect('carometro')
            except Exception as e:
                context["error"] = f"Ocorreu um erro: {str(e)}"
        context["form"] = form
    else:
        form = FormTurma()
        context["form"] = form
    return render(request, 'adicionarturma.html', context)

def editarturma(request, turma_id):
    turma = get_object_or_404(ATurma, id=turma_id)

    if request.method == 'POST':
        form = FormTurma(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Turma editado com sucesso!")  # Mensagem de sucesso
            return redirect('carometro')  # Redireciona para a página de cursos após salvar
    else:
        form = FormTurma()

    return render(request, 'editarturma.html', {'form': form, 'turma': turma})

def excluirturma(request, turma_id):
    turma = get_object_or_404(ATurma, id=turma_id)
    if request.method == 'POST':
        turma.delete()
        return JsonResponse({'status': 'sucesso', 'mensagem': 'Turma excluída com sucesso!'})
    return JsonResponse({'status': 'erro', 'mensagem': 'Método não permitido'}, status=405)

def adicionaraluno(request):
    context = {}

    if request.method == "POST":
        form = FormAluno(request.POST)
        if form.is_valid():
            var_nome = form.cleaned_data['nome']
            var_telefone = form.cleaned_data['telefone']
            var_nome_pai = form.cleaned_data['nome_pai']
            var_nome_mae = form.cleaned_data['nome_mae']
            var_turma = form.cleaned_data['turma']  # Captura o curso selecionado
            var_observacoes = form.cleaned_data.get('observacoes', '')
            try:
                if AAluno.objects.filter(nome=var_nome, turma=var_turma).exists():
                    context["error"] = "Aluno já adicionado na turma!"
                else:
                    user_aluno = AAluno(
                        nome=var_nome,
                        telefone=var_telefone,
                        nome_pai=var_nome_pai,
                        nome_mae=var_nome_mae,
                        turma=var_turma,
                        observacoes=var_observacoes
                    )
                    user_aluno.save()
                    context["success"] = "Aluno adicionado com sucesso!"
                    return redirect('carometro')
            except Exception as e:
                context["error"] = f"Ocorreu um erro: {str(e)}"
        context["form"] = form
    else:
        form = FormAluno()
        context["form"] = form
    return render(request, 'adicionaraluno.html', context)

def editaraluno(request, aluno_id):
    aluno = get_object_or_404(AAluno, id=aluno_id)

    if request.method == 'POST':
        form = FormAluno(request.POST, instance=aluno)
        if form.is_valid():
            form.save()
            messages.success(request, "Aluno editado com sucesso!")
            return redirect('carometro')
    else:
        form = FormAluno()

    return render(request, 'editaraluno.html', {'form': form, 'aluno': aluno})

def excluiraluno(request, aluno_id):
    aluno = get_object_or_404(ATurma, id=aluno_id)
    if request.method == 'POST':
        aluno.delete()
        return JsonResponse({'status': 'sucesso', 'mensagem': 'Turma excluída com sucesso!'})
    return JsonResponse({'status': 'erro', 'mensagem': 'Método não permitido'}, status=405)


from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Aviso
from django.views.decorators.csrf import csrf_exempt

from django.shortcuts import render, get_object_or_404, redirect
from .models import Aviso


def muralaviso(request):
    if request.method == 'POST':
        # Captura a mensagem do formulário e cria um novo aviso
        mensagem = request.POST.get('mensagem')
        if mensagem:
            aviso = Aviso.objects.create(mensagem=mensagem)
            return JsonResponse({'status': 'sucesso', 'mensagem': aviso.mensagem, 'data_criacao': aviso.data_criacao.strftime("%d/%m/%Y %H:%M")})
        
    # Busca todos os avisos para exibição
    avisos = Aviso.objects.all()  # Obtém todos os avisos

    # Renderiza o template, passando todos os avisos
    return render(request, 'muralaviso.html', {'avisos': avisos})

def editaraviso(request, aviso_id):
    aviso = get_object_or_404(Aviso, id=aviso_id)
    if request.method == 'POST':
        mensagem = request.POST.get('mensagem')
        aviso.mensagem = mensagem
        aviso.save()
        return redirect('muralaviso')
    return render(request, 'editaraviso.html', {'aviso': aviso})

def excluiraviso(request, aviso_id):
    aviso = get_object_or_404(Aviso, id=aviso_id)
    if request.method == 'POST':
        aviso.delete()
        return redirect('muralaviso')
    return render(request, 'excluiraviso.html', {'aviso': aviso})

def criar_aviso_ajax(request):
    if request.method == 'POST':
        mensagem = request.POST.get('mensagem', '')
        if mensagem:
            aviso = Aviso.objects.create(mensagem=mensagem)
            return JsonResponse({'status': 'sucesso', 'mensagem': aviso.mensagem}, status=201)
        else:
            return JsonResponse({'status': 'erro', 'mensagem': 'Mensagem vazia'}, status=400)
    return JsonResponse({'status': 'erro', 'mensagem': 'Método não permitido'}, status=405)