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
    ''' The login view for users to login with their existing Facebook,
    GooglePlus or github account.
    '''
    return render_template('login.html')


@app.route('/user/<user_id>', methods=['GET', 'POST'])
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


@app.route('/discs/<user_id>/add', methods=['GET', 'POST'])
def addDisc(user_id):
    '''View for adding discs to the database. Intended only for users that
    are currently logged in. If the request method is a POST, we'll add
    a disc to the database according to the information submitted through
    the form. If the request method is not POST, then the 'addDisc' form
    will be presented to the user.
    '''
    if request.method == 'POST':
        newDisc = Disc(name=request.form['disc_name_form'],
                       description=request.form['disc_desc_form'],
                       weight=request.form['disc_weight_form'],
                       color=request.form['disc_color_form'],
                       manufacturer_id=request.form['maker_id_form'],
                       disc_type=request.form['disc_type_form'],
                       user_id=user_id)
        session.add(newDisc)
        session.commit()
        return redirect(url_for('showUserHome', user_id=user_id))
    else:
        list_of_makers = session.query(Manufacturer).all()
        return render_template('addDisc.html',
                               user_id=user_id,
                               makers=list_of_makers)


@app.route('/disc/<int:disc_id>')
def showDisc(disc_id):
    ''' Show details about a unique disc on the site. Because any user can
    submit a description of their unique disc, the unique id from the 'disc'
    table will be used to pull the first record matching the disc_id from
    the URL.
    '''
    thisDisc = session.query(Disc).filter_by(id=disc_id).first()
    if thisDisc:
        return render_template('disc.html', disc=thisDisc)
    else:
        return redirect(url_for('showHome'))


@app.route('/disc/<int:disc_id>/edit', methods=['GET', 'POST'])
def edit_disc(disc_id):
    '''Edit any field of the specified disc'''
    editDisc = session.query(Disc).filter_by(id=disc_id).one()
    if request.method == 'POST':
        editDisc.name = request.form['name']
        editDisc.description = request.form['description']
        editDisc.disc_type = request.form['disc_type']
        editDisc.manufacturer_id = request.form['manufacturer_id']
        session.add(editDisc)
        session.commit()
        return redirect(url_for('showDisc', disc_id=disc_id))
    else:
        return render_template('editDisc.html',
                               disc=editDisc,
                               disc_id=disc_id)


@app.route('/discs/<disc_type>')
def show_discs(disc_type):
    '''Show a list of all discs of a certain type. So far only five types of
    disc are supported. Those five types are stored in the DISCTYPES global
    variable.
    '''
    if disc_type in DISCTYPES:
        discs_by_type = (session.query(Disc)
                         .filter_by(disc_type=disc_type)
                         .all())
        return render_template("discsbytype.html",
                               disc_type=disc_type,
                               discs=discs_by_type)
    else:
        return ("%s is not a type of disc. Choose"
                "from this list %s" % (disc_type, DISCTYPES))


@app.route('/maker/<maker_id>')
def showMaker(maker_id):
    makerInfo = session.query(Manufacturer).filter_by(id=maker_id).one()
    return render_template("maker.html", maker=makerInfo)


@app.route('/maker/<maker>/all')
def showMakerAll(maker):
    '''Show Information about this disc manufacturer, and a list of all discs
    made by this manufacturer.
    '''
    manufacturer = session.query(Manufacturer).filter_by(id=maker).one()
    list_all_by_maker = session.query(
        Disc).filter_by(manufacturer_id=maker).all()
    return render_template("makerAll.html",
                           listofAllByMaker=list_all_by_maker,
                           maker=manufacturer)


@app.route('/user/<user_id>/add/maker')
@app.route('/maker/<user_id>/add')
def add_maker(user_id):
    '''Form to add a new disc manufacturer. URL includes user_id for
    record keeping purposes.
    '''
    return render_template('addMaker.html', user_id=user_id)

if __name__ == '__main__':
    app.config.from_pyfile('config.py')
    app.run(host="0.0.0.0", port=5000)
