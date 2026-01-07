from django.core.management.base import BaseCommand
from farms.soil_services import SoilSyncService
from farms.models import Plot


class Command(BaseCommand):
    help = 'Sync all plots to soil.py service'

    def add_arguments(self, parser):
        parser.add_argument(
            '--plot-id',
            type=int,
            help='Sync specific plot by ID',
        )

    def handle(self, *args, **options):
        sync_service = SoilSyncService()
        
        if options['plot_id']:
            try:
                plot = Plot.objects.get(id=options['plot_id'])
                self.stdout.write(f"Syncing plot {plot.id} ({plot.gat_number}/{plot.plot_number}) to soil.py...")
                
                if sync_service.sync_plot_to_soil(plot):
                    self.stdout.write(
                        self.style.SUCCESS(f"Successfully synced plot {plot.id} to soil.py")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"Failed to sync plot {plot.id} to soil.py")
                    )
            except Plot.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Plot with ID {options['plot_id']} does not exist")
                )
        else:
            self.stdout.write("Syncing all plots to soil.py...")
            
            if sync_service.sync_all_plots():
                self.stdout.write(
                    self.style.SUCCESS("Successfully synced all plots to soil.py")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("Failed to sync plots to soil.py")
                )
