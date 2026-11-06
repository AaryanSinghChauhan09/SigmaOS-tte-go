//! SigmaOS-tte-go — terminal text effects (Omarchy `ttfx` parity).
//!
//! Pure functions that wrap text in ANSI escape sequences: rainbow
//! gradient, glow/blur illusion, matrix-style frames, and banners.
//! No external crates, no unsafe, deterministic output.

/// ANSI true-color / 256-color helpers. All sequences are emitted as
/// `\x1b[...m` SGR codes terminated by reset `\x1b[0m`.
pub struct TerminalEffects;

const RAINBOW: [u8; 7] = [196, 202, 208, 214, 220, 226, 190]; // red->violet 256-palette

impl TerminalEffects {
    /// Wrap text in a single SGR style.
    fn sgr(text: &str, code: &str) -> String {
        format!("\x1b[{code}m{text}\x1b[0m")
    }

    /// Rainbow: each character cycles through a 7-color gradient.
    pub fn colorize_rainbow(text: &str) -> String {
        let mut out = String::new();
        for (i, ch) in text.chars().enumerate() {
            let color = RAINBOW[i % RAINBOW.len()];
            out.push_str(&format!("\x1b[38;5;{color}m{ch}"));
        }
        out.push_str("\x1b[0m");
        out
    }

    /// Bold + bright-white "glow" approximation (terminals without blur).
    pub fn glow(text: &str) -> String {
        Self::sgr(text, "1;97")
    }

    /// Dim/secondary text.
    pub fn dim(text: &str) -> String {
        Self::sgr(text, "2")
    }

    /// Underline.
    pub fn underline(text: &str) -> String {
        Self::sgr(text, "4")
    }

    /// Inverse video.
    pub fn inverse(text: &str) -> String {
        Self::sgr(text, "7")
    }

    /// Matrix-style banner: text inside a box of `#` with a scanline row.
    pub fn banner(text: &str) -> String {
        let width = text.chars().count() + 4;
        let mut out = String::new();
        out.push_str(&"#".repeat(width));
        out.push('\n');
        out.push_str(&format!("# {:^width$} #\n", text, width = width - 4));
        out.push_str(&"#".repeat(width));
        out
    }

    /// Legacy helper kept for compatibility.
    pub fn colorize(text: &str) -> String {
        Self::sgr(text, "35")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_terminal_effects_aaa() {
        let banner = TerminalEffects::banner("SigmaOS");
        assert!(banner.contains("SigmaOS"));
        assert!(banner.contains('#'));
    }

    #[test]
    fn rainbow_emits_per_char_colors() {
        let out = TerminalEffects::colorize_rainbow("AB");
        // two colored chars + reset
        assert!(out.contains("\x1b[38;5;196mA"));
        assert!(out.contains("\x1b[38;5;202mB"));
        assert!(out.ends_with("\x1b[0m"));
    }

    #[test]
    fn styles_wrap_and_reset() {
        let g = TerminalEffects::glow("hi");
        assert!(g.starts_with("\x1b[1;97m"));
        assert!(g.ends_with("\x1b[0m"));
        assert!(TerminalEffects::dim("x").contains("\x1b[2m"));
        assert!(TerminalEffects::inverse("x").contains("\x1b[7m"));
    }

    #[test]
    fn banner_width_matches_text() {
        let b = TerminalEffects::banner("hi");
        let top = b.lines().next().unwrap();
        assert_eq!(top.chars().count(), "hi".len() + 4);
    }
}
