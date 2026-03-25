// Copyright 2025 AptS-1547
// Licensed under the Apache License, Version 2.0

//! GitHub webhook handling modules.

pub mod formatter;
pub mod payload;
pub mod webhook;

pub use webhook::{find_matching_webhook, verify_signature};
