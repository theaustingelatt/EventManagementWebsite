from . import db
from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# User model representing each registered user
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    # Unique identifier for each user
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    contact_number = db.Column(db.String(15), nullable=False)
    street_address = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    # Relationships to other models
    events = db.relationship('Event', backref='creator', lazy=True)
    bookings = db.relationship('Booking', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)

# Event model representing individual events created by users
class Event(db.Model):
    __tablename__ = 'events'

    # Basic event details
    id = db.Column(db.Integer, primary_key=True)
    game = db.Column(db.String(100), nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=False)

    # Participant and spectator information
    participants = db.Column(db.Integer, default=0)
    max_participants = db.Column(db.Integer, nullable=False, default=0)
    spectators = db.Column(db.Integer, default=0)
    max_spectators = db.Column(db.Integer, nullable=False, default=0)

    # Event timing and status
    date_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum('Open', 'Inactive', 'Sold Out', 'Cancelled', name='event_status'), nullable=False)
    image_url = db.Column(db.String(255))
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ticket_price = db.Column(db.Float, nullable=False, default=0.0)

    # Relationships to other models
    bookings = db.relationship('Booking', backref='event', lazy=True)
    comments = db.relationship('Comment', backref='event', lazy=True)

    # Method to update event status based on conditions
    def update_status(self):
        current_time = datetime.utcnow()
        
        # Check if the event has been explicitly cancelled
        if self.status == 'Cancelled':
            return  # No further updates if the event is cancelled
        
        # Check if the event date has passed
        if self.date_time < current_time:
            self.status = 'Inactive'
        # Check if the event is sold out when participants reach the max limit
        elif self.participants >= self.max_participants:
            self.status = 'Sold Out'
        # Otherwise, set the status to Open
        else:
            self.status = 'Open'

# Booking model representing bookings made by users for events
class Booking(db.Model):
    __tablename__ = 'bookings'

    # Booking details
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    order_id = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), default='active', nullable=False)
    is_spectator = db.Column(db.Boolean, default=False)

# Comment model representing comments posted by users on events
class Comment(db.Model):
    __tablename__ = 'comments'

    # Comment details
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)

# SearchEvent model representing historical event searches
class SearchEvent(db.Model):
    __tablename__ = 'search_events'

    # Search event details
    id = db.Column(db.Integer, primary_key=True)
    game = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    participants = db.Column(db.Integer)
    price = db.Column(db.Float)
    date_time = db.Column(db.DateTime, nullable=False)
    event_type = db.Column(db.String(100), nullable=False)

    # String representation for debugging
    def __repr__(self):
        return f"<SearchEvent {self.id}: {self.game}>"

# ContactMessage model representing messages sent via a contact-form
class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'

    # Message details
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # String representation for debugging
    def __repr__(self):
        return f'<ContactMessage {self.name}>'
