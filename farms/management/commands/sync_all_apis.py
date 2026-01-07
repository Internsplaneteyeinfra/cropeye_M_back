from django.core.management.base import BaseCommand
from farms.models import Plot
from farms.services import EventsSyncService
from farms.soil_services import SoilSyncService
from farms.admin_services import AdminSyncService
from farms.et_services import ETSyncService
from farms.field_services import FieldSyncService


class Command(BaseCommand):
    help = 'Sync all plots to ALL FastAPI services'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch',
            action='store_true',
            help='Sync all plots in batch mode to each service',
        )
        parser.add_argument(
            '--services',
            nargs='+',
            choices=['events', 'soil', 'admin', 'et', 'field'],
            default=['events', 'soil', 'admin', 'et', 'field'],
            help='Specify which services to sync to (default: all)',
        )

    def handle(self, *args, **options):
        services = {
            'events': EventsSyncService(),
            'soil': SoilSyncService(),
            'admin': AdminSyncService(),
            'et': ETSyncService(),
            'field': FieldSyncService(),
        }
        
        service_urls = {
            'events': 'http://localhost:9000',
            'soil': 'http://localhost:8003',
            'admin': 'http://localhost:7030',
            'et': 'http://localhost:8009',
            'field': 'http://localhost:7002',
        }
        
        selected_services = options['services']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting sync to {len(selected_services)} services: {", ".join(selected_services)}'
            )
        )
        
        if options['batch']:
            self.stdout.write('Using batch mode for all services...')
            
            for service_name in selected_services:
                self.stdout.write(f'\n--- Syncing to {service_name}.py ({service_urls[service_name]}) ---')
                service = services[service_name]
                
                try:
                    success = service.sync_all_plots()
                    if success:
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Successfully synced all plots to {service_name}.py')
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'✗ Failed to sync plots to {service_name}.py')
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Error syncing to {service_name}.py: {str(e)}')
                    )
        
        else:
            plots = Plot.objects.all()
            total_plots = plots.count()
            
            self.stdout.write(f'Syncing {total_plots} plots individually to each service...')
            
            results = {service: 0 for service in selected_services}
            
            for plot in plots:
                self.stdout.write(f'\nSyncing plot {plot.id}: {plot}')
                
                for service_name in selected_services:
                    service = services[service_name]
                    
                    try:
                        # Call the appropriate sync method
                        if service_name == 'events':
                            success = service.sync_plot_to_events(plot)
                        elif service_name == 'soil':
                            success = service.sync_plot_to_soil(plot)
                        elif service_name == 'admin':
                            success = service.sync_plot_to_admin(plot)
                        elif service_name == 'et':
                            success = service.sync_plot_to_et(plot)
                        elif service_name == 'field':
                            success = service.sync_plot_to_field(plot)
                        
                        if success:
                            results[service_name] += 1
                            self.stdout.write(f'  ✓ {service_name}.py')
                        else:
                            self.stdout.write(f'  ✗ {service_name}.py (failed)')
                    
                    except Exception as e:
                        self.stdout.write(f'  ✗ {service_name}.py (error: {str(e)})')
            
            # Show final results
            self.stdout.write('\n' + '='*50)
            self.stdout.write(self.style.SUCCESS('SYNC RESULTS SUMMARY:'))
            self.stdout.write('='*50)
            
            for service_name in selected_services:
                synced_count = results[service_name]
                self.stdout.write(
                    f'{service_name}.py: {synced_count}/{total_plots} plots synced '
                    f'({service_urls[service_name]})'
                )
            
            total_synced = sum(results.values())
            total_possible = total_plots * len(selected_services)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nOverall: {total_synced}/{total_possible} sync operations completed'
                )
            )
