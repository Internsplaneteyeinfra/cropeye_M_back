import json
import requests
from datetime import datetime
from decimal import Decimal, InvalidOperation
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


def _parse_date(val):
    """Parse date from string (YYYY-MM-DD or DD-MM-YYYY) or return None."""
    if val is None or val == "":
        return None
    if hasattr(val, "year"):
        return val
    if isinstance(val, str):
        s = val.strip()[:10]
        for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
    return None


def _parse_decimal(val):
    """Parse Decimal from string/number or return None."""
    if val is None or val == "":
        return None
    try:
        return Decimal(str(val))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _parse_int(val):
    """Parse int from string/number or return None."""
    if val is None or val == "":
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _normalize_plant_age(val):
    """Normalize plant_age e.g. '0_2' -> '0-2', 'above-3' -> 'above_3'."""
    if val is None or val == "":
        return None
    s = str(val).strip().replace("_", "-")
    if s == "above-3":
        s = "above_3"
    if s in ("0-2", "2-3", "above_3"):
        return s
    return None


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
        """
        Create farmer with multiple plots, farms, and irrigations.
        
        Supports two formats:
        1. Single plot (backward compatible):
           {
             "farmer": {...},
             "plot": {...},
             "farm": {...},
             "irrigation": {...}
           }
        
        2. Multiple plots:
           {
             "farmer": {...},
             "plots": [
               {
                 "plot": {...},
                 "farm": {...},
                 "irrigation": {...}
               },
               ...
             ]
           }
        """
        from users.models import Role
        
        # 1. Create Farmer/User with password and farmer role
        farmer_data = data.get("farmer", {})
        
        # Get or create farmer role (roleid = 1)
        farmer_role, _ = Role.objects.get_or_create(
            id=1,
            defaults={'name': 'farmer', 'display_name': 'Farmer'}
        )
        
        # Create user with password (phone_number is the unique identifier)
        phone_number = farmer_data.get("phone_number")
        if not phone_number:
            raise ValueError("phone_number is required for farmer registration.")
        farmer = User.objects.create_user(
            phone_number=str(phone_number).strip(),
            email=farmer_data.get("email"),
            password=farmer_data.get("password"),
            first_name=farmer_data.get("first_name", ""),
            last_name=farmer_data.get("last_name", ""),
            address=farmer_data.get("address", ""),
            village=farmer_data.get("village", ""),
            district=farmer_data.get("district", ""),
            state=farmer_data.get("state", ""),
            taluka=farmer_data.get("taluka", ""),
            role=farmer_role
        )

        # Check if using multiple plots format or single plot format
        plots_data = data.get("plots", [])
        
        # If no "plots" array, check for single plot format (backward compatible)
        if not plots_data:
            single_plot = data.get("plot")
            single_farm = data.get("farm")
            single_irrigation = data.get("irrigation")
            if single_plot:
                plots_data = [{
                    "plot": single_plot,
                    "farm": single_farm or {},
                    "irrigation": single_irrigation
                }]
        
        # 2. Create Plots, Farms, and Irrigations
        created_plots = []
        created_farms = []
        created_irrigations = []
        
        for plot_entry in plots_data:
            plot_data = plot_entry.get("plot", {})
            farm_data = plot_entry.get("farm", {})
            irrigation_data = plot_entry.get("irrigation")
            
            logger.info(f"Processing plot_entry: {plot_entry}")
            logger.info(f"Extracted plot_data: {plot_data}")
            logger.info(f"plot_data has 'boundary' key: {'boundary' in plot_data}")
            
            # Create Plot
            from django.contrib.gis.geos import Polygon
            
            location = None
            boundary = None
            
            # Handle point location (center point): { "lat", "lon" } or { "lat", "lng" }
            if "location" in plot_data and plot_data["location"]:
                loc = plot_data["location"]
                lon = loc.get("lon") if loc.get("lon") is not None else loc.get("lng", 0.0)
                lat = loc.get("lat", 0.0)
                location = Point(float(lon), float(lat))
                logger.info(f"Created location Point: {location}")
            
            # Handle boundary polygon coordinates
            if "boundary" in plot_data and plot_data["boundary"]:
                boundary_data = plot_data["boundary"]
                logger.info(f"Received boundary data: {boundary_data}")
                logger.info(f"Boundary data type: {type(boundary_data)}")
                
                # Support multiple formats:
                # 1. GeoJSON format: {"type": "Polygon", "coordinates": [[[lon, lat], [lon, lat], ...]]}
                # 2. Simple array: [[lon, lat], [lon, lat], ...]
                # 3. Array of objects: [{"lon": x, "lat": y}, {"lon": x, "lat": y}, ...]
                
                coords = None
                if isinstance(boundary_data, dict) and "coordinates" in boundary_data:
                    # GeoJSON format
                    coords = boundary_data["coordinates"]
                    logger.info(f"GeoJSON format detected, coordinates: {coords}")
                    if coords and isinstance(coords[0], list) and len(coords[0]) > 0 and isinstance(coords[0][0], list):
                        # Nested array [[coords]]
                        coords = coords[0]
                        logger.info(f"Unwrapped nested coordinates: {coords}")
                elif isinstance(boundary_data, list):
                    coords = boundary_data
                    logger.info(f"Simple array format detected: {coords}")
                
                if coords:
                    # Convert to list of tuples (lon, lat)
                    polygon_coords = []
                    for coord in coords:
                        if isinstance(coord, dict):
                            # {"lon": x, "lat": y} or {"lng": x, "lat": y}
                            x = coord.get("lon") if coord.get("lon") is not None else coord.get("lng", 0.0)
                            polygon_coords.append((float(x), float(coord.get("lat", 0.0))))
                        elif isinstance(coord, (list, tuple)) and len(coord) >= 2:
                            # [lon, lat] format
                            polygon_coords.append((float(coord[0]), float(coord[1])))
                    
                    logger.info(f"Parsed polygon_coords: {polygon_coords}")
                    
                    # Ensure polygon is closed (first point == last point)
                    if polygon_coords and polygon_coords[0] != polygon_coords[-1]:
                        polygon_coords.append(polygon_coords[0])
                        logger.info(f"Closed polygon_coords: {polygon_coords}")
                    
                    # Need at least 4 points for a valid polygon (3 vertices + closing point)
                    if len(polygon_coords) >= 4:
                        try:
                            boundary = Polygon(polygon_coords)
                            logger.info(f"Created Polygon boundary: {boundary}")
                        except Exception as e:
                            logger.error(f"Failed to create Polygon: {e}")
                    else:
                        logger.warning(f"Not enough points for polygon: {len(polygon_coords)} (need at least 4)")
            else:
                logger.info(f"No boundary data in plot_data. Keys: {plot_data.keys()}")

            logger.info(f"Creating Plot with location={location}, boundary={boundary}")
            
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
                boundary=boundary,
                farmer=farmer,
                created_by=created_by
            )
            
            # Verify what was stored
            plot.refresh_from_db()
            logger.info(f"Plot created with id={plot.id}, stored boundary={plot.boundary}")
            
            created_plots.append(plot)

            # Create Farm for this plot
            # Handle optional foreign keys - only set if ID exists and is valid
            from .models import SoilType, CropType, IrrigationType
            from users.models import Industry
            
            soil_type = None
            crop_type = None
            industry = None
            soil_type_id = farm_data.get("soil_type") or farm_data.get("soil_type_id")
            crop_type_id = farm_data.get("crop_type") or farm_data.get("crop_type_id")
            industry_id = farm_data.get("industry") or farm_data.get("industry_id")
            
            if soil_type_id:
                try:
                    soil_type = SoilType.objects.get(id=soil_type_id)
                except SoilType.DoesNotExist:
                    pass  # Leave as None if not found
            
            if crop_type_id:
                try:
                    crop_type = CropType.objects.get(id=crop_type_id)
                except CropType.DoesNotExist:
                    pass  # Leave as None if not found
            
            if industry_id:
                try:
                    industry = Industry.objects.get(id=industry_id)
                except Industry.DoesNotExist:
                    pass
            
            # Area: support alias size_in_acres (Farm.area_size is required; fallback to 0 if missing)
            area_size = _parse_decimal(farm_data.get("area_size")) or _parse_decimal(
                farm_data.get("size_in_acres")
            )
            if area_size is None:
                area_size = Decimal("0")
            
            # Optional string fields (strip empty to None for consistency)
            def _str_or_none(v):
                if v is None or (isinstance(v, str) and not v.strip()):
                    return None
                return str(v).strip() if v else None
            
            crop_variety = _str_or_none(farm_data.get("crop_variety"))
            variety_type = _str_or_none(farm_data.get("variety_type"))
            variety_subtype = _str_or_none(farm_data.get("variety_subtype"))
            variety_timing = _str_or_none(farm_data.get("variety_timing"))
            plant_age = _normalize_plant_age(farm_data.get("plant_age"))
            resting_period_days = _parse_int(farm_data.get("resting_period_days"))
            row_spacing = _parse_decimal(farm_data.get("row_spacing"))
            plant_spacing = _parse_decimal(farm_data.get("plant_spacing"))
            flow_rate_liter_per_hour = _parse_decimal(
                farm_data.get("flow_rate_liter_per_hour") or farm_data.get("flow_rate_lph")
            )
            emitters_per_plant = _parse_int(farm_data.get("emitters_per_plant"))
            
            # Parsed dates
            plantation_date = _parse_date(
                farm_data.get("plantation_date")
            )
            foundation_pruning_date = _parse_date(farm_data.get("foundation_pruning_date"))
            fruit_pruning_date = _parse_date(farm_data.get("fruit_pruning_date"))
            last_harvesting_date = _parse_date(farm_data.get("last_harvesting_date"))
            
            farm = Farm.objects.create(
                farm_owner=farmer,
                created_by=created_by,
                plot=plot,
                industry=industry,
                address=farm_data.get("address") or "",
                area_size=area_size,
                soil_type=soil_type,
                crop_type=crop_type,
                crop_variety=crop_variety,
                variety_type=variety_type,
                variety_subtype=variety_subtype,
                variety_timing=variety_timing,
                plant_age=plant_age,
                resting_period_days=resting_period_days,
                row_spacing=row_spacing,
                plant_spacing=plant_spacing,
                flow_rate_liter_per_hour=flow_rate_liter_per_hour,
                emitters_per_plant=emitters_per_plant,
                spacing_a=_parse_decimal(farm_data.get("spacing_a")),
                spacing_b=_parse_decimal(farm_data.get("spacing_b")),
                plantation_date=plantation_date,
                foundation_pruning_date=foundation_pruning_date,
                fruit_pruning_date=fruit_pruning_date,
                last_harvesting_date=last_harvesting_date,
            )
            created_farms.append(farm)

            # Create Irrigation for this farm (optional)
            irrigation = None
            if irrigation_data:
                loc = irrigation_data.get("location")
                if isinstance(loc, dict) and "lat" in loc and (loc.get("lon") is not None or loc.get("lng") is not None):
                    lon = loc.get("lon") if loc.get("lon") is not None else loc.get("lng", 0.0)
                    loc_point = Point(float(lon), float(loc.get("lat", 0.0)))
                else:
                    loc_point = Point(0.0, 0.0)

                # Handle optional irrigation type (accept irrigation_type or irrigation_type_id)
                irrigation_type = None
                irrigation_type_id = irrigation_data.get("irrigation_type_id") or irrigation_data.get("irrigation_type")
                if irrigation_type_id:
                    try:
                        irrigation_type = IrrigationType.objects.get(id=irrigation_type_id)
                    except IrrigationType.DoesNotExist:
                        pass  # Leave as None if not found

                irrigation = FarmIrrigation.objects.create(
                    farm=farm,
                    irrigation_type=irrigation_type,
                    status=irrigation_data.get("status", True),
                    motor_horsepower=irrigation_data.get("motor_horsepower"),
                    pipe_width_inches=irrigation_data.get("pipe_width_inches"),
                    distance_motor_to_plot_m=irrigation_data.get("distance_motor_to_plot_m"),
                    plants_per_acre=irrigation_data.get("plants_per_acre"),
                    flow_rate_lph=irrigation_data.get("flow_rate_lph"),
                    emitters_count=irrigation_data.get("emitters_count"),
                    location=loc_point
                )
                created_irrigations.append(irrigation)

        # Return result - backward compatible for single plot, extended for multiple
        return {
            "farmer": farmer,
            "plots": created_plots,
            "farms": created_farms,
            "irrigations": created_irrigations,
            # Backward compatibility - return first items as singular
            "plot": created_plots[0] if created_plots else None,
            "farm": created_farms[0] if created_farms else None,
            "irrigation": created_irrigations[0] if created_irrigations else None
        }
