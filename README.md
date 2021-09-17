# Cache Money

[![Coverage Status](https://coveralls.io/repos/github/novisto/cache-money/badge.svg)](https://coveralls.io/github/novisto/cache-money)

Async cache library for [memoization](https://en.wikipedia.org/wiki/Memoization) using Redis. Inspired by 
[Walrus](https://github.com/coleifer/walrus) and implemented with [aioredis](https://github.com/aio-libs/aioredis-py).

Cache Money is used through a decorator you can add to your function that needs to be cached. When the decorator 
gets executed, Cache Money will make a unique key from the name of the function and the params received and look up in 
reddit if there is a result for this key. If there is a result it will be used as the output of the function and the 
execution of the function will be skipped.

You can add a timeout in the declaration of the decorator, you can find constants for common timeout duration in 
`cache_money/constants.py`. When the timeout is reached, Redis remove the entry itself.

It's also possible to clear the cache early by using the method bust that gets added to a function decorated by 
Cache Money. An example is provided below.

This library is available on PyPI under the name cache-money. You can install with pip by running `pip install 
cache-money`.


# Requirements

You need a redis instance running to use this library. This library was tested to run on version of Redis >= 4.0.0. 
If you have docker set up you can create a redis instance like this:

```
make redis-start
```


# Usage

## Basic usage

First thing is initializing Cache Money and decorating a function that you want to cache

```
from cache_money import cache_money, init_cache_money
from cache_money.constants import CACHE_HOUR

init_cache_money(host="localhost")

@cache_money.cached(timeout=CACHE_HOUR)
async def addition(x: int, y: int) -> int:
    return x + y

@cache_money.cached(timeout=CACHE_HOUR)
async def multiplication(x: int, y: int) -> int:
    return x * y
```

If you run the following calls to the function addition consecutively:
```
  >> await addition(3, 4)
  7
  
  >> await addition(3, 7)
  10
 
  >> await addition(3, 4)
  7
```
  
The first and second call would be executed, but the third call would have used the cache in redis instead, as long 
as the third call was done within one hour of when the first call was made, as the function addition is caching results 
for one hour.

In Redis you would see two entries like this:

```
# redis-cli 

127.0.0.1:6379> KEYS *
1) "addition:ea53056bad64a599c84efdfd4f4cbb64"
2) "addition:bb6b7afb6a6cf3191f6d7fd35d976d42"

127.0.0.1:6379> TTL addition:ea53056bad64a599c84efdfd4f4cbb64
(integer) 3403
```

## Busting cache for a specific function call

You can force expire(bust) the cache for a specific function call

```
>> await addition(3, 4)
>> await addition(3, 7)
>> await addition.bust(3, 4)
```

In Redis you would see one entry as the other one has been busted

```
127.0.0.1:6379> KEYS *
1) "addition:bb6b7afb6a6cf3191f6d7fd35d976d42"
```


## Busting cache for all function calls of a specific function

You can bust the cache for all instance of a function call

```
>> await addition(3, 4)
>> await addition(3, 7)
>> await multiplication(2, 4)
>> await addition.bust_all()
```

In Redis you would see no entries for fn addition which has been busted, you would see one entry for multiplication

```
127.0.0.1:6379> KEYS *
1) "multiplication:bc3b7afc6a7cf3191f6d1fd31d810d55"
```


## Busting cache for all function calls of all functions

You can bust the cache of all entries made by Cache Money as well

```
>> await addition(3, 4)
>> await addition(3, 7)
>> await multiplication(2, 4)
>> cache_money.bust()
```

In Redis you would see no entries

```
127.0.0.1:6379> KEYS *
(empty array)
```


## Contributing and getting set up for local development

To set yourself up for development on Cache Money, make sure you are using
[poetry](https://poetry.eustace.io/docs/) and simply run the following commands from the root directory:

```bash
make sys-deps
make install
```
