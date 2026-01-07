from django.core.management.base import BaseCommand
from farms.models import Plot
from farms.farmer_registration_service import CompleteFarmerRegistrationService


class Command(BaseCommand):
    help = 'Sync all plots to all FastAPI services (Admin.py, ET.py, field.py, main.py, events.py)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--plot-id',
            type=int,
            help='Sync a specific plot by ID',
        )
        parser.add_argument(
            '--recent',
            type=int,
            help='Sync only the N most recent plots',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without actually syncing',
        )

    def handle(self, *args, **options):
        if options['plot_id']:
            # Sync specific plot
            try:
                plot = Plot.objects.get(id=options['plot_id'])
                self.stdout.write(f'Syncing plot {plot.id} ({plot.gat_number})...')
                
                if not options['dry_run']:
                    sync_results = CompleteFarmerRegistrationService._sync_plot_to_fastapi_services(plot)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Plot {plot.id} synced: {len(sync_results["successful"])} successful, '
                            f'{len(sync_results["failed"])} failed'
                        )
                    )
                    if sync_results['failed']:
                        self.stdout.write(
                            self.style.WARNING(f'❌ Failed: {", ".join(sync_results["failed"])}')
                        )
                else:
                    self.stdout.write(f'[DRY RUN] Would sync plot {plot.id}')
                    
            except Plot.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Plot with ID {options["plot_id"]} does not exist')
                )
                return
        
        else:
            # Sync multiple plots
            queryset = Plot.objects.all().order_by('-created_at')
            
            if options['recent']:
                queryset = queryset[:options['recent']]
                self.stdout.write(f'Syncing {options["recent"]} most recent plots...')
            else:
                self.stdout.write(f'Syncing all {queryset.count()} plots...')
            
            if options['dry_run']:
                self.stdout.write('[DRY RUN] Would sync the following plots:')
                for plot in queryset:
                    self.stdout.write(f'  - Plot {plot.id}: {plot.gat_number} ({plot.village})')
                return
            
            total_successful = 0
            total_failed = 0
            
            for i, plot in enumerate(queryset, 1):
                self.stdout.write(f'[{i}/{queryset.count()}] Syncing plot {plot.id} ({plot.gat_number})...')
                
                try:
                    sync_results = CompleteFarmerRegistrationService._sync_plot_to_fastapi_services(plot)
                    successful = len(sync_results['successful'])
                    failed = len(sync_results['failed'])
                    
                    total_successful += successful
                    total_failed += failed
                    
                    if successful > 0:
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✅ {successful} services synced successfully')
                        )
                    
                    if failed > 0:
                        self.stdout.write(
                            self.style.WARNING(f'  ❌ {failed} services failed')
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ Error syncing plot {plot.id}: {str(e)}')
                    )
                    total_failed += 5  # Assume all 5 services failed
            
            # Summary
            self.stdout.write('\n' + '='*50)
            self.stdout.write(
                self.style.SUCCESS(
                    f'📊 SYNC SUMMARY:\n'
                    f'   Total successful syncs: {total_successful}\n'
                    f'   Total failed syncs: {total_failed}\n'
                    f'   Plots processed: {queryset.count()}'
                )
            )
            
            if total_failed == 0:
                self.stdout.write(
                    self.style.SUCCESS('🎉 All plots synced successfully to all FastAPI services!')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️ Some syncs failed. Check the logs for details.'
                    )
                )
