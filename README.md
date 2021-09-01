# SCOAP3 [![Build Status](https://travis-ci.org/SCOAP3/scoap3-next.svg?branch=master)](https://travis-ci.org/SCOAP3/scoap3-next)
[www.scoap3.org](https://scoap3.org)

SCOAP3 is a one-of-its-kind partnership of over three-thousand libraries, key funding agencies and research centers in 43 countries and 3 intergovernmental organizations. Working with leading publishers, SCOAP3 has converted key journals in the field of high-energy physics to open access at no cost for authors. SCOAP3 centrally pays publishers for costs involved in providing their services, publishers, in turn, reduce subscription fees to all their customers, who can redirect these funds to contribute to SCOAP3. Each country contributes in a way commensurate to its scientific output in the field. In addition, existing open access journals are also centrally supported, removing any existing financial barrier for authors.

SCOAP3 journals are open for any scientist to publish without any financial barriers. Copyright stays with authors, and a permissive [CC-BY](https://creativecommons.org/licenses/by/4.0/) license allows text- and data-mining. SCOAP3 addresses open access mandates at no burden for authors. All articles appear in the SCOAP3 repository for further distribution, as well as being open access on publishers’ websites.

 # Installation Instructions

## Docker

```shell
docker-compose up

# Initialize database
docker-compose exec web scripts/recreate_records

```
## Local

 First of all, keep in mind that we are creating a local environment here, so a lot of things that run on Docker,
 will run locally instead.

 ### First steps
 * Create a new virtualenv, install everything using `pip install -r requirements.txt` and `pip install -e .`
 * Make sure that redis and rabbitmq have open ports for local access (6379 and 5672)
 * Start the services (we keep ES, Redis, RabbitMQ and Postgres only) using `docker-compose up redis indexer database rabbitmq -d`
 * Make sure that you create a folder that will be used for everything related to this project. In this case, we will be using `~/docker_scoap_data`

 ---
 **NOTE**

 Sometimes, ES is almost at capacity and does not allow the user to modify or add data.
 To overcome this issue, use the following commands:

 ```shell
 curl -XPUT -H "Content-Type: application/json" http://localhost:9200/_all/_settings -d '{"index.blocks.read_only_allow_delete": null}'

 curl -XPUT -H "Content-Type: application/json" http://localhost:9200/_cluster/settings -d '{ "transient": { "cluster.routing.allocation.disk.threshold_enabled": false } }'
 ```

 ---

 Make sure that the correct environment variables are exported and visible to the services. An example is following:

 ```shell
 # db
 export APP_SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://scoap3:dbpass123@localhost:5432/scoap3

 # celery + redis, used for tasks
 export APP_CELERY_BROKER_URL=pyamqp://guest:guest@localhost:5672//
 export APP_CELERY_RESULT_BACKEND=redis://localhost:6379/1
 export CELERY_BROKER_URL=pyamqp://guest:guest@localhost:5672//
 export CELERY_RESULT_BACKEND=redis://localhost:6379/1
 export APP_CACHE_REDIS_URL=redis://localhost:6379/0
 export APP_ACCOUNTS_SESSION_REDIS_URL=redis://localhost:6379/2

 # es vars
 export APP_SEARCH_ELASTIC_HOSTS=localhost
 export APP_ES_BULK_TIMEOUT=240

 # crawler vars
 export APP_CRAWLER_HOST_URL=http://localhost:6800
 export APP_CRAWLER_API_PIPELINE_URL=http://localhost:5555/api/task/async-apply
 export APP_LAST_RUNS_PATH=.lastruns

 # ALWAYS FALSE - related to UI issues, doesn't build if True
 export APP_DEBUG=False
 export APP_ASSETS_DEBUG=False
 export ASSETS_DEBUG=False
 ```

 Some additional variables that are absolutely necessary, but can be defined by the user, are the following:

 ```shell
 export DOCKER_DATA=~/docker_scoap_data
 export HEPCRAWL_SOURCE=~/scoap-repos/scoap3-hepcrawl
 export APP_OAIHARVESTER_WORKDIR=~/docker_scoap_data/tmp/virtualenv/oaiharvest_workdir
 export SCRAPY_FEED_URI=~/docker_scoap_data/tmp/virtualenv/scrapy_feed.json
 export SCOAP_DEFAULT_LOCATION=~/docker_scoap_data/tmp/virtualenv/files/
 ```

 Make sure that hepcrawl is in the correct path, and running. After following the instructions above, start the services.


 ### Build scripts - db and search

 Scoap3 has some scripts that need to be used in order to run the project, along with specific things that need to be done to make them work locally:

 ```shell
 # This script recreates the db and the search indices
 sh scripts/recreate_records --no-populate
 ```

 After recreating the db, make sure that the `location` table is populated. In case it is not, you need to:

 * make sure that `SCOAP_DEFAULT_LOCATION` is exported and not empty
 * run `scoap3 fixdb init_default_location` to add the location in the db


 ### Build scripts - UI

 Sometimes NPM has issues in the installation process, and in that case try to install:

 ```shell
 sudo npm install -g node-sass clean-css clean-css-cli requirejs uglify-js --unsafe-perm=true --allow-root
 ```

 After that you should be able to run `sh scripts/clean_assets` with no problem at all.


 ### Local services

 You can run the last remaining components (the scoap3 project itself, and the celery worker) as
 local services using honcho `pip install honcho` and then `honcho start` in the main scoap3 path.
 Honcho will use the `Procfile` to see what services to start.

 ---
 **NOTE**

 As shown in the config `SERVER_NAME` var, you need to use an alias for the `localhost` to run without an issue.
 Go to the `etc/hosts` file and add `127.0.0.1   web` to the list of hosts. Now you can use `web:5000` in the browser to access
 the Scoap3 UI.

 ---

 ### Harvesting

 Now you should have the following:

 * Hepcrawl running (check the hepcrawl repo for instructions)
 * ES, Redis, RabbitMQ, DB running in Docker
 * Celery and Scoap3 running in Honcho

 You can now harvest articles following the rules and cli commands found in the `cli_harvest.py` file.
