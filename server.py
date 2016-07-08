from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

# OAuth stuff
from flask import session as login_session
import random, string

# Imports for G-Connect stuff
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

# Token for Google authentication
CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']

app = Flask(__name__)

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/login/')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)
    # return "This is the login page"

@app.route('/gconnect', methods = ['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Connect-Type'] = 'application/json'
        print "The states match!"
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorization code'), 401)
        response.headers['Connect-Type'] = 'application/json'
        return response

    # Check that access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 501)
        response.headers['contentType'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps('Token\'s user ID doesn\'t match given user ID.'), 401)
        response.headers['Connect-Type'] = 'application/json'
        return response

    # Check to see if user is already logged in.
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Connect-Type'] = 'application/json'

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt':'json'}
    answer = requests.get(userinfo_url, params = params)
    # print answer.text # Print Google response for debugging
    data = json.loads(answer.text)

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # Check if email exists and if not, create a new user
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1> Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src ="'
    output += login_session['picture']
    output += ' style = "width: 300px; height: 300px; border-radius: 150px; -webkit-border-radius: 150px; -moz-border-radius: 150px;"> '
    flash_message = "You are now logged in as %s" % login_session['username']
    flash(flash_message)
    return output

@app.route('/gdisconnect')
def gdisconnect():
    credentials = json.loads(login_session['credentials'].to_json())
    access_token = credentials['access_token']
    print 'In gdisconnect access token is %s' % access_token
    print 'User name is: %s ' % login_session['username']
    if access_token is None:
 	print 'Access Token is None'
    	response = make_response(json.dumps('Current user not connected.'), 401)
    	response.headers['Content-Type'] = 'application/json'
    	return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
	# del login_session['access_token']
    	# del login_session['gplus_id']
    	del login_session['username']
    	del login_session['email']
    	del login_session['picture']
    	response = make_response(json.dumps('Successfully disconnected.'), 200)
    	response.headers['Content-Type'] = 'application/json'
    	print response
        flash_string = "You have been logged out"
        flash(flash_string)
        return redirect(url_for('showCategories'))
    else:
        # del login_session['username']
    	# del login_session['email']
    	# del login_session['picture']
    	response = make_response(json.dumps('Failed to revoke token for given user.', 400))
    	response.headers['Content-Type'] = 'application/json'
    	return response
        # return redirect(url_for('gdisconnect'))

@app.route('/')
@app.route('/catalog')
def showCategories():
    categories = session.query(Category).all();
    return render_template('categories.html', categories = categories, login_session = login_session)

@app.route('/category/<category_name>')
def showItemList(category_name):
    category = session.query(Category).filter_by(name = category_name).one()
    items = session.query(Item).filter_by(category_id = category.id).all()
    return render_template('itemlist.html', category = category, items = items, login_session = login_session)
    # return render_template('itemlist.html', category = category, items = items)

@app.route('/category/<category_name>/<item_name>')
def showItemPage(category_name, item_name):
    category = session.query(Category).filter_by(name = category_name).one()
    # creator = getUserInfo(category.user_id)
    item = session.query(Item).filter_by(category_id = category.id, name = item_name).one()
    # if 'username' not in login_session or creator.id != login_session['user_id']:
    #     return render_template('publicitempage.html', category = category, item = item, login_session = login_session)
    # else:
    #     return render_template('itempage.html', category = category, item = item, login_session = login_session)
    return render_template('itempage.html', category = category, item = item, login_session = login_session)

@app.route('/category/new/', methods = ['GET', 'POST'])
def newCategory():
    # if 'username' not in login_session:
    #     return redirect('/login/')
    if request.method == 'POST':
        # newCategory = Category(name = request.form['name'], user_id = login_session['user_id'])
        newCategory = Category(name = request.form['name'], description = request.form['description'])

        # Initialize duplicate name flag to false
        name_exists = False

        # Check if category name has been taken already
        categories = session.query(Category).all();
        for category in categories:
            if str(category.name) == newCategory.name:
                # Set duplicate name flag
                name_exists = True

        if name_exists == True:
            # Name has been taken, reload same page and flash message
            flash_string = "%s is already in use. Provide a different name" % newCategory.name
            flash(flash_string)
            return redirect(url_for('newCategory'))
        else:
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
    if 'username' not in login_session:
        return redirect('/login/')
    category = session.query(Category).filter_by(name = category_name).one()
    if request.method == 'POST':
        newItem = Item(name = request.form['name'], category_id = category.id, description = request.form['description'], user_id = login_session['user_id'])
        # newItem = Item(name = request.form['name'], category_id = category.id, description = request.form['description'])

        # Initialize duplicate name flag
        name_exists = False

        # Check if item name has been taken already
        items = session.query(Item).all();
        for item in items:
            if str(item.name) == newItem.name:
                # Set duplicate name flag
                name_exists = True

        if name_exists == True:
            # Name has been taken, reload same page and flash message
            flash_string = "%s is already in use. Provide a different name" % newItem.name
            flash(flash_string)
            return redirect(url_for('newItem', category_name = category.name))
        else:
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
    if 'username' not in login_session:
        return redirect('/login/')

    category = session.query(Category).filter_by(name = category_name).one()
    editedItem = session.query(Item).filter_by(name = item_name).one()

    if request.method == 'POST':
        # Check if user is the owner of the item
        if editedItem.user_id == login_session['user_id']:
            # User is the owner, allow edit to proceed
            if request.form['name']:
                editedItem.name = request.form['name']
            if request.form['description']:
                editedItem.description = request.form['description']
            session.add(editedItem)
            session.commit()
            flash_string = "%s has been edited" % editedItem.name
            flash(flash_string)
            return redirect(url_for('showItemList', category_name = category.name))
        else:
            # User is not the ownder, edit cannot proceed
            flash_string = "You do not have permission to edit %s." % editedItem.name
            flash(flash_string)
            return redirect(url_for('showItemList', category_name = category.name))
    else:
        # return render_template('edititem.html', category = category, item = editedItem, login_session = login_session)
        return render_template('edititem.html', category = category, item = editedItem)

@app.route('/category/<category_name>/item/<item_name>/delete/', methods = ['GET', 'POST'])
def deleteItem(item_name, category_name):
    if 'username' not in login_session:
        return redirect('/login/')

    category = session.query(Category).filter_by(name = category_name).one()
    deletedItem = session.query(Item).filter_by(name = item_name).one()

    if request.method == 'POST':
        # Check if user is the owner of the item
        if deletedItem.user_id == login_session['user_id']:
            # User is the owner, allow delete operation to proceed
            session.delete(deletedItem)
            session.commit()
            flash_string = "%s has been deleted" % deletedItem.name
            flash(flash_string)
            return redirect(url_for('showItemList', category_name = category.name))
        else:
            # User is not the owner, do not allow delete operation to proceed
            flash_string = "You do not have permission to delete %s." % deletedItem.name
            flash(flash_string)
            return redirect(url_for('showItemList', category_name = category.name))
    else:
        # return render_template('deleteitem.html', category = category, item = deletedItem, login_session = login_session)
        return render_template('deleteitem.html', category = category, item = deletedItem)

@app.route('/catalog.json')
def catalog_json():
    categories = session.query(Category).all()
    return jsonify(Category = [i.serialize for i in categories])

def createUser(login_session):
    users = session.query(User).all()
    id_num = len(users) + 1
    newUser = User(id = id_num, name = login_session['username'], email = login_session['email'], picture = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).one()
    print user
    return user.id

def getUserID(email):
    try:
        user = session.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None

def getUserInfo(user_id):
    user = session.query(User).filter_by(id = user_id).one()
    # print user
    return user

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
