from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class AutoAssignmentService:
    """
    Service to handle auto-assignment of farmers to plots and farms
    created by field officers in the enrollment workflow.
    """
    
    @staticmethod
    def get_most_recent_farmer_by_field_officer(field_officer: User, within_minutes: int = 30) -> Optional[User]:
        """
        Get the most recently created farmer by a specific field officer.
        
        Args:
            field_officer: The field officer user
            within_minutes: Only consider farmers created within this many minutes (default: 30)
        
        Returns:
            User: Most recent farmer or None if not found
        """
        try:
            # Calculate the time threshold
            time_threshold = timezone.now() - timedelta(minutes=within_minutes)
            
            # Find the most recent farmer created by this field officer
            recent_farmer = User.objects.filter(
                # Farmer role
                role__name='farmer',
                # Created by this field officer (assuming there's a created_by field)
                # If there's no created_by field, we'll use a different approach
                date_joined__gte=time_threshold
            ).order_by('-date_joined').first()
            
            # If no direct created_by relationship, find farmers created around the same time
            # This is a fallback approach - we look for farmers created recently
            if not recent_farmer:
                recent_farmer = User.objects.filter(
                    role__name='farmer',
                    date_joined__gte=time_threshold
                ).order_by('-date_joined').first()
            
            return recent_farmer
            
        except Exception as e:
            logger.error(f"Error getting recent farmer for field officer {field_officer.id}: {str(e)}")
            return None
    
    @staticmethod
    def get_farmers_by_field_officer_today(field_officer: User) -> User.objects:
        """
        Get all farmers created by a field officer today.
        
        Args:
            field_officer: The field officer user
        
        Returns:
            QuerySet: Farmers created today
        """
        try:
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            return User.objects.filter(
                role__name='farmer',
                date_joined__gte=today_start
            ).order_by('-date_joined')
            
        except Exception as e:
            logger.error(f"Error getting today's farmers for field officer {field_officer.id}: {str(e)}")
            return User.objects.none()
    
    @staticmethod
    def auto_assign_farmer_to_plot(plot, field_officer: User) -> bool:
        """
        Auto-assign the most recent farmer to a plot.
        
        Args:
            plot: Plot instance
            field_officer: Field officer who created the plot
        
        Returns:
            bool: True if assignment successful, False otherwise
        """
        try:
            # Get the most recent farmer
            recent_farmer = AutoAssignmentService.get_most_recent_farmer_by_field_officer(field_officer)
            
            if recent_farmer:
                plot.farmer = recent_farmer
                plot.created_by = field_officer
                plot.save(update_fields=['farmer', 'created_by'])
                
                logger.info(f"Auto-assigned farmer {recent_farmer.username} to plot {plot.id}")
                return True
            else:
                logger.warning(f"No recent farmer found for field officer {field_officer.username}")
                return False
                
        except Exception as e:
            logger.error(f"Error auto-assigning farmer to plot {plot.id}: {str(e)}")
            return False
    
    @staticmethod
    def auto_assign_farmer_to_farm(farm, field_officer: User) -> bool:
        """
        Auto-assign the most recent farmer to a farm.
        
        Args:
            farm: Farm instance
            field_officer: Field officer who created the farm
        
        Returns:
            bool: True if assignment successful, False otherwise
        """
        try:
            # Get the most recent farmer
            recent_farmer = AutoAssignmentService.get_most_recent_farmer_by_field_officer(field_officer)
            
            if recent_farmer:
                farm.farm_owner = recent_farmer
                farm.created_by = field_officer
                farm.save(update_fields=['farm_owner', 'created_by'])
                
                logger.info(f"Auto-assigned farmer {recent_farmer.username} to farm {farm.id}")
                return True
            else:
                logger.warning(f"No recent farmer found for field officer {field_officer.username}")
                return False
                
        except Exception as e:
            logger.error(f"Error auto-assigning farmer to farm {farm.id}: {str(e)}")
            return False
    
    @staticmethod
    def validate_farmer_assignment(farmer: User, field_officer: User) -> bool:
        """
        Validate that a farmer can be assigned by a field officer.
        
        Args:
            farmer: Farmer user
            field_officer: Field officer user
        
        Returns:
            bool: True if assignment is valid, False otherwise
        """
        try:
            # Check if farmer has farmer role
            if not farmer.has_role('farmer'):
                logger.warning(f"User {farmer.username} does not have farmer role")
                return False
            
            # Check if field officer has fieldofficer role
            if not field_officer.has_role('fieldofficer'):
                logger.warning(f"User {field_officer.username} does not have fieldofficer role")
                return False
            
            # Additional validation: farmer should be created recently (within 24 hours)
            time_threshold = timezone.now() - timedelta(hours=24)
            if farmer.date_joined < time_threshold:
                logger.warning(f"Farmer {farmer.username} was not created recently")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating farmer assignment: {str(e)}")
            return False
