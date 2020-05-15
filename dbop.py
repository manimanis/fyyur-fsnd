from app import db, Venue, Artist, Show


def fetch_venues_cities_and_states():
    """
  :return: (city, state)
  """
    return db.session.query(
        Venue.city,
        Venue.state
    ).group_by(Venue.state, Venue.city).all()


def fetch_num_upcoming_show_byvenue(venue_id):
    count = (db.session
             .query(db.func.count(Show.venue_id))
             .group_by(Show.venue_id)
             .filter(Show.start_time > db.func.current_timestamp(),
                     Show.venue_id == venue_id)
             .scalar())
    return count if count is not None else 0


def fetch_num_upcoming_show_by_artist(artist_id):
    count = (db.session
             .query(db.func.count(Show.artist_id))
             .group_by(Show.artist_id)
             .filter(Show.start_time > db.func.current_timestamp(),
                     Show.artist_id == artist_id)
             .scalar())
    return count if count is not None else 0


def fill_num_upcoming_shows(venue_dict):
    """
    :param venue_dict: a dict containing Venue.id, Venue.name
    :return:
    """
    num_upcoming_shows = fetch_num_upcoming_show_byvenue(venue_dict['id'])
    venue_dict['num_upcoming_shows'] = num_upcoming_shows


def fetch_venues():
    """
    :return: list of venues
    """
    venues = Venue.query.order_by(Venue.state, Venue.city).all()
    data = []
    for venue in venues:
        if len(data) == 0
        or venue.city != data[-1]['city']
        or venue.state != data[-1]['state']:
            data.append({
                'city': venue.city,
                'state': venue.state,
                'venues': []
            })
        venue_dict = {
            'id': venue.id,
            'name': venue.name
        }
        fill_num_upcoming_shows(venue_dict)
        data[-1]['venues'].append(venue_dict)
    return data


def fetch_venue_byname(name):
    """
    :param name:
    :return: search all the venues which contains 'name'
    """
    venues = (Venue.query
              .filter(Venue.name.ilike(f'%{name}%'))
              .order_by(Venue.state, Venue.city)
              .all())
    data = []
    for venue in venues:
        venue_dict = {
            'id': venue.id,
            'name': venue.name
        }
        fill_num_upcoming_shows(venue_dict)
        data.append(venue_dict)
    return data


def fetch_past_shows_by_venue(venue_id):
    """
    :param venue_id:
    :return: list of past shows
    """
    shows = (db.session
             .query(Artist.id,
                    Artist.name,
                    Artist.image_link,
                    Show.start_time)
             .join(Venue, Venue.id == Show.venue_id)
             .join(Artist, Artist.id == Show.artist_id)
             .filter(Show.start_time <= db.func.current_timestamp(),
                     Venue.id == venue_id)
             .all())
    data = []
    for show in shows:
        data.append({
            "artist_id": show[0],
            "artist_name": show[1],
            "artist_image_link": show[2],
            "start_time": str(show[3])
        })
    return data


def fetch_past_shows_by_artist(artist_id):
    """
    :param artist_id:
    :return: list of past shows
    """
    shows = (db.session
             .query(Venue.id, Venue.name, Venue.image_link, Show.start_time)
             .join(Venue, Venue.id == Show.venue_id)
             .join(Artist, Artist.id == Show.artist_id)
             .filter(Show.start_time <= db.func.current_timestamp(),
                     Artist.id == artist_id)
             .all())
    data = []
    for show in shows:
        data.append({
            "venue_id": show[0],
            "venue_name": show[1],
            "venue_image_link": show[2],
            "start_time": str(show[3])
        })
    return data


def fetch_upcoming_shows_by_artist(artist_id):
    """
    :param artist_id:
    :return: list of past shows
    """
    shows = (db.session
             .query(Venue.id, Venue.name, Venue.image_link, Show.start_time)
             .join(Venue, Venue.id == Show.venue_id)
             .join(Artist, Artist.id == Show.artist_id)
             .filter(Show.start_time > db.func.current_timestamp(),
                     Artist.id == artist_id)
             .all())
    data = []
    for show in shows:
        data.append({
            "venue_id": show[0],
            "venue_name": show[1],
            "venue_image_link": show[2],
            "start_time": str(show[3])
        })
    return data


def fetch_upcoming_shows_by_venue(venue_id):
    """
        :param venue_id:
        :return: list of past shows
        """
    shows = (db.session
             .query(Artist.id, Artist.name, Artist.image_link, Show.start_time)
             .join(Venue, Venue.id == Show.venue_id)
             .join(Artist, Artist.id == Show.artist_id)
             .filter(Show.start_time > db.func.current_timestamp(),
                     Venue.id == venue_id)
             .all())
    data = []
    for show in shows:
        data.append({
            "artist_id": show[0],
            "artist_name": show[1],
            "artist_image_link": show[2],
            "start_time": str(show[3])
        })
    return data


def fetch_artists():
    return Artist.query.order_by(Artist.name).all()


def fetch_artists_by_name(name):
    """
    :param name:
    :return: search all the venues which contains 'name'
    """
    artists = (Artist.query
               .filter(Artist.name.ilike(f'%{name}%'))
               .order_by(Artist.name)
               .all())
    data = []
    for artist in artists:
        artist_dict = {
            'id': artist.id,
            'name': artist.name,
            'num_upcoming_shows': fetch_num_upcoming_show_by_artist(artist.id)
        }
        data.append(artist_dict)
    return data


def fetch_shows():
    shows = (db.session
             .query(Venue.id,
                    Venue.name,
                    Artist.id,
                    Artist.name,
                    Artist.image_link,
                    Show.start_time)
             .join(Venue, Venue.id == Show.venue_id)
             .join(Artist, Artist.id == Show.artist_id)
             .all())
    data = []
    for show in shows:
        data.append({
            "venue_id": show[0],
            "venue_name": show[1],
            "artist_id": show[2],
            "artist_name": show[3],
            "artist_image_link": show[4],
            "start_time": str(show[5])
        })
    return data
