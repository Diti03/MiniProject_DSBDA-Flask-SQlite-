from flask import Flask,render_template,request,redirect,session
import pickle
import numpy as np
from flask_sqlalchemy import SQLAlchemy
import os
import logging
from sqlalchemy import inspect
from sqlalchemy import text  # Import text for defining SQL queries
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
# Generate a secure random key
def generate_secret_key():
    return os.urandom(24)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = generate_secret_key()
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)



popular_df = pickle.load(open('popular.pkl','rb'))
pt = pickle.load(open('pt.pkl','rb'))
books = pickle.load(open('books.pkl','rb'))
similarity_scores = pickle.load(open('similarity_scores.pkl','rb'))


@app.route('/')
def index():
    return render_template('index.html',
                           book_name = list(popular_df['Book-Title'].values),
                           author=list(popular_df['Book-Author'].values),
                           image=list(popular_df['Image-URL-M'].values),
                           votes=list(popular_df['num_ratings'].values),
                           rating=list(popular_df['avg_rating'].values)
                           )

@app.route('/recommend')
def recommend_ui():
    if 'user_id' not in session:  # Check if the user is logged in
        return redirect('/signin')
    return render_template('recommend.html')

@app.route('/recommend_books',methods=['post'])
def recommend():
    if 'user_id' not in session:  # Check if the user is logged in
        return redirect('/signin')
    user_input = request.form.get('user_input')
    index = np.where(pt.index == user_input)[0][0]
    similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:5]

    data = []
    for i in similar_items:
        item = []
        temp_df = books[books['Book-Title'] == pt.index[i[0]]]
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))

        data.append(item)

    print(data)

    return render_template('recommend.html',data=data)

@app.route('/contact')
def contact_ui():
    return render_template('contact.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/signin')
    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['user_id'] = user.id
            return redirect('/')
        else:
            return 'Invalid username or password'
    return render_template('signin.html')

@app.route('/show_users')
def show_users():
    logging.info("show_users route called")

    # Get the table name from the User model
    user_table_name = User.__table__.name

    # Use text() to specify the SQL query
    users = db.session.execute(text(f"SELECT * FROM {user_table_name}")).fetchall()

    for user in users:
        logging.info(f"Username: {user.username}, Password: {user.password}")

    return 'Check console for users'

if __name__ == '__main__':
    with app.app_context():
        # Create tables
        db.create_all()
    app.run(debug=True)