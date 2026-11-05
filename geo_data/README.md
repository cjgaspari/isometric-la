# Geo Data

This directory is used to store the data for city geometry, which was used to create a "whitebox" render of the buildings/map. It's a legacy part of the application and workflow, but is kept for historical reasons.

## Los Angeles Building / 3D Geometry

Primary public sources for Los Angeles building geometry:

* City of Los Angeles Geohub — [Building Footprints](https://geohub.lacity.org/datasets/813fcefde1f64b209103107b26a8909f_0)
* Los Angeles County — Countywide Building Outlines (LARIAC)

## Overview

Place downloaded mesh / footprint datasets for Los Angeles under this directory (for example under `geo_data/los-angeles/`). The generation and whitebox tooling expects local geometry assets when producing 3D renders for tile generation.
