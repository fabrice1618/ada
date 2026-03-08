from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from core.models import (
    Utilisateur, Classe, Creneau,
    Devoir, Soumission, Quiz, Question, Tentative,
)


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    model = Utilisateur
    list_display = ('email', 'nom_complet', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'classes')
    search_fields = ('email', 'nom_complet')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations', {'fields': ('nom_complet', 'role', 'classes')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nom_complet', 'role', 'password1', 'password2', 'classes'),
        }),
    )
    filter_horizontal = ('classes', 'groups', 'user_permissions')


@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ('nom', 'annee')
    list_filter = ('annee',)
    search_fields = ('nom',)


@admin.register(Creneau)
class CreneauAdmin(admin.ModelAdmin):
    list_display = ('classe', 'type_ressource', 'ressource_id', 'chemin_page', 'ouverture', 'fermeture')
    list_filter = ('type_ressource', 'classe')
    search_fields = ('chemin_page',)


@admin.register(Devoir)
class DevoirAdmin(admin.ModelAdmin):
    list_display = ('titre', 'classe', 'date_limite', 'cree_par')
    list_filter = ('classe', 'cree_par')


@admin.register(Soumission)
class SoumissionAdmin(admin.ModelAdmin):
    list_display = ('devoir', 'etudiant', 'type', 'date_soumission')
    list_filter = ('type', 'devoir')
    search_fields = ('etudiant__email', 'etudiant__nom_complet')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('titre', 'classe', 'duree_max_minutes', 'tentative_unique', 'cree_par')
    list_filter = ('classe', 'tentative_unique')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'enonce', 'points')
    list_filter = ('quiz',)


@admin.register(Tentative)
class TentativeAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'etudiant', 'score', 'debut', 'fin')
    list_filter = ('quiz',)
    search_fields = ('etudiant__email', 'etudiant__nom_complet')
