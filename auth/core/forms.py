import re

from django import forms

from core.models import TYPE_RENDU_CHOICES, Classe, Devoir

LIEN_GITHUB = re.compile(r'https://github\.com/[A-Za-z0-9-]+/[A-Za-z0-9._-]+(/[^\s]*)?')


class FormulaireConnexion(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Adresse email',
            'autofocus': True,
        })
    )
    mot_de_passe = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe',
        })
    )


class FormulaireDevoir(forms.Form):
    classe = forms.ModelChoiceField(
        queryset=Classe.objects.order_by('-annee', 'nom'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Classe',
    )
    titre = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Titre',
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Description',
    )
    date_limite = forms.DateTimeField(
        localize=False,
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S'],
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'type': 'datetime-local', 'class': 'form-control'},
        ),
        label='Date limite',
    )
    type_rendu = forms.ChoiceField(
        required=False,
        choices=TYPE_RENDU_CHOICES,
        initial='fichier',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Type de rendu',
    )
    mode = forms.ChoiceField(
        required=False,
        choices=Devoir.MODE_CHOICES,
        initial='individuel',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Rendu',
    )
    taille_groupe_max = forms.IntegerField(
        required=False,
        min_value=2,
        max_value=20,
        initial=3,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Taille maximale des groupes',
        help_text='Pour un rendu en groupe.',
    )

    def __init__(self, *args, avec_classe=True, verrouille=False, taille_min=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.taille_min = taille_min
        if not avec_classe:
            self.fields.pop('classe')
        if verrouille:
            # Des rendus existent : type et mode restent ceux de la création.
            for nom in ('type_rendu', 'mode'):
                self.fields[nom].disabled = True
                self.fields[nom].help_text = 'Verrouillé : des rendus ont été déposés.'

    def clean_type_rendu(self):
        return self.cleaned_data['type_rendu'] or 'fichier'

    def clean_mode(self):
        return self.cleaned_data['mode'] or 'individuel'

    def clean(self):
        donnees = super().clean()
        if donnees.get('mode') == 'groupe':
            taille = donnees.get('taille_groupe_max')
            if not taille:
                self.add_error('taille_groupe_max', 'Indiquez la taille maximale des groupes.')
            elif self.taille_min and taille < self.taille_min:
                self.add_error(
                    'taille_groupe_max',
                    f'Un groupe compte déjà {self.taille_min} membres.',
                )
        else:
            donnees['taille_groupe_max'] = None
        return donnees


class FormulaireLienGithub(forms.Form):
    lien = forms.URLField(
        max_length=500,
        assume_scheme='https',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://github.com/compte/depot',
        }),
        label='Lien du dépôt GitHub',
    )

    def clean_lien(self):
        lien = self.cleaned_data['lien'].strip()
        if not LIEN_GITHUB.fullmatch(lien):
            raise forms.ValidationError(
                'Indiquez un dépôt GitHub : https://github.com/compte/depot'
            )
        return lien


class FormulaireGroupe(forms.Form):
    nom = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du groupe'}),
        label='Nom du groupe',
    )

    def clean_nom(self):
        nom = ' '.join(self.cleaned_data['nom'].split())
        if not nom:
            raise forms.ValidationError('Indiquez un nom.')
        return nom
