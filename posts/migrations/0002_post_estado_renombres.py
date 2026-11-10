from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("posts", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="post",
            old_name="title",
            new_name="titulo",
        ),
        migrations.RenameField(
            model_name="post",
            old_name="content",
            new_name="contenido",
        ),
        migrations.RenameField(
            model_name="post",
            old_name="author",
            new_name="autor",
        ),
        migrations.RenameField(
            model_name="post",
            old_name="created_at",
            new_name="fecha_creacion",
        ),
        migrations.AlterModelOptions(
            name="post",
            options={
                "ordering": ["-fecha_creacion"],
                "verbose_name": "Publicación",
                "verbose_name_plural": "Publicaciones",
            },
        ),
        migrations.AddField(
            model_name="post",
            name="estado",
            field=models.CharField(
                choices=[
                    ("borrador", "Borrador"),
                    ("publicado", "Publicado"),
                    ("archivado", "Archivado"),
                ],
                default="publicado",
                max_length=10,
                verbose_name="Estado",
            ),
        ),
        migrations.AlterField(
            model_name="post",
            name="estado",
            field=models.CharField(
                choices=[
                    ("borrador", "Borrador"),
                    ("publicado", "Publicado"),
                    ("archivado", "Archivado"),
                ],
                default="borrador",
                max_length=10,
                verbose_name="Estado",
            ),
        ),
    ]
