// Copyright 2025 AptS-1547
// Licensed under the Apache License, Version 2.0

//! OneBot client implementations.

pub mod client;
pub mod http;
pub mod websocket;

pub use client::{create_client, OneBotClient};
pub use http::OneBotHttpClient;
pub use websocket::OneBotWebSocketClient;
