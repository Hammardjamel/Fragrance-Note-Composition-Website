import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
import bcrypt

# ------------------------------
# Database connection (adjust if needed)
# ------------------------------
# If your MySQL has a password, change 'root:@localhost' to 'root:YOUR_PASSWORD@localhost'
engine = create_engine('mysql+mysqlconnector://root:@localhost/perfume_db')

# ------------------------------
# Authentication helpers
# ------------------------------
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_user(username, password, email=None):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id FROM users WHERE username = :username"), {"username": username})
        if result.fetchone():
            return False, "Username already exists"
        if email:
            result = conn.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email})
            if result.fetchone():
                return False, "Email already registered"
        hashed = hash_password(password)
        conn.execute(
            text("INSERT INTO users (username, password_hash, email) VALUES (:username, :password_hash, :email)"),
            {"username": username, "password_hash": hashed, "email": email}
        )
        conn.commit()
        return True, "User created"

def login_user(username, password):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, password_hash FROM users WHERE username = :username"), {"username": username})
        row = result.fetchone()
        if row and verify_password(password, row[1]):
            return row[0]
        return None

def get_user_dna(user_id):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT dna_notes FROM users WHERE id = :uid"), {"uid": user_id})
        row = result.fetchone()
        if row and row[0]:
            return row[0].split(',')
        return []

def save_user_dna(user_id, notes_list):
    dna_str = ','.join(notes_list)
    with engine.connect() as conn:
        conn.execute(text("UPDATE users SET dna_notes = :dna WHERE id = :uid"), {"dna": dna_str, "uid": user_id})
        conn.commit()

# ------------------------------
# Favorites functions
# ------------------------------
def add_favorite(user_id, perfume_id):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id FROM user_favorites WHERE user_id = :uid AND perfume_id = :pid"),
            {"uid": user_id, "pid": perfume_id}
        )
        if not result.fetchone():
            conn.execute(
                text("INSERT INTO user_favorites (user_id, perfume_id, added_at) VALUES (:uid, :pid, NOW())"),
                {"uid": user_id, "pid": perfume_id}
            )
            conn.commit()
            return True
        return False

def remove_favorite(user_id, perfume_id):
    with engine.connect() as conn:
        conn.execute(
            text("DELETE FROM user_favorites WHERE user_id = :uid AND perfume_id = :pid"),
            {"uid": user_id, "pid": perfume_id}
        )
        conn.commit()
        return True

def get_user_favorites(user_id):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT p.id, p.name_perfume, p.brand FROM perfumes p JOIN user_favorites f ON p.id = f.perfume_id WHERE f.user_id = :uid"),
            {"uid": user_id}
        )
        return result.fetchall()

# ------------------------------
# Review functions
# ------------------------------
def add_or_update_review(user_id, perfume_id, rating, review_text, longevity, sillage):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id FROM user_reviews WHERE user_id = :uid AND perfume_id = :pid"),
            {"uid": user_id, "pid": perfume_id}
        )
        if result.fetchone():
            conn.execute(
                text("""UPDATE user_reviews 
                        SET rating = :rating, review_text = :review_text, 
                            longevity_rating = :longevity, sillage_rating = :sillage, updated_at = NOW()
                        WHERE user_id = :uid AND perfume_id = :pid"""),
                {"rating": rating, "review_text": review_text, "longevity": longevity, "sillage": sillage, "uid": user_id, "pid": perfume_id}
            )
        else:
            conn.execute(
                text("""INSERT INTO user_reviews (user_id, perfume_id, rating, review_text, longevity_rating, sillage_rating, created_at, updated_at)
                        VALUES (:uid, :pid, :rating, :review_text, :longevity, :sillage, NOW(), NOW())"""),
                {"uid": user_id, "pid": perfume_id, "rating": rating, "review_text": review_text, "longevity": longevity, "sillage": sillage}
            )
        conn.commit()
        return True

def get_user_review(user_id, perfume_id):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT rating, review_text, longevity_rating, sillage_rating FROM user_reviews WHERE user_id = :uid AND perfume_id = :pid"),
            {"uid": user_id, "pid": perfume_id}
        )
        row = result.fetchone()
        if row:
            return {"rating": row[0], "review_text": row[1], "longevity": row[2], "sillage": row[3]}
        return None

# ------------------------------
# Search history logging
# ------------------------------
def log_search(user_id, search_query, search_type, results_count):
    with engine.connect() as conn:
        conn.execute(
            text("""INSERT INTO search_history (user_id, search_query, search_type, results_count, searched_at)
                    VALUES (:uid, :query, :type, :count, NOW())"""),
            {"uid": user_id, "query": search_query, "type": search_type, "count": results_count}
        )
        conn.commit()

# ------------------------------
# Load perfume data and notes
# ------------------------------
@st.cache_data
def load_perfume_data():
    query = "SELECT id, brand, name_perfume, fragrances FROM perfumes WHERE fragrances IS NOT NULL AND fragrances != ''"
    df = pd.read_sql(query, engine)
    df['notes_list'] = df['fragrances'].apply(lambda x: [n.strip().lower() for n in str(x).split(',')])
    return df

# Try to load data; if error, show message and stop
try:
    df = load_perfume_data()
    all_notes = set()
    for notes in df['notes_list']:
        all_notes.update(notes)
    all_notes = sorted(all_notes)
except Exception as e:
    st.error(f"Database error: {e}\n\nMake sure MySQL is running, database 'perfume_db' exists, and table 'perfumes' has data.")
    st.stop()

# Note families
note_families = {
    "Floral": ["rose", "jasmine", "lily", "tuberose", "orange blossom", "ylang ylang", "gardenia", "violet", "peony", "freesia"],
    "Woody": ["sandalwood", "cedar", "vetiver", "oud", "patchouli", "pine", "cypress", "oakmoss"],
    "Oriental / Warm": ["vanilla", "amber", "benzoin", "cinnamon", "clove", "cardamom", "tonka", "incense"],
    "Fresh / Citrus": ["bergamot", "lemon", "lime", "grapefruit", "orange", "mandarin", "sea salt", "aquatic", "mint", "green notes"],
    "Fruity": ["apple", "peach", "berry", "blackcurrant", "raspberry", "plum", "fig", "coconut"],
    "Spicy": ["black pepper", "pink pepper", "ginger", "nutmeg", "coriander", "anise", "saffron"],
    "Leather / Tobacco": ["leather", "tobacco", "smoke", "birch tar"],
    "Musk / Animalic": ["musk", "ambergris", "ambroxan", "civet"],
    "Gourmand": ["caramel", "honey", "chocolate", "cotton candy", "marshmallow", "praline"],
    "Green / Herbal": ["grass", "fig leaf", "violet leaf", "basil", "thyme", "rosemary", "sage", "lavender"]
}
note_to_family = {}
for family, notes in note_families.items():
    for note in notes:
        note_to_family[note] = family
for note in all_notes:
    if note not in note_to_family:
        note_to_family[note] = "Other"

family_to_notes = {}
for note, family in note_to_family.items():
    family_to_notes.setdefault(family, []).append(note)

# ------------------------------
# Recommendation function (Jaccard)
# ------------------------------
def recommend_by_notes(selected_notes, top_n=20):
    if not selected_notes:
        return pd.DataFrame()
    selected_set = set(selected_notes)
    scores = []
    for idx, row in df.iterrows():
        perfume_set = set(row['notes_list'])
        if not perfume_set:
            scores.append(0)
            continue
        intersection = len(selected_set & perfume_set)
        union = len(selected_set | perfume_set)
        jaccard = intersection / union if union > 0 else 0
        scores.append(jaccard)
    df_copy = df.copy()
    df_copy['score'] = scores
    df_sorted = df_copy.sort_values('score', ascending=False).head(top_n)
    return df_sorted[['id', 'brand', 'name_perfume', 'fragrances', 'score']]

# ------------------------------
# Streamlit UI
# ------------------------------
st.set_page_config(page_title="Perfume DNA App", layout="wide")

# Session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'search_results' not in st.session_state:
    st.session_state.search_results = None

# Sidebar Authentication
with st.sidebar:
    st.title("🔐 Account")
    if st.session_state.user_id is None:
        choice = st.radio("Login / Register", ["Login", "Register"])
        if choice == "Login":
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                uid = login_user(username, password)
                if uid:
                    st.session_state.user_id = uid
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        else:
            new_user = st.text_input("Choose username")
            new_pass = st.text_input("Choose password", type="password")
            email = st.text_input("Email (optional)")
            if st.button("Register"):
                if not new_user or not new_pass:
                    st.error("Username and password required")
                else:
                    ok, msg = create_user(new_user, new_pass, email if email else None)
                    if ok:
                        st.success(msg + " – please login")
                    else:
                        st.error(msg)
    else:
        st.write(f"Logged in as: **{st.session_state.username}**")
        saved_dna = get_user_dna(st.session_state.user_id)
        if saved_dna:
            st.write("Your saved DNA notes:")
            st.write(", ".join(saved_dna))
        if st.button("Logout"):
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.search_results = None
            st.rerun()

# Main app
st.title("🌿 Perfume DNA Recommender")

if st.session_state.user_id is None:
    st.info("Please login or register to save DNA, favorites, and reviews.")
else:
    # Note selection
    st.subheader("Build your scent DNA (notes you love – affects recommendations)")
    selected_notes = []
    for family, notes in sorted(family_to_notes.items()):
        with st.expander(f"🌼 {family} ({len(notes)} notes)"):
            cols = st.columns(4)
            for i, note in enumerate(sorted(notes)):
                if cols[i % 4].checkbox(note, key=f"note_{note}"):
                    selected_notes.append(note)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Find my perfumes", type="primary"):
            if not selected_notes:
                st.warning("Select at least one note")
            else:
                results = recommend_by_notes(selected_notes, top_n=20)
                st.session_state.search_results = results
                log_search(st.session_state.user_id, ", ".join(selected_notes), "note_dna", len(results))
                st.success(f"Found {len(results)} perfumes. Search logged!")
        if st.button("💾 Save my DNA (current selection)"):
            if selected_notes:
                save_user_dna(st.session_state.user_id, selected_notes)
                st.success("DNA saved!")
            else:
                st.warning("No notes selected")
    
    # Display results
    if st.session_state.search_results is not None and not st.session_state.search_results.empty:
        results = st.session_state.search_results
        st.subheader(f"Top {len(results)} matching perfumes")
        for _, row in results.iterrows():
            with st.container():
                st.markdown(f"**{row['name_perfume']}** by *{row['brand']}* – match: {row['score']:.2f}")
                st.caption(f"Notes: {row['fragrances']}")
                
                # Favorite button
                if st.button(f"❤️ Add to favorites", key=f"fav_{row['id']}"):
                    if add_favorite(st.session_state.user_id, row['id']):
                        st.success(f"Added {row['name_perfume']} to favorites!")
                        st.rerun()
                    else:
                        st.info("Already in favorites")
                
                # Review section
                with st.expander("✍️ Write a review"):
                    rating = st.slider("Rating (1-5)", 1.0, 5.0, 3.0, 0.5, key=f"rate_{row['id']}")
                    longevity = st.selectbox("Longevity (1-5)", [1,2,3,4,5], key=f"long_{row['id']}")
                    sillage = st.selectbox("Sillage (1-5)", [1,2,3,4,5], key=f"sill_{row['id']}")
                    review_text = st.text_area("Your review", key=f"rev_{row['id']}")
                    if st.button("Submit review", key=f"submit_{row['id']}"):
                        add_or_update_review(st.session_state.user_id, row['id'], rating, review_text, longevity, sillage)
                        st.success("Review saved!")
                
                existing_review = get_user_review(st.session_state.user_id, row['id'])
                if existing_review:
                    st.caption(f"Your review: {existing_review['rating']}⭐ | Longevity: {existing_review['longevity']} | Sillage: {existing_review['sillage']}")
                st.divider()
    
    # Favorites in sidebar
    st.sidebar.subheader("❤️ Your Favorites")
    favs = get_user_favorites(st.session_state.user_id)
    if favs:
        for fav in favs:
            st.sidebar.write(f"- {fav[1]} by {fav[2]}")
            if st.sidebar.button(f"Remove", key=f"remove_{fav[0]}"):
                remove_favorite(st.session_state.user_id, fav[0])
                st.rerun()
    else:
        st.sidebar.write("No favorites yet.")