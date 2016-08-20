from flask import render_template, flash, redirect, url_for

from sqlalchemy.orm.exc import NoResultFound

from application import app
from application import session
from application import login_session
from application import get_user_info

from database_setup import Manufacturer, Disc, User

from application.constants import DISCTYPES
from application.constants import UPLOAD_FOLDER


@app.route('/')
def show_home():
    """Main page will provide different experience for the user if they
    are currently logged in or not.
    """
    list_of_makers = session.query(Manufacturer).all()
    return render_template('main.html', makers=list_of_makers)


@app.route('/user/<int:user_id>', methods=['GET', 'POST'])
def show_user_home(user_id):
    """Using the unique user id number, display this user's profile to
    anyone that is not logged in, or is not this user. If the current
    user matches this ID, then show them their own user dashboard.
    """
    # Try to lookup the user id in the database
    try:
        this_user = session.query(User).filter_by(id=user_id).one()
    # ... if no result is found route to the main page with a flash
    except NoResultFound:
        flash("This user does not exist.")
        return redirect(url_for('show_home'))
    # However, if no exceptions are raised then proceed as normal by
    # getting the user's disc collection and makers
    else:
        list_of_makers = session.query(Manufacturer).all()
        this_users_discs = session.query(Disc).filter_by(user_id=user_id).all()
        this_users_makers = session.query(
            Manufacturer).filter_by(user_id=user_id).all()
    # Check if this is the user's own profile
    if user_id == login_session.get('user_id'):
        return render_template('user.html',
                               user_info=this_user,
                               discs=this_users_discs,
                               makers=list_of_makers,
                               this_makers=this_users_makers)
    else:
        return render_template('public_user.html',
                               user_info=this_user,
                               discs=this_users_discs,
                               makers=list_of_makers,
                               this_makers=this_users_makers)


@app.route('/disc/<int:disc_id>')
def show_disc(disc_id):
    """ Show details about a unique disc on the site. Because any user can
    submit a description of their unique disc, the unique id from the 'disc'
    table will be used to pull the first record matching the disc_id from
    the URL.
    """
    # Try to lookup the disc in the database
    try:
        this_disc = session.query(Disc).filter_by(id=disc_id).one()
    # ... if no result is found set this_disc to None
    except NoResultFound:
        this_disc = None
    # However, if no exceptions are raised then proceed as normal by
    # getting the disc owner info
    else:
        disc_owner = get_user_info(this_disc.user_id)
    # Verify this disc exists AND the currently logged in user owns the disc.
    # If so show the disc owner page which includes edit/delete links.
    list_of_makers = session.query(Manufacturer).all()
    if this_disc and this_disc.user_id == login_session.get('user_id'):
        return render_template('disc.html',
                               makers=list_of_makers,
                               disc=this_disc,
                               disc_owner=disc_owner,
                               UPLOAD_FOLDER=UPLOAD_FOLDER)
    # If the disc exists but the user is not the owner, show the public
    # disc page which does not include edit/delete.
    elif this_disc:
        return render_template('public_disc.html',
                               makers=list_of_makers,
                               disc=this_disc,
                               disc_owner=disc_owner,
                               UPLOAD_FOLDER=UPLOAD_FOLDER)
    # Finally if the disc doesn't exist, route to main with a flash
    else:
        flash("Disc does not exist.")
        return redirect(url_for('show_home'))


@app.route('/discs/<disc_type>')
def show_discs(disc_type):
    """Show a list of all discs of a certain type. So far only five types of
    disc are supported. Those five types are stored in the DISCTYPES global
    variable.
    """
    if disc_type in DISCTYPES:
        discs_by_type = session.query(
            Disc).filter_by(disc_type=disc_type).all()
        list_of_makers = session.query(Manufacturer).all()
        return render_template("discsbytype.html",
                               makers=list_of_makers,
                               disc_type=disc_type,
                               discs=discs_by_type)
    else:
        return ("%s is not a type of disc. Choose"
                "from this list %s" % (disc_type, DISCTYPES))


@app.route('/maker/<int:maker>')
def show_maker_all(maker):
    """Show Information about this disc manufacturer, and a list of all discs
    made by this manufacturer.
    """
    try:
        manufacturer = session.query(Manufacturer).filter_by(id=maker).one()
    except NoResultFound:
        flash("Manufacturer does not exist.")
        return redirect(url_for('show_home'))
    else:
        list_of_makers = session.query(Manufacturer).all()
        list_all_by_maker = session.query(
            Disc).filter_by(manufacturer_id=maker).all()
        return render_template("makerAll.html",
                               makers=list_of_makers,
                               listofAllByMaker=list_all_by_maker,
                               maker=manufacturer)


@app.route('/test')
def test_page():
    return "the test index"


@app.route('/sess')
def show_sess_info():
    """Quick and dirty func see what's going on."""
    output = 'Session info'
    for i in login_session:
        output += '<br>'
        output += i
        output += '<br>'
        output += str(login_session.get(i))
        output += '<br>'
    return output


@app.route('/clear')
def clear_session():
    login_session.clear()
    return redirect(url_for('show_sess_info'))
