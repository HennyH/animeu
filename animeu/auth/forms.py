# /animeu/auth/forms.py
#
# Forms for the auth module.
#
# See /LICENCE.md for Copyright information
"""Forms for the auth module."""
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import BooleanField, StringField, PasswordField, validators
from wtforms.fields.html5 import EmailField

_EMAIL_FIELD = EmailField("Email", validators=[validators.Email(),
                                               validators.DataRequired()])
_PASSWORD_FIELD = PasswordField(
    'Password',
    validators=[validators.InputRequired(), validators.Length(min=8)]
)

class LoginForm(FlaskForm):
    """Form for user login."""

    email = _EMAIL_FIELD
    password = _PASSWORD_FIELD
    remember_me = BooleanField("Remember Me?")

class RegisterForm(FlaskForm):
    """Form for signing up to the site."""

    email = _EMAIL_FIELD
    username = StringField("Username",
                           validators=[validators.DataRequired(),
                                       validators.Length(min=4, max=20)])
    password = _PASSWORD_FIELD
    recaptcha = RecaptchaField()
