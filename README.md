DISCR
=============

Udacity Full Stack Nanodegree - Project 3 (RDB, oauth web application)

DISCR is a web application for Disc Golfers.
Registered users can add descriptions of their discs including a picture of the disc.
Each disc is unique to the account that added the disc, so every disc description is unique.

It is written primarily in Python making extensive use of the flask framework.
It uses sqlite as a local storage backend.
Users can register via Oauth 2.0 with their Facebook or Google+ account.

## Installation
Follow these instructions to setup your own local instance of DISCR.
A Vagrant file is included in the /vagrant directory for your convenience.
To spin up a local instance of DISCR follow these steps;
  1) clone this repo
  2) change to the 'item-cat-full-stack/vagrant' directory
  3) Add your own Facebook and Google+ oauth 2.0 AppID and keys to these files
     * vagrant/catalog/application/templates/login.html
     * vagrant/catalog/client_secrets.json
     * vagrant/catalog/fb_client_secrets.json
  4) $ vagrant init
  5) $ vagrant ssh
  6) $ cd /vagrant/catalog
  7) $ python runserver.py
  8) Open your favorite browser on the same machine and navigate to 'localhost:8000'
     - If that doesn't work try 127.0.0.1:8000

## Some words about structure
