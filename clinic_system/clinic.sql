


CREATE DATABASE clinic;
USE clinic;

CREATE TABLE Users (
    userID    INT AUTO_INCREMENT PRIMARY KEY,
    userName  VARCHAR(50)  NOT NULL UNIQUE,
    password  VARCHAR(255) NOT NULL,          
    roles     ENUM('Doctor', 'Patient', 'Pharmacist', 'Admin') NOT NULL,
    email     VARCHAR(100) NOT NULL UNIQUE,
    phone     VARCHAR(15),
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_username CHECK (CHAR_LENGTH(userName) >= 5),
    CONSTRAINT chk_phone CHECK ( CHAR_LENGTH(phone) >= 9)
);

-- -----------------------------------------------------
-- Doctors
-- -----------------------------------------------------
CREATE TABLE Doctors (
    doctorID        INT AUTO_INCREMENT PRIMARY KEY,
    doctorName      VARCHAR(50) NOT NULL,
    specialization  ENUM('Dermatology', 'Cosmetic', 'General', 'Pediatrics', 'Cardiology') NOT NULL,
    userID          INT NOT NULL,
    email           VARCHAR(100) UNIQUE,
    phone           VARCHAR(15),
    consultationFee DECIMAL(10,2) DEFAULT 50.00,
    FOREIGN KEY (userID) REFERENCES Users(userID) ON DELETE CASCADE,
    CONSTRAINT chk_doctor_name CHECK (CHAR_LENGTH(doctorName) >= 3)
);
alter table doctors
add check(char_length(phone) >=9);

-- -----------------------------------------------------
-- Patients
-- -----------------------------------------------------
CREATE TABLE Patients (
    patientID   INT AUTO_INCREMENT PRIMARY KEY,
    patientName VARCHAR(50) NOT NULL,
    userID      INT NOT NULL,
    email       VARCHAR(100),
    phone       VARCHAR(15),
    dateOfBirth DATE,
    gender      ENUM('Male', 'Female', 'Other'),
    address     VARCHAR(255),
    FOREIGN KEY (userID) REFERENCES Users(userID) ON DELETE CASCADE,
    CONSTRAINT chk_patient_name CHECK (CHAR_LENGTH(patientName) >= 3)
    
);
alter table patients
add check(char_length(phone) >=9);

-- -----------------------------------------------------
-- Pharmacists
-- -----------------------------------------------------
CREATE TABLE Pharmacists (
    pharmacistID   INT AUTO_INCREMENT PRIMARY KEY,
    pharmacistName VARCHAR(50) NOT NULL,
    userID         INT NOT NULL,
    email          VARCHAR(100) UNIQUE,
    phone          VARCHAR(15),
    FOREIGN KEY (userID) REFERENCES Users(userID) ON DELETE CASCADE,
    CONSTRAINT chk_pharmacist_name CHECK (CHAR_LENGTH(pharmacistName) >= 3)
);
alter table Pharmacists
add check (char_length(phone) >=9);

-- -----------------------------------------------------
-- Appointments
-- -----------------------------------------------------
CREATE TABLE Appointments (
    appointmentID   INT AUTO_INCREMENT PRIMARY KEY,
    patientID       INT NOT NULL,
    doctorID        INT NOT NULL,
    appointmentDate DATETIME NOT NULL,
    reason          VARCHAR(255),
    status          ENUM('Scheduled', 'Completed', 'Cancelled') DEFAULT 'Scheduled',
    createdAt       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patientID) REFERENCES Patients(patientID) ON DELETE CASCADE,
    FOREIGN KEY (doctorID)  REFERENCES Doctors(doctorID)   ON DELETE CASCADE
);

-- -----------------------------------------------------
-- Medicines
-- -----------------------------------------------------
CREATE TABLE Medicines (
    medicineID   INT AUTO_INCREMENT PRIMARY KEY,
    medicineName VARCHAR(100) NOT NULL,
    category     VARCHAR(50),
    price        DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    stock        INT DEFAULT 0,
    description  TEXT
);

-- -----------------------------------------------------
-- Prescriptions
-- -----------------------------------------------------
CREATE TABLE Prescriptions (
    prescriptionID INT AUTO_INCREMENT PRIMARY KEY,
    appointmentID  INT NOT NULL,
    pharmacistID   INT,
    medicineID     INT NOT NULL,
    quantity       INT NOT NULL DEFAULT 1,
    instructions   TEXT,
    createdAt      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointmentID) REFERENCES Appointments(appointmentID) ON DELETE CASCADE,
    FOREIGN KEY (pharmacistID)  REFERENCES Pharmacists(pharmacistID)   ON DELETE SET NULL,
    FOREIGN KEY (medicineID)    REFERENCES Medicines(medicineID)
);

-- -----------------------------------------------------
-- Invoices
-- -----------------------------------------------------
CREATE TABLE Invoices (
    invoiceID     INT AUTO_INCREMENT PRIMARY KEY,
    appointmentID INT NOT NULL,
    amount        DECIMAL(10,2) NOT NULL,
    paymentStatus ENUM('Pending', 'Paid', 'Cancelled') DEFAULT 'Pending',
    issuedAt      DATETIME DEFAULT CURRENT_TIMESTAMP,
    paidAt        DATETIME,
    FOREIGN KEY (appointmentID) REFERENCES Appointments(appointmentID) ON DELETE CASCADE
);

-- -----------------------------------------------------
-- Contact messages
-- -----------------------------------------------------
CREATE TABLE Messages (
    messageID INT AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(100) NOT NULL,
    email     VARCHAR(100) NOT NULL,
    phone     VARCHAR(20),
    subject   VARCHAR(100) NOT NULL,
    message   TEXT NOT NULL,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- SAMPLE DATA (password-free only)

insert into users(userName,Password,roles,email,phone)
value('Honglyly','Hong9090$','Admin','hong86097@gmail.com','095535582');
delete from users 
where userName='Honglyly';
select * from users;
select * from appointments;
select * from doctors;
select * from pharmacists;

ALTER TABLE Doctors ADD COLUMN photo_url VARCHAR(255);

UPDATE Doctors
SET photo_url = '/static/image/doc1.jpg'
WHERE doctorID = 1;

UPDATE Doctors
SET photo_url = '/static/image/doc2.jpg'
WHERE doctorID = 2;

UPDATE Doctors
SET photo_url = '/static/image/doc3.jpg'
WHERE doctorID = 3;

UPDATE Doctors
SET photo_url = '/static/image/doc4.jpg'
WHERE doctorID = 4;

UPDATE Doctors
SET photo_url = '/static/image/doc5.jpg'
WHERE doctorID = 5;

UPDATE Doctors
SET photo_url = '/static/image/doc6.jpg'
WHERE doctorID = 6;

UPDATE Doctors
SET photo_url = '/static/image/doc7.jpg'
WHERE doctorID = 7;

UPDATE Doctors
SET photo_url = '/static/image/doc8.jpg'
WHERE doctorID = 8;

UPDATE Doctors
SET photo_url = '/static/image/doc9.jpg'
WHERE doctorID = 9;

UPDATE Doctors
SET photo_url = '/static/image/doc10.jpg'
WHERE doctorID = 10;

ALTER TABLE Pharmacists ADD COLUMN photo_url VARCHAR(255);

UPDATE Pharmacists
SET photo_url = '/static/image/pha1.jpg'
WHERE pharmacistID = 1;

UPDATE Pharmacists
SET photo_url = '/static/image/pha2.jpg'
WHERE pharmacistID = 2;

UPDATE Pharmacists
SET photo_url = '/static/image/pha3.jpg'
WHERE pharmacistID = 3;

UPDATE Pharmacists
SET photo_url = '/static/image/ph4.jpg'
WHERE pharmacistID = 4;
select * from pharmacists;




-- =====================================================
-- Medicines need no hashing, so they are safe to seed here.
INSERT INTO Medicines (medicineName, category, price, stock, description) VALUES
('Paracetamol 500mg', 'Pain Relief',   5.00, 200, 'For pain and fever'),
('Amoxicillin 250mg', 'Antibiotic',   12.50, 100, 'Bacterial infections'),
('Ibuprofen 200mg',   'Pain Relief',   6.50, 150, 'Anti-inflammatory'),
('Vitamin C 1000mg',  'Supplement',    8.00, 300, 'Immune support'),
('Cetirizine 10mg',   'Antihistamine', 4.50, 120, 'Allergy relief');
SELECT * FROM Doctors WHERE userID = 3;
-- =====================================================
-- NEXT STEPS (do these AFTER running this file)
-- =====================================================
-- 1. Create the admin (hashed automatically):
--        flask --app app create-admin
-- 2. Create doctors / patients / pharmacists by signing up on /register.
--    Each registration hashes the password and creates the matching
--    profile row, so every account can log in correctly.