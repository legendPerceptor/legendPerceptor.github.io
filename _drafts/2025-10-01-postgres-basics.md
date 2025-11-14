---
title: Postgres basics
author: yuanjian
date: 2025-10-01 14:34:00 +0800
categories: [Tutorial]
tags: [postgres, PostgreSQL, database]
pin: false
---

The goal of this article is to build postgres from source and play it with some basic functionalities to better prepare us for PostgreSQL development or gain a better understanding of the code base.

## 1. Compile postgres and configure the environment

We can obtain any release version of postgres' source code from [Postgres ftp source](https://www.postgresql.org/ftp/source/). We can also get the code from [Postgres' Github Repo](https://github.com/postgres/postgres) via `git clone`. This article is written on October 1, 2025. The latest version of Postgres is 18.0, and we will use that as an example.

We can build postgres in a dedicated folder and install it to somewhere in the user space without root priviledges.

```bash
# start from the root folder of postgres' source code
mkdir build
cd build
../configure --prefix='your/install/folder'
make
make install
```

If the configuration failed, it is likely you do not have the `libicu` or `libicu-devel` package in the system. We can use the following commands to fix the problem.

```bash
# for Ubuntu
sudo apt install 
# for RedHat/CentOS/EulerOS
sudo yum install libicu libicu-devel
# for macOS
brew install icu4c
```

For macOS, we need to set an environment variable `PKG_CONFIG_PATH` to help `./configure` find the package.

```bash
# on fish shell
if not contains (brew --prefix icu4c)/lib/pkgconfig $PKG_CONFIG_PATH
    set -x PKG_CONFIG_PATH (brew --prefix icu4c)/lib/pkgconfig $PKG_CONFIG_PATH
end

# on bash shell
export PKG_CONFIG_PATH=$(brew --prefix icu4c)/lib/pkgconfig:$PKG_CONFIG_PATH
```

After you successfully compiled and installed Postgres, we need to set `PATH`, `LDFLAGS`, `CPPFLAGS` and `DYLD_LIBRARY_PATH` (this will be `LD_LIBRARY_PATH` on linux) to use postgres commands without absolute paths.

```bash
# on fish shell (assume on macOS)
set -x POSTGRES_HOME "/your/postgres/install/folder"
set -gx DYLD_LIBRARY_PATH "$POSTGRES_HOME/lib"
set -gx LDFLAGS "-L$POSTGRES_HOME/lib"
set -gx CPPFLAGS "-I$POSTGRES_HOME/include"
fish_add_path $POSTGRES_HOME/bin

# on bash shell (assume on Linux)
export POSTGRES_HOME="/your/postgres/install/folder"
export LD_LIBRARY_PATH="$POSTGRES_HOME/lib"
export LDFLAGS="-L$POSTGRES_HOME/lib":$LDFLAGS
export CPPFLAGS="-I$POSTGRES_HOME/include"
export PATH=$POSTGRES_HOME/bin:$PATH
```

If `psql`, `createdb` commands exist after you source your config file, your postgres should have been installed correclty.

To view source code in VS Code without a bunch of include errors, we need to put the following makefile-tools configuration in `settings.json` under `.vscode` folder.

```json
{
  "C_Cpp.default.configurationProvider": "ms-vscode.makefile-tools",
}
```

## 2. Create a postgres role and load the dvdrental database

First of all, we need to intialize the postgres database in a desired folder, and start the server.

```bash
# Set $PGDATA beforehand to your desired folder for postgres to store data
initdb -D $PGDATA

# Start the postgres server
pg_ctrl -D $PGDATA start
```

Then we create a role called `postgres` to manage databases.

```bash
psql -d postgres

# in postgres commandline interface
# create a role postgres as a superuser
CREATE ROLE postgres WITH LOGIN SUPERUSER PASSWORD 'your_password'
```

We will use the dvdrental data to play with Postgres.

Get the dvdrental example database from [dvdrental GitHub Repo](https://github.com/robconery/dvdrental) and load it into our newly created postgres' dvdrental database.

```bash
git clone https://github.com/robconery/dvdrental.git
cd dvdrental
createdb dvdrental
pg_restore -d dvdrental ./dvdrental.tar
```

Now you can connect to the database and show some information about the imported database.

```bash
psql -d dvdrental -U postgres
```

Inside Postgres, we can use `\l` to list existing databases, `\c` to connect to certain database and `\dt` to list all tables in the current database. For instance, you may see output similar to the following.

```txt
dvdrental=# \l
                                                          List of databases
   Name    |    Owner    | Encoding | Locale Provider |   Collate   |    Ctype    | Locale | ICU Rules |      Access privileges      
-----------+-------------+----------+-----------------+-------------+-------------+--------+-----------+-----------------------------
 dvdrental | yuanjianliu | UTF8     | libc            | en_US.UTF-8 | en_US.UTF-8 |        |           | 
 postgres  | yuanjianliu | UTF8     | libc            | en_US.UTF-8 | en_US.UTF-8 |        |           | 
 template0 | yuanjianliu | UTF8     | libc            | en_US.UTF-8 | en_US.UTF-8 |        |           | =c/yuanjianliu             +
           |             |          |                 |             |             |        |           | yuanjianliu=CTc/yuanjianliu
 template1 | yuanjianliu | UTF8     | libc            | en_US.UTF-8 | en_US.UTF-8 |        |           | =c/yuanjianliu             +
           |             |          |                 |             |             |        |           | yuanjianliu=CTc/yuanjianliu
(4 rows)

dvdrental=# \c
You are now connected to database "dvdrental" as user "postgres".
dvdrental=# \dt
              List of tables
 Schema |     Name      | Type  |  Owner   
--------+---------------+-------+----------
 public | actor         | table | postgres
 public | address       | table | postgres
 public | category      | table | postgres
 public | city          | table | postgres
 public | country       | table | postgres
 public | customer      | table | postgres
 public | film          | table | postgres
 public | film_actor    | table | postgres
 public | film_category | table | postgres
 public | inventory     | table | postgres
 public | language      | table | postgres
 public | payment       | table | postgres
 public | rental        | table | postgres
 public | staff         | table | postgres
 public | store         | table | postgres
(15 rows)
```

The database is ready, and now let's learn some basic SQL query to interact with the database.

## 3. Play with the dvdrental database

