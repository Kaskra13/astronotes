from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# defines the FlashcardSet model representing a constellation of star cards
class FlashcardSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    # relationship to the Flashcard model, allows access to all star cards in the constellation
    flashcards = db.relationship('Flashcard', backref='set', lazy=True)

# defines the Flashcard model representing individual star cards
class Flashcard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    front = db.Column(db.String(1000), nullable=False)
    back = db.Column(db.String(1000), nullable=False)
    category = db.Column(db.String(20), default='unknown')
    # foreign key linking the star card to a constellation
    set_id = db.Column(db.Integer, db.ForeignKey('flashcard_set.id'), nullable=False)
