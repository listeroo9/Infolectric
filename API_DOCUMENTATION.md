# Infolectric API Documentation

## Base URL
```
http://localhost:8000/api/
```

## Authentication
The API uses Django's session authentication. For production deployments with token authentication, see the [DRF documentation](https://www.django-rest-framework.org/api-guide/authentication/).

## Response Format
All API responses are in JSON format.

### Success Response (200 OK)
```json
{
  "id": 1,
  "name": "Component Name",
  "description": "Description",
  ...
}
```

### Error Response (4xx/5xx)
```json
{
  "error": "Error message",
  "detail": "Additional details if applicable"
}
```

---

## Endpoints

### Components API

#### List Components
**GET** `/api/components/`

Query Parameters:
- `search` - Search by name or description
- `category` - Filter by category ID
- `page` - Page number (default: 1)
- `ordering` - Order by field (`name`, `date_created`, `-date_created`)

Example:
```bash
curl "http://localhost:8000/api/components/?search=resistor&page=1"
```

Response:
```json
{
  "count": 10,
  "next": "http://localhost:8000/api/components/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Carbon Film Resistor 10kΩ",
      "description": "Standard carbon film resistor...",
      "category": 1,
      "category_name": "Resistors",
      "image": null,
      "image_url": null,
      "date_created": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

#### Get Component
**GET** `/api/components/{id}/`

Example:
```bash
curl "http://localhost:8000/api/components/1/"
```

Response:
```json
{
  "id": 1,
  "name": "Carbon Film Resistor 10kΩ",
  "description": "Standard carbon film resistor with 10 kilohm resistance...",
  "category": 1,
  "category_name": "Resistors",
  "image": "/media/component_images/resistor.jpg",
  "image_url": "http://localhost:8000/media/component_images/resistor.jpg",
  "date_created": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

#### Create Component
**POST** `/api/components/`

Authentication: Required (admin)

Request:
```json
{
  "name": "New Resistor",
  "description": "A new resistor component",
  "category": 1
}
```

Response: (201 Created)
```json
{
  "id": 11,
  "name": "New Resistor",
  "description": "A new resistor component",
  "category": 1,
  "category_name": "Resistors",
  "image": null,
  "image_url": null,
  "date_created": "2024-01-15T12:00:00Z",
  "updated_at": "2024-01-15T12:00:00Z"
}
```

#### Update Component
**PUT** `/api/components/{id}/`

Authentication: Required (admin)

Request:
```json
{
  "name": "Updated Resistor",
  "description": "Updated description",
  "category": 1
}
```

Response: (200 OK)
```json
{
  "id": 1,
  "name": "Updated Resistor",
  ...
}
```

#### Delete Component
**DELETE** `/api/components/{id}/`

Authentication: Required (admin)

Response: (204 No Content)

#### Filter by Category
**GET** `/api/components/by_category/?category_id={id}`

Example:
```bash
curl "http://localhost:8000/api/components/by_category/?category_id=1"
```

---

### Categories API

#### List Categories
**GET** `/api/categories/`

Query Parameters:
- `search` - Search by name or description
- `ordering` - Order by field (`name`, `created_at`)
- `page` - Page number

Example:
```bash
curl "http://localhost:8000/api/categories/"
```

Response:
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Resistors",
      "description": "Passive components that resist electric current flow",
      "components_count": 3,
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

#### Get Category
**GET** `/api/categories/{id}/`

Example:
```bash
curl "http://localhost:8000/api/categories/1/"
```

#### Get Category's Components
**GET** `/api/categories/{id}/components/`

Example:
```bash
curl "http://localhost:8000/api/categories/1/components/"
```

Response:
```json
[
  {
    "id": 1,
    "name": "Carbon Film Resistor 10kΩ",
    "description": "Standard carbon film resistor...",
    ...
  }
]
```

#### Create Category
**POST** `/api/categories/`

Authentication: Required (admin)

Request:
```json
{
  "name": "New Category",
  "description": "Category description"
}
```

#### Update Category
**PUT** `/api/categories/{id}/`

Authentication: Required (admin)

#### Delete Category
**DELETE** `/api/categories/{id}/`

Authentication: Required (admin)

---

### Wire Sizes API

#### List Wire Sizes
**GET** `/api/wire-sizes/`

Query Parameters:
- `ordering` - Order by field (`wire_size_mm2`, `max_ampacity`)
- `page` - Page number

Example:
```bash
curl "http://localhost:8000/api/wire-sizes/"
```

Response:
```json
{
  "count": 14,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "wire_size_mm2": "0.75",
      "max_ampacity": 6,
      "description": "Very small gauge, signal and low-power applications",
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

#### Get Wire Size
**GET** `/api/wire-sizes/{id}/`

Example:
```bash
curl "http://localhost:8000/api/wire-sizes/1/"
```

#### Create Wire Size
**POST** `/api/wire-sizes/`

Authentication: Required (admin)

Request:
```json
{
  "wire_size_mm2": "50.00",
  "max_ampacity": 200,
  "description": "Heavy industrial power distribution"
}
```

#### Update Wire Size
**PUT** `/api/wire-sizes/{id}/`

Authentication: Required (admin)

#### Delete Wire Size
**DELETE** `/api/wire-sizes/{id}/`

Authentication: Required (admin)

---

### Wire Recommendation Calculator API

#### Get Wire Recommendations
**POST** `/api/wire-recommendation/recommend/`

Request:
```json
{
  "required_current": 15.5
}
```

Response: (200 OK)
```json
{
  "required_current": 15.5,
  "recommendations": [
    {
      "id": 3,
      "wire_size_mm2": "2.5",
      "max_ampacity": 20,
      "description": "Standard for household outlet circuits",
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    },
    {
      "id": 4,
      "wire_size_mm2": "4.00",
      "max_ampacity": 32,
      "description": "Heavy duty residential circuits, kitchen appliances",
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

Error Response (404 Not Found):
```json
{
  "error": "No wire sizes available for 500A",
  "required_current": 500,
  "recommendations": []
}
```

---

## Pagination

All list endpoints support pagination. Default page size is 20 items.

```bash
curl "http://localhost:8000/api/components/?page=2"
```

Response includes:
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/components/?page=3",
  "previous": "http://localhost:8000/api/components/?page=1",
  "results": [...]
}
```

---

## Filtering & Search

### Search
Search for components by name or description:
```bash
curl "http://localhost:8000/api/components/?search=resistor"
```

### Filter by Category
Filter components by category:
```bash
curl "http://localhost:8000/api/components/?category=1"
```

### Ordering
Order results by field:
```bash
curl "http://localhost:8000/api/components/?ordering=name"
curl "http://localhost:8000/api/components/?ordering=-date_created"
```

---

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200  | OK - Request succeeded |
| 201  | Created - Resource created successfully |
| 204  | No Content - Successful deletion |
| 400  | Bad Request - Invalid parameters |
| 401  | Unauthorized - Authentication required |
| 403  | Forbidden - Permission denied |
| 404  | Not Found - Resource not found |
| 500  | Server Error - Internal server error |

---

## Error Handling

### Example Error Response

```json
{
  "field_name": [
    "Error message for this field"
  ]
}
```

### Validation Error (400 Bad Request)

Request:
```bash
curl -X POST "http://localhost:8000/api/components/" \
  -H "Content-Type: application/json" \
  -d '{"name": "", "category": 1}'
```

Response:
```json
{
  "name": [
    "This field may not be blank."
  ]
}
```

---

## Authentication

### Session Authentication (Default)

For authenticated requests (e.g., POST, PUT, DELETE), include credentials:

```bash
curl -b cookies.txt -c cookies.txt \
  -X POST "http://localhost:8000/api/components/" \
  -H "Content-Type: application/json" \
  -d '{"name": "New Component", "category": 1}'
```

### CSRF Token

For POST/PUT/DELETE requests, include CSRF token:

```bash
# Get CSRF token
csrf_token=$(curl -b cookies.txt -c cookies.txt \
  "http://localhost:8000/api/components/" | grep csrf)

# Use it in request
curl -b cookies.txt \
  -X POST "http://localhost:8000/api/components/" \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $csrf_token" \
  -d '{"name": "New Component", "category": 1}'
```

---

## Examples

### Python Example

```python
import requests

# List components
response = requests.get('http://localhost:8000/api/components/')
components = response.json()

# Search components
response = requests.get('http://localhost:8000/api/components/', 
                       params={'search': 'resistor'})

# Get wire recommendations
data = {'required_current': 15.5}
response = requests.post('http://localhost:8000/api/wire-recommendation/recommend/', 
                        json=data)
recommendations = response.json()
```

### JavaScript Example

```javascript
// List components
fetch('http://localhost:8000/api/components/')
  .then(response => response.json())
  .then(data => console.log(data))

// Get wire recommendations
fetch('http://localhost:8000/api/wire-recommendation/recommend/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    required_current: 15.5
  })
})
  .then(response => response.json())
  .then(data => console.log(data))
```

### cURL Example

```bash
# List all components
curl "http://localhost:8000/api/components/"

# Search for resistors
curl "http://localhost:8000/api/components/?search=resistor"

# Get specific component
curl "http://localhost:8000/api/components/1/"

# Get wire recommendations
curl -X POST "http://localhost:8000/api/wire-recommendation/recommend/" \
  -H "Content-Type: application/json" \
  -d '{"required_current": 15.5}'
```

---

## Rate Limiting

Currently, there is no rate limiting implemented. For production use, consider implementing rate limiting using Django REST Framework's throttling.

---

## Versioning

The current API is Version 1.0. Future versions may be implemented using URL versioning (e.g., `/api/v2/components/`).

---

## Support

For issues or questions about the API, please check the main documentation or create an issue on the repository.
