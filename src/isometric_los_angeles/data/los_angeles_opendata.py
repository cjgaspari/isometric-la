from typing import Any, Dict, Optional

from sodapy import Socrata

# Building footprints for the City of Los Angeles are published primarily via
# Geohub (ArcGIS), dataset id: 813fcefde1f64b209103107b26a8909f_0
# https://geohub.lacity.org/datasets/813fcefde1f64b209103107b26a8909f_0
#
# This client talks to the Socrata portal at data.lacity.org. Override
# DATASET_ID with a Socrata 4x4 id when using a Socrata-hosted layer.
DATASET_ID = "nbyu-2ha9"  # Building & Safety permits (Socrata example)


class LosAngelesOpenDataClient:
  def __init__(self, app_token: Optional[str] = None):
    self.client = Socrata("data.lacity.org", app_token)

  def get_building_footprint(self, lat: float, lng: float) -> Optional[Dict[str, Any]]:
    """
    Find a record near the given point via SoQL intersects, when the configured
    dataset exposes a polygon geometry column named the_geom.
    Returns the first match found.
    """
    # SoQL query to find polygon containing the point
    # We use 'intersects(the_geom, 'POINT(lng lat)')'
    # Note: WKT is POINT(x y) -> POINT(lng lat)
    query = f"intersects(the_geom, 'POINT({lng} {lat})')"

    results = self.client.get(DATASET_ID, where=query, limit=1)

    if results:
      return results[0]
    return None
