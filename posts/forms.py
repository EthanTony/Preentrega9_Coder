from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Post


class PostForm(forms.ModelForm):
    """Formulario para crear y editar publicaciones."""

    class Meta:
        model = Post
        fields = ("titulo", "contenido", "estado", "image")
        widgets = {
            "titulo": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Escribe un título descriptivo",
                    "autofocus": True,
                }
            ),
            "contenido": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 10,
                    "placeholder": "Comparte el contenido de tu publicación...",
                }
            ),
            "estado": forms.Select(attrs={"class": "form-select"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        labels = {
            "titulo": "Título",
            "contenido": "Contenido",
            "estado": "Estado",
            "image": "Imagen (opcional)",
        }


class SearchForm(forms.Form):
    """Búsqueda de publicaciones por título o contenido."""

    q = forms.CharField(
        required=False,
        label="Buscar",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "type": "search",
                "placeholder": "Buscar por título o contenido...",
                "aria-label": "Buscar publicaciones",
            }
        ),
    )


class LoginForm(AuthenticationForm):
    """Formulario de acceso con estilos de Bootstrap."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Nombre de usuario"
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "autofocus": True, "placeholder": "Tu usuario"}
        )
        self.fields["password"].label = "Contraseña"
        self.fields["password"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Tu contraseña"}
        )


class RegisterForm(UserCreationForm):
    """Registro de usuarios basado en UserCreationForm."""

    email = forms.EmailField(
        required=False,
        label="Correo electrónico (opcional)",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "correo@ejemplo.com"}
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Nombre de usuario"
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "autofocus": True, "placeholder": "Elige un usuario"}
        )
        self.fields["password1"].label = "Contraseña"
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Crea una contraseña segura"}
        )
        self.fields["password2"].label = "Confirmar contraseña"
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Repite la contraseña"}
        )
