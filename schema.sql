-- ============================================================================
-- FridgeBuddy Database Schema
-- PostgreSQL initialization script
-- ============================================================================

-- Create database (run this as postgres superuser)
-- CREATE DATABASE fridgebuddy;
-- CREATE USER fridgebuddy WITH ENCRYPTED PASSWORD 'fridgebuddy123';
-- GRANT ALL PRIVILEGES ON DATABASE fridgebuddy TO fridgebuddy;

-- Connect to fridgebuddy database before running the rest

-- ============================================================================
-- Drop existing tables (for clean setup)
-- ============================================================================

DROP TABLE IF EXISTS items CASCADE;
DROP TYPE IF EXISTS category_enum CASCADE;
DROP TYPE IF EXISTS unit_enum CASCADE;
DROP TYPE IF EXISTS user_role_enum CASCADE;

-- ============================================================================
-- Create ENUM types
-- ============================================================================

-- Category enum for item categorization
CREATE TYPE category_enum AS ENUM (
    'Dairy',
    'Meat',
    'Seafood',
    'Vegetables',
    'Fruits',
    'Beverages',
    'Condiments',
    'Leftovers',
    'Frozen',
    'Other'
);

-- Unit enum for quantity measurement
CREATE TYPE unit_enum AS ENUM (
    'pieces',
    'mL',
    'L',
    'g',
    'kg'
);

-- User role enum (for future multi-user support)
CREATE TYPE user_role_enum AS ENUM (
    'Owner',
    'Co-Owner',
    'Child'
);

-- ============================================================================
-- Create Items Table
-- ============================================================================

CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity >= 0),
    unit unit_enum NOT NULL DEFAULT 'pieces',
    expiry_date DATE NOT NULL,
    category category_enum NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Create Indexes for Performance
-- ============================================================================

-- Index for category filtering (User Story 5)
CREATE INDEX idx_items_category ON items(category);

-- Index for name search (User Story 6)
CREATE INDEX idx_items_name_lower ON items(LOWER(name) varchar_pattern_ops);

-- Index for expiry date sorting and filtering
CREATE INDEX idx_items_expiry_date ON items(expiry_date);

-- Composite index for common query pattern (category + expiry)
CREATE INDEX idx_items_category_expiry ON items(category, expiry_date);

-- ============================================================================
-- Create Function for Auto-updating updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================================================
-- Create Trigger for Auto-updating updated_at
-- ============================================================================

CREATE TRIGGER update_items_updated_at
    BEFORE UPDATE ON items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Insert Sample Data
-- ============================================================================

INSERT INTO items (name, quantity, unit, expiry_date, category) VALUES
    -- Dairy products
    ('Milk', 2, 'L', CURRENT_DATE + INTERVAL '5 days', 'Dairy'),
    ('Greek Yogurt', 3, 'pieces', CURRENT_DATE + INTERVAL '10 days', 'Dairy'),
    ('Cheddar Cheese', 500, 'g', CURRENT_DATE + INTERVAL '30 days', 'Dairy'),
    ('Butter', 250, 'g', CURRENT_DATE + INTERVAL '45 days', 'Dairy'),
    
    -- Meat products
    ('Chicken Breast', 500, 'g', CURRENT_DATE + INTERVAL '3 days', 'Meat'),
    ('Ground Beef', 400, 'g', CURRENT_DATE + INTERVAL '2 days', 'Meat'),
    ('Bacon', 200, 'g', CURRENT_DATE + INTERVAL '7 days', 'Meat'),
    
    -- Seafood
    ('Salmon Fillet', 300, 'g', CURRENT_DATE + INTERVAL '2 days', 'Seafood'),
    ('Shrimp', 500, 'g', CURRENT_DATE + INTERVAL '4 days', 'Seafood'),
    
    -- Vegetables
    ('Broccoli', 2, 'pieces', CURRENT_DATE + INTERVAL '5 days', 'Vegetables'),
    ('Carrots', 500, 'g', CURRENT_DATE + INTERVAL '14 days', 'Vegetables'),
    ('Spinach', 200, 'g', CURRENT_DATE + INTERVAL '4 days', 'Vegetables'),
    ('Bell Peppers', 3, 'pieces', CURRENT_DATE + INTERVAL '7 days', 'Vegetables'),
    ('Tomatoes', 4, 'pieces', CURRENT_DATE + INTERVAL '6 days', 'Vegetables'),
    
    -- Fruits
    ('Apples', 6, 'pieces', CURRENT_DATE + INTERVAL '14 days', 'Fruits'),
    ('Bananas', 5, 'pieces', CURRENT_DATE + INTERVAL '4 days', 'Fruits'),
    ('Oranges', 4, 'pieces', CURRENT_DATE + INTERVAL '10 days', 'Fruits'),
    ('Strawberries', 250, 'g', CURRENT_DATE + INTERVAL '3 days', 'Fruits'),
    
    -- Beverages
    ('Orange Juice', 1, 'L', CURRENT_DATE + INTERVAL '14 days', 'Beverages'),
    ('Sparkling Water', 6, 'pieces', CURRENT_DATE + INTERVAL '180 days', 'Beverages'),
    
    -- Condiments
    ('Mayonnaise', 400, 'mL', CURRENT_DATE + INTERVAL '60 days', 'Condiments'),
    ('Ketchup', 500, 'mL', CURRENT_DATE + INTERVAL '90 days', 'Condiments'),
    ('Soy Sauce', 300, 'mL', CURRENT_DATE + INTERVAL '365 days', 'Condiments'),
    
    -- Leftovers
    ('Pasta from Monday', 1, 'pieces', CURRENT_DATE + INTERVAL '2 days', 'Leftovers'),
    ('Chicken Curry', 2, 'pieces', CURRENT_DATE + INTERVAL '3 days', 'Leftovers'),
    
    -- Frozen items
    ('Ice Cream', 500, 'mL', CURRENT_DATE + INTERVAL '90 days', 'Frozen'),
    ('Frozen Pizza', 2, 'pieces', CURRENT_DATE + INTERVAL '60 days', 'Frozen'),
    ('Frozen Vegetables Mix', 1, 'kg', CURRENT_DATE + INTERVAL '120 days', 'Frozen');

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Show all items
SELECT 'All Items:' as info;
SELECT id, name, quantity, unit, expiry_date, category FROM items ORDER BY expiry_date;

-- Show items by category count
SELECT 'Items by Category:' as info;
SELECT category, COUNT(*) as item_count FROM items GROUP BY category ORDER BY category;

-- Show items expiring within 5 days
SELECT 'Items Expiring Within 5 Days:' as info;
SELECT id, name, expiry_date, category 
FROM items 
WHERE expiry_date <= CURRENT_DATE + INTERVAL '5 days'
ORDER BY expiry_date;
