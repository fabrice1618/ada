from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_rendus_groupes'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='soumission',
            name='chemin_fichier',
        ),
        migrations.RemoveField(
            model_name='soumission',
            name='nom_original',
        ),
    ]
