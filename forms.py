from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, RadioField
from wtforms.validators import DataRequired, Length

# form for creating a new flashcard set
class FlashcardSetForm(FlaskForm):
    # input for the name of the flashcard set
    name = StringField('⭐ Constellation name', validators=[
        DataRequired(), 
        Length(max=100, message='📝 Constellation name cannot exceed 100 characters!')
    ])
    # input for the description of the flashcard set
    description = TextAreaField('📄 Description', validators=[
        Length(max=500, message='📝 Description cannot exceed 500 characters!')
    ])
    # submit button for creating the flashcard set
    submit = SubmitField('➕ Create constellation')

# form for creating a new flashcard
class FlashcardForm(FlaskForm):
    # input for the front side of the flashcard
    front = StringField('🌟 Front side', validators=[
        DataRequired(), 
        Length(max=1000, message='⭐ Front side cannot exceed 1000 characters!')
    ])
    # input for the back side of the flashcard
    back = StringField('🪐 Back side', validators=[
        DataRequired(), 
        Length(max=1000, message='⭐ Back side cannot exceed 1000 characters!')
    ])
    # submit button for adding the flashcard
    submit = SubmitField('➕ Add star card')

# form for importing flashcards from a file
class ImportFlashcardsForm(FlaskForm):
    # file input for uploading a .txt file
    file = FileField('📁 Choose file (.txt)', validators=[
        DataRequired(), 
        FileAllowed(['txt'], 'Only .txt star data files are allowed!')
    ])
    # radio field for selecting the separator used in the file
    separator = RadioField('🔗 Separator', choices=[
        ('-', 'Dash (-)'),
        (',', 'Comma (,)'),
        (':', 'Colon (:)'),
        (';', 'Semicolon (;)'),
        ('|', 'Pipe (|)'),
        ('custom', 'Custom separator')
    ], default='-', validators=[DataRequired()])
    # input for specifying a custom separator if selected
    custom_separator = StringField('✏️ Custom separator (if selected above)', validators=[
        Length(max=5, message='📝 Custom separator cannot exceed 5 characters!')
    ])
    # submit button for importing flashcards
    submit = SubmitField('📥 Import star data')
