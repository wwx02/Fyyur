# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import logging
import re
from logging import Formatter, FileHandler

import babel
import dateutil.parser
from flask import render_template, request, flash, redirect, url_for, abort
from sqlalchemy import and_

from config import *
from forms import *
from models.Artist import Artist
from models.Show import Show
from models.Venue import Venue

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    venues= Venue.query.order_by(Venue.created_at.desc()).limit(10).all()
    artists = Artist.query.order_by(Artist.created_at.desc()).limit(10).all()
    return render_template('pages/home.html', artists= artists, venues=venues)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # replace with real venues data.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    data = Venue.query.with_entities(Venue.city, Venue.state).distinct().all()
    data = [dict(x) for x in data]
    for area in data:
        venues = Venue.query.with_entities(Venue.id, Venue.name).filter_by(city=area["city"], state=area["state"]).all()
        venues = [dict(v) for v in venues]
        for venue in venues:
            num = Show.query.filter_by(venue_id=venue["id"]).filter(Show.start_time>datetime.utcnow()).count()
            venue["num_upcoming_show"] = num
        area["venues"] = venues
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    #  implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    # extra search by city and state
    term = request.form.get('search_term', '')
    state = term.split(",")
    data = Venue.query.filter(Venue.name.ilike("%{}%".format(term)))
    if (len(state) == 2):
        data = data.union_all(
            Venue.query.filter(Venue.city.ilike(state[0].strip()), Venue.state.ilike(state[1].strip())))

    data = data.with_entities(Venue.id, Venue.name).all()
    print(data)
    data = [dict(v) for v in data]
    for artist in data:
        num = Show.query.filter_by(venue_id=artist["id"]).filter(Show.start_time > datetime.utcnow()).count()
        artist["num_upcoming_show"] = num
    response = {"count": len(data),
                "data": data}
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # replace with real venue data from the venues table, using venue_id
    data = Venue.query.get(venue_id)
    data = data.__dict__
    past_shows = Show.query.filter_by(venue_id=venue_id).filter(Show.start_time<datetime.utcnow()).with_entities(Show.artist_id,
                                                                 Artist.name.label("artist_name"),
                                                                 Artist.image_link.label("artist_image_link"),
                                                                 Show.start_time).join(Artist).all()
    past_shows = [dict(s) for s in past_shows]
    for s in past_shows:
        s["start_time"] = str(s["start_time"])
    data["past_shows"] = past_shows

    upcoming_shows = Show.query.filter_by(venue_id=venue_id).filter(Show.start_time>datetime.utcnow()).with_entities(Show.artist_id,
                                                                 Artist.name.label("artist_name"),
                                                                 Artist.image_link.label("artist_image_link"),
                                                                 Show.start_time).join(Artist).all()
    upcoming_shows = [dict(s) for s in upcoming_shows]
    for s in upcoming_shows:
        s["start_time"] = str(s["start_time"])
    data["upcoming_shows"] = upcoming_shows
    data["genres"] = data["genres"].split(",")
    data["upcoming_shows_count"] = len(data["upcoming_shows"])
    data["past_shows_count"] = len(data["past_shows"])
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    #  insert form data as a new Venue record in the db, instead
    #  modify data to be the data object returned from db insertion
    form = VenueForm(request.form)
    if form.validate():
        try:
            venue = Venue(name=form.name.data.strip(),
                          city=form.city.data.strip(),
                          state=form.state.data.strip(),
                          address=form.address.data.strip(),
                          genres= ",".join(form.genres.data),
                        seeking_talent=form.seeking_talent.data,
                        phone= form.phone.data,
                      image_link= form.image_link.data.strip(),
                      facebook_link= form.facebook_link.data.strip(),
                      website= form.website_link.data.strip(),
                      seeking_description = form.seeking_description.data.strip(),
                      created_at= datetime.today())
            db.session.add(venue)
            db.session.commit()

    # on successful db insert, flash success
            flash('Venue ' + form.name.data + ' was successfully listed!')
        except:
            db.session.rollback()
            flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
        finally:
            db.session.close()
    else:
        for field, message in form.errors.items():
            flash(field + ' - ' + str(message), 'danger')
    return redirect(url_for('index'))
    # e.g.,
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/



@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        venue = Venue.query.get(venue_id)
        name = venue.name
        db.session.delete(venue)
        db.session.commit()
        flash('Venue ' + name + ' was successfully deleted!')
    except:
        flash('An error occurred. Venue ' + name + ' could not be deleted.')
        db.session.rollback()
    finally:
        db.session.close()
    #  Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
        return redirect(url_for("index"))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    #  replace with real data returned from querying the database
    data = Artist.query.with_entities(Artist.id, Artist.name).all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    #  implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    # extra search by city and state
    term = request.form.get('search_term', '')
    state = term.split(",")
    data = Artist.query.filter(Artist.name.ilike("%{}%".format(term)))
    if (len(state) == 2):
        data = data.union_all(
            Artist.query.filter(Artist.city.ilike(state[0].strip()), Artist.state.ilike(state[1].strip())))

    data = data.with_entities(Artist.id, Artist.name).all()
    print(data)
    data = [dict(v) for v in data]
    for artist in data:
        num = Show.query.filter_by(artist_id=artist["id"]).filter(Show.start_time > datetime.utcnow()).count()
        artist["num_upcoming_show"] = num
    response = {"count": len(data),
                "data": data}
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    #  replace with real artist data from the artist table, using artist_id
    data = Artist.query.get(artist_id)
    if (data is None):
        abort(404)
    data = data.__dict__
    past_shows = Show.query.filter_by(artist_id=artist_id).filter(Show.start_time<datetime.utcnow()).with_entities(Show.venue_id,
                                                                                         Venue.name.label("venue_name"),
                                                                                         Venue.image_link.label(
                                                                                             "venue_image_link"),
                                                                                         Show.start_time).join(Venue).all()
    past_shows = [dict(s) for s in past_shows]
    for s in past_shows:
        s["start_time"] = str(s["start_time"])
    data["past_shows"] = past_shows

    upcoming_shows = Show.query.filter_by(artist_id=artist_id).filter(Show.start_time>datetime.utcnow()).with_entities(Show.venue_id,
                                                                                            Venue.name.label(
                                                                                                "venue_name"),
                                                                                            Venue.image_link.label(
                                                                                                "venue_image_link"),
                                                                                            Show.start_time).join(
        Venue).all()
    upcoming_shows = [dict(s) for s in upcoming_shows]
    for s in upcoming_shows:
        s["start_time"] = str(s["start_time"])
    data["past_shows"] = past_shows
    data["upcoming_shows"] = upcoming_shows
    data["genres"] = data["genres"].split(",")
    data["upcoming_shows_count"] = len(data["upcoming_shows"])
    data["past_shows_count"] = len(data["past_shows"])
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    if (artist is None):
        abort(404)
    form = ArtistForm(obj=artist)
    #populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    #  take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    form = ArtistForm(request.form)
    if form.validate():
        try:
            artist = Artist.query.get(artist_id)
            artist.name=form.name.data.strip()
            artist.city=form.city.data.strip()
            artist.state=form.state.data.strip()
            artist.genres=",".join(form.genres.data)
            artist.seeking_venue=form.seeking_venue.data
            artist.phone=form.phone.data
            artist.image_link=form.image_link.data.strip()
            artist.facebook_link=form.facebook_link.data.strip()
            artist.website=form.website_link.data.strip()
            artist.seeking_description=form.seeking_description.data.strip()
            artist.availability= form.availability.data.strip()
            db.session.commit()

        # on successful db insert, flash success
            flash('Artist ' + form.name.data + ' was successfully edited!')
        except:
            db.session.rollback()
            flash('An error occurred. Artist ' + form.name.data + ' could not be edited.')
        finally:
            db.session.close()
    else:
        for field, message in form.errors.items():
            flash(field + ' - ' + str(message), 'danger')
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    if venue is None:
        abort(404)
    form = VenueForm(obj=venue)
    #  populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    #  take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    form = VenueForm(request.form)
    if form.validate():
        try:
            venue = Venue.query.get(venue_id)
            venue.name=form.name.data.strip()
            venue.city=form.city.data.strip()
            venue.state=form.state.data.strip()
            venue.address=form.address.data.strip()
            venue.genres=",".join(form.genres.data)
            venue.seeking_talent=form.seeking_talent.data
            venue.phone=form.phone.data
            venue.image_link=form.image_link.data.strip()
            venue.facebook_link=form.facebook_link.data.strip()
            venue.website=form.website_link.data.strip()
            venue.seeking_description=form.seeking_description.data.strip()

            db.session.commit()

        # on successful db insert, flash success
            flash('Venue ' + form.name.data + ' was successfully edited!')
        except:
            db.session.rollback()
            flash('An error occurred. Venue ' + form.name.data + ' could not be edited.')
        finally:
            db.session.close()
    else:
        for field, message in form.errors.items():
            flash(field + ' - ' + str(message), 'danger')
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
    # insert form data as a new Artist record in the db, instead
    #  modify data to be the data object returned from db insertion
    form = ArtistForm(request.form)
    if form.validate():
        try:
            artist = Artist(name=form.name.data.strip(),
                      city=form.city.data.strip(),
                      state=form.state.data.strip(),
                      genres=",".join(form.genres.data),
                      seeking_venue=form.seeking_venue.data,
                      phone=form.phone.data,
                      image_link=form.image_link.data.strip(),
                      facebook_link=form.facebook_link.data.strip(),
                      website=form.website_link.data.strip(),
                      seeking_description=form.seeking_description.data.strip(),
                      created_at= datetime.today(),
                      availability= form.availability.data.strip())
            db.session.add(artist)
            db.session.commit()

        # on successful db insert, flash success
            flash('Artist ' + form.name.data + ' was successfully listed!')
        except:
            db.session.rollback()
            flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
        finally:
            db.session.close()
    else:
        for field, message in form.errors.items():
            flash(field + ' - ' + str(message), 'danger')
    return redirect(url_for('index'))

    #  on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    #  replace with real venues data.
    data = Show.query.with_entities(Show.artist_id, Show.venue_id, Artist.name.label("artist_name"),
                                    Artist.image_link.label("artist_image_link"), Show.start_time,
                                    Venue.name.label("venue_name"), Venue.image_link.label("venue_image_link")).join(
        Artist).join(Venue).all()

    data = [dict(x) for x in data]
    for x in data:
        x["start_time"] = str(x["start_time"])

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # insert form data as a new Show record in the db, instead
    form = ShowForm(request.form)
    artist= Artist.query.get(form.artist_id.data)
    if artist is not None:
        error = False
        if (artist.availability is not None):
            s = "(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])"
            s = s + "-" + s
            times = re.findall(s, artist.availability)
            start= form.start_time.data
            for time in times:
                begin = datetime.replace(start, hour=int(time[0]), minute=int(time[1]))
                end = datetime.replace(start, hour=int(time[2]), minute=int(time[3]))
                if start > begin and start < end:
                    error=True
            if error==False:
                flash("The artist isn't available at that time")
                return(redirect(url_for('create_shows')))
    if form.validate():
        try:
            show= Show(start_time = form.start_time.data,
                venue_id = form.venue_id.data,
                artist_id = form.artist_id.data)
            db.session.add(show)
            db.session.commit()
    # on successful db insert, flash success
            flash('Show was successfully listed!')
    # on unsuccessful db insert, flash an error instead.
        except:
            flash('An error occurred. Show could not be listed.')
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        finally:
            db.session.close()
    else:
        for field, message in form.errors.items():
            flash(field + ' - ' + str(message), 'danger')
    return redirect(url_for('index'))

@app.route('/shows/search', methods=['POST'])
def search_shows():
    # search for shows by date and location
    # search for "New York, NY" gives shows on that state
    # search for 2020-07-06 gives all shows during that date

    term = request.form.get('search_term', '')

    try:
        day = datetime.strptime(term, '%Y-%m-%d')
        new_day = day.replace(hour=23, minute=59)
        data = Show.query.filter(and_(Show.start_time > day, Show.start_time < new_day))
    except ValueError:
        loc = term.split(",")
        if (len(loc)==2):
            data = Show.query.filter(Venue.city.ilike(loc[0].strip()), Venue.state.ilike(loc[1].strip()))
        else:
            data= []

    if not isinstance(data, list):
        data = data.join(Artist).join(Venue).with_entities(Show.artist_id, Show.venue_id, Artist.name.label("artist_name"),
                                                       Artist.image_link.label("artist_image_link"), Show.start_time,
                                                       Venue.name.label("venue_name"),
                                                       Venue.image_link.label("venue_image_link")).all()

        data = [dict(v) for v in data]
        for v in data:
            v["start_time"]= str(v["start_time"])
        response = {"count": len(data),
                "data": data}

    return render_template('pages/show.html', results=response,
                           search_term=request.form.get('search_term', ''))


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
