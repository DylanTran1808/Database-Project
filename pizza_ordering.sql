-- MySQL dump 10.13  Distrib 9.4.0, for macos14.7 (arm64)
--
-- Host: localhost    Database: pizza_ordering
-- ------------------------------------------------------
-- Server version	9.4.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-09-04 13:47:25
-- Drop tables if they exist (for clean setup)

/* Only use the 2 below commands once*/
DROP DATABASE IF EXISTS pizza_ordering;
CREATE DATABASE pizza_ordering; 

USE pizza_ordering;


-- ========================
-- Customer Table
-- ========================
CREATE TABLE Customer (
    customer_id INT AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    postcode VARCHAR(20) NOT NULL,
    birth_date DATE NOT NULL,
    address VARCHAR(255),
    PRIMARY KEY (customer_id)
);

-- ========================
-- Delivery Person Table
-- ========================
CREATE TABLE DeliveryPerson (
    delivery_person_id INT AUTO_INCREMENT,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    gender VARCHAR(10),
    age INT,
    PRIMARY KEY (delivery_person_id)
);

-- ========================
-- Pizza Table
-- ========================
CREATE TABLE Pizza (
    pizza_id INT AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    PRIMARY KEY (pizza_id)
);

-- ========================
-- Ingredient Table
-- ========================
CREATE TABLE Ingredient (
    ingredient_id INT AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    PRIMARY KEY (ingredient_id)
);

-- ========================
-- PizzaIngredient (junction for Pizza ↔ Ingredient)
-- ========================
CREATE TABLE PizzaIngredient (
    pizza_id INT,
    ingredient_id INT,
    quantity DECIMAL(5,2) DEFAULT 1,
    PRIMARY KEY (pizza_id, ingredient_id),
    FOREIGN KEY (pizza_id) REFERENCES Pizza(pizza_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES Ingredient(ingredient_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- ========================
-- Discount Code Table
-- ========================
CREATE TABLE DiscountCode (
    discount_id INT AUTO_INCREMENT,
    percentage DECIMAL(5,2),
    cost DECIMAL(10,2),
    type VARCHAR(50),
    PRIMARY KEY (discount_id)
);

-- ========================
-- Orders Table
-- ========================
CREATE TABLE Orders (
    order_id INT AUTO_INCREMENT,
    customer_id INT,
    delivery_person_id INT,
    discount_id INT,
    total_amount DECIMAL(10,2),
    total_price DECIMAL(10,2),
    order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (order_id),
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (delivery_person_id) REFERENCES DeliveryPerson(delivery_person_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (discount_id) REFERENCES DiscountCode(discount_id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- ========================
-- OrderItem Table
-- ========================
CREATE TABLE OrderItem (
    order_item_id INT AUTO_INCREMENT,
    order_id INT,
    pizza_id INT,
    type VARCHAR(50),
    quantity INT NOT NULL,
    price DECIMAL(10,2),
    PRIMARY KEY (order_item_id),
    FOREIGN KEY (order_id) REFERENCES Orders(order_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (pizza_id) REFERENCES Pizza(pizza_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);
