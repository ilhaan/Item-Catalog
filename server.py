from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

app = Flask(__name__)

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/login/')
def showLogin():
    # state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    # login_session['state'] = state
    # return render_template('login.html', STATE=state)
    return "This is the login page"

@app.route('/')
def showCategories():
    categories = session.query(Category).all();
    return render_template('categories.html', categories = categories)
    # return "This is the main page. All categories will be listed here."

@app.route('/category/<category_name>')
def showItemList(category_name):
    category = session.query(Category).filter_by(name = category_name).one()
    # creator = getUserInfo(category.user_id)
    items = session.query(Item).filter_by(category_id = category.id).all()
    # if 'username' not in login_session or creator.id != login_session['user_id']:
    #     return render_template('publicitemlist.html', restaurant = restaurant, items = items, creator = creator, login_session = login_session)
    # else:
    #     return render_template('itemlist.html', restaurant = restaurant, items = items, creator = creator, login_session = login_session)
    return render_template('itemlist.html', category = category, items = items)

@app.route('/category/<category_name>/<item_name>')
def showItemPage(category_name, item_name):
    category = session.query(Category).filter_by(name = category_name).one()
    # creator = getUserInfo(category.user_id)
    item = session.query(Item).filter_by(category_id = category.id, name = item_name).one()
    # if 'username' not in login_session or creator.id != login_session['user_id']:
    #     return render_template('publicitemlist.html', restaurant = restaurant, items = items, creator = creator, login_session = login_session)
    # else:
    #     return render_template('itemlist.html', restaurant = restaurant, items = items, creator = creator, login_session = login_session)
    return render_template('itempage.html', category = category, item = item)

@app.route('/category/new/', methods = ['GET', 'POST'])
def newCategory():
    # if 'username' not in login_session:
    #     return redirect('/login/')
    if request.method == 'POST':
        # newCategory = Category(name = request.form['name'], user_id = login_session['user_id'])
        newCategory = Category(name = request.form['name'])
        session.add(newCategory)
        session.commit()
        flash("New category created!")
        return redirect(url_for('showCategories'))
    else:
        return render_template('newcategory.html')
        # return render_template('newcategory.html', login_session = login_session)
        # return "This is the add new item page"

@app.route('/category/<category_name>/item/new/', methods = ['GET', 'POST'])
def newItem(category_name):
    # if 'username' not in login_session:
    #     return redirect('/login/')
    category = session.query(Category).filter_by(name = category_name).one()
    if request.method == 'POST':
        # newItem = Item(name = request.form['name'], category_id = category.id, description = request.form['description'], price = request.form['price'], user_id = restaurant.user_id)
        newItem = Item(name = request.form['name'], category_id = category.id, description = request.form['description'])
        session.add(newItem)
        session.commit()
        flash_string = "%s has been added to the list" % newItem.name
        flash(flash_string)
        return redirect(url_for('showItemList', category_name = category.name))
    else:
        # return render_template('newitem.html', category = category, login_session = login_session)
        return render_template('newitem.html', category = category)

@app.route('/category/<category_name>/item/<item_name>/edit/', methods = ['GET', 'POST'])
def editItem(item_name, category_name):
    # if 'username' not in login_session:
    #     return redirect('/login/')
    category = session.query(Category).filter_by(name = category_name).one()
    editedItem = session.query(Item).filter_by(name = item_name).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        # if request.form['price']:
        #     editedItem.price = request.form['price']
        session.add(editedItem)
        session.commit()
        flash_string = "%s has been edited" % editedItem.name
        flash(flash_string)
        return redirect(url_for('showItemList', category_name = category.name))
    else:
        # return render_template('edititem.html', category = category, item = editedItem, login_session = login_session)
        return render_template('edititem.html', category = category, item = editedItem)

@app.route('/category/<category_name>/item/<item_name>/delete/', methods = ['GET', 'POST'])
def deleteItem(item_name, category_name):
    # if 'username' not in login_session:
    #     return redirect('/login/')
    category = session.query(Category).filter_by(name = category_name).one()
    deletedItem = session.query(Item).filter_by(name = item_name).one()
    if request.method == 'POST':
        session.delete(deletedItem)
        session.commit()
        flash_string = "%s has been deleted" % deletedItem.name
        flash(flash_string)
        return redirect(url_for('showItemList', category_name = category.name))
    else:
        # return render_template('deleteitem.html', category = category, item = deletedItem, login_session = login_session)
        return render_template('deleteitem.html', category = category, item = deletedItem)

@app.route('/catalog.json')
def catalog_json():
    categories = session.query(Category).all()
    return jsonify(Category = [i.serialize for i in categories])

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
