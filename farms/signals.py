from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Plot, Farm, FarmIrrigation
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(pre_delete, sender=User)
def cascade_delete_farmer_assets(sender, instance, **kwargs):
    """
    When a farmer is deleted, cascade delete all their plots, farms, and irrigations.
    This handles the cascading deletion since Django CASCADE doesn't work with nullable fields.
    """
    # Check if this user is a farmer (has role 'farmer' or has associated plots/farms)
    is_farmer = False
    
    # Check if user has farmer role
    if hasattr(instance, 'role') and instance.role and instance.role.name == 'farmer':
        is_farmer = True
    
    # Check if user has plots or farms (indicating they're a farmer)
    plots_count = instance.plots.count()
    farms_count = instance.farms.count()
    
    if plots_count > 0 or farms_count > 0:
        is_farmer = True
    
    if is_farmer:
        logger.info(f"Cascading deletion for farmer {instance.username} (ID: {instance.id})")
        
        # Get all related data before deletion
        plots = list(instance.plots.all())
        farms = list(instance.farms.all())
        
        logger.info(f"Found {len(plots)} plots and {len(farms)} farms to delete")
        
        # Delete farms first (this will cascade to irrigations)
        for farm in farms:
            logger.info(f"Deleting farm {farm.farm_uid} for farmer {instance.username}")
            farm.delete()
        
        # Delete plots
        for plot in plots:
            logger.info(f"Deleting plot {plot.gat_number} for farmer {instance.username}")
            plot.delete()
        
        logger.info(f"Successfully cascaded deletion for farmer {instance.username}")


@receiver(post_delete, sender=Plot)
def sync_plot_deletion_to_fastapi(sender, instance, **kwargs):
    """
    Sync plot deletion to all FastAPI services when a plot is deleted
    """
    # Skip sync if this is part of a cascading farmer deletion to avoid conflicts
    if getattr(instance, '_skip_fastapi_sync', False):
        logger.info(f"Skipping FastAPI sync for plot {instance.id} (cascading deletion)")
        return
    
    logger.info(f"Syncing deletion of plot {instance.id} to FastAPI services")
    
    # Import here to avoid circular imports
    try:
        # Sync deletion to all FastAPI services
        sync_services = [
            ('services', 'EventsSyncService', 'delete_plot_from_events'),
            ('soil_services', 'SoilSyncService', 'delete_plot_from_soil'),
            ('admin_services', 'AdminSyncService', 'delete_plot_from_admin'),
            ('et_services', 'ETSyncService', 'delete_plot_from_et'),
            ('field_services', 'FieldSyncService', 'delete_plot_from_field'),
        ]
        
        success_count = 0
        
        for module_name, class_name, method_name in sync_services:
            try:
                module = __import__(f'farms.{module_name}', fromlist=[class_name])
                service_class = getattr(module, class_name)
                service_instance = service_class()
                delete_method = getattr(service_instance, method_name)
                
                # Call the delete method with plot ID
                result = delete_method(instance.id)
                
                if result:
                    success_count += 1
                    logger.info(f"✅ Successfully synced plot {instance.id} deletion to {module_name}")
                else:
                    logger.warning(f"⚠️ Delete sync to {module_name} returned False for plot {instance.id}")
                    
            except Exception as e:
                logger.warning(f"❌ Failed to sync plot {instance.id} deletion to {module_name}: {str(e)}")
        
        logger.info(f"Plot {instance.id} deletion sync completed: {success_count}/{len(sync_services)} services successful")
                
    except Exception as e:
        logger.error(f"Failed to sync plot deletion: {str(e)}")


@receiver(post_delete, sender=Farm)
def log_farm_deletion(sender, instance, **kwargs):
    """
    Log farm deletion for tracking purposes
    """
    logger.info(f"Farm {instance.farm_uid} deleted (owner: {instance.farm_owner.username if instance.farm_owner else 'Unknown'})")


@receiver(post_delete, sender=FarmIrrigation)
def log_irrigation_deletion(sender, instance, **kwargs):
    """
    Log irrigation deletion for tracking purposes
    """
    # Get farm info before the object is fully deleted
    farm_info = "Unknown"
    try:
        if hasattr(instance, '_farm_uid_cache'):
            farm_info = instance._farm_uid_cache
        elif instance.farm_id:
            # Try to get farm info if still accessible
            try:
                farm = Farm.objects.get(id=instance.farm_id)
                farm_info = farm.farm_uid
            except Farm.DoesNotExist:
                farm_info = f"Farm ID {instance.farm_id} (deleted)"
    except Exception:
        pass
    
    logger.info(f"Irrigation system {instance.id} deleted (farm: {farm_info})")
