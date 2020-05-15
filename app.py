# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

from dbop import fetch_venue_byname, fill_num_upcoming_shows, \
    fetch_venues, fetch_num_upcoming_show_byvenue, \
    fetch_venues_cities_and_states, fetch_past_shows_by_venue, \
    fetch_upcoming_shows_by_venue, fetch_artists_by_name, \
    fetch_past_shows_by_artist, fetch_upcoming_shows_by_artist, fetch_shows
import json
import sys

import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect,\
    url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy.orm import backref
from werkzeug.datastructures import MultiDict

from forms import *

from flask_migrate import Migrate

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String, nullable=True)

    # artists = db.relationship('Artist', secondary='Show')

    def __repr__(self):
        return f'<Venue id: {self.id} - name: {self.name} - city: {self.city}'
        ' - state: {self.state} - phone: {self.phone}>'


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String, nullable=True)

    # venues = db.relationship('Venue', secondary='Show')


class Show(db.Model):
    # noinspection SpellCheckingInspection
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    start_time = db.Column(db.DateTime, default=datetime.utcnow)

    artist = db.relationship('Artist', backref=backref(
        'Show', cascade='all, delete-orphan'))
    venue = db.relationship('Venue', backref=backref(
        'Show', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Show id: {self.id} - venue_id: {self.venue_id} - '
        'artist_id: {self.artist_id} - start_time: {self.start_time}>'


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en_150")


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    data = fetch_venues()
    from pprint import pprint
    pprint(data)
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # seach for Hop should return "The Musical Hop".
    # search for "Music"
    # should return "The Musical Hop" and "Park Square Live Music & Coffee"
    name = request.form['search_term']
    venues = fetch_venue_byname(name)
    response = {
        "count": len(venues),
        "data": venues
    }
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = Venue.query.get(venue_id)
    past_shows = fetch_past_shows_by_venue(venue_id)
    upcoming_shows = fetch_upcoming_shows_by_venue(venue_id)
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres[1:-1].replace('"', '').split(',')
        if len(venue.genres) > 2 else [],
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # Grab data from form
    venue = {
        "name": request.form.get('name', ''),
        "genres": request.form.getlist('genres'),
        "address": request.form.get('address', ''),
        "city": request.form.get('city', ''),
        "state": request.form.get('state', ''),
        "phone": request.form.get('phone', ''),
        "website": None,
        "facebook_link": request.form.get('facebook_link', ''),
    }
    # Make an instance from the data
    newVenue = Venue(**venue)
    error = False
    exists = len(Venue.query
                 .filter(
                     db.func.lower(Venue.name) == db.func.lower(newVenue.name))
                 .all()) > 0

    # Inserts the venue only if it doesn't exist
    if exists:
        error = True
        flash('An error occurred. Venue ' +
              newVenue.name + ' exists already.', 'error')
    else:
        try:
            db.session.add(newVenue)
            db.session.commit()
            # on successful db insert, flash success
            flash('Venue ' + newVenue.name + ' was successfully listed!')
        except Exception:
            error = True
            print(sys.exc_info())
            db.session.rollback()
            flash('An error occurred. Venue ' + newVenue.name +
                  ' could not be listed.', 'error')

    if error:
        form = VenueForm(**venue)
        return render_template('forms/new_venue.html', form=form)

    # e.g.,
    # flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where
    # the session commit could fail.
    venue = Venue.query.get(venue_id)
    error = False
    try:
        db.session.delete(venue)
        db.session.commit()
        flash('Venue was deleted successfully.')
    except Exception:
        error = True
        db.session.rollback()
        flash(f'Could not delete Venue ID {venue_id}', 'error')

    # BONUS CHALLENGE:
    # Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then
    # redirect the user to the homepage
    return jsonify({'success': not error, 'redirect': '/'})


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists = Artist.query.all()
    data = []
    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name,
        })
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # search for "A"
    # should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    artists = fetch_artists_by_name(request.form['search_term'])
    response = {
        "count": len(artists),
        "data": artists
    }
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    artist = Artist.query.get(artist_id)
    past_shows = fetch_past_shows_by_artist(artist_id)
    upcoming_shows = fetch_upcoming_shows_by_artist(artist_id)
    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres[1:-1].replace('"', '').split(','),
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id).__dict__
    artist['genres'] = artist['genres'][1:-1].replace('"', '').split(',')
    form = ArtistForm(MultiDict(artist))
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # artist record with ID <artist_id> using the new attributes
    # Load the existing Artist
    oArtist = Artist.query.get(artist_id)
    # Update the Artist instance from the data in the form
    oArtist.name = request.form.get('name', '')
    oArtist.genres = request.form.getlist('genres')
    oArtist.city = request.form.get('city', '')
    oArtist.state = request.form.get('state', '')
    oArtist.phone = request.form.get('phone', '')
    oArtist.facebook_link = request.form.get('facebook_link', '')

    # Finds if the name is taken by another artist
    error = False
    exists = len(
        Artist.query
        .filter(db.func.lower(Artist.name) == db.func.lower(oArtist.name),
                Artist.id != artist_id)
        .all()) > 0

    # Update the artist only if it doesn't exist
    if exists:
        error = True
        flash('An error occurred. Another artist ' +
              oArtist.name + ' exists already.', 'error')
    else:
        try:
            db.session.commit()
            # on successful db insert, flash success
            flash('Artist ' + oArtist.name + ' was successfully updated!')
        except Exception:
            error = True
            db.session.rollback()
            flash('An error occurred. Artist ' + oArtist.name +
                  ' could not be listed.', 'error')

    if error:
        return redirect(url_for('edit_artist', artist_id=artist_id))

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id).__dict__
    venue['genres'] = venue['genres'][1:-1].replace('"', '').split(',')
    form = VenueForm(MultiDict(venue))
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # venue record with ID <venue_id> using the new attributes
    # Load the existing Venue
    oVenue = Venue.query.get(venue_id)
    # Update the Venue instance from the data in the form
    oVenue.name = request.form.get('name', '')
    oVenue.genres = request.form.getlist('genres')
    oVenue.city = request.form.get('city', '')
    oVenue.state = request.form.get('state', '')
    oVenue.address = request.form.get('address', '')
    oVenue.phone = request.form.get('phone', '')
    oVenue.facebook_link = request.form.get('facebook_link', '')

    # Finds if the name is taken by another Venue
    error = False
    exists = len(
        Venue.query
        .filter(db.func.lower(Venue.name) == db.func.lower(oVenue.name),
                Venue.id != venue_id)
        .all()) > 0

    # Update the Venue only if it doesn't exist
    if exists:
        error = True
        flash('An error occurred. Another venue ' +
              oVenue.name + ' exists already.', 'error')
    else:
        try:
            db.session.commit()
            # on successful db insert, flash success
            flash('Venue ' + oVenue.name + ' was successfully updated!')
        except Exception:
            error = True
            db.session.rollback()
            flash('An error occurred. Venue ' + oVenue.name +
                  ' could not be listed.', 'error')

    if error:
        return redirect(url_for('edit_venue', venue_id=venue_id))

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # Called upon submitting the new artist listing form.
    # Grab data from form.
    artist = {
        "name": request.form.get('name', ''),
        "genres": request.form.getlist('genres'),
        "city": request.form.get('city', ''),
        "state": request.form.get('state', ''),
        "phone": request.form.get('phone', ''),
        "website": None,
        "facebook_link": request.form.get('facebook_link', ''),
    }
    # Make an instance from the data
    newArtist = Artist(**artist)
    error = False
    exists = len(
        Artist.query
        .filter(db.func.lower(Artist.name) == db.func.lower(newArtist.name))
        .all()) > 0

    # Inserts the venue only if it doesn't exist
    if exists:
        error = True
        flash('An error occurred. Artist ' +
              newArtist.name + ' exists already.', 'error')
    else:
        try:
            db.session.add(newArtist)
            db.session.commit()
            # on successful db insert, flash success
            flash('Artist ' + newArtist.name + ' was successfully listed!')
        except Exception:
            error = True
            db.session.rollback()
            flash('An error occurred. Artist ' + newArtist.name +
                  ' could not be listed.', 'error')

    if error:
        form = ArtistForm(**artist)
        return render_template('forms/new_artist.html', form=form)

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    data = fetch_shows()
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db,
    # upon submitting new show listing form
    show = {
        'artist_id': request.form.get('artist_id', ''),
        'venue_id': request.form.get('venue_id', ''),
        'start_time': request.form.get('start_time', '')
    }
    new_show = Show(**show)
    artist_exists = Artist.query.get(new_show.artist_id) is not None
    venue_exists = Venue.query.get(new_show.venue_id) is not None
    old_date = dateutil.parser.parse(
        new_show.start_time).date() <= datetime.today().date()
    error = False
    if not artist_exists:
        error = True
        flash(f'The Artist ID {new_show.artist_id} cannot be found.', 'error')
    if not venue_exists:
        error = True
        flash(f'The Venue ID {new_show.venue_id} cannot be found.', 'error')
    if old_date:
        error = True
        flash(f'The date {new_show.start_time} is a previous date.', 'error')

    if not error:
        try:
            db.session.add(new_show)
            db.session.commit()
            # on successful db insert, flash success
            flash('Show was successfully listed!')
        except Exception:
            error = True
            db.session.rollback()
            flash('An error occurred. Show could not be listed.', 'error')

    if error:
        form = ShowForm(**show)
        return render_template('forms/new_show.html', form=form)

    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
            '[in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
