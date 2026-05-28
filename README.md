# Fragrance-Note-Composition-Website
A web-based perfume recommendation system that helps users discover perfumes based on fragrance notes, preferences, and favorites. The system includes user authentication, recommendation features, and database management.


# Perfume DNA Recommender prototype

## Overview

This application is a perfume recommendation system built with:

* Python
* Streamlit
* MySQL
* SQLAlchemy
* Pandas
* BCrypt authentication

The system allows users to:

* Register and login securely
* Build a personal perfume DNA based on fragrance notes
* Receive perfume recommendations
* Save favorite perfumes
* Write and update reviews
* Store scent preferences
* Track search history

---

# Main Components

## Database Connection

Creates a connection to the MySQL database `perfume_db` using SQLAlchemy.

Purpose:

* Access perfume data
* Store user accounts
* Save favorites, reviews, and search history

---

## Authentication System

### `hash_password(password)`

Encrypts passwords using BCrypt before saving them to the database.

### `verify_password(password, hashed)`

Checks if a login password matches the stored encrypted password.

### `create_user(username, password, email)`

Registers a new user after checking:

* username uniqueness
* email uniqueness

### `login_user(username, password)`

Authenticates users and returns the user ID after successful login.

---

## User DNA Functions

### `get_user_dna(user_id)`

Retrieves saved fragrance notes for a user.

### `save_user_dna(user_id, notes_list)`

Stores selected fragrance notes as the user’s perfume DNA.

Purpose:

* personalize recommendations
* save user preferences

---

# Favorites System

### `add_favorite(user_id, perfume_id)`

Adds a perfume to the user favorites list.

### `remove_favorite(user_id, perfume_id)`

Removes a perfume from favorites.

### `get_user_favorites(user_id)`

Returns all saved favorite perfumes for a user.

---

# Review System

### `add_or_update_review(...)`

Allows users to:

* rate perfumes
* write reviews
* score longevity
* score sillage

If a review already exists, it updates the existing review.

### `get_user_review(user_id, perfume_id)`

Retrieves a user review for a specific perfume.

---

# Search History

### `log_search(user_id, search_query, search_type, results_count)`

Stores user searches for analytics and tracking.

---

# Perfume Data Loading

### `load_perfume_data()`

Loads perfume information from the database and converts fragrance notes into structured lists.

Uses Streamlit cache for better performance.

---

# Recommendation System

### `recommend_by_notes(selected_notes, top_n=20)`

Core recommendation engine.

Uses:

* Jaccard similarity algorithm

Purpose:

* compare user selected notes with perfume notes
* calculate similarity scores
* return the best perfume matches

---

# Streamlit User Interface

The UI includes:

## Authentication Sidebar

* Login
* Register
* Logout

## Perfume DNA Builder

Users select fragrance notes grouped by families:

* Floral
* Woody
* Oriental
* Fresh
* Fruity
* Spicy
* Gourmand
* Herbal
* and more

## Recommendation Results

Displays:

* perfume name
* brand
* fragrance notes
* similarity score

Users can:

* save favorites
* write reviews
* update reviews

## Favorites Sidebar

Displays all favorite perfumes for the logged-in user.

---

# Technologies Used

* Python
* Streamlit
* Pandas
* SQLAlchemy
* MySQL
* BCrypt

---

# Recommendation Algorithm

The application uses:

* Jaccard Similarity

Formula:

Similarity = Intersection / Union

This compares:

* user selected fragrance notes
  with
* perfume fragrance notes

Higher score = better perfume match.

---

# Features Summary

✔ User authentication
✔ Secure password hashing
✔ Perfume DNA system
✔ Personalized recommendations
✔ Favorites system
✔ Review system
✔ Search history logging
✔ Dynamic Streamlit interface
✔ MySQL database integration
✔ Recommendation engine using similarity matching

