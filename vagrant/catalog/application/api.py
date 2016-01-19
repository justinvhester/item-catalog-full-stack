"""APIs for Discr providing JSON formatted data of Disc collections."""
from application import app
from application.config import DISCTYPES
from flask import jsonify
from database_setup import Disc, engine
from sqlalchemy.orm import sessionmaker

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/user/<user_id>/JSON')
def show_user_collection_json(user_id):
    """Return JSON formatted data of this user's disc collection."""
    this_users_discs = session.query(Disc).filter_by(user_id=user_id).all()
    return jsonify(users_discs=[i.serialize for i in this_users_discs])


@app.route('/discs/<disc_type>/JSON')
def show_discs_json(disc_type):
    """Return JSON formatted data set for all discs of a certain type"""
    if disc_type in DISCTYPES:
        discs_by_type = session.query(
            Disc).filter_by(disc_type=disc_type).all()
        return jsonify(Discs=[i.serialize for i in discs_by_type])


@app.route('/maker/<maker>/all/JSON')
def show_maker_all_json(maker):
    """Return JSON formatted data of all discs manufactured by a
    particular disc manufacturer.
    """
    list_all_by_maker = session.query(
        Disc).filter_by(manufacturer_id=maker).all()
    return jsonify(Discs=[i.serialize for i in list_all_by_maker])
