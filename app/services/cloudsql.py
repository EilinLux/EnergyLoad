import sqlalchemy, pymysql, logging, sys, os

environment = os.environ.get("ENVIRONMENT")
public_ip_database = os.environ.get("_CLOUD_SQL_INSTANCE_CONNECTION_NAME")


class CloudSql:
    def raw_connect(self, cloud_sql_instance_connection_name, db_user,
                    db_pass):
        """Open database connection using raw pymysql."""
        logging.debug(
            f"Contacting {cloud_sql_instance_connection_name} with {db_user}:{db_pass}..."
        )
        params = {
            'user': db_user,
            'password': db_pass,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor,
            'autocommit': False,
            'unix_socket': f'/cloudsql/{cloud_sql_instance_connection_name}'
        }
        return pymysql.connect(**params)

    def local_connect(self, db_user, db_pass):
        """Open database connection using raw pymysql."""
        logging.debug(f"Contacting database from local environment...")
        params = {
            'user': db_user,
            'password': db_pass,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor,
            'autocommit': False,
            'host': public_ip_database
        }
        return pymysql.connect(**params)

    def connect(self, cloud_sql_instance_connection_name, db_user, db_pass):
        """Connect to the database depending on environment"""

        if environment and environment == "local":
            return self.local_connect(db_user, db_pass)
        else:
            return self.raw_connect(cloud_sql_instance_connection_name,
                                    db_user, db_pass)
