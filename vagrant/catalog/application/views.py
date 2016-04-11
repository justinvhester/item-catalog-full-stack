from flask import render_template, flash, redirect, url_for

from sqlalchemy.orm.exc import NoResultFound

from application import app
from application import session
from application import login_session

from database_setup import Manufacturer, Disc, User


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
        this_users_discs = session.query(Disc).filter_by(user_id=user_id).all()
        this_users_makers = session.query(
            Manufacturer).filter_by(user_id=user_id).all()
    # Check if this is the user's own profile
    if user_id == login_session.get('user_id'):
        return render_template('user.html',
                               user_info=this_user,
                               discs=this_users_discs,
                               makers=this_users_makers)
    else:
        return render_template('public_user.html',
                               user_info=this_user,
                               discs=this_users_discs,
                               makers=this_users_makers)
