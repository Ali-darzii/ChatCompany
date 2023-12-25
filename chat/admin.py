from django.contrib import admin
from . import models


# admin.site.register(models.User)

@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["id", "username", "company"]
    list_filter = ["date_joined", "id"]
    fields = [("name", "username"), "avatar", "company", ("is_staff", "is_active", "is_superuser"), "description",
              ("date_joined", "last_login"), "groups", "password"]
    list_editable = ["username"]


@admin.register(models.Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "city"]
    list_filter = ["title"]
    fields = [("title", "city"), "url"]
    list_editable = ["city"]


@admin.register(models.Message)
class MessageAdmin(admin.ModelAdmin):
    # list_display = [""]
    list_filter = ["timestamp"]
    fields = ["user", "recipient", "body"]


@admin.register(models.Phone)
class MessageAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Groups)
class MessageAdmin(admin.ModelAdmin):
    pass


@admin.register(models.GroupMessage)
class MessageAdmin(admin.ModelAdmin):
    pass
