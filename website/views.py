from flask import Blueprint, render_template, url_for, request, flash, redirect, current_app
from flask_login import current_user, login_required
from .forms import RegisterForm, LoginForm, UpdateProfileForm, ContactForm
from .models import SearchEvent, Event, ContactMessage, User, Booking, Comment
from datetime import datetime
from werkzeug.utils import secure_filename
from . import db
import uuid
import os

#Define blueprint for main views
main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    #Retrieve unique games and locations from the database for search filtering
    games = [game[0] for game in Event.query.with_entities(Event.game)
            .distinct().order_by(Event.game).all()]
    locations = [location[0] for location in Event.query.with_entities(Event.location)
                .distinct().order_by(Event.location).all()]
    
    #Default values for search status and results
    search_performed = False
    results = []
    popular_events = []
    
    #Initialise the contact form
    contact_form = ContactForm()
    
    if request.method == 'POST':
        #Check if the contact form is being submitted
        if 'message' in request.form:
            if contact_form.validate_on_submit():
                contact_message = ContactMessage(
                    name=contact_form.name.data,
                    email=contact_form.email.data,
                    message=contact_form.message.data
                )
                try:
                    #Attempt to save the contact message to the database
                    db.session.add(contact_message)
                    db.session.commit()
                    flash('Thank you for your message! We will get back to you soon.', 'success')
                    #Clear form fields after submission
                    contact_form.name.data = ''
                    contact_form.email.data = ''
                    contact_form.message.data = ''
                except Exception as e:
                    db.session.rollback()
                    flash('An error occurred while sending your message. Please try again.', 'danger')
            else:
                #Display validation errors if form is invalid
                for field, errors in contact_form.errors.items():
                    for error in errors:
                        flash(f'{field.title()}: {error}', 'error')
        else:
            #Handle event search functionality
            game_search = request.form.get('game', '')
            location_search = request.form.get('location', '')
            
            #Query for events that are open or sold out
            query = Event.query.filter(Event.status.in_(['Open', 'Sold Out']))

            if game_search:
                query = query.filter(Event.game == game_search)
            if location_search:
                query = query.filter(Event.location == location_search)

            search_performed = True
            results = query.order_by(Event.date_time.asc()).all()
    
    if not search_performed or not results:
        #Retrieve popular events if no search results
        query = Event.query.filter(
            Event.status.in_(['Open', 'Sold Out'])
        )
        popular_events = query.order_by(Event.participants.desc()).all()
    
    #Initialise registration and login forms for the page
    register_form = RegisterForm()
    login_form = LoginForm()
    
    return render_template('index.html',
                         login_form=login_form,
                         register_form=register_form,
                         popular_events=popular_events,
                         results=results,
                         games=games,
                         locations=locations,
                         search_performed=search_performed,
                         form=contact_form)

@main_bp.route('/create-event', methods=['GET', 'POST'])
@login_required
def create_event():
    if request.method == 'POST':
        #Collect form data
        game = request.form['gameTitle']
        event_type = request.form['eventType']
        description = request.form['eventDescription']
        location = request.form['eventLocation']
        date_time_str = f"{request.form['eventDate']} {request.form['eventTime']}"
        date_time = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M')
        participants = int(request.form.get('participants', 0))
        max_participants = int(request.form.get('max_participants', 1))
        spectators = int(request.form.get('spectators', 0))
        max_spectators = int(request.form.get('max_spectators', 0))
        ticket_price = float(request.form['ticketPrice'])

        #Initialise image URL
        image_url = None

        #Handle image file upload if provided
        if 'eventImage' in request.files:
            image_file = request.files['eventImage']
            if image_file and image_file.filename != '':
                filename = secure_filename(image_file.filename)
                
                #Define path for saving image in static/img
                target_directory = os.path.join(current_app.root_path, 'static/img')
                os.makedirs(target_directory, exist_ok=True)  # Ensure the directory exists
                
                #Full path to save the file
                image_path = os.path.join(target_directory, filename)
                
                #Attempt to save the image file
                try:
                    image_file.save(image_path)
                    image_url = f'img/{filename}'  # Store relative path from static
                except Exception as e:
                    flash(f'Error saving file: {str(e)}', 'error')

        #Create the new event instance with the collected data
        new_event = Event(
            game=game,
            event_type=event_type,
            description=description,
            location=location,
            date_time=date_time,
            created_by_user_id=current_user.id,
            status='Open',
            ticket_price=ticket_price,
            max_participants=max_participants,
            participants=0,
            max_spectators=max_spectators,
            spectators=0,
            image_url=image_url
        )
        new_event.update_status()

        #Save the event to the database
        try:
            db.session.add(new_event)
            db.session.commit()
            flash('Event created successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving event: {str(e)}', 'error')

        return redirect(url_for('main.index'))

    return render_template('event_creation.html')

#Event details
@main_bp.route('/event/<int:event_id>', methods=['GET'])
def event_details(event_id):
    #Retrieve event details and associated comments
    event = Event.query.get_or_404(event_id)
    comments = Comment.query.filter_by(event_id=event_id)\
        .order_by(Comment.posted_at.desc())\
        .all()
    
    return render_template('event_details.html', 
                         event=event, 
                         comments=comments)

#Comment
@main_bp.route('/event/<int:event_id>/comment', methods=['POST'])
@login_required
def add_comment(event_id):
    """Add a comment to an event"""
    event = Event.query.get_or_404(event_id)
    content = request.form.get('content')
    
    if not content:
        flash('Comment cannot be empty', 'error')
        return redirect(url_for('main.event_details', event_id=event_id))
    
    #Create and save the comment to the database
    comment = Comment(
        content=content,
        user_id=current_user.id,
        event_id=event_id
    )
    
    try:
        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while adding your comment.', 'error')
    
    return redirect(url_for('main.event_details', event_id=event_id))

#Booking event
@main_bp.route('/event/<int:event_id>/book', methods=['POST'])
@login_required
def book_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    #Retrieve booking option and extract type and quantity
    booking_option = request.form.get('booking_option', '')
    
    try:
        ticket_type, quantity_str = booking_option.split('-')
        quantity = int(quantity_str)
        is_spectator = (ticket_type == 'spectator')
    except (ValueError, AttributeError):
        flash('Invalid booking option selected.', 'error')
        return redirect(url_for('main.event_details', event_id=event_id))
    
    #Check ticket quantity range
    if quantity < 1 or quantity > 4:
        flash('Please select between 1 and 4 tickets.', 'error')
        return redirect(url_for('main.event_details', event_id=event_id))
    
    #Ensure event has not passed or been cancelled
    if event.date_time < datetime.utcnow():
        flash('This event has already taken place.', 'error')
        return redirect(url_for('main.event_details', event_id=event_id))
    
    if event.status == 'Cancelled':
        flash('This event has been cancelled.', 'error')
        return redirect(url_for('main.event_details', event_id=event_id))
    
    #Validate ticket availability based on type
    if is_spectator:
        if event.spectators + quantity > event.max_spectators:
            flash(f'Not enough spectator tickets available. Only {event.max_spectators - event.spectators} tickets left.', 'error')
            return redirect(url_for('main.event_details', event_id=event_id))
    else:
        if event.participants + quantity > event.max_participants:
            flash(f'Not enough participant tickets available. Only {event.max_participants - event.participants} tickets left.', 'error')
            return redirect(url_for('main.event_details', event_id=event_id))
    
    #Calculate the total price, spectators are free of charge
    total_price = event.ticket_price * quantity if not is_spectator else 0
    
    try:
        #Generate a unique order ID for the booking
        order_id = str(uuid.uuid4().hex[:20])
        
        #Create the booking and update event counts
        booking = Booking(
            quantity=quantity,
            price=total_price,
            event_id=event_id,
            user_id=current_user.id,
            order_id=order_id,
            booking_date=datetime.utcnow(),
            is_spectator=is_spectator
        )
        
        if is_spectator:
            event.spectators += quantity
        else:
            event.participants += quantity
        
        #Update event status if necessary
        event.update_status()
        
        db.session.add(booking)
        db.session.commit()
        
        # Display booking confirmation
        ticket_type = "spectator" if is_spectator else "participant"
        if is_spectator:
            flash(f'Successfully booked {quantity} {ticket_type} ticket(s)!', 'success')
        else:
            flash(f'Successfully booked {quantity} {ticket_type} ticket(s) for ${total_price:.2f}!', 'success')
            
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while processing your booking.', 'error')
    
    return redirect(url_for('main.event_details', event_id=event_id))

#models.py - Update the Event class's update_status method
def update_status(self):
    current_time = datetime.utcnow()
    
    #Maintain cancelled status without further changes
    if self.status == 'Cancelled':
        return 
        
    #Set event as inactive if the date has passed
    if self.date_time < current_time:
        self.status = 'Inactive'
    #Mark event as sold out if both participant and spectator spots are full
    elif (self.participants >= self.max_participants and 
          self.spectators >= self.max_spectators):
        self.status = 'Sold Out'
    else:
        #Keep the event open if spots are available
        self.status = 'Open'

#User detail page
@main_bp.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def user_detail(user_id):
    #Retrieve user data
    user = User.query.get_or_404(user_id)
    
    #Restrict profile access to the current user
    if user.id != current_user.id:
        flash('You can only view your own profile.', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        form = UpdateProfileForm()
        if form.validate_on_submit():
            #Check for existing email in use by other users
            existing_user = User.query.filter(User.email == form.email.data, User.id != user.id).first()
            if existing_user:
                flash('Email address is already in use.', 'error')
                return redirect(url_for('main.user_detail', user_id=user.id))
            
            try:
                #Update user profile details
                user.first_name = form.first_name.data
                user.surname = form.surname.data
                user.email = form.email.data
                user.contact_number = form.contact_number.data
                user.street_address = form.street_address.data
                
                db.session.commit()
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('main.user_detail', user_id=user.id))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while updating your profile.', 'error')
    else:
        #Populate form with current user data for GET requests
        form = UpdateProfileForm(obj=user)
    
    #Retrieve events created by the user and booked events
    created_events = Event.query.filter_by(created_by_user_id=user.id).all()
    booked_events = Event.query.join(Booking).filter(Booking.user_id == user.id).all()
    
    return render_template('user_detail.html', 
                         user=user, 
                         created_events=created_events, 
                         booked_events=booked_events,
                         form=form)

#Edit event
@main_bp.route('/edit-event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    #Retrieve the event to be edited
    event = Event.query.get_or_404(event_id)
    
    #Check if the current user created the event
    if event.created_by_user_id != current_user.id:
        flash('You can only edit your own events.', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        #Update event details with form data
        event.game = request.form['gameTitle']
        event.event_type = request.form['eventType']
        event.description = request.form['eventDescription']
        event.location = request.form['eventLocation']
        
        #Combine date and time fields
        date_time_str = f"{request.form['eventDate']} {request.form['eventTime']}"
        event.date_time = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M')
        
        #update participant and spectator capacities
        event.max_participants = int(request.form.get('max_participants', 0))
        event.spectators = int(request.form.get('spectators', 0))
        
        #Validate and set ticket price
        ticket_price = float(request.form['ticketPrice'])
        if ticket_price < 0:
            flash('Ticket price cannot be negative', 'error')
            return redirect(url_for('main.edit_event', event_id=event_id))
        event.ticket_price = ticket_price
        
        try:
            db.session.commit()
            flash('Event updated successfully!', 'success')
            return redirect(url_for('main.user_detail', user_id=current_user.id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the event.', 'error')
            return redirect(url_for('main.edit_event', event_id=event_id))
    
    #Format event date and time for form population
    event_date = event.date_time.strftime('%Y-%m-%d')
    event_time = event.date_time.strftime('%H:%M')
    
    return render_template('edit_event.html', event=event, 
                         event_date=event_date, event_time=event_time)

#Cancel event
@main_bp.route('/event/<int:event_id>/cancel', methods=['POST'])
@login_required
def cancel_event(event_id):
    event = Event.query.get_or_404(event_id)

    #Only the event owner is allowed to cancel the event
    if event.created_by_user_id != current_user.id:
        flash('You can only cancel your own events.', 'error')
        return redirect(url_for('main.event_details', event_id=event_id))

    #Set event status to cancelled and save
    event.status = 'Cancelled'
    db.session.commit()
    flash('Event cancelled successfully!', 'success')

    return redirect(url_for('main.user_detail', user_id=current_user.id))

#Delete event
@main_bp.route('/delete-event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    #Only the event creator can delete the event
    if event.created_by_user_id != current_user.id:
        flash("You are not authorised to delete this event.", "error")
        return redirect(url_for('main.user_detail', user_id=current_user.id))
    
    #Allow deletion only if the event is Inactive or Cancelled
    if event.status in ['Inactive', 'Cancelled']:
        db.session.delete(event)
        db.session.commit()
        flash("Event deleted successfully.", "success")
    else:
        flash("Only Inactive or Cancelled events can be deleted.", "error")
    
    return redirect(url_for('main.user_detail', user_id=current_user.id))
