# Bounds App

We want to determine the x/y tile boundaries for a full-scale isometric pixel
art generation map of Los Angeles. Create a script in the
`src/isometric_los_angeles/generation` directory called "visualize bounds" that
takes three parameters:

generation_dir - the directory containing the generation config top-left - an
(x,y) tuple string that determines the top left of the bounding box
bottom-right - an (x,y) tuple string that determines the bottom right of the
bounding box

Given these parameters and the configuration parameters (seed center, azimuth,
etc) contained in the generation dir generation_config.json, render a
`web render` of the full box at a width of ~2000px in order to visualize the map
of what the full generation would look like.
