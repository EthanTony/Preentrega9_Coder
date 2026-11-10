from django.conf import settings
from django.db import models
from django.urls import reverse


class Post(models.Model):
    """Publicación creada por un usuario del blog."""

    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador"
        PUBLICADO = "publicado", "Publicado"
        ARCHIVADO = "archivado", "Archivado"

    titulo = models.CharField(max_length=200, verbose_name="Título")
    contenido = models.TextField(verbose_name="Contenido")
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Autor",
    )
    image = models.ImageField(
        upload_to="posts/",
        blank=True,
        null=True,
        verbose_name="Imagen",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.BORRADOR,
        verbose_name="Estado",
    )

    class Meta:
        ordering = ["-fecha_creacion"]
        verbose_name = "Publicación"
        verbose_name_plural = "Publicaciones"

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse("posts:post_detail", kwargs={"pk": self.pk})

    def can_be_edited_by(self, user):
        """El autor y el personal del sitio pueden modificar la publicación."""
        return user.is_authenticated and (user.is_staff or user.pk == self.autor_id)
