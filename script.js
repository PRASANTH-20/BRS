let selectedTone = "All";

// Tone selection highlight logic
document.querySelectorAll(".emoji-button").forEach(button => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".emoji-button").forEach(b => {
      b.classList.remove("ring-4", "ring-indigo-400", "ring-offset-2");
    });
    button.classList.add("ring-4", "ring-indigo-400", "ring-offset-2");
    selectedTone = button.getAttribute("data-tone");
  });
});

// Handle form submission and redirect
function submitData() {
  const query = document.getElementById("query").value;
  const category = document.getElementById("category").value;
  const tone = selectedTone;

  if (!query || !category) {
    alert("Please fill in both description and category.");
    return;
  }

  localStorage.setItem("bookDescription", query);
  localStorage.setItem("bookCategory", category);
  localStorage.setItem("bookTone", tone);

  window.location.href = "list_of_books.html";
}

// Load category list from backend
function loadCategories() {
fetch("https://brs-8rlq.onrender.com/categories")
 // fetch("http://localhost:8000/categories")
    .then(res => res.json())
    .then(data => {
      const dropdown = document.getElementById("category");
      dropdown.innerHTML = '<option disabled selected value="">Select Category</option>';
      data.forEach(cat => {
        const option = document.createElement("option");
        option.value = cat;
        option.textContent = cat;
        dropdown.appendChild(option);
      });
    });
}

// Book Details Page Loader
function loadBookDetailsPage() {
  const urlParams = new URLSearchParams(window.location.search);
  const bookId = urlParams.get('id');

  if (!bookId) {
    const titleEl = document.getElementById('book-title');
    if (titleEl) titleEl.textContent = "Book ID missing in URL.";
    return;
  }

  fetch(`http://localhost:8000/book/${bookId}`)
    .then(res => {
      if (!res.ok) throw new Error("Book not found");
      return res.json();
    })
    .then(book => {
      if (document.getElementById('book-image')) {
        document.getElementById('book-image').src = book.thumbnail || 'cover-not-found.jpg';
        document.getElementById('book-quote').textContent = book.quote || "No quote available.";
        document.getElementById('book-title').textContent = book.caption || "Untitled Book";
        document.getElementById('book-description').textContent = book.description || "No description available.";
        document.getElementById('book-category').textContent = `Category: ${book.category || "Unknown"}`;
        document.getElementById('book-emotion').textContent = `Emotion: ${book.emotion || "N/A"}`;
      }
    })
    .catch(err => {
      console.error("Failed to load book details:", err);
      const titleEl = document.getElementById('book-title');
      if (titleEl) titleEl.textContent = "Failed to load book details.";
    });
}

// Initialize on window load
window.onload = () => {
  loadCategories();
  loadBookDetailsPage();
};
