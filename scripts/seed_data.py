"""Generate repeatable fictional HarborWing Air data.
Run after sql/schema.sql using: python scripts/seed_data.py
Requires a local MySQL server and Faker (pip install -r requirements.txt).
Set DB_HOST, DB_PORT, DB_USER, DB_PASSWORD if your MySQL settings differ.
"""
import os, random
from datetime import date, datetime, time, timedelta
from faker import Faker
import mysql.connector

SEED = 20261016
random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Mydokg109727@",
    database="harborwing_air"
)
cur = conn.cursor()

def insert_many(sql, rows):
    cur.executemany(sql, rows)
    conn.commit()

# Airports are synthetic demo locations/codes.
airports = [
("HWA","Harborwing Central","Harborwing","Fictional Isles"),
("BAY","Bayview Airport","Bayview","Fictional Isles"),
("COR","Coral Coast Airport","Coral Coast","Fictional Isles"),
("ISL","Island Gateway","Isleton","Fictional Isles"),
("PAL","Palm Shore Airport","Palm Shore","Fictional Isles"),
("REE","Reefside Airport","Reefside","Fictional Isles"),
("SUN","Sunport Regional","Sunport","Fictional Isles"),
("CLI","Cliffhaven Airport","Cliffhaven","Fictional Isles"),
("LAG","Lagoon Airport","Lagoon City","Fictional Isles"),
("MST","Mist Harbor Airport","Mist Harbor","Fictional Isles"),
]
insert_many("INSERT INTO airport VALUES (%s,%s,%s,%s,%s)",
            [(a[0],a[1],a[2],a[3],"Fictional airport for coursework") for a in airports])

# Dates needed by cost validity periods; every date in a 3-year window is available.
start = date(2025,1,1)
end = date(2027,12,31)
dates=[]
d=start
while d <= end:
    dates.append((d, d.day, d.weekday() < 5))
    d += timedelta(days=1)
insert_many("INSERT INTO calendar_date VALUES (%s,%s,%s)", dates)

agents=[]
for i in range(50):
    agents.append((f"{fake.name()} Travel Desk", f"agent{i+1}@example.test",
                   fake.phone_number()[:30], f"{fake.city()} Demo Travel", "Fictional training record"))
insert_many("""INSERT INTO booking_agent
(agent_name,email,phone,agency_name,additional_details) VALUES (%s,%s,%s,%s,%s)""", agents)

passengers=[]
for i in range(100):
    passengers.append((fake.first_name(), random.choice([None, fake.first_name()]),
       fake.last_name(), fake.phone_number()[:30], f"passenger{i+1}@example.test",
       fake.street_address()[:160], None, fake.city(), fake.state()[:100], "Fictional Isles",
       "Fictional passenger generated for IT8 coursework"))
insert_many("""INSERT INTO passenger
(first_name,second_name,last_name,phone_number,email_address,address_line1,address_line2,
 city,state_province_county,country,other_details)
 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", passengers)

# Add 40 more clearly fictional demo airports so airport also has at least 50 rows.
for i in range(40):
    code = f"Z{i:02d}"
    airports.append((code, f"Demo Regional Airport {i+11}", f"Demo City {i+11}", "Fictional Isles"))
insert_many("INSERT INTO airport VALUES (%s,%s,%s,%s,%s)",
            [(a[0],a[1],a[2],a[3],"Fictional airport for coursework") for a in airports[10:]])
airport_codes=[a[0] for a in airports]
schedules=[]
for i in range(50):
    origin,dest=random.sample(airport_codes,2)
    dep=datetime(2026,11,1,6,0)+timedelta(days=i, hours=random.randrange(0,12))
    arr=dep+timedelta(minutes=random.randrange(45,181))
    schedules.append((f"HW{i+1:04d}", "HW", random.choice(["ATR72","DHC8","E190","A220"]),
                      origin,dest,dep,arr))
insert_many("""INSERT INTO flight_schedule VALUES (%s,%s,%s,%s,%s,%s,%s)""", schedules)

reservations=[]
for i in range(100):
    agent_id = None if i % 2 == 0 else random.randint(1,50)
    created=datetime(2026,1,1,9,0)+timedelta(days=i, minutes=random.randrange(0,600))
    reservations.append((random.randint(1,100), agent_id, random.choice(["CONFIRMED","PENDING","CANCELLED"]),
       f"HWBOOK{i+1:06d}", random.choice(["STANDARD","FLEX","SAVER"]),
       random.choice(["ECONOMY","PREMIUM","BUSINESS"]), created, random.randint(1,5)))
insert_many("""INSERT INTO reservation
(main_passenger_id,agent_id,reservation_status_code,reservation_code,ticket_type_code,
 travel_class_code,created_at_utc,party_size) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""", reservations)

payments=[]
for i in range(100):
    payments.append((random.choice(["PAID","PENDING","REFUNDED"]),
        datetime(2026,1,2,10,0)+timedelta(days=i, minutes=random.randrange(0,500)),
        round(random.uniform(35,950),2)))
insert_many("""INSERT INTO payment (payment_status_code,payment_date_utc,payment_amount)
VALUES (%s,%s,%s)""", payments)

legs=[]
for i, s in enumerate(schedules):
    actual_dep = s[5] + timedelta(minutes=random.randint(-5,35)) if i % 4 else None
    actual_arr = (actual_dep + timedelta(minutes=random.randrange(45,181))) if actual_dep else None
    legs.append((s[0],s[3],s[4],actual_dep,actual_arr))
insert_many("""INSERT INTO flight_leg
(flight_number,origin_airport_code,destination_airport_code,actual_departure_utc,actual_arrival_utc)
VALUES (%s,%s,%s,%s,%s)""", legs)

costs=[]
for i,s in enumerate(schedules):
    valid_from=date(2026,1,1)+timedelta(days=i)
    valid_to=valid_from+timedelta(days=180)
    costs.append((s[0],s[2],valid_from,valid_to,round(random.uniform(800,12000),2)))
insert_many("INSERT INTO flight_cost VALUES (%s,%s,%s,%s,%s)", costs)

# Ensure >50 links and demonstrate multi-payment, multi-leg, and shared-payment cases.
rp=set()
for rid in range(1,101):
    rp.add((rid, rid))
    rp.add((rid, (rid % 100)+1))  # each reservation gets two payment links; payments are shared
insert_many("INSERT INTO reservation_payment VALUES (%s,%s)", sorted(rp))

rl=set()
for rid in range(1,101):
    rl.add((rid, ((rid-1) % 50)+1))
    rl.add((rid, (rid % 50)+1))  # each reservation links to two legs
insert_many("INSERT INTO reservation_leg VALUES (%s,%s)", sorted(rl))

# Row-count verification for all 11 core tables.
tables = ["booking_agent","passenger","reservation","payment","airport","flight_schedule",
          "flight_leg","calendar_date","flight_cost","reservation_payment","reservation_leg"]
print("\nRow-count verification:")
for table in tables:
    cur.execute(f"SELECT COUNT(*) FROM `{table}`")
    print(f"{table}: {cur.fetchone()[0]}")

cur.close()
conn.close()
print("\nSeed completed. Synthetic data only; fixed random seed:", SEED)
