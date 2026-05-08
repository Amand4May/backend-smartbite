# Generated migration to add nutrition calculation fields to Pet model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smartbite', '0003_alert_smartbite_a_user_id_5981ed_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='pet',
            name='is_neutered',
            field=models.BooleanField(default=False, verbose_name='Castrado/Esterilizado'),
        ),
        migrations.AddField(
            model_name='pet',
            name='body_condition',
            field=models.CharField(
                choices=[
                    ('underweight', 'Abaixo do peso'),
                    ('ideal', 'Peso ideal'),
                    ('overweight', 'Sobrepeso'),
                    ('obese', 'Obeso'),
                ],
                default='ideal',
                max_length=15,
                verbose_name='Condição corporal'
            ),
        ),
        migrations.AddField(
            model_name='pet',
            name='breed_factor',
            field=models.DecimalField(decimal_places=2, default=1.0, max_digits=3, verbose_name='Fator de raça'),
        ),
        migrations.AlterField(
            model_name='pet',
            name='activity_level',
            field=models.CharField(
                choices=[('low', 'Baixo'), ('moderate', 'Moderado'), ('high', 'Alto')],
                default='moderate',
                max_length=10,
                verbose_name='Nível de atividade'
            ),
        ),
    ]
