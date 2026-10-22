from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='soumission',
            name='nom_original',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='soumission',
            name='date_soumission',
            field=models.DateTimeField(),
        ),
        migrations.AddConstraint(
            model_name='soumission',
            constraint=models.UniqueConstraint(
                fields=('devoir', 'etudiant'),
                name='soumission_une_par_etudiant',
            ),
        ),
    ]
