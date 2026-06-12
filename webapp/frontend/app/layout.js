import "./globals.css";

export const metadata = {
  title: "Meridian — AI Hiring Bias Audit",
  description: "Test models and CVs for demographic bias.",
};

function Nav() {
  return (
    <div className="nav">
      <div style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 500 }}>
        <span style={{ color: "var(--info)" }}>◈</span> Meridian
      </div>
      <div className="links">
        <a href="/test-model">Test a model</a>
        <a href="/test-cv">Test a CV</a>
        <a href="/">Registry</a>
        <a href="/assistant">Assistant</a>
      </div>
    </div>
  );
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div className="wrap">
          <Nav />
          {children}
        </div>
      </body>
    </html>
  );
}
