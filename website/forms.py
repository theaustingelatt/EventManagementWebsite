from flask_wtf import FlaskForm
from wtforms.fields import TextAreaField, SubmitField, StringField, PasswordField
from wtforms.validators import InputRequired, Length, Email, EqualTo

# creates the login information
class LoginForm(FlaskForm):
    email = StringField("Email Address", validators=[Email("Please enter a valid email")])
    password=PasswordField("Password", validators=[InputRequired('Enter user password')])
    submit = SubmitField("Login")

 # this is the registration form
class RegisterForm(FlaskForm):
    first_name = StringField("First Name", validators=[InputRequired()])
    surname = StringField("Surname", validators=[InputRequired()])
    email = StringField("Email Address", validators=[Email("Please enter a valid email")])
    contact_number = StringField('Contact Number', validators=[InputRequired()])
    street_address = StringField('Street Address', validators=[InputRequired()])
    # linking two fields - password should be equal to data entered in confirm
    password=PasswordField("Password", validators=[InputRequired(),
                  EqualTo('confirm', message="Passwords should match")])
    confirm = PasswordField("Confirm Password")

    # submit button
    submit = SubmitField("Register")

#Contact us form
class ContactForm(FlaskForm):
    name = StringField("Your Name", validators=[InputRequired()])
    email = StringField("Email Address", validators=[
        InputRequired(),
        Email("Please enter a valid email")
    ])
    message = TextAreaField("Your Message", validators=[
        InputRequired(),
        Length(max=1000, message="Message must not exceed 1000 characters")
    ])
    submit = SubmitField("Submit")

class UpdateProfileForm(FlaskForm):
    first_name = StringField("First Name", validators=[InputRequired()])
    surname = StringField("Surname", validators=[InputRequired()])
    email = StringField("Email Address", validators=[Email("Please enter a valid email")])
    contact_number = StringField('Contact Number', validators=[InputRequired()])
    street_address = StringField('Street Address', validators=[InputRequired()])
    submit = SubmitField("Update Profile")