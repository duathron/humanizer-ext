---
domain: technical
lang: en
notes: Inline-header lists are conventional in technical docs; preserved.
---

## Configuring the retry policy

The `RetryPolicy` struct controls how the client recovers from transient failures.

**Constructor:** `RetryPolicy::new(max_attempts: u32, base_delay: Duration)`

- `max_attempts`: total number of attempts, including the initial call. Setting this to 1 disables retry.
- `base_delay`: delay before the second attempt. Subsequent delays double until `max_delay` is reached.

**Default:** Three attempts, 100 ms base delay, 5 s cap.

You typically pass an instance to `Client::with_retry_policy()` before any request methods are called. The policy is immutable after that — to change retry behavior at runtime, construct a new client.

```rust
let policy = RetryPolicy::new(5, Duration::from_millis(200));
let client = Client::new(api_key).with_retry_policy(policy);
```

If `max_attempts` is 0, `RetryPolicy::new` panics. Use `max_attempts = 1` to disable retry while keeping a valid policy.
