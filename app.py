from flask import Flask, render_template, url_for, request, redirect, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os
import matplotlib
matplotlib.use('Agg')  # Set the backend to Agg to avoid GUI issues
import matplotlib.pyplot as plt
from datetime import datetime

# Initialize Flask app and configurations
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Todo Model for Task Master
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.id

# Final Project Model
class FinalUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    file_path = db.Column(db.String(200))

db.create_all()

# Task Master Routes
@app.route('/')
def home():
    return render_template('landing.html')

@app.route('/finalproject/')
def final_project():
    return render_template('Finalproject/finalbase.html')


@app.route('/Assignments/', methods=['POST', 'GET'])
def task_index():
    if request.method == 'POST':
        task_content = request.form['content']
        new_task = Todo(content=task_content)
        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/Assignments/')
        except:
            return 'There was an issue adding your task'
    else:
        tasks = Todo.query.order_by(Todo.date_created).all()
        return render_template('Assignments/index.html', tasks=tasks)

@app.route('/delete/<int:id>')
def task_delete(id):
    task_to_delete = Todo.query.get_or_404(id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/Assignments/')
    except:
        return 'There was a problem deleting that task'

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def task_update(id):
    task = Todo.query.get_or_404(id)
    if request.method == 'POST':
        task.content = request.form['content']
        try:
            db.session.commit()
            return redirect('/Assignments/')
        except:
            return 'There was an issue updating your task'
    else:
        return render_template('Assignments/update.html', task=task)

# Final Project Routes
@app.route('/final_form', methods=['GET', 'POST'])
def final_form():
    if request.method == 'POST':
        # Handle form submission
        name = request.form.get('name')
        age = request.form.get('age')
        file = request.files.get('file')

        # Validate form inputs
        if not name or not age or not file:
            return 'All fields are required.', 400

        # Save the file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(file_path)

        # Store user data in the database
        user = FinalUser(name=name, age=int(age), file_path=file_path)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('final_display'))  # Redirect to a display page

    # Handle GET request (render the form)
    return render_template('Finalproject/finalform.html')

@app.route('/view/<int:id>', methods=['GET'])
def view_file(id):
    user = FinalUser.query.get(id)
    if user:
        # Extract the filename
        filename = os.path.basename(user.file_path)

        # Return the file for viewing in the browser
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],  # Pass the directory containing the file
            filename  # Pass only the filename
        )
    return "File not found.", 404


@app.route('/update_user/<int:user_id>', methods=['GET', 'POST'])
def update_user(user_id):
    user = FinalUser.query.get_or_404(user_id)  # Retrieve user from the database

    if request.method == 'POST':
        # Update user details from the form
        user.name = request.form['name']
        user.age = int(request.form['age'])

        # Check if a new file is uploaded
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:  # Only process if a new file is provided
                # Delete the old file
                if user.file_path and os.path.exists(user.file_path):
                    os.remove(user.file_path)

                # Save the new file
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)
                user.file_path = file_path  # Update file path in the database

        try:
            db.session.commit()
            return redirect(url_for('final_display'))  # Redirect to the display page
        except Exception as e:
            return f"An error occurred while updating the user: {str(e)}", 500

    # Render the update form with the user's current data
    return render_template('Finalproject/update_user.html', user=user)

@app.route('/final_display')
def final_display():
    users = FinalUser.query.all()
    print(users)
    return render_template('Finalproject/finaldisplay.html', users=users)

@app.route('/final_delete/<int:id>')
def final_delete(id):
    user = FinalUser.query.get_or_404(id)
    if user:
        if os.path.exists(user.file_path):
            os.remove(user.file_path)
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('final_display')) 

@app.route('/final_visualize')
def final_visualize():
    users = FinalUser.query.all()
    ages = [user.age for user in users]
    names = [user.name for user in users]

    plt.bar(names, ages, color='blue')
    plt.xlabel('Names')
    plt.ylabel('Ages')
    plt.title('User Data')

    # Save the plot as an image file
    chart_path = os.path.join('static', 'age_chart.png')
    plt.savefig(chart_path)
    plt.close()  # Close the plot to free memory

    # Return the visualization page with the chart URL
    return render_template('Finalproject/finalvisualise.html', chart_url=chart_path)

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
