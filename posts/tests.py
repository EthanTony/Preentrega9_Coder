import os
import shutil
import tempfile

from django.contrib.auth.models import AnonymousUser, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Post


class PostModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.autor = User.objects.create_user(username="autor", password="ClaveSegura123!")
        cls.other_user = User.objects.create_user(username="otro", password="ClaveSegura123!")
        cls.staff_user = User.objects.create_user(
            username="staff", password="ClaveSegura123!", is_staff=True
        )
        cls.post = Post.objects.create(
            titulo="Primera publicación",
            contenido="Contenido de prueba",
            autor=cls.autor,
            estado=Post.Estado.PUBLICADO,
        )

    def test_str_returns_title(self):
        self.assertEqual(str(self.post), "Primera publicación")

    def test_get_absolute_url_uses_detail_route(self):
        self.assertEqual(
            self.post.get_absolute_url(),
            reverse("posts:post_detail", kwargs={"pk": self.post.pk}),
        )

    def test_post_without_image_is_allowed(self):
        self.assertFalse(bool(self.post.image))

    def test_author_can_edit(self):
        self.assertTrue(self.post.can_be_edited_by(self.autor))

    def test_staff_can_edit(self):
        self.assertTrue(self.post.can_be_edited_by(self.staff_user))

    def test_other_user_cannot_edit(self):
        self.assertFalse(self.post.can_be_edited_by(self.other_user))

    def test_anonymous_cannot_edit(self):
        self.assertFalse(self.post.can_be_edited_by(AnonymousUser()))

    def test_posts_are_ordered_newest_first(self):
        newer = Post.objects.create(
            titulo="Más reciente",
            contenido="Otra publicación",
            autor=self.autor,
            estado=Post.Estado.PUBLICADO,
        )
        self.assertEqual(Post.objects.first(), newer)


class PostViewTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user(username="autor", password="ClaveSegura123!")
        self.other_user = User.objects.create_user(username="otro", password="ClaveSegura123!")
        self.staff_user = User.objects.create_user(
            username="staff", password="ClaveSegura123!", is_staff=True
        )
        self.post = Post.objects.create(
            titulo="Django para principiantes",
            contenido="Una guía introductoria sobre Django y sus vistas.",
            autor=self.autor,
            estado=Post.Estado.PUBLICADO,
        )

    def test_list_view_is_public(self):
        response = self.client.get(reverse("posts:post_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.titulo)
        self.assertContains(response, self.autor.username)

    def test_detail_view_is_public(self):
        response = self.client.get(self.post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.titulo)
        self.assertContains(response, self.post.contenido)

    def test_search_by_title(self):
        other = Post.objects.create(
            titulo="Python avanzado",
            contenido="Contenido diferente.",
            autor=self.autor,
            estado=Post.Estado.PUBLICADO,
        )
        response = self.client.get(reverse("posts:post_list"), {"q": "django"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.titulo)
        self.assertNotContains(response, other.titulo)
        self.assertEqual(response.context["query"], "django")

    def test_search_by_content(self):
        response = self.client.get(reverse("posts:post_list"), {"q": "introductoria"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.titulo)

    def test_search_without_results_shows_message(self):
        response = self.client.get(reverse("posts:post_list"), {"q": "inexistente"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No se encontraron publicaciones")
        self.assertContains(response, "inexistente")

    def test_list_renders_post_without_image(self):
        response = self.client.get(reverse("posts:post_list"))
        self.assertContains(response, "Sin imagen")

    def test_anonymous_cannot_create(self):
        response = self.client.get(reverse("posts:post_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.assertIn("next=", response.url)

    def test_create_form_renders_for_authenticated_user(self):
        self.client.login(username="autor", password="ClaveSegura123!")
        response = self.client.get(reverse("posts:post_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nueva publicación")
        self.assertContains(response, 'enctype="multipart/form-data"')

    def test_edit_form_renders_for_author(self):
        self.client.login(username="autor", password="ClaveSegura123!")
        response = self.client.get(
            reverse("posts:post_update", kwargs={"pk": self.post.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editar publicación")

    def test_authenticated_user_can_create(self):
        self.client.login(username="autor", password="ClaveSegura123!")
        response = self.client.post(
            reverse("posts:post_create"),
            {
                "titulo": "Nueva publicación",
                "contenido": "Contenido nuevo",
                "estado": Post.Estado.PUBLICADO,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        created = Post.objects.get(titulo="Nueva publicación")
        self.assertEqual(created.autor, self.autor)
        self.assertRedirects(response, created.get_absolute_url())
        self.assertContains(response, "La publicación se creó correctamente.")

    def test_author_can_edit(self):
        self.client.login(username="autor", password="ClaveSegura123!")
        response = self.client.post(
            reverse("posts:post_update", kwargs={"pk": self.post.pk}),
            {
                "titulo": "Título actualizado",
                "contenido": self.post.contenido,
                "estado": self.post.estado,
            },
            follow=True,
        )
        self.assertRedirects(response, self.post.get_absolute_url())
        self.post.refresh_from_db()
        self.assertEqual(self.post.titulo, "Título actualizado")

    def test_anonymous_cannot_edit(self):
        response = self.client.get(
            reverse("posts:post_update", kwargs={"pk": self.post.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_non_author_cannot_edit(self):
        self.client.login(username="otro", password="ClaveSegura123!")
        response = self.client.post(
            reverse("posts:post_update", kwargs={"pk": self.post.pk}),
            {
                "titulo": "Intento no autorizado",
                "contenido": "Contenido",
                "estado": self.post.estado,
            },
        )
        self.assertEqual(response.status_code, 403)
        self.post.refresh_from_db()
        self.assertEqual(self.post.titulo, "Django para principiantes")

    def test_staff_can_edit_other_user_post(self):
        self.client.login(username="staff", password="ClaveSegura123!")
        response = self.client.post(
            reverse("posts:post_update", kwargs={"pk": self.post.pk}),
            {
                "titulo": "Editado por staff",
                "contenido": self.post.contenido,
                "estado": self.post.estado,
            },
            follow=True,
        )
        self.assertRedirects(response, self.post.get_absolute_url())
        self.post.refresh_from_db()
        self.assertEqual(self.post.titulo, "Editado por staff")

    def test_author_can_delete(self):
        self.client.login(username="autor", password="ClaveSegura123!")
        response = self.client.get(
            reverse("posts:post_delete", kwargs={"pk": self.post.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "¿Seguro que quieres eliminar")

        response = self.client.post(
            reverse("posts:post_delete", kwargs={"pk": self.post.pk}),
            follow=True,
        )
        self.assertRedirects(response, reverse("posts:post_list"))
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())
        self.assertContains(response, "La publicación se eliminó correctamente.")

    def test_non_author_cannot_delete(self):
        self.client.login(username="otro", password="ClaveSegura123!")
        response = self.client.post(
            reverse("posts:post_delete", kwargs={"pk": self.post.pk})
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_staff_can_delete_other_user_post(self):
        self.client.login(username="staff", password="ClaveSegura123!")
        response = self.client.post(
            reverse("posts:post_delete", kwargs={"pk": self.post.pk})
        )
        self.assertRedirects(response, reverse("posts:post_list"))
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())


class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="usuario", password="ClaveSegura123!"
        )

    def test_register_view_is_public(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Crear cuenta")

    def test_register_creates_user(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "nuevo_usuario",
                "email": "nuevo@example.com",
                "password1": "ClaveMuySegura2026!",
                "password2": "ClaveMuySegura2026!",
            },
            follow=True,
        )
        self.assertRedirects(response, reverse("login"))
        self.assertTrue(User.objects.filter(username="nuevo_usuario").exists())
        self.assertContains(response, "Tu cuenta se creó correctamente")

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "nuevo_usuario",
                "password1": "ClaveMuySegura2026!",
                "password2": "OtraClaveDistinta2026!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="nuevo_usuario").exists())

    def test_login_with_valid_credentials(self):
        response = self.client.post(
            reverse("login"),
            {"username": "usuario", "password": "ClaveSegura123!"},
            follow=True,
        )
        self.assertRedirects(response, reverse("posts:post_list"))
        self.assertIn("_auth_user_id", self.client.session)
        self.assertContains(response, "Bienvenido, usuario.")

    def test_logout_via_post(self):
        self.client.login(username="usuario", password="ClaveSegura123!")
        response = self.client.post(reverse("logout"), follow=True)
        self.assertRedirects(response, reverse("posts:post_list"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(response, "Has cerrado sesión correctamente.")

    def test_logout_get_is_not_allowed(self):
        self.client.login(username="usuario", password="ClaveSegura123!")
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)

    def test_navigation_differs_for_anonymous_and_authenticated(self):
        response = self.client.get(reverse("posts:post_list"))
        self.assertContains(response, "Iniciar sesión")
        self.assertContains(response, "Registrarse")
        self.assertNotContains(response, "Cerrar sesión")

        self.client.login(username="usuario", password="ClaveSegura123!")
        response = self.client.get(reverse("posts:post_list"))
        self.assertContains(response, "Nueva publicación")
        self.assertContains(response, "Cerrar sesión")
        self.assertNotContains(response, "Registrarse")


class PostEstadoTests(TestCase):
    def setUp(self):
        self.autor = User.objects.create_user(
            username="autor", password="ClaveSegura123!"
        )
        self.otro = User.objects.create_user(
            username="otro", password="ClaveSegura123!"
        )
        self.staff = User.objects.create_user(
            username="staff", password="ClaveSegura123!", is_staff=True
        )
        self.publicado = Post.objects.create(
            titulo="Publicación visible",
            contenido="Contenido visible para todo el público.",
            autor=self.autor,
            estado=Post.Estado.PUBLICADO,
        )
        self.borrador = Post.objects.create(
            titulo="Borrador privado",
            contenido="Contenido en borrador.",
            autor=self.autor,
            estado=Post.Estado.BORRADOR,
        )
        self.archivado = Post.objects.create(
            titulo="Publicación archivada",
            contenido="Contenido archivado.",
            autor=self.autor,
            estado=Post.Estado.ARCHIVADO,
        )

    def test_estado_por_defecto_es_borrador(self):
        post = Post.objects.create(
            titulo="Sin estado explícito",
            contenido="Contenido.",
            autor=self.autor,
        )
        self.assertEqual(post.estado, Post.Estado.BORRADOR)

    def test_get_estado_display(self):
        self.assertEqual(self.publicado.get_estado_display(), "Publicado")
        self.assertEqual(self.borrador.get_estado_display(), "Borrador")
        self.assertEqual(self.archivado.get_estado_display(), "Archivado")

    def test_listado_solo_muestra_publicadas(self):
        response = self.client.get(reverse("posts:post_list"))
        self.assertContains(response, self.publicado.titulo)
        self.assertNotContains(response, self.borrador.titulo)
        self.assertNotContains(response, self.archivado.titulo)

    def test_busqueda_no_incluye_borradores(self):
        response = self.client.get(reverse("posts:post_list"), {"q": "Borrador"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.borrador.titulo)

    def test_detalle_borrador_no_visible_para_anonimos(self):
        response = self.client.get(self.borrador.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_detalle_borrador_visible_para_autor(self):
        self.client.login(username="autor", password="ClaveSegura123!")
        response = self.client.get(self.borrador.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.borrador.titulo)

    def test_detalle_borrador_visible_para_staff(self):
        self.client.login(username="staff", password="ClaveSegura123!")
        response = self.client.get(self.borrador.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_detalle_archivado_no_visible_para_otros_usuarios(self):
        self.client.login(username="otro", password="ClaveSegura123!")
        response = self.client.get(self.archivado.get_absolute_url())
        self.assertEqual(response.status_code, 404)


class PostImageTests(TestCase):
    # GIF transparente de 1x1 píxel para validar ImageField sin depender de archivos externos.
    TINY_GIF = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04"
        b"\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D"
        b"\x01\x00;"
    )

    @classmethod
    def setUpClass(cls):
        cls._media_dir = tempfile.mkdtemp()
        cls._override = override_settings(MEDIA_ROOT=cls._media_dir)
        cls._override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._override.disable()
        shutil.rmtree(cls._media_dir, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(
            username="con_imagen", password="ClaveSegura123!"
        )
        self.client.login(username="con_imagen", password="ClaveSegura123!")

    def test_create_post_with_image(self):
        upload = SimpleUploadedFile(
            "imagen.gif", self.TINY_GIF, content_type="image/gif"
        )
        response = self.client.post(
            reverse("posts:post_create"),
            {
                "titulo": "Con imagen",
                "contenido": "Publicación con imagen.",
                "estado": Post.Estado.PUBLICADO,
                "image": upload,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        post = Post.objects.get(titulo="Con imagen")
        self.assertTrue(post.image)
        self.assertTrue(os.path.exists(post.image.path))
        self.assertContains(response, post.image.url)

    def test_create_post_without_image(self):
        response = self.client.post(
            reverse("posts:post_create"),
            {
                "titulo": "Sin imagen",
                "contenido": "Publicación sin imagen.",
                "estado": Post.Estado.PUBLICADO,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        post = Post.objects.get(titulo="Sin imagen")
        self.assertFalse(bool(post.image))
        self.assertContains(response, "Sin imagen")
