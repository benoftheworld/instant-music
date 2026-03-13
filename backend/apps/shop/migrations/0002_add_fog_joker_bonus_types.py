"""Migration : ajout des types de bonus FOG et JOKER."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="shopitem",
            name="bonus_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("double_points", "Points doublés"),
                    ("max_points", "Points maximum"),
                    ("time_bonus", "Temps bonus (+15 s)"),
                    ("fifty_fifty", "50/50 (retire 2 mauvaises réponses)"),
                    ("steal", "Vol de points (-100 pts au 1er)"),
                    ("shield", "Bouclier (protection vol)"),
                    ("fog", "Mode brouillard (floute les réponses au prochain round)"),
                    ("joker", "Joker (réponse fausse comptée comme correcte)"),
                ],
                help_text="Uniquement pour les articles de type bonus",
                max_length=30,
                null=True,
                verbose_name="type de bonus",
            ),
        ),
        migrations.AlterField(
            model_name="gamebonus",
            name="bonus_type",
            field=models.CharField(
                choices=[
                    ("double_points", "Points doublés"),
                    ("max_points", "Points maximum"),
                    ("time_bonus", "Temps bonus (+15 s)"),
                    ("fifty_fifty", "50/50 (retire 2 mauvaises réponses)"),
                    ("steal", "Vol de points (-100 pts au 1er)"),
                    ("shield", "Bouclier (protection vol)"),
                    ("fog", "Mode brouillard (floute les réponses au prochain round)"),
                    ("joker", "Joker (réponse fausse comptée comme correcte)"),
                ],
                max_length=30,
                verbose_name="type de bonus",
            ),
        ),
    ]
