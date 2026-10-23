from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from database import get_db_connection, execute_query
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/passengers')
def list_passengers():
    search = request.args.get('search', '')
    if search:
        query = """
            SELECT * FROM passenger 
            WHERE first_name LIKE %s OR last_name LIKE %s OR email_address LIKE %s
        """
        term = f"%{search}%"
        passengers = execute_query(query, (term, term, term), fetchall=True)
    else:
        passengers = execute_query("SELECT * FROM passenger ORDER BY passenger_id DESC", fetchall=True)
    return render_template('passengers/list.html', passengers=passengers, search=search)

@app.route('/passengers/create', methods=['GET', 'POST'])
def create_passenger():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email_address = request.form.get('email_address')
        phone_number = request.form.get('phone_number')
        city = request.form.get('city')

        try:
            query = """
                INSERT INTO passenger (first_name, last_name, email_address, phone_number, city)
                VALUES (%s, %s, %s, %s, %s)
            """
            execute_query(query, (first_name, last_name, email_address, phone_number, city), commit=True)
            flash("Passenger added successfully!", "success")
            return redirect(url_for('list_passengers'))
        except Exception as e:
            flash(f"Database error: {e}", "danger")

    return render_template('passengers/form.html')
@app.route('/passengers/delete/<int:passenger_id>', methods=['POST'])
def delete_passenger(passenger_id):
    try:
        execute_query("DELETE FROM passenger WHERE passenger_id = %s", (passenger_id,), commit=True)
        flash("Passenger deleted successfully.", "success")
    except mysql.connector.Error as err:
        if err.errno == 1451:
            flash("Cannot delete passenger: This passenger has active reservations associated with them.", "danger")
        else:
            flash(f"Delete failed: {err}", "danger")
    return redirect(url_for('list_passengers'))

@app.route('/reservations')
def list_reservations():
    query = """
        SELECT r.*, CONCAT(p.first_name, ' ', p.last_name) AS passenger_name, b.agent_name AS agent_name
        FROM reservation r
        JOIN passenger p ON r.main_passenger_id = p.passenger_id
        LEFT JOIN booking_agent b ON r.agent_id = b.agent_id
        ORDER BY r.reservation_id DESC
    """
    reservations = execute_query(query, fetchall=True)
    return render_template('reservations/list.html', reservations=reservations)
def create_reservation():
    if request.method == 'POST':
        passenger_id = request.form.get('passenger_id')
        agent_id = request.form.get('agent_id') or None
        status = request.form.get('reservation_status_code', 'CONF')
        ticket_type = request.form.get('ticket_type_code', 'ECO')
        travel_class = request.form.get('travel_class_code', 'STD')
        party_size = int(request.form.get('number_in_party', 1))

        if party_size <= 0:
            flash("Party size must be greater than zero.", "danger")
            return redirect(url_for('create_reservation'))

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO reservation (main_passenger, booking_agent, reservation_status_code, 
                                       ticket_type_code, travel_class_code, creation_timestamp, number_in_party)
                VALUES (%s, %s, %s, %s, %s, NOW(), %s)
            """
            cursor.execute(query, (passenger_id, agent_id, status, ticket_type, travel_class, party_size))
            res_id = cursor.lastrowid
            conn.commit()
            flash(f"Reservation #{res_id} created successfully!", "success")
            return redirect(url_for('view_reservation', res_id=res_id))
        except mysql.connector.Error as err:
            conn.rollback()
            flash(f"Error creating reservation: {err}", "danger")
        finally:
            cursor.close()
            conn.close()

    passengers = execute_query("SELECT passenger_id, CONCAT(first_name, ' ', last_name) AS name FROM passenger", fetchall=True)
    agents = execute_query("SELECT agent_id, name FROM booking_agent", fetchall=True)
    return render_template('reservations/form.html', passengers=passengers, agents=agents)

@app.route('/reservations/<int:res_id>')
def view_reservation(res_id):
    res_query = """
        SELECT r.*, CONCAT(p.first_name, ' ', p.last_name) AS passenger_name, p.email_address, b.name AS agent_name
        FROM reservation r
        JOIN passenger p ON r.main_passenger = p.passenger_id
        LEFT JOIN booking_agent b ON r.booking_agent = b.agent_id
        WHERE r.reservation_id = %s
    """
    reservation = execute_query(res_query, (res_id,), fetchone=True)
    if not reservation:
        flash("Reservation not found.", "warning")
        return redirect(url_for('list_reservations'))

    legs_query = """
        SELECT l.*, rll.reservation_id 
        FROM flight_leg l
        JOIN reservation_leg_link rll ON l.leg_id = rll.leg_id
        WHERE rll.reservation_id = %s
    """
    linked_legs = execute_query(legs_query, (res_id,), fetchall=True)

    payments_query = """
        SELECT p.*, rpl.reservation_id 
        FROM payment p
        JOIN reservation_payment_link rpl ON p.payment_id = rpl.payment_id
        WHERE rpl.reservation_id = %s
    """
    linked_payments = execute_query(payments_query, (res_id,), fetchall=True)

    all_legs = execute_query("SELECT leg_id, scheduled_flight, origin_airport, destination_airport FROM flight_leg", fetchall=True)
    all_payments = execute_query("SELECT payment_id, payment_amount, payment_status_code FROM payment", fetchall=True)

    return render_template('reservations/view.html', reservation=reservation, legs=linked_legs, 
                           payments=linked_payments, all_legs=all_legs, all_payments=all_payments)

@app.route('/reservations/<int:res_id>/add_leg', methods=['POST'])
def add_leg_link(res_id):
    leg_id = request.form.get('leg_id')
    try:
        query = "INSERT INTO reservation_leg_link (reservation_id, leg_id) VALUES (%s, %s)"
        execute_query(query, (res_id, leg_id), commit=True)
        flash("Flight leg linked successfully!", "success")
    except mysql.connector.Error as err:
        if err.errno == 1062:
            flash("This flight leg is already linked to this reservation.", "warning")
        else:
            flash(f"Error linking leg: {err}", "danger")
    return redirect(url_for('view_reservation', res_id=res_id))

@app.route('/reservations/<int:res_id>/remove_leg/<int:leg_id>', methods=['POST'])
def remove_leg_link(res_id, leg_id):
    try:
        query = "DELETE FROM reservation_leg_link WHERE reservation_id = %s AND leg_id = %s"
        execute_query(query, (res_id, leg_id), commit=True)
        flash("Flight leg unlinked safely. The leg record remains intact.", "info")
    except Exception as e:
        flash(f"Error unlinking leg: {str(e)}", "danger")
    return redirect(url_for('view_reservation', res_id=res_id))

@app.route('/reservations/<int:res_id>/add_payment', methods=['POST'])
def add_payment_link(res_id):
    payment_id = request.form.get('payment_id')
    try:
        query = "INSERT INTO reservation_payment_link (reservation_id, payment_id) VALUES (%s, %s)"
        execute_query(query, (res_id, payment_id), commit=True)
        flash("Payment linked successfully!", "success")
    except mysql.connector.Error as err:
        if err.errno == 1062:
            flash("This payment is already linked to this reservation.", "warning")
        else:
            flash(f"Error linking payment: {err}", "danger")
    return redirect(url_for('view_reservation', res_id=res_id))

@app.route('/reservations/<int:res_id>/remove_payment/<int:payment_id>', methods=['POST'])
def remove_payment_link(res_id, payment_id):
    try:
        query = "DELETE FROM reservation_payment_link WHERE reservation_id = %s AND payment_id = %s"
        execute_query(query, (res_id, payment_id), commit=True)
        flash("Payment link removed safely. The payment record remains intact.", "info")
    except Exception as e:
        flash(f"Error unlinking payment: {str(e)}", "danger")
    return redirect(url_for('view_reservation', res_id=res_id))

@app.route('/airports')
def list_airports():
    query = "SELECT * FROM airport ORDER BY airport_code"
    airports = execute_query(query, fetchall=True)
    return render_template('airports/list.html', airports=airports)

@app.route('/agents')
def list_agents():
    query = "SELECT * FROM booking_agent ORDER BY agent_id"
    agents = execute_query(query, fetchall=True)
    return render_template('agents/list.html', agents=agents)

@app.route('/payments')
def list_payments():
    query = "SELECT * FROM payment ORDER BY payment_id DESC"
    payments = execute_query(query, fetchall=True)
    return render_template('payments/list.html', payments=payments)

@app.route('/reservations/create', methods=['GET', 'POST'])
def create_reservation():
    if request.method == 'POST':
        passenger_id = request.form.get('passenger_id')
        agent_id = request.form.get('agent_id') or None
        ticket_type = request.form.get('ticket_type')
        travel_class = request.form.get('travel_class')
        party_size = int(request.form.get('party_size', 1))

        try:
            query = """
                INSERT INTO reservation (main_passenger_id, agent_id, ticket_type_code, travel_class_code, number_in_party, reservation_status_code)
                VALUES (%s, %s, %s, %s, %s, 'CONFIRMED')
            """
            execute_query(query, (passenger_id, agent_id, ticket_type, travel_class, party_size), commit=True)
            flash("Reservation created successfully!", "success")
            return redirect(url_for('list_reservations'))
        except Exception as e:
            flash(f"Error creating reservation: {e}", "danger")

    passengers = execute_query("SELECT passenger_id, first_name, last_name FROM passenger", fetchall=True)
    agents = execute_query("SELECT agent_id, first_name, last_name, agency_name FROM booking_agent", fetchall=True)
    return render_template('reservations/form.html', passengers=passengers, agents=agents)


if __name__ == '__main__':
    app.run(debug=True, port=5000)


