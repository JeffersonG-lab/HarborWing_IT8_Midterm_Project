# Design and developer explanation

## Table purposes

1. **booking_agent** — optional agent details for agent-assisted bookings.
2. **passenger** — one record per main passenger, including contact and address information.
3. **reservation** — reservation code, main passenger, optional agent, booking status, ticket/travel class, creation time, and party size.
4. **payment** — payment status, UTC payment time, and positive payment amount.
5. **airport** — canonical airport code, name, city, country, and notes.
6. **flight_schedule** — unique flight number, airline/aircraft codes, route, and scheduled UTC times.
7. **flight_leg** — an operated or planned leg of one schedule, with actual times nullable until known.
8. **calendar_date** — calendar date, day of month, and business-day indicator; cost validity dates reference it.
9. **flight_cost** — cost history by flight, aircraft type, and validity start date.
10. **reservation_payment** — bridge between reservations and payments.
11. **reservation_leg** — bridge between reservations and flight legs.

## Relationships

- One passenger can have many reservations; each reservation has exactly one main passenger.
- One agent can handle many reservations; a reservation may have no agent or one agent.
- Reservations and payments are many-to-many, implemented by `reservation_payment`.
- Reservations and flight legs are many-to-many, implemented by `reservation_leg`.
- One scheduled flight can have many legs and many cost records.
- Airports are referenced as origins and destinations by schedules and legs.
- Both `valid_from_date` and `valid_to_date` in `flight_cost` reference `calendar_date`.

## Why linking tables?

A reservation can have multiple payments, and one payment may cover multiple reservations. Similarly, one reservation may include connecting legs, while one leg can appear on multiple reservations. A bridge table stores each relationship once and prevents duplicate pairs through a composite primary key. No allocation amount is stored in `reservation_payment`, matching the brief.

## Separate scheduled and actual times

Scheduled times are the planned timetable; actual times are what happened operationally. Keeping them separate preserves the plan even when a flight is delayed or arrives early. Actual times are nullable because they may not exist before the flight operates.

## Composite key for costs

`(flight_number, aircraft_type_code, valid_from_date)` identifies a version of the cost record. This allows the same flight and aircraft type to have a new cost beginning on a different date without overwriting history. The validity end date must be on or after the start date, and the amount cannot be negative. Overlapping periods need a further business rule or trigger.

## Advantages and trade-offs

**Advantages:** normalized passenger and airport data, enforced references, duplicate-link prevention, indexes for common joins/searches, historical costs, nullable actual times, and repeatable synthetic data.

**Trade-offs:** joins are required for complete reservation views; the simplified unique flight-number assumption is not production-grade; code fields are not locally validated against reference tables; shared payment links do not allocate money; and overlapping cost periods are not blocked by a simple CHECK constraint.

## How another developer runs it

1. Execute `sql/schema.sql` in MySQL Workbench.
2. Install `requirements.txt`.
3. Set `DB_USER` and `DB_PASSWORD` if needed.
4. Run `python scripts/seed_data.py`.
5. Execute `sql/example_queries.sql` and check the row-count output.
6. Reverse-engineer the schema in Workbench, save the `.mwb`, and export a PDF/PNG diagram.

## Explainer video checklist

- Keep your face visible during the explanation.
- Introduce the HarborWing Air problem and the normalization goal.
- Show the EER diagram and explain the main relationships.
- Show the two linking tables and why they are needed.
- Execute the schema or show the created tables in Workbench.
- Run the seed script and show the row counts (50+ in every table).
- Run the four required example queries.
- Explain the trade-offs and limitations: shared payment allocation, party-size-only passenger tracking, joins, overlapping cost periods, and the flight-number assumption.
