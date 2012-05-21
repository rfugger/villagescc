Villages.cc
===========

Source for [Villages.cc](https://villages.cc/).  The code is licensed under the [AGPL v3](https://www.gnu.org/licenses/agpl-3.0.html).

A somewhat dated to-do list is at docs/todo.txt.

Installation
------------

[TODO: Better instructions!]

This is a Django project.  Among other things, you'll need:

* Python 2.6+
* Django 1.4
* PostgreSQL 8.3+, PostGIS 1.5, psycopg2 (may be able to configure for other DBs)
* Django-mediagenerator (incl. Sass, Compass)
* South
* Networkx

You'll need to create a file cc/settings/local.py containing the following Django settings:

* DATABASES
  * Need to create two dbs: 'default' and 'ripple'.  Default must be a postgis db.
* CACHES

You can also override other default settings.

There are some useful scripts in bin/.

Pull requests welcome!
