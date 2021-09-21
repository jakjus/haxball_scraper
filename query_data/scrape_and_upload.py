import time
import os
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import math
import mysql.connector
from mysql.connector import errorcode

options = Options()
options.headless = True
driver = webdriver.Firefox(options=options)

base_url = 'https://www.haxball.com/play'


def scrape():
    out = []
    names = []
    driver.get(base_url)
    time.sleep(1)  # would be sweet to use selenium waits
    driver.switch_to.frame(0)
    driver.find_element_by_xpath("//input[1]").send_keys('o')
    time.sleep(1)
    driver.find_element_by_xpath("//button[@data-hook='ok']").click()
    time.sleep(1)

    desctop = driver.find_element_by_xpath(
        "//p[@data-hook='count']").text.split(' ')
    total_players = desctop[0]
    total_rooms = desctop[3]

    print('Scrolling room list started...')
    split = 15
    for i in range(math.ceil(int(total_rooms)/split)):
        driver.switch_to.default_content()
        splitnow = i*15
        js_scroll = 'document.getElementsByClassName("gameframe")[0]\
                .contentWindow.document.getElementsByTagName("tbody")[0]\
                .childNodes['+str(splitnow)+'].scrollIntoView()'
        driver.execute_script(js_scroll)
        driver.switch_to.frame(0)
        table = driver.find_element_by_xpath("//tbody[@data-hook='list']")
        ll = table.find_elements_by_tag_name('tr')
        for el in ll:
            try:
                pl = el.find_elements_by_tag_name("td")[1].text
                if len(pl) < 3:
                    continue
                (players_now, players_max) = pl.split('/')
                name = el.find_elements_by_tag_name("td")[0].text
                password = el.find_elements_by_tag_name("td")[2].text
                if password == 'Yes':
                    password = 1
                else:
                    password = 0
                flag = el.find_elements_by_tag_name("td")[3]\
                    .find_element_by_tag_name("div")\
                    .get_attribute('class')[-2:]

                d = {'name': name,
                     'players_now': players_now,
                     'players_max': players_max,
                     'password': password,
                     'flag': flag
                     }
                if name not in names:
                    out.append(d)
                    names.append(name)
            except Exception as e:
                print(e)
                continue

    print('Scrolling room list finished.')
    out2 = {'total_players': total_players, 'total_rooms': total_rooms}
    return {'server_details': out, 'global_info': out2}


def insert_into_db(server_details, global_info):
    cnx = mysql.connector.connect(
        user='root',
        password=os.environ['MYSQL_ROOT_PASSWORD'],
        host='mariadb',
        use_unicode=True,
        charset='utf8mb4')
    cnx.set_charset_collation('utf8mb4')
    cursor = cnx.cursor()

    DB_NAME = 'haxball'

    TABLES = {}
    TABLES['servers'] = (
        "CREATE TABLE `servers` ("
        "  `id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `name` TINYTEXT character set utf8mb4 UNIQUE,"
        "  `flag` varchar(2),"
        "  PRIMARY KEY (`id`)"
        ") ENGINE=InnoDB")

    TABLES['players'] = (
        "CREATE TABLE `players` ("
        "  `id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `server_id` int(11),"
        "  `players_now` int(11),"
        "  `players_max` int(11),"
        "  `date` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),"
        "  CONSTRAINT `fk_players_servers`"
        "  FOREIGN KEY (`server_id`) REFERENCES servers (`id`)"
        "  ON DELETE SET NULL,"
        "  PRIMARY KEY (`id`)"
        ") ENGINE=InnoDB")

    TABLES['total'] = (
        "CREATE TABLE `total` ("
        "  `id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `players_now` int(11),"
        "  `rooms_now` int(11),"
        "  `date` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),"
        "  PRIMARY KEY (`id`)"
        ") ENGINE=InnoDB")

    def create_database(cursor):
        try:
            cursor.execute(
                "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))
        except mysql.connector.Error as err:
            print("Failed creating database: {}".format(err))
            exit(1)

    try:
        cursor.execute("USE {}".format(DB_NAME))
    except mysql.connector.Error as err:
        print("Database {} does not exists.".format(DB_NAME))
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            create_database(cursor)
            print("Database {} created successfully.".format(DB_NAME))
            cnx.database = DB_NAME
        else:
            print(err)
            exit(1)

    for table_name in TABLES:
        table_description = TABLES[table_name]
        try:
            print("Creating table {}: ".format(table_name), end='')
            cursor.execute(table_description)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("already exists.")
            else:
                print(err.msg)
        else:
            print("OK")

    add_server = ("INSERT IGNORE INTO `servers` "
                  "(name, flag) "
                  "VALUES (%s, %s)")

    serv_no = cursor.lastrowid

    add_players = ("INSERT INTO `players` "
                   "(server_id, players_now, players_max, date) "
                   "VALUES (%s, %s, %s, %s)")

    add_total = ("INSERT INTO `total` "
                 "(players_now, rooms_now) "
                 "VALUES (%s, %s)")

    find_id = ("SELECT id FROM servers WHERE name=%s COLLATE utf8mb4_general_ci")
    date = time.strftime('%Y-%m-%d %H:%M:%S')

    try:
        for one in server_details:
            cursor.execute(add_server, (one['name'], one['flag']))
            cnx.commit()
            cursor.execute(find_id, (one['name'],))
            for el in cursor:
                serv_no = el[0]
            cursor.execute(
                add_players, (serv_no, one['players_now'], one['players_max'], date))
            cnx.commit()
        cursor.execute(
            add_total, (global_info['total_players'], global_info['total_rooms']))
        cnx.commit()
        cursor.close()
        cnx.close()
    except Exception as e:
        print(e)
        cursor.close()
        cnx.close()
        raise
    print('Process finished.')


def cycle():
    data = scrape()
    insert_into_db(data['server_details'], data['global_info'])


if __name__ == "__main__":
    while True:
        cycle()
        time.sleep(60*5)
