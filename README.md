# SCOAP3 [![Build Status](https://travis-ci.org/SCOAP3/scoap3-next.svg?branch=master)](https://travis-ci.org/SCOAP3/scoap3-next)
[www.scoap3.org](https://scoap3.org)

SCOAP3 is a one-of-its-kind partnership of over three-thousand libraries, key funding agencies and research centers in 43 countries and 3 intergovernmental organizations. Working with leading publishers, SCOAP3 has converted key journals in the field of high-energy physics to open access at no cost for authors. SCOAP3 centrally pays publishers for costs involved in providing their services, publishers, in turn, reduce subscription fees to all their customers, who can redirect these funds to contribute to SCOAP3. Each country contributes in a way commensurate to its scientific output in the field. In addition, existing open access journals are also centrally supported, removing any existing financial barrier for authors.

SCOAP3 journals are open for any scientist to publish without any financial barriers. Copyright stays with authors, and a permissive [CC-BY](https://creativecommons.org/licenses/by/4.0/) license allows text- and data-mining. SCOAP3 addresses open access mandates at no burden for authors. All articles appear in the SCOAP3 repository for further distribution, as well as being open access on publishers’ websites.


## Installation

* create a virtualenv with Python 2.7
* git clone this repo
* `git clone https://github.com/SCOAP3/hepcrawl.git` (used to be in requirements, add it outside for ease of use)
* `export DOCKER_DATA=<docker-data-path>`
* `pip install -r requirements.txt`
* `pip install -e .` (to make scoap executable)
* change path to hepcrawl and do the above command again
* `pip install inspire-schemas==59.0.5` because hepcrawl breaks it

Run `scoap3 --help` to check out if it was installed correctly (after running `docker-compose up`)

Then go to the hepcrawl installation and make the following changes to the repo:

#### At `hepcrawl/settings.py`:

* Comment out the `ELSEVIER_` parameters and replace them with paths that are reachable without sudo, and then make sure to create those paths, i.e.
    * ELSEVIER_SOURCE_DIR = "/Users/iliaskoutsakis/elsevier-sftp"
    * ELSEVIER_DOWNLOAD_DIR = "/Users/iliaskoutsakis/elsevier-sftp/download"
    * ELSEVIER_UNPACK_FOLDER = "/Users/iliaskoutsakis/elsevier-sftp/unpack"
* Also change the `LAST_RUNS_PATH`:
```python
LAST_RUNS_PATH = os.environ.get(
    'APP_LAST_RUNS_PATH',
    '/Users/iliaskoutsakis/elsevier-sftp/last_run'
)
```
* And add `os.environ['SCRAPY_FEED_URI']="/tmp/scrapy_feed.json"`


#### At `hepcrawl/scrapyd.cfg`:

Uncomment everything and add `items` to the `items_dir` parameter

### Environment vars

Add the following in your .zshrc or export them in the terminal (everything that was supposed to be in the docker instance, with some changes for localhost):

```shell script
export APP_SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://scoap3:dbpass123@localhost:5432/scoap3

# celery has issues, so i am leaving the defaults here
export APP_CELERY_BROKER_URL=pyamqp://guest:guest@rabbitmq:5672//
export APP_CELERY_RESULT_BACKEND=redis://redis:6379/1
export CELERY_BROKER_URL=pyamqp://guest:guest@rabbitmq:5672//
export CELERY_RESULT_BACKEND=redis://redis:6379/1

export APP_CACHE_REDIS_URL=redis://redis:6379/0
export APP_ACCOUNTS_SESSION_REDIS_URL=redis://redis:6379/2

export APP_SEARCH_ELASTIC_HOSTS=indexer
export APP_ES_BULK_TIMEOUT=240

export APP_CRAWLER_HOST_URL=http://localhost:6800
export APP_CRAWLER_API_PIPELINE_URL=http://localhost:5555/api/task/async-apply
export APP_LAST_RUNS_PATH=.lastruns
```


## Running

* Docker should be running already
* Open a new terminal, choose the scoap virtualenv, go to the `hepcrawl` folder and run the command `scrapyd`
* Then (in another termianl) change path to `hepcrawl/hepcrawl` (the main folder) and run `scrapyd-deploy`
* if all went well, then at the url `http://127.0.0.1:6800/` you should be able to see 2 projects: hepcrawl and default
* You can also check if it is accepting requests by using this url in the browser, it should show a few spiders and the host name (of your computer): `http://localhost:6800/listspiders.json?project=hepcrawl`

To create the db just run `scoap3 db init` and `scoap3 db create`.

Then create a folder that has the required tar files and run `scoap3 harvest elsevier --source_folder <path-to-tars>`.
The task should run, and you should see the request in the scrapyd window.
Also, you can check the logs in the scrapyd browser, `http://127.0.0.1:6800/`, where you can see that it ran, exported the data, and then failed in the end.

## TODO
Fix celery and see if this works.