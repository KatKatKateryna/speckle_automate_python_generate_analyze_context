

def downloadElev():
    import elevation
    # clip the SRTM1 30m DEM of Rome and save it to Rome-DEM.tif
    elevation.clip(bounds=(12.35, 41.8, 12.65, 42), output='Rome-DEM.tif')
    # clean up stale temporary files and fix the cache in the event of a server error
    elevation.clean()