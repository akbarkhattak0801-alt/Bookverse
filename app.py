import streamlit as st
import requests
import json
from datetime import datetime

st.set_page_config(page_title="BookGrok • AI Goodreads", page_icon="📖", layout="wide")

# ==================== SESSION STATE ====================
if "library" not in st.session_state:
    st.session_state.library = {}  # key: openlibrary key → book data + status

if "grok_api_key" not in st.session_state:
    st.session_state.grok_api_key = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ==================== SIDEBAR ====================
st.sidebar.title("📖 BookGrok")
st.sidebar.caption("Your AI-powered Goodreads")

page = st.sidebar.radio("Navigate", 
    ["🏠 Home", "🔎 Search Books", "📚 My Library", "✨ AI Recommendations", "💬 AI Chat"])

st.sidebar.divider()

api_key = st.sidebar.text_input("xAI Grok API Key", 
                               value=st.session_state.grok_api_key,
                               type="password",
                               help="Get it free at console.x.ai")

if api_key:
    st.session_state.grok_api_key = api_key

st.sidebar.caption("Built with ❤️ for readers in Pakistan 🇵🇰")

# ==================== HELPER FUNCTIONS ====================
def fetch_books(query, limit=12):
    url = f"https://openlibrary.org/search.json?q={query}&fields=key,title,author_name,first_publish_year,cover_i,edition_key&limit={limit}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        return data.get("docs", [])
    except:
        return []

def get_cover_url(cover_i):
    if cover_i:
        return f"https://covers.openlibrary.org/b/id/{cover_i}-M.jpg"
    return "https://via.placeholder.com/150x200/1a1a2e/ffffff?text=No+Cover"

def ask_grok(prompt, api_key):
    if not api_key:
        return "Please add your xAI API key in the sidebar first!"
    
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "grok-4.20-reasoning",
        "messages": [
            {"role": "system", "content": "You are Grok, an extremely knowledgeable and fun book expert. You help readers discover great books, answer questions without spoilers, and give honest literary advice."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 1200
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        else:
            return f"API Error {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return f"Connection error: {str(e)}"

# ==================== PAGES ====================
if page == "🏠 Home":
    st.title("📖 Welcome to BookGrok")
    st.markdown("### Your personal AI reading companion — Goodreads + Grok intelligence")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.image("https://picsum.photos/id/1015/1200/400", use_container_width=True)
    with col2:
        st.success("**AI Features Active**")
        st.write("• Smart recommendations")
        st.write("• Instant book/author Q&A")
        st.write("• No spoilers unless you ask 😉")
    
    st.subheader("Popular this week")
    popular = fetch_books("bestsellers OR award-winning", 6)
    cols = st.columns(6)
    for i, book in enumerate(popular[:6]):
        with cols[i]:
            cover = get_cover_url(book.get("cover_i"))
            st.image(cover, use_container_width=True)
            st.caption(f"**{book.get('title', 'Unknown')}**  \n{', '.join(book.get('author_name', ['Unknown']))}")
            if st.button("Add to Want to Read", key=f"home_{i}"):
                key = book["key"]
                st.session_state.library[key] = {
                    "title": book.get("title"),
                    "authors": book.get("author_name", ["Unknown"]),
                    "cover": cover,
                    "year": book.get("first_publish_year"),
                    "status": "want",
                    "rating": None,
                    "review": ""
                }
                st.success("Added!")

if page == "🔎 Search Books":
    st.title("🔎 Search Books")
    query = st.text_input("Search by title, author, or genre", placeholder="Dune, Haruki Murakami, fantasy Pakistan...")
    
    if query:
        books = fetch_books(query)
        if not books:
            st.warning("No books found. Try different keywords!")
        else:
            cols = st.columns(4)
            for i, book in enumerate(books):
                with cols[i % 4]:
                    cover = get_cover_url(book.get("cover_i"))
                    st.image(cover, use_container_width=True)
                    st.subheader(book.get("title", "Untitled"))
                    st.caption(f"{' • '.join(book.get('author_name', ['Unknown']))} • {book.get('first_publish_year', 'N/A')}")
                    
                    key = book["key"]
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        if st.button("Want", key=f"want_{i}"):
                            st.session_state.library[key] = {
                                "title": book.get("title"),
                                "authors": book.get("author_name", ["Unknown"]),
                                "cover": cover,
                                "year": book.get("first_publish_year"),
                                "status": "want",
                                "rating": None,
                                "review": ""
                            }
                            st.rerun()
                    with col_b:
                        if st.button("Reading", key=f"reading_{i}"):
                            st.session_state.library[key] = {**st.session_state.library.get(key, {}), "status": "reading"}
                            st.rerun()
                    with col_c:
                        if st.button("Read", key=f"read_{i}"):
                            st.session_state.library[key] = {**st.session_state.library.get(key, {}), "status": "read"}
                            st.rerun()

if page == "📚 My Library":
    st.title("📚 My Library")
    
    tabs = st.tabs(["Want to Read", "Currently Reading", "Read"])
    
    statuses = ["want", "reading", "read"]
    tab_names = ["Want to Read", "Currently Reading", "Read"]
    
    for tab, status in zip(tabs, statuses):
        with tab:
            books_in_shelf = [ (k, v) for k, v in st.session_state.library.items() if v.get("status") == status ]
            if not books_in_shelf:
                st.info(f"No books in {tab_names[statuses.index(status)]} yet")
                continue
            
            for key, book in books_in_shelf:
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.image(book["cover"], width=80)
                with col2:
                    st.subheader(book["title"])
                    st.caption(f"{' • '.join(book['authors'])} • {book.get('year', 'N/A')}")
                    
                    rating = st.slider("Rating", 1, 5, value=book.get("rating") or 3, key=f"rate_{key}")
                    review = st.text_area("Review / Notes", value=book.get("review", ""), key=f"rev_{key}", height=80)
                    
                    if st.button("Save changes", key=f"save_{key}"):
                        st.session_state.library[key]["rating"] = rating
                        st.session_state.library[key]["review"] = review
                        st.success("Saved!")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("Move to Read", key=f"move_{key}"):
                            st.session_state.library[key]["status"] = "read"
                            st.rerun()
                    with col_b:
                        if st.button("Remove", key=f"del_{key}"):
                            del st.session_state.library[key]
                            st.rerun()

    # Export / Import
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export Library as JSON"):
            data = json.dumps(st.session_state.library, indent=2)
            st.download_button("Download backup", data, file_name=f"bookgrok_backup_{datetime.now().strftime('%Y%m%d')}.json")
    with col2:
        uploaded = st.file_uploader("Import backup JSON", type="json")
        if uploaded:
            st.session_state.library = json.load(uploaded)
            st.success("Library restored!")

if page == "✨ AI Recommendations":
    st.title("✨ AI-Powered Recommendations")
    st.write("Grok will analyze your library and suggest perfect next reads.")
    
    if st.button("Get Personalized Recommendations", type="primary", use_container_width=True):
        if not st.session_state.library:
            st.warning("Add some books to your library first!")
        elif not st.session_state.grok_api_key:
            st.error("Add your xAI API key in the sidebar")
        else:
            with st.spinner("Grok is thinking about your taste..."):
                # Build context
                context = "My library:\n"
                for book in st.session_state.library.values():
                    status = book["status"]
                    rating = book.get("rating")
                    context += f"- {book['title']} by {', '.join(book['authors'])} ({status}"
                    if rating:
                        context += f", rated {rating}/5"
                    context += ")\n"
                
                prompt = f"{context}\n\nBased on the books above, recommend 5 new books I will love. For each suggestion give: title, author, short reason why it matches my taste, and a one-sentence hook. Be specific and exciting. Do not recommend anything already in my library."
                
                response = ask_grok(prompt, st.session_state.grok_api_key)
                st.markdown(response)

if page == "💬 AI Chat":
    st.title("💬 Talk to Grok about Books")
    st.caption("Ask anything: plot analysis, author deep-dives, 'what should I read if I loved Dune?', genre recommendations, etc.")
    
    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask anything about books or authors..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Grok is reading..."):
                # Optional: include library context
                library_summary = ""
                if st.session_state.library:
                    library_summary = "User's current library: " + ", ".join([b["title"] for b in st.session_state.library.values()]) + ". "
                
                full_prompt = f"{library_summary}Question: {prompt}"
                answer = ask_grok(full_prompt, st.session_state.grok_api_key)
                st.markdown(answer)
        
        st.session_state.chat_history.append({"role": "assistant", "content": answer})

# Footer
st.sidebar.divider()
st.sidebar.caption("Book data from Open Library • AI by xAI Grok 4.20")
st.caption("Made for you by Grok 🚀 Enjoy your reading journey!")
