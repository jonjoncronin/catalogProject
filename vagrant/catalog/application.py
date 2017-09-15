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
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Item, Category

import httplib2

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

@app.route('/catalog/category/<int:category_id>/')
def showItemsForCategory(category_id):
    """
    route to showItemsForCategory will render a page that shows the items
    associated with a specific category.
    """
    categories = session.query(Category).order_by(Category.name).all()
    targetCategory = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).order_by(Item.name)
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
        items = session.query(Item).filter_by(category_id = entry['id']).order_by(Item.name).all()
        items_dict = [item.serialize for item in items]
        cate_dict[index]["Item"] = items_dict
        index+=1
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
                        # session.commit
                        existingCategory = session.query(Category).filter_by(
                                            name=request.form['category']).one()
                    except:
                        print("Unable to add {0} category to the DB".format(newCategory))
                        return redirect(url_for('showItems'))

                categoryId = existingCategory.id
                newItem = Item(name=request.form['name'],
                               description=request.form['description'],
                               category_id=categoryId)
                try:
                    session.add(newItem)
                    session.commit
                except:
                    print("Unable to add {0} item to the DB".format(newItem))
                    pass
            else:
                print("{0} already exists with category {1}".format(
                    request.form['name'], existingItem.category))
        return redirect(url_for('showItems'))
    else:
        return render_template('new.html')


@app.route('/catalog/item/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(item_id):
    """
    route to editItem will render a page to allow a user to edit a specific
    items category and/or description. Changing the name is NOT allowed and you
    MUST delete an entry if you want one with a different name.
    """
    editedItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        print("attempting to edit an item")
        # Flask doesn't like it if we check form input and it has no value.
        # See the editRestaurant.html template for the save_button <button>
        # object and notice that we set a value of "True".
        print(request.form)
        if request.form['category'] and request.form['category'] is not editedItem.category:
            #print("attempting to edit item category")
            editedItem.category = request.form['category']
        if request.form['description'] and request.form['description'] is not editedItem.description:
            editedItem.description = request.form['description']
        try:
            session.add(editedItem)
            session.commit
        except:
            print("Unable to add {0} to the DB".format(editedItem))
            pass
        return redirect(url_for('showItems'))
    else:
        return render_template('edit.html', item=editedItem)

@app.route('/catalog/item/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(item_id):
    """
    route to deleteItem will render a page to prompt the user for confirmation
    that an item is to be deleted and performs the delete if confirmed.
    """
    item = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        print(request.form)
        if request.form['submit']:
            print("attempting to delete an item")
            try:
                session.delete(item)
                session.commit
            except:
                print("Unable to delete {0} from the DB".format(item))
                pass
        return redirect(url_for('showItems'))
    else:
        return render_template('delete.html', item=item)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
