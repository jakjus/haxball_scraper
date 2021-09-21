### Haxball Scraper

Haxball Scraper is a tool that uses Selenium (*Query Data*), scrolls through a room list in web game Haxball ([haxball.com](https://haxball.com)) and saves the data of all rooms and global stats to MariaDB.

Uses:
- MariaDB - storing data
- Adminer - reading data
- Query Data - scraping data

[_docker-compose.yml_](docker-compose.yml)
```
services:
  mariadb:
    image: mariadb:10.6
    ...
  adminer:
    image: adminer
    ports:
      - 8080:8080
    ...

  query_data:
    build: ./query_data
    ...
```
The compose file defines a stack with three services: `mariadb`, `adminer` and `query_data`.
When deploying the stack, docker-compose maps container ports to host ports. Make sure, that `port 8080` is not already in use.

## Requirements
- docker
- docker-compose

## Usage
Create `.env` file in root directory with the following content:
```
MYSQL_ROOT_PASSWORD=yoursecretpassword
```
Change `yoursecretpassword` to your own password.

 
Run stack:
```
docker-compose up -d
```

Listing containers must show three containers running and the port mapping:
```
docker ps
```

If containers are visible, navigate to `http://localhost:8080` in your web browser and use the login credentials 
- user: `root`
- password: from `.env` file 
- database name: `haxball`

to access the database.

*Note: Database may be empty if the first scrape was not finished*

Scrape process (`scrape_and_upload.py`) is being run chronically with 5 minutes cooldown by default.

👏 **Seems like you are getting all the juicy Haxball data. Sweet.**


If you got enough, stop and remove the containers. Use `-v` to remove the volumes if looking to erase all data.
```
$ docker-compose down -v
```

## Caveats
[scrape_data/scrape_and_upload.py](./scrape_data/scrape_and_upload.py)
```
199 if __name__ == "__main__":
200     while True:
201         cycle()
202         time.sleep(60*5)
```
1. Loop is endless by default. This way we minimize need for changing container environment in order to run cron processes, as well as outside of container (one level higher - as another service in stack).
2. Sleep time between executions is 5 minutes, but it **does not** mean, that the data is scraped every 5 minutes. The process itself takes around 3 minutes. Therefore, you will get data once every ~8 minutes.

[docker-compose.yml](docker-compose.yml)
```
  8     environment:
  9       MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
```
3. Stack is using only `root` database user. Consider altering the code in order to create suitable roles in the database.

## What's next?

Now you can only read data through `adminer`. Next step would be visualizing the data.

Add `grafana` to the stack in `docker-compose.yml`:

```
  grafana:
    image: grafana/grafana:main
    restart: always
    ports:
      - 3000:3000
    volumes:
      - grafana-storage:/var/lib/grafana
    environment:
      GF_AUTH_ANONYMOUS_ENABLED: "true"
      GF_AUTH_ANONYMOUS_HIDE_VERSION: "true"
      GF_AUTH_ANONYMOUS_ORG_NAME: something
```

Change volumes section to the following:
```
volumes:
  grafana-storage:
  mariadb-storage:
```

Next, navigate to https://localhost:3000 and connect to the Data Source. MariaDB will be accessible under URI `mariadb:3306` or just `mariadb`. Insert database user details and you should be good to go with making your own visualizations.

*Note: You would have to use root user as reader for Grafana, which is not recommended. Consider creating additional role to have a production-ready Grafana solution.*

## Contributions
Very welcome.

## License
[MIT](./LICENSE)
