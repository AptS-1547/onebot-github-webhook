// Copyright 2025 AptS-1547
// Licensed under the Apache License, Version 2.0

//! OneBot message segment types.

use serde::{Deserialize, Serialize};

/// A single message segment in OneBot format.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", content = "data")]
#[serde(rename_all = "snake_case")]
pub enum MessageSegment {
    /// Text message segment
    Text { text: String },

    /// Image message segment
    Image { file: String },

    /// At mention segment
    At { qq: String },

    /// Face/emoji segment
    Face { id: String },
}

impl MessageSegment {
    ///Create a text message segment.
    pub fn text(content: impl Into<String>) -> Self {
        MessageSegment::Text {
            text: content.into(),
        }
    }

    /// Create an image message segment.
    pub fn image(file: impl Into<String>) -> Self {
        MessageSegment::Image { file: file.into() }
    }

    /// Create an at mention segment.
    pub fn at(qq: impl Into<String>) -> Self {
        MessageSegment::At { qq: qq.into() }
    }
}

/// A complete message consisting of one or more segments.
pub type Message = Vec<MessageSegment>;

/// Convert a Message to a plain text string (for non-OneBot targets).
pub fn message_to_plain_text(message: &Message) -> String {
    message
        .iter()
        .filter_map(|seg| match seg {
            MessageSegment::Text { text } => Some(text.as_str()),
            _ => None,
        })
        .collect()
}

/// Helper to build messages
pub struct MessageBuilder {
    segments: Vec<MessageSegment>,
}

impl MessageBuilder {
    pub fn new() -> Self {
        Self { segments: vec![] }
    }

    pub fn text(mut self, content: impl Into<String>) -> Self {
        self.segments.push(MessageSegment::text(content));
        self
    }

    pub fn image(mut self, file: impl Into<String>) -> Self {
        self.segments.push(MessageSegment::image(file));
        self
    }

    pub fn at(mut self, qq: impl Into<String>) -> Self {
        self.segments.push(MessageSegment::at(qq));
        self
    }

    pub fn build(self) -> Message {
        self.segments
    }
}

impl Default for MessageBuilder {
    fn default() -> Self {
        Self::new()
    }
}
