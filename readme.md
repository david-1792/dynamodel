# Dynamodel

## Overview
Dynamodel is an async Python ORM library for AWS DynamoDB. Dynamodel objects are based off Pydantic for easy integration with FastAPI and similar frameworks.

Dynamodel objects are optimized for operations within single-table designs.

## Installation
### Pip
`pip install dynamodel`

### Poetry
`poetry add dynamodel`

### uv
`uv add dynamodel`

## Example
```py
import uuid

from dynamodel import Dynamodel, Field
from dynamodel.config import Table, Index, AccessPattern

primary_index = Index(
    partition_key='pk',
    sort_key='sk'
)

domain_index = Index(
    index_name='domain',
    partition_key='domain',
    sort_key='created_at'
)

secondary_index = Index(
    index_name='gs1',
    partition_key='gs1pk',
    sort_key='gs1sk'
)

table = Table(
    table_name='example',
    primary_index=primary_index,
    domain_index=domain_index,
    secondary_indexes=[secondary_index]
)

class User(Dynamodel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    email: str
    first_name: str
    last_name: str | None
    age: int
    
    class Settings:
        table=table
        domain='user'
        access_patterns=[
            AccessPattern(primary_index, 'user:{id}', 'user:{id}'),
            AccessPattern(secondary_index, 'user-email:{email}', 'user:{id}')
        ]

async def example() -> None:
    user = User(
        email='david.jr1792@gmail.com'
        first_name='David'
        last_name='Jiménez Rodríguez'
        age=21
    )

    await user.save()

    user = await User.get('41b103a6-e051-4cc6-8bb2-772b84573a0f')

    users = await User.query('david.jr1792@gmail.com', index=secondary_index)

class Post(Dynamodel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    title: str
    body: str

    class Settings:
        table=table
        domain='post'
        access_patterns=[
            AccessPattern(primary_index, 'user:{user_id}', 'post:{id}')
        ]
    
from enum import Enum
from datetime import datetime

from pydantic import BaseModel

class MetadataAttrs(BaseModel):
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class SubscriptionPlatform(str, Enum):
    STRIPE = 'stripe'
    GOOGLE_PLAY = 'google-play'
    APP_STORE = 'app-store'

# Adds the MetadataAttrs attributes to the model
class Customer(Dynamodel, MetadataAttrs):
    id: str
    user_id: uuid.UUID
    platform: SubscriptionPlatform

    class Settings:
        table=table
        domain='subscription'
        access_patterns=[
            AccessPattern(primary_index, 'user:{user_id}', 'platform:{platform}:customer:{id}')
        ]

class Subscription(Dynamodel, MetadataAttrs):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    platform: SubscriptionPlatform

    class Settings:
        table=table
        domain='subscription'
        access_patterns=[
            AccessPattern(primary_index, 'user:{user_id}', 'platform:{platform}:subscription:{id}')
        ]

async def example() -> None:
    sub = Subscription(
        user_id=user.id,
        platform=SubscriptionPlatform.STRIPE
    )

    await sub.save()

    sub = await Subscription.get(user.id, SubscriptionPlatform.STRIPE, sub.id)

    # Queries for pk = 'user:<user.id>' and sk starting with 'platform:stripe', with a filter condition on the domain
    stripe_subs = await Subscription.query(user.id, SubscriptionPlatform.STRIPE)

    # Does the same query as above but recovers the first object (or none)
    stripe_sub = await Subscription.find_one(user.id, SubscriptionPlaform.Stripe)

from dynamodel.collections import Collection

async def example() -> None:
    # Combines models into a single queryable object
    # NOTE: All models need to follow the same pk pattern to be added to a collection
    collection = Collection(models=[User, Post])

    # Does a query with pk = 'user:<user.id>' with a filter condition on the domains
    results = await collection.query(user.id)

    # Retrieves the first result of the User objects in the query result
    user = results[User].first()

    # Iterates through the user posts
    for post in results[Post]:
        print(post)

    collection = Collection(models=[Customer, Subscription])

    results = await collection.query(user.id)
    
    # Iterates through the user customers
    for customer in results[Customer]:
        print(customer)

    # Iterates through the user subscriptions
    for subscription in results[Subscription]:
        print(subscription)
```
