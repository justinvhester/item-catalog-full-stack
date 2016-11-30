import os
from flask import Flask, render_template, request, redirect, url_for
from flask import send_from_directory, flash
from flask import session as login_session
import random
import string
from werkzeug import secure_filename
# Database, sqlalchemy and ORM imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Manufacturer, Disc, User, engine
# Imports for login with oauth2 and google plus
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


with open('/var/www/discr/vagrant/catalog/client_secrets.json', 'r') as secrets:
    CLIENT_ID = json.load(secrets).get('web').get('client_id')

from application.constants import DISCTYPES, DISC_TYPE_NAMES
from application.constants import UPLOAD_FOLDER, PERMITTED_IMG

app = Flask(__name__)
import application.api


DBSession = sessionmaker(bind=engine)
session = DBSession()


# My own little time saver
def makeJSONResponse(message, response_code):
    response = make_response(json.dumps(message), response_code)
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/login')
def show_login():
    """The login view for users to login with their existing Facebook or
    GooglePlus account.
    """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    print "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        return makeJSONResponse('Invalid state parameter', 401)
    access_token = request.data
    app_id = json.loads(open('/var/www/discr/vagrant/catalog/fb_client_secrets.json', 'r').read())['web']['app_id']
    app_secret = json.loads(open('/var/www/discr/vagrant/catalog/fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    userinfo_url = "https://graph.facebook.com/v2.6/me"
    token = result.split("&")[0]
    url = 'https://graph.facebook.com/v2.6/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    # let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.6/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = get_user_id(login_session['email'])
    if not user_id:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    #flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    print(result)
    return


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Sign into DISCR with Google Plus credentials."""
    if request.args.get('state') != login_session['state']:
        return makeJSONResponse('Invalid state parameter', 401)
    try:
        oauth_flow = flow_from_clientsecrets('/var/www/discr/vagrant/catalog/client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(request.data)
    except FlowExchangeError:
        return makeJSONResponse("Failed to upgrade the authorization code.",
                                401)

    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If my result contains any errors then I send a 500 internal server
    # error to my client
    if result.get('error') is not None:
        return makeJSONResponse(json.dumps(result.get('error')), 500)

    gplus_id = credentials.id_token['sub']
    # Verify the gplus_id matches
    if result['user_id'] != gplus_id:
        return makeJSONResponse("Token's user ID doesn't match given user ID.",
                                401)

    # Verify the CLIENT_ID matches
    if result['issued_to'] != CLIENT_ID:
        return makeJSONResponse("Token CLIENT ID is not the app's client id.",
                                401)

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        return makeJSONResponse("Current user is already connected.", 200)

    login_session['provider'] = 'google'
    login_session['credentials'] = access_token
    login_session['gplus_id'] = gplus_id

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = get_user_id(login_session.get('email'))
    if not user_id:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id

    return makeJSONResponse("Welcome to DISCR", 200)


@app.route("/gdisconnect")
def gdisconnect():
    """Revoke the gplus token, thus disconnecting the user"""
    credentials = login_session.get('credentials')
    if credentials is None:
        return makeJSONResponse('Current user not connected.', 401)

    access_token = login_session['credentials']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    response = requests.get(url)

    if response.status_code == 200:
        return
    else:
        return makeJSONResponse('Failed to revoke token for given user', 400)


@app.route("/disconnect")
def disconnect():
    if "provider" in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
            del login_session['access_token']
        del login_session['username']
        del login_session['state']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('show_home'))
    else:
        flash("You were not logged in")
        return redirect(url_for('show_home'))


@app.route('/discs/<int:user_id>/add', methods=['GET', 'POST'])
def add_disc(user_id):
    """View for adding discs to the database.

    Intended only for users that are currently logged in. If the
    request method is a POST, we'll add a disc to the database according
    to the information submitted through the form. If the request method
    is not POST, then the 'addDisc.html' template form will be presented
    to the user. disc_img variable is the result of disc_image_upload
    function, being the full directory path and filename of the disc
    picture stored as a string in the database.
    """
    if 'user_id' not in login_session:
        flash("Please login to add a new disc to your collection")
        return redirect('/login')
    elif login_session.get('user_id') != user_id:
        flash("Please add a disc from your own user page.")
        return redirect(url_for('show_user_home', user_id=user_id))
    elif request.method == 'POST' and login_session.get('user_id') is user_id:
        if request.files['disc_image_form']:
            disc_img_file = request.files['disc_image_form']
            if allowed_file(disc_img_file.filename):
                disc_img = disc_image_upload(disc_img_file)
            else:
                disc_img = "FILE NOT UPLOADED"
        else:
            disc_img = "FILE NOT UPLOADED"
        new_disc = Disc(name=request.form['disc_name_form'],
                        description=request.form['disc_desc_form'],
                        weight=request.form['disc_weight_form'],
                        picture=disc_img,
                        color=request.form['disc_color_form'],
                        manufacturer_id=request.form['maker_id_form'],
                        disc_type=request.form['disc_type_form'],
                        condition=request.form['disc_cond_form'],
                        user_id=user_id)
        session.add(new_disc)
        session.commit()
        flash("New Disc has been added")
        return redirect(url_for('show_user_home', user_id=user_id))
    else:
        list_of_makers = session.query(Manufacturer).all()
        return render_template('addDisc.html',
                               user_id=user_id,
                               makers=list_of_makers)


def allowed_file(filename):
    """Return True or False if type of file is permitted

    Check if the filename string contains a '.' and also if the file
    extension matches a member of the PERMITTED_IMG set.
    Great example of this pattern found at:
    http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
    """
    return '.' in filename and filename.rsplit('.', 1)[1] in PERMITTED_IMG


def disc_image_upload(img_file):
    """Upload picture of the disc to DISCR"""
    filename = secure_filename(img_file.filename)
    img_file.save(os.path.join(UPLOAD_FOLDER, filename))
    return filename


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve the file stored in the 'UPLOAD_FOLDER' to the browser."""
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/disc/<int:disc_id>/edit', methods=['GET', 'POST'])
def edit_disc(disc_id):
    """Edit any field of the specified disc"""
    if 'username' not in login_session:
        flash("Please login to edit your own Discs")
        return redirect('/login')
    disc = session.query(Disc).filter_by(id=disc_id).one()
    if disc.user_id is not login_session.get('user_id'):
        return redirect(url_for('show_disc', disc_id=disc_id))
    if request.method == 'POST':
        for field in request.form:
            print request.form.get(field, "")
        if request.form['name']:
            disc.name = request.form['name']
        if request.files['disc_image']:
            disc_img = disc_image_upload(request.files['disc_image'])
            disc.picture = disc_img
        if request.form['description']:
            disc.description = request.form['description']
        if request.form['disc_type']:
            disc.disc_type = request.form['disc_type']
        if request.form['maker_id_form']:
            disc.manufacturer_id = request.form['maker_id_form']
        if request.form['weight']:
            disc.weight = request.form['weight']
        if request.form['color']:
            disc.color = request.form['color']
        if request.form['condition']:
            disc.condition = request.form['condition']
        session.add(disc)
        session.commit()
        flash("Disc has been edited")
        return redirect(url_for('show_disc', disc_id=disc_id))
    else:
        list_of_makers = session.query(Manufacturer).all()
        return render_template('editDisc.html',
                               disc=disc,
                               disc_id=disc_id,
                               makers=list_of_makers,
                               DISCTYPES=DISCTYPES,
                               DISC_TYPE_NAMES=DISC_TYPE_NAMES)


@app.route('/disc/<int:disc_id>/delete', methods=['GET', 'POST'])
def delete_disc(disc_id):
    """Delete a unique disc from DISCR

    Only the user that added the disc (the owner) is allowed to
    delete the disc.
    """
    if 'username' not in login_session:
        flash("Please login to delete your own Discs")
        return redirect('/login')
    disc_to_delete = session.query(Disc).filter_by(id=disc_id).one()
    if disc_to_delete.user_id is not login_session.get('user_id'):
        return redirect(url_for('show_disc', disc_id=disc_id))
    elif request.method == 'POST':
        session.delete(disc_to_delete)
        session.commit()
        flash("Disc has been Deleted")
        return redirect(url_for('show_user_home',
                                user_id=request.args.get('user_id', '')))
    else:
        return render_template('deleteDisc.html',
                               disc=disc_to_delete)


@app.route('/user/<user_id>/add/maker', methods=['GET', 'POST'])
@app.route('/maker/<user_id>/add', methods=['GET', 'POST'])
def add_maker(user_id):
    """Form to add a new disc manufacturer. URL includes user_id for
    record keeping purposes.
    """
    if request.method == 'POST':
        new_maker = Manufacturer(
            name=request.form['manufacturer_name_form'],
            country=request.form['manufacturer_country_form'],
            user_id=user_id)
        session.add(new_maker)
        session.commit()
        user = session.query(
            User).filter_by(id=user_id).one()
        flash("New manufacturer has been added")
        return redirect(url_for('add_disc', user_id=user_id))
    else:
        user = session.query(
            User).filter_by(id=user_id).one()
        return render_template('addMaker.html', user=user)


@app.route('/maker/<int:maker_id>/edit', methods=['GET', 'POST'])
def edit_manufacturer(maker_id):
    """Edit manufacturer information"""
    maker_edit = session.query(
        Manufacturer).filter_by(id=maker_id).one()
    print dir(maker_edit)
    if request.method == 'POST':
        if request.form['name']:
            maker_edit.name = request.form['name']
        if request.form['country']:
            maker_edit.country = request.form['country']
        session.add(maker_edit)
        session.commit()
        flash("Manufacturer has been edited")
        return redirect(url_for('show_maker', maker_id=maker_id))
    else:
        return render_template('editManufacturer.html', maker=maker_edit)


@app.route('/maker/<int:maker_id>/delete', methods=['GET', 'POST'])
def delete_manufacturer(maker_id):
    """Delete manufacturer from website"""
    mnfctr_delete = session.query(Manufacturer).filter_by(id=maker_id).one()
    list_all_by_maker = session.query(
        Disc).filter_by(manufacturer_id=maker_id).all()
    if request.method == 'POST':
        session.delete(mnfctr_delete)
        session.commit()
        flash("Menufacturer has been Deleted")
        return redirect(url_for('show_user_home',
                                user_id=request.args.get('user_id', '')))
    else:
        return render_template('deleteManufacturer.html',
                               maker=mnfctr_delete,
                               listofDiscs=list_all_by_maker)


def create_user(login_session):
    new_user = User(name=login_session['username'],
                    email=login_session['email'],
                    picture=login_session['picture'])
    session.add(new_user)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def get_user_info(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def get_user_id(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

import application.views
