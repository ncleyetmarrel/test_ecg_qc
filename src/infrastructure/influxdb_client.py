from influxdb import InfluxDBClient


def connect_client_to_db(client: InfluxDBClient, dbname: str) -> None:
    dbs = client.get_list_database()
    if dbname not in [d['name'] for d in dbs if 'name' in d]:
        print(f"Creating database {dbname}.")
        client.create_database(dbname)
    client.switch_database(dbname)
