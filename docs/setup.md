# Setup

## Environment variables

First, copy the .env file and set the necessary environment variables

```bash
cp .env.example .env
```

## Python

isometric-los-angeles uses [`uv`](https://docs.astral.sh/uv/) for python dependency management and runtimes. First, ensure `uv` is installed and then run:

```bash
uv sync
```

This will install all python dependencies and set up the necessary python environment.

## Tiles

Tile data is stored in a sqlite db in `generations/<map-name>`. This repo ships with a script to download a small subset of the Los Angeles map at `generations/tiny-los-angeles`. The default generation directory that will be used is defined by the `MAP_ID` environment variable (defaulting to `tiny-los-angeles` in the .env file template).

```bash
uv run python src/isometric_los_angeles/download_generation.py tiny-los-angeles
```

If you'd like to download the full Los Angeles tile dataset, follow the *Full Dataset* instructions at the bottom of this README.

## Creating the DZI tiles

The web application uses OpenSeaDragon and the DZI tile viewer format. This repo ships with a pre-computed DZI image pyramid, but you can reconstruct it at any time by running the `export_dzi` script:

```bash
uv run python src/isometric_los_angeles/generation/export_dzi.py
```

## Web application

isometric los-angeles uses [`bun`](https://bun.com/) to build, manage, and run JavaScript and frontend apps. First, ensure that `bun` is installed.

You can run the isometric los-angeles web application with the following command:

```
cd src/app
bun i
bun run dev
```

The web app will run and point to the dzi image pyramid at `src/app/public/dzi/<MAP_ID>` (with `MAP_ID` corresponding to the `MAP_ID` .env variable, defaulting to `tiny-los-angeles`)

See the web application [docs](docs/app.md) for more information.

---

## Full Dataset

In order to download and initialize the full Los Angeles tiles dataset, you'll need to load the data from [oxen.ai](https://oxen.ai).

```bash
cd oxen/datasets
oxen clone https://hub.oxen.ai/cannoneyed/isometric-los-angeles-tiles
```

Then, you'll need to populate the generations dir with the downloaded png files

```bash
# From the repo root
uv run python src/isometric_los_angeles/oxen_sync/import_from_oxen.py --generations_dir los-angeles --oxen_dataset oxen/isometric-los-angeles-tiles
```

This will populate the `generations/los-angeles/quadrants.db` with the data and metadata for the generation. You can then create the DZI tiles for the new generations database using the instructions above. Ensure you set the MAP_ID env variable to use the new `los-angeles` generations dir by default.

```bash
# .env
MAP_ID="los-angeles"  # The full map generations dir
```

```bash
uv run python src/isometric_los_angeles/generation/export_dzi.py
```

Then, you can start up the web app with the new local dzi tiles for the full map.

```bash
cd src/app
bun run dev
```
