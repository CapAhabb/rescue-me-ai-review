# Rescue Me Web Data

## Lake Michigan Bathymetry

- `noaa_lake_michigan_bathymetry_contours.geojson`
- `lake_michigan_shoreline.geojson`

These files were copied from the local Lake Command asset set in
`/home/captain/lake_command_in_depth/starter_app/assets/` so Rescue Me can render
Lake Michigan seabed contouring from real project data while remaining runnable
as a static web console.

The bathymetry contour file contains GeoJSON line features with a `depth`
property in meters. The web console renders those features directly and does not
generate fallback contours.

This layer is a mariner visual aid only and is not a certified navigation chart.
