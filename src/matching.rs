// Copyright 2025 AptS-1547
// Licensed under the Apache License, Version 2.0

//! Wildcard pattern matching utilities.

use glob::Pattern;

/// Match a value against a pattern with wildcard support.
///
/// Supports glob patterns:
/// - `*` matches any number of characters
/// - `?` matches a single character
/// - `[abc]` matches any character in the set
///
/// Matching is case-insensitive.
pub fn match_pattern(value: &str, pattern: &str) -> bool {
    if value.is_empty() || pattern.is_empty() {
        return false;
    }

    let value_lower = value.to_lowercase();
    let pattern_lower = pattern.to_lowercase();

    // "*" matches everything
    if pattern_lower == "*" {
        return true;
    }

    // If pattern contains wildcards, use glob matching
    if pattern_lower.contains('*') || pattern_lower.contains('?') || pattern_lower.contains('[') {
        Pattern::new(&pattern_lower)
            .map(|p| p.matches(&value_lower))
            .unwrap_or(false)
    } else {
        // Exact match (case-insensitive)
        value_lower == pattern_lower
    }
}

/// Check if any pattern in the list matches the value.
pub fn match_any_pattern(value: &str, patterns: &[String]) -> bool {
    patterns.iter().any(|p| match_pattern(value, p))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_exact_match() {
        assert!(match_pattern("user/repo", "user/repo"));
        assert!(match_pattern("User/Repo", "user/repo")); // Case insensitive
        assert!(!match_pattern("user/repo", "other/repo"));
    }

    #[test]
    fn test_wildcard_star() {
        assert!(match_pattern("user/repo", "user/*"));
        assert!(match_pattern("user/anything", "user/*"));
        assert!(!match_pattern("other/repo", "user/*"));
    }

    #[test]
    fn test_star_all() {
        assert!(match_pattern("any-branch", "*"));
        assert!(match_pattern("main", "*"));
        assert!(match_pattern("feature/xyz", "*"));
    }

    #[test]
    fn test_complex_patterns() {
        assert!(match_pattern("user/repo-api", "*/*-api"));
        assert!(match_pattern("org/my-service", "*/*-service"));
        assert!(!match_pattern("user/repo", "*/*-api"));
    }

    #[test]
    fn test_empty_values() {
        assert!(!match_pattern("", "pattern"));
        assert!(!match_pattern("value", ""));
        assert!(!match_pattern("", ""));
    }

    #[test]
    fn test_match_any_pattern() {
        let patterns = vec!["main".to_string(), "feature/*".to_string()];
        assert!(match_any_pattern("main", &patterns));
        assert!(match_any_pattern("feature/xyz", &patterns));
        assert!(!match_any_pattern("develop", &patterns));
    }
}
