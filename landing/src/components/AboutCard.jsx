import logo from "../assets/logo.png";

const TECH = ["py", "lm", "streamlit", "folium", "pytorch", "opencv"];

const LINKS = [
  {
    label: "GitHub",
    href: "https://github.com/cavalcanteprofissional",
    svg: (
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.387.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.73.083-.73 1.205.085 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 21.795 24 17.295 24 12 24 5.37 18.63 0 12 0z" />
    ),
  },
  {
    label: "Portfólio",
    href: "https://cavalcanteprofissional.github.io/portfolio/",
    svg: (
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
    ),
  },
  {
    label: "LinkedIn",
    href: "https://linkedin.com/in/cavalcante-Lucas",
    svg: (
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    ),
  },
  {
    label: "Email",
    href: "mailto:cavalcanteprofissional@outlook.com",
    svg: (
      <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z" />
    ),
  },
];

export default function AboutCard() {
  return (
    <div className="about-card">
      <div className="about-card-inner">
        <div className="about-top">
          <img
            className="about-avatar"
            src="https://avatars.githubusercontent.com/u/133777385?v=4"
            alt="Lucas Cavalcante"
            width={64}
            height={64}
          />
          <div className="about-info">
            <h3 className="about-name">Lucas Cavalcante dos Santos</h3>
            <p className="about-bio">dev dados com py, lm, streamlit, folium, pytorch, opencv</p>
            <span className="about-location">Fortaleza, Cear&aacute;</span>
          </div>
        </div>

        <div className="about-links">
          {LINKS.map((link) => (
            <a
              key={link.label}
              href={link.href}
              target="_blank"
              rel="noopener noreferrer"
              className="about-link"
              title={link.label}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                {link.svg}
              </svg>
              {link.label}
            </a>
          ))}
        </div>

        <div className="about-tech-tags">
          {TECH.map((t) => (
            <span key={t} className="tech-tag">{t}</span>
          ))}
        </div>

        <div className="about-stats">
          38 reposit&oacute;rios &middot; 4 seguidores &middot; 18 following
        </div>

        <img src={logo} alt="assinatura" className="about-badge" />
      </div>
    </div>
  );
}
