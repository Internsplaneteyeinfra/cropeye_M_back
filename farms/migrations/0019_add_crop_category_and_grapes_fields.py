# Generated manually for crop category and grapes-specific fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('farms', '0018_add_crop_variety_to_farm'),
    ]

    operations = [
        # Add crop_category to CropType
        migrations.AddField(
            model_name='croptype',
            name='crop_category',
            field=models.CharField(
                choices=[
                    ('sugarcane', 'Sugarcane'),
                    ('grapes', 'Grapes'),
                    ('wheat', 'Wheat'),
                    ('rice', 'Rice'),
                    ('other', 'Other'),
                ],
                default='sugarcane',
                help_text='Category of crop (determines which fields to show)',
                max_length=50
            ),
        ),
        # Add grapes-specific fields to Farm
        migrations.AddField(
            model_name='farm',
            name='variety_type',
            field=models.CharField(
                blank=True,
                choices=[('pre_season', 'Pre-Season'), ('seasonal', 'Seasonal')],
                help_text='Variety type (Grapes only)',
                max_length=50,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='farm',
            name='variety_subtype',
            field=models.CharField(
                blank=True,
                choices=[('wine', 'Wine Grapes'), ('table', 'Table Grapes')],
                help_text='Variety subtype (Grapes only)',
                max_length=50,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='farm',
            name='variety_timing',
            field=models.CharField(
                blank=True,
                choices=[('early', 'Early'), ('late', 'Late')],
                help_text='Variety timing (Grapes only)',
                max_length=50,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='farm',
            name='plant_age',
            field=models.CharField(
                blank=True,
                choices=[
                    ('0-2', '0-2 years'),
                    ('2-3', '2-3 years'),
                    ('above_3', 'Above 3 years'),
                ],
                help_text='Plant age (Grapes only)',
                max_length=50,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='farm',
            name='foundation_pruning_date',
            field=models.DateField(
                blank=True,
                help_text='Foundation pruning date (Grapes only)',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='farm',
            name='fruit_pruning_date',
            field=models.DateField(
                blank=True,
                help_text='Fruit pruning date (Grapes only)',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='farm',
            name='last_harvesting_date',
            field=models.DateField(
                blank=True,
                help_text='Last harvesting date (Grapes only)',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='farm',
            name='resting_period_days',
            field=models.IntegerField(
                blank=True,
                help_text='Resting period in days (Grapes only)',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='farm',
            name='row_spacing',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Row spacing in meters (Grapes drip irrigation)',
                max_digits=8,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='farm',
            name='plant_spacing',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Plant spacing in meters (Grapes drip irrigation)',
                max_digits=8,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='farm',
            name='flow_rate_liter_per_hour',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Flow rate in liters/hour (Grapes drip irrigation)',
                max_digits=10,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='farm',
            name='emitters_per_plant',
            field=models.IntegerField(
                blank=True,
                help_text='Number of emitters per plant (Grapes drip irrigation)',
                null=True
            ),
        ),
    ]

