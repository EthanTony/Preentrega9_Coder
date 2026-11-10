from django.contrib import admin

from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "autor",
        "estado",
        "has_image",
        "fecha_creacion",
        "updated_at",
    )
    list_filter = ("estado", "fecha_creacion", "autor")
    search_fields = ("titulo", "contenido", "autor__username")
    date_hierarchy = "fecha_creacion"
    readonly_fields = ("fecha_creacion", "updated_at")
    list_select_related = ("autor",)
    list_editable = ("estado",)

    @admin.display(boolean=True, description="Con imagen")
    def has_image(self, obj):
        return bool(obj.image)
