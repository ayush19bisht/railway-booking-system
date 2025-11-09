from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'ayush123'
DB = 'railway.db'


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        conn = get_db()
        conn.execute(
            "INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)",
            (name, email, phone, hashed_password)
        )
        conn.commit()
        conn.close()

        flash("Registered successfully! Please login now.")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['is_admin'] = bool(user['is_admin']) if 'is_admin' in user.keys() else False

            flash(f"Welcome back, {user['name']}!")

            if session['is_admin']:
                return redirect(url_for('admin_panel'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password. Please try again.")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', name=session['user_name'])


@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    trains = None

    if request.method == 'POST':
        source = request.form['source']
        destination = request.form['destination']
        trains = conn.execute(
            "SELECT * FROM trains WHERE source=? AND destination=?", (source, destination)
        ).fetchall()
    
    conn.close()
    return render_template('search.html', trains=trains)


@app.route('/book_ticket', methods=['GET', 'POST'])
def book_ticket():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    trains = conn.execute("SELECT * FROM trains").fetchall()

    if request.method == 'POST':
        train_id = request.form['train_id']
        num_seats = int(request.form['num_seats'])
        train = conn.execute("SELECT * FROM trains WHERE id=?", (train_id,)).fetchone()

        if not train:
            flash("❌ Invalid train selected.", "error")
        elif num_seats > train['seats']:
            flash("❌ Not enough seats available.", "error")
        else:
            total_fare = num_seats * train['fare']
            conn.execute(
                "INSERT INTO bookings (user_id, train_id, num_seats, total_fare) VALUES (?, ?, ?, ?)",
                (session['user_id'], train_id, num_seats, total_fare)
            )
            conn.execute("UPDATE trains SET seats = seats - ? WHERE id=?", (num_seats, train_id))
            conn.commit()
            flash("✅ Ticket booked successfully!", "success")

        conn.close()
        return redirect(url_for('book_ticket'))

    conn.close()
    return render_template('book_ticket.html', trains=trains)




@app.route('/my_bookings')
def my_bookings():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    bookings = conn.execute("""
        SELECT b.id, t.name AS train_name, t.source, t.destination, b.num_seats, b.total_fare
        FROM bookings b
        JOIN trains t ON b.train_id = t.id
        WHERE b.user_id=?
    """, (session['user_id'],)).fetchall()
    conn.close()

    return render_template('bookings.html', bookings=bookings)

@app.route('/cancel_booking/<int:booking_id>')
def cancel_booking(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    booking = conn.execute("SELECT * FROM bookings WHERE id=? AND user_id=?", (booking_id, session['user_id'])).fetchone()

    if not booking:
        conn.close()
        flash("❌ Booking not found or unauthorized.", "error")
        return redirect(url_for('my_bookings'))

    # Restore seats in train table
    conn.execute("UPDATE trains SET seats = seats + ? WHERE id=?", (booking['num_seats'], booking['train_id']))
    conn.execute("DELETE FROM bookings WHERE id=?", (booking_id,))
    conn.commit()
    conn.close()

    flash("🚮 Booking cancelled successfully.", "success")
    return redirect(url_for('my_bookings'))



@app.route('/logout')
def logout():
    session.clear()
    flash("You’ve been logged out successfully.")
    return redirect(url_for('login'))

@app.route('/admin')
def admin_panel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if not session.get('is_admin'):
        return "❌ Access Denied: Admins only", 403

    conn = get_db()
    trains = conn.execute('SELECT * FROM trains').fetchall()
    conn.close()

    return render_template('admin.html', trains=trains)


@app.route('/admin/add_train', methods=['GET', 'POST'])
def add_train():
    if 'user_id' not in session or not session.get('is_admin'):
        return "Access Denied", 403

    if request.method == 'POST':
        name = request.form['name']
        source = request.form['source']
        destination = request.form['destination']
        seats = int(request.form['seats'])
        fare = float(request.form['fare'])

        conn = get_db()
        conn.execute(
            'INSERT INTO trains (name, source, destination, seats, fare) VALUES (?, ?, ?, ?, ?)',
            (name, source, destination, seats, fare)
        )
        conn.commit()
        conn.close()
        flash("✅ Train added successfully!")
        return redirect(url_for('admin_panel'))

    return render_template('add_train.html')


@app.route('/admin/edit_train/<int:train_id>', methods=['GET', 'POST'])
def edit_train(train_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return "Access Denied", 403

    conn = get_db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        source = request.form['source']
        destination = request.form['destination']
        seats = int(request.form['seats'])
        fare = float(request.form['fare'])

        c.execute('''
            UPDATE trains
            SET name=?, source=?, destination=?, seats=?, fare=?
            WHERE id=?
        ''', (name, source, destination, seats, fare, train_id))
        conn.commit()
        conn.close()
        flash("✅ Train updated successfully!")
        return redirect(url_for('admin_panel'))

    train = c.execute('SELECT * FROM trains WHERE id=?', (train_id,)).fetchone()
    conn.close()
    return render_template('edit_train.html', train=train)


@app.route('/admin/delete_train/<int:train_id>')
def delete_train(train_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return "Access Denied", 403

    conn = get_db()
    conn.execute('DELETE FROM trains WHERE id=?', (train_id,))
    conn.commit()
    conn.close()
    flash("🗑️ Train deleted successfully!")
    return redirect(url_for('admin_panel'))


if __name__ == "__main__":
    app.run(debug=True)
