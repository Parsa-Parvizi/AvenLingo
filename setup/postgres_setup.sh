#!/bin/bash

DB_NAME=$1
DB_USER=$2
DB_PASS=$3

if [ -z "$DB_NAME" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASS" ]; then
  echo "Usage: $0 <db_name> <db_user> <db_password>"
  exit 1
fi

# ساخت دیتابیس و یوزر در دیتابیس postgres
sudo -i -u postgres psql -v ON_ERROR_STOP=1 <<EOF
DO
\$do\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME') THEN
      CREATE DATABASE $DB_NAME;
      RAISE NOTICE 'Database \"$DB_NAME\" created.';
   ELSE
      RAISE NOTICE 'Database \"$DB_NAME\" already exists.';
   END IF;
END
\$do\$;

DO
\$do\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$DB_USER') THEN
      CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';
      RAISE NOTICE 'User \"$DB_USER\" created.';
   ELSE
      RAISE NOTICE 'User \"$DB_USER\" already exists.';
   END IF;
END
\$do\$;

GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF

# دادن دسترسی‌های schema در دیتابیس مورد نظر
sudo -i -u postgres psql -v ON_ERROR_STOP=1 -d $DB_NAME <<EOF
GRANT ALL PRIVILEGES ON SCHEMA public TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
EOF

echo "Setup completed."
