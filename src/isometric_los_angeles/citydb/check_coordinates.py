import psycopg2
from isometric_los_angeles.city_db.db import get_db_config
from shapely.wkb import loads as load_wkb


def check_raw_coords():
  conn = psycopg2.connect(**get_db_config())
  with conn.cursor() as cur:
    # Get one raw geometry from the table
    sql = "SELECT ST_AsBinary(geometry) FROM citydb.geometry_data LIMIT 1;"
    cur.execute(sql)
    row = cur.fetchone()

    if row:
      geom = load_wkb(bytes(row[0]))
      # Get the first point of the geometry
      if geom.geom_type == "Polygon":
        x, y = geom.exterior.coords[0][0], geom.exterior.coords[0][1]
      elif geom.geom_type == "MultiPolygon":
        x, y = geom.geoms[0].exterior.coords[0][0], geom.geoms[0].exterior.coords[0][1]
      elif geom.geom_type == "MultiSurface":
        # Handle MultiSurface (common in CityGML)
        x, y = geom.geoms[0].exterior.coords[0][0], geom.geoms[0].exterior.coords[0][1]
      else:
        x, y = 0, 0

      print(f"\n📢 RAW COORDINATE SAMPLE: X={x:.2f}, Y={y:.2f}")

      # --- DIAGNOSIS ---
      if 300000 < x < 500000 and 3_700_000 < y < 4_000_000:
        print("✅ DIAGNOSIS: Data is in UTM 11N (Meters).")
        print("👉 ACTION: Set FORCE_SRID = 32611 in your script.")
      elif 6_000_000 < x < 7_000_000:
        print("✅ DIAGNOSIS: Data is in California State Plane Zone 5 (Feet).")
        print("👉 ACTION: Set FORCE_SRID = 2229 in your script.")
      else:
        print("⚠️  Unknown Projection. Use these SRID values to find the match.")
    else:
      print("❌ Table is empty.")


def main():
  check_raw_coords()


if __name__ == "__main__":
  main()
