CREATE DATABASE Bluck Hut Tech Services;

USE Bluck Hut Tech Services;

CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phone VARCHAR(20) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    account_reference VARCHAR(255) NOT NULL,
    request_time DATETIME NOT NULL,
    completion_time DATETIME,
    status ENUM('pending', 'completed', 'failed') DEFAULT 'pending',
    mpesa_receipt VARCHAR(50),
    mpesa_response JSON
);

CREATE TABLE contacts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    submission_time DATETIME NOT NULL,
    status ENUM('unread', 'read', 'replied') DEFAULT 'unread'
);