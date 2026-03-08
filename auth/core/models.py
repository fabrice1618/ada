from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


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


class Devoir(models.Model):
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='devoirs')
    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    date_limite = models.DateTimeField()
    cree_par = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='devoirs_crees')

    class Meta:
        db_table = 'devoirs'

    def __str__(self):
        return self.titre


class Soumission(models.Model):
    TYPE_CHOICES = [
        ('fichier', 'Fichier'),
        ('github', 'GitHub'),
    ]

    devoir = models.ForeignKey(Devoir, on_delete=models.CASCADE, related_name='soumissions')
    etudiant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='soumissions')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    chemin_fichier = models.CharField(max_length=500, null=True, blank=True)
    lien_github = models.URLField(null=True, blank=True)
    date_soumission = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'soumissions'

    def __str__(self):
        return f"{self.etudiant} - {self.devoir}"


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
