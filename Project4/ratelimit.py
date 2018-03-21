from redis import Redis

redis = Redis()


class RateLimit(object):
    # Provides 10 second buffer for key expiration to mitigate against clock
    # skew between workers and redis server
    expiration_window = 10

    def __init__(self, key_prefix, limit, per, send_x_headers):
        # Timestamp indicating when request limit gets reset
        self.reset = (int(time.time()) // per) * per + per
        # String to keep track of rate limits from each request, also
        # contains timestamp from reset above
        self.key = key_prefix + str(self.reset)
        # How many requests to allow
        self.limit = limit
        # How many requests per time period
        self.per = per
        # Boolean flag - do we put header in response telling client how many
        # requests they have left before they exceed the limit
        self.send_x_headers = send_x_headers
        # Use a pipeline to make sure we don't increment key without also setting
        # key expiration in case an exception happens (e.g., process killed)
        p = redis.pipeline()
        # Increment
        p.incr(self.key)
        # Set expiration time
        p.expireat(self.key, self.reset + self.expiration_window)
        self.current = min(p.execute()[0], limit)

    # How many requests do I have left before exceeding limit?
    remaining = property(lambda x: x.limit - x.current)
    # Have I hit the rate limit (exceeded limit)?
    over_limit = property(lambda x: x.current >= x.limit)


# Retrieve rate limit from g (Flask)
def get_view_rate_limit():
    return getattr(g, '_view_rate_limit', None)


# Client at/over limit, return 429 (too many requests)
def on_over_limit(limit):
    return (jsonify({'data':'You hit the rate limit','error':'429'}),429)


def ratelimit(limit, per=300, send_x_headers=True,
              over_limit=on_over_limit,
              scope_func=lambda: request.remote_addr,
              key_func=lambda: request.endpoint):
    def decorator(f):
        def rate_limited(*args, **kwargs):
            # Constructed from remote address and current endpoint
            key = 'rate-limit/%s/%s/' % (key_func(), scope_func())
            # Increment rate limit using class
            rlimit = RateLimit(key, limit, per, send_x_headers)
            # Store in Flask g
            g._view_rate_limit = rlimit
            if over_limit is not None and rlimit.over_limit:
                return over_limit(rlimit)
            return f(*args, **kwargs)
        return update_wrapper(rate_limited, f)
    return decorator


@app.after_request
def inject_x_rate_headers(response):
    limit = get_view_rate_limit()
    # If send_x_headers on, send rate limit info to client (using headers)
    if limit and limit.send_x_headers:
        h = response.headers
        h.add('X-RateLimit-Remaining', str(limit.remaining))
        h.add('X-RateLimit-Limit', str(limit.limit))
        h.add('X-RateLimit-Reset', str(limit.reset))
    return response

