#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
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

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))

    def __repr__(self):
      return f'<Venue {self.name}>'

    def get_upcoming_shows(self):
      shows = Shows.query.filter(Shows.venue_id==self.id, Shows.start_time > datetime.now())
      return self.get_show_list(shows)

    def get_past_shows(self):
      shows = Shows.query.filter(Shows.venue_id==self.id, Shows.start_time < datetime.now())
      return self.get_show_list(shows)

    def get_show_list(self, shows):
      show_list = []
      for show in shows:
        show_list.append(
          {
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": str(show.start_time)
          }
        )
      return show_list

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
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))

    def __repr__(self):
      return f'<Artist {self.name}>'

    def get_upcoming_shows(self):
      shows = Shows.query.filter(Shows.artist_id==self.id, Shows.start_time > datetime.now())
      return self.get_show_list(shows)

    def get_past_shows(self):
      shows = Shows.query.filter(Shows.artist_id==self.id, Shows.start_time < datetime.now())
      return self.get_show_list(shows)

    def get_show_list(self, shows):
      show_list = []
      for show in shows:
        show_list.append(
          {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": str(show.start_time)
          }
        )
      return show_list


  
class Shows(db.Model):
  __tablename__ = 'Shows'

  id = db.Column(db.Integer, primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  start_time = db.Column(db.DateTime())

  venue = db.relationship('Venue', backref=db.backref('shows', cascade='all, delete'))
  artist = db.relationship('Artist', backref=db.backref('shows', cascade='all, delete'))

  def __repr__(self):
    return f'<Show {self.venue}, {self.artist}>'


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
  unique_cities = Venue.query.distinct(Venue.city, Venue.state).all()
  data = []
  for unique_city in unique_cities:
    city_item = {}
    city_item['city'] = unique_city.city
    city_item['state'] = unique_city.state
    venues = Venue.query.filter_by(city=unique_city.city, state=unique_city.state).all()
    venue_list = []
    for venue in venues:
      venue_list.append(
        {
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": len(venue.get_upcoming_shows())
        }
      )
    city_item['venues'] = venue_list
    data.append(city_item)

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():

  search_term = request.form.get('search_term', '')
  search_query = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()

  data = []
  for venue in search_query:
      data.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(venue.get_upcoming_shows())
      })

  response={
    "count": len(search_query),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id

  venue = Venue.query.get(venue_id)
  past_shows = venue.get_past_shows()
  upcoming_shows = venue.get_upcoming_shows()
  
  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres.split(',') if venue.genres else [],
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone":  venue.phone,
    "website":  venue.website,
    "facebook_link":  venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description":  venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
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

  try:
    form = VenueForm(request.form)

    venue = Venue(
      name=form.name.data,
      genres=','.join(form.genres.data),
      city=form.city.data,
      state=form.state.data,
      address=form.address.data,
      phone=form.phone.data,
      image_link=form.image_link.data,
      facebook_link=form.facebook_link.data,
      website=form.website_link.data,
      seeking_talent=form.seeking_talent_check.data,
      seeking_description=form.seeking_talent_description.data
    )
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()

  return redirect(url_for('index'))

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():

  search_term = request.form.get('search_term', '')
  search_query = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

  data = []
  for artist in search_query:
      data.append({
        "id": artist.id,
        "name": artist.name,
        "num_upcoming_shows": len(artist.get_upcoming_shows())
      })

  response={
    "count": len(search_query),
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  past_shows = artist.get_past_shows()
  upcoming_shows = artist.get_upcoming_shows()
  
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres.split(',') if artist.genres else [],
    "city": artist.city,
    "state": artist.state,
    "phone":  artist.phone,
    "website":  artist.website,
    "facebook_link":  artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description":  artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  artist_query = Artist.query.get(artist_id)
  if artist_query is None:
    abort(404)

  artist={
    "id": artist_query.id,
    "name": artist_query.name,
    "genres": artist_query.genres.split(',') if artist_query.genres else [],
    "city": artist_query.city,
    "state": artist_query.state,
    "phone": artist_query.phone,
    "website_link": artist_query.website,
    "facebook_link": artist_query.facebook_link,
    "seeking_venue": artist_query.seeking_venue,
    "seeking_description": artist_query.seeking_description,
    "image_link": artist_query.image_link
  }
  form = ArtistForm(data=artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    artist = Artist.query.get(artist_id)
    form = ArtistForm(request.form)

    artist.name = form.name.data
    artist.genres = ','.join(form.genres.data)
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.image_link = form.image_link.data
    artist.facebook_link = form.facebook_link.data
    artist.website = form.website_link.data
    artist.seeking_venue = form.seeking_venue_check.data
    artist.seeking_description = form.seeking_venue_description.data
    
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

  venue_query = Venue.query.get(venue_id)
  if venue_query is None:
    abort(404)

  venue={
    "id": venue_query.id,
    "name": venue_query.name,
    "genres": venue_query.genres.split(',') if venue_query.genres else [],
    "address": venue_query.address,
    "city": venue_query.city,
    "state": venue_query.state,
    "phone": venue_query.phone,
    "website_link": venue_query.website,
    "facebook_link": venue_query.facebook_link,
    "seeking_talent": venue_query.seeking_talent,
    "seeking_description": venue_query.seeking_description,
    "image_link": venue_query.image_link
  }
  form = VenueForm(data=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    form = VenueForm(request.form)

    venue.name = form.name.data
    venue.genres = ','.join(form.genres.data)
    venue.address = form.address.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.phone = form.phone.data
    venue.image_link = form.image_link.data
    venue.facebook_link = form.facebook_link.data
    venue.website = form.website_link.data
    venue.seeking_talent = form.seeking_talent_check.data
    venue.seeking_description = form.seeking_talent_description.data
    
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  try:
    form = ArtistForm(request.form)

    artist = Artist(
      name=form.name.data,
      genres=','.join(form.genres.data),
      city=form.city.data,
      state=form.state.data,
      phone=form.phone.data,
      image_link=form.image_link.data,
      facebook_link=form.facebook_link.data,
      website=form.website_link.data,
      seeking_venue=form.seeking_venue_check.data,
      seeking_description=form.seeking_venue_description.data
    )
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()

  return redirect(url_for('index'))



#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  shows = Shows.query.all()
  data = []
  for show in shows:
    show_data = {
      'venue_id': show.venue_id,
      'venue_name': show.venue.name,
      'artist_id':  show.artist_id,
      'artist_name':  show.artist.name,
      'artist_image_link':  show.artist.image_link,
      'start_time': str(show.start_time)
    }
    data.append(show_data)

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # on successful db insert, flash success
  # on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/

  try:
    form = ShowForm(request.form)
    show = Shows(
      venue_id=form.venue_id.data,
      artist_id=form.venue_id.data,
      start_time=form.start_time.data
    )
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()

  return redirect(url_for('index'))


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
