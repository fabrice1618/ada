from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class UtilisateurManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(email, password, **extra_fields)


class Classe(models.Model):
    nom = models.CharField(max_length=100)
    annee = models.CharField(max_length=20)
    debut_autorisation = models.DateField(null=True, blank=True, verbose_name="Début autorisation login")
    fin_autorisation = models.DateField(null=True, blank=True, verbose_name="Fin autorisation login")

    class Meta:
        db_table = 'core_classe'

    def __str__(self):
        return f"{self.nom} ({self.annee})"


class Utilisateur(AbstractUser):
    ROLE_CHOICES = [
        ('etudiant', 'Étudiant'),
        ('enseignant', 'Enseignant'),
        ('admin', 'Administrateur'),
    ]

    username = None
    email = models.EmailField(unique=True)
    nom_complet = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='etudiant')
    classes = models.ManyToManyField(Classe, blank=True, related_name='utilisateurs')

    objects = UtilisateurManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom_complet']

    class Meta:
        db_table = 'core_utilisateur'

    def __str__(self):
        return self.nom_complet


class Creneau(models.Model):
    TYPE_CHOICES = [
        ('quiz', 'Quiz'),
        ('devoir', 'Devoir'),
        ('page', 'Page'),
    ]

    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='creneaux')
    type_ressource = models.CharField(max_length=20, choices=TYPE_CHOICES)
    ressource_id = models.IntegerField(null=True, blank=True)
    chemin_page = models.CharField(max_length=500, null=True, blank=True)
    ouverture = models.DateTimeField()
    fermeture = models.DateTimeField()

    class Meta:
        db_table = 'core_creneau'

    def __str__(self):
        return f"{self.type_ressource} - {self.classe} ({self.ouverture} → {self.fermeture})"


TYPE_RENDU_CHOICES = [
    ('fichier', 'Un fichier'),
    ('fichiers', 'Plusieurs fichiers'),
    ('github', 'Lien GitHub'),
]


class Devoir(models.Model):
    MODE_CHOICES = [
        ('individuel', 'Individuel'),
        ('groupe', 'En groupe'),
    ]

    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='devoirs')
    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    date_limite = models.DateTimeField()
    cree_par = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='devoirs_crees')
    type_rendu = models.CharField(max_length=20, choices=TYPE_RENDU_CHOICES, default='fichier')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='individuel')
    taille_groupe_max = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'devoirs'

    def __str__(self):
        return self.titre

    def est_ouvert(self):
        return timezone.now() <= self.date_limite

    def en_groupe(self):
        return self.mode == 'groupe'


class Groupe(models.Model):
    devoir = models.ForeignKey(Devoir, on_delete=models.CASCADE, related_name='groupes')
    nom = models.CharField(max_length=100)
    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, related_name='groupes_crees',
    )
    date_creation = models.DateTimeField(default=timezone.now)
    membres = models.ManyToManyField(
        Utilisateur, through='MembreGroupe', through_fields=('groupe', 'etudiant'),
        related_name='groupes',
    )

    class Meta:
        db_table = 'groupes'
        constraints = [
            models.UniqueConstraint(fields=('devoir', 'nom'), name='groupe_nom_unique'),
        ]

    def __str__(self):
        return self.nom


class MembreGroupe(models.Model):
    # devoir est recopié du groupe : la contrainte d'unicité garantit
    # qu'un étudiant n'appartient qu'à un groupe par devoir.
    groupe = models.ForeignKey(Groupe, on_delete=models.CASCADE, related_name='adhesions')
    devoir = models.ForeignKey(Devoir, on_delete=models.CASCADE, related_name='adhesions')
    etudiant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='adhesions')
    date_adhesion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'groupes_membres'
        constraints = [
            models.UniqueConstraint(fields=('devoir', 'etudiant'), name='un_groupe_par_devoir'),
        ]


class Soumission(models.Model):
    devoir = models.ForeignKey(Devoir, on_delete=models.CASCADE, related_name='soumissions')
    etudiant = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, null=True, blank=True, related_name='soumissions',
    )
    groupe = models.ForeignKey(
        Groupe, on_delete=models.CASCADE, null=True, blank=True, related_name='soumissions',
    )
    deposee_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='depots',
    )
    type = models.CharField(max_length=20, choices=TYPE_RENDU_CHOICES)
    lien_github = models.URLField(max_length=500, null=True, blank=True)
    date_soumission = models.DateTimeField()

    class Meta:
        db_table = 'soumissions'
        constraints = [
            models.UniqueConstraint(
                fields=('devoir', 'etudiant'),
                name='soumission_une_par_etudiant',
            ),
            models.UniqueConstraint(
                fields=('devoir', 'groupe'),
                name='soumission_une_par_groupe',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(etudiant__isnull=False, groupe__isnull=True)
                    | models.Q(etudiant__isnull=True, groupe__isnull=False)
                ),
                name='soumission_etudiant_ou_groupe',
            ),
        ]

    def __str__(self):
        return f"{self.etudiant or self.groupe} - {self.devoir}"


class FichierRendu(models.Model):
    soumission = models.ForeignKey(Soumission, on_delete=models.CASCADE, related_name='fichiers')
    chemin = models.CharField(max_length=500)
    nom_original = models.CharField(max_length=255)
    taille = models.PositiveBigIntegerField(default=0)
    date_depot = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'soumissions_fichiers'
        ordering = ('nom_original', 'id')

    def __str__(self):
        return self.nom_original


class Quiz(models.Model):
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='quiz')
    titre = models.CharField(max_length=255)
    duree_max_minutes = models.IntegerField()
    tentative_unique = models.BooleanField(default=True)
    cree_par = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='quiz_crees')

    class Meta:
        db_table = 'quiz'

    def __str__(self):
        return self.titre


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    enonce = models.TextField()
    choix = models.JSONField()
    reponse_correcte = models.CharField(max_length=500)
    points = models.IntegerField(default=1)

    class Meta:
        db_table = 'questions'

    def __str__(self):
        return f"Q{self.id} - {self.quiz.titre}"


class Tentative(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='tentatives')
    etudiant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='tentatives')
    reponses = models.JSONField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
    debut = models.DateTimeField(auto_now_add=True)
    fin = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tentatives'

    def __str__(self):
        return f"{self.etudiant} - {self.quiz} ({self.score})"
