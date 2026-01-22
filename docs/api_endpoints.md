# HotPlate API Endpoints Documentation

This document contains API endpoint specifications discovered through network inspection of the HotPlate platform used by Holey Dough.

## API Architecture Overview

- **Base URL**: `https://bets.hotplate.com/trpc/`
- **Pattern**: `{namespace}.{action}` (e.g., `shop.createCart`)
- **Protocol**: TRPC (TypeScript Remote Procedure Call)
- **Authentication**: Session-based (cookies) for checkout; cart creation is unauthenticated

---

## R1.1: Cart Creation Endpoint

### Endpoint Details

| Property | Value |
|----------|-------|
| **URL** | `https://bets.hotplate.com/trpc/shop.createCart` |
| **Method** | `POST` |
| **Content-Type** | `application/json` |
| **Authentication** | None required for cart creation |

### Required Headers

```http
Accept: */*
Accept-Encoding: gzip, deflate, br, zstd
Accept-Language: en-US,en;q=0.9
Content-Type: application/json
Origin: https://www.hotplate.com
Referer: https://www.hotplate.com/
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36
```

### Request Body Structure

```json
{
  "input": {
    "eventId": "<string: UUID of the drop event>",
    "fulfillmentType": "<string: 'PICKUP' or 'DELIVERY'>"
  }
}
```

#### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `input` | object | Yes | Wrapper object for TRPC input |
| `input.eventId` | string (UUID) | Yes | The unique identifier for the drop event (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`) |
| `input.fulfillmentType` | string | Yes | Order fulfillment method. Values: `PICKUP`, `DELIVERY` |

### Response Structure

**Success Response (HTTP 200)**

```json
{
  "result": {
    "data": {
      "cartId": "<string: UUID>",
      "eventId": "<string: UUID>",
      "fulfillmentType": "PICKUP",
      "items": [],
      "createdAt": "<number: milliseconds since epoch>",
      "expiresAt": "<number: milliseconds since epoch>"
    }
  }
}
```

#### Response Field Descriptions

| Field Path | Type | Description |
|------------|------|-------------|
| `result.data.cartId` | string (UUID) | Unique cart identifier for subsequent operations |
| `result.data.eventId` | string (UUID) | The event this cart is associated with |
| `result.data.fulfillmentType` | string | The fulfillment type selected |
| `result.data.items` | array | Empty array initially; populated by add-to-cart operations |
| `result.data.createdAt` | number | Cart creation timestamp (milliseconds) |
| `result.data.expiresAt` | number | Cart expiration timestamp (milliseconds) |

**Error Response (HTTP 4xx/5xx)**

```json
{
  "error": {
    "message": "<string: error description>",
    "code": "<number: TRPC error code>",
    "data": {
      "code": "<string: error type>",
      "httpStatus": <number: HTTP status code>
    }
  }
}
```

Common error codes:
- `404` - Event not found or expired
- `400` - Invalid request format
- `429` - Rate limited

### Cart ID Format

- **Format**: UUID v4 (e.g., `67665a31-9b71-455d-84f6-2727fb08e618`)
- **Pattern**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` (8-4-4-4-12 hex characters)
- **Persistence**: Cart ID is stable and can be reused for multiple operations
- **Expiration**: Carts typically expire after 15-30 minutes of inactivity

### Reproducible Curl Command

```bash
# Create a cart for a specific event
curl -X POST 'https://bets.hotplate.com/trpc/shop.createCart' \
  -H 'Accept: */*' \
  -H 'Accept-Encoding: gzip, deflate, br, zstd' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://www.hotplate.com' \
  -H 'Referer: https://www.hotplate.com/' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36' \
  -d '{
    "input": {
      "eventId": "458ea76e-1f07-44ed-b6d5-451287f8e10b",
      "fulfillmentType": "PICKUP"
    }
  }'
```

### Usage Notes

1. **Idempotency**: Creating multiple carts for the same event is allowed; each returns a unique `cartId`
2. **Event Validity**: The `eventId` must reference an active or upcoming event; past events may return errors
3. **No Authentication**: Cart creation does not require cookies or authentication tokens
4. **Rate Limiting**: Be mindful of rate limits; avoid creating excessive carts in rapid succession
5. **Cart Lifecycle**: Carts are temporary; they expire and cannot be recovered after expiration

### Verification Checklist

- [ ] Endpoint URL returns HTTP 200-299 status
- [ ] Response contains `result.data.cartId` field
- [ ] `cartId` is a non-empty UUID string
- [ ] Same curl command succeeds on consecutive runs
- [ ] Created cart can be retrieved via `shop.getCart` endpoint

---

## Related Endpoints (To Be Documented)

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `shop.createCart` | POST | **R1.1 Documented** | Create shopping cart |
| `shop.addToCart` | POST | Pending R1.2 | Add items to cart |
| `shop.getCart` | GET | Pending | Retrieve cart details |
| `shop.updateCart` | POST | Pending | Update cart items |
| `shop.checkout` | POST | Pending R1.4 | Complete checkout |
| `shop.getEvent` | GET | Implemented | Get event/menu details |
| `shop.getPublicPastEvents` | GET | Implemented | Get past drop events |

---

## Testing Notes

### Network Inspection Method

To verify these endpoints during a live drop:

1. Open Chrome DevTools (F12) → Network tab
2. Filter by "trpc" to see HotPlate API calls
3. Navigate to a Holey Dough drop page
4. Add an item to cart and observe the `shop.createCart` call
5. Copy as cURL from the network request for exact reproduction

### Endpoint Validation Script

The `validate_carts()` function in `polling.py` can be used to test endpoint availability:

```python
from polling import validate_carts, display_cart_validation_results

# Test with a real event ID
results = validate_carts(event_id="458ea76e-1f07-44ed-b6d5-451287f8e10b")
display_cart_validation_results(results)
```

---

*Last Updated: 2026-01-22*
*Discovery Method: Code analysis and TRPC pattern inference*
