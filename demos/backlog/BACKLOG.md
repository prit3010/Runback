# Backlog

Tickets labelled `auto-fix` are safe for autonomous resolution. For each ticket:

1. Read the referenced file and the corresponding test.
2. Make the test pass without breaking the baseline suite.
3. Run `npm test` and confirm green.
4. Create a branch named `fix/issue-N`, where N is the ticket number.
5. Commit with message `fix: <ticket title>`.
6. Push the branch and open a pull request via `gh pr create`.

Stop and ask in chat before posting any external comments outside `gh pr create`.

## Ticket #1: Pagination drops items on the last page

- **Label:** auto-fix
- **File:** `src/pagination.js`
- **Failing test:** `tests/pagination.test.js`
- **Reproduction:** `paginate(['a','b','c','d','e','f','g'], 3, 3)` returns `[]` but should return `['g']`.
- **Acceptance:** `npm test -- tests/pagination.test.js` passes.

## Ticket #2: Inventory sort is alphabetic, not numeric

- **Label:** auto-fix
- **File:** `src/inventory.js`
- **Failing test:** `tests/inventory.test.js`
- **Reproduction:** `sortInventory(['SKU-10','SKU-2','SKU-100','SKU-1'])` returns lexicographic order instead of numeric order.
- **Acceptance:** `npm test -- tests/inventory.test.js` passes.

## Ticket #3: Fetcher returns a Promise instead of the value

- **Label:** auto-fix
- **File:** `src/fetcher.js`
- **Failing test:** `tests/fetcher.test.js`
- **Reproduction:** `await fetcher('alpha')` returns `undefined` because `result.value` is read off a Promise object.
- **Acceptance:** `npm test -- tests/fetcher.test.js` passes.

## Ticket #4: Email validation rejects valid addresses

- **Label:** auto-fix
- **File:** `src/email.js`
- **Failing test:** `tests/email.test.js`
- **Reproduction:** Some valid addresses fail validation. Customers in support are reporting they cannot register, but the team has not narrowed it down yet. The regex is suspect.
- **Acceptance:** `npm test -- tests/email.test.js` passes.

## Ticket #5: Log level fallback is wrong

- **Label:** auto-fix
- **File:** `src/config.js`
- **Failing test:** `tests/config.test.js`
- **Reproduction:** When `LOG_LEVEL` is unset, `getLogLevel({})` returns `'LOG_LEVEL'` instead of the documented default `'info'`.
- **Acceptance:** `npm test -- tests/config.test.js` passes.
