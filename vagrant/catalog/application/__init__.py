import os
from flask import Flask, render_template, request, redirect, url_for
from flask import send_from_directory, flash
from werkzeug import secure_filename

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Manufacturer, Disc, User, engine

from application.config import DISCTYPES

app = Flask(__name__)
import application.api


DBSession = sessionmaker(bind=engine)
session = DBSession()

UPLOAD_FOLDER = '/vagrant/catalog/static/images'
PERMITTED_IMG = set(['PNG', 'png', 'JPG', 'jpg', 'JPEG', 'jpeg'])


DISC_TYPE_NAMES = {"putter": "Putter",
                   "midrange": "Mid-Range",
                   "fairwaydriver": "Fairway Driver",
                   "longrangedriver": "Long-Range Driver",
                   "distancedriver": "Distance Driver"}


@app.route('/')
def show_home():
    """Main page will provide different experience for the user if they
    are currently logged in or not.
    """
    list_of_makers = session.query(Manufacturer).all()
    return render_template('main.html', makers=list_of_makers)


@app.route('/login')
def show_login():
    """ The login view for users to login with their existing Facebook,
    GooglePlus or github account.
    """
    return render_template('login.html')


@app.route('/user/<user_id>', methods=['GET', 'POST'])
def show_user_home(user_id):
    """Using the unique user id number, display this user's profile to
    anyone that is not logged in, or is not this user. If the current
    user matches this ID, then show them their own user dashboard.
    """
    this_user = session.query(User).filter_by(id=user_id).one()
    this_users_discs = session.query(Disc).filter_by(user_id=user_id).all()
    this_users_makers = session.query(
        Manufacturer).filter_by(user_id=user_id).all()
    return render_template('user.html',
                           user_info=this_user,
                           discs=this_users_discs,
                           makers=this_users_makers)


@app.route('/discs/<user_id>/add', methods=['GET', 'POST'])
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
    if request.method == 'POST':
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
    img_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return filename


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve the file stored in the 'UPLOAD_FOLDER' to the browser."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/disc/<int:disc_id>')
def show_disc(disc_id):
    """ Show details about a unique disc on the site. Because any user can
    submit a description of their unique disc, the unique id from the 'disc'
    table will be used to pull the first record matching the disc_id from
    the URL.
    """
    this_disc = session.query(Disc).filter_by(id=disc_id).first()
    if this_disc:
        return render_template('disc.html', disc=this_disc, UPLOAD_FOLDER=UPLOAD_FOLDER)
    else:
        return redirect(url_for('show_home'))


@app.route('/disc/<int:disc_id>/edit', methods=['GET', 'POST'])
def edit_disc(disc_id):
    """Edit any field of the specified disc"""
    disc = session.query(Disc).filter_by(id=disc_id).one()
    print type(disc)
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
    disc_to_delete = session.query(Disc).filter_by(id=disc_id).one()
    if request.method == 'POST':
        session.delete(disc_to_delete)
        session.commit()
        flash("Disc has been Deleted")
        return redirect(url_for('show_user_home',
                                user_id=request.args.get('user_id', '')))
    else:
        return render_template('deleteDisc.html',
                               disc=disc_to_delete)


@app.route('/discs/<disc_type>')
def show_discs(disc_type):
    """Show a list of all discs of a certain type. So far only five types of
    disc are supported. Those five types are stored in the DISCTYPES global
    variable.
    """
    if disc_type in DISCTYPES:
        discs_by_type = session.query(
            Disc).filter_by(disc_type=disc_type).all()
        return render_template("discsbytype.html",
                               disc_type=disc_type,
                               discs=discs_by_type)
    else:
        return ("%s is not a type of disc. Choose"
                "from this list %s" % (disc_type, DISCTYPES))


@app.route('/maker/<maker_id>')
def show_maker(maker_id):
    """Show basic info about a maker"""
    maker_info = session.query(Manufacturer).filter_by(id=maker_id).one()
    return render_template("maker.html", maker=maker_info)


@app.route('/maker/<maker>/all')
def show_maker_all(maker):
    """Show Information about this disc manufacturer, and a list of all discs
    made by this manufacturer.
    """
    manufacturer = session.query(Manufacturer).filter_by(id=maker).one()
    list_all_by_maker = session.query(
        Disc).filter_by(manufacturer_id=maker).all()
    return render_template("makerAll.html",
                           listofAllByMaker=list_all_by_maker,
                           maker=manufacturer)


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


if __name__ == '__main__':
    app.config.from_pyfile('config.py')
    app.run(host="0.0.0.0", port=8000)
