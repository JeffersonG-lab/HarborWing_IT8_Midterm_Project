-- HarborWing Air - IT8 Midterm Drill
-- MySQL 8.0+ | All timestamps are stored in UTC.
-- Reset warning: DROP DATABASE permanently removes the existing harborwing_air database.
DROP DATABASE IF EXISTS harborwing_air;
CREATE DATABASE harborwing_air CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE harborwing_air;

CREATE TABLE booking_agent (
  agent_id INT AUTO_INCREMENT PRIMARY KEY,
  agent_name VARCHAR(120) NOT NULL,
  email VARCHAR(254) UNIQUE,
  phone VARCHAR(30),
  agency_name VARCHAR(120),
  additional_details TEXT
) ENGINE=InnoDB;

CREATE TABLE passenger (
  passenger_id INT AUTO_INCREMENT PRIMARY KEY,
  first_name VARCHAR(80) NOT NULL,
  second_name VARCHAR(80) NULL,
  last_name VARCHAR(80) NOT NULL,
  phone_number VARCHAR(30),
  email_address VARCHAR(254) UNIQUE,
  address_line1 VARCHAR(160),
  address_line2 VARCHAR(160),
  city VARCHAR(100),
  state_province_county VARCHAR(100),
  country VARCHAR(100),
  other_details TEXT,
  INDEX idx_passenger_name (last_name, first_name)
) ENGINE=InnoDB;

CREATE TABLE airport (
  airport_code CHAR(3) PRIMARY KEY,
  airport_name VARCHAR(140) NOT NULL,
  city VARCHAR(100) NOT NULL,
  country VARCHAR(100) NOT NULL,
  other_details TEXT,
  UNIQUE KEY uq_airport_name_city (airport_name, city)
) ENGINE=InnoDB;

CREATE TABLE calendar_date (
  calendar_date DATE PRIMARY KEY,
  day_of_month TINYINT UNSIGNED NOT NULL,
  is_business_day BOOLEAN NOT NULL,
  CONSTRAINT chk_calendar_day CHECK (day_of_month BETWEEN 1 AND 31)
) ENGINE=InnoDB;

CREATE TABLE flight_schedule (
  flight_number VARCHAR(12) PRIMARY KEY,
  airline_code CHAR(2) NOT NULL,
  usual_aircraft_type_code VARCHAR(20) NOT NULL,
  origin_airport_code CHAR(3) NOT NULL,
  destination_airport_code CHAR(3) NOT NULL,
  scheduled_departure_utc DATETIME NOT NULL,
  scheduled_arrival_utc DATETIME NOT NULL,
  CONSTRAINT fk_schedule_origin FOREIGN KEY (origin_airport_code)
    REFERENCES airport(airport_code) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_schedule_destination FOREIGN KEY (destination_airport_code)
    REFERENCES airport(airport_code) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_schedule_different_airports CHECK (origin_airport_code <> destination_airport_code),
  CONSTRAINT chk_schedule_times CHECK (scheduled_arrival_utc > scheduled_departure_utc),
  INDEX idx_schedule_departure (scheduled_departure_utc),
  INDEX idx_schedule_route (origin_airport_code, destination_airport_code)
) ENGINE=InnoDB;

CREATE TABLE reservation (
  reservation_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  main_passenger_id INT NOT NULL,
  agent_id INT NULL,
  reservation_status_code VARCHAR(20) NOT NULL,
  reservation_code VARCHAR(16) NOT NULL UNIQUE,
  ticket_type_code VARCHAR(20) NOT NULL,
  travel_class_code VARCHAR(20) NOT NULL,
  created_at_utc DATETIME NOT NULL,
  party_size SMALLINT UNSIGNED NOT NULL,
  CONSTRAINT fk_reservation_passenger FOREIGN KEY (main_passenger_id)
    REFERENCES passenger(passenger_id) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_reservation_agent FOREIGN KEY (agent_id)
    REFERENCES booking_agent(agent_id) ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT chk_party_size CHECK (party_size > 0),
  INDEX idx_reservation_passenger (main_passenger_id),
  INDEX idx_reservation_agent (agent_id),
  INDEX idx_reservation_status (reservation_status_code)
) ENGINE=InnoDB;

CREATE TABLE payment (
  payment_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  payment_status_code VARCHAR(20) NOT NULL,
  payment_date_utc DATETIME NOT NULL,
  payment_amount DECIMAL(12,2) NOT NULL,
  CONSTRAINT chk_payment_positive CHECK (payment_amount > 0),
  INDEX idx_payment_date (payment_date_utc),
  INDEX idx_payment_status (payment_status_code)
) ENGINE=InnoDB;

CREATE TABLE flight_leg (
  leg_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  flight_number VARCHAR(12) NOT NULL,
  origin_airport_code CHAR(3) NOT NULL,
  destination_airport_code CHAR(3) NOT NULL,
  actual_departure_utc DATETIME NULL,
  actual_arrival_utc DATETIME NULL,
  CONSTRAINT fk_leg_schedule FOREIGN KEY (flight_number)
    REFERENCES flight_schedule(flight_number) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_leg_origin FOREIGN KEY (origin_airport_code)
    REFERENCES airport(airport_code) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_leg_destination FOREIGN KEY (destination_airport_code)
    REFERENCES airport(airport_code) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_leg_different_airports CHECK (origin_airport_code <> destination_airport_code),
  CONSTRAINT chk_leg_actual_times CHECK (
    actual_departure_utc IS NULL OR actual_arrival_utc IS NULL OR actual_arrival_utc > actual_departure_utc
  ),
  INDEX idx_leg_flight (flight_number),
  INDEX idx_leg_route (origin_airport_code, destination_airport_code)
) ENGINE=InnoDB;

CREATE TABLE flight_cost (
  flight_number VARCHAR(12) NOT NULL,
  aircraft_type_code VARCHAR(20) NOT NULL,
  valid_from_date DATE NOT NULL,
  valid_to_date DATE NOT NULL,
  cost_amount DECIMAL(12,2) NOT NULL,
  PRIMARY KEY (flight_number, aircraft_type_code, valid_from_date),
  CONSTRAINT fk_cost_schedule FOREIGN KEY (flight_number)
    REFERENCES flight_schedule(flight_number) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_cost_aircraft_valid_from FOREIGN KEY (valid_from_date)
    REFERENCES calendar_date(calendar_date) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_cost_aircraft_valid_to FOREIGN KEY (valid_to_date)
    REFERENCES calendar_date(calendar_date) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_cost_dates CHECK (valid_to_date >= valid_from_date),
  CONSTRAINT chk_cost_nonnegative CHECK (cost_amount >= 0),
  INDEX idx_cost_lookup (flight_number, aircraft_type_code, valid_from_date, valid_to_date)
) ENGINE=InnoDB;

CREATE TABLE reservation_payment (
  reservation_id BIGINT NOT NULL,
  payment_id BIGINT NOT NULL,
  PRIMARY KEY (reservation_id, payment_id),
  CONSTRAINT fk_rp_reservation FOREIGN KEY (reservation_id)
    REFERENCES reservation(reservation_id) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_rp_payment FOREIGN KEY (payment_id)
    REFERENCES payment(payment_id) ON UPDATE CASCADE ON DELETE CASCADE,
  INDEX idx_rp_payment (payment_id)
) ENGINE=InnoDB;

CREATE TABLE reservation_leg (
  reservation_id BIGINT NOT NULL,
  leg_id BIGINT NOT NULL,
  PRIMARY KEY (reservation_id, leg_id),
  CONSTRAINT fk_rl_reservation FOREIGN KEY (reservation_id)
    REFERENCES reservation(reservation_id) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_rl_leg FOREIGN KEY (leg_id)
    REFERENCES flight_leg(leg_id) ON UPDATE CASCADE ON DELETE RESTRICT,
  INDEX idx_rl_leg (leg_id)
) ENGINE=InnoDB;
