# Decision response contract

Every seat returns one JSON object. The initial round is blind: a seat receives
the request and instructions, but no other seat's response. In the revision
round it receives the other responses without vendor labels.

The object contains a non-empty `positions` array. Each position has a stable
`position_id`, `kind` (`part` or `whole`), plain-English `text`, a
`decisive_factor`, a checkable `acceptance` statement, and `depends_on` IDs.

The comparison groups matching IDs and retains every text and reason. Different
conclusions are recorded as contested. Agreement reached through different
reasons is recorded separately from agreement repeating the same reason.
