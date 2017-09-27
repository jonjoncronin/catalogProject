#!/usr/local/bin/python3
"""
application.py -
This module is a standalone module intended to act as a webserver hosting
the site for a Catalog Item App.
This Catalog Item App is intended to allow users to maintain a list of items
that fall under a variety of categories. Both the item and the category it falls
under are user specified.
Currently an item is unique even if it falls under different categories - ie
you CANNOT have a ball under the category of baseball and a ball under the
category of soccer.
"""
from flask import Flask, render_template, url_for, request, redirect, flash, jsonify, g
from flask import session as login_session
from flask import make_response
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models import Base, Item, Category
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

import httplib2, random, string, json, requests


"""
Store off Google CLIENT_ID and APPLICATION_NAME
"""
CLIENT_ID = json.loads(
    open('google_client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Project Application"

"""
Create the connections and sessions to the catalog database
"""
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)


@app.route('/')
@app.route('/catalog/')
def showItems():
    """
    routes to showItems will render the initial home page that show all the
    items in the database and the categories they fall under.
    """
    categories = session.query(Category).order_by(Category.name).all()
    items = session.query(Item).order_by(Item.name)
    return render_template('items.html', items=items, categories=categories)

# @app.route('/catalog/category/<string:category_name>/')


@app.route('/catalog/category/<int:category_id>/')
def showItemsForCategory(category_id):
    """
    route to showItemsForCategory will render a page that shows the items
    associated with a specific category.
    """
    categories = session.query(Category).order_by(Category.name).all()
    targetCategory = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(
        category_id=category_id).order_by(Item.name)
    return render_template('categoryItems.html', items=items, categories=categories, targetCategory=targetCategory)


@app.route('/catalog/JSON')
def allItemsByAllCategoryJSON():
    """
    route to allItemsByAllCatagoryJSON will dump all the items in the database
    in JSON format ordered in a format that shows items per category.
    """
    categories = session.query(Category).order_by(Category.name).all()
    cate_dict = [entry.serialize for entry in categories]
    index = 0
    for entry in cate_dict:
        items = session.query(Item).filter_by(
            category_id=entry['id']).order_by(Item.name).all()
        items_dict = {'Item': [item.serialize for item in items]}
        cate_dict[index].update(items_dict)
        index += 1
    return jsonify(Category=cate_dict)


@app.route('/catalog/item/<int:item_id>/JSON')
def itemDetailsJSON(item_id):
    """
    route to itemDetailsJSON will dump all the details about a specific item in
    JSON format.
    """
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(Item=item.serialize)


@app.route('/catalog/category/JSON')
def allCategoriesJSON():
    """
    route to allCatagoriesJSON will dump all the categories in the database
    in JSON format ordered by name.
    """
    categories = session.query(Category).order_by(Category.name).all()
    return jsonify(Category=[entry.serialize for entry in categories])


@app.route('/catalog/item/new/', methods=['GET', 'POST'])
def newItem():
    """
    route to newItem will render a page to allow a user to create a new item
    through a web form and store it in the database.
    """
    if 'username' not in login_session:
        return redirect(url_for('showAuth'))

    categories = session.query(Category).order_by(Category.name).all()
    if request.method == 'POST':
        print(request.form)
        if request.form['name']:
            print("attempting to add item")
            try:
                existingItem = session.query(Item).filter_by(
                    name=request.form['name']).one()
                print(existingItem)
            except:
                existingItem = ""
                pass
            if not existingItem:
                try:
                    existingCategory = session.query(Category).filter_by(
                        name=request.form['category']).one()
                    print(existingCategory)
                except:
                    existingCategory = ""
                    pass
                if not existingCategory:
                    newCategory = Category(name=request.form['category'])
                    try:
                        session.add(newCategory)
                        # You think you need to commit this new category
                        # before adding the item because you need the unique
                        # id for the item -> category relationship.
                        # SqlAlchemy is smart enough to not need that commit
                        # call.
                        # session.commit()
                        existingCategory = session.query(Category).filter_by(
                            name=request.form['category']).one()
                    except:
                        print("Unable to add {0} category to the DB".format(
                            newCategory))
                        flash("Failed to add item {0}".format(request.form['name']))
                        return redirect(url_for('showItems'))

                newItem = Item(name=request.form['name'],
                               description=request.form['description'],
                               category_id=existingCategory.id)
                try:
                    session.add(newItem)
                    session.commit()
                except:
                    print("Unable to add {0} item to the DB".format(newItem))
                    flash("Failed to add item {0}".format(request.form['name']))
                    pass
            else:
                print("{0} already exists with category {1}".format(
                    request.form['name'], existingItem.category))
                flash("Failed to add item {0}".format(request.form['name']))
        flash("Item {0} added to the catalog".format(request.form['name']))
        return redirect(url_for('showItems'))
    else:
        return render_template('new.html', categories=categories)


@app.route('/catalog/item/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(item_id):
    """
    route to editItem will render a page to allow a user to edit a specific
    items category and/or description. Due to the table dependencies an edit
    will be processed as an delete->add action.
    """
    if 'username' not in login_session:
        return redirect(url_for('showAuth'))

    categories = session.query(Category).order_by(Category.name).all()
    editedItem = session.query(Item).filter_by(id=item_id).one()
    item_name = editedItem.name
    if request.method == 'POST':
        print("attempting to edit an item")
        print(request.form)

        # remove the previous item and cleanup any empty category
        category = editedItem.category
        session.delete(editedItem)
        # now check to see if the category needs to be removed
        itemsForCat = session.query(Item.id).join(Category).filter_by(name = category.name)
        count = session.query(func.count(itemsForCat)).scalar()
        print (count)
        if count == 0:
            try:
                session.delete(category)
            except:
                print("Unable to delete {0} from the DB".format(category))
                pass
        session.commit()

        # add the new item and category if they don't exist
        print("attempting to add item")
        try:
            existingItem = session.query(Item).filter_by(
                name=item_name).one()
            print(existingItem)
        except:
            existingItem = ""
            pass
        if not existingItem:
            try:
                existingCategory = session.query(Category).filter_by(
                    name=request.form['category']).one()
                print(existingCategory)
            except:
                existingCategory = ""
                pass
            if not existingCategory:
                newCategory = Category(name=request.form['category'])
                print(newCategory)
                try:
                    session.add(newCategory)
                    # You think you need to commit this new category
                    # before adding the item because you need the unique
                    # id for the item -> category relationship.
                    # SqlAlchemy is smart enough to not need that commit
                    # call.
                    # session.commit()
                    existingCategory = session.query(Category).filter_by(
                        name=request.form['category']).one()
                except:
                    print("Unable to add {0} category to the DB".format(
                        newCategory))
                    flash("Failed to edit item {0}".format(item_name))
                    return redirect(url_for('showItems'))

            newItem = Item(name=item_name,
                           description=request.form['description'],
                           category_id=existingCategory.id)
            try:
                session.add(newItem)
                session.commit()
            except:
                print("Unable to add {0} item to the DB".format(newItem))
                flash("Failed to edit item {0}".format(item_name))
                pass
        else:
            print("{0} already exists with category {1}".format(
                item_name, existingItem.category))
            flash("Failed to edit item {0}".format(item_name))
        flash("Item {0} has been modified".format(item_name))
        return redirect(url_for('showItems'))
    else:
        return render_template('edit.html', item=editedItem, categories=categories)


@app.route('/catalog/item/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(item_id):
    """
    route to deleteItem will render a page to prompt the user for confirmation
    that an item is to be deleted and performs the delete if confirmed.
    """
    if 'username' not in login_session:
        return redirect(url_for('showAuth'))

    categories = session.query(Category).order_by(Category.name).all()
    item = session.query(Item).filter_by(id=item_id).one()
    item_name = item.name
    category = item.category
    if request.method == 'POST':
        print("attempting to delete an item")
        try:
            session.delete(item)
            session.commit()
        except:
            print("Unable to delete {0} from the DB".format(item))
            flash("Failed to delete item {0}".format(item_name))
            pass
        # now check to see if the category needs to be removed
        itemsForCat = session.query(Item.id).join(Category).filter_by(name = category.name)
        count = session.query(func.count(itemsForCat)).scalar()
        print (count)
        if count == 0:
            try:
                session.delete(category)
                session.commit()
            except:
                print("Unable to delete {0} from the DB".format(category))
                pass

        flash("Item {0} has been removed".format(item_name))
        return redirect(url_for('showItems'))
    else:
        return render_template('delete.html', item=item, categories=categories)


@app.route('/auth/')
def showAuth():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('authenticate.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('google_client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    print "done!"
    flash("{0} has the power to create".format(login_session['username']))
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        flash("There was an issue logging out")
        return redirect(url_for('showItems'))
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    return "you have been logged out"
    # if result['status'] == '200':
    #     # del login_session['access_token']
    #     # del login_session['gplus_id']
    #     # del login_session['username']
    #     # del login_session['email']
    #     # del login_session['picture']
    #     return redirect(url_for('showItems'))
    # else:
    #     flash("There was an issue logging out")
    #     return redirect(url_for('showItems'))


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token


    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]


    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.10/me"
    '''
        Due to the formatting for the result from the server token exchange we have to
        split the token first on commas and select the first index which gives us the key : value
        for the server access token then we split it on colons to pull out the actual token value
        and replace the remaining quotes with nothing so that it can be used directly in the graph
        api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.10/me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    print (data)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.10/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    # user_id = getUserID(login_session['email'])
    # if not user_id:
    #     user_id = createUser(login_session)
    # login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("{0} has the power to create".format(login_session['username']))
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    print 'result is '
    print result
    return "you have been logged out"


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    print login_session
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        # del login_session['user_id']
        del login_session['provider']
        flash("You are a mere mortal")
        return redirect(url_for('showItems'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showItems'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
