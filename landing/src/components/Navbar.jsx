import { useState, useEffect } from "react";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 100);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const links = [
    { label: "In\u00edcio", href: "#hero" },
    { label: "Ranking", href: "#ranking" },
    { label: "Sa\u00fade", href: "#saude" },
    { label: "Forecast", href: "#forecast" },
    { label: "Sobre", href: "#sobre" },
  ];

  return (
    <nav className={`navbar${scrolled ? " scrolled" : ""}`}>
      <div className="nav-inner">
        <a href="#hero" className="nav-brand">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-light)" strokeWidth="2" style={{marginRight:6}}>
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
          BR Stocks
        </a>
        <button
          className={`nav-toggle${menuOpen ? " active" : ""}`}
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label={menuOpen ? "Fechar menu" : "Abrir menu"}
          aria-expanded={menuOpen}
        >
          <span /><span /><span />
        </button>
        <ul className={`nav-links${menuOpen ? " open" : ""}`}>
          {links.map((l) => (
            <li key={l.href}>
              <a href={l.href} onClick={() => setMenuOpen(false)}>
                {l.label}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}
