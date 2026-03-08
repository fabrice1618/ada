from django import forms


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
