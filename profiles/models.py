# ============================================================
# SPORTLINK — Modèles des profils joueurs et recruteurs
# Ce fichier définit toutes les tables liées aux profils
# dans la base de données
# ============================================================

from django.db import models
from django.utils.text import slugify  # Pour générer les URLs propres
from django.core.exceptions import ValidationError
from datetime import date
from accounts.models import User


# ── SPORT ────────────────────────────────────────────────────
class Sport(models.Model):
    """
    Table des disciplines sportives disponibles sur la plateforme.
    Pour le MVP : seul le Football est actif (is_active=True).
    Les autres sports apparaissent grisés dans l'app Flutter.
    """

    nom_sport = models.CharField(
        max_length=50,
        unique=True,
        # unique=True : on ne peut pas avoir deux fois "Football"
    )

    is_active = models.BooleanField(
        default=False,
        # False par défaut — on active manuellement depuis l'admin Django
        # Pour le MVP : Football = True, tout le reste = False
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Sport'
        verbose_name_plural = 'Sports'
        ordering            = ['nom_sport']  # Tri alphabétique dans l'admin

    def __str__(self):
        return self.nom_sport


# ── POSITION ─────────────────────────────────────────────────
class Position(models.Model):
    """
    Table des postes de jeu, organisés par sport et par catégorie.
    Exemple pour le Football :
        - Catégorie "Défense" → postes : Axial, Latéral Droit, Latéral Gauche
        - Catégorie "Milieu"  → postes : Défensif, Box-to-box, Offensif
        - Catégorie "Attaque" → postes : Ailier Droit, Ailier Gauche, Avant-centre
        - Catégorie "Gardien" → postes : Gardien de but
    """

    sport = models.ForeignKey(
        Sport,
        on_delete=models.CASCADE,
        related_name='positions',
        # Si on supprime le sport Football, tous ses postes sont supprimés aussi
    )

    categorie = models.CharField(
        max_length=50,
        # Ex : "Défense", "Milieu", "Attaque", "Gardien"
    )

    nom_poste = models.CharField(
        max_length=50,
        # Ex : "Ailier Droit", "Avant-centre", "Axial"
    )

    code_poste = models.CharField(
        max_length=10,
        unique=True,
        null=True,
        blank=True,
        # Abréviation internationale : DC, LB, RB, CM, CAM, ST, GK...
        # Optionnel mais utile pour les filtres rapides
    )

    class Meta:
        verbose_name        = 'Position'
        verbose_name_plural = 'Positions'
        # Un même poste ne peut pas exister deux fois dans la même catégorie
        unique_together     = ('sport', 'categorie', 'nom_poste')
        ordering            = ['categorie', 'nom_poste']

    def __str__(self):
        return f'{self.sport.nom_sport} — {self.categorie} — {self.nom_poste}'


# ── PROFIL JOUEUR ────────────────────────────────────────────
class Profile(models.Model):
    """
    Table centrale du système. Contient toutes les informations
    sportives et personnelles d'un joueur.
    Chaque utilisateur de type 'talent' a exactement un profil.
    """

    # ── Choix pour les champs ENUM ────────────────────────────

    PIED_CHOICES = [
        ('droit',       'Droit'),
        ('gauche',      'Gauche'),
        ('ambidextre',  'Ambidextre'),
    ]

    CLUB_STATUS_CHOICES = [
        ('club_officiel',      'Club Officiel'),
        ('centre_formation',   'Centre de Formation'),
        ('groupe_travail',     'Groupe de Travail'),
        # Groupe de travail = joueurs sans structure officielle
        # qui s'entraînent ensemble de manière informelle
    ]

    TUTEUR_LIEN_CHOICES = [
        ('pere',          'Père'),
        ('mere',          'Mère'),
        ('tuteur_legal',  'Tuteur Légal'),
        ('autre',         'Autre Responsable'),
    ]

    # ── Relations ─────────────────────────────────────────────

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        # OneToOneField : un utilisateur = un seul profil
        # Si l'utilisateur est supprimé, son profil l'est aussi
    )

    sport = models.ForeignKey(
        Sport,
        on_delete=models.SET_NULL,
        null=True,
        related_name='profiles',
        # Si un sport est supprimé, le profil reste mais sport devient null
    )

    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profiles_principal',
        # Poste principal du joueur — obligatoire mais peut devenir null
        # si la position est supprimée
    )

    position_secondaire = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profiles_secondaire',
        # Poste secondaire — totalement optionnel
        # Ex : un ailier qui peut aussi jouer milieu offensif
    )

    # ── Informations personnelles ──────────────────────────────

    nom_complet = models.CharField(
        max_length=100,
        # Prénom + Nom du joueur
    )

    date_naissance = models.DateField(
        # Utilisé pour calculer l'âge et la catégorie (U13, U15, U17, etc.)
    )

    ville = models.CharField(
        max_length=100,
        # Ville de résidence au Bénin
    )

    # ── Informations sportives ─────────────────────────────────

    pied_fort = models.CharField(
        max_length=15,
        choices=PIED_CHOICES,
        default='droit',
    )

    taille = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        # En centimètres — Ex : 178.50
        # Optionnel : le joueur peut ne pas le renseigner
    )

    poids = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        # En kilogrammes — Ex : 72.00
    )

    statut_club = models.CharField(
        max_length=25,
        choices=CLUB_STATUS_CHOICES,
        default='groupe_travail',
        # Obligatoire : le recruteur doit savoir si le joueur
        # est dans un club, un centre ou un groupe informel
    )

    nom_club = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        # Nom du club, centre de formation ou groupe de travail
        # Optionnel si statut_club = 'groupe_travail'
    )

    # ── Contact ───────────────────────────────────────────────

    whatsapp = models.CharField(
        max_length=20,
        # Format international — Ex : +22997123456
        # Pour les mineurs : c'est le numéro du tuteur qui est stocké ici
    )

    # ── Médias ────────────────────────────────────────────────

    photo_profil = models.ImageField(
        upload_to='photos/profils/',
        null=True,
        blank=True,
        # Uploadée sur Cloudinary automatiquement grâce à la config settings.py
    )

    identity_doc = models.FileField(
        upload_to='documents/identite/',
        null=True,
        blank=True,
        # Pièce d'identité — stockée dans un dossier privé
        # Visible uniquement par l'administrateur dans le panneau admin
    )

    # ── Statuts et badges ─────────────────────────────────────

    is_verified = models.BooleanField(
        default=False,
        # True = badge "Vérifié" affiché sur le profil public
        # Activé manuellement par l'admin après vérification de la pièce d'identité
    )

    is_published = models.BooleanField(
        default=False,
        # False = profil en brouillon, non visible par les recruteurs
        # True = profil public, visible dans le feed et la recherche
    )

    # ── Gestion des mineurs ───────────────────────────────────

    is_minor = models.BooleanField(
        default=False,
        # True automatiquement si age < 16 ans au moment de l'inscription
        # Active toutes les protections : contact redirigé, badge mineur, etc.
    )

    tuteur_nom = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        # Nom complet du parent ou tuteur légal
        # Obligatoire si is_minor = True
    )

    tuteur_lien = models.CharField(
        max_length=20,
        choices=TUTEUR_LIEN_CHOICES,
        null=True,
        blank=True,
        # Lien entre le tuteur et le joueur : Père, Mère, Tuteur légal, Autre
    )

    tuteur_whatsapp = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        # Numéro WhatsApp du tuteur
        # C'est CE numéro qui s'affiche sur le profil public si is_minor = True
    )

    consent_doc = models.FileField(
        upload_to='documents/consentements/',
        null=True,
        blank=True,
        # Document de consentement parental signé
        # Uploadé par le tuteur lors de l'inscription du mineur
    )

    is_minor_consent_validated = models.BooleanField(
        default=False,
        # True = l'admin a vérifié le document de consentement
        # Le profil mineur ne peut pas être publié tant que c'est False
    )

    consent_validated_at = models.DateTimeField(
        null=True,
        blank=True,
        # Date et heure exactes de la validation par l'admin
    )

    consent_validated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validated_consents',
        # Admin qui a validé le consentement — traçabilité importante
    )

    # ── Statistiques et URL ───────────────────────────────────

    slug = models.SlugField(
        max_length=120,
        unique=True,
        # URL unique du profil — Ex : omar-traore-229
        # Généré automatiquement depuis le nom du joueur
    )

    profile_views = models.PositiveIntegerField(
        default=0,
        # Nombre de fois que le profil a été consulté
        # Affiché au joueur dans son tableau de bord
    )

    # ── Dates ─────────────────────────────────────────────────

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # auto_now=True : mis à jour automatiquement à chaque modification

    class Meta:
        verbose_name        = 'Profil Joueur'
        verbose_name_plural = 'Profils Joueurs'
        ordering            = ['-created_at']  # Les plus récents en premier

    def __str__(self):
        return f'{self.nom_complet} — {self.ville}'

    # ── Méthodes utilitaires ──────────────────────────────────

    def get_age(self):
        """
        Calcule et retourne l'âge exact du joueur en années.
        Utilisé pour afficher l'âge sur le profil public.
        """
        today = date.today()
        age = today.year - self.date_naissance.year
        # Vérifie si l'anniversaire est déjà passé cette année
        if (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day):
            age -= 1
        return age

    def get_categorie_age(self):
        """
        Retourne la catégorie d'âge selon les standards FIFA.
        Utilisé pour les filtres recruteurs et l'affichage du profil.
        """
        age = self.get_age()
        if age < 12:
            return 'U11'
        elif age < 14:
            return 'U13'
        elif age < 16:
            return 'U15'
        elif age < 18:
            return 'U17'
        elif age < 21:
            return 'U20'
        elif age < 24:
            return 'U23'
        else:
            return 'Senior'

    def generate_slug(self):
        """
        Génère un slug unique pour l'URL du profil.
        Ex : "Omar Traoré" + id=229 → "omar-traore-229"
        Le suffixe numérique garantit l'unicité même si deux joueurs
        ont le même nom.
        """
        base_slug = slugify(self.nom_complet)
        return f'{base_slug}-{self.user.id}'

    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save() pour :
        1. Générer le slug automatiquement si pas encore défini
        2. Marquer automatiquement le profil comme mineur si âge < 16 ans
        """
        # Génère le slug si c'est un nouveau profil
        if not self.slug:
            self.slug = self.generate_slug()

        # Détecte et marque automatiquement les mineurs
        if self.date_naissance:
            self.is_minor = self.get_age() < 16

        super().save(*args, **kwargs)

    def clean(self):
        """
        Validation métier supplémentaire avant sauvegarde.
        Django appelle cette méthode automatiquement dans les formulaires.
        """
        # Vérifie que le joueur a au moins 10 ans
        if self.date_naissance:
            if self.get_age() < 10:
                raise ValidationError(
                    'L\'inscription n\'est pas autorisée pour les moins de 10 ans.'
                )

        # Vérifie que les informations du tuteur sont présentes pour les mineurs
        if self.is_minor:
            if not self.tuteur_nom:
                raise ValidationError(
                    'Le nom du tuteur est obligatoire pour un profil mineur.'
                )
            if not self.tuteur_whatsapp:
                raise ValidationError(
                    'Le numéro WhatsApp du tuteur est obligatoire pour un profil mineur.'
                )


# ── PROFIL RECRUTEUR ─────────────────────────────────────────
class RecruiterProfile(models.Model):
    """
    Profil spécifique aux recruteurs.
    Un recruteur doit être validé par l'admin avant de pouvoir
    consulter les profils et contacter des joueurs.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='recruiter_profile',
    )

    nom_complet = models.CharField(max_length=100)

    organisation = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        # Nom du club, académie ou centre de formation
        # Ex : "Académie de Football de Cotonou"
    )

    poste_occupe = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        # Rôle du recruteur dans son organisation
        # Ex : "Directeur Sportif", "Recruteur U20", "Scout"
    )

    telephone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        # Contact professionnel du recruteur
    )

    is_validated = models.BooleanField(
        default=False,
        # CRUCIAL : False par défaut
        # Un recruteur ne peut pas voir les profils ni contacter des joueurs
        # tant que l'admin n'a pas mis ce champ à True
        # C'est la barrière principale contre les faux recruteurs
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Profil Recruteur'
        verbose_name_plural = 'Profils Recruteurs'
        ordering            = ['-created_at']

    def __str__(self):
        return f'{self.nom_complet} — {self.organisation or "Sans organisation"}'
    
    