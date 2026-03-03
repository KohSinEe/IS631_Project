# FridgeBuddy – Entity Relationship Diagram

## Mermaid ER diagram

```mermaid
erDiagram
    users {
        int id PK
        string email UK "not null"
        string hashed_password "not null"
        string name
        boolean is_active "default true"
        int household_id FK "nullable"
            enum household_role "co_owner, child nullable"
        datetime created_at
        datetime updated_at
    }

    households {
        int id PK
        string name "not null"
        int owner_id FK "nullable"
        datetime created_at
        datetime updated_at
    }

    items {
        int id PK
        string name "not null"
        int quantity "default 1"
        enum unit "pieces, mL, L, g, kg"
        string expiry_date "ISO date"
        enum category "Dairy, Meat, ..."
        int household_id FK "not null"
        datetime created_at
        datetime updated_at
    }

    users }o--|| households : "member of"
    households ||--o| users : "owner"
    households ||--|{ items : "contains"
    items }o--|| households : "belongs to"

    invitations {
        int id PK
        int household_id FK
        int inviter_id FK
        string invitee_email
        enum role "co_owner, child"
        enum status "pending, accepted, declined"
        datetime created_at
    }

    invitations }o--|| households : "for"
    invitations }o--o| users : "inviter"
```

## Relationships

| From       | To         | Cardinality | Description |
|-----------|------------|-------------|-------------|
| users     | households | N : 1       | User belongs to one household (`household_id`). Optional (nullable). |
| households| users      | 1 : N       | Household has many members. |
| households| users      | 1 : 1       | Household has one owner (`owner_id`). Optional (nullable). |
| households| items      | 1 : N       | Household has many items. Items are cascade-deleted with the household. |
| items     | households | N : 1       | Item belongs to one household (`household_id`). |
| invitations | households | N : 1     | Invitation is for one household. |
| invitations | users      | N : 1     | Invitation is sent by one user (inviter). |

## Table summary

- **users** – User accounts; can be linked to one household (fridge). `household_role` is co_owner or child (owner is implied by household.owner_id).
- **households** – Fridge/household; has an optional owner (`owner_id` → users.id) and many items.
- **items** – Food inventory rows; each belongs to one household.
- **invitations** – Pending/accepted/declined invites to join a household with a role (co_owner or child).
