from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

app = Flask(__name__)

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
def showCategories():
    return "This is the main page. All categories will be listed here."

@app.route('/category/<int:category_id>')
def showItemList(category_id):
    return "This page will list all items under a category %s." % category_id

@app.route('/category/<int:category_id>/<int:item_id>')
def showItem(category_id, item_id):
    return "This page will have a description of the %s item under the %s \
            category." % (category_id, item_id)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
