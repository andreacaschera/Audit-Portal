from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, FileField, SubmitField
from wtforms.validators import DataRequired, Optional, Length

class NewCourseForm(FlaskForm):
    title = StringField("Titolo del corso", validators=[DataRequired(), Length(max=255)])
    teacher = StringField("Docente", validators=[DataRequired(), Length(max=255)])
    validity_months = IntegerField("Validità (mesi)", validators=[Optional()])
    material = FileField("Carica Slides o Video-corso", validators=[Optional()])
    submit = SubmitField("Salva corso")

class CandidateForm(FlaskForm):
    first_name = StringField("Nome", validators=[DataRequired(), Length(max=128)])
    last_name = StringField("Cognome", validators=[DataRequired(), Length(max=128)])
    place_of_birth = StringField("Luogo di nascita", validators=[Optional(), Length(max=128)])
    date_of_birth = DateField("Data di nascita", validators=[Optional()], format="%Y-%m-%d")
    role = StringField("Mansione", validators=[Optional(), Length(max=128)])
    submit = SubmitField("Salva candidato")
