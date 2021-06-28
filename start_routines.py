#!/bin/python

import os
import mysql.connector
import configparser

from datetime import date

CONFIGS = configparser.ConfigParser(interpolation=None)
PATH_CONFIG_FILE = os.path.join(os.path.dirname(__file__), '', 'config.ini')
if os.path.exists( PATH_CONFIG_FILE ):
    CONFIGS.read(PATH_CONFIG_FILE)
else:
    raise Exception(f"config file not found: {PATH_CONFIG_FILE}")
DATABASE = CONFIGS['MYSQL']['DATABASE']
TABLE_SESSIONS = "emails"
mydb = None
mysqlcursor = None

# A little bit too extensive
columns = {
        "id": "VARCHAR(255) NOT NULL PRIMARY KEY",
        "_from": "VARCHAR(512) NOT NULL",
        "_to": "VARCHAR(255) NOT NULL",
        "subject": "VARCHAR(1028) NOT NULL",
        "encoding": "VARCHAR(64) NOT NULL",
        "content_transfer_encoding": "VARCHAR(64) NULL",
        "body": "TEXT", 
        "date": "VARCHAR(64) NOT NULL",
        "meta_date": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "meta_mdate": "TIMESTAMP on update CURRENT_TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"
    }


def create_database(mysqlcursor, name :str ):
    mysqlcursor.execute(f"CREATE DATABASE {name}")

def check_tables(DATABASE, TABLE, custom_columns):
    global mysqlcursor
    supplus = []
    minus = []
    try:
        mysqlcursor.execute(f"SHOW COLUMNS FROM {TABLE}")
        cols = mysqlcursor.fetchall()
        cols = [list(col)[0] for col in cols]
        value = True
        for col in cols:
            if col not in custom_columns.keys():
                supplus.append( col )
                value = False

        col_keys = list(custom_columns.keys())
        # print( cols )
        for col in col_keys:
            # print(f"{col} ---> {cols}")
            if col not in cols:
                print("[+] Appending minus...", custom_columns[col])
                minus.append( [col,custom_columns[col]] )
                value = False
    except mysql.connector.Error as err:
        raise Exception( err )
    return_value= {"value": value, "extra": supplus, "missing": minus}
    # print( return_value )
    return return_value

def create_table( mysqlcursor, DATABASE, TABLE, custom_columns):
    # TODO: Maybe add a value to account for test SMS messages
    statement = f"CREATE TABLE {TABLE} ("
    comma=False
    for col in custom_columns:
        if comma:
            statement+=','
        statement += f"{col} {custom_columns[col]}"
        comma=True
    statement += ")"
    '''
    if TABLE == "messages":
        statement += ",PRIMARY KEY(id), UNIQUE(other_id))"
    else:
        statement += ",PRIMARY KEY(id))"
    '''
    # print( statement )
    try:
        mysqlcursor.execute( statement )
    except mysql.connector.Error as err:
        raise Exception( err )

def alter_table( DATABASE, TABLE, alters ):
    global mysqlcursor
    for alter in alters:
        statement = f"ALTER TABLE {TABLE} ADD COLUMN {alter[0]} {alter[1]}"
        print(f"[+] Altering with: {statement}")
        try:
            mysqlcursor.execute( statement )
            mydb.commit( )
        except mysql.connector.Error as err:
            raise Exception( err )

def set_connection( host, user, password, database=None):
    global mysqlcursor, mydb
    mydb = mysql.connector.connect( host= host, user= user, password= password, database=database, auth_plugin='mysql_native_password')
    mysqlcursor = mydb.cursor()

def insert_default_route( router_url):
    query = f"INSERT INTO configs SET router_url={router_url}"
    try:
        mysqlcursor.execute( query )
        mydb.commit( )
    except mysql.connector.Error as err:
        raise Exception( err )

# CHECK DATABASE
def sr_database_checks():
    global mysqlcursor, mydb

    HOST = CONFIGS["MYSQL"]["HOST"]
    USER = CONFIGS["MYSQL"]["USER"]
    PASSWORD = CONFIGS["MYSQL"]["PASSWORD"]
    set_connection(host=HOST, user=USER, password=PASSWORD)

    mysqlcursor = mydb.cursor()
    mysqlcursor.execute("SHOW DATABASES")

    databases = []
    for database in mysqlcursor:
        databases.append(list(database)[0])

    print(">> Checking Databases....")
    if DATABASE in databases:
        print("\t>> Database found")
    else:
        print("\t>> Database not found")
        # Do something about it
        try:
            create_database( mysqlcursor, CONFIGS['MYSQL']['DATABASE'])
            print("\t[+] Database created!")
        except Exception as error:
            print( error )


    list_tables = {TABLE_SESSIONS:columns}
    # CHECK TABLES
    set_connection(host=HOST, user=USER, password=PASSWORD, database=DATABASE)
    # TODO: Check if connected
    mysqlcursor = mydb.cursor()
    mysqlcursor.execute("SHOW TABLES")
    tables = []
    for table in mysqlcursor:
        tables.append(list(table)[0])

    for TABLE in list_tables:
        print(">> Checking Tables...")
        if TABLE in tables:
            print(f"\t>> Table found <<{TABLE}>>")
            check_state = check_tables( DATABASE, TABLE, list_tables[TABLE])
            # if not check_state["value"]:
            if not check_state["value"]:
                # Do something like repair or rebuild entire table
                print("\t>> Table does not match with requirements")
                print(f"\t>> {check_state}")
                try:
                    alter_table( DATABASE, TABLE, check_state["missing"] )
                    print("\t[+] Changes to table added!")
                except Exception as err:
                    raise Exception( err)
        else:
            print(f"\t>> Table not found <<{TABLE}>>")
            # Do something about it
            try: 
                create_table( mysqlcursor, DATABASE, TABLE, list_tables[TABLE])
                print("\t[+] Table created!")
                if TABLE == "configs":
                    PATH_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'configs', 'config.ini')
                    if os.path.exists( PATH_CONFIG_FILE ):
                        CONFIGS.read(PATH_CONFIG_FILE)
                    else:
                        raise Exception(f"config file not found: {PATH_CONFIG_FILE}")
                    # CONFIGS.read("config.ini")
                    if "default" in CONFIGS["ROUTER"]:
                        insert_default_route(CONFIGS["ROUTER"]["default"])
            except Exception as error:
                raise Exception( error )

    # Insert default route


    mydb.close()
    return {"value": True}
