-- Script to list Glam rock bands by longevity
SELECT band_name, (2022 - formed) AS lifespan
FROM metal_bands
WHERE main_style = 'Glam rock'
ORDER BY lifespan DESC;

