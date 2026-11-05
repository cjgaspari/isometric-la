## Isometric city whitebox generation

We will implement a system to generate isometric city whitebox images from the data in the map_data directory.

* Building footprints for Los Angeles: https://geohub.lacity.org/datasets/813fcefde1f64b209103107b26a8909f_0

### 3D City DB

* 3D City DB: https://github.com/3dcitydb
* Import CityGML / LoD2 building models for Los Angeles into 3DCityDB when available locally under `map_data/3dcitydb`.

Installing Docker
Installing the 3DCityDB docker image: https://docs.3dcitydb.org/1.1/3dcitydb/docker

```bash
docker pull 3dcitydb/3dcitydb-pg
```

```bash
docker run --name 3dciytdb -p 5432:5432 -d \
    -e POSTGRES_PASSWORD=isometric-los-angeles \
    -e SRID=25832 \
    -e POSTGRES_DB=isometric-los-angeles \
    -e POSTGRES_USER=isometric-los-angeles \
    -e POSTGIS_SFCGAL=true \
    3dcitydb/3dcitydb-pg
```

Docker Container ID: 61c785d1d8c93cb6e15d9c317cc2560a53ed8a93325db7f295fc1f22464719d3


Now installing the `citdyb-tool` - https://github.com/3dcitydb/citydb-tool

Also installing as a docker image!

```
docker pull 3dcitydb/citydb-tool
```

From the github repo:

> The Docker image exposes the commands of the citydb-tool, as described in the usage section. The environment variables listed below can be used to specify a 3DCityDB v5 connection. To exchange data with the container, mount a host folder to /data inside the container.

```
docker run --rm --name citydb-tool -it \
    -e CITYDB_HOST=host.docker.internal \
    -e CITYDB_PORT=5432 \
    -e CITYDB_NAME=isometric-los-angeles \
    -e CITYDB_USERNAME=isometric-los-angeles \
    -e CITYDB_PASSWORD=isometric-los-angeles \
    -v /Users/andycoenen/cannoneyed/isometric-los-angeles/map_data/3dcitydb:/data \
    3dcitydb/citydb-tool connect
```

Connection successful! Let's try importing the data

```
docker run --rm --name citydb-tool -it \
    -e CITYDB_HOST=host.docker.internal \
    -e CITYDB_PORT=5432 \
    -e CITYDB_NAME=isometric-los-angeles \
    -e CITYDB_USERNAME=isometric-los-angeles \
    -e CITYDB_PASSWORD=isometric-los-angeles \
    -v /Users/andycoenen/cannoneyed/isometric-los-angeles/map_data/3dcitydb:/data \
    3dcitydb/citydb-tool import citygml /data/LosAngeles_Buildings_LoD2_CityGML.gml
```
