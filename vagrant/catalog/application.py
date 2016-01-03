from flask import Flask, render_template, request, redirect, url_for

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Manufacturer, Disc, User, engine

app = Flask(__name__)


DBSession = sessionmaker(bind=engine)
session = DBSession()


# Tuple for the statically defined types of disc golf discs we support
DISCTYPES = ("putter",
             "midrange",
             "fairwaydriver",
             "longrangedriver",
             "distancedriver")


@app.route('/')
def showHome():
    '''Main page will provide different experience for the user if they
    are currently logged in or not.
    '''
    return render_template('main.html')


@app.route('/login')
def showLogin():
    return "This login page will offer at least a couple of external OAuth2 providers. Start off with Facebook and G plus."


@app.route('/user/<user_id>')
def showUserHome(user_id):
    '''Using the unique user id number, display this user's profile to
    anyone that is not logged in, or is not this user. If the current
    user matches this ID, then show them their own user dashboard.
    '''
    thisUser = session.query(User).filter_by(id=user_id).one()
    thisUsersDiscs = session.query(Disc).filter_by(user_id=user_id).all()
    return render_template('user.html',
                           user_info=thisUser,
                           discs=thisUsersDiscs)




@app.route('/discs/<int:make_id>/<int:disc_id>')
def showDisc(make_id, disc_id):
    return "This page will show the details of the unique disc with the disc ID of %d" % disc_id


@app.route('/discs/<disc_type>')
def showDiscs(disc_type):
    if disc_type in disc_types:
        return "All discs in the %s category are listed here" % disc_type
    else:
        return "%s is not a type of disc you silly-billy. Choose one of these %s" % (disc_type, disc_types)


@app.route('/maker/<maker_id>')
def showMaker(maker_id):
    return "Show details about disc manufacturer with unique ID %s" % maker_id


if __name__ == '__main__':
    app.config.from_pyfile('config.py')
    app.run(host = "0.0.0.0", port = 5000)
