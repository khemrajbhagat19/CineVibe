import { useEffect, useState } from "react";
import { Link, Navigate, Route, Routes, useNavigate, useParams, useSearchParams } from "react-router-dom";
import api, { mediaUrl } from "./api";


// Convert API/network errors into readable text for the UI.
// FastAPI validation errors may return an array of objects in `detail`.
function getApiErrorMessage(error, fallback = "Something went wrong. Please try again.") {
  const data = error?.response?.data;
  const detail = data?.detail ?? data?.message ?? error?.message;

  if (typeof detail === "string" && detail.trim()) return detail;

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object") {
          const location = Array.isArray(item.loc) ? item.loc.join(" → ") : "";
          const message = item.msg || item.message || JSON.stringify(item);
          return location ? `${location}: ${message}` : message;
        }
        return String(item);
      })
      .join("; ");
  }

  if (detail && typeof detail === "object") {
    return detail.message || detail.msg || JSON.stringify(detail);
  }

  return fallback;
}

function readUser() {
  try { return JSON.parse(localStorage.getItem("cinevibe_user") || "null"); }
  catch { return null; }
}

function useAuth() {
  const [user, setUser] = useState(readUser);
  function onAuth(data) {
    localStorage.setItem("cinevibe_token", data.access_token);
    localStorage.setItem("cinevibe_user", JSON.stringify(data.user));
    setUser(data.user);
  }
  function logout() {
    localStorage.removeItem("cinevibe_token");
    localStorage.removeItem("cinevibe_user");
    setUser(null);
  }
  return { user, onAuth, logout };
}

function App() {
  const auth = useAuth();
  return <>
    <Header user={auth.user} logout={auth.logout} />
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/movies" element={<Movies />} />
      <Route path="/movies/:id" element={<MovieDetails />} />
      <Route path="/watch/:id" element={<Watch user={auth.user} />} />
      <Route path="/login" element={<AuthPage mode="login" onAuth={auth.onAuth} />} />
      <Route path="/register" element={<AuthPage mode="register" onAuth={auth.onAuth} />} />
      <Route path="/history" element={auth.user ? <History /> : <Navigate to="/login" replace />} />
      <Route path="/admin" element={auth.user?.is_admin ? <Admin /> : <Navigate to={auth.user ? "/" : "/login"} replace />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
    <footer className="section muted center">© {new Date().getFullYear()} CineVibe. Stream your next favourite.</footer>
  </>;
}

function Header({ user, logout }) {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  function submit(e) { e.preventDefault(); navigate(`/movies?search=${encodeURIComponent(query)}`); }
  return <header className="nav">
    <Link className="brand" to="/"><span>CV</span> Cine<span>Vibe</span></Link>
    <nav><Link to="/">Home</Link><Link to="/movies">Movies</Link>{user && <Link to="/history">My History</Link>}{user?.is_admin && <Link to="/admin">Admin</Link>}</nav>
    <form className="search" onSubmit={submit}><input aria-label="Search movies" placeholder="Search movies..." value={query} onChange={e => setQuery(e.target.value)} /></form>
    {user ? <button className="ghost small" onClick={logout}>Logout</button> : <Link className="primary small" to="/login">Sign in</Link>}
  </header>;
}

function Home() {
  const [movies, setMovies] = useState([]);
  const [error, setError] = useState("");
  useEffect(() => { api.get("/movies").then(r => setMovies(r.data)).catch(() => setError("Could not load movies. Check that the backend is running.")); }, []);
  const featured = movies[0];
  return <>
    <section className="hero">
      <div className="hero-copy"><div className="eyebrow">Your cinema, anywhere</div><h1>Stories worth<br/>staying in for.</h1><p>Discover movies, press play, and pick up right where you left off.</p><div className="actions"><Link className="primary" to={featured ? `/movies/${featured.id}` : "/movies"}>Explore movies</Link><Link className="ghost" to="/movies">Browse library</Link></div></div>
    </section>
    <section className="section"><div className="section-title"><h2>Recently added</h2><Link to="/movies">View all →</Link></div>{error ? <p className="error">{error}</p> : <MovieGrid movies={movies.slice(0, 10)} />}</section>
  </>;
}

function Movies() {
  const [params, setParams] = useSearchParams();
  const [movies, setMovies] = useState([]);
  const [genres, setGenres] = useState([]);
  const [loading, setLoading] = useState(true);
  const search = params.get("search") || "";
  const genre = params.get("genre") || "";
  const sort = params.get("sort") || "latest";
  useEffect(() => { api.get("/movies/meta/genres").then(r => setGenres(r.data)).catch(() => {}); }, []);
  useEffect(() => {
    setLoading(true);
    api.get("/movies", { params: { search, genre, sort } }).then(r => setMovies(r.data)).catch(() => setMovies([])).finally(() => setLoading(false));
  }, [search, genre, sort]);
  function change(key, value) { const next = new URLSearchParams(params); value ? next.set(key, value) : next.delete(key); setParams(next); }
  return <main className="container page"><div className="page-head"><div><div className="eyebrow">Explore</div><h1>Movie library</h1></div><span className="muted">{movies.length} titles</span></div>
    <div className="filters"><input placeholder="Search title, genre or description" value={search} onChange={e => change("search", e.target.value)} /><select value={genre} onChange={e => change("genre", e.target.value)}><option value="">All genres</option>{genres.map(g => <option key={g}>{g}</option>)}</select><select value={sort} onChange={e => change("sort", e.target.value)}><option value="latest">Recently added</option><option value="views">Most watched</option><option value="az">A–Z</option></select></div>
    {loading ? <Loader /> : <MovieGrid movies={movies} />}
  </main>;
}

function MovieGrid({ movies }) {
  if (!movies.length) return <div className="empty">No movies found yet. An administrator can add movies from the dashboard.</div>;
  return <div className="grid">{movies.map(movie => <MovieCard key={movie.id} movie={movie} />)}</div>;
}
function MovieCard({ movie, progress }) {
  return <article className="card"><Link className="poster" to={`/movies/${movie.id}`}>
    {movie.thumbnail_url ? <img src={mediaUrl(movie.thumbnail_url)} alt={`${movie.title} poster`} onError={e => { e.currentTarget.style.display = "none"; }} /> : <div className="fallback">CV</div>}
    <span className="tag">{movie.genre}</span><span className="play">▶</span>{progress > 0 && <span className="progress"><i style={{width:`${progress}%`}} /></span>}
  </Link><div className="card-body"><h3><Link to={`/movies/${movie.id}`} style={{color:"inherit",textDecoration:"none"}}>{movie.title}</Link></h3><p>{movie.release_year} · {formatDuration(movie.duration_seconds)}</p></div></article>;
}

function MovieDetails() {
  const { id } = useParams(); const [movie, setMovie] = useState(null); const [error, setError] = useState("");
  useEffect(() => { api.get(`/movies/${id}`).then(r => setMovie(r.data)).catch(() => setError("Movie not found.")); }, [id]);
  if (error) return <main className="container page"><p className="error">{error}</p></main>;
  if (!movie) return <Loader />;
  return <main className="container page details"><div className="details-poster">{movie.thumbnail_url && <img src={mediaUrl(movie.thumbnail_url)} alt={movie.title} />}</div><div><div className="eyebrow">{movie.genre} · {movie.release_year}</div><h1>{movie.title}</h1><p className="lead">{movie.description || "No description available."}</p><p className="muted">{formatDuration(movie.duration_seconds)} · {movie.views} views</p><div className="actions"><Link className="primary" to={`/watch/${movie.id}`}>▶ Watch now</Link><Link className="ghost" to="/movies">Back to movies</Link></div></div></main>;
}

function Watch({ user }) {
  const { id } = useParams(); const [movie, setMovie] = useState(null); const [error, setError] = useState("");
  useEffect(() => { api.get(`/movies/${id}`).then(r => setMovie(r.data)).catch(() => setError("Movie not found.")); api.post(`/movies/${id}/view`).catch(() => {}); }, [id]);
  async function saveProgress(e) {
    if (!user) return;
    const v = e.currentTarget; if (!v.duration || !Number.isFinite(v.duration)) return;
    const progress = Math.min(100, Math.round(v.currentTime / v.duration * 100));
    try { await api.post(`/movies/${id}/progress`, { progress }); } catch { /* user may have an expired session */ }
  }
  if (error) return <main className="container page"><p className="error">{error}</p></main>;
  if (!movie) return <Loader />;
  return <main className="container page watch-page"><div className="video-wrap"><video controls autoPlay playsInline onPause={saveProgress} onEnded={saveProgress} src={mediaUrl(movie.stream_url)} /></div><div className="watch-meta"><div className="eyebrow">{movie.genre} · {movie.release_year}</div><h1>{movie.title}</h1><p className="muted">{movie.description}</p><Link className="ghost" to={`/movies/${movie.id}`}>Movie details</Link>{!user && <p className="muted">Sign in to save your watch progress.</p>}</div></main>;
}

function AuthPage({ mode, onAuth }) {
  const register = mode === "register"; const [name, setName] = useState(""); const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [error, setError] = useState(""); const [busy, setBusy] = useState(false); const navigate = useNavigate();
  async function submit(e) { e.preventDefault(); setError(""); setBusy(true); try { const { data } = await api.post(register ? "/auth/register" : "/auth/login", register ? {name,email,password} : {email,password}); onAuth(data); navigate(data.user?.is_admin ? "/admin" : "/"); } catch (err) { console.error("Authentication failed:", err); setError(getApiErrorMessage(err, "Unable to authenticate. Check your details and backend.")); } finally { setBusy(false); } }
  return <main className="auth"><form className="auth-box" onSubmit={submit}><div className="eyebrow">Welcome to CineVibe</div><h1>{register ? "Create account" : "Sign in"}</h1>{register && <input required minLength="2" placeholder="Your name" value={name} onChange={e=>setName(e.target.value)} />}<input required type="email" placeholder="Email address" value={email} onChange={e=>setEmail(e.target.value)} /><input required minLength={register ? 8 : 1} type="password" placeholder="Password" value={password} onChange={e=>setPassword(e.target.value)} />{error && <div className="error">{String(error)}</div>}<button className={`primary full${register ? " register-submit" : ""}`} disabled={busy}>{busy ? "Please wait…" : register ? "Create account" : "Sign in"}</button><p className="muted center">{register ? "Already have an account?" : "New to CineVibe?"} <Link className="auth-switch-link" to={register ? "/login" : "/register"}>{register ? "Sign in" : "Create account"}</Link></p></form></main>;
}

function History() {
  const [rows, setRows] = useState([]); const [error, setError] = useState("");
  useEffect(() => { api.get("/users/me/history").then(r => setRows(r.data)).catch(e => setError(getApiErrorMessage(e, "Could not load history."))); }, []);
  return <main className="container page"><div className="page-head"><h1>Continue watching</h1></div>{error && <p className="error">{error}</p>}<div className="grid">{rows.map(row => <MovieCard key={row.movie.id} movie={row.movie} progress={row.progress} />)}</div>{!rows.length && !error && <div className="empty">Your watch history will appear here.</div>}</main>;
}

function Admin() {
  const [stats, setStats] = useState(null); const [movies, setMovies] = useState([]); const [message, setMessage] = useState(""); const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  async function load() { try { const [s,m] = await Promise.all([api.get("/admin/stats"), api.get("/admin/movies")]); setStats(s.data); setMovies(m.data); } catch (e) { console.error("Admin data loading failed:", e); setError(getApiErrorMessage(e, "Could not load admin data. Sign in with an administrator account.")); } }
  useEffect(() => { load(); }, []);
  async function upload(e) {
    e.preventDefault();
    const formElement = e.currentTarget;
    const formData = new FormData(formElement);

    setBusy(true);
    setMessage("");
    setError("");

    try {
      // Do not manually set Content-Type: Axios must add the multipart boundary.
      await api.post("/admin/movies", formData);
      formElement.reset();
      setMessage("Movie uploaded successfully.");
      await load();
    } catch (err) {
      console.error("Movie upload failed:", err);
      setError(getApiErrorMessage(err, "Upload failed. Check your admin access, FFmpeg and file format."));
    } finally {
      setBusy(false);
    }
  }
  async function remove(id) { if (!window.confirm("Delete this movie and its media files?")) return; try { await api.delete(`/admin/movies/${id}`); await load(); } catch (e) { setError(e.response?.data?.detail || "Delete failed."); } }
  return <main className="container page"><div className="page-head"><div><div className="eyebrow">Management</div><h1>Admin dashboard</h1></div></div>
    {stats && <div className="stats"><Stat label="Movies" value={stats.movies}/><Stat label="Users" value={stats.users}/><Stat label="Views" value={stats.views}/><Stat label="Genres" value={stats.genres}/></div>}
    <section className="admin-panel"><h2>Upload a movie</h2><form className="upload-form" onSubmit={upload}><div className="form-grid"><input name="title" required placeholder="Movie title"/><input name="genre" required placeholder="Genre"/><input name="release_year" required type="number" min="1888" max="2100" placeholder="Release year"/></div><textarea name="description" placeholder="Movie description"/><label className="file">Video file (MP4, MKV, MOV, AVI, WEBM)<input name="video" required type="file" accept="video/mp4,video/x-matroska,video/webm,video/quicktime,video/x-msvideo"/></label><label className="file">Poster image (optional)<input name="thumbnail_file" type="file" accept="image/jpeg,image/png,image/webp"/></label><button className="primary" disabled={busy}>{busy ? "Uploading and processing…" : "Upload movie"}</button></form>{message && <p className="success">{message}</p>}{error && <p className="error">{error}</p>}</section>
    <section className="admin-panel"><h2>Manage movies</h2><div className="admin-table">{movies.map(m => <div className="admin-row" key={m.id}>{m.thumbnail_url && <img src={mediaUrl(m.thumbnail_url)} alt=""/>}<div><strong>{m.title}</strong><small>{m.genre} · {m.release_year}</small></div><button className="danger small" onClick={()=>remove(m.id)}>Delete</button></div>)}{!movies.length && <p className="muted">No movies uploaded yet.</p>}</div></section>
  </main>;
}

function Stat({label, value}) { return <div className="stat"><small>{label}</small><strong>{Number(value || 0).toLocaleString()}</strong></div>; }
function Loader() { return <div className="loader">Loading…</div>; }
function NotFound() { return <main className="auth"><div className="auth-box center"><h1>404</h1><p>Page not found.</p><Link className="primary" to="/">Go home</Link></div></main>; }
function formatDuration(seconds) { if (!seconds) return "—"; const h=Math.floor(seconds/3600); const m=Math.floor((seconds%3600)/60); const s=seconds%60; return h ? `${h}:${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}` : `${m}:${String(s).padStart(2,"0")}`; }

export default App;
