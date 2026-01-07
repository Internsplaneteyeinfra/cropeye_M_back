from django.core.management.base import BaseCommand
from farms.models import Plot
from farms.et_services import ETSyncService


class Command(BaseCommand):
    help = 'Sync all plots to ET.py FastAPI service'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch',
            action='store_true',
            help='Sync all plots in a single batch request',
        )

    def handle(self, *args, **options):
        sync_service = ETSyncService()
        
        if options['batch']:
            self.stdout.write('Syncing all plots to ET.py in batch mode...')
            success = sync_service.sync_all_plots()
            if success:
                self.stdout.write(
                    self.style.SUCCESS('Successfully synced all plots to ET.py')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Failed to sync plots to ET.py')
                )
        else:
            plots = Plot.objects.all()
            total_plots = plots.count()
            synced_count = 0
            
            self.stdout.write(f'Syncing {total_plots} plots to ET.py individually...')
            
            for plot in plots:
                if sync_service.sync_plot_to_et(plot):
                    synced_count += 1
                    self.stdout.write(f'Synced plot {plot.id}: {plot}')
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Failed to sync plot {plot.id}: {plot}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully synced {synced_count}/{total_plots} plots to ET.py'
                )
            )
