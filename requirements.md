BagelBot Requirements Document

## Project Goal
Automate order placement for Holey Dough bagel drops via HotPlate platform API to secure orders during high-demand, time-limited drops that sell out in <10 seconds.

## R1: API Discovery & Reverse Engineering

### R1.1: Automated Cart Router Endpoint Discovery via JavaScript Bundle Analysis
**Task**: Programmatically reverse engineer the HotPlate cart router by analyzing JavaScript bundles to discover ALL available cart-related TRPC endpoints

- **Input**: HotPlate website URL (https://www.hotplate.com)
- **Method**: Automated JavaScript bundle fetching, parsing, and TRPC router pattern extraction
- **Success Criteria**:
  - **Bundle Discovery & Fetching**: Function fetches main JavaScript bundle(s) from HotPlate website automatically; identifies all webpack/rollup chunks that may contain TRPC router definitions; downloads and caches bundles locally to `cache/js_bundles/` directory; handles minified and obfuscated JavaScript without manual intervention; logs bundle URLs, sizes, and SHA256 hashes for reproducibility
  - **TRPC Router Pattern Recognition**: Identifies TRPC router definition patterns in minified code (e.g., `.router({`, `.procedure(`, `.query(`, `.mutation(`); extracts namespace patterns (e.g., `cart`, `shop`, `checkout`, `order`); detects procedure names within each namespace (e.g., `create`, `addItem`, `get`, `update`, `delete`); uses regex or AST parsing to handle code obfuscation and variable renaming
  - **Cart-Specific Endpoint Extraction**: Filters for cart-related namespaces: `cart`, `shop.cart`, or any namespace containing cart operations; extracts minimum 10 distinct cart-related endpoints (create, add, remove, update, get, clear, etc.); for each endpoint: captures namespace, action name, HTTP method (GET/POST), and parameter structure; identifies input schema patterns (field names, required vs optional, data types)
  - **JSON Output Structure**: Outputs to `docs/discovered_endpoints.json` with schema containing: `discovery_metadata` (timestamp, source_url, bundle_urls, discovery_method), `endpoints` array (namespace, action, full_path, trpc_url, http_method, input_schema, confidence, notes), and `summary` (total_endpoints, cart_endpoints, shop_endpoints, other_endpoints); JSON file is valid (passes `json.loads()` without errors); minimum 10 cart-related endpoints documented in output
  - **Endpoint Validation Integration**: For each discovered endpoint: automatically tests against HotPlate API using `validate_carts()` approach; records validation results in `docs/discovered_endpoints.json` under each endpoint's `validation_result` field; validation includes: status code, response structure, error messages, success boolean; separates confirmed working endpoints from unconfirmed/failed endpoints in output; updates `confidence` level based on validation results (high = 2xx response, low = 4xx/5xx)
  - **Parser Implementation**: Function `discover_cart_endpoints(url: str, use_cache: bool = True) -> dict` exists in new module `endpoint_discovery.py`; supports two parsing strategies: AST-based (using `ast` or `esprima`) OR regex-based patterns; includes fallback: if AST parsing fails, uses regex patterns as backup; handles JavaScript parsing errors gracefully with clear error messages; average execution time <30 seconds for full discovery + validation cycle
  - **Source Map Support** (Optional Enhancement): Detects if source maps are available (`.map` files or inline); if source maps found: extracts unminified variable/function names for better accuracy; logs whether source maps were used in `discovery_metadata.source_maps_available` field; falls back to minified analysis if source maps unavailable
  - **Error Handling & Logging**: Uses `rich.console` for formatted progress output during discovery; logs each stage: bundle fetching, parsing, pattern matching, validation; if no cart endpoints found: raises `ValueError` with message "No cart endpoints discovered in bundles"; if bundle download fails: raises `requests.HTTPError` with status code and URL; creates detailed log file at `logs/endpoint_discovery_{timestamp}.log` with debug information
  - **Documentation Requirements**: New section in `docs/api_endpoints.md` titled "Automated Endpoint Discovery"; documents discovery method, patterns used, confidence levels, and validation approach; includes example command: `python endpoint_discovery.py --validate --output docs/discovered_endpoints.json`; README or CLAUDE.md updated with endpoint discovery as completed Phase 1 task; includes limitations section (e.g., "May miss runtime-generated endpoints")
  - **Dependency Management**: If using AST parsing: adds `esprima` or `js2py` to `requirements.txt`; if using beautifulsoup: leverages existing dependency (no new deps needed); all new dependencies documented in requirements.txt with version pinning; no dependencies that require Node.js/npm (Python-only solution)
  - **CLI Interface**: Supports command-line arguments: `--url`, `--output`, `--validate`, `--no-cache`; `--validate` flag: runs validation tests on discovered endpoints; `--no-cache` flag: forces fresh bundle download (skips cache); `--output` flag: specifies custom output path (default: `docs/discovered_endpoints.json`); help text accessible via `python endpoint_discovery.py --help`
  - **Comparison with Manual Discovery**: Script compares discovered endpoints with those in existing `validate_carts()` function; identifies NEW endpoints not in manual test list (logs count of new discoveries); identifies MISSING endpoints (tested manually but not discovered automatically); output includes `discovery_comparison` section showing overlap analysis
  - **Reproducibility & Caching**: Cached bundles stored with timestamp and hash to detect changes; running discovery twice in a row returns identical results (deterministic); cache invalidation after 24 hours or when bundle hash changes; `--force-refresh` flag bypasses all caches for clean discovery
  - **Integration Test**: Test function `test_endpoint_discovery()` in `endpoint_discovery.py` main block; test validates: bundle download succeeds, parsing extracts >5 endpoints, JSON schema valid, one endpoint validates successfully; test runs in <60 seconds on typical network connection; test prints summary: "Discovered X endpoints, validated Y successfully"
  - **Performance Optimization**: Parallel validation of discovered endpoints (using `concurrent.futures` or `asyncio`); bundle parsing uses streaming/chunked reading for large files (>5MB); regex compilation cached for repeated pattern matching; total execution time <2 minutes for discovery + validation of 20+ endpoints

**Implementation Notes**:
- **Parsing Strategy**: (1) First attempt to fetch source maps if available for unminified code analysis, (2) If source maps unavailable, use regex patterns to find TRPC router definitions, (3) Common patterns to search: `cart:router()` or `cart:{` (namespace declarations), `create:publicProcedure`, `addItem:protectedProcedure` (procedure definitions), `.input(z.object({` (Zod schema definitions)
- **JavaScript Analysis Tools**: Regex-based (fast, simple, works on minified code, may miss complex patterns) vs AST-based with esprima (more accurate, handles obfuscation better, slower, requires valid JavaScript). Recommended: Hybrid approach using regex for initial filtering, AST for detailed extraction
- **Integration**: `validate_carts()` function in polling.py (lines 407-566) becomes validation engine for discovered endpoints; discovered endpoints can populate test cases automatically
- **Why This Approach**: Advantages include completeness (discovers ALL endpoints in bundle, not just those used during manual testing), automation (runs in seconds without human interaction), version detection (automatically detects when HotPlate updates their API via bundle hash changes), auto-documentation, and maintainability (re-run script after HotPlate updates)
- **Limitations to Document**: Only discovers endpoints present in client-side bundles (server-only endpoints missed); may not capture runtime-generated or dynamic endpoints; input schema inference may be incomplete if Zod schemas are complex; confidence levels are heuristic-based, not guaranteed accurate

### R1.2: Cart Creation Endpoint Discovery
**Task**: Identify the correct API endpoint and request format for creating a shopping cart
- **Input**: Active event ID from a live drop window
- **Method**: Chrome DevTools network inspection during manual cart creation
- **Success Criteria**:
  - Endpoint URL documented in `docs/api_endpoints.md` with full path
  - HTTP method (GET/POST) documented
  - All required headers documented with example values
  - Request body structure documented with field names and types
  - Reproducible curl command documented that creates a cart
  - Response status code is 200-299
  - Response contains field `result.data.cartId` (or document actual path)
  - cartId value is non-empty string (document format: UUID/random/other)
  - Same curl command succeeds on 2 consecutive runs (not one-time token)

### R1.3: Add to Cart Endpoint Discovery  
**Task**: Identify API endpoint for adding items with options to cart
- **Input**: Valid cart ID, event menu item ID, quantity, selected options
- **Method**: Network inspection during manual item addition
- **Success Criteria**:
  - Endpoint URL, method, headers documented in `docs/api_endpoints.md`
  - Request body structure documented with all fields (cartId, itemId, quantity, options)
  - Option selection format documented (array/object structure, field names)
  - Reproducible curl command adds 1 item to cart and returns 200-299 status
  - After adding item, calling get_cart(cart_id) shows cart.items length increased by 1
  - Cart response contains added item's event_menu_item_id in items array
  - Test with item containing 2+ option categories (e.g., bagel + schmear) succeeds
  - Selected options appear in cart item's options/selections field

### R1.4: Time Window Selection Discovery
**Task**: Identify how pickup time windows are selected/assigned
- **Method**: Network inspection during time window selection
- **Success Criteria**:
  - Document if time window selection is automatic (assigned at cart creation) or explicit (separate API call)
  - If explicit: endpoint URL, method, headers, request body documented in `docs/api_endpoints.md`
  - If automatic: document which step assigns it (cart creation, first item add, etc.)
  - Time window ID field name and location in request documented
  - Reproducible curl command that assigns/selects time window returns 200-299 status
  - After selection, get_cart(cart_id) response contains timeWindow object
  - timeWindow.id field matches the requested/assigned window ID
  - timeWindow object includes startTime and endTime fields (document format: ISO/epoch)

### R1.5: Checkout Flow Discovery
**Task**: Map complete checkout process from cart to order confirmation
- **Method**: Network inspection during full checkout flow
- **Success Criteria**:
  - All checkout endpoints documented in sequence order in `docs/api_endpoints.md`
  - Each endpoint has URL, method, headers, request/response body documented
  - Customer info field names documented (minimum: name, email, phone)
  - Payment info field structure documented (card/token fields, billing address if required)
  - Authentication requirements documented: cookie names, header tokens, or none required
  - If auth required: document extraction method (browser-cookie3, manual copy, etc.)
  - Order confirmation response documented with order ID field path (e.g., `result.data.orderId`)
  - Confirmation response includes order status field (document possible values)
  - Confirmation response includes order total/subtotal fields
  - Test checkout with dummy/test payment succeeds (or document that live payment is required)

---

## R2: Configuration Management

### R2.1: Order Configuration Schema
**Task**: Create JSON schema for order configuration
- **Output**: `order_config.json` with structure:
  ```json
  {
    "items": [
      {
        "event_menu_item_id": "uuid",
        "quantity": 1,
        "options": [
          {
            "category_id": "uuid",
            "selections": ["option_id_1"]
          }
        ]
      }
    ]
  }
  ```
- **Success Criteria**: 
  - File `order_config.json` exists in project root
  - File is valid JSON (can be parsed without errors)
  - Field names match API request format documented in R1.3
  - Schema includes example item with 0 options (simple item)
  - Schema includes example item with 2+ option categories (complex item)
  - Python script can load file with `json.load()` and access all fields
  - Field types match API requirements (strings for IDs, integers for quantity)

### R2.2: Menu Item ID Extraction
**Task**: Extract and document menu item IDs for standard Holey Dough items
- **Input**: Output from `get_all_menu_items()` for a recent event
- **Output**: Document mapping of human-readable item names to UUIDs
- **Items to capture**: All bagel varieties, schmears, coffee options
- **Success Criteria**: 
  - File `docs/menu_items.md` or `menu_items.json` created
  - Minimum 5 bagel items documented with IDs
  - Minimum 3 schmear/spread items documented with IDs
  - Each entry includes: item title, event_menu_item_id, price, section name
  - For items with options: document option category IDs and choice IDs
  - IDs follow UUID format (8-4-4-4-12 hex pattern) or document actual format
  - Sample menu item ID can be used in get_event API call without 404 error
  - Document includes event_id that these IDs are valid for

### R2.3: Environment Configuration
**Task**: Define `.env` structure for sensitive data
- **Required fields**:
  - Customer info: `CUSTOMER_NAME`, `CUSTOMER_EMAIL`, `CUSTOMER_PHONE`
  - Payment info: Structure TBD based on R1.5 findings
  - Authentication: Cookies/tokens TBD based on R1.5 findings
- **Success Criteria**: 
  - File `.env.example` exists in project root
  - All customer info fields present with placeholder values
  - All payment fields from R1.4 present with placeholder values
  - All auth fields from R1.4 present with placeholder values
  - Each field has inline comment explaining its purpose
  - File can be loaded with `python-dotenv` without errors
  - No actual credentials present in `.env.example` (only placeholders)
  - `.env` file in .gitignore

---

## R3: Core Bot Functions

### R3.1: Cart Creation Function
**Task**: Implement `create_cart(event_id: str) -> str`
- **Input**: Event ID for active drop
- **Output**: Cart ID string
- **Success Criteria**:
  - Function exists in `polling.py` or new `cart.py` module
  - Returns string type (not dict, not None)
  - Return value is non-empty
  - With valid event_id: function completes without raising exception
  - With invalid event_id: raises `ValueError` or `requests.HTTPError`
  - Exception message includes error type (e.g., "Event not found" or "Invalid event ID")
  - Function includes type hints for parameters and return value
  - Average execution time <200ms over 5 runs (measured with `time.time()`)
  - Return value can be used successfully in subsequent `get_cart()` call

### R3.2: Add Items to Cart Function
**Task**: Implement `add_items_to_cart(cart_id: str, items: list[dict]) -> bool`
- **Input**: Cart ID and items list from order config
- **Output**: Success boolean
- **Success Criteria**:
  - Function exists with correct signature and type hints
  - With valid cart_id and items: returns True
  - With invalid cart_id: raises `ValueError` with message containing "cart"
  - With invalid item structure: raises `ValueError` with message containing "item"
  - After successful call with N items: `get_cart(cart_id)['items']` has length N
  - Each returned cart item's `event_menu_item_id` matches an input item's ID
  - Test with item containing 0 options: succeeds
  - Test with item containing 2 option categories: succeeds and options appear in cart
  - Average execution time <500ms for 5 items over 3 runs
  - Function handles partial failures: if item 3/5 fails, raises exception with details

### R3.3: Time Window Selection Function
**Task**: Implement `select_time_window(cart_id: str, time_window_id: str) -> bool`
- **Input**: Cart ID and preferred time window ID
- **Output**: Success boolean
- **Success Criteria**:
  - Function exists with correct signature and type hints
  - With valid cart_id and window_id: returns True
  - With invalid cart_id: raises `ValueError` with message containing "cart"
  - With full/unavailable window: raises `ValueError` with message containing "full" or "unavailable"
  - After successful call: `get_cart(cart_id)['timeWindow']['id']` equals input time_window_id
  - After successful call: cart response includes timeWindow.startTime and timeWindow.endTime
  - Average execution time <200ms over 5 runs
  - Function works regardless of whether time window selection happened earlier (idempotent)

### R3.4: Checkout Function
**Task**: Implement `checkout(cart_id: str) -> dict`
- **Input**: Cart ID with items and time window assigned
- **Output**: Order confirmation details dict
- **Success Criteria**:
  - Function exists with correct signature and type hints
  - Return value is dict type
  - Return dict contains key 'order_id' with non-empty string value
  - Return dict contains key 'status' (document expected value: "confirmed", "pending", etc.)
  - With valid cart: function completes without raising exception
  - With empty cart: raises `ValueError` with message containing "empty" or "no items"
  - With cart missing time window: raises `ValueError` with message containing "time window"
  - Function reads CUSTOMER_NAME, CUSTOMER_EMAIL, CUSTOMER_PHONE from environment
  - Function reads payment fields from environment (based on R1.5 findings)
  - HTTP response status code is 200-299
  - Average execution time <1000ms over 3 runs
  - After successful checkout, original cart_id becomes invalid (returns 404 or "not found")

---

## R4: Event Monitoring

### R4.1: Upcoming Events Endpoint Discovery
**Task**: Identify API endpoint for fetching upcoming (not past) events
- **Method**: Network inspection on HotPlate homepage or shop page
- **Success Criteria**:
  - Endpoint URL, method, headers documented in `docs/api_endpoints.md`
  - Request parameters documented (chefId, date filters, etc.)
  - Response structure documented with field paths
  - Sample curl command included that returns upcoming events
  - Response includes events where goLiveTime > current time (milliseconds since epoch)
  - Response distinguishes between upcoming and live events (document status field if exists)
  - Test endpoint 3 times with 5-second gaps: does not return rate limit error (429)
  - Endpoint returns same event consistently when polled (stable results)

### R4.2: Monitor for New Events Function
**Task**: Implement `monitor_for_new_events(chef_id: str) -> dict`
- **Input**: Chef ID (hardcoded "holeydoughandco")
- **Output**: Dict with next upcoming event details
- **Success Criteria**:
  - Function exists with correct signature and type hints
  - Return dict contains keys: 'event_id', 'go_live_time', 'title'
  - go_live_time is integer (milliseconds since epoch)
  - go_live_time is > current time when function returns
  - Function includes configurable poll_interval parameter (default 5 seconds)
  - Function logs each poll attempt with timestamp
  - Function caches last result and only returns when event changes (different event_id)
  - If endpoint returns empty/no events: function sleeps and retries (does not crash)
  - Test: function detects new event within 10 seconds of it being published (if testable)

### R4.3: Wait Until Go Live Function
**Task**: Implement `wait_until_go_live(event_id: str, go_live_time: int)`
- **Input**: Event ID and go-live timestamp (milliseconds)
- **Output**: None (blocks until go-live time)
- **Success Criteria**:
  - Function exists with correct signature and type hints
  - Function blocks (does not return early) until 100ms before go_live_time
  - Returns within 200ms window around go_live_time (Â±100ms precision)
  - Logs countdown message every 10 seconds while waiting
  - Countdown shows time remaining in human-readable format (e.g., "5m 23s")
  - If go_live_time is in past: function returns immediately (does not sleep)
  - Test with go_live_time 30 seconds in future: function waits approximately 30s
  - Function is interruptible with Ctrl+C (raises KeyboardInterrupt, not hanging)

---

## R5: Main Orchestration

### R5.1: Bot Execution Flow
**Task**: Implement `main()` orchestration function
- **Flow**:
  1. Load order config from `order_config.json`
  2. Load credentials from `.env`
  3. Monitor for next upcoming event
  4. Display event details and wait for user confirmation
  5. Wait until go-live time
  6. Execute order sequence: create cart â add items â select time â checkout
  7. Log order confirmation or failure
- **Success Criteria**:
  - Function completes steps 1-7 without crashing when configs are valid
  - Total time from go-live trigger to checkout complete is <3 seconds (steps 6-7)
  - Each major step logs message with format: `[TIMESTAMP] STEP_NAME: status`
  - Missing order_config.json raises FileNotFoundError with clear message
  - Missing .env values raise ValueError with missing field name in message
  - Successful checkout prints order ID to console
  - Successful checkout creates file `orders/{order_id}_{timestamp}.json`
  - Failed checkout logs error message with step name and reason
  - User confirmation prompt (step 4) accepts 'y' or 'yes' to continue
  - Ctrl+C during wait phase (step 5) exits gracefully with message

### R5.2: Error Handling & Retry Logic
**Task**: Add retry logic for transient failures
- **Scope**: Cart creation, add to cart, checkout endpoints
- **Strategy**: Exponential backoff with max 3 retries
- **Success Criteria**:
  - On 5xx error: function retries automatically (does not raise immediately)
  - On timeout (requests.Timeout): function retries automatically
  - On 4xx error: function raises exception immediately (no retries)
  - First retry waits 0.5s, second waits 1s, third waits 2s (exponential backoff)
  - After 3 failed attempts: raises exception with message including "max retries exceeded"
  - Each retry logs attempt number and reason (e.g., "Retry 2/3: 503 error")
  - Total time for 3 retries is <5 seconds (measured from first attempt to final failure)
  - Successful retry stops further attempts (does not retry unnecessarily)
  - Test: mock function returning [500, 500, 200] succeeds on 3rd attempt

---

## R6: Validation & Testing

### R6.1: Dry Run Mode
**Task**: Implement dry run mode that simulates order without checkout
- **Flag**: `--dry-run` command line argument
- **Behavior**: Execute all steps except `checkout()`
- **Success Criteria**:
  - Running `python main.py --dry-run` executes without error
  - Dry run creates real cart via API (not mocked)
  - Dry run adds all items from order_config.json to cart
  - Dry run selects time window
  - Dry run prints cart contents: item names, quantities, options
  - Dry run prints cart total cost (if available in cart response)
  - Dry run prints checkout URL: `https://www.hotplate.com/checkout/{cart_id}`
  - Dry run does NOT call checkout endpoint (verify with network logs)
  - Dry run calls delete/cleanup endpoint to remove cart after display
  - After dry run: verify cart_id is no longer valid (404 on get_cart)

### R6.2: Success Verification
**Task**: Implement order confirmation verification
- **Method**: Parse checkout response for order ID
- **Secondary check**: Monitor email for confirmation (manual step)
- **Success Criteria**:
  - Order ID logged to console immediately after checkout (within 100ms)
  - Log message format: `ORDER CONFIRMED: {order_id}`
  - File created at `orders/{order_id}_{timestamp}.json` with full checkout response
  - JSON file includes: order_id, status, items, total, customer_email, timestamp
  - JSON file is valid (can be parsed without errors)
  - Console prints summary: "Order {order_id} confirmed for {customer_email}"
  - Console prints expected time window: "Pickup: {start_time} - {end_time}"
  - Documentation includes steps to verify email confirmation (manual checklist)

---

## Implementation Order

1. **Phase 1: Discovery** (R1) - Manual exploration, document findings
2. **Phase 2: Configuration** (R2) - Set up config files and schemas
3. **Phase 3: Core Functions** (R3) - Implement API wrappers
4. **Phase 4: Monitoring** (R4) - Build event detection
5. **Phase 5: Integration** (R5) - Wire everything together
6. **Phase 6: Testing** (R6) - Validate with dry runs

## Success Metrics

- **Speed**: Complete order in <3 seconds from go-live time
- **Reliability**: Successfully place order in 95%+ of attempts
- **Validation**: Order confirmation email received within 2 minutes

---

## Technical Notes

### API Architecture
- **Base URL**: `https://bets.hotplate.com/trpc/`
- **Pattern**: `namespace.action` (e.g., `shop.getEvent`)
- **Request Format**: GET with JSON-encoded `input` parameter
- **Response Format**: `{"result": {"data": {...}}}`

### Current Codebase Status
- â Event history retrieval
- â Menu item fetching with full details
- â Cart endpoint validation framework
- ð§ Cart creation (endpoint unknown)
- â³ Add to cart, checkout, monitoring (not started)

### Dependencies
```
requests - HTTP client
pyyaml - Config file parsing
browser-cookie3 - Cookie extraction for auth
python-dotenv - Environment variable management
rich - Terminal output formatting
beautifulsoup4 - HTML parsing if needed
```
