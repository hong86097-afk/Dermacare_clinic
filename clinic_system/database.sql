-- =====================================================
-- Clinic Management System - Database Schema
-- =====================================================

DROP DATABASE IF EXISTS clinic;
CREATE DATABASE clinic;
USE clinic;

-- -----------------------------------------------------
-- Users (authentication for all roles)
-- -----------------------------------------------------
CREATE TABLE Users (
    userID INT AUTO_INCREMENT PRIMARY KEY,
    userName VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    roles ENUM('Doctor', 'Patient', 'Pharmacist', 'Admin') NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15),
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_username CHECK (CHAR_LENGTH(userName) >= 5),
    CONSTRAINT chk_phone CHECK (CHAR_LENGTH(phone) >= 9)
);

-- -----------------------------------------------------
-- Doctors
-- -----------------------------------------------------
CREATE TABLE Doctors (
    doctorID INT AUTO_INCREMENT PRIMARY KEY,
    doctorName VARCHAR(50) NOT NULL,
    specialization ENUM('Dermatology', 'Cosmetic', 'General', 'Pediatrics', 'Cardiology') NOT NULL,
    userID INT NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(15),
    consultationFee DECIMAL(10,2) DEFAULT 50.00,
    FOREIGN KEY (userID) REFERENCES Users(userID) ON DELETE CASCADE,
    CONSTRAINT chk_doctor_name CHECK (CHAR_LENGTH(doctorName) >= 3)
);

-- -----------------------------------------------------
-- Patients
-- -----------------------------------------------------
CREATE TABLE Patients (
    patientID INT AUTO_INCREMENT PRIMARY KEY,
    patientName VARCHAR(50) NOT NULL,
    userID INT NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(15),
    dateOfBirth DATE,
    gender ENUM('Male', 'Female', 'Other'),
    address VARCHAR(255),
    FOREIGN KEY (userID) REFERENCES Users(userID) ON DELETE CASCADE,
    CONSTRAINT chk_patient_name CHECK (CHAR_LENGTH(patientName) >= 3)
);

-- -----------------------------------------------------
-- Pharmacists
-- -----------------------------------------------------
CREATE TABLE Pharmacists (
    pharmacistID INT AUTO_INCREMENT PRIMARY KEY,
    pharmacistName VARCHAR(50) NOT NULL,
    userID INT NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(15),
    FOREIGN KEY (userID) REFERENCES Users(userID) ON DELETE CASCADE,
    CONSTRAINT chk_pharmacist_name CHECK (CHAR_LENGTH(pharmacistName) >= 3)
);

-- -----------------------------------------------------
-- Appointments
-- -----------------------------------------------------
CREATE TABLE Appointments (
    appointmentID INT AUTO_INCREMENT PRIMARY KEY,
    patientID INT NOT NULL,
    doctorID INT NOT NULL,
    appointmentDate DATETIME NOT NULL,
    reason VARCHAR(255),
    status ENUM('Scheduled', 'Completed', 'Cancelled') DEFAULT 'Scheduled',
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patientID) REFERENCES Patients(patientID) ON DELETE CASCADE,
    FOREIGN KEY (doctorID) REFERENCES Doctors(doctorID) ON DELETE CASCADE
);

-- -----------------------------------------------------
-- Medicines
-- -----------------------------------------------------
CREATE TABLE Medicines (
    medicineID INT AUTO_INCREMENT PRIMARY KEY,
    medicineName VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    stock INT DEFAULT 0,
    description TEXT
);

-- -----------------------------------------------------
-- Prescriptions
-- -----------------------------------------------------
CREATE TABLE Prescriptions (
    prescriptionID INT AUTO_INCREMENT PRIMARY KEY,
    appointmentID INT NOT NULL,
    pharmacistID INT,
    medicineID INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    instructions TEXT,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointmentID) REFERENCES Appointments(appointmentID) ON DELETE CASCADE,
    FOREIGN KEY (pharmacistID) REFERENCES Pharmacists(pharmacistID) ON DELETE SET NULL,
    FOREIGN KEY (medicineID) REFERENCES Medicines(medicineID)
);

-- -----------------------------------------------------
-- Invoices
-- -----------------------------------------------------
CREATE TABLE Invoices (
    invoiceID INT AUTO_INCREMENT PRIMARY KEY,
    appointmentID INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    paymentStatus ENUM('Pending', 'Paid', 'Cancelled') DEFAULT 'Pending',
    issuedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    paidAt DATETIME,
    FOREIGN KEY (appointmentID) REFERENCES Appointments(appointmentID) ON DELETE CASCADE
);

-- -----------------------------------------------------
-- Contact messages
-- -----------------------------------------------------
CREATE TABLE Messages (
    messageID INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    subject VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- SAMPLE DATA (default password for all: "password123")
-- =====================================================

-- Admin user
INSERT INTO Users (userName, password, roles, email, phone) VALUES
('adminuser', 'scrypt:32768:8:1$placeholder', 'Admin', 'admin@clinic.com', '0123456789');

-- Sample doctors
INSERT INTO Users (userName, password, roles, email, phone) VALUES
('drsmith', 'scrypt:32768:8:1$placeholder', 'Doctor', 'smith@clinic.com', '0123456701'),
('drjones', 'scrypt:32768:8:1$placeholder', 'Doctor', 'jones@clinic.com', '0123456702');

INSERT INTO Doctors (doctorName, specialization, userID, email, phone, consultationFee) VALUES
('Dr. John Smith', 'General', 2, 'smith@clinic.com', '0123456701', 50.00),
('Dr. Sarah Jones', 'Dermatology', 3, 'jones@clinic.com', '0123456702', 75.00);

-- Sample patient
INSERT INTO Users (userName, password, roles, email, phone) VALUES
('patient1', 'scrypt:32768:8:1$placeholder', 'Patient', 'patient1@mail.com', '0987654321');

INSERT INTO Patients (patientName, userID, email, phone, dateOfBirth, gender, address) VALUES
('Mary Johnson', 4, 'patient1@mail.com', '0987654321', '1990-05-15', 'Female', '123 Main St');

-- Sample pharmacist
INSERT INTO Users (userName, password, roles, email, phone) VALUES
('pharma1', 'scrypt:32768:8:1$placeholder', 'Pharmacist', 'pharma@clinic.com', '0111222333');

INSERT INTO Pharmacists (pharmacistName, userID, email, phone) VALUES
('Tom Wilson', 5, 'pharma@clinic.com', '0111222333');

-- Sample medicines
INSERT INTO Medicines (medicineName, category, price, stock, description) VALUES
('Paracetamol 500mg', 'Pain Relief', 5.00, 200, 'For pain and fever'),
('Amoxicillin 250mg', 'Antibiotic', 12.50, 100, 'Bacterial infections'),
('Ibuprofen 200mg', 'Pain Relief', 6.50, 150, 'Anti-inflammatory'),
('Vitamin C 1000mg', 'Supplement', 8.00, 300, 'Immune support'),
('Cetirizine 10mg', 'Antihistamine', 4.50, 120, 'Allergy relief');
