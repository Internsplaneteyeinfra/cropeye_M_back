import json
import requests
from django.conf import settings
from typing import Dict, Any, Optional
import logging
from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib.gis.geos import Point
from users.models import User  
from farms.models import Plot, Farm, FarmIrrigation

User = get_user_model()  # this will now point to your actual User model

logger = logging.getLogger(__name__)


class EventsSyncService:
    """
    Service to sync plot data between Django and events.py FastAPI service
    """

    def __init__(self):
        self.events_api_url = getattr(settings, 'EVENTS_API_URL', 'http://localhost:9000')

    def sync_plot_to_events(self, plot_instance) -> bool:
        try:
            plot_data = self._prepare_plot_data(plot_instance)
            response = requests.post(
                f"{self.events_api_url}/sync/plot",
                json=plot_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            if response.status_code == 200:
                logger.info(f"Successfully synced plot {plot_instance.id} to events.py")
                return True
            else:
                logger.error(f"Failed to sync plot {plot_instance.id}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error syncing plot {plot_instance.id} to events.py: {str(e)}")
            return False

    def _prepare_plot_data(self, plot_instance) -> Dict[str, Any]:
        plot_data = {
            "id": plot_instance.id,
            "name": self._generate_plot_name(plot_instance),
            "properties": {
                "Name": self._generate_plot_name(plot_instance),
                "Description": f"GAT: {plot_instance.gat_number}, Plot: {plot_instance.plot_number or 'N/A'}, Village: {plot_instance.village or 'Unknown'}",
                "gat_number": plot_instance.gat_number,
                "plot_number": plot_instance.plot_number,
                "village": plot_instance.village,
                "taluka": plot_instance.taluka,
                "district": plot_instance.district,
                "state": plot_instance.state,
                "country": plot_instance.country,
                "pin_code": plot_instance.pin_code
            },
            "geometry": {
                "type": "Polygon" if plot_instance.boundary else "Point",
                "coordinates": []
            }
        }

        if plot_instance.boundary:
            coords = list(plot_instance.boundary.coords[0])
            plot_data["geometry"]["coordinates"] = [coords]
        elif plot_instance.location:
            coords = [plot_instance.location.x, plot_instance.location.y, 0.0]
            plot_data["geometry"]["coordinates"] = coords
        else:
            plot_data["geometry"] = {"type": "Point", "coordinates": [0.0, 0.0, 0.0]}

        return plot_data

    def _generate_plot_name(self, plot_instance) -> str:
        if plot_instance.gat_number and plot_instance.plot_number:
            return f"{plot_instance.gat_number}_{plot_instance.plot_number}"
        elif plot_instance.gat_number:
            return plot_instance.gat_number
        else:
            return f"plot_{plot_instance.id}"

    def sync_all_plots(self) -> bool:
        try:
            plots = Plot.objects.all()
            plot_list = [self._prepare_plot_data(plot) for plot in plots]
            response = requests.post(
                f"{self.events_api_url}/sync/plots",
                json={"plots": plot_list},
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            if response.status_code == 200:
                logger.info(f"Successfully synced {len(plot_list)} plots to events.py")
                return True
            else:
                logger.error(f"Failed to sync plots: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error syncing plots to events.py: {str(e)}")
            return False

    def delete_plot_from_events(self, plot_id: int) -> bool:
        try:
            response = requests.delete(f"{self.events_api_url}/sync/plot/{plot_id}", timeout=10)
            if response.status_code == 200:
                logger.info(f"Successfully deleted plot {plot_id} from events.py")
                return True
            else:
                logger.error(f"Failed to delete plot {plot_id}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error deleting plot {plot_id} from events.py: {str(e)}")
            return False


class CompleteFarmerRegistrationService:
  
    @staticmethod
    @transaction.atomic
    def create_all(data: dict, created_by=None) -> dict:
        # 1. Create Farmer/User
        farmer_data = data.get("farmer", {})
        farmer = User.objects.create(
            username=farmer_data.get("username"),
            email=farmer_data.get("email"),
            first_name=farmer_data.get("first_name", ""),
            last_name=farmer_data.get("last_name", "")
        )

        # 2. Create Plot
        plot_data = data.get("plot", {})
        location = None
        if "location" in plot_data and plot_data["location"]:
            loc = plot_data["location"]
            location = Point(loc.get("lon", 0.0), loc.get("lat", 0.0))

        plot = Plot.objects.create(
            gat_number=plot_data.get("gat_number"),
            plot_number=plot_data.get("plot_number"),
            village=plot_data.get("village"),
            taluka=plot_data.get("taluka"),
            district=plot_data.get("district"),
            state=plot_data.get("state"),
            country=plot_data.get("country", "India"),
            pin_code=plot_data.get("pin_code"),
            location=location,
            farmer=farmer,
            created_by=created_by
        )

        # 3. Create Farm
        farm_data = data.get("farm", {})
        farm = Farm.objects.create(
            farm_owner=farmer,
            created_by=created_by,
            plot=plot,
            address=farm_data.get("address", ""),
            area_size=farm_data.get("area_size"),
            soil_type_id=farm_data.get("soil_type"),
            crop_type_id=farm_data.get("crop_type"),
            spacing_a=farm_data.get("spacing_a"),
            spacing_b=farm_data.get("spacing_b"),
            plantation_date=farm_data.get("plantation_date"),
            foundation_pruning_date=farm_data.get("foundation_pruning_date"),
            fruit_pruning_date=farm_data.get("fruit_pruning_date"),
            last_harvesting_date=farm_data.get("last_harvesting_date")
        )

        # 4. Optional: Create Irrigation
        irrigation_data = data.get("irrigation")
        irrigation = None
        if irrigation_data:
            # Ensure location is a Point
            loc = irrigation_data.get("location")
            if isinstance(loc, dict) and "lat" in loc and "lon" in loc:
                loc_point = Point(loc.get("lon", 0.0), loc.get("lat", 0.0))
            else:
                loc_point = Point(0.0, 0.0)  # default fallback

            irrigation = FarmIrrigation.objects.create(
                farm=farm,
                irrigation_type_id=irrigation_data.get("irrigation_type_id"),
                status=irrigation_data.get("status", True),
                motor_horsepower=irrigation_data.get("motor_horsepower"),
                pipe_width_inches=irrigation_data.get("pipe_width_inches"),
                distance_motor_to_plot_m=irrigation_data.get("distance_motor_to_plot_m"),
                plants_per_acre=irrigation_data.get("plants_per_acre"),
                flow_rate_lph=irrigation_data.get("flow_rate_lph"),
                emitters_count=irrigation_data.get("emitters_count"),
                location=loc_point
            )

        return {
            "farmer": farmer,
            "farm": farm,
            "plot": plot,
            "irrigation": irrigation
        }
