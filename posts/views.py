from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
)

from .forms import LoginForm, PostForm, RegisterForm, SearchForm
from .models import Post


class PostListView(ListView):
    """Listado público de publicaciones con búsqueda y paginación."""

    model = Post
    template_name = "posts/post_list.html"
    context_object_name = "posts"
    paginate_by = 6

    def get_queryset(self):
        queryset = Post.objects.select_related("autor").filter(
            estado=Post.Estado.PUBLICADO
        )
        self.search_form = SearchForm(self.request.GET or None)
        self.query = ""

        if self.search_form.is_valid():
            self.query = self.search_form.cleaned_data.get("q", "").strip()
            if self.query:
                queryset = queryset.filter(
                    Q(titulo__icontains=self.query)
                    | Q(contenido__icontains=self.query)
                )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = self.search_form
        context["query"] = self.query
        return context


class PostDetailView(DetailView):
    """Detalle de una publicación visible para el público o su autor/staff."""

    model = Post
    template_name = "posts/post_detail.html"
    context_object_name = "post"
    queryset = Post.objects.select_related("autor")

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_authenticated:
            if user.is_staff:
                return queryset
            return queryset.filter(
                Q(estado=Post.Estado.PUBLICADO) | Q(autor=user)
            )

        return queryset.filter(estado=Post.Estado.PUBLICADO)


class PostCreateView(LoginRequiredMixin, CreateView):
    """Creación de publicaciones para usuarios autenticados."""

    model = Post
    form_class = PostForm
    template_name = "posts/post_form.html"

    def form_valid(self, form):
        form.instance.autor = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "La publicación se creó correctamente.")
        return response


class AuthorOrStaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Permite editar o eliminar solo al autor o al personal del sitio."""

    def test_func(self):
        return self.get_object().can_be_edited_by(self.request.user)


class PostUpdateView(AuthorOrStaffRequiredMixin, UpdateView):
    """Edición de una publicación existente."""

    model = Post
    form_class = PostForm
    template_name = "posts/post_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "La publicación se actualizó correctamente.")
        return response


class PostDeleteView(AuthorOrStaffRequiredMixin, DeleteView):
    """Eliminación de una publicación con confirmación."""

    model = Post
    template_name = "posts/post_confirm_delete.html"
    context_object_name = "post"
    success_url = reverse_lazy("posts:post_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "La publicación se eliminó correctamente.")
        return response


class RegisterView(FormView):
    """Registro de nuevos usuarios."""

    template_name = "registration/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("posts:post_list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            "Tu cuenta se creó correctamente. Ya puedes iniciar sesión.",
        )
        return super().form_valid(form)


class CustomLoginView(auth_views.LoginView):
    """Login con mensaje de bienvenida."""

    template_name = "registration/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Bienvenido, {self.request.user.username}.")
        return response


class CustomLogoutView(auth_views.LogoutView):
    """Logout exclusivamente por POST."""

    next_page = reverse_lazy("posts:post_list")

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, "Has cerrado sesión correctamente.")
        return response
