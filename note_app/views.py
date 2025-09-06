# views.py (updated)
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from datetime import datetime
from note_app import db
from note_app.models import Note
from note_app.forms import NoteForm,CategoryForm
from flask_login import current_user, login_required
from sqlalchemy import text  # Add this import
from werkzeug.utils import secure_filename
from flask import request
import os
from note_app.models import User,Attachment,SharedNote,Note,Category

views2 = Blueprint('views', __name__,template_folder='public')

@views2.route('/', methods=['GET', 'POST'])
@views2.route('/home', methods=['GET', 'POST'])
def home():
    form = SimpleNoteForm()  # Use the simple form instead
    
    if form.validate_on_submit():
        if current_user.is_authenticated:
            note = Note(
                title=form.title.data, 
                content=form.content.data, 
                user_id=current_user.id
            )
            db.session.add(note)
            db.session.commit()
            flash('Your note has been saved!', 'success')
            return redirect(url_for('views.home'))
        else:
            flash('You need to be logged in to save notes.', 'warning')
            return redirect(url_for('auth.login'))
    # form = NoteForm()
    # if form.validate_on_submit():
    #     if current_user.is_authenticated:
    #         note = Note(title=form.title.data, content=form.content.data, user_id=current_user.id)
    #         db.session.add(note)
    #         db.session.commit()
    #         flash('Your note has been saved!', 'success')
    #         return redirect(url_for('views.home'))
    #     else:
    #         flash('You need to be logged in to save notes.', 'warning')
    #         return redirect(url_for('auth.login'))
    
    notes = []
    if current_user.is_authenticated:
        notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.date_created.desc()).all()
    
    date = datetime.now()
    current_date = date.strftime("%Y")
    return render_template("home.html", title="Home", form=form, notes=notes, current_date=current_date)

@views2.route('/note/<int:note_id>/delete')
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)
    db.session.delete(note)
    db.session.commit()
    flash('Your note has been deleted!', 'success')
    return redirect(url_for('views.home'))


@views2.route('/note/<int:note_id>')
@login_required
def view_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)
    
    date = datetime.now()
    current_date = date.strftime("%Y")
    return render_template("view_note.html", title=note.title, note=note, current_date=current_date)

@views2.route('/note/<int:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)
    
    form = NoteForm()
    if form.validate_on_submit():
        note.title = form.title.data
        note.content = form.content.data
        db.session.commit()
        flash('Your note has been updated!', 'success')
        return redirect(url_for('views.view_note', note_id=note.id))
    
    # Pre-populate the form with existing data
    elif request.method == 'GET':
        form.title.data = note.title
        form.content.data = note.content
    
    date = datetime.now()
    current_date = date.strftime("%Y")
    return render_template("edit_note.html", title="Edit Note", form=form, note=note, current_date=current_date)



@views2.route('/test-db')
def test_db():
    try:
        from note_app import db
        result = db.session.execute(text('SELECT 1'))  # Wrap with text()
        return 'Database connection: OK'
    except Exception as e:
        return f'Database error: {str(e)}', 500

# views.py - add this route
@views2.route('/health')
def health_check():
    try:
        # Test database connection
        from note_app import db
        db.session.execute(text('SELECT 1'))
        return 'Database connection: OK', 200
    except Exception as e:
        return f'Database error: {str(e)}', 500

@views2.route('/debug/vercel')
def debug_vercel():
    import os
    info = {
        'vercel': os.environ.get('VERCEL'),
        'database_url_set': bool(os.environ.get('DATABASE_URL')),
        'python_version': os.environ.get('PYTHON_VERSION'),
        'all_env_vars': {k: v for k, v in os.environ.items() if 'KEY' not in k and 'PASS' not in k}
    }
    return info

@views2.route('/debug/db')
def debug_db():
    try:
        from note_app import db
        from sqlalchemy import text
        result = db.session.execute(text('SELECT 1'))
        return 'Database connection: OK'
    except Exception as e:
        return f'Database error: {str(e)}', 500
    

@views2.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    form = CategoryForm()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    if form.validate_on_submit():
        category = Category(name=form.name.data,color=form.color.data,user_id=current_user.id)
        db.session.add(category)
        db.session.commit()
        flash('Category created successfully!', 'success')
        return redirect(url_for('views.categories'))
    
    return render_template('categories.html', form=form, categories=categories)

@views2.route('/category/<int:category_id>/delete')
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    if category.user_id != current_user.id:
        abort(403)
    
    # Move notes to uncategorized
    Note.query.filter_by(category_id=category_id).update({Note.category_id: None})
    
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('views.categories'))


@views2.route('/note/<int:note_id>/upload', methods=['POST'])
@login_required
def upload_attachment(note_id):
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)
    
    if 'file' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('views.view_note', note_id=note_id))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('views.view_note', note_id=note_id))
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.root_path, 'static', 'uploads', filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)
        
        attachment = Attachment(
            filename=filename,
            file_path=f'/static/uploads/{filename}',
            note_id=note_id
        )
        db.session.add(attachment)
        db.session.commit()
        
        flash('File uploaded successfully!', 'success')
    
    return redirect(url_for('views.view_note', note_id=note_id))


@views2.route('/note/<int:note_id>/share', methods=['GET', 'POST'])
@login_required
def share_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)
    
    if request.method == 'POST':
        email = request.form.get('email')
        can_edit = 'can_edit' in request.form
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('views.share_note', note_id=note_id))
        
        # Check if already shared
        existing_share = SharedNote.query.filter_by(
            note_id=note_id, 
            shared_with_id=user.id
        ).first()
        
        if existing_share:
            flash('Note already shared with this user', 'warning')
        else:
            shared_note = SharedNote(
                note_id=note_id,
                shared_with_id=user.id,
                shared_by_id=current_user.id,
                can_edit=can_edit
            )
            db.session.add(shared_note)
            db.session.commit()
            flash('Note shared successfully!', 'success')
        
        return redirect(url_for('views.view_note', note_id=note_id))
    
    shared_with = SharedNote.query.filter_by(note_id=note_id).all()
    return render_template('share_note.html', note=note, shared_with=shared_with)


@views2.route('/search')
@login_required
def search_notes():
    query = request.args.get('q', '')
    
    if query:
        # Search in title and content
        notes = Note.query.filter(
            Note.user_id == current_user.id,
            (Note.title.ilike(f'%{query}%') | Note.content.ilike(f'%{query}%'))
        ).order_by(Note.date_created.desc()).all()
    else:
        notes = []
    

    return render_template('search.html', notes=notes, query=query)
