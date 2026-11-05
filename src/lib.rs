pub struct TerminalEffects;

impl TerminalEffects {
    pub fn colorize_rainbow(text: &str) -> String {
        format!("[35m{}[0m", text)
    }
    pub fn banner(text: &str) -> String {
        format!("=== {} ===", text)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_terminal_effects_aaa() {
        // Arrange
        let input = "SigmaOS";
        // Act
        let banner = TerminalEffects::banner(input);
        // Assert
        assert_eq!(banner, "=== SigmaOS ===");
    }
}
