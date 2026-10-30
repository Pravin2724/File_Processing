CREATE DATABASE AadhaarDB;
GO

USE AadhaarDB;
GO

CREATE TABLE AadhaarFiles (
    id INT IDENTITY(1,1) PRIMARY KEY,
    aadhaar_number VARCHAR(12) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_data VARBINARY(MAX) NOT NULL,
    uploaded_at DATETIME DEFAULT GETDATE()
);

select * from AadhaarFiles