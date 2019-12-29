#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)
session = db.session


# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.ARRAY(db.String()), nullable=False)
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(150))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    location_id = db.Column(db.Integer, db.ForeignKey('Locations.id'), nullable=False)
    artists = db.relationship('Shows', back_populates='venue', cascade='all, delete-orphan')

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.ARRAY(db.String()), nullable=False)
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(150))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    location_id = db.Column(db.Integer, db.ForeignKey('Locations.id'), nullable=False)
    shows = db.relationship('Shows', back_populates='artist', cascade='all, delete-orphan')
 
class Shows(db.Model):
    __tablename__ = "Shows"

    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False, primary_key=True)
    artist = db.relationship("Artist",  back_populates='shows')
    venue = db.relationship("Venue",   back_populates='artists')

class Locations(db.Model):
    __tablename__ = "Locations"

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(120), nullable=False, unique=True)
    state = db.Column(db.String(120), nullable=False)
    artist =   db.relationship('Artist', backref="location", lazy=False, cascade='all, delete-orphan')
    venue =   db.relationship('Venue', backref="location", lazy=False, cascade='all, delete-orphan')

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  error=False

  try:
    data = []
    locations = Locations.query.order_by('id').all()

    for location in locations:
      venues = {}
      venues["city"] = location.city
      venues["state"] = location.state
      venues["venues"] = []  

      location_venues =  Venue.query.filter_by(location_id=location.id).order_by('id').all()

      for venue in location_venues:
        location_venue = {}
        location_venue['id'] = venue.id
        location_venue['name'] = venue.name
        location_venue["num_upcoming_shows"] = 0

        venues['venues'].append(location_venue)

      if bool(location_venues): data.append(venues)
  except:
    error=True
  finally:
    if error:
      abort(500)
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  search_term = request.form['search_term']
  results = session.query(Venue.id, Venue.name).filter(Venue.name.ilike(f"%{search_term}%")).all()

  response = {
    "count": len(results),
    "data": [{
      "id": id,
      "name": name 
      }
    for id, name in results]
  }
  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  error=False
  results=False

  try:
    results = session.query(Venue, Locations).filter(Venue.id == venue_id).\
                      join(Locations, Venue.location_id == Locations.id).first()

    venue, location = results
    
    venue_details = {
      "id": venue.id,
      "name": venue.name,
      "genres": venue.genres,
      "address": venue.address,
      "city": location.city,
      "state": location.state,
      "phone": venue.phone,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
      }

    past_shows = []
    upcoming_shows= []

    shows = session.query(Shows.start_time, Artist).filter_by(venue_id = venue.id)\
            .join(Artist, Artist.id == Shows.artist_id).all()
    
    for start_time, artist in shows:
      show_details = {
        "artist_id": artist.id,
        "artist_name": artist.name,
        "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
        "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S")
      }

      if start_time < datetime.now():
        past_shows.append(show_details)
      else:
        upcoming_shows.append(show_details)

    venue_details["past_shows"] = past_shows
    venue_details["upcoming_shows"] = upcoming_shows
    venue_details["past_shows_count"] = len(past_shows)
    venue_details["upcoming_shows_count"] = len(upcoming_shows)
  except:
    error=True
  finally:
    if error:
      if results is None: abort(404)
      else: abort(500)
    return render_template('pages/show_venue.html', venue=venue_details)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  error=False
  try:
    venue = Venue(name=request.form['name'], 
                address=request.form['address'],
                phone=request.form['phone'],
                genres=request.form.getlist('genres'),
                website=request.form['website'],
                facebook_link=request.form['facebook_link'],
                seeking_talent=bool(request.form.get('seeking_talent')),
                seeking_description=request.form.get('seeking_description')
                )

    location = Locations(city=request.form['city'], state=request.form['state'])

    city_exists = Locations.query.filter_by(city=location.city).scalar() is not None
    if city_exists:
      location = Locations.query.filter_by(city=location.city).first()

    venue.location = location

    session.add(venue)
    session.commit()
  except:
    error=True
    session.rollback()
  finally:
    session.close()
    if error:
      flash('An error occurred. Venue ' + venue.name + ' could not be listed.')
    else:
      flash('Venue ' + request.form['name'] + ' was successfully listed!')

  # on successful db insert, flash success
  # flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    venue = session.query(Venue).filter(Venue.id == venue_id).first()
    session.delete(venue)
    session.commit()
  except:
    session.rollback()
  finally:
    session.close()
    flash('Venue deleted!')
    return jsonify({'success': True})

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  error=False
  try:
    artists = Artist.query.order_by('id').all()
    data = [{"id":artist.id, "name":artist.name} for artist in artists]
  except:
    error=True
  finally:
    if error:
      abort(500)
    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  search_term = request.form['search_term']
  results = session.query(Artist.id, Artist.name).filter(Artist.name.ilike(f"%{search_term}%")).all()

  response = {
    "count": len(results),
    "data": [{
      "id": id,
      "name": name
      }
    for id, name in results]
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  error=False
  results=False
  try:
    results = session.query(Artist, Locations).filter(Artist.id == artist_id).\
              join(Locations, Artist.location_id == Locations.id).first()

    artist, location = results

    artist_details = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": location.city,
    "state": location.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
    }

    past_shows = []
    upcoming_shows= []

    shows =  session.query(Shows.start_time, Venue).filter_by(artist_id = artist.id).join(Venue, Venue.id == Shows.venue_id).all()

    for start_time, venue in shows:
      show_details = {
        "venue_id": venue.id,
        "venue_name": venue.name,
        "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
        "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S")
      }

      if start_time < datetime.now():
        past_shows.append(show_details)
      else:
        upcoming_shows.append(show_details)

    artist_details["past_shows"] = past_shows
    artist_details["upcoming_shows"] = upcoming_shows
    artist_details["past_shows_count"] = len(past_shows)
    artist_details["upcoming_shows_count"] = len(upcoming_shows)

  except:
    error=True
  finally:
    if error:
      if results is None: abort(404)
      else: abort(500)
    return render_template('pages/show_artist.html', artist=artist_details)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  error=False
  results=False

  try:
    results = session.query(Artist, Locations).filter(Artist.id == artist_id).join(Locations, Artist.location_id == Locations.id).first()

    artist, location = results

    form = ArtistForm(
      id=artist.id,
      name=artist.name,
      genres=artist.genres,
      city=location.city,
      state=location.state,
      phone=artist.phone,
      website=artist.website,
      facebook_link=artist.facebook_link,
      seeking_venue=artist.seeking_venue,
      seeking_description=artist.seeking_description
    )
  except:
    error=True

  finally:
    if error:
      if results is None: abort(404)
      else: abort(500)
    return render_template('forms/edit_artist.html', form=form, artist=artist)

  # TODO: populate form with fields from artist with ID <artist_id>
  

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error=False

  try:
    artist_data = dict(name=request.form['name'], 
                  phone=request.form['phone'],
                  genres=request.form.getlist('genres'),
                  website=request.form['website'],
                  facebook_link=request.form['facebook_link'],
                  seeking_venue=bool(request.form.get('seeking_venue')),
                  seeking_description=request.form.get('seeking_description')
    )
    
    location = Locations.query.filter_by(city=request.form['city']).first()

    if location is None:
      location = Locations(city=request.form['city'], state=request.form['state'])

    Artist.query.get(artist_id).location = location
   
    artist_updated_rows = Artist.query.filter_by(id = artist_id).update(artist_data)
    session.commit()
  except:
    error=True
    session.rollback()
  finally:
    session.close()
    if error:
      flash("Nothing changed.")
    else:
       flash('Profile updated!')
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  error=False
  results=False

  try:
    results = session.query(Venue, Locations).filter(Venue.id == venue_id).\
              join(Locations, Venue.location_id == Locations.id).first()

    venue, location = results

    form = VenueForm(
      id=venue.id,
      name=venue.name,
      genres=venue.genres,
      address=venue.address,
      city=location.city,
      state=location.state,
      phone=venue.phone,
      website=venue.website,
      facebook_link=venue.facebook_link,
      seeking_talent=venue.seeking_talent,
      seeking_description=venue.seeking_description,
      image_link=venue.image_link
    )
  except:
    error=True

  finally:
    if error:
      if results is None: abort(404)
      else: abort(500)
    return render_template('forms/edit_venue.html', form=form, venue=venue)

  # TODO: populate form with values from venue with ID <venue_id>

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error=False

  try:
    venue_data = dict(name=request.form['name'], 
                  address=request.form['address'],
                  phone=request.form['phone'],
                  genres=request.form.getlist('genres'),
                  website=request.form['website'],
                  facebook_link=request.form['facebook_link'],
                  seeking_talent=bool(request.form.get('seeking_talent')),
                  seeking_description=request.form.get('seeking_description')
    )

    location = Locations.query.filter_by(city=request.form['city']).first()

    if location is None:
      location = Locations(city=request.form['city'], state=request.form['state'])

    Venue.query.get(venue_id).location = location

    venue_updated_rows = Venue.query.filter_by(id = venue_id).update(venue_data)
    session.commit() 

  except:
    error=True
    session.rollback()
  finally:
    session.close()
    if error:
      flash('Nothing changed.')
    else:
      flash('Venue updated!')
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  error=False
  try:
    artist = Artist(name=request.form['name'], 
                  phone=request.form['phone'],
                  genres=request.form.getlist('genres'),
                  website=request.form['website'],
                  facebook_link=request.form['facebook_link'],
                  seeking_venue=bool(request.form.get('seeking_venue')),
                  seeking_description=request.form.get('seeking_description')
    )
    
    location = Locations(city=request.form['city'], state=request.form['state'])

    city_exists = Locations.query.filter_by(city=location.city).scalar() is not None
    if city_exists:
      location = Locations.query.filter_by(city=location.city).first()

    artist.location = location      

    session.add(artist)
    session.commit()
  except:
    error=True
    session.rollback()
    print(sys.exc_info())
  finally:
    session.close()
    if error == True:
      flash('An error occurred. Artist ' + artist.name + ' could not be listed.')
    else: 
      flash('Artist ' + request.form['name'] + ' was successfully listed!')

  # on successful db insert, flash success
  # flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  joined_data = session.query(Artist, Shows.start_time, Venue).join(Shows, Artist.id == Shows.artist_id).join(Venue, Venue.id == Shows.venue_id).all() 
  
  data = [{
      "venue_id": venue.id,
      "venue_name": venue.name,
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
      "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S")
    }
    for artist, start_time, venue in joined_data
    ]

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  error=False
  try:
    start_time = (request.form['start_time'])

    artist = Artist.query.filter_by(id = request.form['artist_id']).one()
    venue = Venue.query.filter_by(id = request.form['venue_id']).one()
    
    show = Shows(start_time=start_time)

    show.venue = venue
    show.artist = artist

    session.add(show)
    session.commit()
  except:
    error=True
    session.rollback()
  finally:
    session.close()
    if error:
      flash('An error occurred. Show could not be listed.')
    else:
      flash('Show was successfully listed!')


  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
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
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
