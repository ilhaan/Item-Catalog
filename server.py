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

@app.route('/category/<int:category_id>')
def showItemList(category_id):
    return "This page will list all items under a category %s." % category_id

@app.route('/category/<int:category_id>/<int:item_id>')
def showItem(category_id, item_id):
    return "This page will have a description of the %s item under the %s \
            category." % (category_id, item_id)

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

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
