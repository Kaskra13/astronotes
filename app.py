from flask import Flask, render_template, redirect, url_for, request, flash, session
from models import db, FlashcardSet, Flashcard
from forms import FlashcardSetForm, FlashcardForm, ImportFlashcardsForm
from werkzeug.utils import secure_filename
import random
import os
from dotenv import load_dotenv

# create flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-only-for-development'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
db.init_app(app)

# create all database tables
with app.app_context():
    db.create_all()

# home page route
@app.route('/')
def index():
    # get all flashcard sets
    sets = FlashcardSet.query.all()
    return render_template('index.html', sets=sets)

# add new flashcard set
@app.route('/add_set', methods=['GET', 'POST'])
def add_set():
    form = FlashcardSetForm()
    if form.validate_on_submit():
        # create new set and add to database
        new_set = FlashcardSet(name=form.name.data, description=form.description.data)
        db.session.add(new_set)
        db.session.commit()
        flash('⭐ Constellation created successfully! Keep it in orbit!', 'success')
        return redirect(url_for('index'))
    return render_template('add_set.html', form=form)

# view a specific flashcard set and its cards
@app.route('/set/<int:set_id>', methods=['GET', 'POST'])
def view_set(set_id):
    set_obj = FlashcardSet.query.get_or_404(set_id)
    form = FlashcardForm()
    import_form = ImportFlashcardsForm()
    
    if form.validate_on_submit():
        # add new card to set
        new_card = Flashcard(front=form.front.data, back=form.back.data, set=set_obj)
        db.session.add(new_card)
        db.session.commit()
        return redirect(url_for('view_set', set_id=set_id))

    # filter cards by known/unknown/all
    current_filter = request.args.get('filter', 'all')
    if current_filter == 'known':
        cards = Flashcard.query.filter_by(set_id=set_id, category='known').order_by(Flashcard.id).all()
    elif current_filter == 'unknown':
        cards = Flashcard.query.filter_by(set_id=set_id, category='unknown').order_by(Flashcard.id).all()
    else:
        cards = Flashcard.query.filter_by(set_id=set_id).order_by(Flashcard.id).all()

    return render_template('view_set.html', set_obj=set_obj, cards=cards, form=form, import_form=import_form, current_filter=current_filter)

# edit a flashcard's front and back
@app.route('/edit_card/<int:card_id>', methods=['POST'])
def edit_set(card_id):
    card = Flashcard.query.get_or_404(card_id)
    
    front = request.form.get('front')
    back = request.form.get('back')
    
    if front and back:
        card.front = front
        card.back = back
        db.session.commit()
        flash('✅ Star card updated successfully!', 'success')
    else:
        flash('⚠️ Both front side and back side are required!', 'error')
    
    return redirect(url_for('view_set', set_id=card.set_id))

# delete a flashcard set and its cards
@app.route('/delete_set/<int:set_id>', methods=['POST'])
def delete_set(set_id):
    set_obj = FlashcardSet.query.get_or_404(set_id)
    
    # delete all cards in the set
    Flashcard.query.filter_by(set_id=set_id).delete()
    
    db.session.delete(set_obj)
    db.session.commit()
    
    flash('🗑️ Constellation deleted successfully!', 'success')
    return redirect(url_for('index'))

# delete a single flashcard
@app.route('/delete_card/<int:card_id>', methods=['POST'])
def delete_card(card_id):
    card = Flashcard.query.get_or_404(card_id)
    set_id = card.set_id
    db.session.delete(card)
    db.session.commit()
    flash('🗑️ Star card deleted successfully!', 'success')
    return redirect(url_for('view_set', set_id=set_id))

# add a new card to a set
@app.route('/add_card/<int:set_id>', methods=['POST'])
def add_card(set_id):
    set_obj = FlashcardSet.query.get_or_404(set_id)
    front = request.form.get('front')
    back = request.form.get('back')
    
    if front and back:
        new_card = Flashcard(front=front, back=back, set=set_obj)
        db.session.add(new_card)
        db.session.commit()
        flash('✅ New star added successfully! Reach for the stars!', 'success')
    else:
        flash('⚠️ Both front side and back side are required!', 'error')
    
    return redirect(url_for('view_set', set_id=set_id))

# import cards from a file
@app.route('/import_cards/<int:set_id>', methods=['POST'])
def import_cards(set_id):
    set_obj = FlashcardSet.query.get_or_404(set_id)
    
    file = request.files.get('file')
    separator_choice = request.form.get('separator')
    custom_separator = request.form.get('custom_separator')
    
    if not file or file.filename == '':
        flash('❌ Please select a file!', 'error')
        return redirect(url_for('view_set', set_id=set_id))
    
    # determine separator to use
    if separator_choice == 'custom' and custom_separator:
        separator = custom_separator
    elif separator_choice == 'custom' and not custom_separator:
        flash('⚠️ Please provide a custom separator!', 'error')
        return redirect(url_for('view_set', set_id=set_id))
    else:
        separator = separator_choice
    
    try:
        # read file content
        content = file.read().decode('utf-8')
        lines = content.strip().split('\n')
        
        imported_count = 0
        error_lines = []
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            # check if separator is present
            if separator not in line:
                error_lines.append(f"Line {line_num}: Missing separator '{separator}' - {line[:50]}...")
                continue
            
            parts = line.split(separator, 1)
            
            if len(parts) != 2:
                error_lines.append(f"Line {line_num}: Invalid format - {line[:50]}...")
                continue
            
            front = parts[0].strip()
            back = parts[1].strip()
            
            if not front or not back:
                error_lines.append(f"Line {line_num}: Empty sides - {line[:50]}...")
                continue
            
            # add new card to set
            new_card = Flashcard(front=front, back=back, set=set_obj)
            db.session.add(new_card)
            imported_count += 1
        
        db.session.commit()
        
        if imported_count > 0:
            flash(f'✅ Successfully imported {imported_count} stars!', 'success')
        
        if error_lines:
            error_message = f"⚠️ {len(error_lines)} lines had errors:\n" + "\n".join(error_lines[:5])
            if len(error_lines) > 5:
                error_message += f"\n... and {len(error_lines) - 5} more errors"
            flash(error_message, 'warning')
            
    except UnicodeDecodeError:
        flash('❌ Error reading file. Please make sure it\'s a valid UTF-8 text file.', 'error')
    except Exception as e:
        flash(f'❌ Error processing file: {str(e)}', 'error')

    return redirect(url_for('view_set', set_id=set_id))

# learning mode for a set
@app.route('/learn/<int:set_id>', methods=['GET', 'POST'])
def learn(set_id):
    # initialize session for learning
    if 'set_id' not in session or session.get('set_id') != set_id:
        session.clear()
        session['set_id'] = set_id

    if request.method == 'POST':
        # handle restart actions
        if 'restart' in request.form:
            restart_type = request.form['restart']
            mode = request.form.get('mode') or session.get('mode', 'sequential')

            if restart_type == 'all':
                cards = (Flashcard.query
                         .filter_by(set_id=set_id)
                         .order_by(Flashcard.id)
                         .all())
                session['card_history'] = {}

            elif restart_type == 'to_learn':
                cards = (Flashcard.query
                         .filter_by(set_id=set_id, category='unknown')
                         .order_by(Flashcard.id)
                         .all())
                if not cards:
                    flash('🎉 All stars in this constellation are explored! No unexplored territory to discover', 'info')
                    stats = {'known': 0, 'unknown': 0}
                    db_cards = Flashcard.query.filter_by(set_id=set_id).all()
                    for c in db_cards:
                        if c.category == 'known':
                            stats['known'] += 1
                        else:
                            stats['unknown'] += 1
                    return render_template('learn_summary.html', set_id=set_id, stats=stats)
            else:
                cards = []

            session['mode'] = mode
            card_ids = [c.id for c in cards]
            if mode == 'random':
                random.shuffle(card_ids)
            session['card_queue'] = card_ids
            session['current_index'] = 0
            return redirect(url_for('learn', set_id=set_id))

        # handle marking card as known/unknown
        if 'action' in request.form:
            action = request.form['action']
            if action in ['known', 'unknown']:
                card_queue = session.get('card_queue', [])
                current_index = session.get('current_index', 0)
                if current_index >= len(card_queue):
                    return redirect(url_for('learn', set_id=set_id))

                card_id = card_queue[current_index]
                card = Flashcard.query.get_or_404(card_id)

                history = session.get('card_history', {})
                card_history = history.get(str(card_id), [])
                card_history.append(action)
                history[str(card_id)] = card_history
                session['card_history'] = history

                last_response = card_history[-1]
                if last_response == 'known':
                    card.category = 'known'
                else:
                    card.category = 'unknown'

                db.session.commit()
                session['current_index'] = current_index + 1
                return redirect(url_for('learn', set_id=set_id))

        # handle mode and subset selection
        if 'mode' in request.form:
            mode = request.form['mode']
            subset = request.form.get('subset', 'all')
            session['mode'] = mode
            session['subset'] = subset
            session['card_history'] = {}

            if subset == 'unknown':
                base_query = Flashcard.query.filter_by(set_id=set_id, category='unknown')
            else:
                base_query = Flashcard.query.filter_by(set_id=set_id)

            if mode == 'random':
                cards = base_query.all()
                card_ids = [c.id for c in cards]
                random.shuffle(card_ids)
            else:
                cards = base_query.order_by(Flashcard.id).all()
                card_ids = [c.id for c in cards]

            if subset == 'unknown' and not card_ids:
                flash('🎉 No unexplored stars to discover in this constellation.', 'info')
                return redirect(url_for('view_set', set_id=set_id))

            session['card_queue'] = card_ids
            session['current_index'] = 0
            return redirect(url_for('learn', set_id=set_id))

    card_queue = session.get('card_queue')
    current_index = session.get('current_index', 0)

    # check if there are cards to learn
    if not card_queue:
        cards_exist = Flashcard.query.filter_by(set_id=set_id).count()
        if cards_exist == 0:
            flash('📂 No stars to explore in this constellation.', 'warning')
            return redirect(url_for('view_set', set_id=set_id))
        else:
            flash('🌌 Please select exploration mode and start your cosmic journey.', 'info')
            return redirect(url_for('view_set', set_id=set_id))

    # check if learning session is finished
    if current_index >= len(card_queue):
        history = session.get('card_history', {})
        stats = {}
        for card_id_str, responses in history.items():
            if responses:
                if responses[-1] == 'known':
                    stats['known'] = stats.get('known', 0) + 1
                else:
                    stats['unknown'] = stats.get('unknown', 0) + 1
        return render_template('learn_summary.html', set_id=set_id, stats=stats)

    # get current card to learn
    card_id = card_queue[current_index]
    card = Flashcard.query.get_or_404(card_id)

    return render_template('learn_flashcard.html',
                           flashcard=card,
                           current=current_index + 1,
                           total=len(card_queue))

# select learning mode and subset
@app.route('/learn/<int:set_id>/mode', methods=['GET', 'POST'])
def learn_mode(set_id):
    if request.method == 'POST':
        mode = request.form['mode']
        subset = request.form.get('subset', 'all')
        session['mode'] = mode
        session['subset'] = subset
        session['card_history'] = {}

        if subset == 'unknown':
            base_query = Flashcard.query.filter_by(set_id=set_id, category='unknown')
        else:
            base_query = Flashcard.query.filter_by(set_id=set_id)

        if mode == 'random':
            cards = base_query.all()
            card_ids = [c.id for c in cards]
            random.shuffle(card_ids)
        else:
            cards = base_query.order_by(Flashcard.id).all()
            card_ids = [c.id for c in cards]

        if subset == 'unknown' and not card_ids:
            flash('🎉 No unexplored stars to discover in this constellation.', 'info')
            return redirect(url_for('view_set', set_id=set_id))

        session['card_queue'] = card_ids
        session['current_index'] = 0
        session['set_id'] = set_id
        return redirect(url_for('learn', set_id=set_id))
    return render_template('learn_mode.html', set_id=set_id)

# edit flashcard set details
@app.route('/edit_set_details/<int:set_id>', methods=['POST'])
def edit_set_details(set_id):
    set_obj = FlashcardSet.query.get_or_404(set_id)
    name = request.form.get('name')
    description = request.form.get('description')

    if name:
        set_obj.name = name
    set_obj.description = description

    db.session.commit()
    flash('⭐ Constellation details updated successfully! Keep it in orbit!', 'success')
    return redirect(url_for('view_set', set_id=set_id))

# print flashcards for a set
@app.route('/print_cards/<int:set_id>')
def print_cards(set_id):
    set_obj = FlashcardSet.query.get_or_404(set_id)
    
    cards_per_page = int(request.args.get('cards_per_page', 4))
    font_size = int(request.args.get('font_size', 14))
    filter_type = request.args.get('filter', 'all')
    
    # filter cards for printing
    if filter_type == 'known':
        cards = Flashcard.query.filter_by(set_id=set_id, category='known').order_by(Flashcard.id).all()
    elif filter_type == 'unknown':
        cards = Flashcard.query.filter_by(set_id=set_id, category='unknown').order_by(Flashcard.id).all()
    else:
        cards = Flashcard.query.filter_by(set_id=set_id).order_by(Flashcard.id).all()
    
    if not cards:
        flash('📄 No stars to print in this constellation.', 'warning')
        return redirect(url_for('view_set', set_id=set_id))
    
    return render_template('print_cards.html', 
                         set_obj=set_obj, 
                         cards=cards, 
                         cards_per_page=cards_per_page,
                         font_size=font_size,
                         filter_type=filter_type)

# run the app if this file is executed directly
if __name__ == '__main__':
    app.run(debug=True)
