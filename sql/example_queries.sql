USE harborwing_air;

-- 1. Reservation with passenger, agent, payments and legs.
-- Separate aggregate subqueries avoid inflating payment totals when there are multiple legs.
SELECT r.reservation_id, r.reservation_code, r.reservation_status_code, r.party_size,
       CONCAT(p.first_name,' ',p.last_name) AS main_passenger,
       ba.agent_name,
       pay.payment_ids, pay.payment_count, pay.payment_total,
       legs.leg_ids, legs.leg_count
FROM reservation r
JOIN passenger p ON p.passenger_id = r.main_passenger_id
LEFT JOIN booking_agent ba ON ba.agent_id = r.agent_id
LEFT JOIN (
  SELECT rp.reservation_id,
         GROUP_CONCAT(DISTINCT pm.payment_id ORDER BY pm.payment_id) AS payment_ids,
         COUNT(DISTINCT pm.payment_id) AS payment_count,
         SUM(pm.payment_amount) AS payment_total
  FROM reservation_payment rp JOIN payment pm ON pm.payment_id = rp.payment_id
  GROUP BY rp.reservation_id
) pay ON pay.reservation_id = r.reservation_id
LEFT JOIN (
  SELECT rl.reservation_id,
         GROUP_CONCAT(DISTINCT fl.leg_id ORDER BY fl.leg_id) AS leg_ids,
         COUNT(DISTINCT fl.leg_id) AS leg_count
  FROM reservation_leg rl JOIN flight_leg fl ON fl.leg_id = rl.leg_id
  GROUP BY rl.reservation_id
) legs ON legs.reservation_id = r.reservation_id
WHERE r.reservation_id = 1;

-- 2. Find reservations using a particular leg.
SELECT r.reservation_id, r.reservation_code, r.reservation_status_code,
       p.first_name, p.last_name
FROM reservation_leg rl
JOIN reservation r ON r.reservation_id = rl.reservation_id
JOIN passenger p ON p.passenger_id = r.main_passenger_id
WHERE rl.leg_id = 1;

-- 3. Find payments linked to a reservation.
SELECT r.reservation_code, pm.payment_id, pm.payment_status_code,
       pm.payment_date_utc, pm.payment_amount
FROM reservation_payment rp
JOIN reservation r ON r.reservation_id = rp.reservation_id
JOIN payment pm ON pm.payment_id = rp.payment_id
WHERE r.reservation_id = 1
ORDER BY pm.payment_date_utc;

-- 4. Find the applicable cost for a flight, aircraft type, and date.
SET @flight_number = 'HW0001';
SET @aircraft_type = 'ATR72';
SET @travel_date = '2026-06-15';
SELECT flight_number, aircraft_type_code, valid_from_date, valid_to_date, cost_amount
FROM flight_cost
WHERE flight_number = @flight_number
  AND aircraft_type_code = @aircraft_type
  AND @travel_date BETWEEN valid_from_date AND valid_to_date
ORDER BY valid_from_date DESC
LIMIT 1;

-- Row count of every core table.
SELECT 'booking_agent' AS table_name, COUNT(*) AS row_count FROM booking_agent
UNION ALL SELECT 'passenger', COUNT(*) FROM passenger
UNION ALL SELECT 'reservation', COUNT(*) FROM reservation
UNION ALL SELECT 'payment', COUNT(*) FROM payment
UNION ALL SELECT 'airport', COUNT(*) FROM airport
UNION ALL SELECT 'flight_schedule', COUNT(*) FROM flight_schedule
UNION ALL SELECT 'flight_leg', COUNT(*) FROM flight_leg
UNION ALL SELECT 'calendar_date', COUNT(*) FROM calendar_date
UNION ALL SELECT 'flight_cost', COUNT(*) FROM flight_cost
UNION ALL SELECT 'reservation_payment', COUNT(*) FROM reservation_payment
UNION ALL SELECT 'reservation_leg', COUNT(*) FROM reservation_leg;
