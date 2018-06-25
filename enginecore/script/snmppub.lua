if table.getn(ARGV) > 0 then
    redis.call('PUBLISH', 'oid-upd', KEYS[1])
    return redis.call('set', KEYS[1], ARGV[1])
else
    return redis.call('get', KEYS[1])
end
