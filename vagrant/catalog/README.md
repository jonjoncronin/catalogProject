<!-- TOC depthFrom:1 depthTo:6 withLinks:1 updateOnSave:1 orderedList:0 -->

- [Summary](#summary)
- [Requirements](#requirements)
	- [API Endpoints](#api-endpoints)
	- [CRUD: Read](#crud-read)
	- [CRUD: Create](#crud-create)
	- [CRUD: Update](#crud-update)
	- [CRUD: Delete](#crud-delete)
	- [Authentication and Authorization](#authentication-and-authorization)
	- [Code Quality](#code-quality)
	- [Comments](#comments)
	- [Documentation](#documentation)
- [High Level Design](#high-level-design)
- [Resources](#resources)
	- [application.py](#applicationpy)
	- [models.py](#modelspy)
	- [populateDummyDb.py](#populatedummydbpy)
	- [fb_client_secrets.json](#fbclientsecretsjson)
	- [google_client_secrets.json](#googleclientsecretsjson)
	- [HTML pages and CSS stylesheets](#html-pages-and-css-stylesheets)
- [Usage](#usage)

<!-- /TOC -->

# Summary
The Catalog App is a web application that provides a list of items within a
variety of categories as well as provide a user registration and authentication
system. Registered users will have the ability to view, create, edit and delete
their own items but can only view items added by other users.

The Catalog App is the 4th project laid out in the curriculum for the Udacity
Full Stack web developer Nanodegree.

# Requirements
## API Endpoints
  * The project implements a JSON endpoint that serves the same information as
    displayed in the HTML endpoints for an arbitrary item in the catalog.

## CRUD: Read
  * Website reads category and item information from a database.

## CRUD: Create
  * Website includes a form allowing users to add new items and correctly
	  processes submitted forms.

## CRUD: Update
  * Website does include a form to edit/update a current record in the database
    table and correctly processes submitted forms.

## CRUD: Delete
  * Website does include a function to delete a current record.

## Authentication and Authorization
  * Create, delete and update operations do consider authorization status prior
	  to execution.
  * Page implements a third-party authentication & authorization service
    (like Google Accounts or Mozilla Persona) instead of implementing its own
    authentication & authorization spec.
  * Make sure there is a 'Login' and 'Logout'
    button/link in the project. The aesthetics of this button/link is up to the
    discretion of the student.

## Code Quality
Code is ready for personal review and neatly formatted and compliant with the
Python PEP 8 style guide.

## Comments
Comments are present and effectively explain longer code procedures.

## Documentation
README file includes details of all the steps required to successfully run the
application.

# High Level Design
To meet the specifications laid out above, the Catalog App uses a sqlite
Database to keep track of items, categories and users. The main HTTP server is
a running python application that services page requests, handles user input for
logging in, logging out, and viewing items as well as allowing users to create,
update and delete items that they "own". Ownership in this case is not economic
owning or property but instead means they are the original creators of the items
in the database and have the authority to manage those items.

The site utilizes
  * the Flask micro web framework for backend HTTP Server support, user session
    management, and dynamic HTML page content creation
  * the sqlalchemy python library for backend SQL and object-relational mapper
    support
  * the oauth2client python library for accessing resources protected by
    OAuth 2.0

The site utilizes 2 different 3rd party authentication services to help users
register and login to the site. Users can sign up/sign in using either their
Facebook or Google account credentials. Authenticated users are authorized to
manage only the items that they have originally created.

The site has a responsive design and utilizes the W3.CSS framework to relieve
the developer from having to craft all the CSS stylesheet classes that allow
a responsive design.

The site provides 3 REST API endpoints that dump content in a JSON format when
requested via the HTTP protocol. These 3 endpoints will allow an external
caller to view the current table information for
 * all categories and their items in the database
 * all items in a specific category in the database
 * the details for a specific item in the database

# Resources
## application.py
The application.py module implements the main python application running the
HTTP server handling page requests and user inputs. It implements the logic for
accessing items from the database to be displayed on various pages on the site.
It also contains implementation for authenticating, adding users to the database
and logging them off. It implements the adding, updating, and deleting of items
managed by authenticated users. Further it handles the processing of REST API
requests, accessing items from the database and returning JSON formatted content
to the callers.

## models.py
The models.py module implements the data model for the Catalog Application. This
data model defines the Item, Category and User objects and the relationships
between them.

Users have items.
Categories have items.

## populateDummyDb.py
The populateDummyDb.py module implements a rather simple database population by
a single user to aid in the development process.

## fb_client_secrets.json
The fb_client_secrets.json file defines the required OAuth2 application ID and
secret that allows this Catalog web application to access the Facebook Login
API.

## google_client_secrets.json
The google_client_secrets.json file defines the required OAuth2 application ID
and secret that allows this Catalog web application to access the Google+ API.

## HTML pages and CSS stylesheets
The Flask micro web framework utilizes a python backend and HTML/CSS frontend
to provide a total website solution. The HTML pages are a mix between HTML and
Flask syntax that allow the application to dynamically render pages requested
by a user utilizing the site. The HTML pages define the content of the pages
displayed to the user while the CSS stylesheets define the styling of the pages
that the user sees.

There are HTML templates for -
  * showing all items - items.html
  * showing items in a specific category - categoryItems.html
  * logging into the application - authentication.html
  * creating a new item - new.html
  * editing a specific item - edit.html
  * deleting a specific item - delete.html

# Usage
Usage of this application assumes quite a bit.

Server administration is beyond the scope of this project and I will simply ask
you to refer to the pages from the Udacity site that describe how to "Prepare
the software and data" for this project. The quick summary is that you need a VM
running locally that has that has python installed with the following python
libraries installed
  * flask
  * oauth2client  
  * flask-httpauth
  * sqlalchemy
  * flask-sqlalchemy
  * requests

The HTTP server can be started by executing the application.py  
- Open a terminal window on the VM/server.
- Navigate to the location of the application.py script.
- Execute the script - $> python application.py

Your web application will now be hosted and running on that server reachable
via port 5000.

The CSS styling of the HTML pages will require external Internet Access as it
utilizes the W3.CSS CSS framework CDN, the Google Fonts CDN and the Font-Awesome
CDN. If you have isolated your webserver you will not see the pages rendered as
they are intended.

OPTIONAL -
The catalog database will be created locally on the server on the first instance
of the HTTP server being run/execute, but if you wish to pre-populate the
database you can run/execute the populateDummyDb.py script.

- Open a terminal window on the VM/server.
- Navigate to the location of the populateDummyDb.py script.
- Execute the script - $> python populateDummyDb.py
