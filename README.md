# Isometric Los Angeles

# isometric-los-angeles

This is the codebase for generating an isometric pixel-art map of Los Angeles. It is adapted from the open-source [isometric-nyc](https://github.com/cannoneyed/isometric-nyc) project by Andy Coenen.

## The Idea

Growing up, I played a lot of video games, and my favorites were world building games like SimCity 2000 and Rollercoaster Tycoon. As a core millennial rapidly approaching middle age, I’m a sucker for the nostalgic vibes of those late 90s / early 2000s games. As I stared out at the city, I couldn’t help but imagine what it would look like in the style of those childhood memories.

So here’s the idea: Make a giant isometric pixel-art map of Los Angeles. And I’m going to use it as an excuse to push hard on the limits of the latest and greatest generative models and coding agents.

## The Codebase (⚠️ Warning! ⚠️)

This codebase was built entirely via collaboration with coding agents such as [`gemini-cli`](https://geminicli.com/), [`Claude Code`](https://code.claude.com/docs/en/overview), and [`Cursor`](https://cursor.com/). As such, the code probably sucks. Honestly, I've looked at less than 1% of it, and I didn't write any of it by hand. YMMV, but because this was partly an exercise in pushing "vibe-engineering" to its limits I bought fully into the "hands-off" approach and the results speak for themselves.

Some of this cruft is still around, and will likely never get around to getting cleaned up.

I also used a lot of services to help bring this project to life, some of which are cheap, but aren't cheap to run at scale. I've tried to set things up so that they'll more or less just work, but it might be a bit rough until things mature more. That said, if you're ok with hacking around on this and finding all those rough edges, go ahead and get started.

## Getting Started

The easiest way to get started is to run the web app with the production data served from R2.

```bash
cd src/app

# Install dependencies
bun install

# Start development server (pointed at R2 Production Los Angeles tiles data)
USE_R2_LOS_ANGELES=true bun run dev
```

If you open the app at [http://localhost:3000](http://localhost:3000) you'll be able to interact with the real, production data.

## Docs

* **[Setup](docs/setup.md)** For setting up and downloading sample/full city data
* **[App](docs/app.md)** For the tiled image viewer web app
* **[Bounds](docs/bounds.md)** For the city bounds editor
* **[Data](docs/data.md)** A description of the various datasets and tile data management
* **[Deployment](docs/deployment.md)** How the production app is deployed
* **[Generation](docs/generation.md)** How to generate new tiles
* **[Generation approaches](docs/generation_approaches.md)** NYC vs London/Toronto methods and options for Los Angeles
* **[Local Mac setup](docs/local_mac_setup.md)** On-device Apple Silicon hardware + software spec
* **[Inference](inference/README.md)** How to set up custom fine-tuned model inference on Modal
* **[Water Shader](docs/water_shader.md)** The WIP water shader documentation

## Project Structure

```
isometric-los-angeles/
├── src/
│   ├── app/                 # Web viewer (React + OpenSeaDragon)
│   ├── isometric_los_angeles/       # Core libraries + workflows
│   ├── demos/               # Demos for WIP features (e.g. Water Shader)
│   └── web/                 # 3D map tiles data viewer / renderer (Three.js)
└── tasks/                   # Tasks for agents
```


## Development

| Task                  | Command                                     |
| --------------------- | ------------------------------------------- |
| Run Python tests      | `uv run pytest`                             |
| Format Python code    | `uv run ruff format .`                      |
| Lint Python code      | `uv run ruff check .`                       |
| Run web app           | `cd src/app && bun run dev`                 |
| Build web app         | `cd src/app && bun run build`               |

---
