from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("administration", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LegalPage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "page_type",
                    models.CharField(
                        choices=[
                            ("privacy", "Politique de confidentialité"),
                            ("legal", "Mentions légales"),
                        ],
                        max_length=20,
                        unique=True,
                        verbose_name="type de page",
                    ),
                ),
                (
                    "title",
                    models.CharField(max_length=200, verbose_name="titre"),
                ),
                (
                    "content",
                    models.TextField(
                        help_text="Texte libre. Séparer les paragraphes par une ligne vide.",
                        verbose_name="contenu",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="mis à jour le"),
                ),
            ],
            options={
                "verbose_name": "Page légale",
                "verbose_name_plural": "Pages légales",
            },
        ),
    ]
