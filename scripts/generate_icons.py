"""Generate PNG and SVG icons for the Chrome extension."""
import math
from pathlib import Path

# Create SVG icon
svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">
  <defs>
    <linearGradient id="shieldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00f2fe" />
      <stop offset="50%" stop-color="#4facfe" />
      <stop offset="100%" stop-color="#000824" />
    </linearGradient>
    <linearGradient id="coreGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00f2fe" />
      <stop offset="100%" stop-color="#6b11ff" />
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="6" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>
  <!-- Shield Base -->
  <path d="M 64 8 C 96 8 116 22 116 48 C 116 88 64 120 64 120 C 64 120 12 88 12 48 C 12 22 32 8 64 8 Z" 
        fill="url(#shieldGrad)" stroke="#00f2fe" stroke-width="3" filter="url(#glow)"/>
  <!-- Inner Shield Glow -->
  <path d="M 64 20 C 88 20 102 30 102 50 C 102 82 64 108 64 108 C 64 108 26 82 26 50 C 26 30 40 20 64 20 Z" 
        fill="#0a1026" fill-opacity="0.85" stroke="#38bdf8" stroke-width="1.5"/>
  <!-- AI / Crypto Pulse Core -->
  <circle cx="64" cy="58" r="18" fill="url(#coreGrad)" filter="url(#glow)" opacity="0.9"/>
  <!-- Circuit Nodes & Center Lock -->
  <path d="M 64 46 L 64 70 M 52 58 L 76 58 M 55 49 L 73 67 M 55 67 L 73 49" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
  <circle cx="64" cy="58" r="6" fill="#ffffff"/>
  <!-- Warning / Pulse Orbit -->
  <path d="M 44 58 A 20 20 0 0 1 84 58" fill="none" stroke="#00f2fe" stroke-width="2" stroke-dasharray="3,3"/>
</svg>"""

out_dir = Path("extension/icons")
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "icon.svg").write_text(svg_content)
print("Saved SVG icon")
