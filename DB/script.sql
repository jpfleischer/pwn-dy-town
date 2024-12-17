CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    content VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
    sender VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    coordinates POINT
) CHARACTER SET=utf8mb4 COLLATE=utf8mb4_general_ci;
